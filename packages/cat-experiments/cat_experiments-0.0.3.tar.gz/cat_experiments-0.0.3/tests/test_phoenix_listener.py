"""Tests for the Phoenix experiment listener adapter."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterator, cast

from cat.experiments.adapters.phoenix import PhoenixExperimentListener, PhoenixSyncConfig
from cat.experiments.experiments import ExperimentConfig, ExperimentResult, ExperimentSummary
from cat.experiments.models import DatasetExample


class _StubResponse:
    def __init__(self, *, status_code: int = 200, data: dict[str, Any] | None = None):
        self._status_code = status_code
        self._data = data or {}

    def raise_for_status(self) -> None:
        if self._status_code >= 400:
            raise RuntimeError(f"HTTP {self._status_code}")

    def json(self) -> dict[str, Any]:
        return {"data": self._data}


class _StubHTTPClient:
    def __init__(self, responses: Iterator[dict[str, Any]]):
        self.requests: list[dict[str, Any]] = []
        self._responses = responses

    def post(self, url: str, *, json: Any, timeout: int | float | None = None):
        self.requests.append({"url": url, "json": json, "timeout": timeout})
        try:
            payload = next(self._responses)
        except StopIteration:  # pragma: no cover - protects against insufficient fixtures
            payload = {}
        return _StubResponse(data=payload)


class _StubPhoenixClient:
    def __init__(self, http_client: _StubHTTPClient):
        self._client = http_client
        self.datasets = _StubDatasets()
        self.experiments = _StubExperiments()


class _StubDatasets:
    def get_dataset(self, dataset: str, version_id: str | None = None, timeout: int | None = None):
        return type(
            "Dataset",
            (),
            {
                "examples": [
                    {
                        "id": "ex-1",
                        "input": {"prompt": "hi"},
                        "output": {"expected": "hello"},
                        "metadata": {},
                    }
                ]
            },
        )()


class _StubExperiments:
    def create(
        self,
        *,
        dataset_id: str,
        dataset_version_id: str | None = None,
        experiment_name: str | None = None,
        experiment_description: str | None = None,
        experiment_metadata: dict[str, Any] | None = None,
        splits=None,
        repetitions: int = 1,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        return {"id": "exp-remote-1", "project_name": "demo-project"}


def test_phoenix_listener_posts_runs_and_evaluations(tmp_path):
    responses = iter(
        [
            {"id": "run-remote-1"},
            {"id": "eval-remote-1"},
        ]
    )
    http_client = _StubHTTPClient(responses)
    phoenix_client = cast(Any, _StubPhoenixClient(http_client))
    listener = PhoenixExperimentListener(phoenix_client, config=PhoenixSyncConfig())

    example = DatasetExample(
        input={"prompt": "hi"}, output={"expected": "hello"}, metadata={}, id="ex-1"
    )
    config = ExperimentConfig(
        name="demo",
        description="desc",
        dataset_id="dataset-123",
        dataset_version_id="dataset-version-1",
        repetitions=1,
    )

    listener.on_experiment_started("local-exp-1", config, [example])

    assert listener._remote_experiment_id == "exp-remote-1"

    started_at = datetime.now(UTC)
    completed_at = datetime.now(UTC)
    eval_started_at = datetime.now(UTC)
    eval_completed_at = datetime.now(UTC)

    result = ExperimentResult(
        example_id="ex-1",
        run_id="ex-1#1",
        repetition_number=1,
        started_at=started_at,
        completed_at=completed_at,
        input_data={"input": {}},
        output={"expected": "hello"},
        actual_output={"response": "hello"},
        evaluation_scores={"accuracy": 0.9},
        evaluator_metadata={
            "accuracy": {
                "label": "pass",
                "explanation": "looks good",
                "annotator_kind": "LLM",
                "started_at": eval_started_at.isoformat(),
                "completed_at": eval_completed_at.isoformat(),
                "execution_time_ms": 12.3,
            }
        },
        metadata={
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
        },
        trace_id="trace-1",
        error=None,
        execution_time_ms=42.0,
    )

    listener.on_task_completed("local-exp-1", result)
    summary = ExperimentSummary(
        total_examples=1,
        successful_examples=1,
        failed_examples=0,
        average_scores=result.evaluation_scores,
        total_execution_time_ms=result.execution_time_ms or 0.0,
        experiment_id="local-exp-1",
        config=config,
        started_at=started_at,
        completed_at=completed_at,
    )
    listener.on_experiment_completed("local-exp-1", [result], summary=summary)

    # Verify HTTP calls (stream runs/evals; dataset fetch + experiment create done via client)
    run_request = http_client.requests[0]
    assert run_request["url"] == "v1/experiments/exp-remote-1/runs"
    assert run_request["json"]["dataset_example_id"] == "ex-1"
    assert run_request["json"]["trace_id"] == "trace-1"
    eval_request = http_client.requests[1]
    assert eval_request["url"] == "v1/experiment_evaluations"
    assert eval_request["json"]["experiment_run_id"] == "run-remote-1"
    assert eval_request["json"]["result"]["score"] == 0.9
    assert eval_request["json"]["annotator_kind"] == "LLM"
