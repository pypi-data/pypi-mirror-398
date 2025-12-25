"""
Cat Cafe adapter package that mirrors cat.experiments runs into CAT Cafe.

Import this subpackage explicitly to access integrations that depend on the optional
cat-cafe-client dependency.
"""

from ..cat_cafe_evaluator import (
    CatCafeEvaluationCoordinator,
    CatCafeEvaluationPlan,
    build_cat_cafe_runner,
    build_cat_cafe_runner_async,
)
from ..cat_cafe_listener import (
    CatCafeExperimentListener,
    CatCafeExperimentResult,
    CatCafeSyncConfig,
    convert_result_to_cat_cafe,
)

__all__ = [
    "CatCafeEvaluationCoordinator",
    "CatCafeEvaluationPlan",
    "CatCafeExperimentListener",
    "CatCafeExperimentResult",
    "CatCafeSyncConfig",
    "build_cat_cafe_runner",
    "build_cat_cafe_runner_async",
    "convert_result_to_cat_cafe",
]
