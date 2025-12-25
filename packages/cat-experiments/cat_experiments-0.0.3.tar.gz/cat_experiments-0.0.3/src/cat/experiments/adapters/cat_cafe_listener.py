"""Cat Cafe listener that syncs cat-experiments experiments to CAT Cafe server."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Callable, Protocol, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from cat.cafe.client import CATCafeClient
    from cat.cafe.client import Experiment as CatCafeExperiment
    from cat.cafe.client import ExperimentResult as CatCafeExperimentResult
else:  # pragma: no cover - exercised indirectly via tests
    try:
        from cat.cafe.client import CATCafeClient
        from cat.cafe.client import Experiment as CatCafeExperiment
        from cat.cafe.client import ExperimentResult as CatCafeExperimentResult
    except ModuleNotFoundError as exc:  # pragma: no cover - fallback activated in unit tests
        missing = exc.name or ""
        if "cat" not in missing and "cafe" not in missing:
            raise

        @runtime_checkable
        class CATCafeClient(Protocol):
            """Minimal protocol for CAT Cafe client interactions."""

            def start_experiment(self, experiment_config: "CatCafeExperiment") -> str: ...

            def create_run(self, experiment_id: str, payload: dict[str, Any]) -> dict[str, Any]: ...

            def append_evaluation(
                self, experiment_id: str, run_id: str, payload: dict[str, Any]
            ) -> dict[str, Any]: ...

            def complete_experiment(self, experiment_id: str, summary: dict[str, Any]) -> None: ...

        @dataclass
        class CatCafeExperiment:
            """Lightweight representation used when the SDK is unavailable."""

            name: str
            description: str
            dataset_id: str
            dataset_version: str | None = None
            tags: list[str] = field(default_factory=list)
            metadata: dict[str, Any] = field(default_factory=dict)

        @dataclass
        class CatCafeExperimentResult:
            """Local stand-in for cat.cafe.client.ExperimentResult."""

            run_id: str
            example_id: str
            repetition_number: int
            input_data: dict[str, Any]
            output: dict[str, Any] | None
            actual_output: dict[str, Any] | str
            evaluation_scores: dict[str, float | int | None] = field(default_factory=dict)
            evaluator_metadata: dict[str, dict[str, Any]] = field(default_factory=dict)
            metadata: dict[str, Any] = field(default_factory=dict)
            trace_id: str | None = None
            error: str | None = None
            execution_time_ms: float | int | None = None
            evaluator_execution_times_ms: dict[str, float | int | None] = field(
                default_factory=dict
            )


from cat.experiments.listeners import ExperimentListener
from cat.experiments.models import DatasetExample

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from cat.experiments.experiments import ExperimentConfig, ExperimentResult, ExperimentSummary

logger = logging.getLogger(__name__)


@dataclass
class CatCafeRunSubmission:
    """Run payload plus evaluator events to stream to CAT Cafe."""

    run: dict[str, Any]
    evaluations: list[dict[str, Any]]


def _normalize_actual_output(actual_output: Any) -> str | dict[str, Any]:
    """Coerce actual output into a JSON-safe form for CAT Cafe."""
    if isinstance(actual_output, dict):
        return actual_output
    if isinstance(actual_output, str):
        return actual_output
    return "" if actual_output is None else repr(actual_output)


def _extract_evaluator_execution_times(result: "ExperimentResult") -> dict[str, float]:
    """Parse evaluator execution times from metadata, tolerating missing/invalid data."""
    evaluator_execution_times: dict[str, float] = {}
    for name, metadata in result.evaluator_metadata.items():
        try:
            evaluator_execution_times[name] = float(metadata.get("execution_time_ms", 0.0))
        except (TypeError, ValueError):
            evaluator_execution_times[name] = 0.0
    return evaluator_execution_times


def build_run_payload(result: "ExperimentResult") -> dict[str, Any]:
    """Convert an experiment result into a run payload for the streaming API."""
    run_id = result.run_id or f"{result.example_id}-rep-{result.repetition_number}"
    evaluator_execution_times = _extract_evaluator_execution_times(result)

    metadata = dict(result.metadata)
    if result.started_at:
        metadata.setdefault("started_at", result.started_at.isoformat())
    if result.completed_at:
        metadata.setdefault("completed_at", result.completed_at.isoformat())
    metadata.setdefault("run_id", run_id)
    metadata.setdefault("repetition_number", result.repetition_number)
    if result.execution_time_ms is not None:
        metadata.setdefault("execution_time_ms", result.execution_time_ms)
    if evaluator_execution_times:
        metadata.setdefault("evaluator_execution_times_ms", dict(evaluator_execution_times))
    if result.error:
        metadata.setdefault("error", result.error)

    return {
        "run_id": run_id,
        "example_id": result.example_id,
        "repetition_number": result.repetition_number,
        "input_data": dict(result.input_data or {}),
        "output": dict(result.output or {}),
        "actual_output": _normalize_actual_output(result.actual_output),
        "trace_id": result.trace_id,
        "started_at": result.started_at.isoformat() if result.started_at else None,
        "completed_at": result.completed_at.isoformat() if result.completed_at else None,
        "execution_time_ms": result.execution_time_ms,
        "metadata": metadata,
    }


def build_evaluation_payloads(result: "ExperimentResult") -> list[dict[str, Any]]:
    """Build evaluation events for the streaming API."""
    payloads: list[dict[str, Any]] = []
    evaluator_names = set(result.evaluation_scores.keys()) | set(result.evaluator_metadata.keys())

    for evaluator_name in evaluator_names:
        meta = dict(result.evaluator_metadata.get(evaluator_name, {}))
        payload = {
            "evaluator_name": evaluator_name,
            "score": result.evaluation_scores.get(evaluator_name),
            "label": meta.pop("label", None),
            "explanation": meta.pop("explanation", None),
            "metadata": meta,
            "trace_id": meta.pop("trace_id", result.trace_id),
            "started_at": meta.pop("started_at", None),
            "completed_at": meta.pop("completed_at", None),
            "error": meta.pop("error", None),
        }
        payloads.append(payload)

    return payloads


def convert_result_to_cat_cafe(result: "ExperimentResult") -> CatCafeExperimentResult:
    """Legacy converter kept for compatibility with older CAT Cafe APIs."""
    evaluator_execution_times = _extract_evaluator_execution_times(result)
    metadata = dict(result.metadata)
    if result.started_at:
        metadata.setdefault("started_at", result.started_at.isoformat())
    if result.completed_at:
        metadata.setdefault("completed_at", result.completed_at.isoformat())
    run_id = result.run_id or f"{result.example_id}-rep-{result.repetition_number}"
    metadata.setdefault("run_id", run_id)
    if result.execution_time_ms is not None:
        metadata.setdefault("execution_time_ms", result.execution_time_ms)
    if evaluator_execution_times:
        metadata.setdefault("evaluator_execution_times_ms", dict(evaluator_execution_times))
    if result.error:
        metadata.setdefault("error", result.error)

    converted = CatCafeExperimentResult(
        run_id=run_id,
        example_id=result.example_id,
        repetition_number=result.repetition_number,
        input_data=dict(result.input_data or {}),
        output=dict(result.output or {}),
        actual_output=_normalize_actual_output(result.actual_output),
        evaluation_scores=dict(result.evaluation_scores),
        evaluator_metadata={name: dict(meta) for name, meta in result.evaluator_metadata.items()},
        metadata=metadata,
        trace_id=result.trace_id,
        error=result.error,
        execution_time_ms=result.execution_time_ms,
        evaluator_execution_times_ms=evaluator_execution_times,
    )

    setattr(converted, "evaluator_execution_times", evaluator_execution_times)
    # Ensure run_id attribute exists for SDKs that serialize it
    try:
        setattr(converted, "run_id", result.run_id)
    except Exception:
        pass
    return converted


@dataclass
class CatCafeSyncConfig:
    """Configuration placeholder for syncing cat-experiments runs to CAT Cafe."""


class CatCafeExperimentListener(ExperimentListener):
    """Listener that mirrors cat-experiments experiment runs into CAT Cafe."""

    def __init__(
        self,
        client: CATCafeClient,
        *,
        config: CatCafeSyncConfig | None = None,
    ) -> None:
        self._client = client
        self._config = config or CatCafeSyncConfig()

        self._server_experiment_id: str | None = None
        self._pending_runs: list[CatCafeRunSubmission] = []
        self._pending_keys: set[tuple[str, str]] = set()
        self._submitted_runs: set[tuple[str, str]] = set()
        self._experiment_started_at: datetime | None = None
        self._config_snapshot: ExperimentConfig | None = None
        self._results_by_run_id: dict[str, ExperimentResult] = {}
        self._run_id_map: dict[str, str] = {}
        self._example_id_map: dict[str, str] = {}
        self._dataset_id: str | None = None
        self._dataset_version_id: str | None = None

    # ------------------------------------------------------------------ #
    # ExperimentListener interface
    # ------------------------------------------------------------------ #
    def on_experiment_started(
        self,
        experiment_id: str,
        config: ExperimentConfig,
        examples,
    ) -> None:
        if not config.dataset_id:
            raise ValueError(
                "CatCafeExperimentListener requires ExperimentConfig.dataset_id to be set."
            )

        self._config_snapshot = config
        self._experiment_started_at = datetime.now(timezone.utc)
        self._pending_runs.clear()
        self._pending_keys.clear()
        self._submitted_runs.clear()
        self._results_by_run_id = {}
        self._run_id_map = {}
        self._example_id_map = {}
        self._dataset_id = None
        self._dataset_version_id = None
        self._example_id_map = {}
        self._dataset_id = config.dataset_id
        self._dataset_version_id = config.dataset_version_id
        cat_experiment = CatCafeExperiment(
            name=config.name,
            description=config.description,
            dataset_id=config.dataset_id,
            dataset_version=config.dataset_version_id,
            tags=list(config.tags),
            metadata=dict(config.metadata),
        )

        try:
            self._server_experiment_id = self._client.start_experiment(cat_experiment)
        except Exception as exc:
            raise RuntimeError(f"Failed to start CAT Cafe experiment: {exc}") from exc
        if self._server_experiment_id:
            config.metadata.setdefault("remote_experiment_id", self._server_experiment_id)
            config.metadata.setdefault("cat_cafe_experiment_id", self._server_experiment_id)
        self._prepare_example_id_mapping(examples)

    def on_task_completed(
        self,
        experiment_id: str,
        result: ExperimentResult,
    ) -> None:
        if result.run_id:
            self._results_by_run_id[result.run_id] = result
        if self._server_experiment_id:
            result.metadata.setdefault("cat_cafe_experiment_id", self._server_experiment_id)
            result.metadata.setdefault("experiment_id", self._server_experiment_id)
            result.metadata.setdefault("remote_experiment_id", self._server_experiment_id)

        submission = self._build_submission(result)

        # Always send the run immediately when possible.
        if self._server_experiment_id:
            success, remote_run_id = self._submit_run(self._server_experiment_id, submission)
            if success:
                if remote_run_id:
                    result.metadata.setdefault("cat_cafe_run_id", remote_run_id)
                    result.metadata.setdefault("remote_run_id", remote_run_id)
                    self._run_id_map[result.run_id] = remote_run_id
            else:
                self._queue_submission(submission)
        else:
            self._queue_submission(submission)

    def on_task_evaluated(
        self,
        experiment_id: str,
        result: ExperimentResult,
    ) -> None:
        """No-op; evaluations are synced during experiment completion."""
        return

    def on_aggregate_completed(
        self,
        experiment_id: str,
        aggregate_scores: dict[str, float],
        aggregate_metadata: dict[str, dict[str, object]],
    ) -> None:
        """No-op hook; aggregate metrics are included with the final summary submission."""
        return

    def on_experiment_completed(
        self,
        experiment_id: str,
        results: list[ExperimentResult],
        summary: ExperimentSummary,
    ) -> None:
        if not self._server_experiment_id:
            raise RuntimeError("CAT Cafe experiment missing remote id; cannot complete.")
        server_experiment_id = str(self._server_experiment_id)

        # Ensure all runs are queued in case some weren't seen via on_task_completed
        for res in results:
            self._queue_submission(self._build_submission(res))

        summary.aggregate_metadata.setdefault("cat_cafe", {"experiment_id": server_experiment_id})
        summary.aggregate_metadata.setdefault("remote", {"experiment_id": server_experiment_id})

        # First, flush runs to ensure they exist before evaluations are sent.
        if not self._flush_pending_runs():
            return

        # Next, flush evaluations (for runs that are now present server-side).
        evaluations = self._build_evaluations(results, server_experiment_id)
        for item in evaluations:
            experiment_id_value = item.get("experiment_id")
            run_id_value = item.get("run_id")
            if not isinstance(experiment_id_value, str) or not isinstance(run_id_value, str):
                continue
            experiment_id = experiment_id_value
            run_id = run_id_value
            payload = item.get("payload", {})
            local_run_id = item.get("local_run_id")
            evaluator_name = item.get("evaluator_name")
            try:
                response = self._client.append_evaluation(experiment_id, run_id, payload)
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to sync CAT Cafe evaluation for run {run_id}: {exc}"
                ) from exc

            remote_eval_id = None
            try:
                if isinstance(response, dict):
                    remote_eval_id = response.get("id") or response.get("evaluation_id")
                elif hasattr(response, "id"):
                    remote_eval_id = getattr(response, "id", None)
            except Exception:
                remote_eval_id = None

            if remote_eval_id and local_run_id and evaluator_name:
                result = self._results_by_run_id.get(str(local_run_id))
                if result is not None:
                    meta = result.evaluator_metadata.setdefault(evaluator_name, {})
                    meta.setdefault("cat_cafe_evaluation_id", remote_eval_id)
                    meta.setdefault("remote_evaluation_id", remote_eval_id)
                    meta.setdefault("experiment_id", self._server_experiment_id)

        summary_payload = self._build_summary_payload(summary)
        try:
            self._client.complete_experiment(server_experiment_id, summary_payload)
        except Exception as exc:
            raise RuntimeError(f"Failed to mark CAT Cafe experiment complete: {exc}") from exc

        self._pending_runs.clear()
        self._pending_keys.clear()
        self._submitted_runs.clear()
        self._results_by_run_id = {}
        self._run_id_map = {}

    def on_experiment_failed(
        self,
        experiment_id: str,
        error: str,
    ) -> None:
        if not self._server_experiment_id:
            raise RuntimeError(f"Experiment failed before CAT Cafe registration: {error}")
        self._flush_pending_runs()
        failure_summary = {
            "status": "failed",
            "error": error,
            "partial_results_count": len(self._submitted_runs),
        }
        try:
            self._client.complete_experiment(self._server_experiment_id, failure_summary)
        except Exception as exc:
            raise RuntimeError(f"Failed to notify CAT Cafe of failure: {exc}") from exc
        finally:
            self._pending_runs.clear()
            self._pending_keys.clear()
            self._submitted_runs.clear()
            self._results_by_run_id = {}
            self._run_id_map = {}
            self._example_id_map = {}
            self._dataset_id = None
            self._dataset_version_id = None

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _build_submission(self, result: ExperimentResult) -> CatCafeRunSubmission:
        run_payload = build_run_payload(result)
        mapped_example_id = self._example_id_map.get(str(run_payload.get("example_id")))
        if mapped_example_id:
            run_payload["example_id"] = mapped_example_id
            run_payload["metadata"]["example_id"] = mapped_example_id
        return CatCafeRunSubmission(
            run=run_payload,
            evaluations=build_evaluation_payloads(result),
        )

    def _queue_submission(self, submission: CatCafeRunSubmission) -> None:
        key = self._run_key(submission.run)
        if key in self._submitted_runs or key in self._pending_keys:
            return
        self._pending_keys.add(key)
        self._pending_runs.append(submission)

    def _submit_run(
        self, experiment_id: str, submission: CatCafeRunSubmission
    ) -> tuple[bool, str | None]:
        run_id = submission.run.get("run_id")
        try:
            response = self._client.create_run(experiment_id, submission.run)
        except Exception as exc:
            raise RuntimeError(f"Failed to sync CAT Cafe run {run_id}: {exc}") from exc

        remote_run_id = None
        try:
            if isinstance(response, dict):
                remote_run_id = (
                    response.get("id") or response.get("run_id") or response.get("runId")
                )
            elif hasattr(response, "id"):
                remote_run_id = getattr(response, "id", None)
            elif hasattr(response, "run_id"):
                remote_run_id = getattr(response, "run_id", None)
        except Exception:
            remote_run_id = None

        key = self._run_key(submission.run)
        self._submitted_runs.add(key)
        self._pending_keys.discard(key)
        return True, remote_run_id

    def _flush_pending_runs(self) -> bool:
        if not self._server_experiment_id:
            raise RuntimeError("CAT Cafe experiment was never started; unable to sync results.")

        remaining: list[CatCafeRunSubmission] = []
        for submission in list(self._pending_runs):
            success, remote_run_id = self._submit_run(self._server_experiment_id, submission)
            if not success:
                remaining.append(submission)
                continue

            # Run was accepted; queue its evaluations for later flush.
            if remote_run_id:
                run_id = submission.run.get("run_id")
                if run_id is not None:
                    run_id_str = str(run_id)
                    self._run_id_map[run_id_str] = remote_run_id
                    result = self._results_by_run_id.get(run_id_str)
                    if result is not None:
                        result.metadata.setdefault("cat_cafe_run_id", remote_run_id)
                        result.metadata.setdefault("remote_run_id", remote_run_id)

        self._pending_runs = remaining
        return not remaining

    def _decorate_evaluations(
        self, experiment_id: str, submission: CatCafeRunSubmission
    ) -> list[dict[str, Any]]:
        run_id = submission.run.get("run_id")
        local_run_id = str(run_id) if run_id is not None else ""
        remote_run_id = self._run_id_map.get(local_run_id, local_run_id)
        return [
            {
                "experiment_id": experiment_id,
                "run_id": remote_run_id,
                "payload": evaluation,
                "local_run_id": local_run_id,
                "evaluator_name": evaluation.get("evaluator_name"),
            }
            for evaluation in submission.evaluations
        ]

    def _build_evaluations(
        self, results: list["ExperimentResult"], experiment_id: str
    ) -> list[dict[str, Any]]:
        evaluations: list[dict[str, Any]] = []
        for result in results:
            submission = self._build_submission(result)
            run_id = submission.run.get("run_id")
            local_run_id = str(run_id) if run_id is not None else ""
            remote_run_id = self._run_id_map.get(local_run_id, local_run_id)
            decorated = self._decorate_evaluations(experiment_id, submission)
            for item in decorated:
                item["run_id"] = remote_run_id
                item["local_run_id"] = local_run_id
                evaluations.append(item)
        return evaluations

    @staticmethod
    def _run_key(run_payload: dict[str, Any]) -> tuple[str, str]:
        example_id = run_payload.get("example_id")
        run_id = run_payload.get("run_id")
        return (
            str(example_id) if example_id is not None else "",
            str(run_id) if run_id is not None else "",
        )

    def _build_summary_payload(self, summary: ExperimentSummary) -> dict[str, Any]:
        payload = {
            "total_examples": summary.total_examples,
            "successful_examples": summary.successful_examples,
            "failed_examples": summary.failed_examples,
            "average_scores": dict(summary.average_scores),
            "aggregate_scores": dict(summary.aggregate_scores),
            "aggregate_metadata": dict(summary.aggregate_metadata),
        }
        if summary.started_at:
            payload["started_at"] = summary.started_at.isoformat()
        if summary.completed_at:
            payload["completed_at"] = summary.completed_at.isoformat()
        if self._experiment_started_at:
            payload.setdefault("listener_started_at", self._experiment_started_at.isoformat())
        return payload

    def _prepare_example_id_mapping(self, examples: list[DatasetExample]) -> None:
        """Align local DatasetExample IDs with the remote dataset to avoid 404s."""
        if not self._dataset_id:
            return

        try:
            remote_examples = self._fetch_dataset_examples()
        except Exception:
            remote_examples = []

        if not remote_examples:
            # Fallback: use provided example IDs directly if present
            self._example_id_map = {
                str(ex.id): str(ex.id) for ex in examples if getattr(ex, "id", None)
            }
            return

        signature_to_id: dict[tuple[str, str], str] = {}
        for remote in remote_examples:
            remote_id = getattr(remote, "id", None)
            if remote_id is None:
                continue
            signature_to_id.setdefault(self._example_signature(remote), str(remote_id))

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
        dataset_id = str(self._dataset_id)
        fetcher: Callable[[], Any] | None = None
        if hasattr(self._client, "datasets") and hasattr(self._client.datasets, "get"):  # type: ignore[attr-defined]

            def _fetch_dataset() -> Any:
                return self._client.datasets.get(  # type: ignore[attr-defined]
                    dataset=dataset_id, version=self._dataset_version_id, timeout=30
                )

            fetcher = _fetch_dataset
        elif hasattr(self._client, "get_dataset"):

            def _fetch_dataset() -> Any:
                return self._client.get_dataset(dataset_id, version=self._dataset_version_id)  # type: ignore[attr-defined]

            fetcher = _fetch_dataset

        if not fetcher:
            return []

        dataset = fetcher()
        examples: list[DatasetExample] = []
        for entry in getattr(dataset, "examples", []) or []:
            examples.append(
                DatasetExample(
                    input=dict(
                        getattr(entry, "input", {}) or getattr(entry, "input_data", {}) or {}
                    ),
                    output=dict(getattr(entry, "output", {}) or {}),
                    metadata=dict(getattr(entry, "metadata", {}) or {}),
                    id=getattr(entry, "id", None),
                )
            )
        return examples

    @staticmethod
    def _example_signature(example: DatasetExample) -> tuple[str, str]:
        """Stable signature combining input/output for mapping across sources."""
        safe_input = getattr(example, "input", {}) or getattr(example, "input_data", {}) or {}
        safe_output = getattr(example, "output", {}) or {}
        return (
            json.dumps(safe_input, sort_keys=True, ensure_ascii=False),
            json.dumps(safe_output, sort_keys=True, ensure_ascii=False),
        )
