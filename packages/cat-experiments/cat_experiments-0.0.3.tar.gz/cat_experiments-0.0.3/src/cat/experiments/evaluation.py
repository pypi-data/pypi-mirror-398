"""Core evaluation functions with OpenTelemetry trace capture support.

This module provides the foundational generate() and evaluate() functions that
compose together to form the experiment execution pipeline, with automatic
trace capture for rich agent execution monitoring.
"""

import asyncio
import logging
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Optional, cast

from .models import (
    AgentTrace,
    AggregateEvaluationContext,
    DatasetExample,
    EvaluationContext,
    EvaluationMetric,
    EvaluatorResult,
    TestCase,
    TestFunctionOutput,
    ToolCall,
)
from .observers import (
    RunObservation,
    get_observer,
    observation_metadata,
    observation_tool_calls,
    observation_trace_id,
)
from .types import (
    AggregateEvaluatorFn,
    AggregateEvaluatorResult,
    AsyncAggregateEvaluatorFn,
    AsyncEvaluatorFn,
    AsyncTestFn,
    EvaluatorFn,
    TestFn,
)

logger = logging.getLogger(__name__)


def generate(
    runs: list[TestCase],
    test_function: TestFn,
    *,
    max_workers: int = 1,
    on_context_completed: Optional[Callable[[EvaluationContext, int], None]] = None,
) -> list[EvaluationContext]:
    """Generate evaluation contexts by executing test function on example runs.

    This function converts dataset example runs into rich evaluation contexts by:
    1. Running the test function on each example run
    2. Extracting actual output from the test function result
    3. Creating EvaluationContext objects with both expected and actual data plus run metadata

    Args:
        runs: List of dataset example runs to process
        test_function: Function that takes a DatasetExample and returns output

    Returns:
        List of evaluation contexts ready for evaluator consumption
    """
    max_workers = max(1, int(max_workers or 1))
    if not runs:
        return []

    if max_workers == 1:
        contexts: list[EvaluationContext] = []
        for index, run in enumerate(runs):
            context = _execute_test_case(run, test_function, default_example_index=index)
            if context is not None and on_context_completed:
                on_context_completed(context, index)
            contexts.append(context)
        return contexts

    context_slots: list[EvaluationContext | None] = [None] * len(runs)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                _execute_test_case,
                run,
                test_function,
                default_example_index=index,
            ): index
            for index, run in enumerate(runs)
        }

        for future in as_completed(futures):
            idx = futures[future]
            context = future.result()
            context_slots[idx] = context
            if context is not None and on_context_completed:
                on_context_completed(context, idx)

    return [cast(EvaluationContext, context) for context in context_slots if context is not None]


async def generate_async(
    runs: list[TestCase],
    test_function: AsyncTestFn,
    *,
    max_workers: int = 1,
    on_context_completed: Optional[Callable[[EvaluationContext, int], Any]] = None,
) -> list[EvaluationContext]:
    """Async version of generate() that handles async test functions only.

    Args:
        runs: List of dataset example runs to process
        test_function: Async function that takes a DatasetExample and returns output

    Returns:
        List of evaluation contexts ready for evaluator consumption
    """
    max_workers = max(1, int(max_workers or 1))
    if not runs:
        return []

    if max_workers == 1:
        contexts: list[EvaluationContext] = []
        for index, run in enumerate(runs):
            context = await _execute_test_case_async(
                run, test_function, default_example_index=index
            )
            if context is not None and on_context_completed:
                maybe_awaitable = on_context_completed(context, index)
                if asyncio.iscoroutine(maybe_awaitable):
                    await maybe_awaitable
            contexts.append(context)
        return contexts

    semaphore = asyncio.Semaphore(max_workers)

    async def _run_with_semaphore(index: int, test_case: TestCase) -> EvaluationContext:
        async with semaphore:
            context = await _execute_test_case_async(
                test_case,
                test_function,
                default_example_index=index,
            )
            if context is not None and on_context_completed:
                maybe_awaitable = on_context_completed(context, index)
                if asyncio.iscoroutine(maybe_awaitable):
                    await maybe_awaitable
            return context

    tasks = [asyncio.create_task(_run_with_semaphore(index, run)) for index, run in enumerate(runs)]
    return await asyncio.gather(*tasks)


def evaluate(
    contexts: list[EvaluationContext],
    evaluators: list[EvaluatorFn],
    *,
    on_evaluation_completed: Optional[Callable[[EvaluationContext, str], None]] = None,
) -> list[dict[str, Any]]:
    """Evaluate contexts with given evaluators.

    This function takes evaluation contexts and runs multiple evaluators on them,
    collecting scores and metadata.

    Args:
        contexts: List of evaluation contexts to evaluate
        evaluators: List of evaluator functions

    Returns:
        List of evaluation results (one per context)
    """
    results = []

    for context in contexts:
        result = {
            "example_id": context.example_id,
            "input_data": dict(context.input or {}),
            "output": dict(context.output or {}),
            "actual_output": context.actual_output,
            "evaluation_scores": {},
            "evaluator_metadata": {},
            "metadata": {
                "execution_time_ms": context.execution_time_ms,
                "error": context.error,
                "run_id": context.run_id,
                "repetition_number": context.repetition_number,
                **dict(context.execution_metadata or {}),
            },
            "error": context.error,
        }
        if context.started_at:
            result["metadata"]["started_at"] = context.started_at.isoformat()
        if context.completed_at:
            result["metadata"]["completed_at"] = context.completed_at.isoformat()
        if context.trace_id:
            result["metadata"]["trace_id"] = context.trace_id

        # Run each evaluator
        for evaluator in evaluators:
            evaluator_name = getattr(evaluator, "__name__", "evaluator")
            eval_started_at = datetime.now(timezone.utc)

            try:
                eval_start_time = time.time()
                eval_result = evaluator(context)
                eval_time = (time.time() - eval_start_time) * 1000
                eval_completed_at = datetime.now(timezone.utc)

                # Extract metric from different return types
                metric = _extract_evaluator_result(eval_result, evaluator_name)
                result["evaluation_scores"][metric.name] = metric.score
                metadata = dict(metric.metadata or {})
                if metric.label is not None:
                    metadata.setdefault("label", metric.label)
                if metric.explanation is not None:
                    metadata.setdefault("explanation", metric.explanation)
                metadata["execution_time_ms"] = eval_time
                metadata["started_at"] = eval_started_at.isoformat()
                metadata["completed_at"] = eval_completed_at.isoformat()
                result["evaluator_metadata"][metric.name] = metadata

            except Exception as e:
                eval_completed_at = datetime.now(timezone.utc)
                # Use evaluator name as fallback when we can't get metric name
                fallback_name = evaluator_name
                result["evaluation_scores"][fallback_name] = 0.0
                result["evaluator_metadata"][fallback_name] = {
                    "error": str(e),
                    "execution_time_ms": 0.0,
                    "started_at": eval_started_at.isoformat(),
                    "completed_at": eval_completed_at.isoformat(),
                }

            if on_evaluation_completed:
                on_evaluation_completed(context, evaluator_name)

        results.append(result)

    return results


def evaluate_aggregate(
    context: AggregateEvaluationContext,
    aggregate_evaluators: list[AggregateEvaluatorFn],
) -> dict[str, dict[str, Any]]:
    """Run aggregate evaluators once over the full experiment context."""
    aggregate_scores: dict[str, float] = {}
    aggregate_metadata: dict[str, dict[str, Any]] = {}

    for evaluator in aggregate_evaluators:
        evaluator_name = getattr(evaluator, "__name__", "aggregate_evaluator")
        eval_started_at = datetime.now(timezone.utc)

        try:
            eval_start_time = time.time()
            eval_result: AggregateEvaluatorResult = evaluator(context)
            eval_time = (time.time() - eval_start_time) * 1000
            eval_completed_at = datetime.now(timezone.utc)

            metrics = _extract_aggregate_metrics(eval_result, evaluator_name)
            for metric in metrics:
                aggregate_scores[metric.name] = metric.score
                metadata = dict(metric.metadata or {})
                if metric.label is not None:
                    metadata.setdefault("label", metric.label)
                if metric.explanation is not None:
                    metadata.setdefault("explanation", metric.explanation)
                metadata["execution_time_ms"] = eval_time
                metadata["started_at"] = eval_started_at.isoformat()
                metadata["completed_at"] = eval_completed_at.isoformat()
                aggregate_metadata[metric.name] = metadata

            if not metrics:
                aggregate_metadata[evaluator_name] = {
                    "warning": "aggregate evaluator returned no metrics",
                    "execution_time_ms": eval_time,
                    "started_at": eval_started_at.isoformat(),
                    "completed_at": eval_completed_at.isoformat(),
                }
        except Exception as exc:  # pragma: no cover - defensive
            eval_completed_at = datetime.now(timezone.utc)
            aggregate_scores[evaluator_name] = 0.0
            aggregate_metadata[evaluator_name] = {
                "error": str(exc),
                "execution_time_ms": 0.0,
                "started_at": eval_started_at.isoformat(),
                "completed_at": eval_completed_at.isoformat(),
            }

    return {
        "aggregate_scores": aggregate_scores,
        "aggregate_metadata": aggregate_metadata,
    }


async def evaluate_aggregate_async(
    context: AggregateEvaluationContext,
    aggregate_evaluators: list[AsyncAggregateEvaluatorFn],
) -> dict[str, dict[str, Any]]:
    """Async variant of evaluate_aggregate for async aggregate evaluators."""
    aggregate_scores: dict[str, float] = {}
    aggregate_metadata: dict[str, dict[str, Any]] = {}

    for evaluator in aggregate_evaluators:
        evaluator_name = getattr(evaluator, "__name__", "aggregate_evaluator")
        eval_started_at = datetime.now(timezone.utc)

        try:
            eval_start_time = time.time()
            eval_result: AggregateEvaluatorResult = await evaluator(context)
            eval_time = (time.time() - eval_start_time) * 1000
            eval_completed_at = datetime.now(timezone.utc)

            metrics = _extract_aggregate_metrics(eval_result, evaluator_name)
            for metric in metrics:
                aggregate_scores[metric.name] = metric.score
                metadata = dict(metric.metadata or {})
                if metric.label is not None:
                    metadata.setdefault("label", metric.label)
                if metric.explanation is not None:
                    metadata.setdefault("explanation", metric.explanation)
                metadata["execution_time_ms"] = eval_time
                metadata["started_at"] = eval_started_at.isoformat()
                metadata["completed_at"] = eval_completed_at.isoformat()
                aggregate_metadata[metric.name] = metadata

            if not metrics:
                aggregate_metadata[evaluator_name] = {
                    "warning": "aggregate evaluator returned no metrics",
                    "execution_time_ms": eval_time,
                    "started_at": eval_started_at.isoformat(),
                    "completed_at": eval_completed_at.isoformat(),
                }
        except Exception as exc:  # pragma: no cover - defensive
            eval_completed_at = datetime.now(timezone.utc)
            aggregate_scores[evaluator_name] = 0.0
            aggregate_metadata[evaluator_name] = {
                "error": str(exc),
                "execution_time_ms": 0.0,
                "started_at": eval_started_at.isoformat(),
                "completed_at": eval_completed_at.isoformat(),
            }

    return {
        "aggregate_scores": aggregate_scores,
        "aggregate_metadata": aggregate_metadata,
    }


async def evaluate_async(
    contexts: list[EvaluationContext],
    evaluators: list[AsyncEvaluatorFn],
    *,
    on_evaluation_completed: Optional[Callable[[EvaluationContext, str], Any]] = None,
) -> list[dict[str, Any]]:
    """Async version of evaluate() that handles async evaluators only.

    Args:
        contexts: List of evaluation contexts to evaluate
        evaluators: List of async evaluator functions

    Returns:
        List of evaluation results (one per context)
    """
    results = []

    for context in contexts:
        result = {
            "example_id": context.example_id,
            "input_data": dict(context.input or {}),
            "output": dict(context.output or {}),
            "actual_output": context.actual_output,
            "evaluation_scores": {},
            "evaluator_metadata": {},
            "metadata": {
                "execution_time_ms": context.execution_time_ms,
                "error": context.error,
                "run_id": context.run_id,
                "repetition_number": context.repetition_number,
                **dict(context.execution_metadata or {}),
            },
            "error": context.error,
        }
        if context.started_at:
            result["metadata"]["started_at"] = context.started_at.isoformat()
        if context.completed_at:
            result["metadata"]["completed_at"] = context.completed_at.isoformat()
        if context.trace_id:
            result["metadata"]["trace_id"] = context.trace_id

        # Run each async evaluator
        for evaluator in evaluators:
            evaluator_name = getattr(evaluator, "__name__", "evaluator")
            eval_started_at = datetime.now(timezone.utc)

            try:
                eval_start_time = time.time()
                eval_result = await evaluator(context)
                eval_time = (time.time() - eval_start_time) * 1000
                eval_completed_at = datetime.now(timezone.utc)

                # Extract metric from different return types
                metric = _extract_evaluator_result(eval_result, evaluator_name)
                result["evaluation_scores"][metric.name] = metric.score
                metadata = dict(metric.metadata or {})
                if metric.label is not None:
                    metadata.setdefault("label", metric.label)
                if metric.explanation is not None:
                    metadata.setdefault("explanation", metric.explanation)
                metadata["execution_time_ms"] = eval_time
                metadata["started_at"] = eval_started_at.isoformat()
                metadata["completed_at"] = eval_completed_at.isoformat()
                result["evaluator_metadata"][metric.name] = metadata

            except Exception as e:
                eval_completed_at = datetime.now(timezone.utc)
                # Use evaluator name as fallback when we can't get metric name
                fallback_name = evaluator_name
                result["evaluation_scores"][fallback_name] = 0.0
                result["evaluator_metadata"][fallback_name] = {
                    "error": str(e),
                    "execution_time_ms": 0.0,
                    "started_at": eval_started_at.isoformat(),
                    "completed_at": eval_completed_at.isoformat(),
                }

            if on_evaluation_completed:
                maybe_awaitable = on_evaluation_completed(context, evaluator_name)
                if asyncio.iscoroutine(maybe_awaitable):
                    await maybe_awaitable

        results.append(result)

    return results


def run_experiment(
    examples: list[DatasetExample],
    test_function: TestFn,
    evaluators: list[EvaluatorFn],
    *,
    max_workers: int = 1,
) -> dict[str, Any]:
    """High-level experiment runner that composes generate() and evaluate().

    This is the convenience function that most users will call. It combines
    context generation and evaluation into a single operation.

    Args:
        examples: Dataset examples to test
        test_function: Function to execute on each example
        evaluators: Evaluator functions to run on results

    Returns:
        Experiment results with summary statistics
    """
    # Step 1: Generate contexts
    runs = [TestCase(example=example, repetition_number=1) for example in examples]
    contexts = generate(runs, test_function, max_workers=max_workers)

    # Step 2: Evaluate contexts
    results = evaluate(contexts, evaluators)

    # Step 3: Calculate summary statistics
    total_examples = len(results)
    successful_examples = len([r for r in results if not r["error"]])

    # Calculate average scores per metric (across all evaluators)
    evaluator_averages = {}
    if evaluators and results:
        # Collect all unique metric names from results
        all_metric_names = set()
        for result in results:
            if not result["error"]:
                all_metric_names.update(result["evaluation_scores"].keys())

        # Calculate average for each metric
        for metric_name in all_metric_names:
            scores = [
                r["evaluation_scores"].get(metric_name, 0.0)
                for r in results
                if not r["error"] and metric_name in r["evaluation_scores"]
            ]
            evaluator_averages[metric_name] = sum(scores) / len(scores) if scores else 0.0

    return {
        "results": results,
        "summary": {
            "total_examples": total_examples,
            "successful_examples": successful_examples,
            "failed_examples": total_examples - successful_examples,
            "average_scores": evaluator_averages,
            "total_execution_time_ms": sum(
                r["metadata"].get("execution_time_ms", 0) for r in results
            ),
        },
    }


def _execute_test_case(
    run: TestCase,
    test_function: TestFn,
    *,
    default_example_index: int,
) -> EvaluationContext:
    example = run.example
    started_at = datetime.now(timezone.utc)
    start_time = time.time()
    error: str | None = None
    error_traceback: str | None = None
    actual_output: Any = None
    result_tool_calls: list[ToolCall] | None = None

    observer = get_observer()
    observation: RunObservation | None = None

    try:
        with observer.enter_run(
            run_id=run.run_id,
            example_id=example.id or f"example_{default_example_index}",
            repetition=run.repetition_number,
        ):
            result = test_function(example)
        actual_output, result_tool_calls = _extract_execution_data(result)
    except Exception as exc:  # pragma: no cover - exercised via tests
        error = str(exc)
        error_traceback = traceback.format_exc()
    finally:
        observation = _safe_collect_observation(observer, run.run_id)

    completed_at = datetime.now(timezone.utc)
    execution_time_ms = (time.time() - start_time) * 1000

    return _build_evaluation_context(
        run,
        example,
        default_example_index,
        actual_output,
        result_tool_calls,
        observation,
        error,
        error_traceback,
        started_at,
        completed_at,
        execution_time_ms,
    )


async def _execute_test_case_async(
    run: TestCase,
    test_function: AsyncTestFn,
    *,
    default_example_index: int,
) -> EvaluationContext:
    example = run.example
    started_at = datetime.now(timezone.utc)
    start_time = time.time()
    error: str | None = None
    error_traceback: str | None = None
    actual_output: Any = None
    result_tool_calls: list[ToolCall] | None = None

    observer = get_observer()
    observation: RunObservation | None = None

    try:
        with observer.enter_run(
            run_id=run.run_id,
            example_id=example.id or f"example_{default_example_index}",
            repetition=run.repetition_number,
        ):
            result = await test_function(example)
        actual_output, result_tool_calls = _extract_execution_data(result)
    except Exception as exc:  # pragma: no cover - exercised via tests
        error = str(exc)
        error_traceback = traceback.format_exc()
    finally:
        observation = _safe_collect_observation(observer, run.run_id)

    completed_at = datetime.now(timezone.utc)
    execution_time_ms = (time.time() - start_time) * 1000

    return _build_evaluation_context(
        run,
        example,
        default_example_index,
        actual_output,
        result_tool_calls,
        observation,
        error,
        error_traceback,
        started_at,
        completed_at,
        execution_time_ms,
    )


def _build_evaluation_context(
    run: TestCase,
    example: DatasetExample,
    default_example_index: int,
    actual_output: Any,
    result_tool_calls: list[ToolCall] | None,
    observation: RunObservation | None,
    error: str | None,
    error_traceback: str | None,
    started_at: datetime,
    completed_at: datetime,
    execution_time_ms: float,
) -> EvaluationContext:
    observer_tool_calls = observation_tool_calls(observation)
    trace_id = observation_trace_id(observation)
    actual_tool_calls = result_tool_calls or observer_tool_calls

    example_metadata = dict(example.metadata or {})
    tags = getattr(example, "tags", None)
    if tags and "tags" not in example_metadata:
        example_metadata["tags"] = list(tags)

    execution_metadata = {
        "repetition_number": run.repetition_number,
        "run_id": run.run_id,
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
    }
    if trace_id:
        execution_metadata["trace_id"] = trace_id
    if error_traceback:
        execution_metadata["error_traceback"] = error_traceback

    observer_metadata = observation_metadata(observation)
    if observer_metadata:
        execution_metadata.setdefault("observer_metadata", {}).update(observer_metadata)

    expected_tool_calls: list[ToolCall] | None = None
    expected_tool_calls_data = example_metadata.get("expected_tool_calls")
    if expected_tool_calls_data:
        expected_tool_calls = [
            tc if isinstance(tc, ToolCall) else ToolCall.from_dict(tc)
            for tc in expected_tool_calls_data
        ]

    example_id = example.id or f"example_{default_example_index}"

    return EvaluationContext(
        example_id=example_id,
        run_id=run.run_id,
        repetition_number=run.repetition_number,
        actual_output=actual_output,
        input=dict(example.input or {}),
        output=dict(example.output or {}),
        metadata={**example_metadata},
        expected_tool_calls=expected_tool_calls,
        actual_tool_calls=actual_tool_calls,
        started_at=started_at,
        completed_at=completed_at,
        execution_time_ms=execution_time_ms,
        error=error,
        execution_metadata=execution_metadata,
        trace_id=trace_id,
    )


def _safe_collect_observation(observer, run_id: str) -> RunObservation | None:
    try:
        return observer.collect_observation(run_id)
    except Exception:  # pragma: no cover - defensive
        logger.debug("Observer collect_observation failed for run %s", run_id, exc_info=True)
        return None


def _extract_execution_data(result: TestFunctionOutput) -> tuple[Any, list[ToolCall] | None]:
    """Extract output and tool calls from test function result.

    This function handles different types of test function outputs and extracts
    the relevant data for creating an EvaluationContext.

    Args:
        result: The result from executing a test function

    Returns:
        Tuple of (actual_output, actual_tool_calls)
    """
    actual_output: Any = None
    actual_tool_calls = None

    if isinstance(result, str):
        # Simple string output
        actual_output = result

    elif isinstance(result, AgentTrace):
        # Rich agent trace with tool calls
        actual_output = result.final_response
        actual_tool_calls = result.tools_called

    elif isinstance(result, dict):
        # Serialize entire dict to preserve structure
        actual_output = result

    elif isinstance(result, list):
        # List output - serialize to JSON
        actual_output = result

    elif hasattr(result, "final_response"):
        # Objects with final_response attribute
        actual_output = result.final_response

        # Check if this object also has tool calls
        if hasattr(result, "tools_called"):
            actual_tool_calls = result.tools_called

    else:
        # Fallback: return as-is
        actual_output = result

    return actual_output, actual_tool_calls


def _extract_evaluator_result(result: EvaluatorResult, evaluator_name: str) -> EvaluationMetric:
    """Extract EvaluationMetric from different evaluator return types.

    Args:
        result: Result from evaluator (float, tuple, or EvaluationMetric)
        evaluator_name: Name of the evaluator for fallback

    Returns:
        EvaluationMetric object
    """
    if isinstance(result, EvaluationMetric):
        return result
    elif isinstance(result, float):
        return EvaluationMetric(name=evaluator_name, score=result)
    elif isinstance(result, tuple) and len(result) >= 2:
        score, metadata = result[0], result[1]
        return EvaluationMetric(name=evaluator_name, score=score, metadata=metadata)
    else:
        # Fallback: treat as score-like
        return EvaluationMetric(name=evaluator_name, score=float(result))


def _extract_aggregate_metrics(
    result: AggregateEvaluatorResult,
    evaluator_name: str,
) -> list[EvaluationMetric]:
    """Normalize aggregate evaluator outputs into a list of EvaluationMetric objects."""
    if result is None:
        return []

    if isinstance(result, Mapping):
        metrics: list[EvaluationMetric] = []
        for metric_name, metric_value in result.items():
            if isinstance(metric_value, dict):
                score = float(metric_value.get("score", 0.0))
                metadata = {k: v for k, v in metric_value.items() if k != "score"}
                metric = EvaluationMetric(name=metric_name, score=score, metadata=metadata)
            else:
                metric = _extract_evaluator_result(metric_value, metric_name)
            metric.name = metric_name
            metrics.append(metric)
        return metrics

    if isinstance(result, (list, tuple)):
        metrics: list[EvaluationMetric] = []
        for idx, entry in enumerate(result):
            metric_name = f"{evaluator_name}_{idx}"
            if isinstance(entry, dict):
                score = float(entry.get("score", 0.0))
                metadata = {k: v for k, v in entry.items() if k != "score"}
                metric = EvaluationMetric(name=metric_name, score=score, metadata=metadata)
            else:
                metric = _extract_evaluator_result(entry, metric_name)
            metrics.append(metric)
        return metrics

    return [_extract_evaluator_result(result, evaluator_name)]
