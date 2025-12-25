"""Tests for the Phoenix evaluation backend."""

from __future__ import annotations

from typing import Any, cast

from cat.experiments import EvaluationMetric, ExperimentRunner
from cat.experiments.adapters.phoenix_evaluator import PhoenixEvaluationCoordinator


class _StubResponse:
    def __init__(self, data: dict[str, object]) -> None:
        self._data = data

    def json(self) -> dict[str, object]:
        return self._data

    def raise_for_status(self) -> None:
        return None


class _StubHTTP:
    def __init__(self, example_payload: dict, run_payload: dict) -> None:
        self.run_payload = run_payload
        self.posts: list[dict] = []

    def get(self, url: str, params=None, timeout=None):
        if url.endswith("/experiments/exp-1/runs"):
            return _StubResponse({"data": [self.run_payload], "next_cursor": None})
        raise AssertionError(f"unexpected GET {url}")

    def post(self, url: str, json=None, timeout=None):
        self.posts.append({"url": url, "json": json})
        return _StubResponse({"data": {"id": "eval-1"}})


class _StubExperiments:
    def __init__(self, payload: dict):
        self._payload = payload

    def get(self, experiment_id: str):
        assert experiment_id == self._payload["id"]
        return self._payload


class _StubDatasets:
    def __init__(self, payload: dict):
        self._payload = payload

    def get_dataset(self, dataset: str, version_id=None, timeout=None):
        assert dataset == self._payload["id"]
        return self._payload


class _StubPhoenixClient:
    def __init__(self, experiment_payload: dict, dataset_payload: dict, run_payload: dict):
        self.experiments = _StubExperiments(experiment_payload)
        self.datasets = _StubDatasets(dataset_payload)
        self._client = _StubHTTP(dataset_payload.get("examples", [{}])[0], run_payload)


def test_phoenix_evaluation_backend_posts_new_evaluations():
    experiment_payload = {
        "id": "exp-1",
        "dataset_id": "ds-1",
        "dataset_version_id": "v1",
        "metadata": {},
        "tags": [],
    }

    example_payload = {
        "id": "ex-1",
        "input": {"prompt": "hi"},
        "output": {"answer": "hello"},
        "metadata": {},
    }

    dataset_payload = {
        "id": "ds-1",
        "version_id": "v1",
        "examples": [example_payload],
    }

    run_payload = {
        "id": "run-1",
        "dataset_example_id": "ex-1",
        "output": {"answer": "hello"},
        "repetition_number": 1,
        "start_time": "2024-01-01T00:00:00Z",
        "end_time": "2024-01-01T00:00:01Z",
    }

    client = cast(Any, _StubPhoenixClient(experiment_payload, dataset_payload, run_payload))
    backend = PhoenixEvaluationCoordinator(client)

    def accuracy(ctx):
        return EvaluationMetric(name="accuracy", score=1.0)

    runner = ExperimentRunner()
    results = backend.run_evaluators(
        experiment_id="exp-1",
        evaluators=[accuracy],
        runner=runner,
    )

    assert results[0].evaluation_scores["accuracy"] == 1.0
    assert len(client._client.posts) == 1
    payload = client._client.posts[0]["json"]
    assert payload["experiment_run_id"] == "run-1"
    assert payload["name"] == "accuracy"
