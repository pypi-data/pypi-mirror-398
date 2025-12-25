"""Tests for running additional evaluators via the local storage adapter."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from cat.experiments import DatasetExample, ExperimentConfig, ExperimentResult
from cat.experiments.adapters.local_storage_evaluator import LocalEvaluationCoordinator
from cat.experiments.models import EvaluationMetric
from cat.experiments.serde import (
    dataset_example_to_dict,
    experiment_config_to_dict,
    experiment_result_to_dict,
)
from cat.experiments.types import AggregateEvaluatorResult


def _write_json(path, payload) -> None:
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2)


def test_local_evaluation_coordinator_updates_runs(tmp_path):
    storage_dir = tmp_path / "cache"
    experiment_id = "exp-local"
    experiment_path = storage_dir / experiment_id
    experiment_path.mkdir(parents=True)

    config = ExperimentConfig(name="Demo", dataset_id="ds-1")
    example = DatasetExample(
        input={"question": "hi"},
        output={"answer": "hello"},
        metadata={},
        id="ex-1",
    )
    result = ExperimentResult(
        example_id="ex-1",
        run_id="ex-1#1",
        repetition_number=1,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        input_data=example.input,
        output=example.output,
        actual_output={"answer": "hello"},
        evaluation_scores={},
        evaluator_metadata={},
        metadata={"run_id": "ex-1#1"},
        trace_id=None,
        error=None,
        execution_time_ms=5.0,
    )

    _write_json(experiment_path / "config.json", experiment_config_to_dict(config))
    with open(experiment_path / "examples.jsonl", "w") as fh:
        json.dump(dataset_example_to_dict(example), fh)
        fh.write("\n")
    with open(experiment_path / "runs.jsonl", "w") as fh:
        json.dump(experiment_result_to_dict(result), fh)
        fh.write("\n")

    def accuracy_evaluator(ctx):
        return 1.0 if ctx.actual_output == ctx.output else 0.0

    coordinator = LocalEvaluationCoordinator(storage_dir=storage_dir)
    results = coordinator.run_evaluators(
        experiment_id=experiment_id,
        evaluators=[accuracy_evaluator],
    )

    assert results[0].evaluation_scores["accuracy_evaluator"] == 1.0

    with open(experiment_path / "runs.jsonl") as fh:
        persisted = json.loads(fh.readline())
    assert persisted["evaluation_scores"]["accuracy_evaluator"] == 1.0


def test_local_evaluation_coordinator_updates_aggregates(tmp_path):
    storage_dir = tmp_path / "cache"
    experiment_id = "exp-local-agg"
    experiment_path = storage_dir / experiment_id
    experiment_path.mkdir(parents=True)

    config = ExperimentConfig(name="DemoAgg", dataset_id="ds-agg")
    example = DatasetExample(
        input={"question": "hi"},
        output={"answer": "hello"},
        metadata={},
        id="ex-1",
    )
    result = ExperimentResult(
        example_id="ex-1",
        run_id="ex-1#1",
        repetition_number=1,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        input_data=example.input,
        output=example.output,
        actual_output={"answer": "hello"},
        evaluation_scores={},
        evaluator_metadata={},
        metadata={"run_id": "ex-1#1"},
        trace_id=None,
        error=None,
        execution_time_ms=5.0,
    )

    _write_json(experiment_path / "config.json", experiment_config_to_dict(config))
    with open(experiment_path / "examples.jsonl", "w") as fh:
        json.dump(dataset_example_to_dict(example), fh)
        fh.write("\n")
    with open(experiment_path / "runs.jsonl", "w") as fh:
        json.dump(experiment_result_to_dict(result), fh)
        fh.write("\n")

    def agg_evaluator(ctx) -> AggregateEvaluatorResult:
        return {"total_runs": EvaluationMetric(name="total_runs", score=len(ctx.results))}

    coordinator = LocalEvaluationCoordinator(storage_dir=storage_dir)
    coordinator.run_evaluators(
        experiment_id=experiment_id,
        evaluators=[],
        aggregate_evaluators=[agg_evaluator],
    )

    summary_path = experiment_path / "summary.json"
    assert summary_path.exists()
    summary_payload = json.loads(summary_path.read_text())
    assert summary_payload["aggregate_scores"]["total_runs"] == 1
