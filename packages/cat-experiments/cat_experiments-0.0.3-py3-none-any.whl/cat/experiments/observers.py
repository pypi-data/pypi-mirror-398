"""Generic run observer interface for optional instrumentation plugins."""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass, field
from typing import Any, ContextManager, Protocol

from .models import ToolCall

TRACING_OBSERVER_NAMESPACE = "tracing"
TRACING_TOOL_CALLS_KEY = "tool_calls"
TRACING_TRACE_ID_KEY = "trace_id"


@dataclass
class RunObservation:
    """Structured metadata emitted by a run observer."""

    metadata: dict[str, Any] = field(default_factory=dict)


class RunObserver(Protocol):
    """Contract for plugins that watch experiment runs."""

    def enter_run(
        self,
        *,
        run_id: str,
        example_id: str,
        repetition: int,
    ) -> ContextManager[Any]:
        """Return a context manager used to wrap the test function execution."""
        ...

    def collect_observation(self, run_id: str) -> RunObservation:
        """Harvest metadata captured for the given run."""
        ...

    def shutdown(self) -> None:
        """Clean up any resources held by the observer."""
        ...


class _NoOpObserver:
    """Fallback observer when no plugin is registered."""

    def enter_run(
        self,
        *,
        run_id: str,
        example_id: str,
        repetition: int,
    ) -> ContextManager[Any]:
        return nullcontext(None)

    def collect_observation(self, run_id: str) -> RunObservation:
        return RunObservation()

    def shutdown(self) -> None:
        return None


_ACTIVE_OBSERVER: RunObserver = _NoOpObserver()


def register_observer(observer: RunObserver | None) -> None:
    """Set the active observer (or reset to the default when None)."""

    global _ACTIVE_OBSERVER
    _ACTIVE_OBSERVER = observer if observer is not None else _NoOpObserver()


def reset_observer() -> None:
    """Reset the active observer to the default no-op implementation."""

    register_observer(None)


def get_observer() -> RunObserver:
    """Return the currently registered observer."""

    return _ACTIVE_OBSERVER


def observation_tool_calls(observation: RunObservation | None) -> list[ToolCall] | None:
    """Extract tool call metadata emitted by observers, if any."""

    if observation is None:
        return None

    metadata = observation.metadata
    if not metadata:
        return None

    # Prefer explicit tool_calls field if provided
    tool_calls = metadata.get(TRACING_TOOL_CALLS_KEY)
    if isinstance(tool_calls, list):
        return tool_calls  # type: ignore[return-value]

    # Fall back to tracing namespace to support the OTEL plugin
    tracing_data = metadata.get(TRACING_OBSERVER_NAMESPACE)
    if isinstance(tracing_data, dict):
        tool_calls = tracing_data.get(TRACING_TOOL_CALLS_KEY)
        if isinstance(tool_calls, list):
            return tool_calls  # type: ignore[return-value]

    return None


def observation_trace_id(observation: RunObservation | None) -> str | None:
    """Extract a trace identifier from observer metadata when available."""

    if observation is None:
        return None

    metadata = observation.metadata
    if not metadata:
        return None

    trace_id = metadata.get(TRACING_TRACE_ID_KEY)
    if isinstance(trace_id, str):
        return trace_id

    tracing_data = metadata.get(TRACING_OBSERVER_NAMESPACE)
    if isinstance(tracing_data, dict):
        trace_id = tracing_data.get(TRACING_TRACE_ID_KEY)
        if isinstance(trace_id, str):
            return trace_id

    return None


def observation_metadata(observation: RunObservation | None) -> dict[str, Any]:
    """Return a shallow copy of observer metadata for execution records."""

    if observation is None or not observation.metadata:
        return {}

    return dict(observation.metadata)


__all__ = [
    "RunObservation",
    "RunObserver",
    "get_observer",
    "register_observer",
    "reset_observer",
    "observation_tool_calls",
    "observation_trace_id",
    "observation_metadata",
    "TRACING_OBSERVER_NAMESPACE",
    "TRACING_TOOL_CALLS_KEY",
    "TRACING_TRACE_ID_KEY",
]
