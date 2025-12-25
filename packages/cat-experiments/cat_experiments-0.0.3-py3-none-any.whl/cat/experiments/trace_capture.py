"""Compatibility wrapper for cat.experiments.tracing.

This module preserves the previous import path for tracing helpers while routing
all logic through :mod:`cat.experiments.tracing`, which isolates optional
OpenTelemetry dependencies behind the ``tracing`` extra.
"""

from .tracing import (
    ExperimentTraceCapture,
    ToolCallCollectorProcessor,
    capture_agent_trace,
    capture_experiment_trace,
    consume_collected_tool_calls,
    consume_run_trace_id,
    convert_otlp_spans_to_agent_trace,
    tool_call_collection_scope,
)

__all__ = [
    "ExperimentTraceCapture",
    "ToolCallCollectorProcessor",
    "capture_agent_trace",
    "capture_experiment_trace",
    "consume_collected_tool_calls",
    "consume_run_trace_id",
    "convert_otlp_spans_to_agent_trace",
    "tool_call_collection_scope",
]
