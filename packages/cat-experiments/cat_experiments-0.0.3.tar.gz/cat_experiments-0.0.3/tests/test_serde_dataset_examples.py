"""Tests for serde helpers related to dataset examples."""

from __future__ import annotations

import os
import sys

# Ensure src is on sys.path for direct test execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cat.experiments.serde import dataset_example_from_dict


def test_dataset_example_from_dict_uses_top_level_fields_when_missing_in_metadata():
    payload = {
        "id": "ex-1",
        "input": {"q": "hi"},
        "output": {"a": "hello"},
        "tags": ["top"],
        "source_trace_id": "trace-1",
        "source_node_id": "node-1",
    }

    example = dataset_example_from_dict(payload)

    assert example.metadata["tags"] == ["top"]
    assert example.metadata["source_trace_id"] == "trace-1"
    assert example.metadata["source_node_id"] == "node-1"
    assert example.tags == ["top"]


def test_dataset_example_from_dict_preserves_metadata_overrides():
    payload = {
        "id": "ex-2",
        "input": {"q": "hi"},
        "output": {"a": "hello"},
        "metadata": {"tags": ["keep"], "source_trace_id": "meta-trace"},
        "tags": ["top"],
        "source_trace_id": "top-trace",
        "source_node_id": "node-2",
    }

    example = dataset_example_from_dict(payload)

    assert example.metadata["tags"] == ["keep"]
    assert example.metadata["source_trace_id"] == "meta-trace"
    assert example.metadata["source_node_id"] == "node-2"
    assert example.tags == ["keep"]
