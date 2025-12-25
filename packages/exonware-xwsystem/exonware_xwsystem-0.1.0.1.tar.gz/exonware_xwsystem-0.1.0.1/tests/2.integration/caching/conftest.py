"""
#exonware/xwsystem/tests/2.integration/caching/conftest.py

Integration test fixtures for caching tests.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.388
Generation Date: 01-Nov-2025
"""

import pytest


@pytest.fixture
def integration_cache_data():
    """Large dataset for integration testing."""
    return {f'key_{i}': {'id': i, 'data': f'value_{i}' * 10} for i in range(500)}

