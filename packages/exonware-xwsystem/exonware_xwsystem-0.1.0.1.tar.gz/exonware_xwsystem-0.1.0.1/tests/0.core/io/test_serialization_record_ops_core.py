#!/usr/bin/env python3
"""
Core tests for record-level serialization APIs across common formats.

Covers:
- JSON       (JsonSerializer)
- JSON5      (Json5Serializer)
- JSONL      (JsonLinesSerializer)
- YAML       (YamlSerializer)
- TOML       (TomlSerializer)
- XML        (XmlSerializer)
- BSON       (BsonSerializer)
- MsgPack    (MsgPackSerializer)

For each format we verify:
- get_record_page: basic paging semantics
- get_record_by_id: ID lookup
- stream_read_record: first-match semantics
- stream_update_record: in-place update and persistence to disk

These tests intentionally exercise only small files (a handful of records),
focusing on correctness of behaviour and delegation rather than performance.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pytest

from exonware.xwsystem.io.serialization.formats.text.json import JsonSerializer
from exonware.xwsystem.io.serialization.formats.text.json5 import Json5Serializer
from exonware.xwsystem.io.serialization.formats.text.jsonlines import JsonLinesSerializer
from exonware.xwsystem.io.serialization.formats.text.yaml import YamlSerializer
from exonware.xwsystem.io.serialization.formats.text.toml import TomlSerializer
from exonware.xwsystem.io.serialization.formats.text.xml import XmlSerializer
from exonware.xwsystem.io.serialization.formats.binary.bson import BsonSerializer
from exonware.xwsystem.io.serialization.formats.binary.msgpack import MsgPackSerializer


RECORDS: list[dict[str, Any]] = [
    {"id": 1, "name": "Alice", "age": 30},
    {"id": 2, "name": "Bob", "age": 40},
    {"id": 3, "name": "Carol", "age": 50},
    {"id": 4, "name": "Dave", "age": 60},
    {"id": 5, "name": "Eve", "age": 70},
]


SerializerType = type


FORMAT_CASES: list[tuple[str, SerializerType]] = [
    ("JSON", JsonSerializer),
    ("JSON5", Json5Serializer),
    ("JSONL", JsonLinesSerializer),
    ("YAML", YamlSerializer),
    ("TOML", TomlSerializer),
    ("XML", XmlSerializer),
    ("BSON", BsonSerializer),
    ("MsgPack", MsgPackSerializer),
]


def _write_records(
    serializer_cls: SerializerType,
    path: Path,
    records: list[dict[str, Any]],
) -> None:
    """
    Helper: instantiate serializer_cls and save records to path.

    We rely on save_file/load_file so that each format uses its own natural
    representation (e.g. JSONL vs JSON vs binary).
    """
    serializer = serializer_cls()
    serializer.save_file(records, path)


@pytest.mark.xwsystem_core
@pytest.mark.parametrize("label, serializer_cls", FORMAT_CASES)
def test_get_record_page_basic(label: str, serializer_cls: SerializerType, tmp_path: Path) -> None:
    """
    get_record_page should return the correct logical slice for all formats.

    We request page_number=2, page_size=2 over 5 records → records[2:4].
    For non-list top-level representations, ASerialization falls back to
    single-record-first-page semantics, but all of these serializers treat
    a top-level list naturally.
    """
    file_path = tmp_path / f"records_{label.lower()}"
    _write_records(serializer_cls, file_path, RECORDS)

    serializer = serializer_cls()
    page = serializer.get_record_page(file_path, page_number=2, page_size=2)

    assert isinstance(page, list), f"{label}: page should be a list"
    assert len(page) == 2, f"{label}: expected 2 records on page"
    # IDs 3 and 4
    ids = [r["id"] for r in page]
    assert ids == [3, 4], f"{label}: unexpected page records {ids}"


@pytest.mark.xwsystem_core
@pytest.mark.parametrize("label, serializer_cls", FORMAT_CASES)
def test_get_record_by_id_basic(label: str, serializer_cls: SerializerType, tmp_path: Path) -> None:
    """get_record_by_id should find the correct record by id_field across formats."""
    file_path = tmp_path / f"records_{label.lower()}"
    _write_records(serializer_cls, file_path, RECORDS)

    serializer = serializer_cls()
    record = serializer.get_record_by_id(file_path, id_value=4, id_field="id")

    assert isinstance(record, dict), f"{label}: record should be a dict"
    assert record["name"] == "Dave"
    assert record["age"] == 60


@pytest.mark.xwsystem_core
@pytest.mark.parametrize("label, serializer_cls", FORMAT_CASES)
def test_stream_read_record_first_match(label: str, serializer_cls: SerializerType, tmp_path: Path) -> None:
    """
    stream_read_record should return the first matching record.

    For JSONL, this is line-by-line streaming; for other formats the base
    implementation may load the full file, but semantics are the same.
    """
    file_path = tmp_path / f"records_{label.lower()}"
    _write_records(serializer_cls, file_path, RECORDS)

    serializer = serializer_cls()

    def match(record: Any) -> bool:
        return isinstance(record, dict) and record.get("age") >= 50

    record = serializer.stream_read_record(file_path, match=match)

    assert record["id"] == 3
    assert record["name"] == "Carol"


@pytest.mark.xwsystem_core
@pytest.mark.parametrize("label, serializer_cls", FORMAT_CASES)
def test_stream_update_record_persists_changes(label: str, serializer_cls: SerializerType, tmp_path: Path) -> None:
    """
    stream_update_record should apply updater() to matching records and persist.

    We increment age by 1 for id >= 4 and ensure the file content reflects
    the updated values when reloaded via load_file().
    """
    file_path = tmp_path / f"records_{label.lower()}"
    _write_records(serializer_cls, file_path, RECORDS)

    serializer = serializer_cls()

    def match(record: Any) -> bool:
        return isinstance(record, dict) and record.get("id", 0) >= 4

    def updater(record: Any) -> Any:
        record = dict(record)
        record["age"] = record.get("age", 0) + 1
        return record

    updated_count = serializer.stream_update_record(file_path, match=match, updater=updater)
    assert updated_count == 2, f"{label}: expected 2 records to be updated"

    # Reload and verify effects
    data = serializer.load_file(file_path)
    assert isinstance(data, list), f"{label}: expected list after reload"

    ages_by_id = {r["id"]: r["age"] for r in data}
    # IDs < 4 unchanged
    assert ages_by_id[1] == 30
    assert ages_by_id[2] == 40
    assert ages_by_id[3] == 50
    # IDs >= 4 incremented
    assert ages_by_id[4] == 61
    assert ages_by_id[5] == 71


