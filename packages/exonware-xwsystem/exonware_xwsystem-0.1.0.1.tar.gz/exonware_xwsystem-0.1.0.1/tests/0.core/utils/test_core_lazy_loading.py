#!/usr/bin/env python3
"""
Core tests for lazy-loading infrastructure.
"""

import sys

import pytest

# xwlazy has been removed from the codebase, so these imports are no longer available
# The test file is skipped via pytestmark below
try:
    from exonware.xwsystem import JsonSerializer
except ImportError:
    JsonSerializer = None  # Fallback if not available
# from xwlazy.lazy import DeferredImportError

# Skip all tests in this file - xwlazy has been removed
pytestmark = pytest.mark.skip(reason="xwlazy has been removed from the codebase")


def test_stage1_import_without_dependencies():
    """Stage 1: importing xwsystem modules should succeed."""
    import exonware.xwsystem as xwsystem  # noqa: F401
    from exonware.xwsystem import serialization  # noqa: F401
    from exonware.xwsystem import AvroSerializer, ProtobufSerializer, CapnProtoSerializer  # noqa: F401


def test_import_hook_installation(monkeypatch):
    """Lazy import hook should install and register itself."""
    package_name = "xwsystem"

    original_meta_path = list(sys.meta_path)
    monkeypatch.setattr(sys, "meta_path", original_meta_path[:], raising=False)

    install_import_hook(package_name)
    assert is_import_hook_installed(package_name)

    assert any("Lazy" in finder.__class__.__name__ for finder in sys.meta_path)


def test_lazy_install_stats_accessible():
    """Stats API should return structured information."""
    enable_lazy_install("xwsystem")

    stats = get_lazy_install_stats("xwsystem")
    assert isinstance(stats, dict)
    assert "total_attempts" in stats

    all_stats = get_all_lazy_install_stats()
    assert "xwsystem" in all_stats


def test_deferred_import_error_repr():
    """DeferredImportError carries context for missing packages."""
    original = ImportError("fastavro not found")
    deferred = DeferredImportError("fastavro", original, "xwsystem")

    assert "fastavro" in repr(deferred)
    assert deferred._real_module is None  # type: ignore[attr-defined]


def test_available_serializers_listing():
    """Available serializer listing should include counts."""
    formats = list_available_formats()

    assert "total_count" in formats
    assert isinstance(formats["all"], list)
    assert isinstance(formats["missing"], list)


def test_json_serializer_roundtrip():
    """JsonSerializer should work without optional dependencies."""
    serializer = JsonSerializer()

    payload = {"test": "data", "number": 42, "nested": {"key": "value"}}
    json_str = serializer.dumps(payload)
    result = serializer.loads(json_str)

    assert result == payload

