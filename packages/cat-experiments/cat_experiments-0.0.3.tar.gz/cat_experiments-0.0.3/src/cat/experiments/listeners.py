"""Experiment listener protocols for standalone evaluation.

This module defines the event-driven interfaces that allow experiment runners
to notify interested parties about experiment progress and completion.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from .models import DatasetExample

if TYPE_CHECKING:
    from .experiments import ExperimentConfig, ExperimentResult, ExperimentSummary


class ExperimentListener(Protocol):
    """Protocol for synchronous experiment event listeners.

    Implement any subset of these methods to listen for specific events.
    All methods are optional - implement only what you need.
    """

    def on_experiment_started(
        self, experiment_id: str, config: ExperimentConfig, examples: list[DatasetExample]
    ) -> None:
        """Called when experiment begins.

        Args:
            experiment_id: Unique identifier for this experiment run
            config: Experiment configuration including name, description, metadata
            examples: Prepared list of examples ready for processing
        """
        ...

    def on_task_completed(self, experiment_id: str, result: ExperimentResult) -> None:
        """Called when each task (example run) finishes processing."""
        ...

    def on_task_evaluated(self, experiment_id: str, result: ExperimentResult) -> None:
        """Called after evaluators have been applied to a task result."""
        ...

    def on_aggregate_completed(
        self,
        experiment_id: str,
        aggregate_scores: dict[str, float],
        aggregate_metadata: dict[str, dict[str, object]],
    ) -> None:
        """Called after aggregate evaluators finish.

        Args:
            experiment_id: Unique identifier for this experiment run
            aggregate_scores: Aggregate metrics produced for the run
            aggregate_metadata: Rich metadata per aggregate metric
        """
        ...

    def on_experiment_completed(
        self, experiment_id: str, results: list[ExperimentResult], summary: "ExperimentSummary"
    ) -> None:
        """Called when experiment completes successfully.

        Args:
            experiment_id: Unique identifier for this experiment run
            results: Complete list of all experiment results
            summary: Aggregated summary statistics (success rate, timing, etc.)
        """
        ...

    def on_experiment_failed(self, experiment_id: str, error: str) -> None:
        """Called when experiment fails with an error.

        Args:
            experiment_id: Unique identifier for this experiment run
            error: Error message describing the failure
        """
        ...


class AsyncExperimentListener(Protocol):
    """Protocol for asynchronous experiment event listeners.

    Implement any subset of these methods to listen for specific events.
    All methods are optional - implement only what you need.
    """

    async def on_experiment_started(
        self, experiment_id: str, config: ExperimentConfig, examples: list[DatasetExample]
    ) -> None:
        """Called when experiment begins.

        Args:
            experiment_id: Unique identifier for this experiment run
            config: Experiment configuration including name, description, metadata
            examples: Prepared list of examples ready for processing
        """
        ...

    async def on_task_completed(self, experiment_id: str, result: ExperimentResult) -> None:
        """Called when each task (example run) finishes processing."""
        ...

    async def on_task_evaluated(self, experiment_id: str, result: ExperimentResult) -> None:
        """Called after evaluators have been applied to a task result."""
        ...

    async def on_aggregate_completed(
        self,
        experiment_id: str,
        aggregate_scores: dict[str, float],
        aggregate_metadata: dict[str, dict[str, object]],
    ) -> None:
        """Called after aggregate evaluators finish."""
        ...

    async def on_experiment_completed(
        self, experiment_id: str, results: list[ExperimentResult], summary: "ExperimentSummary"
    ) -> None:
        """Called when experiment completes successfully.

        Args:
            experiment_id: Unique identifier for this experiment run
            results: Complete list of all experiment results
            summary: Aggregated summary statistics (success rate, timing, etc.)
        """
        ...

    async def on_experiment_failed(self, experiment_id: str, error: str) -> None:
        """Called when experiment fails with an error.

        Args:
            experiment_id: Unique identifier for this experiment run
            error: Error message describing the failure
        """
        ...


class LoggingListener:
    """Built-in logging listener for experiment events."""

    def __init__(self, verbose: bool = True):
        """Initialize logging listener.

        Args:
            verbose: Whether to log detailed information
        """
        self.verbose = verbose

    def on_experiment_started(
        self, experiment_id: str, config: ExperimentConfig, examples: list[DatasetExample]
    ) -> None:
        """Log experiment start."""
        print(f"🚀 Starting experiment: {config.name}")
        if self.verbose:
            print(f"   ID: {experiment_id}")
            print(f"   Examples: {len(examples)}")
            print(f"   Description: {config.description}")

    def on_task_completed(self, experiment_id: str, result: ExperimentResult) -> None:
        """Log task completion."""
        if result.error:
            print(f"❌ Example {result.example_id}: FAILED ({result.error})")
        else:
            scores_text = ", ".join(
                [f"{name}={score:.2f}" for name, score in result.evaluation_scores.items()]
            )
            if scores_text:
                print(f"✅ Example {result.example_id}: {scores_text}")
            else:
                print(f"✅ Example {result.example_id}: completed")

    def on_task_evaluated(self, experiment_id: str, result: ExperimentResult) -> None:
        """Log post-evaluation task completion."""
        # Reuse the same logging as on_task_completed to display scores.
        self.on_task_completed(experiment_id, result)

    def on_aggregate_completed(
        self,
        experiment_id: str,
        aggregate_scores: dict[str, float],
        aggregate_metadata: dict[str, dict[str, object]],
    ) -> None:
        """Log aggregate results when present."""
        if not aggregate_scores:
            return
        print("📊 Aggregate metrics:")
        for name, score in aggregate_scores.items():
            print(f"   {name}: {score:.3f}")

    def on_experiment_completed(
        self, experiment_id: str, results: list[ExperimentResult], summary: "ExperimentSummary"
    ) -> None:
        """Log experiment completion."""
        print(f"🎉 Experiment completed: {summary.config.name}")
        print(f"   Success rate: {summary.successful_examples}/{summary.total_examples}")

        if summary.average_scores:
            print("   Average scores:")
            for name, score in summary.average_scores.items():
                print(f"     {name}: {score:.3f}")

        if self.verbose:
            duration_ms = summary.total_execution_time_ms
            print(f"   Total time: {duration_ms:.0f}ms")
            metadata_keys: dict[str, set[str]] = {}
            for result in results:
                for evaluator_name, meta in getattr(result, "evaluator_metadata", {}).items():
                    if not meta:
                        continue
                    metadata_keys.setdefault(evaluator_name, set()).update(meta.keys())
            if metadata_keys:
                print("   Evaluator metadata keys:")
                for name in sorted(metadata_keys):
                    keys = ", ".join(sorted(metadata_keys[name]))
                    print(f"     {name}: {keys}")

    def on_experiment_failed(self, experiment_id: str, error: str) -> None:
        """Log experiment failure."""
        print(f"💥 Experiment failed: {error}")


class AsyncLoggingListener:
    """Built-in async logging listener for experiment events."""

    def __init__(self, verbose: bool = True):
        """Initialize async logging listener.

        Args:
            verbose: Whether to log detailed information
        """
        self.verbose = verbose

    async def on_experiment_started(
        self, experiment_id: str, config: ExperimentConfig, examples: list[DatasetExample]
    ) -> None:
        """Log experiment start."""
        print(f"🚀 Starting async experiment: {config.name}")
        if self.verbose:
            print(f"   ID: {experiment_id}")
            print(f"   Examples: {len(examples)}")
            print(f"   Description: {config.description}")

    async def on_task_completed(self, experiment_id: str, result: ExperimentResult) -> None:
        """Log task completion."""
        if result.error:
            print(f"❌ Example {result.example_id}: FAILED ({result.error})")
        else:
            scores_text = ", ".join(
                [f"{name}={score:.2f}" for name, score in result.evaluation_scores.items()]
            )
            if scores_text:
                print(f"✅ Example {result.example_id}: {scores_text}")
            else:
                print(f"✅ Example {result.example_id}: completed")

    async def on_task_evaluated(self, experiment_id: str, result: ExperimentResult) -> None:
        """Log post-evaluation task completion."""
        await self.on_task_completed(experiment_id, result)

    async def on_aggregate_completed(
        self,
        experiment_id: str,
        aggregate_scores: dict[str, float],
        aggregate_metadata: dict[str, dict[str, object]],
    ) -> None:
        """Log aggregate results when present."""
        if not aggregate_scores:
            return
        print("📊 Aggregate metrics:")
        for name, score in aggregate_scores.items():
            print(f"   {name}: {score:.3f}")

    async def on_experiment_completed(
        self, experiment_id: str, results: list[ExperimentResult], summary: "ExperimentSummary"
    ) -> None:
        """Log experiment completion."""
        print(f"🎉 Async experiment completed: {summary.config.name}")
        print(f"   Success rate: {summary.successful_examples}/{summary.total_examples}")

        if summary.average_scores:
            print("   Average scores:")
            for name, score in summary.average_scores.items():
                print(f"     {name}: {score:.3f}")

        if self.verbose:
            duration_ms = summary.total_execution_time_ms
            print(f"   Total time: {duration_ms:.0f}ms")
            metadata_keys: dict[str, set[str]] = {}
            for result in results:
                for evaluator_name, meta in getattr(result, "evaluator_metadata", {}).items():
                    if not meta:
                        continue
                    metadata_keys.setdefault(evaluator_name, set()).update(meta.keys())
            if metadata_keys:
                print("   Evaluator metadata keys:")
                for name in sorted(metadata_keys):
                    keys = ", ".join(sorted(metadata_keys[name]))
                    print(f"     {name}: {keys}")

    async def on_experiment_failed(self, experiment_id: str, error: str) -> None:
        """Log experiment failure."""
        print(f"💥 Async experiment failed: {error}")


class TqdmProgressListener:
    """Progress bar listener using tqdm; depends on tqdm being installed."""

    def __init__(self, desc: str | None = None):
        self._bar = None
        self._desc = desc
        self._enabled = True
        self._eval_bar = None

    def _ensure_bar(self, total: int, config: ExperimentConfig) -> None:
        if not self._enabled:
            return
        try:
            from tqdm.auto import tqdm  # type: ignore
        except Exception:
            self._enabled = False
            return

        if self._bar is None:
            self._bar = tqdm(total=total, desc=self._desc or config.name, leave=True)

    def _close_bar(self) -> None:
        if self._bar is not None:
            self._bar.close()
        self._bar = None
        if self._eval_bar is not None:
            self._eval_bar.close()
        self._eval_bar = None

    def on_experiment_started(
        self, experiment_id: str, config: ExperimentConfig, examples: list[DatasetExample]
    ) -> None:
        self._ensure_bar(len(examples), config)

    def on_task_completed(self, experiment_id: str, result: ExperimentResult) -> None:
        if self._bar is not None:
            self._bar.update(1)

    def start_evaluations(self, total: int, config: ExperimentConfig) -> None:
        if not self._enabled:
            return
        try:
            from tqdm.auto import tqdm  # type: ignore
        except Exception:
            self._enabled = False
            return
        if self._eval_bar is None:
            self._eval_bar = tqdm(
                total=total, desc=(self._desc or config.name) + " evals", leave=True
            )

    def on_evaluation_completed(self, experiment_id: str, evaluator_name: str) -> None:
        if self._eval_bar is not None:
            self._eval_bar.update(1)

    def on_experiment_completed(
        self, experiment_id: str, results: list[ExperimentResult], summary: "ExperimentSummary"
    ) -> None:
        self._close_bar()

    def on_experiment_failed(self, experiment_id: str, error: str) -> None:
        self._close_bar()


class AsyncTqdmProgressListener:
    """Async progress bar listener using tqdm; depends on tqdm being installed."""

    def __init__(self, desc: str | None = None):
        self._bar = None
        self._desc = desc
        self._enabled = True
        self._eval_bar = None

    def _ensure_bar(self, total: int, config: ExperimentConfig) -> None:
        if not self._enabled:
            return
        try:
            from tqdm.auto import tqdm  # type: ignore
        except Exception:
            self._enabled = False
            return

        if self._bar is None:
            self._bar = tqdm(total=total, desc=self._desc or config.name, leave=True)

    def _close_bar(self) -> None:
        if self._bar is not None:
            self._bar.close()
        self._bar = None
        if self._eval_bar is not None:
            self._eval_bar.close()
        self._eval_bar = None

    async def on_experiment_started(
        self, experiment_id: str, config: ExperimentConfig, examples: list[DatasetExample]
    ) -> None:
        self._ensure_bar(len(examples), config)

    async def on_task_completed(self, experiment_id: str, result: ExperimentResult) -> None:
        if self._bar is not None:
            self._bar.update(1)

    async def start_evaluations(self, total: int, config: ExperimentConfig) -> None:
        if not self._enabled:
            return
        try:
            from tqdm.auto import tqdm  # type: ignore
        except Exception:
            self._enabled = False
            return
        if self._eval_bar is None:
            self._eval_bar = tqdm(
                total=total, desc=(self._desc or config.name) + " evals", leave=True
            )

    async def on_evaluation_completed(self, experiment_id: str, evaluator_name: str) -> None:
        if self._eval_bar is not None:
            self._eval_bar.update(1)

    async def on_experiment_completed(
        self, experiment_id: str, results: list[ExperimentResult], summary: "ExperimentSummary"
    ) -> None:
        self._close_bar()

    async def on_experiment_failed(self, experiment_id: str, error: str) -> None:
        self._close_bar()


__all__ = [
    "ExperimentListener",
    "AsyncExperimentListener",
    "LoggingListener",
    "AsyncLoggingListener",
    "TqdmProgressListener",
    "AsyncTqdmProgressListener",
]
