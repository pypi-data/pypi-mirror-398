"""Resume helpers for experiments cached by the local storage adapter."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..evaluation import evaluate_aggregate
from ..experiments import (
    ExperimentConfig,
    ExperimentResult,
    ExperimentRunner,
    ExperimentSummary,
    _build_summary_from_results,
)
from ..models import AggregateEvaluationContext, DatasetExample
from ..result_utils import build_contexts_from_results
from ..serde import (
    dataset_example_from_dict,
    experiment_config_from_dict,
    experiment_result_from_dict,
    experiment_result_to_dict,
    experiment_summary_from_dict,
    experiment_summary_to_dict,
)
from ..types import AggregateEvaluatorFn, EvaluatorFn, TestFn
from .local_storage import LocalStorageExperimentListener, LocalStorageSyncConfig


@dataclass
class LocalTaskResumePlan:
    """Inputs required to resume cached experiment runs."""

    experiment_id: str
    dataset_examples: list[DatasetExample]
    run_selection: dict[str, set[int]]
    config: ExperimentConfig
    completed_results: list[Any]
    summary: ExperimentSummary | None = None

    @property
    def has_work(self) -> bool:
        return any(self.run_selection.values())


class LocalCacheResumeCoordinator:
    """Resumes experiments stored via the local storage adapter."""

    def __init__(self, storage_dir: str | Path | None = None) -> None:
        self._storage_dir = Path(storage_dir) if storage_dir else Path.cwd() / ".cat_cache"

    def build_task_resume_plan(self, experiment_id: str) -> LocalTaskResumePlan:
        """Load cached examples/config and compute pending repetitions."""
        experiment_path = self._experiment_path(experiment_id)
        config = self._load_config(experiment_path / "config.json")
        examples = self._load_examples(experiment_path / "examples.jsonl")
        completed_results = self._load_results(experiment_path / "runs.jsonl")
        summary = self._load_summary(experiment_path / "summary.json", config=config)
        completed = self._collect_completed_runs(completed_results)

        pending_examples: list[DatasetExample] = []
        run_selection: dict[str, set[int]] = {}
        repetitions = max(1, int(config.repetitions or 1))

        for example in examples:
            example_id = example.id
            if not example_id:
                continue
            finished = completed.get(example_id, set())
            remaining = {rep for rep in range(1, repetitions + 1) if rep not in finished}
            if remaining:
                pending_examples.append(example)
                run_selection[example_id] = remaining

        return LocalTaskResumePlan(
            experiment_id=experiment_id,
            dataset_examples=examples,
            run_selection=run_selection,
            config=config,
            completed_results=completed_results,
            summary=summary,
        )

    def resume_task_runs(
        self,
        *,
        experiment_id: str,
        task: TestFn,
        evaluators: list[EvaluatorFn] | None = None,
        aggregate_evaluators: list[AggregateEvaluatorFn] | None = None,
        runner: ExperimentRunner | None = None,
        experiment_id_override: str | None = None,
    ) -> ExperimentSummary | None:
        """Execute only the pending (example, repetition) pairs from cache."""
        plan = self.build_task_resume_plan(experiment_id=experiment_id)
        if not plan.has_work:
            if not aggregate_evaluators:
                return None
        if aggregate_evaluators is None:
            aggregate_evaluators = []

        if runner is None:
            runner = ExperimentRunner()
            runner.add_listener(
                LocalStorageExperimentListener(
                    config=LocalStorageSyncConfig(base_dir=self._storage_dir)
                )
            )
        run_experiment_id = plan.experiment_id
        if plan.has_work and experiment_id_override:
            run_experiment_id = experiment_id_override
        all_results = list(plan.completed_results)

        # Run only pending repetitions; we will recompute aggregates over all runs afterward.
        if plan.has_work:
            runner.run(
                dataset=plan.dataset_examples,
                task=task,
                evaluators=evaluators or [],
                config=plan.config,
                experiment_id=run_experiment_id,
                run_selection=plan.run_selection,
                aggregate_evaluators=[],
            )

            # Reload all results from disk (pending + previously completed)
            experiment_path = self._experiment_path(run_experiment_id)
            all_results = self._load_results(experiment_path / "runs.jsonl")
        else:
            experiment_path = self._experiment_path(run_experiment_id)
        examples_by_id = {ex.id: ex for ex in plan.dataset_examples if ex.id}
        contexts = build_contexts_from_results(all_results, examples_by_id)

        aggregate_scores: dict[str, float] = {}
        aggregate_metadata: dict[str, dict[str, Any]] = {}
        if aggregate_evaluators:
            aggregate_context = AggregateEvaluationContext(
                experiment_id=run_experiment_id,
                config=plan.config,
                contexts=contexts,
                results=all_results,
                examples=list(examples_by_id.values()),
                started_at=plan.summary.started_at if plan.summary else None,
                completed_at=plan.summary.completed_at if plan.summary else None,
            )
            agg_result = evaluate_aggregate(aggregate_context, aggregate_evaluators)
            aggregate_scores = agg_result.get("aggregate_scores", {})
            aggregate_metadata = agg_result.get("aggregate_metadata", {})

        summary = _build_summary_from_results(
            results=all_results,
            config=plan.config,
            experiment_id=run_experiment_id,
            aggregate_scores=aggregate_scores,
            aggregate_metadata=aggregate_metadata,
            started_at=plan.summary.started_at if plan.summary else None,
            completed_at=datetime.now(timezone.utc),
        )

        # Persist updated runs/summary
        runs_path = experiment_path / "runs.jsonl"
        with open(runs_path, "w") as f:
            for result in all_results:
                json.dump(experiment_result_to_dict(result), f)
                f.write("\n")
        summary_path = experiment_path / "summary.json"
        with open(summary_path, "w") as f:
            json.dump(experiment_summary_to_dict(summary), f, indent=2)

        return summary

    def _experiment_path(self, experiment_id: str) -> Path:
        path = self._storage_dir / experiment_id
        if not path.exists():
            raise FileNotFoundError(
                f"No cached experiment found at {path}. Ensure the experiment ID is correct."
            )
        return path

    @staticmethod
    def _load_config(path: Path) -> ExperimentConfig:
        if not path.exists():
            raise FileNotFoundError(f"Cached config not found at {path}")

        with open(path) as f:
            data = json.load(f)

        return experiment_config_from_dict(data)

    @staticmethod
    def _load_examples(path: Path) -> list[DatasetExample]:
        if not path.exists():
            raise FileNotFoundError(f"Cached examples not found at {path}")

        examples: list[DatasetExample] = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                examples.append(dataset_example_from_dict(payload))
        return examples

    @staticmethod
    def _load_results(path: Path) -> list[ExperimentResult]:
        if not path.exists():
            return []
        results = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                results.append(experiment_result_from_dict(json.loads(line)))
        return results

    @staticmethod
    def _collect_completed_runs(results: list[Any]) -> dict[str, set[int]]:
        completed: dict[str, set[int]] = {}
        for record in results:
            example_id = record.example_id
            rep = record.repetition_number
            if not example_id or not rep or record.error:
                continue
            bucket = completed.setdefault(example_id, set())
            bucket.add(int(rep))
        return completed

    @staticmethod
    def _load_summary(path: Path, *, config: ExperimentConfig) -> ExperimentSummary | None:
        if not path.exists():
            return None
        with open(path) as f:
            payload = json.load(f)
        return experiment_summary_from_dict(payload, config=config)


__all__ = [
    "LocalCacheResumeCoordinator",
    "LocalTaskResumePlan",
]
