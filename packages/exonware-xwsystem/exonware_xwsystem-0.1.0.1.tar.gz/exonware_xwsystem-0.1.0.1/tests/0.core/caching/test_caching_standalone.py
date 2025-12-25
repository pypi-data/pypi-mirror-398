"""
#exonware/xwsystem/tests/0.core/caching/test_caching_standalone.py

Standalone core tests for caching - tests cache logic directly.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.388
Generation Date: 01-Nov-2025
"""

import pytest
import sys
from pathlib import Path

# Ensure src is in path for normal imports
src_path = Path(__file__).parent.parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_caching
class TestCachingStandalone:
    """Standalone caching tests."""
    
    def test_lru_basic_operations(self):
        """Test LRU cache basic put/get operations."""
        from exonware.xwsystem.caching.lru_cache import LRUCache
        
        cache = LRUCache(capacity=10)
        cache.put('key1', 'value1')
        result = cache.get('key1')
        
        assert result == 'value1'
        assert cache.size() == 1

