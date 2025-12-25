from __future__ import annotations

import sys
import types
from typing import Any, cast

import pytest

from cat.experiments.adapters import LocalStorageExperimentListener
from cat.experiments.runner_builders import (
    build_cat_cafe_runner,
    build_local_runner,
    build_phoenix_runner,
)


class _StubCatCafeClient:
    def __init__(self) -> None:
        self.started = False

    def start_experiment(self, experiment):
        self.started = True
        return "exp-123"

    def submit_results(self, experiment_id, results):
        pass

    def complete_experiment(self, experiment_id, summary):
        pass


@pytest.fixture()
def phoenix_client_stub(monkeypatch):
    class _StubHTTPClient:
        def post(self, *args, **kwargs):
            raise RuntimeError("HTTP client should not be used in builder tests.")

    class _StubPhoenixClient:
        def __init__(self):
            self._client = _StubHTTPClient()

    phoenix_module = types.ModuleType("phoenix")
    phoenix_client_module = types.ModuleType("phoenix.client")
    cast(Any, phoenix_client_module).Client = _StubPhoenixClient
    cast(Any, phoenix_module).client = phoenix_client_module

    monkeypatch.setitem(sys.modules, "phoenix", phoenix_module)
    monkeypatch.setitem(sys.modules, "phoenix.client", phoenix_client_module)

    return _StubPhoenixClient


def test_build_local_runner_adds_cache_listener(tmp_path):
    runner = build_local_runner(storage_dir=tmp_path)

    assert any(
        isinstance(listener, LocalStorageExperimentListener) for listener in runner.listeners
    )


def test_build_cat_cafe_runner_wires_listener():
    from cat.experiments.adapters.cat_cafe import CatCafeExperimentListener

    runner = build_cat_cafe_runner(client=_StubCatCafeClient())

    assert any(isinstance(listener, CatCafeExperimentListener) for listener in runner.listeners)
    assert any(
        isinstance(listener, LocalStorageExperimentListener) for listener in runner.listeners
    )


def test_build_phoenix_runner_wires_listener(phoenix_client_stub):
    from cat.experiments.adapters.phoenix import PhoenixExperimentListener

    runner = build_phoenix_runner(client=phoenix_client_stub())

    assert any(isinstance(listener, PhoenixExperimentListener) for listener in runner.listeners)
    assert any(
        isinstance(listener, LocalStorageExperimentListener) for listener in runner.listeners
    )
