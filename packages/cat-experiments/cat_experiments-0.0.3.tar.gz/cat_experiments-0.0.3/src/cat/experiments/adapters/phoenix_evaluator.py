"""Evaluation backend that rehydrates Phoenix experiment runs for new evaluators."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, Mapping

try:  # pragma: no cover - dependency guard
    import httpx
except ImportError as exc:  # pragma: no cover - runtime safeguard
    raise ImportError(
        "Phoenix integration requires the optional 'httpx' dependency. "
        "Install cat-experiments[phoenix] or `pip install httpx` to enable it."
    ) from exc

from ..evaluation_backends import EvaluationBackend
from ..experiments import ExperimentConfig, ExperimentResult, ExperimentSummary
from ..listeners import ExperimentListener
from ..models import DatasetExample
from ..serde import deserialize_datetime, serialize_datetime
from ..types import EvaluatorFn
from .local_storage import build_local_runner, build_local_runner_async
from .phoenix_resume import PhoenixResumeCoordinator

if TYPE_CHECKING:  # pragma: no cover - optional dependency
    from phoenix.client import Client as PhoenixClient
else:  # pragma: no cover
    PhoenixClient = Any  # type: ignore[misc,assignment]

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..experiments import ExperimentRunner


@dataclass
class PhoenixEvaluationPlan:
    experiment_id: str
    config: ExperimentConfig
    dataset_examples: list[DatasetExample]
    results: list[ExperimentResult]
    summary: ExperimentSummary | None = None


class PhoenixEvaluationCoordinator(EvaluationBackend):
    """Fetches task runs from Phoenix and submits new evaluation results."""

    def __init__(self, client: PhoenixClient, *, http_timeout: int = 60) -> None:
        self._client = client
        self._http: httpx.Client = getattr(client, "_client")
        self._http_timeout = http_timeout

    def build_plan(self, experiment_id: str) -> PhoenixEvaluationPlan:
        experiment = self._client.experiments.get(experiment_id=experiment_id)

        dataset_id = experiment.get("dataset_id")
        dataset_version_id = experiment.get("dataset_version_id")
        if not dataset_id:
            raise ValueError("Phoenix experiment missing dataset_id")

        config = ExperimentConfig(
            name=experiment.get("name") or f"phoenix-{experiment_id}",
            description=experiment.get("description", ""),
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            repetitions=int(experiment.get("repetitions") or 1),
            project_name=experiment.get("project_name"),
            metadata=dict(experiment.get("metadata") or {}),
            tags=list(experiment.get("tags") or []),
        )
        config.metadata.setdefault("phoenix_experiment_id", experiment_id)

        examples = self._fetch_dataset_examples(dataset_id, dataset_version_id)
        example_map: dict[str, DatasetExample] = {
            str(ex.id): ex for ex in examples if ex.id is not None
        }

        runs = self._fetch_runs(experiment_id)
        results: list[ExperimentResult] = []
        for payload in runs:
            example_id = payload.get("dataset_example_id")
            example_key = str(example_id) if example_id is not None else None
            if example_key is None:
                continue
            example = example_map.get(example_key)
            if not example:
                continue
            results.append(self._run_to_result(payload, example))

        if not results:
            raise ValueError("Phoenix experiment has no recorded runs to evaluate")

        return PhoenixEvaluationPlan(
            experiment_id=experiment_id,
            config=config,
            dataset_examples=list(example_map.values()),
            results=results,
        )

    def fetch_experiment(self, experiment_id: str) -> PhoenixEvaluationPlan:
        """Return Phoenix runs and metadata without mutating remote state."""
        return self.build_plan(experiment_id)

    def run_evaluators(
        self,
        *,
        experiment_id: str,
        evaluators: list[EvaluatorFn],
        submit: bool = True,
        runner: ExperimentRunner | None = None,
    ) -> list[ExperimentResult]:
        from ..experiments import ExperimentRunner

        runner = runner or ExperimentRunner()
        return runner.rerun_evaluators(
            experiment_id=experiment_id,
            evaluators=evaluators,
            backend=self,
            persist=submit,
        )

    def persist_results(self, plan: PhoenixEvaluationPlan) -> None:
        for payload in self._build_evaluation_payloads(plan.results):
            response = self._http.post(
                "v1/experiment_evaluations",
                json=payload,
                timeout=self._http_timeout,
            )
            response.raise_for_status()

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _fetch_dataset_examples(
        self,
        dataset_id: str,
        dataset_version_id: str | None,
    ) -> list[DatasetExample]:
        """Fetch dataset examples via phoenix-client (preferred) with HTTP fallback."""
        examples_data: list[Any] = []

        datasets = getattr(self._client, "datasets", None)
        get_dataset = getattr(datasets, "get_dataset", None) if datasets else None
        if callable(get_dataset):
            dataset = get_dataset(
                dataset=dataset_id,
                version_id=dataset_version_id,
                timeout=self._http_timeout,
            )
            examples_data = getattr(dataset, "examples", None) or []
            if not examples_data and isinstance(dataset, Mapping):
                examples_data = dataset.get("examples", []) or []
        else:
            params = {"version_id": dataset_version_id} if dataset_version_id else {}

            info_resp = self._http.get(
                f"v1/datasets/{dataset_id}",
                params=params,
                timeout=self._http_timeout,
            )
            info_resp.raise_for_status()

            examples_resp = self._http.get(
                f"v1/datasets/{dataset_id}/examples",
                params=params,
                timeout=self._http_timeout,
            )
            examples_resp.raise_for_status()
            examples_data = examples_resp.json().get("data", [])

        return [PhoenixResumeCoordinator._to_dataset_example(ex) for ex in examples_data]

    def _fetch_runs(self, experiment_id: str) -> list[dict[str, Any]]:
        # Prefer the JSON export endpoint because it includes evaluations/annotations.
        try:
            json_resp = self._http.get(
                f"v1/experiments/{experiment_id}/json",
                timeout=self._http_timeout,
            )
            json_resp.raise_for_status()
            runs_data = json_resp.json()
            # The JSON endpoint returns a list, not wrapped in {"data": ...}
            if isinstance(runs_data, list) and runs_data:
                normalized: list[dict[str, Any]] = []
                for idx, run in enumerate(runs_data):
                    normalized.append(
                        {
                            "id": run.get("id") or run.get("trace_id") or f"run-{idx}",
                            "dataset_example_id": run.get("example_id")
                            or run.get("dataset_example_id"),
                            "repetition_number": run.get("repetition_number"),
                            "start_time": run.get("start_time"),
                            "end_time": run.get("end_time"),
                            "output": run.get("output"),
                            "trace_id": run.get("trace_id"),
                            "error": run.get("error"),
                            "evaluations": run.get("annotations") or [],
                        }
                    )
                return normalized
        except httpx.HTTPError:
            # Fall back to the paginated runs endpoint below.
            pass

        runs: list[dict[str, Any]] = []
        cursor: str | None = None

        while True:
            params: dict[str, Any] = {"limit": 100}
            if cursor:
                params["cursor"] = cursor

            response = self._http.get(
                f"v1/experiments/{experiment_id}/runs",
                params=params,
                timeout=self._http_timeout,
            )
            response.raise_for_status()
            body = response.json()
            runs.extend(body.get("data", []))
            cursor = body.get("next_cursor")
            if not cursor:
                break

        return runs

    def _run_to_result(
        self, payload: Mapping[str, Any], example: DatasetExample
    ) -> ExperimentResult:
        experiment_example_id = (
            example.id if example.id is not None else str(payload.get("dataset_example_id"))
        )
        run_id = payload.get("id") or experiment_example_id

        # Collect any evaluations/annotations and attach to scores/metadata.
        evaluation_scores: dict[str, float] = {}
        evaluator_metadata: dict[str, dict[str, Any]] = {}
        for evaluation in payload.get("evaluations", []) or payload.get("annotations", []):
            name = evaluation.get("name") or "unknown"
            score = evaluation.get("score")
            if score is not None:
                evaluation_scores[name] = score
            meta = evaluator_metadata.setdefault(name, {})
            for key in (
                "label",
                "explanation",
                "annotator_kind",
                "trace_id",
                "error",
                "metadata",
            ):
                value = evaluation.get(key)
                if value is not None:
                    meta[key] = value
            if evaluation.get("start_time"):
                meta["started_at"] = evaluation["start_time"]
            if evaluation.get("end_time"):
                meta["completed_at"] = evaluation["end_time"]

        return ExperimentResult(
            example_id=str(experiment_example_id),
            run_id=str(run_id),
            repetition_number=int(payload.get("repetition_number") or 1),
            started_at=deserialize_datetime(payload.get("start_time")),
            completed_at=deserialize_datetime(payload.get("end_time")),
            input_data=dict(example.input),
            output=dict(example.output),
            actual_output=payload.get("output"),
            evaluation_scores=evaluation_scores,
            evaluator_metadata=evaluator_metadata,
            metadata={
                "trace_id": payload.get("trace_id"),
                "error": payload.get("error"),
            },
            trace_id=payload.get("trace_id"),
            error=payload.get("error"),
            execution_time_ms=None,
        )

    def _build_evaluation_payloads(self, results: list[ExperimentResult]) -> list[dict[str, Any]]:
        payloads: list[dict[str, Any]] = []
        for run in results:
            for metric_name, score in run.evaluation_scores.items():
                metadata = dict(run.evaluator_metadata.get(metric_name, {}))
                evaluator_result: dict[str, Any] = {}
                if score is not None:
                    evaluator_result["score"] = score
                label = metadata.get("label")
                if label is not None:
                    evaluator_result["label"] = label
                explanation = metadata.get("explanation")
                if explanation is not None:
                    evaluator_result["explanation"] = explanation

                started_at = metadata.get("started_at") or serialize_datetime(run.started_at)
                completed_at = metadata.get("completed_at") or serialize_datetime(run.completed_at)
                annotator_kind = metadata.get("annotator_kind", "CODE")
                trace_id = metadata.get("trace_id") or run.trace_id

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

                payloads.append(
                    {
                        "experiment_id": run.metadata.get("phoenix_experiment_id")
                        or run.metadata.get("experiment_id"),
                        "run_id": run.run_id,
                        "experiment_run_id": run.run_id,
                        "dataset_example_id": run.example_id,
                        "repetition_number": run.repetition_number,
                        "name": metric_name,
                        "trace_id": trace_id,
                        "experiment_trace_id": run.trace_id,
                        "evaluator": {
                            "name": metric_name,
                            "annotator_kind": annotator_kind,
                            "timestamp": serialize_datetime(run.completed_at),
                            "started_at": started_at,
                            "completed_at": completed_at,
                        },
                        "metrics": evaluator_result,
                        "metadata": metadata_payload,
                    }
                )

        return payloads


def build_phoenix_runner(
    *,
    client: PhoenixClient | None = None,
    base_url: str | None = None,
    project_name: str | None = None,
    storage_dir: str | Path | None = None,
    clean_on_success: bool = False,
    listeners: Iterable[ExperimentListener] | None = None,
    enable_logging: bool = False,
) -> ExperimentRunner:
    """Create a runner configured with PhoenixExperimentListener."""

    if client is None:
        try:
            from phoenix.client import Client as PhoenixClient  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "phoenix-client must be installed to build a Phoenix runner."
            ) from exc

        client_kwargs: dict[str, Any] = {}
        if base_url is not None:
            client_kwargs["base_url"] = base_url
        client = PhoenixClient(**client_kwargs)

    from .phoenix_listener import PhoenixExperimentListener, PhoenixSyncConfig

    sync_config = PhoenixSyncConfig(project_name=project_name)

    runner = build_local_runner(
        storage_dir=storage_dir,
        clean_on_success=clean_on_success,
        listeners=listeners,
        enable_logging=enable_logging,
    )
    runner.add_listener(PhoenixExperimentListener(client, config=sync_config))
    return runner


def build_phoenix_runner_async(
    *,
    client: PhoenixClient | None = None,
    base_url: str | None = None,
    project_name: str | None = None,
    storage_dir: str | Path | None = None,
    clean_on_success: bool = False,
    listeners: Iterable[ExperimentListener] | None = None,
    enable_logging: bool = False,
):
    """Create an AsyncExperimentRunner configured with PhoenixExperimentListener."""

    if client is None:
        try:
            from phoenix.client import Client as PhoenixClient  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "phoenix-client must be installed to build a Phoenix runner."
            ) from exc

        client_kwargs: dict[str, Any] = {}
        if base_url is not None:
            client_kwargs["base_url"] = base_url
        client = PhoenixClient(**client_kwargs)

    from .phoenix_listener import PhoenixExperimentListener, PhoenixSyncConfig

    sync_config = PhoenixSyncConfig(project_name=project_name)

    runner = build_local_runner_async(
        storage_dir=storage_dir,
        clean_on_success=clean_on_success,
        listeners=listeners,
        enable_logging=enable_logging,
    )
    runner.add_listener(PhoenixExperimentListener(client, config=sync_config))
    return runner

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _fetch_dataset_examples(
        self,
        dataset_id: str,
        dataset_version_id: str | None,
    ) -> list[DatasetExample]:
        params = {"version_id": dataset_version_id} if dataset_version_id else {}

        info_resp = self._http.get(
            f"v1/datasets/{dataset_id}",
            params=params,
            timeout=self._http_timeout,
        )
        info_resp.raise_for_status()

        examples_resp = self._http.get(
            f"v1/datasets/{dataset_id}/examples",
            params=params,
            timeout=self._http_timeout,
        )
        examples_resp.raise_for_status()
        examples_data = examples_resp.json().get("data", [])
        return [PhoenixResumeCoordinator._to_dataset_example(ex) for ex in examples_data]

    def _fetch_runs(self, experiment_id: str) -> list[dict[str, Any]]:
        runs: list[dict[str, Any]] = []
        cursor: str | None = None

        while True:
            params: dict[str, Any] = {"limit": 100}
            if cursor:
                params["cursor"] = cursor

            response = self._http.get(
                f"v1/experiments/{experiment_id}/runs",
                params=params,
                timeout=self._http_timeout,
            )
            response.raise_for_status()
            body = response.json()
            runs.extend(body.get("data", []))
            cursor = body.get("next_cursor")
            if not cursor:
                break

        return runs

    def _run_to_result(
        self, payload: Mapping[str, Any], example: DatasetExample
    ) -> ExperimentResult:
        experiment_example_id = (
            example.id if example.id is not None else str(payload.get("dataset_example_id"))
        )
        run_id = payload.get("id") or experiment_example_id

        return ExperimentResult(
            example_id=str(experiment_example_id),
            run_id=str(run_id),
            repetition_number=int(payload.get("repetition_number") or 1),
            started_at=deserialize_datetime(payload.get("start_time")),
            completed_at=deserialize_datetime(payload.get("end_time")),
            input_data=dict(example.input),
            output=dict(example.output),
            actual_output=payload.get("output"),
            evaluation_scores={},
            evaluator_metadata={},
            metadata={
                "trace_id": payload.get("trace_id"),
                "error": payload.get("error"),
            },
            trace_id=payload.get("trace_id"),
            error=payload.get("error"),
            execution_time_ms=None,
        )

    def _build_evaluation_payloads(self, results: list[ExperimentResult]) -> list[dict[str, Any]]:
        payloads: list[dict[str, Any]] = []
        for run in results:
            for metric_name, score in run.evaluation_scores.items():
                metadata = dict(run.evaluator_metadata.get(metric_name, {}))
                evaluator_result: dict[str, Any] = {}
                if score is not None:
                    evaluator_result["score"] = score
                label = metadata.get("label")
                if label is not None:
                    evaluator_result["label"] = label
                explanation = metadata.get("explanation")
                if explanation is not None:
                    evaluator_result["explanation"] = explanation

                started_at = metadata.get("started_at") or serialize_datetime(run.started_at)
                completed_at = metadata.get("completed_at") or serialize_datetime(run.completed_at)
                annotator_kind = metadata.get("annotator_kind", "CODE")
                trace_id = metadata.get("trace_id") or run.trace_id

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

                payload = {
                    "experiment_run_id": run.run_id,
                    "name": metric_name,
                    "annotator_kind": annotator_kind,
                    "start_time": started_at,
                    "end_time": completed_at,
                    "result": evaluator_result or None,
                }
                if metadata_payload:
                    payload["metadata"] = metadata_payload
                if trace_id:
                    payload["trace_id"] = trace_id
                if run.error and not evaluator_result:
                    payload["error"] = run.error

                payloads.append(payload)

        return payloads


__all__ = ["PhoenixEvaluationCoordinator", "PhoenixEvaluationPlan"]
