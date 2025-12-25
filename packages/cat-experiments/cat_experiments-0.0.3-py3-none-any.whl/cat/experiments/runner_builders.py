"""Factory helpers for pre-configured experiment runners.

Moved in favor of adapter-local builders; this module now delegates to the adapter modules.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .experiments import ExperimentRunner
from .listeners import ExperimentListener


def build_local_runner(
    *,
    storage_dir: str | Path | None = None,
    clean_on_success: bool = False,
    listeners: Iterable[ExperimentListener] | None = None,
    enable_logging: bool = False,
) -> ExperimentRunner:
    from .adapters.local_storage import build_local_runner as _build_local_runner

    return _build_local_runner(
        storage_dir=storage_dir,
        clean_on_success=clean_on_success,
        listeners=listeners,
        enable_logging=enable_logging,
    )


def build_local_runner_async(
    *,
    storage_dir: str | Path | None = None,
    clean_on_success: bool = False,
    listeners: Iterable[ExperimentListener] | None = None,
    enable_logging: bool = False,
):
    from .adapters.local_storage import build_local_runner_async as _build_local_runner_async

    return _build_local_runner_async(
        storage_dir=storage_dir,
        clean_on_success=clean_on_success,
        listeners=listeners,
        enable_logging=enable_logging,
    )


def build_cat_cafe_runner(
    *,
    client=None,
    base_url: str | None = None,
    storage_dir: str | Path | None = None,
    clean_on_success: bool = False,
    listeners: Iterable[ExperimentListener] | None = None,
    enable_logging: bool = False,
) -> ExperimentRunner:
    from .adapters.cat_cafe_evaluator import build_cat_cafe_runner as _build_cat_cafe_runner

    return _build_cat_cafe_runner(
        client=client,
        base_url=base_url,
        storage_dir=storage_dir,
        clean_on_success=clean_on_success,
        listeners=listeners,
        enable_logging=enable_logging,
    )


def build_cat_cafe_runner_async(
    *,
    client=None,
    base_url: str | None = None,
    storage_dir: str | Path | None = None,
    clean_on_success: bool = False,
    listeners: Iterable[ExperimentListener] | None = None,
    enable_logging: bool = False,
):
    from .adapters.cat_cafe_evaluator import (
        build_cat_cafe_runner_async as _build_cat_cafe_runner_async,
    )

    return _build_cat_cafe_runner_async(
        client=client,
        base_url=base_url,
        storage_dir=storage_dir,
        clean_on_success=clean_on_success,
        listeners=listeners,
        enable_logging=enable_logging,
    )


def build_phoenix_runner(
    *,
    client=None,
    base_url: str | None = None,
    project_name: str | None = None,
    storage_dir: str | Path | None = None,
    clean_on_success: bool = False,
    listeners: Iterable[ExperimentListener] | None = None,
    enable_logging: bool = False,
) -> ExperimentRunner:
    from .adapters.phoenix_evaluator import build_phoenix_runner as _build_phoenix_runner

    return _build_phoenix_runner(
        client=client,
        base_url=base_url,
        project_name=project_name,
        storage_dir=storage_dir,
        clean_on_success=clean_on_success,
        listeners=listeners,
        enable_logging=enable_logging,
    )


def build_phoenix_runner_async(
    *,
    client=None,
    base_url: str | None = None,
    project_name: str | None = None,
    storage_dir: str | Path | None = None,
    clean_on_success: bool = False,
    listeners: Iterable[ExperimentListener] | None = None,
    enable_logging: bool = False,
):
    from .adapters.phoenix_evaluator import (
        build_phoenix_runner_async as _build_phoenix_runner_async,
    )

    return _build_phoenix_runner_async(
        client=client,
        base_url=base_url,
        project_name=project_name,
        storage_dir=storage_dir,
        clean_on_success=clean_on_success,
        listeners=listeners,
        enable_logging=enable_logging,
    )
