"""Tests for Phoenix resume coordinator."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast

import httpx

from cat.experiments import DatasetExample, ExperimentConfig, ExperimentRunner
from cat.experiments.adapters.phoenix_resume import (
    PhoenixResumeCoordinator,
    PhoenixTaskResumePlan,
)
from cat.experiments.experiments import ExperimentSummary


class StubHttpResponse:
    def __init__(
        self, *, data: list[dict[str, Any]], next_cursor: str | None = None, status: int = 200
    ):
        self._body = {"data": data, "next_cursor": next_cursor}
        self.status_code = status
        self.headers = {"content-type": "application/json"}

    def json(self) -> dict[str, Any]:
        return self._body

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error",
                request=httpx.Request("GET", "http://example.com"),
                response=httpx.Response(self.status_code, headers=self.headers),
            )


class StubHttpClient:
    def __init__(self, responses: list[StubHttpResponse]):
        self._responses = responses
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def get(self, url: str, *, params: dict[str, Any], timeout: int) -> StubHttpResponse:
        self.calls.append((url, params))
        if not self._responses:
            raise AssertionError("No more responses configured for StubHttpClient")
        return self._responses.pop(0)


class StubExperimentsAPI:
    def __init__(self, payload: dict[str, Any]):
        self._payload = payload

    def get(self, experiment_id: str) -> dict[str, Any]:
        return dict(self._payload)


def make_stub_client(*, experiment_payload: dict[str, Any], responses: list[StubHttpResponse]):
    experiments_api = StubExperimentsAPI(experiment_payload)
    http_client = StubHttpClient(responses)
    return SimpleNamespace(experiments=experiments_api, _client=http_client)


def sample_experiment_payload() -> dict[str, Any]:
    return {
        "id": "exp_remote",
        "name": "Support Demo",
        "description": "Remote Phoenix experiment",
        "dataset_id": "dataset_abc",
        "dataset_version_id": "version_xyz",
        "repetitions": 3,
        "metadata": {"source": "phoenix"},
        "tags": ["demo"],
    }


def test_build_task_resume_plan_collects_examples_and_runs():
    incomplete_page_one = [
        {
            "dataset_example": {
                "id": "ex_a",
                "input": {"question": "A"},
                "output": {"answer": "a"},
                "metadata": {"topic": "billing"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
            "repetition_numbers": [1, 3],
        },
    ]
    incomplete_page_two = [
        {
            "dataset_example": {
                "id": "ex_b",
                "input": {"question": "B"},
                "output": {"answer": "b"},
                "metadata": {},
            },
            "repetition_numbers": [2],
        }
    ]

    client = make_stub_client(
        experiment_payload=sample_experiment_payload(),
        responses=[
            StubHttpResponse(data=incomplete_page_one, next_cursor="cursor-1"),
            StubHttpResponse(data=incomplete_page_two, next_cursor=None),
        ],
    )
    coordinator = PhoenixResumeCoordinator(cast(Any, client))

    plan = coordinator.build_task_resume_plan(experiment_id="exp_remote")

    assert isinstance(plan, PhoenixTaskResumePlan)
    assert plan.config.dataset_id == "dataset_abc"
    assert plan.config.repetitions == 3
    assert plan.run_selection == {"ex_a": {1, 3}, "ex_b": {2}}
    ids = sorted(example.id or "" for example in plan.dataset_examples)
    assert ids == ["ex_a", "ex_b"]
    assert plan.has_work is True


def test_resume_task_runs_invokes_runner_with_selection(monkeypatch):
    incomplete_runs = [
        {
            "dataset_example": {
                "id": "ex_resume",
                "input": {"question": "Resume"},
                "output": {"answer": "resume"},
            },
            "repetition_numbers": [2],
        }
    ]
    client = make_stub_client(
        experiment_payload=sample_experiment_payload(),
        responses=[StubHttpResponse(data=incomplete_runs, next_cursor=None)],
    )

    class StubRunner(ExperimentRunner):
        def __init__(self):
            super().__init__()
            self.call_args: dict[str, Any] | None = None

        def run(  # type: ignore[override]
            self,
            dataset,
            task=None,
            evaluators=None,
            config=None,
            experiment_id=None,
            run_selection=None,
            **kwargs,
        ):
            self.call_args = {
                "dataset": dataset,
                "evaluators": evaluators,
                "config": config,
                "experiment_id": experiment_id,
                "run_selection": run_selection,
            }
            config = config or ExperimentConfig(name="stub")
            return ExperimentSummary(
                total_examples=1,
                successful_examples=1,
                failed_examples=0,
                average_scores={},
                total_execution_time_ms=0,
                experiment_id=experiment_id or "local",
                config=config,
                started_at=datetime.now(UTC),
            )

    runner = StubRunner()
    coordinator = PhoenixResumeCoordinator(cast(Any, client))

    def task(example: DatasetExample) -> dict[str, Any]:
        return {"answer": example.output.get("answer")}

    summary = coordinator.resume_task_runs(
        experiment_id="exp_remote",
        task=task,
        evaluators=[],
        runner=runner,
    )

    assert summary is not None
    assert runner.call_args is not None
    assert runner.call_args["run_selection"] == {"ex_resume": {2}}
    assert len(runner.call_args["dataset"]) == 1


def test_resume_task_runs_returns_none_when_complete():
    client = make_stub_client(
        experiment_payload=sample_experiment_payload(),
        responses=[StubHttpResponse(data=[], next_cursor=None)],
    )
    coordinator = PhoenixResumeCoordinator(cast(Any, client))

    summary = coordinator.resume_task_runs(
        experiment_id="exp_remote",
        task=lambda ex: {},
        evaluators=[],
    )

    assert summary is None
