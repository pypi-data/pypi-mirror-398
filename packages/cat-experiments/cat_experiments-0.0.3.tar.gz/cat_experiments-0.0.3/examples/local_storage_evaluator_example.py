"""Local storage adapter demo with follow-up evaluator runs."""

from __future__ import annotations

from pathlib import Path

from cat.experiments import DatasetExample, EvaluationContext, EvaluationMetric, ExperimentConfig
from cat.experiments.adapters import LocalEvaluationCoordinator
from cat.experiments.runner_builders import build_local_runner

SAMPLE_DATASET = [
    DatasetExample(
        input={"question": "How do I reset my password?"},
        output={"answer": "Open Settings → Security and follow the reset link."},
        metadata={"category": "auth"},
        id="ex-1",
    ),
    DatasetExample(
        input={"question": "Can I upgrade mid-cycle?"},
        output={"answer": "Yes, the difference is prorated on your next invoice."},
        metadata={"category": "billing"},
        id="ex-2",
    ),
]


def test_function(example: DatasetExample) -> dict[str, str]:
    return {"answer": f"(auto) {example.input['question']}"}


def echo_check_evaluator(context: EvaluationContext) -> EvaluationMetric:
    expected = context.output.get("answer", "")
    actual = (
        context.actual_output
        if isinstance(context.actual_output, str)
        else str(context.actual_output)
    )
    score = 1.0 if expected.lower() in actual.lower() else 0.0
    return EvaluationMetric(name="echo_check", score=score, label="match" if score else "mismatch")


def contains_keyword_evaluator(context: EvaluationContext) -> EvaluationMetric:
    keyword = context.metadata.get("category", "")
    actual = (
        context.actual_output
        if isinstance(context.actual_output, str)
        else str(context.actual_output)
    )
    score = 1.0 if keyword and keyword in actual.lower() else 0.0
    return EvaluationMetric(
        name="keyword_category",
        score=score,
        label="contains" if score else "missing",
        metadata={"keyword": keyword},
    )


def main() -> None:
    cache_dir = Path.cwd() / ".cat_cache_local_demo"
    cache_dir.mkdir(parents=True, exist_ok=True)

    runner = build_local_runner(storage_dir=cache_dir, clean_on_success=False)

    config = ExperimentConfig(
        name="local-storage-demo",
        dataset_id="local-support",
        dataset_version_id="v1",
        metadata={"source": "examples/local"},
    )

    summary = runner.run(
        dataset=SAMPLE_DATASET,
        task=test_function,
        evaluators=[echo_check_evaluator],
        config=config,
    )

    print("Initial run complete")
    print(f"  Successful: {summary.successful_examples}/{summary.total_examples}")
    print(f"  Scores: {summary.average_scores}")
    print(f"  Results cached under {cache_dir / summary.experiment_id}")

    coordinator = LocalEvaluationCoordinator(storage_dir=cache_dir)
    updated_results = coordinator.run_evaluators(
        experiment_id=summary.experiment_id,
        evaluators=[contains_keyword_evaluator],
    )

    print("Added keyword evaluator to cached runs:")
    for result in updated_results:
        print(
            f"  {result.example_id}: keyword score = "
            f"{result.evaluation_scores.get('keyword_category')}"
        )


if __name__ == "__main__":
    main()
