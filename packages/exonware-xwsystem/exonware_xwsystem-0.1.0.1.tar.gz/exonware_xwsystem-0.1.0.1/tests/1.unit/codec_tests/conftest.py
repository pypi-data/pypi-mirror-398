"""
#exonware/xwsystem/tests/1.unit/codec_tests/conftest.py

Fixtures for codec tests.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 04-Nov-2025
"""

import pytest
from pathlib import Path
import sys

# Ensure src is in path
src_path = Path(__file__).parent.parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture
def fresh_registry():
    """Create fresh registry for isolated tests."""
    from exonware.xwsystem.io.codec.registry import UniversalCodecRegistry
    return UniversalCodecRegistry()


@pytest.fixture
def populated_registry():
    """Create registry with common codecs registered."""
    from exonware.xwsystem.io.codec.registry import UniversalCodecRegistry
    from exonware.xwsystem.io.serialization.formats.text.json import JsonSerializer
    from exonware.xwsystem.io.serialization.formats.text.yaml import YamlSerializer
    from exonware.xwsystem.io.serialization.formats.text.xml import XmlSerializer
    from exonware.xwsystem.io.serialization.formats.text.toml import TomlSerializer
    
    registry = UniversalCodecRegistry()
    registry.register(JsonSerializer)
    registry.register(YamlSerializer)
    registry.register(XmlSerializer)
    registry.register(TomlSerializer)
    
    return registry


@pytest.fixture
def test_data():
    """Simple test data."""
    return {"name": "Alice", "age": 30, "active": True}


@pytest.fixture
def complex_test_data():
    """Complex nested test data."""
    return {
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"}
        ],
        "config": {
            "debug": True,
            "timeout": 30
        }
    }

