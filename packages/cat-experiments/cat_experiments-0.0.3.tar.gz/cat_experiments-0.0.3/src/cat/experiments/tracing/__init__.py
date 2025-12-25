"""Tracing helpers with optional OpenTelemetry dependencies."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator, Optional

if TYPE_CHECKING:  # pragma: no cover - typing only
    from . import _otel as _otel_module

try:  # pragma: no cover - exercised via tracing extra
    from . import _otel as _otel_module
except ImportError:  # pragma: no cover - fallback path when extras missing
    _otel_module = None  # type: ignore[assignment]

if _otel_module is not None:
    CURRENT_RUN_ID = _otel_module.CURRENT_RUN_ID
    ExperimentTraceCapture = _otel_module.ExperimentTraceCapture
    ToolCallCollectorProcessor = _otel_module.ToolCallCollectorProcessor
    capture_agent_trace = _otel_module.capture_agent_trace
    capture_experiment_trace = _otel_module.capture_experiment_trace
    consume_collected_tool_calls = _otel_module.consume_collected_tool_calls
    consume_run_trace_id = _otel_module.consume_run_trace_id
    convert_otlp_spans_to_agent_trace = _otel_module.convert_otlp_spans_to_agent_trace
    tool_call_collection_scope = _otel_module.tool_call_collection_scope
    OTEL_AVAILABLE = True
else:
    from contextvars import ContextVar

    from ..models import AgentTrace, ToolCall

    CURRENT_RUN_ID: ContextVar[Optional[str]] = ContextVar(
        "cat_experiments_current_trace_run", default=None
    )

    class _NoOpToolCallCollectorProcessor:
        """No-op span processor when OpenTelemetry is unavailable."""

        def on_start(self, *args, **kwargs) -> None:
            return

        def on_end(self, *args, **kwargs) -> None:
            return

        def shutdown(self) -> None:
            return

        def force_flush(self, timeout_millis: int = 30000) -> bool:  # pragma: no cover
            return True

    class _NoOpExperimentTraceCapture:
        """No-op trace capture when OpenTelemetry extras are not installed."""

        def __init__(self, service_name: str = "cat-experiments-experiment", verbose: bool = False):
            self.service_name = service_name
            self.verbose = verbose

        def __enter__(self) -> "_NoOpExperimentTraceCapture":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
            return None

        def convert_to_agent_trace(self) -> AgentTrace:
            return AgentTrace(final_response="")

        @contextmanager
        def start_test_span(
            self,
            example_id: str,
            experiment_id: str,
            test_function_name: Optional[str] = None,
            additional_attributes: Optional[dict[str, Any]] = None,
        ) -> Iterator[None]:
            yield None

    @contextmanager
    def _noop_tool_call_collection_scope(run_id: str) -> Iterator[None]:
        yield

    def _noop_consume_collected_tool_calls(run_id: str) -> list[ToolCall]:
        return []

    def _noop_consume_run_trace_id(run_id: str) -> Optional[str]:
        return None

    @contextmanager
    def _noop_capture_agent_trace(
        *,
        run_id: Optional[str] = None,
        service_name: str = "cat-experiments-agent",
        verbose: bool = False,
    ) -> Iterator[_NoOpExperimentTraceCapture]:
        yield _NoOpExperimentTraceCapture(service_name=service_name, verbose=verbose)

    @contextmanager
    def _noop_capture_experiment_trace(
        example_id: str,
        experiment_id: str,
        test_function_name: Optional[str] = None,
        verbose: bool = False,
    ) -> Iterator[tuple[None, _NoOpExperimentTraceCapture]]:
        yield (None, _NoOpExperimentTraceCapture(verbose=verbose))

    def _noop_convert_otlp_spans_to_agent_trace(spans: list[Any]) -> AgentTrace:
        return AgentTrace(final_response="")

    ExperimentTraceCapture = _NoOpExperimentTraceCapture
    ToolCallCollectorProcessor = _NoOpToolCallCollectorProcessor
    tool_call_collection_scope = _noop_tool_call_collection_scope
    consume_collected_tool_calls = _noop_consume_collected_tool_calls
    consume_run_trace_id = _noop_consume_run_trace_id
    capture_agent_trace = _noop_capture_agent_trace
    capture_experiment_trace = _noop_capture_experiment_trace
    convert_otlp_spans_to_agent_trace = _noop_convert_otlp_spans_to_agent_trace

    consume_collected_tool_calls.__module__ = __name__
    consume_run_trace_id.__module__ = __name__
    convert_otlp_spans_to_agent_trace.__module__ = __name__
    tool_call_collection_scope.__module__ = __name__
    capture_agent_trace.__module__ = __name__
    capture_experiment_trace.__module__ = __name__
    ExperimentTraceCapture.__module__ = __name__
    ToolCallCollectorProcessor.__module__ = __name__
    OTEL_AVAILABLE = False

__all__ = [
    "ExperimentTraceCapture",
    "ToolCallCollectorProcessor",
    "capture_agent_trace",
    "capture_experiment_trace",
    "consume_collected_tool_calls",
    "consume_run_trace_id",
    "convert_otlp_spans_to_agent_trace",
    "tool_call_collection_scope",
    "OTEL_AVAILABLE",
]

# Auto-register the OTEL run observer when tracing helpers are imported.
try:  # pragma: no cover - exercised indirectly in observer tests
    from . import otel_observer as _otel_observer_module
except Exception:  # pragma: no cover - optional extras not installed
    _otel_observer_module = None
