"""Tests for rehydrating CAT Cafe runs for additional evaluators."""

from __future__ import annotations

from typing import cast

from cat.experiments.adapters.cat_cafe_evaluator import CatCafeEvaluationCoordinator
from cat.experiments.adapters.cat_cafe_listener import CATCafeClient


class _StubCatCafeClient:
    def __init__(self) -> None:
        self.runs: list[tuple[str, dict]] = []
        self.evaluations: list[tuple[str, str, dict]] = []

    def get_dataset_examples(self, dataset_id: str, version: str | None = None) -> list[dict]:
        return [
            {
                "id": "ex-1",
                "input": {"question": "hi"},
                "output": {"answer": "hello"},
                "metadata": {},
            }
        ]

    def get_experiment_detail(self, experiment_id: str) -> dict:
        return {
            "experiment": {
                "id": experiment_id,
                "name": "cat-demo",
                "description": "demo",
                "dataset_id": "ds",
                "dataset_version": None,
                "tags": [],
                "metadata": {},
            },
            "results": [
                {
                    "example_id": "ex-1",
                    "run_id": "ex-1#1",
                    "repetition_number": 1,
                    "input_data": {"question": "hi"},
                    "output": {"answer": "hello"},
                    "actual_output": {"answer": "hello"},
                    "metadata": {},
                }
            ],
        }

    def create_run(self, experiment_id: str, payload: dict):
        self.runs.append((experiment_id, payload))
        return payload

    def append_evaluation(self, experiment_id: str, run_id: str, payload: dict):
        self.evaluations.append((experiment_id, run_id, payload))
        return payload


def test_cat_cafe_evaluation_coordinator_runs_extra_evaluator():
    client_stub = _StubCatCafeClient()
    client: CATCafeClient = cast(CATCafeClient, client_stub)
    coordinator = CatCafeEvaluationCoordinator(client)

    def accuracy(context):
        return 1.0 if context.actual_output == context.output else 0.0

    results = coordinator.run_evaluators(
        experiment_id="exp-1",
        evaluators=[accuracy],
    )

    assert results[0].evaluation_scores["accuracy"] == 1.0
    assert len(client_stub.runs) == 1
    run_payload = client_stub.runs[0][1]
    assert run_payload["run_id"] == "ex-1#1"

    assert len(client_stub.evaluations) == 1
    eval_payload = client_stub.evaluations[0][2]
    assert eval_payload["evaluator_name"] == "accuracy"
    assert eval_payload["score"] == 1.0


class _PagingCatCafeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None, int | None, int | None]] = []

    def get_dataset_examples(
        self,
        dataset_id: str,
        version: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict]:
        self.calls.append((dataset_id, version, limit, offset))
        total = 520
        start = offset or 0
        end = min(start + (limit or 100), total)
        return [
            {
                "id": f"ex-{i}",
                "input": {"question": f"q-{i}"},
                "output": {"answer": f"a-{i}"},
                "metadata": {},
            }
            for i in range(start, end)
        ]


def test_cat_cafe_coordinator_fetches_all_pages():
    client_stub = _PagingCatCafeClient()
    examples = CatCafeEvaluationCoordinator._fetch_dataset_examples(
        cast(CATCafeClient, client_stub), "ds-1", "v1"
    )

    assert len(examples) == 520
    assert client_stub.calls[0] == ("ds-1", "v1", 500, 0)
    assert client_stub.calls[1] == ("ds-1", "v1", 500, 500)


class _OneShotCatCafeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []

    def get_dataset_examples(self, dataset_id: str, version: str | None = None) -> list[dict]:
        self.calls.append((dataset_id, version))
        return [
            {
                "id": "ex-1",
                "input": {"question": "hi"},
                "output": {"answer": "hello"},
                "metadata": {"tags": ["demo"]},
            }
        ]


def test_cat_cafe_coordinator_handles_clients_without_pagination():
    client_stub = _OneShotCatCafeClient()
    examples = CatCafeEvaluationCoordinator._fetch_dataset_examples(
        cast(CATCafeClient, client_stub), "ds-legacy", None
    )

    assert len(examples) == 1
    assert examples[0]["id"] == "ex-1"
    assert client_stub.calls == [("ds-legacy", None)]
