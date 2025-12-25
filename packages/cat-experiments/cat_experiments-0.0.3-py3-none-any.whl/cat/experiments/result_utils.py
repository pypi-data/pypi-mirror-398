"""Helpers for rehydrating recorded runs and applying evaluator outputs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, Mapping

from .models import DatasetExample, EvaluationContext

if TYPE_CHECKING:  # pragma: no cover
    from .experiments import ExperimentResult


def build_contexts_from_results(
    results: Iterable["ExperimentResult"],
    examples_by_id: Mapping[str, DatasetExample],
) -> list[EvaluationContext]:
    """Reconstruct evaluation contexts from stored experiment results."""

    contexts: list[EvaluationContext] = []
    for result in results:
        example_id = result.example_id
        if example_id not in examples_by_id:
            raise KeyError(f"Example {example_id} missing from provided dataset examples")
        example = examples_by_id[example_id]
        if result.input_data is None or result.output is None:
            raise ValueError(
                "ExperimentResult is missing recorded input/output; rerun requires persisted data"
            )
        contexts.append(
            EvaluationContext(
                example_id=example_id,
                run_id=result.run_id,
                repetition_number=result.repetition_number,
                actual_output=result.actual_output,
                input=dict(result.input_data),
                output=dict(result.output),
                metadata=dict(example.metadata),
                expected_tool_calls=example.expected_tool_calls,
                started_at=result.started_at,
                completed_at=result.completed_at,
                execution_time_ms=result.execution_time_ms,
                error=result.error,
                execution_metadata=dict(result.metadata),
                trace_id=result.trace_id,
            )
        )
    return contexts


def apply_evaluations_to_results(
    results: list["ExperimentResult"],
    evaluation_payloads: Iterable[dict[str, Any]],
    *,
    merge: bool = False,
) -> None:
    """Attach evaluator outputs to ExperimentResult objects in-place."""

    for result, evaluation in zip(results, evaluation_payloads):
        scores = dict(evaluation.get("evaluation_scores", {}))
        metadata = dict(evaluation.get("evaluator_metadata", {}))

        if merge:
            result.evaluation_scores.update(scores)
            result.evaluator_metadata.update(metadata)
        else:
            result.evaluation_scores = scores
            result.evaluator_metadata = metadata


__all__ = ["build_contexts_from_results", "apply_evaluations_to_results"]
