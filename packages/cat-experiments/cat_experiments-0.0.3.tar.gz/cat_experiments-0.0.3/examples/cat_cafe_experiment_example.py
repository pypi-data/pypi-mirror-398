"""
Run a cat.experiments experiment and sync results to a CAT Cafe server.

This mirrors the CAFÉ experiment lifecycle: dataset → experiment → results →
completion, while keeping the cat.experiments runner fully offline-capable.

Prerequisites
-------------
1. A CAT Cafe server running locally (default http://localhost:8000) or remotely.
2. `cat-cafe-client` and `cat-experiments` installed in the current environment.
3. A dataset already registered with the server, or the name to create one.

Execution
---------
    export CAT_BASE_URL=http://localhost:8000
    export CAT_DATASET=my-dataset
    uv run packages/cat-experiments/examples/cat_cafe_experiment_example.py

The script:
  * Ensures a dataset exists on CAT Cafe (creates a sample one if needed).
  * Converts CAT dataset examples into `cat.experiments.DatasetExample`.
  * Runs a simple experiment and evaluator with `ExperimentRunner`.
  * Uses `CatCafeExperimentListener` so runs and summary are posted back to CAT.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, cast


def _ensure_src_path() -> None:
    """Add the repo src/ directory to sys.path when running from source."""
    project_root = Path(__file__).resolve().parents[1]
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


def _load_cat_cafe_client():
    import cat.cafe.client as cat_client

    return (
        cat_client.CATCafeClient,
        cat_client.Dataset,
        cat_client.DatasetImport,
        cat_client.DatasetExample,
    )


def _load_cat_experiments():
    from cat.experiments import (
        DatasetExample,
        EvaluationContext,
        EvaluationMetric,
        ExperimentConfig,
    )
    from cat.experiments.adapters.cat_cafe import CatCafeExperimentListener, CatCafeSyncConfig
    from cat.experiments.runner_builders import build_cat_cafe_runner

    return (
        DatasetExample,
        EvaluationContext,
        EvaluationMetric,
        ExperimentConfig,
        CatCafeExperimentListener,
        CatCafeSyncConfig,
        build_cat_cafe_runner,
    )


_SAMPLE_DATASET_META = {
    "name": "Support Ticket Demo",
    "description": "Sample dataset auto-created by cat.experiments CAT Cafe example.",
    "metadata": {"source": "cat-experiments-example"},
    "tags": ["support", "demo"],
}

_SAMPLE_EXAMPLES = [
    {
        "id": "ex-1",
        "input": {"question": "Where do I download the desktop app?"},
        "output": {
            "answer": "Visit your dashboard and click Applications to download the installer."
        },
        "metadata": {"category": "product"},
    },
    {
        "id": "ex-2",
        "input": {"question": "Can I get a refund for the premium plan?"},
        "output": {
            "answer": "Yes, refunds are available within 14 days of purchase via billing settings."
        },
        "metadata": {"category": "billing"},
    },
]


def _build_sample_dataset(dataset_cls, dataset_example_cls):
    return dataset_cls(
        id="",
        name=_SAMPLE_DATASET_META["name"],
        description=_SAMPLE_DATASET_META["description"],
        metadata=_SAMPLE_DATASET_META["metadata"],
        tags=_SAMPLE_DATASET_META["tags"],
        example_count=len(_SAMPLE_EXAMPLES),
        version=1,
        examples=[
            dataset_example_cls(
                input=entry["input"],
                output=entry["output"],
                metadata=entry["metadata"],
                id=entry["id"],
            )
            for entry in _SAMPLE_EXAMPLES
        ],
    )


DatasetExample: Any = None
EvaluationContext: Any = None
EvaluationMetric: Any = None
ExperimentConfig: Any = None
CatCafeExperimentListener: Any = None
CatCafeSyncConfig: Any = None
build_cat_cafe_runner: Any = None


def ensure_dataset(
    client,
    dataset_name: str,
    *,
    sample_dataset,
    dataset_import_cls,
    dataset_example_cls,
):
    """Fetch or create a dataset on CAT Cafe."""
    if dataset := client.fetch_dataset_by_name(dataset_name):
        return dataset

    print(f"Dataset '{dataset_name}' not found. Creating sample dataset.")
    dataset_import = dataset_import_cls(
        name=dataset_name,
        description=sample_dataset.description,
        metadata=sample_dataset.metadata,
        tags=sample_dataset.tags,
        examples=[
            dataset_example_cls(
                input=example.input,
                output=example.output,
                metadata=dict(example.metadata),
                id=example.id,
            )
            for example in sample_dataset.examples
        ],
    )
    client.import_dataset(dataset_import)
    dataset = client.fetch_dataset_by_name(dataset_name)
    if dataset is None:
        raise RuntimeError(f"Failed to create dataset '{dataset_name}'.")
    return dataset


def convert_to_cat_experiments_examples(dataset, dataset_example_cls) -> list[Any]:
    examples: list[Any] = []
    for example in dataset.examples:
        examples.append(
            dataset_example_cls(
                input=dict(example.input or {}),
                output=dict(example.output or {}),
                metadata=dict(example.metadata or {}),
                id=example.id,
            )
        )
    return examples


def test_function(example: Any) -> dict[str, str]:
    """Toy task for demonstration: echo underline text to highlight flows."""
    question = example.input.get("question", "")
    return {"answer": f"(auto) {question}"}


def contains_keyword_evaluator(context: Any) -> Any:
    """Checks that the response mentions 'download' when category expects it."""
    keyword = "download"
    actual_answer = ""
    if isinstance(context.actual_output, dict):
        actual_answer = str(context.actual_output.get("answer", "")).lower()
    elif isinstance(context.actual_output, str):
        actual_answer = context.actual_output.lower()

    score = 1.0 if keyword in actual_answer else 0.0
    return EvaluationMetric(
        name="keyword_download",
        score=score,
        metadata={"keyword": keyword, "found": keyword in actual_answer},
        label="contains keyword" if score else "missing keyword",
        explanation="Ensures responses mention download when required.",
    )


def main() -> None:
    _ensure_src_path()
    (
        CATCafeClient,
        Dataset,
        DatasetImport,
        CatDatasetExample,
    ) = _load_cat_cafe_client()
    global DatasetExample, EvaluationContext, EvaluationMetric, ExperimentConfig, ExperimentRunner
    global CatCafeExperimentListener, CatCafeSyncConfig
    (
        DatasetExample,
        EvaluationContext,
        EvaluationMetric,
        ExperimentConfig,
        CatCafeExperimentListener,
        CatCafeSyncConfig,
        build_cat_cafe_runner,
    ) = _load_cat_experiments()

    sample_dataset = _build_sample_dataset(Dataset, CatDatasetExample)

    base_url = os.getenv("CAT_BASE_URL", "http://localhost:8000")
    dataset_name = os.getenv("CAT_DATASET", "cat-experiments-support-demo")

    client = CATCafeClient(base_url=base_url)
    dataset = ensure_dataset(
        client,
        dataset_name,
        sample_dataset=sample_dataset,
        dataset_import_cls=DatasetImport,
        dataset_example_cls=CatDatasetExample,
    )
    examples = convert_to_cat_experiments_examples(dataset, DatasetExample)

    if not examples:
        raise RuntimeError("Dataset has no examples; unable to run experiment.")

    config = ExperimentConfig(
        name="cat-experiments CAT Cafe demo",
        description="Pushes cat.experiments runs into CAT Cafe via listener adapter.",
        dataset_id=dataset.id,
        dataset_version_id=str(dataset.version),
        metadata={"example_source": "cat-experiments"},
    )

    runner = build_cat_cafe_runner(
        client=cast(Any, client),
        base_url=base_url,
    )

    summary = runner.run(
        dataset=examples,
        task=test_function,
        evaluators=[contains_keyword_evaluator],
        config=config,
    )

    print("Experiment complete")
    print(f"  Total examples: {summary.total_examples}")
    print(f"  Successful examples: {summary.successful_examples}")
    print(f"  Average scores: {summary.average_scores}")


if __name__ == "__main__":
    main()
