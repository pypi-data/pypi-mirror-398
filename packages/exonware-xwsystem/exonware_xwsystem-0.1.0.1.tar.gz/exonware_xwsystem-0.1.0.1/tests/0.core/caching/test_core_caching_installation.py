#!/usr/bin/env python3
"""
Core caching installation verification tests.
"""

import pytest


@pytest.mark.xwsystem_core
def test_caching_modules_import():
    """Verify caching submodules can be imported."""
    from exonware.xwsystem.caching.lru_cache import LRUCache  # noqa: F401
    from exonware.xwsystem.caching.lfu_cache import LFUCache  # noqa: F401
    from exonware.xwsystem.caching.ttl_cache import TTLCache  # noqa: F401


@pytest.mark.xwsystem_core
def test_lru_cache_basic_operations():
    """Ensure LRUCache basic put/get functionality works."""
    from exonware.xwsystem.caching.lru_cache import LRUCache

    cache = LRUCache(capacity=10)
    cache.put("test_key", "test_value")

    assert cache.get("test_key") == "test_value"


@pytest.mark.xwsystem_core
def test_pytest_dependency_available():
    """Sanity check that pytest dependency is installed."""
    import pytest as imported_pytest  # noqa: F401

    assert imported_pytest is pytest

