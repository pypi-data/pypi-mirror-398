"""Tests for the local storage adapter."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cat.experiments import DatasetExample, ExperimentConfig, ExperimentRunner
from cat.experiments.adapters import LocalStorageExperimentListener, LocalStorageSyncConfig
from cat.experiments.models import EvaluationMetric


@pytest.fixture
def sample_examples():
    return [
        DatasetExample(
            input={"query": "alpha"},
            output={"response": "expected"},
        )
    ]


def test_cache_listener_writes_runs(tmp_path, sample_examples):
    runner = ExperimentRunner()
    runner.add_listener(
        LocalStorageExperimentListener(
            config=LocalStorageSyncConfig(base_dir=tmp_path),
        )
    )

    config = ExperimentConfig(name="Cache Write")

    runner.run(
        dataset=sample_examples,
        task=lambda example: example.input["query"].upper(),
        config=config,
        experiment_id="cache-write",
    )

    cache_path = tmp_path / "cache-write"
    runs_file = cache_path / "runs.jsonl"

    assert runs_file.exists()
    data = [json.loads(line) for line in runs_file.read_text().splitlines()]
    assert len(data) == 1
    assert data[0]["actual_output"] == "ALPHA"


def test_cache_disabled(tmp_path, sample_examples):
    runner = ExperimentRunner()
    config = ExperimentConfig(name="No Cache")

    runner.run(
        dataset=sample_examples,
        task=lambda example: example.input["query"],
        config=config,
        experiment_id="no-cache",
    )

    assert not (tmp_path / "no-cache").exists()


def test_cache_clean_on_success(tmp_path, sample_examples):
    runner = ExperimentRunner()
    runner.add_listener(
        LocalStorageExperimentListener(
            config=LocalStorageSyncConfig(base_dir=tmp_path, clean_on_success=True),
        )
    )
    config = ExperimentConfig(name="Clean Cache")

    runner.run(
        dataset=sample_examples,
        task=lambda example: example.input["query"],
        config=config,
        experiment_id="clean-cache",
    )

    assert not (tmp_path / "clean-cache").exists()


def test_cache_retained_on_failure(tmp_path, sample_examples):
    runner = ExperimentRunner()
    runner.add_listener(
        LocalStorageExperimentListener(
            config=LocalStorageSyncConfig(base_dir=tmp_path),
        )
    )
    config = ExperimentConfig(name="Failure Cache")

    def failing(_example):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        runner.run(
            dataset=sample_examples,
            task=failing,
            config=config,
            experiment_id="fail-cache",
        )

    failure_dir = tmp_path / "fail-cache"
    assert failure_dir.exists()
    failure_file = failure_dir / "failure.json"
    assert failure_file.exists()


def test_cache_summary_includes_aggregate_metrics(tmp_path, sample_examples):
    runner = ExperimentRunner()
    runner.add_listener(
        LocalStorageExperimentListener(
            config=LocalStorageSyncConfig(base_dir=tmp_path),
        )
    )

    aggregate_calls: list[tuple[str, int]] = []

    def aggregate_evaluator(ctx):
        aggregate_calls.append((ctx.experiment_id, ctx.total_examples))
        return {
            "agg_metric": EvaluationMetric(name="agg_metric", score=0.42, metadata={"note": "ok"}),
            "raw_score": 1.0,
        }

    summary = runner.run(
        dataset=sample_examples,
        task=lambda example: example.input["query"],
        config=ExperimentConfig(name="Aggregate Cache"),
        experiment_id="aggregate-cache",
        aggregate_evaluators=[aggregate_evaluator],
    )

    cache_path = tmp_path / "aggregate-cache"
    summary_file = cache_path / "summary.json"

    assert summary_file.exists()
    payload = json.loads(summary_file.read_text())
    assert payload["aggregate_scores"] == {"agg_metric": 0.42, "raw_score": 1.0}
    assert "agg_metric" in payload["aggregate_metadata"]
    assert aggregate_calls == [("aggregate-cache", 1)]
    # Summary object also carries aggregates
    assert summary.aggregate_scores["agg_metric"] == 0.42
