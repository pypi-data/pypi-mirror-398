"""Test core evaluation functionality."""

import asyncio
import os
import sys

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cat.experiments import (
    DatasetExample,
    EvaluationContext,
    EvaluationMetric,
    TestCase,
    evaluate,
    evaluate_async,
    generate,
    generate_async,
    run_experiment,
)


def as_runs(examples, repetitions: int = 1):
    """Utility to expand dataset examples into example runs for tests."""
    runs = []
    for example in examples:
        for rep in range(1, repetitions + 1):
            runs.append(TestCase(example=example, repetition_number=rep))
    return runs


class TestGenerate:
    """Test the generate function."""

    def test_generate_basic_string_output(self):
        """Test generate with simple string output."""

        def test_function(example):
            return "Hello World"

        example = DatasetExample(
            input={"messages": [{"role": "user", "content": "Say hello"}]},
            output={"messages": [{"role": "assistant", "content": "Hello World"}]},
        )

        contexts = generate(as_runs([example]), test_function)

        assert len(contexts) == 1
        context = contexts[0]
        assert context.example_id == example.id
        assert context.actual_output == "Hello World"
        assert context.input == example.input
        assert context.output == example.output
        assert context.error is None
        assert context.execution_time_ms is not None
        assert context.execution_time_ms >= 0

    def test_generate_with_dict_output(self):
        """Test generate with dictionary output - should preserve dict structure."""

        def test_function(example):
            return {"response": "Processed query", "status": "success"}

        example = DatasetExample(
            input={"query": "test"},
            output={"response": "Expected response"},
        )

        contexts = generate(as_runs([example]), test_function)

        assert len(contexts) == 1
        context = contexts[0]
        assert isinstance(context.actual_output, dict)
        assert context.actual_output["response"] == "Processed query"
        assert context.actual_output["status"] == "success"

    def test_generate_with_generic_dict(self):
        """Test generate with arbitrary dict structure - any keys should work."""

        def test_function(example):
            return {
                "custom_field": "value",
                "nested": {"data": [1, 2, 3]},
                "count": 42,
            }

        example = DatasetExample(
            input={"query": "test"},
            output={"result": "expected"},
        )

        contexts = generate(as_runs([example]), test_function)

        assert len(contexts) == 1
        context = contexts[0]
        assert isinstance(context.actual_output, dict)
        assert context.actual_output["custom_field"] == "value"
        assert context.actual_output["nested"]["data"] == [1, 2, 3]
        assert context.actual_output["count"] == 42

    def test_generate_with_error(self):
        """Test generate when test function raises an exception."""

        def test_function(example):
            raise ValueError("Test error")

        example = DatasetExample(
            input={"query": "test"},
            output={"response": "Expected response"},
        )

        contexts = generate(as_runs([example]), test_function)

        assert len(contexts) == 1
        context = contexts[0]
        assert context.actual_output is None
        assert context.error == "Test error"
        assert "error_traceback" in context.execution_metadata

    def test_generate_multiple_examples(self):
        """Test generate with multiple examples."""

        def test_function(example):
            query = example.input.get("query", "")
            return f"Response to: {query}"

        examples = [
            DatasetExample(
                input={"query": "first"},
                output={"response": "First response"},
            ),
            DatasetExample(
                input={"query": "second"},
                output={"response": "Second response"},
            ),
        ]

        contexts = generate(as_runs(examples), test_function)

        assert len(contexts) == 2
        assert contexts[0].actual_output == "Response to: first"
        assert contexts[1].actual_output == "Response to: second"

    @pytest.mark.asyncio
    async def test_generate_async_with_sync_function(self):
        """Test generate_async rejects synchronous test function."""

        def test_function(example):
            return "Sync response"

        example = DatasetExample(
            input={"query": "test"},
            output={"response": "Expected response"},
        )

        # Should fail because test_function is sync, not async
        contexts = await generate_async(as_runs([example]), test_function)  # type: ignore[arg-type]

        # The sync function will be treated as an async function, but won't work properly
        # So we expect an empty output or error
        assert len(contexts) == 1
        assert contexts[0].actual_output is None  # Should be empty due to improper handling
        assert contexts[0].error is not None  # Should have an error

    @pytest.mark.asyncio
    async def test_generate_async_with_async_function(self):
        """Test generate_async with asynchronous test function."""

        async def async_test_function(example):
            await asyncio.sleep(0.01)  # Simulate async work
            return "Async response"

        example = DatasetExample(
            input={"query": "test"},
            output={"response": "Expected response"},
        )

        contexts = await generate_async(as_runs([example]), async_test_function)

        assert len(contexts) == 1
        assert contexts[0].actual_output == "Async response"


class TestEvaluate:
    """Test the evaluate function."""

    def test_evaluate_simple_metric(self):
        """Test evaluate with simple float return."""

        def simple_evaluator(context):
            return 0.8

        context = EvaluationContext(
            example_id="test",
            run_id="test#1",
            repetition_number=1,
            actual_output="Test output",
            input={"query": "test"},
            output={"response": "expected"},
        )

        results = evaluate([context], [simple_evaluator])

        assert len(results) == 1
        result = results[0]
        assert result["evaluation_scores"]["simple_evaluator"] == 0.8
        assert result["actual_output"] == "Test output"

    def test_evaluate_with_evaluation_metric(self):
        """Test evaluate with EvaluationMetric return."""

        def metric_evaluator(context):
            return EvaluationMetric(
                name="custom_metric",
                score=0.9,
                label="good",
                explanation="This is a good result",
                metadata={"confidence": 0.95},
            )

        context = EvaluationContext(
            example_id="test",
            run_id="test#1",
            repetition_number=1,
            actual_output="Test output",
        )

        results = evaluate([context], [metric_evaluator])

        assert len(results) == 1
        result = results[0]
        assert result["evaluation_scores"]["custom_metric"] == 0.9
        metadata = result["evaluator_metadata"]["custom_metric"]
        assert metadata["confidence"] == 0.95

    def test_evaluate_with_tuple_return(self):
        """Test evaluate with (score, metadata) tuple return."""

        def tuple_evaluator(context):
            return 0.7, {"reason": "Partially correct", "details": {"missing": 1}}

        context = EvaluationContext(
            example_id="test",
            run_id="test#1",
            repetition_number=1,
            actual_output="Test output",
        )

        results = evaluate([context], [tuple_evaluator])

        assert len(results) == 1
        result = results[0]
        assert result["evaluation_scores"]["tuple_evaluator"] == 0.7
        metadata = result["evaluator_metadata"]["tuple_evaluator"]
        assert metadata["reason"] == "Partially correct"
        assert metadata["details"] == {"missing": 1}

    def test_evaluate_with_error(self):
        """Test evaluate when evaluator raises an exception."""

        def failing_evaluator(context):
            raise ValueError("Evaluator failed")

        context = EvaluationContext(
            example_id="test",
            run_id="test#1",
            repetition_number=1,
            actual_output="Test output",
        )

        results = evaluate([context], [failing_evaluator])

        assert len(results) == 1
        result = results[0]
        assert result["evaluation_scores"]["failing_evaluator"] == 0.0
        assert "error" in result["evaluator_metadata"]["failing_evaluator"]

    def test_evaluate_multiple_evaluators(self):
        """Test evaluate with multiple evaluators."""

        def evaluator_1(context):
            return 0.8

        def evaluator_2(context):
            return 0.6

        context = EvaluationContext(
            example_id="test",
            run_id="test#1",
            repetition_number=1,
            actual_output="Test output",
        )

        results = evaluate([context], [evaluator_1, evaluator_2])

        assert len(results) == 1
        result = results[0]
        assert result["evaluation_scores"]["evaluator_1"] == 0.8
        assert result["evaluation_scores"]["evaluator_2"] == 0.6

    @pytest.mark.asyncio
    async def test_evaluate_async_with_sync_evaluator(self):
        """Test evaluate_async rejects synchronous evaluator."""

        def sync_evaluator(context):
            return 0.8

        context = EvaluationContext(
            example_id="test",
            run_id="test#1",
            repetition_number=1,
            actual_output="Test output",
        )

        results = await evaluate_async([context], [sync_evaluator])  # type: ignore[list-item]

        # Should fail because sync_evaluator is not async, so score should be 0.0 (error case)
        assert len(results) == 1
        assert results[0]["evaluation_scores"]["sync_evaluator"] == 0.0
        assert results[0]["evaluator_metadata"]["sync_evaluator"]["error"] is not None

    @pytest.mark.asyncio
    async def test_evaluate_async_with_async_evaluator(self):
        """Test evaluate_async with asynchronous evaluator."""

        async def async_evaluator(context):
            await asyncio.sleep(0.01)  # Simulate async work
            return 0.9

        context = EvaluationContext(
            example_id="test",
            run_id="test#1",
            repetition_number=1,
            actual_output="Test output",
        )

        results = await evaluate_async([context], [async_evaluator])

        assert len(results) == 1
        assert results[0]["evaluation_scores"]["async_evaluator"] == 0.9


class TestRunExperiment:
    """Test the run_experiment convenience function."""

    def test_run_experiment_complete_flow(self):
        """Test complete experiment flow from examples to results."""

        def test_function(example):
            query = example.input.get("query", "")
            return f"Processed: {query}"

        def accuracy_evaluator(context):
            # Simple evaluator that checks if actual contains expected
            expected = context.output.get("response", "")
            actual_raw = context.actual_output
            actual = actual_raw if isinstance(actual_raw, str) else str(actual_raw)
            score = 1.0 if expected.lower() in actual.lower() else 0.0
            return EvaluationMetric(
                name="accuracy", score=score, metadata={"expected": expected, "actual": actual}
            )

        examples = [
            DatasetExample(
                input={"query": "hello"},
                output={"response": "hello"},
            ),
            DatasetExample(
                input={"query": "world"},
                output={"response": "world"},
            ),
        ]

        result = run_experiment(examples, test_function, [accuracy_evaluator])

        assert "results" in result
        assert "summary" in result

        # Check results
        assert len(result["results"]) == 2
        for res in result["results"]:
            assert res["evaluation_scores"]["accuracy"] == 1.0

        # Check summary
        summary = result["summary"]
        assert summary["total_examples"] == 2
        assert summary["successful_examples"] == 2
        assert summary["failed_examples"] == 0
        assert summary["average_scores"]["accuracy"] == 1.0

    def test_run_experiment_with_failures(self):
        """Test run_experiment with some failed examples."""

        def failing_test_function(example):
            if "fail" in example.input.get("query", ""):
                raise ValueError("Intentional failure")
            return "Success"

        def simple_evaluator(context):
            return 1.0

        examples = [
            DatasetExample(
                input={"query": "success"},
                output={"response": "Success"},
            ),
            DatasetExample(
                input={"query": "fail please"},
                output={"response": "Success"},
            ),
        ]

        result = run_experiment(examples, failing_test_function, [simple_evaluator])

        # Check summary accounts for failures
        summary = result["summary"]
        assert summary["total_examples"] == 2
        assert summary["successful_examples"] == 1
        assert summary["failed_examples"] == 1

        # Failed examples should have 0.0 scores excluded from average
        assert summary["average_scores"]["simple_evaluator"] == 1.0
