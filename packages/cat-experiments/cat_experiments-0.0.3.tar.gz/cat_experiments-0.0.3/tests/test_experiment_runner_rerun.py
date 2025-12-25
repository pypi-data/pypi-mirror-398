"""Tests for ExperimentRunner.rerun_evaluators."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from cat.experiments import (
    DatasetExample,
    EvaluationContext,
    EvaluationMetric,
    ExperimentConfig,
    ExperimentResult,
    ExperimentRunner,
    ExperimentSummary,
)
from cat.experiments.evaluation_backends import EvaluationBackend


@dataclass
class _Plan:
    experiment_id: str
    config: ExperimentConfig
    dataset_examples: list[DatasetExample]
    results: list[ExperimentResult]
    summary: ExperimentSummary | None = None


class _Backend(EvaluationBackend[_Plan]):
    def __init__(self, plan: _Plan) -> None:
        self._plan = plan
        self.persisted = False

    def build_plan(self, experiment_id: str) -> _Plan:
        assert experiment_id == self._plan.experiment_id
        return self._plan

    def persist_results(self, plan: _Plan) -> None:
        self.persisted = True


def test_rerun_evaluators_updates_scores_and_persists():
    example = DatasetExample(
        input={"prompt": "hi"}, output={"answer": "hello"}, metadata={}, id="ex-1"
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
        metadata={},
        trace_id=None,
        error=None,
        execution_time_ms=3.0,
    )

    plan = _Plan(
        experiment_id="exp-1",
        config=ExperimentConfig(name="demo-plan"),
        dataset_examples=[example],
        results=[result],
    )

    backend = _Backend(plan)
    runner = ExperimentRunner()

    def accuracy_evaluator(ctx: EvaluationContext) -> EvaluationMetric:
        score = 1.0 if ctx.actual_output == ctx.output else 0.0
        return EvaluationMetric(name="accuracy", score=score)

    updated = runner.rerun_evaluators(
        experiment_id="exp-1",
        evaluators=[accuracy_evaluator],
        backend=backend,
    )

    assert updated[0].evaluation_scores["accuracy"] == 1.0
    assert backend.persisted is True
