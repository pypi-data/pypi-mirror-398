"""Evaluate additional metrics using runs persisted by LocalStorageExperimentListener."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ..evaluation_backends import EvaluationBackend
from ..experiments import ExperimentConfig, ExperimentResult, ExperimentSummary
from ..models import DatasetExample
from ..serde import (
    dataset_example_from_dict,
    experiment_config_from_dict,
    experiment_result_from_dict,
    experiment_result_to_dict,
    experiment_summary_from_dict,
    experiment_summary_to_dict,
)
from ..types import AggregateEvaluatorFn, EvaluatorFn

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..experiments import ExperimentRunner


@dataclass
class LocalEvaluationPlan:
    """Container describing cached runs that can be re-evaluated."""

    experiment_id: str
    config: ExperimentConfig
    dataset_examples: list[DatasetExample]
    results: list[ExperimentResult]
    summary: ExperimentSummary | None = None


class LocalEvaluationCoordinator(EvaluationBackend):
    """Loads recorded runs from disk and runs additional evaluators."""

    def __init__(self, storage_dir: str | Path | None = None) -> None:
        self._storage_dir = Path(storage_dir) if storage_dir else Path.cwd() / ".cat_cache"

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def build_plan(self, experiment_id: str) -> LocalEvaluationPlan:
        experiment_path = self._experiment_path(experiment_id)
        config = self._load_config(experiment_path / "config.json")
        examples = self._load_examples(experiment_path / "examples.jsonl")
        results = self._load_results(experiment_path / "runs.jsonl")
        summary = self._load_summary(experiment_path / "summary.json", config=config)
        return LocalEvaluationPlan(
            experiment_id=experiment_id,
            config=config,
            dataset_examples=examples,
            results=results,
            summary=summary,
        )

    def fetch_experiment(self, experiment_id: str) -> LocalEvaluationPlan:
        """Return cached experiment metadata and runs without mutating the store."""
        return self.build_plan(experiment_id)

    def run_evaluators(
        self,
        *,
        experiment_id: str,
        evaluators: list[EvaluatorFn],
        aggregate_evaluators: list[AggregateEvaluatorFn] | None = None,
        persist: bool = True,
        runner: ExperimentRunner | None = None,
    ) -> list[ExperimentResult]:
        from ..experiments import ExperimentRunner

        runner = runner or ExperimentRunner()
        return runner.rerun_evaluators(
            experiment_id=experiment_id,
            evaluators=evaluators,
            aggregate_evaluators=aggregate_evaluators or [],
            backend=self,
            persist=persist,
        )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
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
                examples.append(dataset_example_from_dict(json.loads(line)))
        return examples

    @staticmethod
    def _load_results(path: Path) -> list[ExperimentResult]:
        if not path.exists():
            raise FileNotFoundError(f"Cached run log not found at {path}")
        results: list[ExperimentResult] = []
        with open(path) as f:
            for line in f:
                payload = line.strip()
                if not payload:
                    continue
                results.append(experiment_result_from_dict(json.loads(payload)))
        return results

    @staticmethod
    def _load_summary(path: Path, *, config: ExperimentConfig) -> ExperimentSummary | None:
        if not path.exists():
            return None
        with open(path) as f:
            payload = json.load(f)
        return experiment_summary_from_dict(payload, config=config)

    def persist_results(self, plan: LocalEvaluationPlan) -> None:
        path = self._experiment_path(plan.experiment_id)
        runs_path = path / "runs.jsonl"
        with open(runs_path, "w") as f:
            for result in plan.results:
                json.dump(experiment_result_to_dict(result), f)
                f.write("\n")
        if plan.summary is not None:
            summary_path = path / "summary.json"
            with open(summary_path, "w") as f:
                json.dump(experiment_summary_to_dict(plan.summary), f, indent=2)


__all__ = ["LocalEvaluationCoordinator", "LocalEvaluationPlan"]
