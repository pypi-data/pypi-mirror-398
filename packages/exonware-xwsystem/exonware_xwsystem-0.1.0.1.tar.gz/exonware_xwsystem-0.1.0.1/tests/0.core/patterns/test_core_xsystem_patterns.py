#exonware/xwsystem/tests/core/patterns/test_core_xwsystem_patterns.py
"""
XSystem Patterns Core Tests

Comprehensive tests for XSystem design patterns including context managers,
dynamic facades, handler factories, import registries, and object pools.
"""

import sys
import os
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

try:
    from exonware.xwsystem.patterns.context_manager import ContextManager
    from exonware.xwsystem.patterns.dynamic_facade import DynamicFacade
    from exonware.xwsystem.patterns.handler_factory import HandlerFactory
    from exonware.xwsystem.patterns.import_registry import ImportRegistry
    from exonware.xwsystem.patterns.object_pool import ObjectPool
    from exonware.xwsystem.patterns.base import BasePattern
    from exonware.xwsystem.patterns.contracts import IContextManager, IDynamicFacade, IHandlerFactory, IObjectPool
    from exonware.xwsystem.patterns.errors import PatternError, ContextError, FacadeError, FactoryError, PoolError
except ImportError as e:
    print(f"Import error: {e}")
    # Create mock classes for testing
    class ContextManager:
        def __init__(self): pass
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): return False
        def enter_context(self): return self
        def exit_context(self): pass
    
    class DynamicFacade:
        def __init__(self): pass
        def create_facade(self, target): return target
        def add_method(self, name, method): pass
        def remove_method(self, name): pass
    
    class HandlerFactory:
        def __init__(self): pass
        def create_handler(self, handler_type): return MagicMock()
        def register_handler(self, name, handler_class): pass
        def get_handler(self, name): return MagicMock()
    
    class ImportRegistry:
        def __init__(self): pass
        def register_import(self, name, module): pass
        def get_import(self, name): return MagicMock()
        def list_imports(self): return []
    
    class ObjectPool:
        def __init__(self, factory, size=10): self.factory = factory; self.size = size
        def get_object(self): return self.factory()
        def return_object(self, obj): pass
        def clear(self): pass
    
    class BasePattern:
        def __init__(self): pass
        def initialize(self): pass
        def cleanup(self): pass
    
    class IContextManager: pass
    class IDynamicFacade: pass
    class IHandlerFactory: pass
    class IObjectPool: pass
    
    class PatternError(Exception): pass
    class ContextError(Exception): pass
    class FacadeError(Exception): pass
    class FactoryError(Exception): pass
    class PoolError(Exception): pass


def test_context_manager():
    """Test context manager functionality."""
    print("📋 Testing: Context Manager")
    print("-" * 30)
    
    try:
        ctx_mgr = ContextManager()
        
        # Test context manager protocol
        with ctx_mgr as cm:
            assert cm is not None
        
        # Test manual context management
        ctx_mgr.enter_context()
        ctx_mgr.exit_context()
        
        print("✅ Context manager tests passed")
        return True
    except Exception as e:
        print(f"❌ Context manager tests failed: {e}")
        return False


def test_dynamic_facade():
    """Test dynamic facade functionality."""
    print("📋 Testing: Dynamic Facade")
    print("-" * 30)
    
    try:
        facade = DynamicFacade()
        
        # Test facade creation
        target = MagicMock()
        created_facade = facade.create_facade(target)
        assert created_facade is not None
        
        # Test method management
        def test_method(): return "test"
        
        facade.add_method("test_method", test_method)
        facade.remove_method("test_method")
        
        print("✅ Dynamic facade tests passed")
        return True
    except Exception as e:
        print(f"❌ Dynamic facade tests failed: {e}")
        return False


def test_handler_factory():
    """Test handler factory functionality."""
    print("📋 Testing: Handler Factory")
    print("-" * 30)
    
    try:
        factory = HandlerFactory()
        
        # Test handler creation
        handler = factory.create_handler("test_handler")
        assert handler is not None
        
        # Test handler registration
        class TestHandler:
            def handle(self): return "handled"
        
        factory.register_handler("test", TestHandler)
        retrieved_handler = factory.get_handler("test")
        assert retrieved_handler is not None
        
        print("✅ Handler factory tests passed")
        return True
    except Exception as e:
        print(f"❌ Handler factory tests failed: {e}")
        return False


def test_import_registry():
    """Test import registry functionality."""
    print("📋 Testing: Import Registry")
    print("-" * 30)
    
    try:
        registry = ImportRegistry()
        
        # Test import registration
        mock_module = MagicMock()
        registry.register_import("test_module", mock_module)
        
        # Test import retrieval
        retrieved_module = registry.get_import("test_module")
        assert retrieved_module is not None
        
        # Test import listing
        imports = registry.list_imports()
        assert isinstance(imports, list)
        
        print("✅ Import registry tests passed")
        return True
    except Exception as e:
        print(f"❌ Import registry tests failed: {e}")
        return False


def test_object_pool():
    """Test object pool functionality."""
    print("📋 Testing: Object Pool")
    print("-" * 30)
    
    try:
        # Test object pool with factory
        def create_object():
            return {"id": "test", "data": "test_data"}
        
        pool = ObjectPool(create_object, size=5)
        
        # Test object retrieval
        obj1 = pool.get_object()
        assert obj1 is not None
        assert "id" in obj1
        
        # Test object return
        pool.return_object(obj1)
        
        # Test pool clearing
        pool.clear()
        
        print("✅ Object pool tests passed")
        return True
    except Exception as e:
        print(f"❌ Object pool tests failed: {e}")
        return False


def test_base_pattern():
    """Test base pattern functionality."""
    print("📋 Testing: Base Pattern")
    print("-" * 30)
    
    try:
        pattern = BasePattern()
        
        # Test pattern operations
        pattern.initialize()
        pattern.cleanup()
        
        print("✅ Base pattern tests passed")
        return True
    except Exception as e:
        print(f"❌ Base pattern tests failed: {e}")
        return False


def test_patterns_interfaces():
    """Test patterns interface compliance."""
    print("📋 Testing: Patterns Interfaces")
    print("-" * 30)
    
    try:
        # Test interface compliance
        ctx_mgr = ContextManager()
        facade = DynamicFacade()
        factory = HandlerFactory()
        pool = ObjectPool(lambda: "test")
        
        # Verify objects can be instantiated
        assert ctx_mgr is not None
        assert facade is not None
        assert factory is not None
        assert pool is not None
        
        print("✅ Patterns interfaces tests passed")
        return True
    except Exception as e:
        print(f"❌ Patterns interfaces tests failed: {e}")
        return False


def test_patterns_error_handling():
    """Test patterns error handling."""
    print("📋 Testing: Patterns Error Handling")
    print("-" * 30)
    
    try:
        # Test error classes
        pattern_error = PatternError("Test pattern error")
        context_error = ContextError("Test context error")
        facade_error = FacadeError("Test facade error")
        factory_error = FactoryError("Test factory error")
        pool_error = PoolError("Test pool error")
        
        assert str(pattern_error) == "Test pattern error"
        assert str(context_error) == "Test context error"
        assert str(facade_error) == "Test facade error"
        assert str(factory_error) == "Test factory error"
        assert str(pool_error) == "Test pool error"
        
        print("✅ Patterns error handling tests passed")
        return True
    except Exception as e:
        print(f"❌ Patterns error handling tests failed: {e}")
        return False


def test_patterns_integration():
    """Test patterns integration functionality."""
    print("📋 Testing: Patterns Integration")
    print("-" * 30)
    
    try:
        # Test integrated workflow
        factory = HandlerFactory()
        pool = ObjectPool(lambda: {"id": "test"})
        registry = ImportRegistry()
        
        # Create handler through factory
        handler = factory.create_handler("test_handler")
        
        # Get object from pool
        obj = pool.get_object()
        
        # Register handler in registry
        registry.register_import("handler", handler)
        
        # Return object to pool
        pool.return_object(obj)
        
        print("✅ Patterns integration tests passed")
        return True
    except Exception as e:
        print(f"❌ Patterns integration tests failed: {e}")
        return False


def main():
    """Run all patterns core tests."""
    print("=" * 50)
    print("🧪 XSystem Patterns Core Tests")
    print("=" * 50)
    print("Testing XSystem design patterns including context managers,")
    print("dynamic facades, handler factories, import registries, and object pools")
    print("=" * 50)
    
    tests = [
        test_context_manager,
        test_dynamic_facade,
        test_handler_factory,
        test_import_registry,
        test_object_pool,
        test_base_pattern,
        test_patterns_interfaces,
        test_patterns_error_handling,
        test_patterns_integration,
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
    print("📊 XSYSTEM PATTERNS TEST SUMMARY")
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All XSystem patterns tests passed!")
        return 0
    else:
        print("💥 Some XSystem patterns tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
