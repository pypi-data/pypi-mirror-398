"""Helpers to resume Phoenix experiments using cat-experiments."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Iterable, Mapping, MutableMapping, Sequence

try:  # pragma: no cover - dependency guard
    import httpx
except ImportError as exc:  # pragma: no cover - runtime safeguard
    raise ImportError(
        "Phoenix resume helpers require the optional 'httpx' dependency. "
        "Install cat-experiments[phoenix] or `pip install httpx` to enable them."
    ) from exc

from cat.experiments.models import DatasetExample
from cat.experiments.types import EvaluatorFn, TestFn

if TYPE_CHECKING:  # pragma: no cover
    from phoenix.client import Client as PhoenixClient

    from cat.experiments.experiments import ExperimentConfig, ExperimentRunner, ExperimentSummary
else:  # pragma: no cover
    PhoenixClient = Any  # type: ignore[misc,assignment]

logger = logging.getLogger(__name__)


@dataclass
class PhoenixTaskResumePlan:
    """Complete inputs required to resume task runs for a Phoenix experiment."""

    experiment_id: str
    dataset_examples: list[DatasetExample]
    run_selection: dict[str, set[int]]
    config: ExperimentConfig

    @property
    def has_work(self) -> bool:
        return any(self.run_selection.values())


class PhoenixResumeCoordinator:
    """Orchestrates translating Phoenix incomplete runs into cat-experiments executions."""

    def __init__(self, client: PhoenixClient, *, http_timeout: int = 60) -> None:
        self._client = client
        self._http: httpx.Client = getattr(client, "_client")
        self._http_timeout = http_timeout

    def build_task_resume_plan(self, *, experiment_id: str) -> PhoenixTaskResumePlan:
        """Fetch Phoenix metadata and incomplete runs to construct a resume plan."""
        experiment = self._client.experiments.get(experiment_id=experiment_id)

        dataset_id = experiment.get("dataset_id")
        dataset_version_id = experiment.get("dataset_version_id")
        repetitions = int(experiment.get("repetitions") or 1)

        run_selection: dict[str, set[int]] = {}
        example_map: MutableMapping[str, DatasetExample] = {}

        for incomplete in self._stream_incomplete_runs(experiment_id=experiment_id):
            dataset_example = incomplete["dataset_example"]
            example_id = dataset_example["id"]
            repetitions_for_example: Sequence[int] = incomplete.get("repetition_numbers", [])

            if example_id not in example_map:
                example_map[example_id] = self._to_dataset_example(dataset_example)

            entry = run_selection.setdefault(example_id, set())
            entry.update(int(rep) for rep in repetitions_for_example)

        from cat.experiments.experiments import ExperimentConfig

        config = ExperimentConfig(
            name=experiment.get("name") or f"phoenix-{experiment_id}",
            description=experiment.get("description", ""),
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            repetitions=repetitions,
            metadata=dict(experiment.get("metadata") or {}),
            project_name=experiment.get("project_name"),
            tags=list(experiment.get("tags") or []),
        )
        config.metadata.setdefault("phoenix_experiment_id", experiment_id)

        return PhoenixTaskResumePlan(
            experiment_id=experiment_id,
            dataset_examples=list(example_map.values()),
            run_selection=run_selection,
            config=config,
        )

    def resume_task_runs(
        self,
        *,
        experiment_id: str,
        task: TestFn,
        evaluators: list[EvaluatorFn] | None = None,
        runner: ExperimentRunner | None = None,
        experiment_id_override: str | None = None,
    ) -> ExperimentSummary | None:
        """Execute only the incomplete (example, repetition) pairs for a Phoenix experiment."""
        plan = self.build_task_resume_plan(experiment_id=experiment_id)

        if not plan.has_work:
            logger.info("Phoenix experiment %s is already complete.", experiment_id)
            return None

        from cat.experiments.experiments import ExperimentRunner

        runner = runner or ExperimentRunner()
        summary = runner.run(
            dataset=plan.dataset_examples,
            task=task,
            evaluators=evaluators or [],
            config=plan.config,
            experiment_id=experiment_id_override or plan.experiment_id,
            run_selection=plan.run_selection,
        )
        return summary

    def _stream_incomplete_runs(self, *, experiment_id: str) -> Iterable[dict[str, Any]]:
        """Yield incomplete run payloads from Phoenix with pagination."""
        cursor: str | None = None

        while True:
            params: dict[str, Any] = {"limit": 50}
            if cursor:
                params["cursor"] = cursor

            try:
                response = self._http.get(
                    f"v1/experiments/{experiment_id}/incomplete-runs",
                    params=params,
                    timeout=self._http_timeout,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    raise ValueError(
                        "Incomplete-run endpoint unavailable. Ensure Phoenix server "
                        "version supports resume_experiment."
                    ) from exc
                raise

            body = response.json()
            data = body.get("data", [])
            if not data:
                break

            for incomplete in data:
                yield incomplete

            cursor = body.get("next_cursor")
            if not cursor:
                break

    @staticmethod
    def _to_dataset_example(payload: Mapping[str, Any] | Any) -> DatasetExample:
        """Convert Phoenix dataset example payload (dict or client model) into DatasetExample."""

        if isinstance(payload, Mapping):
            raw_input = payload.get("input", {}) or {}
            raw_output = payload.get("output", {}) or {}
            raw_metadata = payload.get("metadata", {}) or {}
            example_id = payload.get("id")
            created_at = payload.get("created_at")
            updated_at = payload.get("updated_at")
        else:
            raw_input = getattr(payload, "input", {}) or {}
            raw_output = getattr(payload, "output", {}) or {}
            raw_metadata = getattr(payload, "metadata", {}) or {}
            example_id = getattr(payload, "id", None)
            created_at = getattr(payload, "created_at", None)
            updated_at = getattr(payload, "updated_at", None)

        def _coerce_mapping(value: Any) -> dict[str, Any]:
            return dict(value) if isinstance(value, Mapping) else {}

        return DatasetExample(
            input=_coerce_mapping(raw_input),
            output=_coerce_mapping(raw_output),
            metadata=_coerce_mapping(raw_metadata),
            id=example_id,
            created_at=created_at,
            updated_at=updated_at,
        )
