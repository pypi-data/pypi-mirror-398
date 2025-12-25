"""Experiment runner infrastructure for standalone evaluation.

This module provides experiment runners with listener support for complex
evaluation workflows. It handles caching, parallel execution, and progress tracking.
"""

from __future__ import annotations

import inspect
import time
import uuid
import warnings
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from random import Random
from typing import TYPE_CHECKING, Any

from .evaluation import (
    evaluate,
    evaluate_aggregate,
    evaluate_aggregate_async,
    evaluate_async,
    generate,
    generate_async,
)
from .evaluation_backends import EvaluationBackend

if TYPE_CHECKING:
    from .listeners import AsyncExperimentListener, ExperimentListener
from .models import (
    AggregateEvaluationContext,
    DatasetExample,
    EvaluationContext,
    TestCase,
)
from .result_utils import apply_evaluations_to_results, build_contexts_from_results
from .types import (
    AggregateEvaluatorFn,
    AsyncAggregateEvaluatorFn,
    AsyncEvaluatorFn,
    AsyncTestFn,
    EvaluatorFn,
    TestFn,
)


@dataclass
class ExperimentConfig:
    """Configuration for an experiment run."""

    name: str
    description: str = ""
    dataset_id: str | None = None
    dataset_version_id: str | None = None
    project_name: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    repetitions: int = 1
    """Number of times to execute each selected example."""
    preview_examples: int | None = None
    """Optional preview subset size. None means run all examples."""
    preview_seed: int = 42
    """Deterministic seed for preview example selection."""
    max_workers: int = 1


@dataclass
class ExperimentResult:
    """Complete result from processing a single dataset example."""

    example_id: str
    run_id: str
    repetition_number: int
    started_at: datetime | None
    completed_at: datetime | None
    input_data: dict[str, Any]
    output: dict[str, Any]
    actual_output: str | dict[str, Any] | list[Any] | None
    evaluation_scores: dict[str, float]
    evaluator_metadata: dict[str, dict[str, Any]]
    metadata: dict[str, Any]
    trace_id: str | None = None
    error: str | None = None
    execution_time_ms: float | None = None


@dataclass
class ExperimentSummary:
    """Summary statistics for a completed experiment."""

    total_examples: int
    successful_examples: int
    failed_examples: int
    average_scores: dict[str, float]
    total_execution_time_ms: float
    experiment_id: str
    config: ExperimentConfig
    started_at: datetime
    completed_at: datetime | None = None
    aggregate_scores: dict[str, float] = field(default_factory=dict)
    aggregate_metadata: dict[str, dict[str, Any]] = field(default_factory=dict)


class ExperimentRunnerMixin:
    """Shared functionality for experiment runners."""

    def __init__(self) -> None:
        """Initialize shared runner functionality."""
        # No-op for now; reserved for future shared state.
        return

    def _generate_experiment_id(self) -> str:
        """Generate unique experiment ID."""
        return f"exp_{uuid.uuid4().hex[:12]}_{int(time.time())}"

    def _prepare_dataset(
        self,
        dataset: list[DatasetExample] | dict[str, Any],
        *,
        preview_examples: int | None = None,
        preview_seed: int | None = None,
        repetitions: int = 1,
        run_selection: Mapping[str, Iterable[int]] | None = None,
    ) -> tuple[list[DatasetExample], list[TestCase]]:
        """Normalize dataset input, apply preview sampling, and expand repetitions."""
        if isinstance(dataset, list):
            examples = list(dataset)
        elif isinstance(dataset, dict):
            examples = self._dict_to_examples(dataset)
        else:
            raise ValueError(f"Unsupported dataset type: {type(dataset)}")

        if run_selection:
            selected_examples, expanded_runs = self._build_runs_from_selection(
                examples=examples,
                run_selection=run_selection,
                repetitions=repetitions,
            )
        else:
            selected_examples = self._apply_preview_selection(
                examples, preview_examples=preview_examples, preview_seed=preview_seed
            )
            expanded_runs = self._expand_repetitions(selected_examples, repetitions=repetitions)
        return selected_examples, expanded_runs

    def _dict_to_examples(self, dataset_dict: dict[str, Any]) -> list[DatasetExample]:
        """Convert dictionary to list of DatasetExample objects."""
        examples: list[DatasetExample] = []
        for ex_data in dataset_dict.get("examples", []):
            metadata = dict(ex_data.get("metadata", {}))
            if "tags" in ex_data and "tags" not in metadata:
                metadata["tags"] = ex_data.get("tags", [])
            if "expected_tool_calls" in ex_data and "expected_tool_calls" not in metadata:
                metadata["expected_tool_calls"] = ex_data.get("expected_tool_calls")
            if "source_trace_id" in ex_data and "source_trace_id" not in metadata:
                metadata["source_trace_id"] = ex_data.get("source_trace_id")
            if "source_node_id" in ex_data and "source_node_id" not in metadata:
                metadata["source_node_id"] = ex_data.get("source_node_id")

            example = DatasetExample(
                input=dict(ex_data.get("input", {}) or {}),
                output=dict(ex_data.get("output", {}) or {}),
                metadata=metadata,
                id=ex_data.get("id"),
                created_at=ex_data.get("created_at"),
                updated_at=ex_data.get("updated_at"),
            )

            examples.append(example)

        return examples

    def _apply_preview_selection(
        self,
        examples: list[DatasetExample],
        *,
        preview_examples: int | None,
        preview_seed: int | None,
    ) -> list[DatasetExample]:
        """Select a deterministic preview subset when requested."""
        if preview_examples is None:
            return list(examples)
        if preview_examples <= 0:
            raise ValueError("preview_examples must be a positive integer")

        total = len(examples)
        if total == 0 or preview_examples >= total:
            return list(examples)

        rng = Random(preview_seed) if preview_seed is not None else Random()
        selected_indices = sorted(rng.sample(range(total), k=preview_examples))
        return [examples[i] for i in selected_indices]

    def _expand_repetitions(
        self, examples: list[DatasetExample], *, repetitions: int
    ) -> list[TestCase]:
        """Expand each example into the requested number of repetitions."""
        if repetitions < 1:
            raise ValueError("repetitions must be >= 1")

        runs: list[TestCase] = []
        for example in examples:
            for repetition in range(1, repetitions + 1):
                runs.append(TestCase(example=example, repetition_number=repetition))
        return runs

    def _build_runs_from_selection(
        self,
        *,
        examples: list[DatasetExample],
        run_selection: Mapping[str, Iterable[int]],
        repetitions: int,
    ) -> tuple[list[DatasetExample], list[TestCase]]:
        """Create deterministic TestCase objects from a run selection filter."""
        if repetitions < 1:
            raise ValueError("repetitions must be >= 1")
        if not run_selection:
            return [], []

        selected_examples: list[DatasetExample] = []
        runs: list[TestCase] = []

        remaining_ids = set(run_selection.keys())
        for example in examples:
            example_id = example.id
            if not example_id or example_id not in run_selection:
                continue

            remaining_ids.discard(example_id)
            selected_examples.append(example)

            repetitions_for_example = run_selection.get(example_id, [])
            if repetitions_for_example is None:
                raise ValueError(
                    f"run_selection for example {example_id} must provide repetition numbers."
                )

            normalized_reps = sorted({int(rep) for rep in repetitions_for_example})
            for rep in normalized_reps:
                if rep < 1 or rep > repetitions:
                    raise ValueError(
                        f"run_selection repetition {rep} for example {example_id} "
                        f"is outside the configured range 1..{repetitions}."
                    )
                runs.append(TestCase(example=example, repetition_number=rep))

        if remaining_ids:
            missing = ", ".join(sorted(str(example_id) for example_id in remaining_ids))
            raise ValueError(f"run_selection referenced unknown example IDs: {missing}")

        return selected_examples, runs

    def _generate_contexts(
        self,
        runs: list[TestCase],
        task: TestFn,
        *,
        max_workers: int,
        on_context_completed=None,
    ) -> list[EvaluationContext]:
        return generate(
            runs, task, max_workers=max_workers, on_context_completed=on_context_completed
        )

    async def _generate_contexts_async(
        self,
        runs: list[TestCase],
        task: AsyncTestFn,
        *,
        max_workers: int,
        on_context_completed=None,
    ) -> list[EvaluationContext]:
        return await generate_async(
            runs, task, max_workers=max_workers, on_context_completed=on_context_completed
        )

    def _contexts_to_results(self, contexts: list[EvaluationContext]) -> list[ExperimentResult]:
        """Convert evaluation contexts to experiment results (before evaluation)."""
        return [self._context_to_result(context) for context in contexts]

    def _context_to_result(self, context: EvaluationContext) -> ExperimentResult:
        """Convert a single EvaluationContext to ExperimentResult."""
        return ExperimentResult(
            example_id=context.example_id,
            run_id=context.run_id,
            repetition_number=context.repetition_number,
            started_at=context.started_at,
            completed_at=context.completed_at,
            input_data=dict(context.input or {}),
            output=dict(context.output or {}),
            actual_output=context.actual_output,
            evaluation_scores={},
            evaluator_metadata={},
            metadata={
                "execution_time_ms": context.execution_time_ms,
                "error": context.error,
                "run_id": context.run_id,
                "repetition_number": context.repetition_number,
                **dict(context.execution_metadata or {}),
            },
            trace_id=context.trace_id,
            error=context.error,
            execution_time_ms=context.execution_time_ms,
        )


class ExperimentRunner(ExperimentRunnerMixin):
    """Synchronous experiment runner with listener support."""

    def __init__(self):
        """Initialize synchronous experiment runner."""
        super().__init__()
        self.listeners: list[Any] = []

    def rerun_evaluators(
        self,
        *,
        experiment_id: str,
        evaluators: list[EvaluatorFn],
        aggregate_evaluators: list[AggregateEvaluatorFn] | None = None,
        backend: "EvaluationBackend[Any]",
        persist: bool = True,
    ) -> list["ExperimentResult"]:
        """Fetch persisted runs via adapter backend and execute new evaluators."""

        if not evaluators and not aggregate_evaluators:
            raise ValueError("At least one evaluator must be provided")
        if aggregate_evaluators is None:
            aggregate_evaluators = []

        plan = backend.build_plan(experiment_id)
        examples_by_id = {ex.id: ex for ex in plan.dataset_examples if ex.id}
        if len(examples_by_id) < len(plan.dataset_examples):
            missing = [ex for ex in plan.dataset_examples if not ex.id]
            if missing:
                raise ValueError("All dataset examples must have stable IDs to rerun evaluators")

        contexts = build_contexts_from_results(plan.results, examples_by_id)
        if evaluators:
            evaluation_payloads = evaluate(contexts, evaluators)
            apply_evaluations_to_results(plan.results, evaluation_payloads, merge=True)

        plan_summary = getattr(plan, "summary", None)
        aggregate_scores: dict[str, float] = {}
        aggregate_metadata: dict[str, dict[str, Any]] = {}
        if aggregate_evaluators:
            aggregate_context = AggregateEvaluationContext(
                experiment_id=experiment_id,
                config=plan.config,
                contexts=contexts,
                results=plan.results,
                examples=list(examples_by_id.values()),
                started_at=plan_summary.started_at if plan_summary else None,
                completed_at=plan_summary.completed_at if plan_summary else None,
            )
            aggregate_result = evaluate_aggregate(aggregate_context, aggregate_evaluators)
            aggregate_scores = aggregate_result.get("aggregate_scores", {})
            aggregate_metadata = aggregate_result.get("aggregate_metadata", {})

        summary_started_at = plan_summary.started_at if plan_summary else None
        summary_completed_at = plan_summary.completed_at if plan_summary else None

        summary = _build_summary_from_results(
            results=plan.results,
            config=plan.config,
            experiment_id=experiment_id,
            aggregate_scores=aggregate_scores,
            aggregate_metadata=aggregate_metadata,
            started_at=summary_started_at,
            completed_at=summary_completed_at,
        )
        setattr(plan, "summary", summary)

        if persist:
            backend.persist_results(plan)

        return plan.results

    def add_listener(self, listener: object) -> None:
        """Add a synchronous experiment listener.

        Args:
            listener: Object implementing ExperimentListener protocol
        """
        self.listeners.append(listener)

    def remove_listener(self, listener: object) -> None:
        """Remove a listener.

        Args:
            listener: Listener to remove
        """
        if listener in self.listeners:
            self.listeners.remove(listener)

    def run(
        self,
        dataset: list[DatasetExample] | dict[str, Any],
        task: TestFn | None = None,
        evaluators: list[EvaluatorFn] | None = None,
        aggregate_evaluators: list[AggregateEvaluatorFn] | None = None,
        config: ExperimentConfig | None = None,
        experiment_id: str | None = None,
        run_selection: Mapping[str, Iterable[int]] | None = None,
        *,
        test_function: TestFn | None = None,
    ) -> ExperimentSummary:
        """Run experiment synchronously with listener notifications.

        Args:
            dataset: List of DatasetExample objects or dict with examples
            task: Synchronous function that takes DatasetExample and returns output
            evaluators: List of synchronous evaluator functions
            config: Experiment configuration
            experiment_id: Optional custom experiment ID (generates one if not provided)
            run_selection: Optional mapping of example IDs to repetition numbers to execute

        Returns:
            ExperimentSummary with complete results and metadata
        """
        if task is None and test_function is not None:
            warnings.warn(
                "test_function is deprecated; use task instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            task = test_function

        if task is None:
            raise ValueError("task must be provided")

        # Use default config if not provided
        if config is None:
            config = ExperimentConfig(name="Experiment", description="Synchronous experiment run")

        # Use default evaluators if not provided
        if evaluators is None:
            evaluators = []
        if aggregate_evaluators is None:
            aggregate_evaluators = []

        # Validate that all components are synchronous
        if inspect.iscoroutinefunction(task):
            raise TypeError(
                "Async task provided to synchronous runner. Use AsyncExperimentRunner instead."
            )

        for evaluator in evaluators:
            if inspect.iscoroutinefunction(evaluator):
                raise TypeError(
                    "Async evaluator provided to synchronous runner. "
                    "Use AsyncExperimentRunner instead."
                )
        for aggregate_evaluator in aggregate_evaluators:
            if inspect.iscoroutinefunction(aggregate_evaluator):
                raise TypeError(
                    "Async aggregate evaluator provided to synchronous runner. "
                    "Use AsyncExperimentRunner instead."
                )

        # Prepare dataset (preview selection + repetitions)
        examples, example_runs = self._prepare_dataset(
            dataset,
            preview_examples=config.preview_examples,
            preview_seed=config.preview_seed,
            repetitions=config.repetitions,
            run_selection=run_selection,
        )

        max_workers = max(1, int(config.max_workers or 1))

        # Use provided experiment ID or generate a new one
        if experiment_id is None:
            experiment_id = self._generate_experiment_id()

        started_at = datetime.now(timezone.utc)

        try:
            # Notify listeners that experiment started
            for listener in self.listeners:
                if hasattr(listener, "on_experiment_started"):
                    listener.on_experiment_started(experiment_id, config, examples)

            # Step 1: Generate contexts with streaming callbacks
            interim_results: list[ExperimentResult | None] = [None] * len(example_runs)

            def _on_context_completed(context, index: int) -> None:
                result = self._context_to_result(context)
                interim_results[index] = result
                for listener in self.listeners:
                    if hasattr(listener, "on_task_completed"):
                        listener.on_task_completed(experiment_id, result)

            contexts = self._generate_contexts(
                example_runs,
                task,
                max_workers=max_workers,
                on_context_completed=_on_context_completed,
            )

            # Convert contexts to results (before evaluation), filling any missed slots defensively
            results: list[ExperimentResult] = []
            for idx, context in enumerate(contexts):
                candidate = interim_results[idx]
                result = candidate if candidate is not None else self._context_to_result(context)
                results.append(result)

            # Step 2: Evaluate contexts if evaluators provided
            if evaluators:
                eval_total = len(contexts) * len(evaluators)
                eval_listeners = [
                    listener
                    for listener in self.listeners
                    if hasattr(listener, "start_evaluations")
                ]
                for listener in eval_listeners:
                    listener.start_evaluations(eval_total, config)  # type: ignore[attr-defined]

                def _on_eval(context, evaluator_name: str):
                    for listener in self.listeners:
                        if hasattr(listener, "on_evaluation_completed"):
                            listener.on_evaluation_completed(experiment_id, evaluator_name)  # type: ignore[attr-defined]

                evaluation_results = evaluate(
                    contexts, evaluators, on_evaluation_completed=_on_eval
                )
                apply_evaluations_to_results(results, evaluation_results)
                for result in results:
                    for listener in self.listeners:
                        if hasattr(listener, "on_task_evaluated"):
                            listener.on_task_evaluated(experiment_id, result)  # type: ignore[attr-defined]

            # Step 3: Aggregate evaluators (run-once over the full run)
            aggregate_scores: dict[str, float] = {}
            aggregate_metadata: dict[str, dict[str, Any]] = {}
            if aggregate_evaluators:
                aggregate_context = AggregateEvaluationContext(
                    experiment_id=experiment_id,
                    config=config,
                    contexts=contexts,
                    results=results,
                    examples=examples,
                    started_at=started_at,
                )
                aggregate_result = evaluate_aggregate(aggregate_context, aggregate_evaluators)
                aggregate_scores = aggregate_result.get("aggregate_scores", {})
                aggregate_metadata = aggregate_result.get("aggregate_metadata", {})

            completed_at = datetime.now(timezone.utc)

            # Notify listeners that aggregate evaluators completed
            if aggregate_evaluators:
                for listener in self.listeners:
                    if hasattr(listener, "on_aggregate_completed"):
                        listener.on_aggregate_completed(
                            experiment_id,
                            aggregate_scores,
                            aggregate_metadata,
                        )

            # Calculate summary statistics
            total_examples = len(results)
            successful_examples = len([r for r in results if not r.error])

            # Calculate average scores per metric (across all evaluators)
            evaluator_averages = {}
            if evaluators and results:
                # Collect all unique metric names from results
                all_metric_names = set()
                for result in results:
                    if not result.error:
                        all_metric_names.update(result.evaluation_scores.keys())

                # Calculate average for each metric
                for metric_name in all_metric_names:
                    scores = [
                        r.evaluation_scores.get(metric_name, 0.0)
                        for r in results
                        if not r.error and metric_name in r.evaluation_scores
                    ]
                    evaluator_averages[metric_name] = sum(scores) / len(scores) if scores else 0.0

            summary = ExperimentSummary(
                total_examples=total_examples,
                successful_examples=successful_examples,
                failed_examples=total_examples - successful_examples,
                average_scores=evaluator_averages,
                aggregate_scores=aggregate_scores,
                aggregate_metadata=aggregate_metadata,
                total_execution_time_ms=sum(r.execution_time_ms or 0 for r in results),
                experiment_id=experiment_id,
                config=config,
                started_at=started_at,
                completed_at=completed_at,
            )

            if total_examples > 0 and successful_examples == 0:
                error_message = next((r.error for r in results if r.error), "all runs failed")
                raise RuntimeError(f"Experiment failed: {error_message}")

            # Notify listeners that experiment completed
            for listener in self.listeners:
                if hasattr(listener, "on_experiment_completed"):
                    listener.on_experiment_completed(experiment_id, results, summary)

            return summary

        except Exception as e:
            # Notify listeners of experiment failure
            for listener in self.listeners:
                if hasattr(listener, "on_experiment_failed"):
                    listener.on_experiment_failed(experiment_id, str(e))
            raise


class AsyncExperimentRunner(ExperimentRunnerMixin):
    """Asynchronous experiment runner with listener support."""

    def __init__(self):
        """Initialize asynchronous experiment runner."""
        super().__init__()
        self.listeners: list[Any] = []

    def add_listener(self, listener: object) -> None:
        """Add an asynchronous experiment listener.

        Args:
            listener: Object implementing AsyncExperimentListener protocol
        """
        self.listeners.append(listener)

    def remove_listener(self, listener: object) -> None:
        """Remove a listener.

        Args:
            listener: Listener to remove
        """
        if listener in self.listeners:
            self.listeners.remove(listener)

    async def run(
        self,
        dataset: list[DatasetExample] | dict[str, Any],
        task: AsyncTestFn | None = None,
        evaluators: list[AsyncEvaluatorFn] | None = None,
        aggregate_evaluators: list[AsyncAggregateEvaluatorFn] | None = None,
        config: ExperimentConfig | None = None,
        experiment_id: str | None = None,
        run_selection: Mapping[str, Iterable[int]] | None = None,
        *,
        test_function: AsyncTestFn | None = None,
    ) -> ExperimentSummary:
        """Run experiment asynchronously with listener notifications.

        Args:
            dataset: List of DatasetExample objects or dict with examples
            task: Async function that takes DatasetExample and returns output
            evaluators: List of async evaluator functions
            config: Experiment configuration
            experiment_id: Optional custom experiment ID (generates one if not provided)

        Returns:
            ExperimentSummary with complete results and metadata
        """
        if task is None and test_function is not None:
            warnings.warn(
                "test_function is deprecated; use task instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            task = test_function

        if task is None:
            raise ValueError("task must be provided")

        # Use default config if not provided
        if config is None:
            config = ExperimentConfig(
                name="Async Experiment", description="Asynchronous experiment run"
            )

        # Use default evaluators if not provided
        if evaluators is None:
            evaluators = []
        if aggregate_evaluators is None:
            aggregate_evaluators = []

        if not inspect.iscoroutinefunction(task):
            raise TypeError("AsyncExperimentRunner requires an async task function.")

        for evaluator in evaluators:
            if not inspect.iscoroutinefunction(evaluator):
                raise TypeError(
                    "AsyncExperimentRunner requires async evaluators. "
                    "Provide async callables or use ExperimentRunner instead."
                )
        for aggregate_evaluator in aggregate_evaluators:
            if not inspect.iscoroutinefunction(aggregate_evaluator):
                raise TypeError(
                    "AsyncExperimentRunner requires async aggregate evaluators. "
                    "Provide async callables or use ExperimentRunner instead."
                )

        # Prepare dataset (preview selection + repetitions)
        examples, example_runs = self._prepare_dataset(
            dataset,
            preview_examples=config.preview_examples,
            preview_seed=config.preview_seed,
            repetitions=config.repetitions,
            run_selection=run_selection,
        )

        max_workers = max(1, int(config.max_workers or 1))

        # Use provided experiment ID or generate a new one
        if experiment_id is None:
            experiment_id = self._generate_experiment_id()

        started_at = datetime.now(timezone.utc)

        try:
            # Notify listeners that experiment started
            for listener in self.listeners:
                if hasattr(listener, "on_experiment_started"):
                    result = listener.on_experiment_started(experiment_id, config, examples)
                    if inspect.isawaitable(result):
                        await result

            interim_results: list[ExperimentResult | None] = [None] * len(example_runs)

            async def _on_context_completed(context, index: int):
                result = self._context_to_result(context)
                interim_results[index] = result
                for listener in self.listeners:
                    if hasattr(listener, "on_task_completed"):
                        outcome = listener.on_task_completed(experiment_id, result)
                        if inspect.isawaitable(outcome):
                            await outcome

            contexts = await self._generate_contexts_async(
                example_runs,
                task,
                max_workers=max_workers,
                on_context_completed=_on_context_completed,
            )

            results: list[ExperimentResult] = []
            for idx, context in enumerate(contexts):
                candidate = interim_results[idx]
                result = candidate if candidate is not None else self._context_to_result(context)
                results.append(result)

            # Step 2: Evaluate contexts if evaluators provided
            if evaluators:
                eval_total = len(contexts) * len(evaluators)
                eval_listeners = [
                    listener
                    for listener in self.listeners
                    if hasattr(listener, "start_evaluations")
                ]
                for listener in eval_listeners:
                    outcome = listener.start_evaluations(eval_total, config)  # type: ignore[attr-defined]
                    if inspect.isawaitable(outcome):
                        await outcome

                async def _on_eval(context, evaluator_name: str):
                    for listener in self.listeners:
                        if hasattr(listener, "on_evaluation_completed"):
                            outcome = listener.on_evaluation_completed(  # type: ignore[attr-defined]
                                experiment_id, evaluator_name
                            )
                            if inspect.isawaitable(outcome):
                                await outcome

                evaluation_results = await evaluate_async(
                    contexts, evaluators, on_evaluation_completed=_on_eval
                )
                apply_evaluations_to_results(results, evaluation_results)
                for result in results:
                    for listener in self.listeners:
                        if hasattr(listener, "on_task_evaluated"):
                            outcome = listener.on_task_evaluated(experiment_id, result)  # type: ignore[attr-defined]
                            if inspect.isawaitable(outcome):
                                await outcome

            # Step 3: Aggregate evaluators (run-once over the full run)
            aggregate_scores: dict[str, float] = {}
            aggregate_metadata: dict[str, dict[str, Any]] = {}
            if aggregate_evaluators:
                aggregate_context = AggregateEvaluationContext(
                    experiment_id=experiment_id,
                    config=config,
                    contexts=contexts,
                    results=results,
                    examples=examples,
                    started_at=started_at,
                )
                aggregate_result = await evaluate_aggregate_async(
                    aggregate_context, aggregate_evaluators
                )
                aggregate_scores = aggregate_result.get("aggregate_scores", {})
                aggregate_metadata = aggregate_result.get("aggregate_metadata", {})

            completed_at = datetime.now(timezone.utc)

            if aggregate_evaluators:
                for listener in self.listeners:
                    if hasattr(listener, "on_aggregate_completed"):
                        outcome = listener.on_aggregate_completed(
                            experiment_id,
                            aggregate_scores,
                            aggregate_metadata,
                        )
                        if inspect.isawaitable(outcome):
                            await outcome

            # Calculate summary statistics
            total_examples = len(results)
            successful_examples = len([r for r in results if not r.error])

            # Calculate average scores per metric (across all evaluators)
            evaluator_averages = {}
            if evaluators and results:
                # Collect all unique metric names from results
                all_metric_names = set()
                for result in results:
                    if not result.error:
                        all_metric_names.update(result.evaluation_scores.keys())

                # Calculate average for each metric
                for metric_name in all_metric_names:
                    scores = [
                        r.evaluation_scores.get(metric_name, 0.0)
                        for r in results
                        if not r.error and metric_name in r.evaluation_scores
                    ]
                    evaluator_averages[metric_name] = sum(scores) / len(scores) if scores else 0.0

            summary = ExperimentSummary(
                total_examples=total_examples,
                successful_examples=successful_examples,
                failed_examples=total_examples - successful_examples,
                average_scores=evaluator_averages,
                aggregate_scores=aggregate_scores,
                aggregate_metadata=aggregate_metadata,
                total_execution_time_ms=sum(r.execution_time_ms or 0 for r in results),
                experiment_id=experiment_id,
                config=config,
                started_at=started_at,
                completed_at=completed_at,
            )

            if total_examples > 0 and successful_examples == 0:
                error_message = next((r.error for r in results if r.error), "all runs failed")
                raise RuntimeError(f"Experiment failed: {error_message}")

            # Notify listeners that experiment completed
            for listener in self.listeners:
                if hasattr(listener, "on_experiment_completed"):
                    outcome = listener.on_experiment_completed(experiment_id, results, summary)
                    if inspect.isawaitable(outcome):
                        await outcome

            return summary

        except Exception as e:
            # Notify listeners of experiment failure
            for listener in self.listeners:
                if hasattr(listener, "on_experiment_failed"):
                    outcome = listener.on_experiment_failed(experiment_id, str(e))
                    if inspect.isawaitable(outcome):
                        await outcome
            raise


# Forward references to avoid circular imports
ExperimentListener = "ExperimentListener"
AsyncExperimentListener = "AsyncExperimentListener"


def _build_summary_from_results(
    *,
    results: list[ExperimentResult],
    config: ExperimentConfig,
    experiment_id: str,
    aggregate_scores: dict[str, float] | None = None,
    aggregate_metadata: dict[str, dict[str, Any]] | None = None,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
) -> ExperimentSummary:
    total_examples = len(results)
    successful_examples = len([r for r in results if not r.error])

    evaluator_averages: dict[str, float] = {}
    if results:
        all_metric_names = set()
        for result in results:
            if not result.error:
                all_metric_names.update(result.evaluation_scores.keys())
        for metric_name in all_metric_names:
            scores = [
                r.evaluation_scores.get(metric_name, 0.0)
                for r in results
                if not r.error and metric_name in r.evaluation_scores
            ]
            evaluator_averages[metric_name] = sum(scores) / len(scores) if scores else 0.0

    if started_at is None:
        started_at = min(
            (r.started_at for r in results if r.started_at), default=datetime.now(timezone.utc)
        )
    if completed_at is None:
        completed_at = max(
            (r.completed_at for r in results if r.completed_at), default=datetime.now(timezone.utc)
        )

    return ExperimentSummary(
        total_examples=total_examples,
        successful_examples=successful_examples,
        failed_examples=total_examples - successful_examples,
        average_scores=evaluator_averages,
        aggregate_scores=aggregate_scores or {},
        aggregate_metadata=aggregate_metadata or {},
        total_execution_time_ms=sum(r.execution_time_ms or 0 for r in results),
        experiment_id=experiment_id,
        config=config,
        started_at=started_at,
        completed_at=completed_at,
    )
