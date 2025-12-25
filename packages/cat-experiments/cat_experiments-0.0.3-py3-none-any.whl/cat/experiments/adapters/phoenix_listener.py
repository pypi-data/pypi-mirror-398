"""Phoenix listener that syncs cat-experiments runs to a Phoenix server."""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

import httpx

try:
    from phoenix.client import Client as PhoenixClient
except ImportError as exc:  # pragma: no cover - phoenix optional in some environments
    raise RuntimeError("phoenix-client must be installed to use PhoenixExperimentListener") from exc

from typing import TYPE_CHECKING

from cat.experiments.listeners import ExperimentListener
from cat.experiments.models import DatasetExample

if TYPE_CHECKING:  # pragma: no cover
    from cat.experiments.experiments import ExperimentConfig, ExperimentResult

logger = logging.getLogger(__name__)


@dataclass
class PhoenixSyncConfig:
    """Configuration for syncing experiments to Phoenix."""

    project_name: str | None = None
    """Override project name for spans when not provided by ExperimentConfig."""


class PhoenixExperimentListener(ExperimentListener):
    """Listener that mirrors cat-experiments experiment runs into Phoenix."""

    def __init__(
        self,
        client: PhoenixClient,
        *,
        config: PhoenixSyncConfig | None = None,
    ) -> None:
        self._client = client
        self._http: httpx.Client = client._client  # Uses underlying HTTP client
        self._config = config or PhoenixSyncConfig()

        self._remote_experiment_id: str | None = None
        self._remote_project_name: str | None = None
        self._dataset_id: str | None = None
        self._dataset_version_id: str | None = None
        self._examples_by_id: dict[str, DatasetExample] = {}
        self._example_id_map: dict[str, str] = {}
        self._pending_runs: list[dict[str, Any]] = []
        self._run_id_map: dict[str, str] = {}
        self._results_by_run_id: dict[str, ExperimentResult] = {}

    # ------------------------------------------------------------------ #
    # ExperimentListener interface
    # ------------------------------------------------------------------ #
    def on_experiment_started(
        self,
        experiment_id: str,
        config: ExperimentConfig,
        examples: list[DatasetExample],
    ) -> None:
        self._reset_state(experiment_id, config, examples)

        if not self._dataset_id:
            raise RuntimeError(
                "dataset_id missing in ExperimentConfig; Phoenix sync disabled for this run."
            )

        payload = self._build_experiment_payload(config)

        try:
            experiment = self._client.experiments.create(  # type: ignore[attr-defined]
                dataset_id=self._dataset_id,
                dataset_version_id=self._dataset_version_id,
                experiment_name=payload.get("name"),
                experiment_description=payload.get("description"),
                experiment_metadata=payload.get("metadata"),
                splits=payload.get("splits"),
                repetitions=payload.get("repetitions", 1),
                timeout=30,
            )
        except Exception as exc:  # pragma: no cover - handled via offline mode
            raise RuntimeError(f"Failed to create Phoenix experiment: {exc}") from exc

        self._remote_experiment_id = experiment.get("id")
        self._remote_project_name = (
            experiment.get("project_name") or config.project_name or self._config.project_name
        )
        if self._remote_experiment_id:
            config.metadata.setdefault("remote_experiment_id", self._remote_experiment_id)
            config.metadata.setdefault("phoenix_experiment_id", self._remote_experiment_id)
        if not self._remote_experiment_id:
            raise RuntimeError(
                "Phoenix response missing experiment id; disabling sync for this run."
            )

        logger.info(
            "Phoenix experiment created",
            extra={
                "dataset_id": self._dataset_id,
                "experiment_id": self._remote_experiment_id,
            },
        )

    def on_task_completed(
        self,
        experiment_id: str,
        result: ExperimentResult,
    ) -> None:
        if result.run_id:
            self._results_by_run_id[result.run_id] = result
        if self._remote_experiment_id:
            result.metadata.setdefault("phoenix_experiment_id", self._remote_experiment_id)
            result.metadata.setdefault("experiment_id", self._remote_experiment_id)
            result.metadata.setdefault("remote_experiment_id", self._remote_experiment_id)

        run_payload = self._build_run_payload(result)

        if not self._remote_experiment_id:
            raise RuntimeError("Phoenix experiment not initialized; cannot submit run.")

        try:
            response = self._http.post(
                f"v1/experiments/{self._remote_experiment_id}/runs",
                json=run_payload,
                timeout=30,
            )
            response.raise_for_status()
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            raise RuntimeError(f"Failed to submit Phoenix run payload: {exc}") from exc

        remote_run_id = response.json().get("data", {}).get("id")
        if remote_run_id:
            self._run_id_map[result.run_id] = remote_run_id
            result.metadata.setdefault("phoenix_run_id", remote_run_id)
            result.metadata.setdefault("remote_run_id", remote_run_id)

    def on_task_evaluated(
        self,
        experiment_id: str,
        result: ExperimentResult,
    ) -> None:
        """Phoenix sync defers evaluations until experiment completion."""
        return

    def on_experiment_completed(
        self,
        experiment_id: str,
        results: list[ExperimentResult],
        summary,
    ) -> None:
        if self._remote_experiment_id:
            summary.aggregate_metadata.setdefault(
                "phoenix", {"experiment_id": self._remote_experiment_id}
            )
            summary.aggregate_metadata.setdefault(
                "remote", {"experiment_id": self._remote_experiment_id}
            )

        evaluations = list(self._build_evaluations(results))
        if not self._remote_experiment_id:
            raise RuntimeError("Phoenix experiment not initialized; cannot submit evaluations.")

        # Flush any runs that were queued before completion (should be empty in steady state)
        self._flush_pending_runs()

        for entry in evaluations:
            payload = entry.get("payload", {})
            local_run_id = entry.get("local_run_id")
            evaluator_name = entry.get("evaluator_name")
            try:
                response = self._http.post(
                    "v1/experiment_evaluations",
                    json=payload,
                    timeout=30,
                )
                response.raise_for_status()
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                raise RuntimeError(f"Failed to submit Phoenix evaluation payload: {exc}") from exc

            remote_eval_id = response.json().get("data", {}).get("id")
            if remote_eval_id and local_run_id and evaluator_name:
                result = self._results_by_run_id.get(str(local_run_id))
                if result is not None:
                    meta = result.evaluator_metadata.setdefault(evaluator_name, {})
                    meta.setdefault("phoenix_evaluation_id", remote_eval_id)
                    meta.setdefault("remote_evaluation_id", remote_eval_id)
                    meta.setdefault("experiment_id", self._remote_experiment_id)

        return

    def on_aggregate_completed(
        self,
        experiment_id: str,
        aggregate_scores: dict[str, float],
        aggregate_metadata: dict[str, dict[str, object]],
    ) -> None:
        """No-op for aggregates; they are carried in the final summary payload."""
        return

    def on_experiment_failed(self, experiment_id: str, error: str) -> None:
        raise RuntimeError(f"Experiment {experiment_id} failed: {error}")

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _reset_state(
        self,
        experiment_id: str,
        config: ExperimentConfig,
        examples: list[DatasetExample],
    ) -> None:
        self._remote_experiment_id = None
        self._remote_project_name = config.project_name or self._config.project_name
        self._dataset_id = config.dataset_id or config.metadata.get("dataset_id")
        self._dataset_version_id = config.dataset_version_id or config.metadata.get(
            "dataset_version_id"
        )
        self._example_id_map = {}
        self._examples_by_id = {example.id: example for example in examples if example.id}
        self._pending_runs = []
        self._run_id_map = {}
        self._results_by_run_id = {}

        if self._dataset_id:
            self._prepare_example_id_mapping(examples)

    def _build_experiment_payload(self, config: ExperimentConfig) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "version_id": self._dataset_version_id,
            "splits": config.metadata.get("splits"),
            "name": config.name,
            "description": config.description,
            "metadata": config.metadata,
            "repetitions": config.repetitions,
        }
        # Remove keys with None values to satisfy Phoenix API
        return {k: v for k, v in payload.items() if v is not None}

    def _build_run_payload(self, result: ExperimentResult) -> dict[str, Any]:
        started_at = self._iso_or_metadata(result.started_at, result.metadata.get("started_at"))
        completed_at = self._iso_or_metadata(
            result.completed_at, result.metadata.get("completed_at")
        )
        example_id = self._example_id_map.get(str(result.example_id), result.example_id)

        payload: dict[str, Any] = {
            "dataset_example_id": example_id,
            "output": _ensure_json_safe(result.actual_output),
            "repetition_number": result.repetition_number,
            "start_time": started_at,
            "end_time": completed_at,
            "id": result.run_id or f"temp-{uuid.uuid4().hex[:8]}",
            "experiment_id": self._remote_experiment_id or "pending",
        }

        if result.trace_id:
            payload["trace_id"] = result.trace_id
        if result.error:
            payload["error"] = result.error

        return payload

    def _build_evaluations(self, results: Iterable[ExperimentResult]) -> Iterable[dict[str, Any]]:
        """Build evaluation payloads with local run context for downstream ID mapping."""
        for run in results:
            run_id = self._run_id_map.get(run.run_id, run.run_id)
            for name, score in run.evaluation_scores.items():
                metadata = dict(run.evaluator_metadata.get(name, {}))
                evaluation_result: dict[str, Any] = {}
                if score is not None:
                    evaluation_result["score"] = score
                label = metadata.get("label")
                if label is not None:
                    evaluation_result["label"] = label
                explanation = metadata.get("explanation")
                if explanation is not None:
                    evaluation_result["explanation"] = explanation

                annotator_kind = metadata.get("annotator_kind", "CODE")
                trace_id = metadata.get("trace_id") or run.trace_id
                started_at = metadata.get("started_at") or self._iso_or_metadata(
                    run.started_at, run.metadata.get("started_at")
                )
                completed_at = metadata.get("completed_at") or self._iso_or_metadata(
                    run.completed_at, run.metadata.get("completed_at")
                )
                metadata_payload = {
                    k: v
                    for k, v in metadata.items()
                    if k
                    not in {
                        "label",
                        "explanation",
                        "annotator_kind",
                        "trace_id",
                        "started_at",
                        "completed_at",
                    }
                }

                payload: dict[str, Any] = {
                    "experiment_run_id": run_id,
                    "start_time": started_at,
                    "end_time": completed_at,
                    "name": name,
                    "annotator_kind": annotator_kind,
                    "result": evaluation_result or None,
                    "metadata": metadata_payload,
                }
                if not payload["metadata"]:
                    payload.pop("metadata")

                if trace_id:
                    payload["trace_id"] = trace_id
                if run.error and not evaluation_result:
                    payload["error"] = run.error

                yield {
                    "payload": payload,
                    "local_run_id": run.run_id,
                    "evaluator_name": name,
                }

    def _flush_pending_runs(self) -> None:
        if not self._remote_experiment_id:
            raise RuntimeError("Phoenix experiment not initialized; cannot flush runs.")
        still_pending: list[dict[str, Any]] = []
        for entry in list(self._pending_runs):
            payload = dict(entry["payload"])
            if payload.get("experiment_id") == "pending":
                payload = {**payload, "experiment_id": self._remote_experiment_id}
            try:
                response = self._http.post(
                    f"v1/experiments/{self._remote_experiment_id}/runs",
                    json=payload,
                    timeout=30,
                )
                response.raise_for_status()
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                raise RuntimeError(f"Failed to submit Phoenix run payload: {exc}") from exc
            remote_run_id = response.json().get("data", {}).get("id")
            if remote_run_id:
                self._run_id_map[entry["local_run_id"]] = remote_run_id
                result = self._results_by_run_id.get(str(entry["local_run_id"]))
                if result is not None:
                    result.metadata.setdefault("phoenix_run_id", remote_run_id)
                    result.metadata.setdefault("remote_run_id", remote_run_id)

        self._pending_runs = still_pending

    def _iso_or_metadata(self, dt: datetime | None, fallback: Any) -> str:
        if isinstance(dt, datetime):
            return dt.astimezone(timezone.utc).isoformat()
        if isinstance(fallback, str):
            return fallback
        return datetime.now(timezone.utc).isoformat()

    def _prepare_example_id_mapping(self, examples: list[DatasetExample]) -> None:
        """Align local DatasetExample IDs with the remote dataset to avoid 404s."""
        try:
            remote_examples = self._fetch_dataset_examples()
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            raise RuntimeError(f"Failed to fetch Phoenix dataset examples: {exc}") from exc

        if not remote_examples:
            return

        signature_to_id: dict[tuple[str, str], str] = {}
        for remote in remote_examples:
            if remote.id is None:
                continue
            signature = self._example_signature(remote)
            signature_to_id.setdefault(signature, str(remote.id))

        mapping: dict[str, str] = {}
        for local in examples:
            local_id = getattr(local, "id", None)
            if not local_id:
                continue
            signature = self._example_signature(local)
            remote_id = signature_to_id.get(signature)
            if remote_id:
                mapping[str(local_id)] = remote_id

        if len(mapping) < len(examples) and len(remote_examples) == len(examples):
            for local, remote in zip(examples, remote_examples):
                if getattr(local, "id", None) and getattr(remote, "id", None):
                    mapping.setdefault(str(local.id), str(remote.id))

        if mapping:
            self._example_id_map = mapping

    def _fetch_dataset_examples(self) -> list[DatasetExample]:
        """Fetch dataset examples (respecting version) to recover remote IDs."""
        if not self._dataset_id:
            return []

        try:
            dataset = self._client.datasets.get_dataset(  # type: ignore[attr-defined]
                dataset=self._dataset_id, version_id=self._dataset_version_id, timeout=30
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch Phoenix dataset examples: {exc}") from exc

        examples: list[DatasetExample] = []
        for entry in getattr(dataset, "examples", []) or []:
            examples.append(
                DatasetExample(
                    input=dict(entry.get("input", {}) or {}),
                    output=dict(entry.get("output", {}) or {}),
                    metadata=dict(entry.get("metadata", {}) or {}),
                    id=entry.get("id"),
                    created_at=entry.get("created_at"),
                    updated_at=entry.get("updated_at"),
                )
            )
        return examples

    @staticmethod
    def _example_signature(example: DatasetExample) -> tuple[str, str]:
        """Stable signature combining input/output for mapping across sources."""
        safe_input = _ensure_json_safe(getattr(example, "input", {}) or {})
        safe_output = _ensure_json_safe(getattr(example, "output", {}) or {})
        return (
            json.dumps(safe_input, sort_keys=True, ensure_ascii=False),
            json.dumps(safe_output, sort_keys=True, ensure_ascii=False),
        )


def _ensure_json_safe(value: Any) -> Any:
    """Recursively convert values so they can be JSON serialized."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return {str(k): _ensure_json_safe(v) for k, v in value.items()}
    if isinstance(value, Iterable):
        return [_ensure_json_safe(v) for v in value]
    return repr(value)
