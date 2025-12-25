"""Local storage adapter that mirrors experiments to the filesystem."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable

from ..listeners import (
    AsyncLoggingListener,
    AsyncTqdmProgressListener,
    ExperimentListener,
    LoggingListener,
    TqdmProgressListener,
)
from ..models import DatasetExample
from ..serde import (
    dataset_example_to_dict,
    experiment_config_to_dict,
    experiment_result_to_dict,
    experiment_summary_to_dict,
)

if TYPE_CHECKING:  # pragma: no cover - used only for type checking
    from cat.experiments.experiments import (
        AsyncExperimentRunner,
        ExperimentConfig,
        ExperimentResult,
        ExperimentRunner,
        ExperimentSummary,
    )


@dataclass
class LocalStorageSyncConfig:
    """Configuration for persisting experiments locally."""

    base_dir: str | Path | None = None
    clean_on_success: bool = False


class LocalStorageExperimentListener(ExperimentListener):
    """Listener that writes experiment artifacts to the filesystem."""

    def __init__(self, *, config: LocalStorageSyncConfig | None = None) -> None:
        self._config = config or LocalStorageSyncConfig()
        base_dir = self._config.base_dir or Path.cwd() / ".cat_cache"
        self._base_path = Path(base_dir)
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._experiment_path: Path | None = None
        self._runs_file: Path | None = None
        self._examples_file: Path | None = None
        self._run_cache: dict[str, dict[str, Any]] = {}
        self._run_order: list[str] = []

    # ------------------------------------------------------------------ #
    # ExperimentListener interface
    # ------------------------------------------------------------------ #
    def on_experiment_started(
        self,
        experiment_id: str,
        config: "ExperimentConfig",
        examples: list[DatasetExample],
    ) -> None:
        path = self._ensure_path(experiment_id)
        self._experiment_path = path
        self._runs_file = path / "runs.jsonl"
        self._examples_file = path / "examples.jsonl"
        self._run_cache = {}
        self._run_order = []
        self._load_existing_runs()

        config_path = path / "config.json"
        if not config_path.exists():
            with open(config_path, "w") as f:
                json.dump(experiment_config_to_dict(config), f, indent=2)

        if self._examples_file and not self._examples_file.exists():
            with open(self._examples_file, "w") as f:
                for example in examples:
                    json.dump(dataset_example_to_dict(example), f)
                    f.write("\n")

    def on_task_completed(
        self,
        experiment_id: str,
        result: "ExperimentResult",
    ) -> None:
        self._record_run(result)

    def on_task_evaluated(
        self,
        experiment_id: str,
        result: "ExperimentResult",
    ) -> None:
        """Persist evaluated results; reuse completion logic."""
        self._record_run(result)

    def on_aggregate_completed(
        self,
        experiment_id: str,
        aggregate_scores: dict[str, float],
        aggregate_metadata: dict[str, dict[str, object]],
    ) -> None:
        """No-op for aggregate events; summaries are written in on_experiment_completed."""
        return

    def on_experiment_completed(
        self,
        experiment_id: str,
        results: list["ExperimentResult"],
        summary: "ExperimentSummary",
    ) -> None:
        if not self._experiment_path:
            return

        summary_path = self._experiment_path / "summary.json"
        with open(summary_path, "w") as f:
            json.dump(experiment_summary_to_dict(summary), f, indent=2)

        if self._config.clean_on_success:
            shutil.rmtree(self._experiment_path, ignore_errors=True)

    def on_experiment_failed(self, experiment_id: str, error: str) -> None:
        if not self._experiment_path:
            return

        failure_path = self._experiment_path / "failure.json"
        with open(failure_path, "w") as f:
            json.dump({"error": error, "timestamp": datetime.now().isoformat()}, f, indent=2)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _ensure_path(self, experiment_id: str) -> Path:
        path = self._base_path / experiment_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _record_run(self, result: "ExperimentResult") -> None:
        """Upsert a run record, ensuring one entry per run_id."""
        if not self._runs_file:
            return

        run_id = result.run_id or result.example_id
        if not run_id:
            return
        run_key = str(run_id)

        record = experiment_result_to_dict(result)
        if run_key not in self._run_order:
            self._run_order.append(run_key)
        self._run_cache[run_key] = record

        with open(self._runs_file, "w") as f:
            for rid in self._run_order:
                cached = self._run_cache.get(rid)
                if cached is None:
                    continue
                json.dump(cached, f)
                f.write("\n")

    def _load_existing_runs(self) -> None:
        """Warm the cache with any runs already on disk (for resume flows)."""
        if not self._runs_file or not self._runs_file.exists():
            return

        with open(self._runs_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload: dict[str, Any] = json.loads(line)
                except json.JSONDecodeError:
                    continue
                run_id = payload.get("run_id") or payload.get("example_id")
                if not run_id:
                    continue
                run_key = str(run_id)
                if run_key not in self._run_order:
                    self._run_order.append(run_key)
                self._run_cache[run_key] = payload


def build_local_runner(
    *,
    storage_dir: str | Path | None = None,
    clean_on_success: bool = False,
    listeners: Iterable[ExperimentListener] | None = None,
    enable_logging: bool = False,
) -> "ExperimentRunner":
    """Return an ExperimentRunner that persists runs to the local filesystem."""

    from ..experiments import ExperimentRunner

    runner = ExperimentRunner()
    if listeners:
        for listener in listeners:
            runner.add_listener(listener)

    base_dir = Path(storage_dir) if storage_dir else Path.cwd() / ".cat_cache"
    runner.add_listener(
        LocalStorageExperimentListener(
            config=LocalStorageSyncConfig(base_dir=base_dir, clean_on_success=clean_on_success)
        )
    )
    if enable_logging:
        runner.add_listener(LoggingListener())
    else:
        runner.add_listener(TqdmProgressListener())
    return runner


def build_local_runner_async(
    *,
    storage_dir: str | Path | None = None,
    clean_on_success: bool = False,
    listeners: Iterable[ExperimentListener] | None = None,
    enable_logging: bool = False,
) -> "AsyncExperimentRunner":
    """Return an AsyncExperimentRunner that persists runs to the local filesystem."""

    from ..experiments import AsyncExperimentRunner

    runner = AsyncExperimentRunner()
    if listeners:
        for listener in listeners:
            runner.add_listener(listener)

    base_dir = Path(storage_dir) if storage_dir else Path.cwd() / ".cat_cache"
    runner.add_listener(
        LocalStorageExperimentListener(
            config=LocalStorageSyncConfig(base_dir=base_dir, clean_on_success=clean_on_success)
        )
    )
    if enable_logging:
        runner.add_listener(AsyncLoggingListener())
    else:
        runner.add_listener(AsyncTqdmProgressListener())
    return runner


__all__ = [
    "LocalStorageExperimentListener",
    "LocalStorageSyncConfig",
    "build_local_runner",
    "build_local_runner_async",
]
