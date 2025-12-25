"""
Core data models for cat-experiments - flexible evaluation data structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import uuid4

if TYPE_CHECKING:  # pragma: no cover
    from .experiments import ExperimentConfig, ExperimentResult


@dataclass
class ToolCall:
    """Represents a single tool/function call by an agent."""

    name: str
    args: dict[str, Any] = field(default_factory=dict)
    result: Any | None = None
    error: str | None = None
    execution_time_ms: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str | None = None
    type: str = "function"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "args": self.args,
            "result": self.result,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
            "type": self.type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolCall:
        """Create from dictionary representation."""
        return cls(
            name=data["name"],
            args=data.get("args", {}),
            result=data.get("result"),
            error=data.get("error"),
            execution_time_ms=data.get("execution_time_ms"),
            metadata=data.get("metadata", {}),
            id=data.get("id"),
            type=data.get("type", "function"),
        )

    # Backward compatibility properties
    @property
    def arguments(self) -> dict[str, Any]:
        """Backward compatibility for arguments field."""
        return self.args

    @arguments.setter
    def arguments(self, value: dict[str, Any]) -> None:
        """Backward compatibility for arguments field."""
        self.args = value


@dataclass
class DatasetExample:
    """Dataset example structure aligned with external evaluation tooling expectations."""

    input: dict[str, Any]
    """Arbitrary structured input payload (e.g. {"messages": [...]})."""

    output: dict[str, Any]
    """Reference/expected output payload (e.g. {"messages": [...]})."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional context such as tags, expected tool calls, or trace provenance."""

    id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.id is None:
            self.id = str(uuid4())
        self.created_at = self._ensure_datetime(self.created_at) or datetime.now(timezone.utc)
        self.updated_at = self._ensure_datetime(self.updated_at) or self.created_at

    @property
    def tags(self) -> list[str]:
        """Tags are persisted within metadata."""
        return list(self.metadata.get("tags", []))

    @tags.setter
    def tags(self, value: list[str]) -> None:
        self.metadata["tags"] = list(value)

    @property
    def expected_tool_calls(self) -> list[ToolCall] | None:
        raw = self.metadata.get("expected_tool_calls")
        if not raw:
            return None
        calls: list[ToolCall] = []
        for entry in raw:
            if isinstance(entry, ToolCall):
                calls.append(entry)
            elif isinstance(entry, dict):
                calls.append(ToolCall.from_dict(entry))
        return calls

    @expected_tool_calls.setter
    def expected_tool_calls(self, value: list[ToolCall | dict[str, Any]] | None) -> None:
        if value is None:
            self.metadata.pop("expected_tool_calls", None)
            return
        serialized: list[dict[str, Any]] = []
        for entry in value:
            if isinstance(entry, ToolCall):
                serialized.append(entry.to_dict())
            else:
                serialized.append(dict(entry))
        self.metadata["expected_tool_calls"] = serialized

    @property
    def source_trace_id(self) -> str | None:
        """Trace identifier stored in metadata for provenance."""
        return self.metadata.get("source_trace_id")

    @source_trace_id.setter
    def source_trace_id(self, value: str | None) -> None:
        if value is None:
            self.metadata.pop("source_trace_id", None)
        else:
            self.metadata["source_trace_id"] = value

    @property
    def source_node_id(self) -> str | None:
        """Node identifier stored in metadata for provenance."""
        return self.metadata.get("source_node_id")

    @source_node_id.setter
    def source_node_id(self, value: str | None) -> None:
        if value is None:
            self.metadata.pop("source_node_id", None)
        else:
            self.metadata["source_node_id"] = value

    @staticmethod
    def _ensure_datetime(value: datetime | str | int | float | None) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc)
        if isinstance(value, str):
            normalized = value.strip()
            if normalized.endswith("Z"):
                normalized = normalized[:-1] + "+00:00"
            try:
                return datetime.fromisoformat(normalized)
            except ValueError:
                return None
        return None


@dataclass
class TestCase:
    """Describes a planned execution of a dataset example (input to the runner)."""

    example: DatasetExample
    repetition_number: int = 1
    run_id: str = ""
    __test__ = False  # Prevent pytest from treating this as a test container

    def __post_init__(self) -> None:
        if self.repetition_number < 1:
            raise ValueError("repetition_number must be >= 1")
        if not self.run_id:
            if self.example.id:
                self.run_id = f"{self.example.id}#{self.repetition_number}"
            else:
                self.run_id = uuid4().hex

    @property
    def example_id(self) -> str:
        """Convenience accessor for the underlying example ID."""
        return self.example.id or ""


@dataclass
class EvaluationContext:
    """
    Rich evaluation context providing evaluators with all available data.

    Gives evaluators access to:
    - Original dataset input/output (flexible dicts)
    - Actual output from test function
    - Execution metadata and timing
    - Full context for sophisticated evaluation logic
    """

    example_id: str
    run_id: str
    repetition_number: int
    actual_output: Any
    """The actual output from the test function (string, dict, etc.)"""

    # Flexible input/output from dataset example
    input: dict[str, Any] = field(default_factory=dict)
    """Original input data from dataset example"""

    output: dict[str, Any] = field(default_factory=dict)
    """Reference output data from dataset example"""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Full metadata from original dataset example"""

    # Tool call data for evaluation
    expected_tool_calls: list[ToolCall] | None = None
    """Expected tool calls from dataset example"""

    actual_tool_calls: list[ToolCall] | None = None
    """Actual tool calls from test function execution"""

    # Execution context
    started_at: datetime | None = None
    """UTC timestamp when execution for this context started"""

    completed_at: datetime | None = None
    """UTC timestamp when execution for this context completed"""

    execution_time_ms: float | None = None
    error: str | None = None
    execution_metadata: dict[str, Any] = field(default_factory=dict)
    """Additional execution context (traces, performance, etc.)"""

    trace_id: str | None = None
    """Trace identifier captured during execution, if available"""


@dataclass
class EvaluationMetric:
    """
    Structured evaluation result with rich metadata support.
    """

    name: str
    """Name of the evaluation metric"""

    score: float
    """Numerical score (0.0 to 1.0 typical, but not enforced)"""

    metadata: dict[str, Any] = field(default_factory=dict)
    """
    Rich metadata about the evaluation:
    - Reasoning: {"reason": "Response includes required information"}
    - Confidence: {"confidence": 0.95}
    - Breakdown: {"accuracy": 0.9, "completeness": 0.8}
    - Custom: {"any_field": "any_value"}
    """

    label: str | None = None
    """Optional categorical label (e.g., "good", "bad", "correct")"""

    explanation: str | None = None
    """Optional human-readable explanation"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "score": self.score,
            "metadata": self.metadata,
            "label": self.label,
            "explanation": self.explanation,
        }


@dataclass
class AggregateEvaluationContext:
    """
    Context passed to aggregate evaluators.

    Provides access to the full run: raw contexts, example results, config,
    examples, and experiment metadata.
    """

    experiment_id: str
    config: "ExperimentConfig"
    contexts: list["EvaluationContext"]
    results: list["ExperimentResult"]
    examples: list[DatasetExample]
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def total_examples(self) -> int:
        """Total number of runs executed."""
        return len(self.results)

    @property
    def successful_examples(self) -> int:
        """Number of runs without errors."""
        return len([r for r in self.results if not getattr(r, "error", None)])

    @property
    def failed_examples(self) -> int:
        """Number of runs that failed."""
        return self.total_examples - self.successful_examples


@dataclass
class LLMCall:
    """Represents a single LLM API call within an agent trace."""

    prompt: str
    response: str
    model: str | None = None
    tokens_used: int | None = None
    token_cost: float | None = None
    latency_ms: float | None = None
    timestamp: str | None = None
    step_context: str | None = None  # Which agent step this call belongs to
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentStep:
    """Represents a single step in an agent's reasoning process."""

    action: str  # "search", "reasoning", "tool_call", "format_response", etc.
    input: str  # What the agent received for this step
    output: str  # What the agent produced from this step
    step_type: str = "action"  # "action", "observation", "thought", "tool_use"
    timestamp: str | None = None
    execution_time_ms: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentTrace:
    """Captures the complete execution trace of an agent."""

    final_response: str
    steps: list[AgentStep] = field(default_factory=list)
    llm_calls: list[LLMCall] = field(default_factory=list)
    tools_called: list[ToolCall] = field(default_factory=list)

    # Aggregated metrics
    total_tokens: int | None = None
    total_cost: float | None = None
    execution_time_ms: float | None = None

    # Agent reasoning
    reasoning_trace: list[str] = field(default_factory=list)  # Thought process
    context_retrieved: list[str] = field(default_factory=list)  # RAG context

    # Metadata
    agent_type: str | None = None  # "react", "plan_execute", "cot", etc.
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def step_count(self) -> int:
        """Number of reasoning steps taken."""
        return len(self.steps)

    @property
    def tool_usage_summary(self) -> dict[str, int]:
        """Count of each tool used."""
        tool_counts = {}
        for tool in self.tools_called:
            tool_counts[tool.name] = tool_counts.get(tool.name, 0) + 1
        return tool_counts


# Type aliases for common patterns
TestFunctionOutput = str | dict[str, Any] | list[Any] | AgentTrace
EvaluatorResult = float | tuple[float, dict[str, Any]] | EvaluationMetric
