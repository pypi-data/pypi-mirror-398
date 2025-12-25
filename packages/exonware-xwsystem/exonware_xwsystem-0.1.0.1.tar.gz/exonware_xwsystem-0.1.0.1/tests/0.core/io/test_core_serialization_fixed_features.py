#!/usr/bin/env python3
"""
Core serialization feature coverage aligning with GUIDE_TEST.md.
"""

from dataclasses import dataclass

import pytest

from exonware.xwsystem.io.serialization.formats.text.json import JsonSerializer
from exonware.xwsystem.io.serialization.formats.text.yaml import YamlSerializer
from exonware.xwsystem.io.serialization.formats.text.toml import TomlSerializer
from exonware.xwsystem.io.serialization.formats.text.xml import XmlSerializer


SERIALIZER_CASES = [
    ("JSON", JsonSerializer),
    ("XML", XmlSerializer),
    ("TOML", TomlSerializer),
    ("YAML", YamlSerializer),
]


TEST_DATA = {
    "users": [
        {"id": 1, "name": "Alice", "age": 30, "active": True},
        {"id": 2, "name": "Bob", "age": 25, "active": False},
    ],
    "metadata": {
        "version": "1.0",
        "created": "2025-01-01T00:00:00Z",
    },
}


@dataclass
class User:
    id: int
    name: str
    age: int
    active: bool


@pytest.mark.parametrize("label, serializer_cls", SERIALIZER_CASES)
def test_basic_round_trip(label, serializer_cls):
    """Ensure core serializers can round-trip structured data."""
    serializer = serializer_cls()
    text_data = serializer.dumps_text(TEST_DATA)
    parsed = serializer.loads_text(text_data)
    assert parsed == TEST_DATA, f"{label} failed round-trip"


@pytest.mark.parametrize("label, serializer_cls", SERIALIZER_CASES)
def test_format_detection(label, serializer_cls):
    """Verify sniff_format identifies serialized payloads."""
    serializer = serializer_cls()
    text_data = serializer.dumps_text(TEST_DATA)
    detected = serializer.sniff_format(text_data)
    assert detected is not None, f"{label} sniff_format returned None"


@pytest.mark.parametrize("label, serializer_cls", SERIALIZER_CASES)
def test_partial_access_operations(label, serializer_cls):
    """Validate partial access helpers (get_at/set_at/iter_path)."""
    serializer = serializer_cls()
    text_data = serializer.dumps_text(TEST_DATA)

    name = serializer.get_at(text_data, "users.0.name")
    assert name == "Alice", f"{label} get_at mismatch"

    updated = serializer.set_at(text_data, "users.0.name", "Alice Updated")
    patched_name = serializer.get_at(updated, "users.0.name")
    assert patched_name == "Alice Updated", f"{label} set_at mismatch"

    path_values = list(serializer.iter_path(text_data, "users.0"))
    assert path_values, f"{label} iter_path yielded no values"


@pytest.mark.parametrize("label, serializer_cls", SERIALIZER_CASES)
def test_patch_application(label, serializer_cls):
    """Confirm JSON-patch style updates apply cleanly."""
    serializer = serializer_cls()
    text_data = serializer.dumps_text(TEST_DATA)

    patch = [{"op": "replace", "path": "users.0.name", "value": "Alice Patched"}]
    patched = serializer.apply_patch(text_data, patch)
    assert serializer.get_at(patched, "users.0.name") == "Alice Patched", f"{label} patch failed"


@pytest.mark.parametrize("label, serializer_cls", SERIALIZER_CASES)
def test_schema_validation(label, serializer_cls):
    """Check simple schema validation helper."""
    serializer = serializer_cls()
    text_data = serializer.dumps_text(TEST_DATA)
    schema = {"users": list, "metadata": dict}
    assert serializer.validate_schema(text_data, schema) is True, f"{label} schema validation failed"


@pytest.mark.parametrize("label, serializer_cls", SERIALIZER_CASES)
def test_canonicalization_and_hashing(label, serializer_cls):
    """Canonical serialization should be stable and hashable."""
    serializer = serializer_cls()
    canonical = serializer.canonicalize(TEST_DATA)
    digest = serializer.hash_stable(TEST_DATA)

    assert canonical
    assert isinstance(canonical, str)
    assert isinstance(digest, str)
    assert len(digest) >= 16, f"{label} hash too short"


@pytest.mark.parametrize("label, serializer_cls", SERIALIZER_CASES)
def test_batch_streaming(label, serializer_cls):
    """Streaming helpers should yield all rows and round-trip."""
    serializer = serializer_cls()
    rows = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]

    chunks = list(serializer.serialize_ndjson(rows))
    assert chunks, f"{label} serialize_ndjson returned no chunks"

    deserialized = list(serializer.deserialize_ndjson(chunks))
    assert deserialized == rows, f"{label} deserialize_ndjson mismatch"

