"""OTEL-backed run observer that registers itself when imported."""

from __future__ import annotations

from contextlib import ExitStack, contextmanager
from typing import Any, ContextManager

from ..observers import RunObservation, RunObserver, register_observer
from . import (
    capture_agent_trace,
    consume_collected_tool_calls,
    consume_run_trace_id,
    tool_call_collection_scope,
)


class OTELRunObserver(RunObserver):
    """Observer implementation that reuses the tracing helper APIs."""

    def enter_run(
        self,
        *,
        run_id: str,
        example_id: str,
        repetition: int,
    ) -> ContextManager[Any]:
        stack = ExitStack()
        stack.enter_context(tool_call_collection_scope(run_id))
        stack.enter_context(capture_agent_trace(run_id=run_id))

        @contextmanager
        def _manager():
            with stack:
                yield None

        return _manager()

    def collect_observation(self, run_id: str) -> RunObservation:
        tool_calls = consume_collected_tool_calls(run_id) or None
        trace_id = consume_run_trace_id(run_id)
        metadata = {
            "tracing": {
                "tool_calls": tool_calls,
                "trace_id": trace_id,
            }
        }
        return RunObservation(metadata=metadata)

    def shutdown(self) -> None:
        return None


register_observer(OTELRunObserver())


__all__ = ["OTELRunObserver"]
