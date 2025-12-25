"""Tests for the Cat Cafe listener adapter."""

from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime
from typing import cast

from cat.cafe.client import ExperimentResult as CatCafeExperimentResult

from cat.experiments import DatasetExample, ExperimentConfig, ExperimentResult, ExperimentSummary
from cat.experiments.adapters.cat_cafe import (
    CatCafeExperimentListener,
    CatCafeSyncConfig,
    convert_result_to_cat_cafe,
)
from cat.experiments.adapters.cat_cafe_listener import CATCafeClient


class _StubCatCafeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def start_experiment(self, experiment):
        self.calls.append(("start", {"experiment": experiment}))
        return "server-exp-1"

    def create_run(self, experiment_id: str, payload: dict):
        self.calls.append(("create_run", {"experiment_id": experiment_id, "payload": payload}))
        return payload

    def append_evaluation(self, experiment_id: str, run_id: str, payload: dict):
        self.calls.append(
            (
                "append_evaluation",
                {"experiment_id": experiment_id, "run_id": run_id, "payload": payload},
            )
        )
        return payload

    def complete_experiment(self, experiment_id: str, summary):
        self.calls.append(("complete", {"experiment_id": experiment_id, "summary": summary}))


def test_cat_cafe_listener_batches_and_completes():
    client_stub = _StubCatCafeClient()
    client: CATCafeClient = cast(CATCafeClient, client_stub)
    listener = CatCafeExperimentListener(
        client,
        config=CatCafeSyncConfig(),
    )

    config = ExperimentConfig(
        name="Listener Demo",
        description="testing",
        dataset_id="ds-1",
        dataset_version_id="ver-1",
        tags=["demo"],
        metadata={"source": "test"},
    )
    example = DatasetExample(
        input={"question": "hi"},
        output={"answer": "hello"},
        metadata={},
        id="ex-1",
    )

    started_at = datetime.now(UTC)
    completed_at = datetime.now(UTC)

    listener.on_experiment_started("local-exp", config, [example])

    result = ExperimentResult(
        example_id="ex-1",
        run_id="ex-1#1",
        repetition_number=1,
        started_at=started_at,
        completed_at=completed_at,
        input_data={"question": "hi"},
        output={"answer": "hello"},
        actual_output={"answer": "hello"},
        evaluation_scores={"exact_match": 1.0},
        evaluator_metadata={
            "exact_match": {
                "execution_time_ms": 12.5,
                "label": "pass",
                "explanation": "identical",
            }
        },
        metadata={"execution_time_ms": 5.0},
        trace_id="trace-123",
        error=None,
        execution_time_ms=5.0,
    )

    listener.on_task_completed("local-exp", result)

    summary = ExperimentSummary(
        total_examples=1,
        successful_examples=1,
        failed_examples=0,
        average_scores={"exact_match": 1.0},
        total_execution_time_ms=5.0,
        experiment_id="local-exp",
        config=config,
        started_at=started_at,
        completed_at=completed_at,
    )

    listener.on_experiment_completed("local-exp", [result], summary)

    assert [call[0] for call in client_stub.calls[:4]] == [
        "start",
        "create_run",
        "append_evaluation",
        "complete",
    ]
    run_payload = client_stub.calls[1][1]["payload"]
    assert run_payload["example_id"] == "ex-1"
    assert run_payload["metadata"]["evaluator_execution_times_ms"]["exact_match"] == 12.5

    eval_payload = client_stub.calls[2][1]["payload"]
    assert eval_payload["evaluator_name"] == "exact_match"
    assert eval_payload["score"] == 1.0
    assert eval_payload["label"] == "pass"
    assert eval_payload["explanation"] == "identical"

    summary_payload = client_stub.calls[3][1]["summary"]
    assert summary_payload["total_examples"] == 1
    assert summary_payload["successful_examples"] == 1


def test_convert_result_to_cat_cafe_preserves_timing_in_metadata():
    field_names = {f.name for f in fields(CatCafeExperimentResult)}
    assert "run_id" in field_names, "cat-cafe-client is outdated; expected ExperimentResult.run_id"

    result = ExperimentResult(
        example_id="ex-1",
        run_id="ex-1#1",
        repetition_number=1,
        started_at=None,
        completed_at=None,
        input_data={"question": "hi"},
        output={"answer": "hello"},
        actual_output={"answer": "hi"},
        evaluation_scores={"exact_match": 1.0},
        evaluator_metadata={
            "exact_match": {
                "execution_time_ms": 12.5,
            }
        },
        metadata={},
        trace_id=None,
        error=None,
        execution_time_ms=5.0,
    )

    converted = convert_result_to_cat_cafe(result)

    assert converted.metadata["execution_time_ms"] == 5.0
    assert converted.metadata["evaluator_execution_times_ms"] == {"exact_match": 12.5}
    assert getattr(converted, "evaluator_execution_times")["exact_match"] == 12.5
