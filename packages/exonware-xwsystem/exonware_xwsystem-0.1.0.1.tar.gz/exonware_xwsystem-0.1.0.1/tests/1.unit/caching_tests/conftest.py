#!/usr/bin/env python3
"""
Pytest configuration and fixtures for caching tests.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.388
Generation Date: 01-Nov-2025
"""

import pytest
import sys
from pathlib import Path

# Ensure src is in path
src_path = Path(__file__).parent.parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture
def sample_data():
    """Sample data for cache testing."""
    return {
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'key4': 'value4',
        'key5': 'value5',
    }


@pytest.fixture
def large_dataset():
    """Large dataset for performance testing."""
    return {f"key_{i}": f"value_{i}" for i in range(10000)}


@pytest.fixture
def multilingual_data():
    """Multilingual data for Unicode testing."""
    return {
        "english": "Hello World",
        "chinese": "你好世界",
        "arabic": "مرحبا بالعالم",
        "emoji": "🚀🎉✅❌🔥💯",
        "special": "Special chars: åäö ñ ç ß €",
    }

