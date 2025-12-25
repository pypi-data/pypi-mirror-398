"""
#exonware/xwsystem/tests/0.core/caching/conftest.py

Core test fixtures for caching module - minimal, fast fixtures.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.388
Generation Date: 01-Nov-2025
"""

import pytest


@pytest.fixture
def basic_cache_config():
    """Basic cache configuration for core tests."""
    return {
        'capacity': 128,
        'ttl': 300.0
    }

