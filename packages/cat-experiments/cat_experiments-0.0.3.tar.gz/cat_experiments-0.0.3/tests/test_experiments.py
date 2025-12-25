"""Test experiment runner functionality."""

import asyncio
import os
import sys
import threading
from datetime import UTC, datetime
from typing import Any

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cat.experiments import (
    AsyncExperimentRunner,
    AsyncLoggingListener,
    DatasetExample,
    EvaluationMetric,
    ExperimentConfig,
    ExperimentResult,
    ExperimentRunner,
    ExperimentSummary,
    LoggingListener,
)


class TestExperimentConfig:
    """Test ExperimentConfig data model."""

    def test_experiment_config_creation(self):
        """Test basic ExperimentConfig creation."""
        config = ExperimentConfig(
            name="Test Experiment",
            description="A test experiment",
            tags=["test", "evaluation"],
            repetitions=3,
            preview_examples=5,
            preview_seed=123,
            max_workers=4,
        )

        assert config.name == "Test Experiment"
        assert config.description == "A test experiment"
        assert "test" in config.tags
        assert config.repetitions == 3
        assert config.preview_examples == 5
        assert config.preview_seed == 123
        assert config.max_workers == 4
        assert config.dataset_id is None
        assert config.dataset_version_id is None
        assert config.project_name is None

    def test_experiment_config_defaults(self):
        """Test ExperimentConfig with minimal required fields."""
        config = ExperimentConfig(name="Minimal")

        assert config.name == "Minimal"
        assert config.description == ""
        assert config.tags == []
        assert config.repetitions == 1
        assert config.preview_examples is None
        assert config.preview_seed == 42
        assert config.max_workers == 1
        assert config.dataset_id is None
        assert config.dataset_version_id is None
        assert config.project_name is None


class TestExperimentResult:
    """Test ExperimentResult data model."""

    def test_experiment_result_creation(self):
        """Test basic ExperimentResult creation."""
        now = datetime.now(UTC)
        result = ExperimentResult(
            example_id="test_123",
            run_id="test_123#1",
            repetition_number=1,
            started_at=now,
            completed_at=now,
            input_data={"input": {"query": "test"}, "output": {"response": "expected"}},
            output={"response": "expected"},
            actual_output="Generated response",
            evaluation_scores={"accuracy": 0.8, "relevance": 0.9},
            evaluator_metadata={"accuracy": {"reason": "Good match"}},
            metadata={"execution_time_ms": 150.0},
            trace_id="abc123",
        )

        assert result.example_id == "test_123"
        assert result.actual_output == "Generated response"
        assert result.evaluation_scores["accuracy"] == 0.8
        assert result.evaluation_scores["relevance"] == 0.9
        assert result.evaluator_metadata["accuracy"]["reason"] == "Good match"
        assert result.error is None
        assert result.started_at == now
        assert result.completed_at == now
        assert result.trace_id == "abc123"


class MockListener:
    """Mock listener for testing."""

    def __init__(self):
        self.events = []

    def on_experiment_started(self, experiment_id, config, examples):
        self.events.append(("started", experiment_id, len(examples)))

    def on_task_completed(self, experiment_id, result):
        self.events.append(("task_completed", experiment_id, result.example_id, bool(result.error)))

    def on_task_evaluated(self, experiment_id, result):
        self.events.append(("task_evaluated", experiment_id, result.example_id, bool(result.error)))

    def on_experiment_completed(self, experiment_id, results, summary):
        self.events.append(("completed", experiment_id, len(results), summary.successful_examples))

    def on_experiment_failed(self, experiment_id, error):
        self.events.append(("failed", experiment_id, error))


class MockAsyncListener:
    """Mock async listener for testing."""

    def __init__(self):
        self.events = []

    async def on_experiment_started(self, experiment_id, config, examples):
        self.events.append(("started", experiment_id, len(examples)))

    async def on_task_completed(self, experiment_id, result):
        self.events.append(("task_completed", experiment_id, result.example_id, bool(result.error)))

    async def on_task_evaluated(self, experiment_id, result):
        self.events.append(("task_evaluated", experiment_id, result.example_id, bool(result.error)))

    async def on_experiment_completed(self, experiment_id, results, summary):
        self.events.append(("completed", experiment_id, len(results), summary.successful_examples))

    async def on_experiment_failed(self, experiment_id, error):
        self.events.append(("failed", experiment_id, error))


class TestExperimentRunner:
    """Test synchronous experiment runner."""

    def test_runner_initialization(self):
        """Test ExperimentRunner initialization."""
        runner = ExperimentRunner()
        assert runner.listeners == []

    def test_prepare_dataset_from_list(self):
        """Test dataset preparation from list of examples."""
        runner = ExperimentRunner()

        examples = [
            DatasetExample(input={"query": "first"}, output={"response": "First response"}),
            DatasetExample(input={"query": "second"}, output={"response": "Second response"}),
        ]

        prepared, runs = runner._prepare_dataset(examples)
        assert len(prepared) == 2
        assert len(runs) == 2
        assert prepared[0].input["query"] == "first"
        assert prepared[1].input["query"] == "second"
        assert runs[0].example is prepared[0]
        assert runs[0].repetition_number == 1
        assert runs[1].run_id.endswith("#1")

    def test_prepare_dataset_from_dict(self):
        """Test dataset preparation from dictionary."""
        runner = ExperimentRunner()

        dataset_dict = {
            "examples": [
                {
                    "id": "ex1",
                    "input": {"query": "first"},
                    "output": {"response": "First response"},
                    "metadata": {"category": "test"},
                },
                {"input": {"query": "second"}, "output": {"response": "Second response"}},
            ]
        }

        prepared, runs = runner._prepare_dataset(dataset_dict)
        assert len(prepared) == 2
        assert len(runs) == 2
        assert prepared[0].id == "ex1"
        assert prepared[0].metadata["category"] == "test"
        assert prepared[1].id is not None  # Auto-generated

    def test_preview_examples_selection(self):
        """Test deterministic preview selection."""
        runner = ExperimentRunner()
        examples = [DatasetExample(input={"i": i}, output={"o": i}) for i in range(10)]

        preview_a, runs_a = runner._prepare_dataset(
            examples, preview_examples=3, preview_seed=42, repetitions=1
        )
        preview_b, runs_b = runner._prepare_dataset(
            examples, preview_examples=3, preview_seed=42, repetitions=1
        )
        preview_c, _ = runner._prepare_dataset(
            examples, preview_examples=3, preview_seed=99, repetitions=1
        )

        assert [ex.input["i"] for ex in preview_a] == [ex.input["i"] for ex in preview_b]
        assert len(runs_a) == len(preview_a) == 3
        assert [ex.input["i"] for ex in preview_a] != [ex.input["i"] for ex in preview_c]

    def test_run_selection_filters_examples_and_repetitions(self):
        """Ensure run_selection executes only the requested pairs."""
        runner = ExperimentRunner()
        examples = [
            DatasetExample(input={"question": "A"}, output={"answer": "a"}, metadata={}, id="ex_a"),
            DatasetExample(input={"question": "B"}, output={"answer": "b"}, metadata={}, id="ex_b"),
        ]

        captured_runs: list[tuple[str, int]] = []

        class CaptureListener:
            def on_task_completed(self, experiment_id, result):
                captured_runs.append((result.example_id, result.repetition_number))

        runner.listeners.append(CaptureListener())

        config = ExperimentConfig(name="selection-test", repetitions=3)

        def task_fn(example: DatasetExample) -> dict[str, Any]:
            return {"answer": example.output.get("answer")}

        runner.run(
            dataset=examples,
            task=task_fn,
            evaluators=[],
            config=config,
            run_selection={"ex_a": {2}, "ex_b": [1, 3]},
        )

        assert captured_runs == [("ex_a", 2), ("ex_b", 1), ("ex_b", 3)]

    def test_run_selection_unknown_example(self):
        """run_selection should raise when IDs are missing."""
        runner = ExperimentRunner()
        examples = [
            DatasetExample(
                input={"question": "Only"}, output={"answer": "one"}, metadata={}, id="ex_only"
            )
        ]

        config = ExperimentConfig(name="missing-id", repetitions=1)

        def task_fn(example: DatasetExample) -> dict[str, Any]:
            return {"answer": example.output.get("answer")}

        with pytest.raises(ValueError, match="unknown example IDs"):
            runner.run(
                dataset=examples,
                task=task_fn,
                evaluators=[],
                config=config,
                run_selection={"missing": {1}},
            )

    def test_run_selection_invalid_repetition(self):
        """run_selection should validate repetition numbers."""
        runner = ExperimentRunner()
        examples = [
            DatasetExample(
                input={"question": "Only"}, output={"answer": "one"}, metadata={}, id="ex_only"
            )
        ]

        config = ExperimentConfig(name="bad-repetition", repetitions=2)

        def task_fn(example: DatasetExample) -> dict[str, Any]:
            return {"answer": example.output.get("answer")}

        with pytest.raises(ValueError, match="outside the configured range"):
            runner.run(
                dataset=examples,
                task=task_fn,
                evaluators=[],
                config=config,
                run_selection={"ex_only": {0}},
            )

    def test_repetition_expansion(self):
        """Test expansion into multiple repetitions."""
        runner = ExperimentRunner()
        examples = [DatasetExample(input={"i": i}, output={"o": i}) for i in range(2)]

        prepared, runs = runner._prepare_dataset(examples, repetitions=3)

        assert len(prepared) == 2
        assert len(runs) == 6  # 2 examples * 3 repetitions
        assert [run.repetition_number for run in runs] == [1, 2, 3, 1, 2, 3]
        assert runs[0].example is prepared[0]
        assert runs[3].example is prepared[1]

    def test_basic_experiment_run(self):
        """Test basic experiment execution."""
        runner = ExperimentRunner()
        listener = MockListener()
        runner.add_listener(listener)

        def test_function(example):
            query = example.input.get("query", "")
            return f"Response to: {query}"

        def simple_evaluator(context):
            # Simple evaluator that gives score based on output length
            score = len(context.actual_output) / 100.0
            return EvaluationMetric(name="length_score", score=min(score, 1.0))

        examples = [
            DatasetExample(
                input={"messages": [{"role": "user", "content": "Hello"}]},
                output={"messages": [{"role": "assistant", "content": "Hi there!"}]},
            )
        ]

        config = ExperimentConfig(name="Basic Test", description="A basic test experiment")

        summary = runner.run(
            dataset=examples,
            task=test_function,
            evaluators=[simple_evaluator],
            config=config,
        )

        # Check summary
        assert isinstance(summary, ExperimentSummary)
        assert summary.total_examples == 1
        assert summary.successful_examples == 1
        assert summary.failed_examples == 0
        assert "length_score" in summary.average_scores
        assert summary.config.name == "Basic Test"

        # Check listener events
        assert len(listener.events) == 4  # started, task_completed, task_evaluated, completed
        assert listener.events[0][0] == "started"
        assert listener.events[1][0] == "task_completed"
        assert listener.events[2][0] == "task_evaluated"
        assert listener.events[3][0] == "completed"

    def test_experiment_with_errors(self):
        """Test experiment handling when task function fails."""
        runner = ExperimentRunner()
        listener = MockListener()
        runner.add_listener(listener)

        def failing_test_function(example):
            if "fail" in str(example.input):
                raise ValueError("Intentional test failure")
            return "Success"

        examples = [
            DatasetExample(input={"query": "success"}, output={"response": "Success"}),
            DatasetExample(input={"query": "fail please"}, output={"response": "Success"}),
        ]

        config = ExperimentConfig(name="Error Test")

        summary = runner.run(dataset=examples, task=failing_test_function, config=config)

        # Check that failure was handled properly
        assert summary.total_examples == 2
        assert summary.successful_examples == 1
        assert summary.failed_examples == 1

        # Check that we got events for both examples
        example_events = [e for e in listener.events if e[0] == "task_completed"]
        assert len(example_events) == 2
        assert example_events[0][3] is False  # No error for first
        assert example_events[1][3] is True  # Error for second

    def test_listener_management(self):
        """Test adding and removing listeners."""
        runner = ExperimentRunner()
        listener1 = MockListener()
        listener2 = MockListener()

        # Add listeners
        runner.add_listener(listener1)
        runner.add_listener(listener2)
        assert len(runner.listeners) == 2

        # Remove listener
        runner.remove_listener(listener1)
        assert len(runner.listeners) == 1
        assert listener2 in runner.listeners

    def test_async_function_rejection(self):
        """Test that async functions are rejected by sync runner."""
        runner = ExperimentRunner()

        async def async_test_function(example):
            return "async result"

        examples = [DatasetExample(input={"test": True}, output={"result": "expected"})]

        with pytest.raises(TypeError, match="Async task provided to synchronous runner"):
            runner.run(examples, async_test_function)  # type: ignore[arg-type]

    def test_max_workers_enables_parallel_runs(self):
        """Ensure max_workers>1 executes runs concurrently using a barrier."""
        runner = ExperimentRunner()
        barrier = threading.Barrier(2)

        examples = [
            DatasetExample(input={"query": "first"}, output={"response": "First"}),
            DatasetExample(input={"query": "second"}, output={"response": "Second"}),
        ]

        def blocking_test(example: DatasetExample):
            barrier.wait(timeout=5)
            return example.output

        config = ExperimentConfig(name="Parallel", max_workers=2)
        summary = runner.run(
            dataset=examples,
            task=blocking_test,
            evaluators=[],
            config=config,
        )

        assert summary.total_examples == 2
        assert summary.successful_examples == 2


class TestAsyncExperimentRunner:
    """Test asynchronous experiment runner."""

    @pytest.mark.asyncio
    async def test_async_runner_initialization(self):
        """Test AsyncExperimentRunner initialization."""
        runner = AsyncExperimentRunner()
        assert runner.listeners == []

    @pytest.mark.asyncio
    async def test_async_experiment_with_sync_function(self):
        """Test async runner rejects synchronous task function and evaluator."""
        runner = AsyncExperimentRunner()
        listener = MockAsyncListener()
        runner.add_listener(listener)

        def sync_test_function(example):
            return f"Sync response to: {example.input.get('query', '')}"

        def sync_evaluator(context):
            return 0.8

        examples = [DatasetExample(input={"query": "test"}, output={"response": "expected"})]

        config = ExperimentConfig(name="Async Test")

        with pytest.raises(
            TypeError, match="AsyncExperimentRunner requires an async task function."
        ):
            await runner.run(
                dataset=examples,
                task=sync_test_function,  # type: ignore[arg-type]
                evaluators=[sync_evaluator],  # type: ignore[list-item]
                config=config,
            )

    @pytest.mark.asyncio
    async def test_async_experiment_with_async_function(self):
        """Test async runner with asynchronous task function."""
        runner = AsyncExperimentRunner()
        listener = MockAsyncListener()
        runner.add_listener(listener)

        async def async_test_function(example):
            await asyncio.sleep(0.01)  # Simulate async work
            return f"Async response to: {example.input.get('query', '')}"

        async def async_evaluator(context):
            await asyncio.sleep(0.01)  # Simulate async evaluation
            return 0.9

        examples = [DatasetExample(input={"query": "async test"}, output={"response": "expected"})]

        config = ExperimentConfig(name="Full Async Test")

        summary = await runner.run(
            dataset=examples,
            task=async_test_function,
            evaluators=[async_evaluator],
            config=config,
        )

        assert summary.total_examples == 1
        assert summary.successful_examples == 1
        assert len(listener.events) == 4
        assert listener.events[0][0] == "started"
        task_events = [e for e in listener.events if e[0] == "task_completed"]
        evaluated_events = [e for e in listener.events if e[0] == "task_evaluated"]
        assert len(task_events) == 1
        assert len(evaluated_events) == 1
        assert listener.events[-1][0] == "completed"

    @pytest.mark.asyncio
    async def test_async_max_workers_enables_parallel_runs(self):
        """Ensure async max_workers allows concurrent execution via an event barrier."""
        runner = AsyncExperimentRunner()
        examples = [
            DatasetExample(input={"query": "one"}, output={"response": "One"}),
            DatasetExample(input={"query": "two"}, output={"response": "Two"}),
        ]

        ready_event = asyncio.Event()
        lock = asyncio.Lock()
        started = {"count": 0}

        async def blocking_test(example: DatasetExample):
            async with lock:
                started["count"] += 1
                if started["count"] == 2:
                    ready_event.set()

            await asyncio.wait_for(ready_event.wait(), timeout=2)
            return example.output

        config = ExperimentConfig(name="AsyncParallel", max_workers=2)
        summary = await runner.run(
            dataset=examples,
            task=blocking_test,
            evaluators=[],
            config=config,
        )

        assert summary.total_examples == 2
        assert summary.successful_examples == 2


class TestBuiltinListeners:
    """Test built-in logging listeners."""

    def test_logging_listener_creation(self):
        """Test LoggingListener creation and basic functionality."""
        listener = LoggingListener(verbose=True)
        assert listener.verbose is True

        # Test that methods exist and don't crash
        config = ExperimentConfig(name="Test")
        examples = [DatasetExample(input={"test": True}, output={"result": "test"})]

        # These should not raise exceptions
        listener.on_experiment_started("exp123", config, examples)
        listener.on_experiment_failed("exp123", "Test error")

    @pytest.mark.asyncio
    async def test_async_logging_listener_creation(self):
        """Test AsyncLoggingListener creation and basic functionality."""
        listener = AsyncLoggingListener(verbose=True)
        assert listener.verbose is True

        # Test that methods exist and don't crash
        config = ExperimentConfig(name="Async Test")
        examples = [DatasetExample(input={"test": True}, output={"result": "test"})]

        # These should not raise exceptions
        await listener.on_experiment_started("exp123", config, examples)
        await listener.on_experiment_failed("exp123", "Test error")
