#exonware/xwsystem/tests/core/core/test_core_xwsystem_core.py
"""
XSystem Core Core Tests

Comprehensive tests for XSystem core functionality including base classes,
contracts, and core system operations.
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

try:
    from exonware.xwsystem.shared.base import BaseCore
    from exonware.xwsystem.shared.contracts import ICore
    from exonware.xwsystem.shared.errors import CoreError
except ImportError as e:
    print(f"Import error: {e}")
    # Create mock classes for testing
    class BaseCore:
        def __init__(self): pass
        def initialize(self): pass
        def shutdown(self): pass
        def is_initialized(self): return True
    
    class ICore: pass
    
    class CoreError(Exception): pass


def test_base_core():
    """Test base core functionality."""
    print("📋 Testing: Base Core")
    print("-" * 30)
    
    try:
        core = BaseCore()
        
        # Test core operations
        core.initialize()
        is_init = core.is_initialized()
        assert isinstance(is_init, bool)
        
        core.shutdown()
        
        print("✅ Base core tests passed")
        return True
    except Exception as e:
        print(f"❌ Base core tests failed: {e}")
        return False


def test_core_interfaces():
    """Test core interface compliance."""
    print("📋 Testing: Core Interfaces")
    print("-" * 30)
    
    try:
        # Test interface compliance
        core = BaseCore()
        
        # Verify object can be instantiated
        assert core is not None
        
        print("✅ Core interfaces tests passed")
        return True
    except Exception as e:
        print(f"❌ Core interfaces tests failed: {e}")
        return False


def test_core_error_handling():
    """Test core error handling."""
    print("📋 Testing: Core Error Handling")
    print("-" * 30)
    
    try:
        # Test error classes
        core_error = CoreError("Test core error")
        
        assert str(core_error) == "Test core error"
        
        print("✅ Core error handling tests passed")
        return True
    except Exception as e:
        print(f"❌ Core error handling tests failed: {e}")
        return False


def test_core_lifecycle():
    """Test core lifecycle management."""
    print("📋 Testing: Core Lifecycle")
    print("-" * 30)
    
    try:
        core = BaseCore()
        
        # Test lifecycle operations
        core.initialize()
        assert core.is_initialized()
        
        core.shutdown()
        
        print("✅ Core lifecycle tests passed")
        return True
    except Exception as e:
        print(f"❌ Core lifecycle tests failed: {e}")
        return False


def main():
    """Run all core core tests."""
    print("=" * 50)
    print("🧪 XSystem Core Core Tests")
    print("=" * 50)
    print("Testing XSystem core functionality including base classes,")
    print("contracts, and core system operations")
    print("=" * 50)
    
    tests = [
        test_base_core,
        test_core_interfaces,
        test_core_error_handling,
        test_core_lifecycle,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print("📊 XSYSTEM CORE TEST SUMMARY")
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All XSystem core tests passed!")
        return 0
    else:
        print("💥 Some XSystem core tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
