"""Run additional evaluators using runs stored in CAT Cafe."""

from __future__ import annotations

import inspect
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, cast

from ..evaluation_backends import EvaluationBackend
from ..experiments import ExperimentConfig, ExperimentResult, ExperimentSummary
from ..listeners import ExperimentListener
from ..models import DatasetExample
from ..serde import dataset_example_from_dict, experiment_result_from_dict
from ..types import EvaluatorFn
from .cat_cafe_listener import (
    CatCafeExperimentListener,
    CatCafeSyncConfig,
    build_evaluation_payloads,
    build_run_payload,
)
from .local_storage import build_local_runner, build_local_runner_async

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typing import Any as CATCafeClient  # type: ignore[assignment]

    from ..experiments import ExperimentRunner
else:
    from typing import Any as CATCafeClient  # type: ignore[assignment]


@dataclass
class CatCafeEvaluationPlan:
    experiment_id: str
    config: ExperimentConfig
    dataset_examples: list[DatasetExample]
    results: list[ExperimentResult]
    summary: ExperimentSummary | None = None


class CatCafeEvaluationCoordinator(EvaluationBackend):
    """Fetches recorded CAT Cafe runs and executes new evaluators locally."""

    def __init__(self, client: CATCafeClient) -> None:
        self._client = client

    @staticmethod
    def _fetch_dataset_examples(
        client: CATCafeClient, dataset_id: str, dataset_version: str | None
    ) -> list[dict[str, Any]]:
        """
        Fetch all dataset examples, handling servers that paginate by default.

        Newer CAT servers cap responses at 100 examples unless limit/offset are
        provided. We attempt to paginate when the SDK exposes those parameters,
        or by falling back to the client's low-level request helper if present.
        """

        def _page_from_response(payload: Any) -> list[dict[str, Any]]:
            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict) and "examples" in payload:
                nested = payload.get("examples")
                return nested if isinstance(nested, list) else []
            return []

        get_examples = getattr(client, "get_dataset_examples", None)
        if get_examples is None:
            raise RuntimeError("CAT Cafe client missing get_dataset_examples method.")

        sig = inspect.signature(get_examples)
        params = sig.parameters
        has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
        supports_limit = "limit" in params or has_kwargs
        supports_offset = "offset" in params or has_kwargs

        common_kwargs: dict[str, Any] = {}
        if dataset_version is not None:
            common_kwargs["version"] = dataset_version

        # First preference: SDK exposes limit/offset directly.
        if supports_limit or supports_offset:
            limit = 500
            offset = 0
            examples: list[dict[str, Any]] = []
            while True:
                page_kwargs = {**common_kwargs}
                if supports_limit:
                    page_kwargs["limit"] = limit
                if supports_offset:
                    page_kwargs["offset"] = offset
                payload = get_examples(dataset_id, **page_kwargs)  # type: ignore[arg-type]
                page = _page_from_response(payload)
                examples.extend(page)
                if len(page) < limit:
                    break
                offset += limit
            return examples

        # Fallback: use the client's request helper if available to paginate.
        if hasattr(client, "_make_request") and hasattr(client, "_build_api_url"):
            limit = 500
            offset = 0
            examples: list[dict[str, Any]] = []
            while True:
                params = {**common_kwargs, "limit": limit, "offset": offset}
                url = client._build_api_url(f"datasets/{dataset_id}/examples")  # type: ignore[attr-defined]
                response = client._make_request("GET", url, params=params)  # type: ignore[attr-defined]
                if hasattr(response, "raise_for_status"):
                    response.raise_for_status()
                payload = response.json() if hasattr(response, "json") else []
                page = _page_from_response(payload)
                examples.extend(page)
                if len(page) < limit:
                    break
                offset += limit
            return examples

        # Final fallback: single call (may be capped by server defaults).
        payload = get_examples(dataset_id, **common_kwargs)
        return _page_from_response(payload)

    def build_plan(self, experiment_id: str) -> CatCafeEvaluationPlan:
        detail = self._client.get_experiment_detail(experiment_id)
        experiment_meta = detail.get("experiment", {})
        dataset_id = experiment_meta.get("dataset_id")
        dataset_version = experiment_meta.get("dataset_version")

        if not dataset_id:
            raise ValueError("Experiment detail payload missing dataset_id")

        config = ExperimentConfig(
            name=experiment_meta.get("name") or f"cat-cafe-{experiment_id}",
            description=experiment_meta.get("description", ""),
            dataset_id=dataset_id,
            dataset_version_id=dataset_version,
            tags=list(experiment_meta.get("tags", [])),
            metadata=dict(experiment_meta.get("metadata", {})),
        )
        config.metadata.setdefault("cat_cafe_experiment_id", experiment_id)

        examples_payload = self._fetch_dataset_examples(self._client, dataset_id, dataset_version)
        dataset_examples = [dataset_example_from_dict(example) for example in examples_payload]

        results_payload = detail.get("results", [])
        if not results_payload:
            raise ValueError("Experiment detail payload missing recorded results")
        results = [experiment_result_from_dict(entry) for entry in results_payload]

        return CatCafeEvaluationPlan(
            experiment_id=experiment_id,
            config=config,
            dataset_examples=dataset_examples,
            results=results,
        )

    def fetch_experiment(self, experiment_id: str) -> CatCafeEvaluationPlan:
        """Return recorded CAT Cafe runs and metadata without side effects."""
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

    def persist_results(self, plan: CatCafeEvaluationPlan) -> None:
        for result in plan.results:
            run_payload = build_run_payload(result)
            eval_payloads = build_evaluation_payloads(result)
            run_id = run_payload.get("run_id")
            if not isinstance(run_id, str):
                raise ValueError("Run payload missing run_id; cannot persist evaluations.")
            try:
                self._client.create_run(plan.experiment_id, run_payload)
                for evaluation in eval_payloads:
                    self._client.append_evaluation(plan.experiment_id, run_id, evaluation)
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to persist CAT Cafe evaluations for run {run_id}: {exc}"
                ) from exc


def build_cat_cafe_runner(
    *,
    client: CATCafeClient | None = None,
    base_url: str | None = None,
    storage_dir: str | Path | None = None,
    clean_on_success: bool = False,
    listeners: Iterable[ExperimentListener] | None = None,
    enable_logging: bool = False,
) -> ExperimentRunner:
    """Create a runner wired to stream results into CAT Cafe via the adapter."""

    if client is None:
        try:
            from cat.cafe.client import CATCafeClient as _RealClient  # type: ignore
        except ImportError as exc:  # pragma: no cover - depends on optional package
            raise RuntimeError(
                "cat-cafe-client must be installed to build a CAT Cafe runner."
            ) from exc

        resolved_base_url = base_url or os.getenv("CAT_BASE_URL", "http://localhost:8000")
        client = cast(CATCafeClient, _RealClient(base_url=resolved_base_url))

    sync_config = CatCafeSyncConfig()

    runner = build_local_runner(
        storage_dir=storage_dir,
        clean_on_success=clean_on_success,
        listeners=listeners,
        enable_logging=enable_logging,
    )
    runner.add_listener(
        CatCafeExperimentListener(cast("CATCafeClient", client), config=sync_config)
    )
    return runner


def build_cat_cafe_runner_async(
    *,
    client: CATCafeClient | None = None,
    base_url: str | None = None,
    storage_dir: str | Path | None = None,
    clean_on_success: bool = False,
    listeners: Iterable[ExperimentListener] | None = None,
    enable_logging: bool = False,
):
    """Create an AsyncExperimentRunner wired to stream results into CAT Cafe."""

    if client is None:
        try:
            from cat.cafe.client import CATCafeClient as _RealClient  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "cat-cafe-client must be installed to build a CAT Cafe runner."
            ) from exc

        resolved_base_url = base_url or os.getenv("CAT_BASE_URL", "http://localhost:8000")
        client = cast(CATCafeClient, _RealClient(base_url=resolved_base_url))

    sync_config = CatCafeSyncConfig()

    runner = build_local_runner_async(
        storage_dir=storage_dir,
        clean_on_success=clean_on_success,
        listeners=listeners,
        enable_logging=enable_logging,
    )
    runner.add_listener(
        CatCafeExperimentListener(cast("CATCafeClient", client), config=sync_config)
    )
    return runner


__all__ = ["CatCafeEvaluationCoordinator", "CatCafeEvaluationPlan"]
