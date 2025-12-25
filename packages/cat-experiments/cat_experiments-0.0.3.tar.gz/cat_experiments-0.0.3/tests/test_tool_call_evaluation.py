"""Test tool call evaluation functionality."""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cat.experiments import (
    DatasetExample,
    EvaluationContext,
    TestCase,
    ToolCall,
    ToolCorrectnessConfig,
    basic_tool_correctness_evaluator,
    evaluate,
    exact_tool_correctness_evaluator,
    generate,
    match_tool_calls,
    tool_correctness_evaluator,
)


class TestToolCallMatching:
    """Test core tool call matching algorithms."""

    def test_exact_matching_perfect(self):
        """Test exact matching with perfect tool calls."""
        expected = [ToolCall(name="search", args={"query": "python", "limit": 10})]
        actual = [ToolCall(name="search", args={"query": "python", "limit": 10})]

        result = match_tool_calls(expected, actual, "exact")

        assert result.overall_score == 1.0
        assert result.precision == 1.0
        assert result.recall == 1.0
        assert len(result.matches) == 1
        assert result.matches[0].match_type == "exact"
        assert len(result.extra_tools) == 0
        assert len(result.missing_tools) == 0

    def test_exact_matching_wrong_order(self):
        """Test exact matching fails with wrong order."""
        expected = [
            ToolCall(name="search", args={"query": "python"}),
            ToolCall(name="summarize", args={"text": "results"}),
        ]
        actual = [
            ToolCall(name="summarize", args={"text": "results"}),
            ToolCall(name="search", args={"query": "python"}),
        ]

        result = match_tool_calls(expected, actual, "exact")

        assert result.overall_score == 0.0
        assert result.precision == 0.0
        assert result.recall == 0.0
        assert len(result.matches) == 2
        assert all(m.match_type == "partial" for m in result.matches)

    def test_strict_matching_ignores_order(self):
        """Test strict matching ignores order but requires exact tool calls."""
        expected = [
            ToolCall(name="search", args={"query": "python"}),
            ToolCall(name="summarize", args={"text": "results"}),
        ]
        actual = [
            ToolCall(name="summarize", args={"text": "results"}),
            ToolCall(name="search", args={"query": "python"}),
        ]

        result = match_tool_calls(expected, actual, "strict")

        assert result.overall_score == 1.0
        assert result.precision == 1.0
        assert result.recall == 1.0
        assert len(result.matches) == 2
        assert all(m.match_type == "exact" for m in result.matches)

    def test_fuzzy_matching_partial_similarity(self):
        """Test fuzzy matching with partial tool similarity."""
        expected = [ToolCall(name="search", args={"query": "python programming"})]
        actual = [ToolCall(name="search", args={"query": "python"})]

        result = match_tool_calls(expected, actual, "fuzzy")

        assert result.overall_score > 0.5  # Should be partial match
        assert result.precision > 0.0
        assert result.recall > 0.0
        assert len(result.matches) == 1
        assert result.matches[0].match_type in ["exact", "partial"]

    def test_missing_tool_calls(self):
        """Test handling of missing tool calls."""
        expected = [ToolCall(name="search", args={"query": "python"})]
        actual = []

        result = match_tool_calls(expected, actual, "strict")

        assert result.overall_score == 0.0
        assert result.precision == 1.0  # No false positives
        assert result.recall == 0.0  # All expected calls missed
        assert len(result.matches) == 1
        assert result.matches[0].match_type == "missing"
        assert len(result.missing_tools) == 1

    def test_extra_tool_calls(self):
        """Test handling of unexpected tool calls."""
        expected = []
        actual = [ToolCall(name="search", args={"query": "python"})]

        result = match_tool_calls(expected, actual, "strict")

        assert result.overall_score == 1.0  # No expected tools to miss
        assert result.precision == 0.0  # All actual calls are false positives
        assert result.recall == 1.0  # No expected calls to miss
        assert len(result.matches) == 0
        assert len(result.extra_tools) == 1


class TestToolCorrectnessEvaluator:
    """Test the tool correctness evaluator."""

    def test_perfect_tool_correctness(self):
        """Test evaluator with perfect tool call match."""
        expected_tools = [ToolCall(name="search", args={"query": "python"})]
        actual_tools = [ToolCall(name="search", args={"query": "python"})]

        context = EvaluationContext(
            example_id="test",
            run_id="test#1",
            repetition_number=1,
            actual_output="Found Python resources",
            expected_tool_calls=expected_tools,
            actual_tool_calls=actual_tools,
        )

        result = tool_correctness_evaluator(context)

        assert result.name == "tool_correctness"
        assert result.score == 1.0
        assert "Perfect match" in result.metadata["reason"]
        assert result.metadata["precision"] == 1.0
        assert result.metadata["recall"] == 1.0

    def test_no_tools_expected_or_actual(self):
        """Test evaluator when no tools are expected or used."""
        context = EvaluationContext(
            example_id="test",
            run_id="test#1",
            repetition_number=1,
            actual_output="Simple text response",
            expected_tool_calls=None,
            actual_tool_calls=None,
        )

        result = tool_correctness_evaluator(context)

        assert result.score == 1.0
        assert "No tool calls expected or made" in result.metadata["reason"]

    def test_missing_tool_calls_evaluation(self):
        """Test evaluator when expected tools are missing."""
        expected_tools = [ToolCall(name="search", args={"query": "python"})]
        actual_tools = []

        context = EvaluationContext(
            example_id="test",
            run_id="test#1",
            repetition_number=1,
            actual_output="No search performed",
            expected_tool_calls=expected_tools,
            actual_tool_calls=actual_tools,
        )

        result = tool_correctness_evaluator(context)

        assert result.score == 0.0
        assert "Missing tool calls" in result.metadata["reason"]
        assert result.metadata["precision"] == 1.0
        assert result.metadata["recall"] == 0.0

    def test_unexpected_tool_calls_evaluation(self):
        """Test evaluator when unexpected tools are used."""
        expected_tools = []
        actual_tools = [ToolCall(name="search", args={"query": "python"})]

        context = EvaluationContext(
            example_id="test",
            run_id="test#1",
            repetition_number=1,
            actual_output="Searched for Python",
            expected_tool_calls=expected_tools,
            actual_tool_calls=actual_tools,
        )

        result = tool_correctness_evaluator(context)

        assert result.score == 0.0
        assert "Unexpected tool calls made" in result.metadata["reason"]

    def test_weighted_precision_recall(self):
        """Test custom precision/recall weighting."""
        expected_tools = [
            ToolCall(name="search", args={"query": "python"}),
            ToolCall(name="summarize", args={"text": "results"}),
        ]
        actual_tools = [ToolCall(name="search", args={"query": "python"})]  # Missing one

        config = ToolCorrectnessConfig(weight_precision=0.7, weight_recall=0.3)

        context = EvaluationContext(
            example_id="test",
            run_id="test#1",
            repetition_number=1,
            actual_output="Partial results",
            expected_tool_calls=expected_tools,
            actual_tool_calls=actual_tools,
        )

        result = tool_correctness_evaluator(context, config)

        # Should favor precision (1.0) over recall (0.5)
        expected_score = 0.7 * 1.0 + 0.3 * 0.5  # 0.85
        assert abs(result.score - expected_score) < 0.01

    def test_basic_evaluator_convenience(self):
        """Test basic tool correctness evaluator convenience function."""
        expected_tools = [ToolCall(name="search", args={"query": "python"})]
        actual_tools = [ToolCall(name="search", args={"query": "python"})]

        context = EvaluationContext(
            example_id="test",
            run_id="test#1",
            repetition_number=1,
            actual_output="Found results",
            expected_tool_calls=expected_tools,
            actual_tool_calls=actual_tools,
        )

        result = basic_tool_correctness_evaluator(context)

        assert result.name == "tool_correctness"
        assert result.score == 1.0
        assert result.metadata["mode"] == "strict"

    def test_exact_evaluator_convenience(self):
        """Test exact tool correctness evaluator convenience function."""
        expected_tools = [ToolCall(name="search", args={"query": "python"})]
        actual_tools = [ToolCall(name="search", args={"query": "python"})]

        context = EvaluationContext(
            example_id="test",
            run_id="test#1",
            repetition_number=1,
            actual_output="Found results",
            expected_tool_calls=expected_tools,
            actual_tool_calls=actual_tools,
        )

        result = exact_tool_correctness_evaluator(context)

        assert result.name == "tool_correctness"
        assert result.score == 1.0
        assert result.metadata["mode"] == "exact"


class TestEvaluationIntegration:
    """Test integration with the evaluation pipeline."""

    def test_generate_and_evaluate_with_tool_calls(self):
        """Test full pipeline with tool call evaluation."""

        def test_function(example):
            # Simulate a function that makes tool calls based on input
            if "search" in str(example.input):
                return "Found Python documentation"
            return "No search performed"

        # Create example with expected tool calls
        example = DatasetExample(
            input={"query": "search for python docs"},
            output={"response": "Found Python documentation"},
        )
        example.expected_tool_calls = [ToolCall(name="search", args={"query": "python docs"})]

        # Generate contexts (this would normally extract tool calls from execution)
        contexts = generate([TestCase(example=example, repetition_number=1)], test_function)

        assert len(contexts) == 1
        context = contexts[0]
        assert context.example_id == example.id
        assert context.actual_output == "Found Python documentation"

        # Note: In real usage, tool calls would be extracted from execution traces
        # For this test, we'll manually set them to simulate the extraction
        context.actual_tool_calls = [ToolCall(name="search", args={"query": "python docs"})]

        # Evaluate with tool correctness
        results = evaluate(contexts, [basic_tool_correctness_evaluator])

        assert len(results) == 1
        result = results[0]
        assert result["evaluation_scores"]["tool_correctness"] == 1.0
        assert "Perfect match" in result["evaluator_metadata"]["tool_correctness"]["reason"]

    def test_backward_compatibility_arguments_property(self):
        """Test backward compatibility for arguments property on ToolCall."""
        tool = ToolCall(name="search", args={"query": "python"})

        # Test property access
        assert tool.arguments == {"query": "python"}

        # Test property setter
        tool.arguments = {"query": "java"}
        assert tool.args == {"query": "java"}
        assert tool.arguments == {"query": "java"}
