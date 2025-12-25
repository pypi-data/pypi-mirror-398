"""Tests for the generic observer interface wiring."""

import importlib
import os
import sys
from contextlib import nullcontext

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cat.experiments import DatasetExample, TestCase, ToolCall, generate
from cat.experiments.observers import (
    RunObservation,
    RunObserver,
    get_observer,
    register_observer,
    reset_observer,
)


@pytest.fixture(autouse=True)
def reset_observer_fixture():
    reset_observer()
    yield
    reset_observer()


class DummyObserver(RunObserver):
    def __init__(self, tool_call: ToolCall, trace_id: str):
        self.tool_call = tool_call
        self.trace_id = trace_id

    def enter_run(self, *, run_id: str, example_id: str, repetition: int):
        return nullcontext(None)

    def collect_observation(self, run_id: str) -> RunObservation:
        return RunObservation(
            metadata={
                "tracing": {
                    "tool_calls": [self.tool_call],
                    "trace_id": self.trace_id,
                },
                "custom": {"run_id": run_id},
            }
        )

    def shutdown(self) -> None:
        return None


def _example() -> DatasetExample:
    return DatasetExample(input={"question": "hi"}, output={"answer": "hi"})


def _task(example: DatasetExample):
    return {"response": example.input["question"]}


def test_observer_populates_tool_calls_and_metadata():
    tool_call = ToolCall(name="search", args={"query": "hi"})
    observer = DummyObserver(tool_call=tool_call, trace_id="trace-123")
    register_observer(observer)

    contexts = generate([TestCase(example=_example())], _task)

    assert len(contexts) == 1
    context = contexts[0]
    assert context.actual_tool_calls is not None
    assert context.actual_tool_calls[0].name == "search"
    assert context.execution_metadata["trace_id"] == "trace-123"
    assert context.execution_metadata["observer_metadata"]["custom"]["run_id"] == context.run_id


def test_importing_tracing_registers_otel_observer():
    import cat.experiments.tracing as tracing_mod

    importlib.reload(tracing_mod)
    observer = get_observer()
    assert observer.__class__.__name__ == "OTELRunObserver"
