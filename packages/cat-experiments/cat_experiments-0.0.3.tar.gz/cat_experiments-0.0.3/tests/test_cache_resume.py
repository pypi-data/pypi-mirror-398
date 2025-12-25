from __future__ import annotations

from pathlib import Path

from cat.experiments import DatasetExample, ExperimentConfig
from cat.experiments.adapters import LocalCacheResumeCoordinator
from cat.experiments.models import EvaluationMetric
from cat.experiments.runner_builders import build_local_runner
from cat.experiments.types import AggregateEvaluatorResult


def _build_dataset() -> list[DatasetExample]:
    return [
        DatasetExample(
            id="example-1",
            input={"messages": [{"role": "user", "content": "Hi"}]},
            output={"messages": [{"role": "assistant", "content": "Hello"}]},
            metadata={"topic": "greeting"},
        )
    ]


def _simple_task(example: DatasetExample) -> str:
    return "Hello!"


def test_local_storage_adapter_persists_examples(tmp_path: Path):
    dataset = _build_dataset()
    runner = build_local_runner(storage_dir=tmp_path)

    summary = runner.run(
        dataset=dataset,
        task=_simple_task,
        evaluators=[],
        config=ExperimentConfig(name="cache-test"),
    )

    exp_path = tmp_path / summary.experiment_id
    examples_file = exp_path / "examples.jsonl"

    assert examples_file.exists()
    lines = [line for line in examples_file.read_text().splitlines() if line.strip()]
    assert len(lines) == len(dataset)


def test_local_resume_coordinator_runs_pending_examples(tmp_path: Path):
    dataset = _build_dataset()
    runner = build_local_runner(storage_dir=tmp_path)

    summary = runner.run(
        dataset=dataset,
        task=_simple_task,
        evaluators=[],
        config=ExperimentConfig(name="resume-test", repetitions=2),
    )

    exp_path = tmp_path / summary.experiment_id
    runs_file = exp_path / "runs.jsonl"

    # Keep only the first repetition to simulate an incomplete experiment.
    lines = [line for line in runs_file.read_text().splitlines() if line.strip()]
    assert len(lines) == 2
    with open(runs_file, "w") as f:
        f.write(lines[0] + "\n")

    coordinator = LocalCacheResumeCoordinator(storage_dir=tmp_path)
    plan = coordinator.build_task_resume_plan(summary.experiment_id)

    assert plan.has_work
    assert plan.run_selection == {"example-1": {2}}
    assert len(plan.dataset_examples) == 1

    resume_runner = build_local_runner(storage_dir=tmp_path)
    resume_summary = coordinator.resume_task_runs(
        experiment_id=summary.experiment_id,
        task=_simple_task,
        runner=resume_runner,
    )

    assert resume_summary is not None
    assert resume_summary.total_examples == 2

    # Ensure the missing repetition has now been appended.
    final_lines = [line for line in runs_file.read_text().splitlines() if line.strip()]
    assert len(final_lines) >= 2
    summary_payload = (exp_path / "summary.json").read_text()
    assert '"total_examples": 2' in summary_payload


def test_local_resume_recomputes_aggregates(tmp_path: Path):
    dataset = _build_dataset()
    runner = build_local_runner(storage_dir=tmp_path)

    summary = runner.run(
        dataset=dataset,
        task=_simple_task,
        evaluators=[],
        config=ExperimentConfig(name="resume-agg", repetitions=2),
    )

    exp_path = tmp_path / summary.experiment_id
    runs_file = exp_path / "runs.jsonl"

    lines = [line for line in runs_file.read_text().splitlines() if line.strip()]
    # Keep only first repetition to simulate incomplete run
    with open(runs_file, "w") as f:
        f.write(lines[0] + "\n")

    coordinator = LocalCacheResumeCoordinator(storage_dir=tmp_path)

    def agg_eval(ctx) -> AggregateEvaluatorResult:
        return {"total_runs": EvaluationMetric(name="total_runs", score=len(ctx.results))}

    resume_runner = build_local_runner(storage_dir=tmp_path)
    resume_summary = coordinator.resume_task_runs(
        experiment_id=summary.experiment_id,
        task=_simple_task,
        runner=resume_runner,
        aggregate_evaluators=[agg_eval],
    )

    assert resume_summary is not None
    assert resume_summary.aggregate_scores["total_runs"] == 2

    summary_payload = (exp_path / "summary.json").read_text()
    assert '"total_runs": 2' in summary_payload
