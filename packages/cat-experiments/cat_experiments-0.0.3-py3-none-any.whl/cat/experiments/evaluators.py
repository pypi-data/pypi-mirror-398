"""Built-in evaluators for evaluation experiments.

This module provides standard evaluators that can be used with the evaluation
pipeline, including tool call correctness evaluation.
"""

from dataclasses import dataclass
from typing import Any, Literal

from .models import EvaluationContext, EvaluationMetric
from .tool_call_matching import ToolCallMatchingResult, match_tool_calls


@dataclass
class ToolCorrectnessConfig:
    """Configuration for tool correctness evaluation."""

    mode: Literal["exact", "strict", "fuzzy"] = "strict"
    fuzzy_threshold: float = 0.5
    weight_precision: float = 0.5
    weight_recall: float = 0.5


def tool_correctness_evaluator(
    context: EvaluationContext, config: ToolCorrectnessConfig | None = None
) -> EvaluationMetric:
    """Evaluate tool call correctness by comparing expected vs actual tool calls.

    This evaluator implements tool correctness evaluation by comparing the
    tool calls that were expected versus those that were actually made.

    Args:
        context: Evaluation context with expected and actual tool calls
        config: Configuration for matching behavior

    Returns:
        Evaluation metric with tool correctness score and detailed metadata
    """
    if config is None:
        config = ToolCorrectnessConfig()

    # Handle missing tool call data
    expected_tools = context.expected_tool_calls or []
    actual_tools = context.actual_tool_calls or []

    # If no tool calls are expected and none were made, perfect score
    if not expected_tools and not actual_tools:
        return EvaluationMetric(
            name="tool_correctness",
            score=1.0,
            metadata={
                "reason": "No tool calls expected or made",
                "mode": config.mode,
                "precision": 1.0,
                "recall": 1.0,
                "expected_count": 0,
                "actual_count": 0,
                "matches": [],
                "extra_tools": [],
                "missing_tools": [],
            },
        )

    # If no tool calls expected but some were made, score based on mode
    if not expected_tools and actual_tools:
        # In some contexts, unexpected tool calls might be acceptable
        # This is configurable behavior
        return EvaluationMetric(
            name="tool_correctness",
            score=0.0,  # Conservative: unexpected tools are incorrect
            metadata={
                "reason": (
                    f"Unexpected tool calls made: {len(actual_tools)} tools called "
                    f"but none expected"
                ),
                "mode": config.mode,
                "precision": 0.0,
                "recall": 1.0,  # No expected calls to miss
                "expected_count": 0,
                "actual_count": len(actual_tools),
                "matches": [],
                "extra_tools": [_tool_to_dict(t) for t in actual_tools],
                "missing_tools": [],
            },
        )

    # If tool calls expected but none were made
    if expected_tools and not actual_tools:
        return EvaluationMetric(
            name="tool_correctness",
            score=0.0,
            metadata={
                "reason": (
                    f"Missing tool calls: {len(expected_tools)} tools expected but none called"
                ),
                "mode": config.mode,
                "precision": 1.0,  # No false positives
                "recall": 0.0,  # All expected calls missed
                "expected_count": len(expected_tools),
                "actual_count": 0,
                "matches": [],
                "extra_tools": [],
                "missing_tools": [_tool_to_dict(t) for t in expected_tools],
            },
        )

    # Perform tool call matching
    matching_result = match_tool_calls(expected_tools, actual_tools, config.mode)

    # Calculate final score based on precision and recall weights
    final_score = (
        config.weight_precision * matching_result.precision
        + config.weight_recall * matching_result.recall
    )

    # Generate human-readable reason
    reason = _generate_reason(matching_result, config)

    return EvaluationMetric(
        name="tool_correctness",
        score=final_score,
        metadata={
            "reason": reason,
            "mode": matching_result.mode,
            "precision": matching_result.precision,
            "recall": matching_result.recall,
            "overall_score": matching_result.overall_score,
            "expected_count": len(expected_tools),
            "actual_count": len(actual_tools),
            "exact_matches": len([m for m in matching_result.matches if m.match_type == "exact"]),
            "partial_matches": len(
                [m for m in matching_result.matches if m.match_type == "partial"]
            ),
            "missing_matches": len(
                [m for m in matching_result.matches if m.match_type == "missing"]
            ),
            "matches": [_match_to_dict(m) for m in matching_result.matches],
            "extra_tools": [_tool_to_dict(t) for t in matching_result.extra_tools],
            "missing_tools": [_tool_to_dict(t) for t in matching_result.missing_tools],
            "config": {
                "mode": config.mode,
                "fuzzy_threshold": config.fuzzy_threshold,
                "weight_precision": config.weight_precision,
                "weight_recall": config.weight_recall,
            },
        },
    )


def basic_tool_correctness_evaluator(context: EvaluationContext) -> EvaluationMetric:
    """Basic tool correctness evaluator with default strict matching."""
    return tool_correctness_evaluator(context, ToolCorrectnessConfig(mode="strict"))


def exact_tool_correctness_evaluator(context: EvaluationContext) -> EvaluationMetric:
    """Exact tool correctness evaluator - order and details must match perfectly."""
    return tool_correctness_evaluator(context, ToolCorrectnessConfig(mode="exact"))


# Async wrapper versions for use with AsyncExperimentRunner


async def tool_correctness_evaluator_async(
    context: EvaluationContext, config: ToolCorrectnessConfig | None = None
) -> EvaluationMetric:
    """Async wrapper for tool_correctness_evaluator.

    This is a simple async wrapper around the synchronous tool_correctness_evaluator.
    Since tool call evaluation is purely computational with no I/O, this just calls
    the sync version directly.

    Args:
        context: Evaluation context with expected and actual tool calls
        config: Configuration for matching behavior

    Returns:
        Evaluation metric with tool correctness score and detailed metadata
    """
    return tool_correctness_evaluator(context, config)


async def basic_tool_correctness_evaluator_async(context: EvaluationContext) -> EvaluationMetric:
    """Async wrapper for basic_tool_correctness_evaluator with default strict matching.

    Args:
        context: Evaluation context with expected and actual tool calls

    Returns:
        Evaluation metric with tool correctness score using strict matching
    """
    return basic_tool_correctness_evaluator(context)


async def exact_tool_correctness_evaluator_async(context: EvaluationContext) -> EvaluationMetric:
    """Async wrapper for exact_tool_correctness_evaluator - order and details must match perfectly.

    Args:
        context: Evaluation context with expected and actual tool calls

    Returns:
        Evaluation metric with tool correctness score using exact matching
    """
    return exact_tool_correctness_evaluator(context)


def _generate_reason(result: ToolCallMatchingResult, config: ToolCorrectnessConfig) -> str:
    """Generate human-readable reason for the evaluation result."""
    exact_count = len([m for m in result.matches if m.match_type == "exact"])
    partial_count = len([m for m in result.matches if m.match_type == "partial"])
    missing_count = len([m for m in result.matches if m.match_type == "missing"])
    extra_count = len(result.extra_tools)

    expected_count = len(result.matches)

    if result.mode == "exact":
        if exact_count == expected_count and extra_count == 0:
            return (
                f"Perfect match: {exact_count}/{expected_count} tool calls correct with exact order"
            )
        else:
            issues = []
            if missing_count > 0:
                issues.append(f"{missing_count} missing")
            if extra_count > 0:
                issues.append(f"{extra_count} unexpected")
            if partial_count > 0:
                issues.append(f"{partial_count} incorrect")

            return f"Tool call issues: {', '.join(issues)} (exact mode)"

    elif result.mode == "strict":
        if exact_count == expected_count and extra_count == 0:
            return f"Perfect match: {exact_count}/{expected_count} tool calls correct"
        else:
            correct_ratio = f"{exact_count}/{expected_count}"
            issues = []
            if missing_count > 0:
                issues.append(f"{missing_count} missing")
            if extra_count > 0:
                issues.append(f"{extra_count} unexpected")

            issue_text = f" ({', '.join(issues)})" if issues else ""
            return f"Tool correctness: {correct_ratio} calls matched{issue_text}"

    else:  # fuzzy mode
        if result.overall_score >= 0.95:
            return (
                f"Excellent match: {result.overall_score:.1%} similarity "
                f"across {expected_count} tool calls"
            )
        elif result.overall_score >= 0.8:
            return f"Good match: {result.overall_score:.1%} similarity with minor differences"
        elif result.overall_score >= 0.5:
            return f"Partial match: {result.overall_score:.1%} similarity with some differences"
        else:
            return (
                f"Poor match: {result.overall_score:.1%} similarity, significant differences found"
            )


def _tool_to_dict(tool) -> dict[str, Any]:
    """Convert ToolCall to dictionary for metadata."""
    return {
        "name": tool.name,
        "args": tool.args,
        "result": getattr(tool, "result", None),
        "error": getattr(tool, "error", None),
        "execution_time_ms": getattr(tool, "execution_time_ms", None),
    }


def _match_to_dict(match) -> dict[str, Any]:
    """Convert ToolCallMatch to dictionary for metadata."""
    return {
        "expected": _tool_to_dict(match.expected_tool),
        "matched": _tool_to_dict(match.matched_tool) if match.matched_tool else None,
        "similarity_score": match.similarity_score,
        "match_type": match.match_type,
        "differences": match.differences,
    }
