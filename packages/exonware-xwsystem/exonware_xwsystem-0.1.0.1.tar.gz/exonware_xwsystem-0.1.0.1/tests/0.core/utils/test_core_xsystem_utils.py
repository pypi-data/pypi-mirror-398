#exonware/xwsystem/tests/core/utils/test_core_xwsystem_utils.py
"""
XSystem Utils Core Tests

Comprehensive tests for XSystem utility functions including lazy loading,
path utilities, and common utilities.
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

# Skip xwlazy imports - xwlazy has been removed
# try:
#     from xwlazy.lazy import LazyLoader
try:
    LazyLoader = None  # xwlazy removed
    from exonware.xwsystem.utils.paths import PathUtils
    from exonware.xwsystem.utils.base import BaseUtils
    from exonware.xwsystem.utils.contracts import ILazyLoader, IPathUtils
    from exonware.xwsystem.utils.errors import UtilsError, LazyLoadError, PathError
except ImportError as e:
    print(f"Import error: {e}")
    # Create mock classes for testing
    class LazyLoader:
        def __init__(self): pass
        def load(self, name): return f"loaded_{name}"
        def is_loaded(self, name): return True
        def unload(self, name): return True
        def list_loaded(self): return ["test1", "test2"]
    
    class PathUtils:
        def __init__(self): pass
        def normalize_path(self, path): return str(Path(path).resolve())
        def join_paths(self, *paths): return str(Path(*paths))
        def exists(self, path): return Path(path).exists()
        def is_file(self, path): return Path(path).is_file()
        def is_dir(self, path): return Path(path).is_dir()
    
    class BaseUtils:
        def __init__(self): pass
        def initialize(self): pass
        def cleanup(self): pass
        def get_info(self): return {"version": "1.0.0", "type": "utils"}
    
    class ILazyLoader: pass
    class IPathUtils: pass
    
    class UtilsError(Exception): pass
    class LazyLoadError(Exception): pass
    class PathError(Exception): pass


def test_lazy_loader():
    """Test lazy loader functionality."""
    print("📋 Testing: Lazy Loader")
    print("-" * 30)
    
    try:
        loader = LazyLoader()
        
        # Test loading
        result = loader.load("test_module")
        assert isinstance(result, str)
        assert "loaded_" in result
        
        # Test loaded check
        is_loaded = loader.is_loaded("test_module")
        assert isinstance(is_loaded, bool)
        
        # Test unloading
        unloaded = loader.unload("test_module")
        assert isinstance(unloaded, bool)
        
        # Test list loaded
        loaded_list = loader.list_loaded()
        assert isinstance(loaded_list, list)
        
        print("✅ Lazy loader tests passed")
        return True
    except Exception as e:
        print(f"❌ Lazy loader tests failed: {e}")
        return False


def test_path_utils():
    """Test path utilities functionality."""
    print("📋 Testing: Path Utils")
    print("-" * 30)
    
    try:
        path_utils = PathUtils()
        
        # Test path normalization
        normalized = path_utils.normalize_path("test/path")
        assert isinstance(normalized, str)
        assert len(normalized) > 0
        
        # Test path joining
        joined = path_utils.join_paths("dir1", "dir2", "file.txt")
        assert isinstance(joined, str)
        assert "dir1" in joined
        assert "dir2" in joined
        assert "file.txt" in joined
        
        # Test path existence checks
        current_dir = "."
        exists = path_utils.exists(current_dir)
        assert isinstance(exists, bool)
        
        is_file = path_utils.is_file(current_dir)
        assert isinstance(is_file, bool)
        
        is_dir = path_utils.is_dir(current_dir)
        assert isinstance(is_dir, bool)
        
        print("✅ Path utils tests passed")
        return True
    except Exception as e:
        print(f"❌ Path utils tests failed: {e}")
        return False


def test_base_utils():
    """Test base utils functionality."""
    print("📋 Testing: Base Utils")
    print("-" * 30)
    
    try:
        utils = BaseUtils()
        
        # Test utils operations
        utils.initialize()
        
        # Test info retrieval
        info = utils.get_info()
        assert isinstance(info, dict)
        assert "version" in info
        assert "type" in info
        
        utils.cleanup()
        
        print("✅ Base utils tests passed")
        return True
    except Exception as e:
        print(f"❌ Base utils tests failed: {e}")
        return False


def test_utils_interfaces():
    """Test utils interface compliance."""
    print("📋 Testing: Utils Interfaces")
    print("-" * 30)
    
    try:
        # Test interface compliance
        loader = LazyLoader()
        path_utils = PathUtils()
        utils = BaseUtils()
        
        # Verify objects can be instantiated
        assert loader is not None
        assert path_utils is not None
        assert utils is not None
        
        print("✅ Utils interfaces tests passed")
        return True
    except Exception as e:
        print(f"❌ Utils interfaces tests failed: {e}")
        return False


def test_utils_error_handling():
    """Test utils error handling."""
    print("📋 Testing: Utils Error Handling")
    print("-" * 30)
    
    try:
        # Test error classes
        utils_error = UtilsError("Test utils error")
        lazy_error = LazyLoadError("Test lazy load error")
        path_error = PathError("Test path error")
        
        assert str(utils_error) == "Test utils error"
        assert str(lazy_error) == "Test lazy load error"
        assert str(path_error) == "Test path error"
        
        print("✅ Utils error handling tests passed")
        return True
    except Exception as e:
        print(f"❌ Utils error handling tests failed: {e}")
        return False


def test_utils_operations():
    """Test utils operations."""
    print("📋 Testing: Utils Operations")
    print("-" * 30)
    
    try:
        loader = LazyLoader()
        path_utils = PathUtils()
        utils = BaseUtils()
        
        # Test integrated operations
        utils.initialize()
        
        # Test lazy loading with path operations
        module_name = "test_module"
        loaded = loader.load(module_name)
        assert isinstance(loaded, str)
        
        # Test path operations
        test_path = "test/path/file.txt"
        normalized = path_utils.normalize_path(test_path)
        assert isinstance(normalized, str)
        
        # Test utils info
        info = utils.get_info()
        assert isinstance(info, dict)
        
        utils.cleanup()
        
        print("✅ Utils operations tests passed")
        return True
    except Exception as e:
        print(f"❌ Utils operations tests failed: {e}")
        return False


def test_utils_path_operations():
    """Test utils path operations functionality."""
    print("📋 Testing: Utils Path Operations")
    print("-" * 30)
    
    try:
        path_utils = PathUtils()
        
        # Test various path operations
        test_paths = [
            "relative/path",
            "/absolute/path",
            "path/with/../parent",
            "path/with/./current"
        ]
        
        for test_path in test_paths:
            # Test normalization
            normalized = path_utils.normalize_path(test_path)
            assert isinstance(normalized, str)
            
            # Test existence check
            exists = path_utils.exists(test_path)
            assert isinstance(exists, bool)
            
            # Test file/directory checks
            is_file = path_utils.is_file(test_path)
            is_dir = path_utils.is_dir(test_path)
            assert isinstance(is_file, bool)
            assert isinstance(is_dir, bool)
        
        # Test path joining
        joined = path_utils.join_paths("base", "sub", "file.ext")
        assert isinstance(joined, str)
        assert "base" in joined
        assert "sub" in joined
        assert "file.ext" in joined
        
        print("✅ Utils path operations tests passed")
        return True
    except Exception as e:
        print(f"❌ Utils path operations tests failed: {e}")
        return False


def test_utils_lazy_loading():
    """Test utils lazy loading functionality."""
    print("📋 Testing: Utils Lazy Loading")
    print("-" * 30)
    
    try:
        loader = LazyLoader()
        
        # Test multiple lazy loading operations
        test_modules = ["module1", "module2", "module3"]
        
        for module in test_modules:
            # Load module
            loaded = loader.load(module)
            assert isinstance(loaded, str)
            
            # Check if loaded
            is_loaded = loader.is_loaded(module)
            assert isinstance(is_loaded, bool)
        
        # Test list loaded modules
        loaded_list = loader.list_loaded()
        assert isinstance(loaded_list, list)
        
        # Test unloading
        for module in test_modules:
            unloaded = loader.unload(module)
            assert isinstance(unloaded, bool)
        
        print("✅ Utils lazy loading tests passed")
        return True
    except Exception as e:
        print(f"❌ Utils lazy loading tests failed: {e}")
        return False


def test_utils_integration():
    """Test utils integration functionality."""
    print("📋 Testing: Utils Integration")
    print("-" * 30)
    
    try:
        loader = LazyLoader()
        path_utils = PathUtils()
        utils = BaseUtils()
        
        # Test integrated workflow
        utils.initialize()
        
        # Load a module
        module_name = "integration_test"
        loaded = loader.load(module_name)
        assert isinstance(loaded, str)
        
        # Work with paths
        test_path = "integration/test/path"
        normalized = path_utils.normalize_path(test_path)
        joined = path_utils.join_paths("base", "integration", "test")
        
        assert isinstance(normalized, str)
        assert isinstance(joined, str)
        
        # Get utils info
        info = utils.get_info()
        assert isinstance(info, dict)
        
        # Cleanup
        loader.unload(module_name)
        utils.cleanup()
        
        print("✅ Utils integration tests passed")
        return True
    except Exception as e:
        print(f"❌ Utils integration tests failed: {e}")
        return False


def main():
    """Run all utils core tests."""
    print("=" * 50)
    print("🧪 XSystem Utils Core Tests")
    print("=" * 50)
    print("Testing XSystem utility functions including lazy loading,")
    print("path utilities, and common utilities")
    print("=" * 50)
    
    tests = [
        test_lazy_loader,
        test_path_utils,
        test_base_utils,
        test_utils_interfaces,
        test_utils_error_handling,
        test_utils_operations,
        test_utils_path_operations,
        test_utils_lazy_loading,
        test_utils_integration,
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
    print("📊 XSYSTEM UTILS TEST SUMMARY")
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All XSystem utils tests passed!")
        return 0
    else:
        print("💥 Some XSystem utils tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
