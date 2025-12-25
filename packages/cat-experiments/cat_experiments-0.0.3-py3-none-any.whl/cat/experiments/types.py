"""Shared type aliases and protocols for cat-experiments."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from .models import (
    AggregateEvaluationContext,
    DatasetExample,
    EvaluationContext,
    EvaluatorResult,
    TestFunctionOutput,  # re-exported from models for convenience
)

# Common callable signatures
EvaluatorFn = Callable[[EvaluationContext], EvaluatorResult]
AsyncEvaluatorFn = Callable[[EvaluationContext], Awaitable[EvaluatorResult]]
AggregateEvaluatorResult = (
    EvaluatorResult
    | Mapping[str, EvaluatorResult | dict[str, Any]]
    | list[EvaluatorResult | dict[str, Any]]
)
AggregateEvaluatorFn = Callable[[AggregateEvaluationContext], AggregateEvaluatorResult]
AsyncAggregateEvaluatorFn = Callable[
    [AggregateEvaluationContext], Awaitable[AggregateEvaluatorResult]
]
TestFn = Callable[[DatasetExample], TestFunctionOutput]
AsyncTestFn = Callable[[DatasetExample], Awaitable[TestFunctionOutput]]


__all__ = [
    "EvaluatorFn",
    "AsyncEvaluatorFn",
    "AggregateEvaluatorFn",
    "AsyncAggregateEvaluatorFn",
    "AggregateEvaluatorResult",
    "TestFn",
    "AsyncTestFn",
    "TestFunctionOutput",
]
