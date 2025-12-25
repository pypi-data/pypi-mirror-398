"""
cat-experiments: Standalone evaluation engine for LLM applications.

A flexible, DataFrame-compatible evaluation system that works standalone
or integrates with cat-cafe server infrastructure.
"""

from .adapters.local_storage import (
    LocalStorageExperimentListener,
    LocalStorageSyncConfig,
    build_local_runner,
    build_local_runner_async,
)
from .adapters.local_storage_evaluator import LocalEvaluationCoordinator, LocalEvaluationPlan
from .adapters.local_storage_resume import LocalCacheResumeCoordinator, LocalTaskResumePlan
from .agg_ci import make_wilson_ci_aggregate
from .evaluation import (
    evaluate,
    evaluate_aggregate,
    evaluate_aggregate_async,
    evaluate_async,
    generate,
    generate_async,
    run_experiment,
)
from .evaluation_backends import EvaluationBackend, EvaluationPlanProtocol
from .evaluators import (
    ToolCorrectnessConfig,
    basic_tool_correctness_evaluator,
    basic_tool_correctness_evaluator_async,
    exact_tool_correctness_evaluator,
    exact_tool_correctness_evaluator_async,
    tool_correctness_evaluator,
    tool_correctness_evaluator_async,
)
from .experiments import (
    AsyncExperimentRunner,
    ExperimentConfig,
    ExperimentResult,
    ExperimentRunner,
    ExperimentSummary,
)
from .listeners import (
    AsyncExperimentListener,
    AsyncLoggingListener,
    ExperimentListener,
    LoggingListener,
)
from .models import (
    AggregateEvaluationContext,
    DatasetExample,
    EvaluationContext,
    EvaluationMetric,
    EvaluatorResult,
    TestCase,
    TestFunctionOutput,
    ToolCall,
)
from .tool_call_matching import (
    ToolCallMatch,
    ToolCallMatchingResult,
    match_tool_calls,
)
from .types import (
    AggregateEvaluatorFn,
    AsyncAggregateEvaluatorFn,
    AsyncEvaluatorFn,
    AsyncTestFn,
    EvaluatorFn,
    TestFn,
)

__version__ = "0.0.3"

__all__ = [
    # Core Models
    "DatasetExample",
    "AggregateEvaluationContext",
    "EvaluationContext",
    "EvaluationMetric",
    "ToolCall",
    "TestFunctionOutput",
    "EvaluatorResult",
    "TestCase",
    # CI aggregate evaluators
    "make_wilson_ci_aggregate",
    # Evaluation Functions
    "generate",
    "generate_async",
    "evaluate",
    "evaluate_aggregate",
    "evaluate_aggregate_async",
    "evaluate_async",
    "run_experiment",
    # Built-in Evaluators
    "tool_correctness_evaluator",
    "tool_correctness_evaluator_async",
    "basic_tool_correctness_evaluator",
    "basic_tool_correctness_evaluator_async",
    "exact_tool_correctness_evaluator",
    "exact_tool_correctness_evaluator_async",
    "ToolCorrectnessConfig",
    # Tool Call Matching
    "match_tool_calls",
    "ToolCallMatch",
    "ToolCallMatchingResult",
    # Experiment Infrastructure
    "ExperimentConfig",
    "ExperimentResult",
    "ExperimentSummary",
    "ExperimentRunner",
    "AsyncExperimentRunner",
    # Experiment Listeners
    "ExperimentListener",
    "AsyncExperimentListener",
    "LoggingListener",
    "AsyncLoggingListener",
    "LocalStorageExperimentListener",
    "LocalStorageSyncConfig",
    "LocalEvaluationCoordinator",
    "LocalEvaluationPlan",
    "EvaluationBackend",
    "EvaluationPlanProtocol",
    "LocalCacheResumeCoordinator",
    "LocalTaskResumePlan",
    "EvaluatorFn",
    "AsyncEvaluatorFn",
    "AggregateEvaluatorFn",
    "AsyncAggregateEvaluatorFn",
    "TestFn",
    "AsyncTestFn",
    # Runner Builders
    "build_local_runner",
    "build_local_runner_async",
]
