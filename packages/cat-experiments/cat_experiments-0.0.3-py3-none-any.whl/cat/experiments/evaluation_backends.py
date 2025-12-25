"""Protocols for backends that can provide persisted experiment runs for re-evaluation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar

from .models import DatasetExample

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .experiments import ExperimentConfig, ExperimentResult, ExperimentSummary


class EvaluationPlanProtocol(Protocol):
    experiment_id: str
    config: "ExperimentConfig"
    dataset_examples: list[DatasetExample]
    results: list["ExperimentResult"]
    summary: "ExperimentSummary | None"


PlanT = TypeVar("PlanT", bound=EvaluationPlanProtocol)


class EvaluationBackend(Protocol[PlanT]):
    """Interface for fetching and persisting experiment runs used for re-evaluation."""

    def build_plan(self, experiment_id: str) -> PlanT: ...

    def fetch_experiment(self, experiment_id: str) -> PlanT: ...

    def persist_results(self, plan: PlanT) -> None: ...


__all__ = ["EvaluationBackend", "EvaluationPlanProtocol"]
