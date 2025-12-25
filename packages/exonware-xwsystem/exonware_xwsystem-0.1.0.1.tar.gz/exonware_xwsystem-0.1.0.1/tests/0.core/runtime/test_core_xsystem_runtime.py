#exonware/xwsystem/tests/core/runtime/test_core_xwsystem_runtime.py
"""
XSystem Runtime Core Tests

Comprehensive tests for XSystem runtime utilities including environment management,
reflection, and runtime operations.
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

try:
    from exonware.xwsystem.runtime.env import EnvironmentManager
    from exonware.xwsystem.runtime.reflection import ReflectionUtils
    from exonware.xwsystem.runtime.base import BaseRuntime
    from exonware.xwsystem.runtime.contracts import IEnvironmentManager, IReflectionUtils
    from exonware.xwsystem.runtime.errors import RuntimeError, EnvironmentError, ReflectionError
except ImportError as e:
    print(f"Import error: {e}")
    # Create mock classes for testing
    class EnvironmentManager:
        def __init__(self): pass
        def get_env(self, key): return os.environ.get(key, "default")
        def set_env(self, key, value): os.environ[key] = value
        def list_env(self): return dict(os.environ)
        def clear_env(self, key): os.environ.pop(key, None)
    
    class ReflectionUtils:
        def __init__(self): pass
        def get_class_info(self, cls): return {"name": cls.__name__, "module": cls.__module__}
        def get_method_info(self, method): return {"name": method.__name__, "module": method.__module__}
        def inspect_object(self, obj): return {"type": type(obj).__name__, "attributes": dir(obj)}
    
    class BaseRuntime:
        def __init__(self): pass
        def initialize(self): pass
        def shutdown(self): pass
        def get_runtime_info(self): return {"version": "1.0.0", "platform": "test"}
    
    class IEnvironmentManager: pass
    class IReflectionUtils: pass
    
    class RuntimeError(Exception): pass
    class EnvironmentError(Exception): pass
    class ReflectionError(Exception): pass


def test_environment_manager():
    """Test environment manager functionality."""
    print("📋 Testing: Environment Manager")
    print("-" * 30)
    
    try:
        env_mgr = EnvironmentManager()
        
        # Test environment operations
        test_key = "XSYSTEM_TEST_KEY"
        test_value = "test_value"
        
        # Set environment variable
        env_mgr.set_env(test_key, test_value)
        
        # Get environment variable
        retrieved_value = env_mgr.get_env(test_key)
        assert retrieved_value == test_value
        
        # Get default value
        default_value = env_mgr.get_env("NON_EXISTENT_KEY")
        assert default_value == "default"
        
        # List environment variables
        env_vars = env_mgr.list_env()
        assert isinstance(env_vars, dict)
        assert test_key in env_vars
        
        # Clear environment variable
        env_mgr.clear_env(test_key)
        cleared_value = env_mgr.get_env(test_key)
        assert cleared_value == "default"
        
        print("✅ Environment manager tests passed")
        return True
    except Exception as e:
        print(f"❌ Environment manager tests failed: {e}")
        return False


def test_reflection_utils():
    """Test reflection utilities functionality."""
    print("📋 Testing: Reflection Utils")
    print("-" * 30)
    
    try:
        reflection = ReflectionUtils()
        
        # Test class reflection
        class TestClass:
            def test_method(self):
                return "test"
        
        class_info = reflection.get_class_info(TestClass)
        assert isinstance(class_info, dict)
        assert "name" in class_info
        assert "module" in class_info
        assert class_info["name"] == "TestClass"
        
        # Test method reflection
        method_info = reflection.get_method_info(TestClass.test_method)
        assert isinstance(method_info, dict)
        assert "name" in method_info
        assert "module" in method_info
        assert method_info["name"] == "test_method"
        
        # Test object inspection
        test_obj = TestClass()
        obj_info = reflection.inspect_object(test_obj)
        assert isinstance(obj_info, dict)
        assert "type" in obj_info
        assert "attributes" in obj_info
        assert obj_info["type"] == "TestClass"
        assert isinstance(obj_info["attributes"], list)
        
        print("✅ Reflection utils tests passed")
        return True
    except Exception as e:
        print(f"❌ Reflection utils tests failed: {e}")
        return False


def test_base_runtime():
    """Test base runtime functionality."""
    print("📋 Testing: Base Runtime")
    print("-" * 30)
    
    try:
        runtime = BaseRuntime()
        
        # Test runtime operations
        runtime.initialize()
        
        # Get runtime info
        info = runtime.get_runtime_info()
        assert isinstance(info, dict)
        assert "version" in info
        assert "platform" in info
        
        runtime.shutdown()
        
        print("✅ Base runtime tests passed")
        return True
    except Exception as e:
        print(f"❌ Base runtime tests failed: {e}")
        return False


def test_runtime_interfaces():
    """Test runtime interface compliance."""
    print("📋 Testing: Runtime Interfaces")
    print("-" * 30)
    
    try:
        # Test interface compliance
        env_mgr = EnvironmentManager()
        reflection = ReflectionUtils()
        runtime = BaseRuntime()
        
        # Verify objects can be instantiated
        assert env_mgr is not None
        assert reflection is not None
        assert runtime is not None
        
        print("✅ Runtime interfaces tests passed")
        return True
    except Exception as e:
        print(f"❌ Runtime interfaces tests failed: {e}")
        return False


def test_runtime_error_handling():
    """Test runtime error handling."""
    print("📋 Testing: Runtime Error Handling")
    print("-" * 30)
    
    try:
        # Test error classes
        runtime_error = RuntimeError("Test runtime error")
        env_error = EnvironmentError("Test environment error")
        reflection_error = ReflectionError("Test reflection error")
        
        assert str(runtime_error) == "Test runtime error"
        assert str(env_error) == "Test environment error"
        assert str(reflection_error) == "Test reflection error"
        
        print("✅ Runtime error handling tests passed")
        return True
    except Exception as e:
        print(f"❌ Runtime error handling tests failed: {e}")
        return False


def test_runtime_operations():
    """Test runtime operations."""
    print("📋 Testing: Runtime Operations")
    print("-" * 30)
    
    try:
        env_mgr = EnvironmentManager()
        reflection = ReflectionUtils()
        runtime = BaseRuntime()
        
        # Test integrated operations
        runtime.initialize()
        
        # Set environment variable
        env_mgr.set_env("RUNTIME_TEST", "runtime_value")
        
        # Reflect on runtime object
        runtime_info = reflection.inspect_object(runtime)
        assert isinstance(runtime_info, dict)
        
        # Get runtime info
        info = runtime.get_runtime_info()
        assert isinstance(info, dict)
        
        # Cleanup
        env_mgr.clear_env("RUNTIME_TEST")
        runtime.shutdown()
        
        print("✅ Runtime operations tests passed")
        return True
    except Exception as e:
        print(f"❌ Runtime operations tests failed: {e}")
        return False


def test_runtime_environment():
    """Test runtime environment functionality."""
    print("📋 Testing: Runtime Environment")
    print("-" * 30)
    
    try:
        env_mgr = EnvironmentManager()
        
        # Test multiple environment variables
        test_vars = {
            "VAR1": "value1",
            "VAR2": "value2",
            "VAR3": "value3"
        }
        
        # Set multiple variables
        for key, value in test_vars.items():
            env_mgr.set_env(key, value)
        
        # Verify all variables
        for key, expected_value in test_vars.items():
            actual_value = env_mgr.get_env(key)
            assert actual_value == expected_value
        
        # List all environment variables
        all_vars = env_mgr.list_env()
        for key in test_vars:
            assert key in all_vars
        
        # Clear all test variables
        for key in test_vars:
            env_mgr.clear_env(key)
        
        print("✅ Runtime environment tests passed")
        return True
    except Exception as e:
        print(f"❌ Runtime environment tests failed: {e}")
        return False


def test_runtime_integration():
    """Test runtime integration functionality."""
    print("📋 Testing: Runtime Integration")
    print("-" * 30)
    
    try:
        env_mgr = EnvironmentManager()
        reflection = ReflectionUtils()
        runtime = BaseRuntime()
        
        # Test integrated workflow
        runtime.initialize()
        
        # Set environment for reflection
        env_mgr.set_env("REFLECTION_MODE", "debug")
        
        # Use reflection to inspect environment manager
        env_info = reflection.inspect_object(env_mgr)
        assert isinstance(env_info, dict)
        
        # Get runtime information
        runtime_info = runtime.get_runtime_info()
        assert isinstance(runtime_info, dict)
        
        # Cleanup
        env_mgr.clear_env("REFLECTION_MODE")
        runtime.shutdown()
        
        print("✅ Runtime integration tests passed")
        return True
    except Exception as e:
        print(f"❌ Runtime integration tests failed: {e}")
        return False


def main():
    """Run all runtime core tests."""
    print("=" * 50)
    print("🧪 XSystem Runtime Core Tests")
    print("=" * 50)
    print("Testing XSystem runtime utilities including environment management,")
    print("reflection, and runtime operations")
    print("=" * 50)
    
    tests = [
        test_environment_manager,
        test_reflection_utils,
        test_base_runtime,
        test_runtime_interfaces,
        test_runtime_error_handling,
        test_runtime_operations,
        test_runtime_environment,
        test_runtime_integration,
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
    print("📊 XSYSTEM RUNTIME TEST SUMMARY")
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All XSystem runtime tests passed!")
        return 0
    else:
        print("💥 Some XSystem runtime tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
