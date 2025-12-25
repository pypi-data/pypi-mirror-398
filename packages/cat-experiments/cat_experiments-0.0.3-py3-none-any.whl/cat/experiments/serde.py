"""Serialization helpers for persisting experiment artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from .experiments import ExperimentConfig, ExperimentResult, ExperimentSummary
from .models import DatasetExample


def serialize_datetime(value: datetime | None) -> str | None:
    """Convert datetime objects into ISO strings for persistence."""

    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat()


def deserialize_datetime(value: Any) -> datetime | None:
    """Parse ISO timestamps (or epoch) back into timezone-aware datetimes."""

    if value in (None, ""):
        return None

    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)

    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None

    return None


def experiment_config_to_dict(config: ExperimentConfig) -> dict[str, Any]:
    return {
        "name": config.name,
        "description": config.description,
        "dataset_id": config.dataset_id,
        "dataset_version_id": config.dataset_version_id,
        "project_name": config.project_name,
        "tags": list(config.tags),
        "metadata": dict(config.metadata),
        "repetitions": config.repetitions,
        "preview_examples": config.preview_examples,
        "preview_seed": config.preview_seed,
        "max_workers": config.max_workers,
    }


def experiment_config_from_dict(payload: Mapping[str, Any]) -> ExperimentConfig:
    return ExperimentConfig(
        name=payload["name"],
        description=payload.get("description", ""),
        dataset_id=payload.get("dataset_id"),
        dataset_version_id=payload.get("dataset_version_id"),
        project_name=payload.get("project_name"),
        tags=list(payload.get("tags", [])),
        metadata=dict(payload.get("metadata", {})),
        repetitions=int(payload.get("repetitions") or 1),
        preview_examples=payload.get("preview_examples"),
        preview_seed=payload.get("preview_seed", 42),
        max_workers=int(payload.get("max_workers") or 1),
    )


def dataset_example_to_dict(example: DatasetExample) -> dict[str, Any]:
    return {
        "id": example.id,
        "input": example.input,
        "output": example.output,
        "metadata": example.metadata,
        "created_at": serialize_datetime(example.created_at),
        "updated_at": serialize_datetime(example.updated_at),
    }


def dataset_example_from_dict(payload: Mapping[str, Any]) -> DatasetExample:
    metadata = dict(payload.get("metadata", {}))
    tags = payload.get("tags")
    if tags and "tags" not in metadata:
        metadata["tags"] = list(tags)
    for key in ("source_trace_id", "source_node_id"):
        value = payload.get(key)
        if value is not None and key not in metadata:
            metadata[key] = value

    return DatasetExample(
        input=dict(payload.get("input", {})),
        output=dict(payload.get("output", {})),
        metadata=metadata,
        id=payload.get("id"),
        created_at=deserialize_datetime(payload.get("created_at")),
        updated_at=deserialize_datetime(payload.get("updated_at")),
    )


def experiment_result_to_dict(result: ExperimentResult) -> dict[str, Any]:
    return {
        "example_id": result.example_id,
        "run_id": result.run_id,
        "repetition_number": result.repetition_number,
        "started_at": serialize_datetime(result.started_at),
        "completed_at": serialize_datetime(result.completed_at),
        "input_data": result.input_data,
        "output": result.output,
        "actual_output": result.actual_output,
        "evaluation_scores": result.evaluation_scores,
        "evaluator_metadata": result.evaluator_metadata,
        "metadata": result.metadata,
        "trace_id": result.trace_id,
        "error": result.error,
        "execution_time_ms": result.execution_time_ms,
    }


def experiment_result_from_dict(payload: Mapping[str, Any]) -> ExperimentResult:
    return ExperimentResult(
        example_id=payload["example_id"],
        run_id=payload.get("run_id") or payload["example_id"],
        repetition_number=int(payload.get("repetition_number") or 1),
        started_at=deserialize_datetime(payload.get("started_at")),
        completed_at=deserialize_datetime(payload.get("completed_at")),
        input_data=dict(payload.get("input_data", {})),
        output=dict(payload.get("output", {})),
        actual_output=payload.get("actual_output"),
        evaluation_scores=dict(payload.get("evaluation_scores", {})),
        evaluator_metadata=dict(payload.get("evaluator_metadata", {})),
        metadata=dict(payload.get("metadata", {})),
        trace_id=payload.get("trace_id"),
        error=payload.get("error"),
        execution_time_ms=payload.get("execution_time_ms"),
    )


def experiment_summary_to_dict(summary: ExperimentSummary) -> dict[str, Any]:
    return {
        "total_examples": summary.total_examples,
        "successful_examples": summary.successful_examples,
        "failed_examples": summary.failed_examples,
        "average_scores": summary.average_scores,
        "aggregate_scores": summary.aggregate_scores,
        "aggregate_metadata": summary.aggregate_metadata,
        "total_execution_time_ms": summary.total_execution_time_ms,
        "experiment_id": summary.experiment_id,
        "started_at": serialize_datetime(summary.started_at),
        "completed_at": serialize_datetime(summary.completed_at),
    }


def experiment_summary_from_dict(
    payload: Mapping[str, Any], *, config: ExperimentConfig
) -> ExperimentSummary:
    started_at = deserialize_datetime(payload.get("started_at")) or datetime.now(timezone.utc)
    completed_at = deserialize_datetime(payload.get("completed_at"))
    return ExperimentSummary(
        total_examples=int(payload.get("total_examples") or 0),
        successful_examples=int(payload.get("successful_examples") or 0),
        failed_examples=int(payload.get("failed_examples") or 0),
        average_scores=dict(payload.get("average_scores", {})),
        aggregate_scores=dict(payload.get("aggregate_scores", {})),
        aggregate_metadata=dict(payload.get("aggregate_metadata", {})),
        total_execution_time_ms=float(payload.get("total_execution_time_ms") or 0.0),
        experiment_id=payload.get("experiment_id") or config.name,
        config=config,
        started_at=started_at,
        completed_at=completed_at,
    )


__all__ = [
    "serialize_datetime",
    "deserialize_datetime",
    "experiment_config_to_dict",
    "experiment_config_from_dict",
    "dataset_example_to_dict",
    "dataset_example_from_dict",
    "experiment_result_to_dict",
    "experiment_result_from_dict",
    "experiment_summary_to_dict",
    "experiment_summary_from_dict",
]
