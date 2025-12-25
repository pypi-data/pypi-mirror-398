"""Wilson confidence interval aggregate evaluator for binomial accuracy.

Intended use:
- Per-example evaluator produces 0/1 scores (binomial accuracy) under the given metric name.
- Experiment runner uses a constant repetition count per example, so pooling across repetitions
  is valid. The returned score is the pooled accuracy (equivalent to the mean of per-example
  accuracies when reps are constant).
- CI is a Wilson interval on pooled successes/trials; it is bounded and behaves well near 0/1.

Limitations:
- Not appropriate for continuous or non-binomial metrics.
- If repetitions per example vary, pooling biases toward examples with more reps; use a
  per-item-mean approach or bootstrap in that case.
- CI is a pointwise interval; it is not a test of difference vs a baseline.
"""

from __future__ import annotations

from statistics import NormalDist
from typing import Callable

from .models import AggregateEvaluationContext, EvaluationMetric

AggregateFn = Callable[[AggregateEvaluationContext], EvaluationMetric]


def make_wilson_ci_aggregate(
    metric: str = "accuracy",
    *,
    conf: float = 0.95,
) -> AggregateFn:
    """Build an aggregate evaluator that reports Wilson CI on pooled 0/1 scores."""
    if not (0.0 < conf < 1.0):
        raise ValueError("conf must be between 0 and 1")
    z = NormalDist().inv_cdf((1 + conf) / 2.0)

    def agg(ctx: AggregateEvaluationContext) -> EvaluationMetric:
        successes, trials, examples = _count_successes(ctx, metric)
        if trials == 0:
            return _empty_metric(metric, "no data")
        p_hat = successes / trials
        center, half = _wilson_interval(successes, trials, z)
        ci = {"low": center - half, "high": center + half, "half_width": half}
        return EvaluationMetric(
            name=metric,
            score=p_hat,
            metadata={
                "ci": ci,
                "method": "wilson",
                "conf": conf,
                "n_examples": examples,
                "total_trials": trials,
            },
        )

    agg.__name__ = f"{metric}_ci_wilson"
    return agg


# --- helpers ---


def _count_successes(ctx: AggregateEvaluationContext, metric: str) -> tuple[int, int, int]:
    successes = 0
    trials = 0
    seen_examples: set[str] = set()
    for r in ctx.results:
        if getattr(r, "error", None):
            continue
        if metric not in r.evaluation_scores:
            continue
        score = float(r.evaluation_scores[metric])
        # Treat >0.5 as success to allow slight float noise; expect 0/1.
        successes += 1 if score >= 0.5 else 0
        trials += 1
        seen_examples.add(r.example_id)
    return successes, trials, len(seen_examples)


def _wilson_interval(successes: int, trials: int, z: float) -> tuple[float, float]:
    p = successes / trials
    denom = 1 + z * z / trials
    center = (p + z * z / (2 * trials)) / denom
    margin = z * ((p * (1 - p) / trials) + (z * z) / (4 * trials * trials)) ** 0.5 / denom
    return center, margin


def _empty_metric(metric: str, reason: str) -> EvaluationMetric:
    return EvaluationMetric(
        name=metric,
        score=0.0,
        metadata={
            "warning": reason,
            "ci": {"low": 0.0, "high": 0.0, "half_width": 0.0},
            "n_examples": 0,
        },
    )
