"""OpenTelemetry helpers for cat-experiments tracing."""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from contextvars import ContextVar
from threading import Lock
from typing import Any, Dict, Iterator, List, Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.trace import StatusCode

from ..models import AgentStep, AgentTrace, LLMCall, ToolCall

logger = logging.getLogger(__name__)


CURRENT_RUN_ID: ContextVar[Optional[str]] = ContextVar(
    "cat_experiments_current_trace_run", default=None
)
_TOOL_CALLS: Dict[str, List[ToolCall]] = {}
_TOOL_CALL_LOCK = Lock()
_RUN_TRACE_IDS: Dict[str, str] = {}
_RUN_TRACE_ID_LOCK = Lock()


def _parse_headers(header_str: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for pair in header_str.split(","):
        if not pair.strip():
            continue
        if "=" not in pair:
            continue
        key, value = pair.split("=", 1)
        headers[key.strip()] = value.strip()
    return headers


def _resolve_otlp_exporter_config() -> tuple[Optional[str], dict[str, str]]:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    headers: dict[str, str] = {}

    if env_headers := os.getenv("OTEL_EXPORTER_OTLP_HEADERS"):
        headers.update(_parse_headers(env_headers))

    return endpoint, headers


@contextmanager
def tool_call_collection_scope(run_id: str) -> Iterator[None]:
    """Scope that marks the active run for tool-call collection."""

    token = CURRENT_RUN_ID.set(run_id)
    try:
        yield
    finally:
        CURRENT_RUN_ID.reset(token)


def consume_collected_tool_calls(run_id: str) -> list[ToolCall]:
    """Return and clear collected tool calls for a run."""

    with _TOOL_CALL_LOCK:
        return _TOOL_CALLS.pop(run_id, [])


def consume_run_trace_id(run_id: str) -> Optional[str]:
    """Return and clear the recorded trace ID for a run."""

    with _RUN_TRACE_ID_LOCK:
        return _RUN_TRACE_IDS.pop(run_id, None)


def _record_run_trace_id(run_id: str, span: ReadableSpan) -> None:
    span_context = span.get_span_context()
    if not span_context:
        return

    trace_hex = f"{span_context.trace_id:032x}"
    with _RUN_TRACE_ID_LOCK:
        _RUN_TRACE_IDS.setdefault(run_id, trace_hex)


class ToolCallCollectorProcessor(SpanProcessor):
    """Span processor that records tool call metadata per experiment run."""

    def on_start(self, span: ReadableSpan, parent_context=None) -> None:  # pragma: no cover - no-op
        return

    def on_end(self, span: ReadableSpan) -> None:
        run_id = CURRENT_RUN_ID.get()
        if not run_id:
            return

        _record_run_trace_id(run_id, span)

        attributes = dict(span.attributes or {})
        if not _is_tool_span(span, attributes):
            return

        tool_call = _extract_tool_call(span, attributes)
        if not tool_call:
            return

        with _TOOL_CALL_LOCK:
            _TOOL_CALLS.setdefault(run_id, []).append(tool_call)

    def shutdown(self) -> None:  # pragma: no cover - no-op
        return

    def force_flush(self, timeout_millis: int = 30000) -> bool:  # pragma: no cover - no-op
        return True


def convert_otlp_spans_to_agent_trace(spans: List[ReadableSpan]) -> AgentTrace:
    """Convert OTLP spans to AgentTrace format.

    This function analyzes captured OpenTelemetry spans (typically from OpenInference
    instrumentation) and converts them to our rich AgentTrace format.

    Args:
        spans: List of OpenTelemetry ReadableSpan objects

    Returns:
        AgentTrace object with extracted steps, LLM calls, and tool usage
    """
    if not spans:
        return AgentTrace(final_response="")

    # Sort spans by start time to understand execution order
    sorted_spans = sorted(spans, key=lambda s: s.start_time or 0)

    trace = AgentTrace(final_response="")
    trace.agent_type = "instrumented"

    # Track execution timing
    start_time = sorted_spans[0].start_time or 0
    end_time = max((span.end_time or span.start_time or 0) for span in spans)
    trace.execution_time_ms = (end_time - start_time) / 1_000_000  # Convert from nanoseconds

    for span in sorted_spans:
        attributes = dict(span.attributes) if span.attributes else {}

        # Extract LLM calls (OpenInference LLM spans)
        if _is_llm_span(span, attributes):
            llm_call = _extract_llm_call(span, attributes)
            if llm_call:
                trace.llm_calls.append(llm_call)

                # Add as a reasoning step
                step = AgentStep(
                    action="llm_call",
                    input=llm_call.prompt[:100] + "..."
                    if len(llm_call.prompt) > 100
                    else llm_call.prompt,
                    output=llm_call.response[:100] + "..."
                    if len(llm_call.response) > 100
                    else llm_call.response,
                    step_type="thought",
                    execution_time_ms=llm_call.latency_ms,
                )
                trace.steps.append(step)

        # Extract tool calls (OpenInference tool spans)
        elif _is_tool_span(span, attributes):
            tool_call = _extract_tool_call(span, attributes)
            if tool_call:
                trace.tools_called.append(tool_call)

                # Add as an action step
                step = AgentStep(
                    action="tool_call",
                    input=f"{tool_call.name}({tool_call.args})",
                    output=str(tool_call.result)[:100] + "..."
                    if len(str(tool_call.result)) > 100
                    else str(tool_call.result),
                    step_type="action",
                    execution_time_ms=tool_call.execution_time_ms,
                )
                trace.steps.append(step)

        # Extract other spans as generic steps
        else:
            step = _extract_generic_step(span, attributes)
            if step:
                trace.steps.append(step)

    # Calculate aggregate metrics
    trace.total_tokens = sum(call.tokens_used for call in trace.llm_calls if call.tokens_used)
    trace.total_cost = sum(call.token_cost for call in trace.llm_calls if call.token_cost)

    # Extract final response from the last LLM call or span output
    if trace.llm_calls:
        trace.final_response = trace.llm_calls[-1].response  # type: ignore[assignment]
    elif spans:
        # Try to get final response from span attributes
        final_span = sorted_spans[-1]
        attributes = dict(final_span.attributes) if final_span.attributes else {}
        trace.final_response = attributes.get(  # type: ignore[assignment]
            "output.value", attributes.get("response", "")
        )

    return trace


def _is_llm_span(span: ReadableSpan, attributes: Dict[str, Any]) -> bool:
    """Check if span represents an LLM call."""
    # OpenInference LLM span indicators
    return (
        "llm" in span.name.lower()
        or "openai" in span.name.lower()
        or any(key.startswith("llm.") for key in attributes.keys())
        or "gen_ai.system" in attributes
        or "gen_ai.operation.name" in attributes
    )


def _is_tool_span(span: ReadableSpan, attributes: Dict[str, Any]) -> bool:
    """Check if span represents a tool/function call."""
    return (
        "function" in span.name.lower()
        or "tool" in span.name.lower()
        or any(key.startswith("tool.") for key in attributes.keys())
        or "function_call" in attributes
    )


def _extract_llm_call(span: ReadableSpan, attributes: Dict[str, Any]) -> Optional[LLMCall]:
    """Extract LLM call information from span."""
    try:
        # Get basic info
        prompt = attributes.get("llm.prompts", attributes.get("input.value", ""))
        response = attributes.get("llm.responses", attributes.get("output.value", ""))
        model = attributes.get("llm.model_name", attributes.get("gen_ai.request.model", ""))

        # Calculate execution time
        duration_ns = (span.end_time or 0) - (span.start_time or 0)
        latency_ms = duration_ns / 1_000_000

        # Extract token usage
        tokens_used = None
        token_cost = None

        if "llm.token.counts.input" in attributes and "llm.token.counts.output" in attributes:
            input_tokens = attributes.get("llm.token.counts.input", 0)
            output_tokens = attributes.get("llm.token.counts.output", 0)
            tokens_used = input_tokens + output_tokens
        elif (
            "gen_ai.usage.input_tokens" in attributes and "gen_ai.usage.output_tokens" in attributes
        ):
            input_tokens = attributes.get("gen_ai.usage.input_tokens", 0)
            output_tokens = attributes.get("gen_ai.usage.output_tokens", 0)
            tokens_used = input_tokens + output_tokens

        return LLMCall(
            prompt=str(prompt),
            response=str(response),
            model=model,
            tokens_used=tokens_used,
            token_cost=token_cost,
            latency_ms=latency_ms,
            timestamp=str(span.start_time),
            step_context="auto_extracted",
        )
    except Exception:
        return None


def _extract_tool_call(span: ReadableSpan, attributes: Dict[str, Any]) -> Optional[ToolCall]:
    """Extract tool call information from span."""
    try:
        name = span.name
        args = {}
        result = attributes.get("output.value", attributes.get("result", ""))

        # Try to extract arguments from attributes
        for key, value in attributes.items():
            if key.startswith("input.") and key != "input.value":
                arg_name = key.replace("input.", "")
                args[arg_name] = value

        # Calculate execution time
        duration_ns = (span.end_time or 0) - (span.start_time or 0)
        execution_time_ms = duration_ns / 1_000_000

        # Check for errors
        error = None
        if span.status.status_code == StatusCode.ERROR:
            error = span.status.description

        return ToolCall(
            name=name, args=args, result=result, error=error, execution_time_ms=execution_time_ms
        )
    except Exception:
        return None


def _extract_generic_step(span: ReadableSpan, attributes: Dict[str, Any]) -> Optional[AgentStep]:
    """Extract generic step information from span."""
    try:
        action = span.name
        input_data = attributes.get("input.value", "")
        output_data = attributes.get("output.value", "")

        # Calculate execution time
        duration_ns = (span.end_time or 0) - (span.start_time or 0)
        execution_time_ms = duration_ns / 1_000_000

        # Determine step type based on span characteristics
        step_type = "action"
        if "thought" in span.name.lower() or "reasoning" in span.name.lower():
            step_type = "thought"
        elif "observe" in span.name.lower() or "result" in span.name.lower():
            step_type = "observation"

        return AgentStep(
            action=action,
            input=str(input_data),
            output=str(output_data),
            step_type=step_type,
            execution_time_ms=execution_time_ms,
            timestamp=str(span.start_time),
        )
    except Exception:
        return None


class ExperimentTraceCapture:
    """Context manager for capturing OpenTelemetry traces during experiment execution.

    This class creates an isolated tracer provider in context without affecting
    global OpenTelemetry configuration. Clients are responsible for enabling any
    OpenInference or OpenTelemetry instrumentation they require before entering
    the context.
    """

    def __init__(self, service_name: str = "cat-experiments-experiment", verbose: bool = False):
        """Initialize the trace capture context.

        Args:
            service_name: Service name for the tracer provider resource
            verbose: Whether to log detailed trace-capture information
        """
        self.service_name = service_name
        self.verbose = verbose

        self.test_provider: Optional[TracerProvider] = None
        self._original_provider = None
        self._provider_set = False

    def __enter__(self) -> "ExperimentTraceCapture":
        """Enter the trace capture context."""

        # Create isolated tracer provider
        resource_attrs = {SERVICE_NAME: self.service_name}
        resource = Resource(resource_attrs)
        self.test_provider = TracerProvider(resource=resource)
        assert self.test_provider is not None  # Narrow for type checkers

        endpoint, headers = _resolve_otlp_exporter_config()
        if endpoint:
            try:
                self.test_provider.add_span_processor(
                    SimpleSpanProcessor(OTLPSpanExporter(endpoint=endpoint, headers=headers))
                )
            except Exception as exc:  # pragma: no cover
                logger.warning("Failed to configure OTLP exporter: %s", exc)

        self.test_provider.add_span_processor(ToolCallCollectorProcessor())

        # Set our tracer provider as the global one temporarily
        current_provider = trace.get_tracer_provider()
        self._original_provider = current_provider

        # If there's no concrete provider set yet, we can set ours
        if (
            hasattr(current_provider, "__class__")
            and "Proxy" in current_provider.__class__.__name__
        ):
            trace.set_tracer_provider(self.test_provider)
            self._provider_set = True
        else:
            # Provider already set, we'll work with direct tracer access
            self._provider_set = False
            if self.verbose:
                logger.warning("TracerProvider already set, using direct tracer access")

        if self.verbose:
            logger.info(f"Trace capture context activated with service '{self.service_name}'")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the trace capture context and cleanup resources."""
        # Restore original tracer provider if we set one
        if self._provider_set:
            try:
                if self._original_provider:
                    trace.set_tracer_provider(self._original_provider)
            except Exception as e:
                if self.verbose:
                    logger.warning(f"Could not restore original tracer provider: {e}")

        # Shutdown tracer provider to clean up resources
        if self.test_provider is not None:
            self.test_provider.shutdown()
            self.test_provider = None

        if self.verbose:
            logger.info("Trace capture context exited")

    def start_test_span(
        self,
        example_id: str,
        experiment_id: str,
        test_function_name: Optional[str] = None,
        additional_attributes: Optional[Dict[str, Any]] = None,
    ):
        """Start the root span for test execution.

        Args:
            example_id: ID of the example being tested
            experiment_id: ID of the experiment run
            test_function_name: Name of the test function being executed
            additional_attributes: Additional attributes to add to the span

        Returns:
            Span context manager
        """
        # Get tracer - either from global provider (if we set it) or directly from our provider
        if self._provider_set:
            tracer = trace.get_tracer("cat-experiments-experiment-runner")
        else:
            # Fall back to direct tracer from our provider
            if self.test_provider:
                tracer = self.test_provider.get_tracer("cat-experiments-experiment-runner")
            else:
                tracer = trace.get_tracer("cat-experiments-experiment-runner")

        # Build span attributes
        attributes = {
            "experiment.id": experiment_id,
            "example.id": example_id,
            "cat.experiments.component": "experiment_runner",
            "cat.experiments.version": "0.1.0",
        }

        if test_function_name:
            attributes["test.function_name"] = test_function_name

        # Add additional attributes
        if additional_attributes:
            attributes.update(additional_attributes)

        return tracer.start_as_current_span("test_execution", attributes=attributes)


@contextmanager
def capture_agent_trace(
    run_id: Optional[str] = None,
    service_name: str = "cat-experiments-agent",
    verbose: bool = False,
) -> Iterator[ExperimentTraceCapture]:
    """Capture traces for an ad-hoc agent/test run using ExperimentTraceCapture."""
    attributes: Dict[str, Any] = {"cat.experiments.component": "agent_runner"}
    if run_id:
        attributes["cat.experiments.run_id"] = run_id

    with ExperimentTraceCapture(service_name=service_name, verbose=verbose) as capture:
        with capture.start_test_span(
            example_id=run_id or "cat-experiments-agent-example",
            experiment_id="cat-experiments-agent",
            additional_attributes=attributes,
        ):
            yield capture


@contextmanager
def capture_experiment_trace(
    example_id: str,
    experiment_id: str,
    test_function_name: Optional[str] = None,
    verbose: bool = False,
) -> Iterator[tuple[Any, ExperimentTraceCapture]]:
    """Convenience context manager for capturing experiment traces.

    Args:
        example_id: ID of the example being tested
        experiment_id: ID of the experiment run
        test_function_name: Name of the test function
        verbose: Whether to enable verbose logging

    Yields:
        Tuple of (root_span, trace_capture) for the execution context
    """
    with ExperimentTraceCapture(verbose=verbose) as capture:
        with capture.start_test_span(example_id, experiment_id, test_function_name) as root_span:
            yield root_span, capture
