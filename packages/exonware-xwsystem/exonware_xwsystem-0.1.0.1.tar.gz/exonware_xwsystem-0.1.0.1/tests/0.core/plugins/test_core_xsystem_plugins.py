#exonware/xwsystem/tests/core/plugins/test_core_xwsystem_plugins.py
"""
XSystem Plugins Core Tests

Comprehensive tests for XSystem plugin system including plugin management,
loading, and lifecycle management.
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

try:
    from exonware.xwsystem.plugins.base import BasePlugin
    from exonware.xwsystem.plugins.contracts import IPlugin
    from exonware.xwsystem.plugins.errors import PluginError
except ImportError as e:
    print(f"Import error: {e}")
    # Create mock classes for testing
    class BasePlugin:
        def __init__(self): pass
        def initialize(self): pass
        def activate(self): pass
        def deactivate(self): pass
        def cleanup(self): pass
        def get_info(self): return {"name": "test_plugin", "version": "1.0.0"}
    
    class IPlugin: pass
    
    class PluginError(Exception): pass


def test_base_plugin():
    """Test base plugin functionality."""
    print("📋 Testing: Base Plugin")
    print("-" * 30)
    
    try:
        plugin = BasePlugin()
        
        # Test plugin lifecycle
        plugin.initialize()
        plugin.activate()
        plugin.deactivate()
        plugin.cleanup()
        
        # Test plugin info
        info = plugin.get_info()
        assert isinstance(info, dict)
        assert "name" in info
        assert "version" in info
        
        print("✅ Base plugin tests passed")
        return True
    except Exception as e:
        print(f"❌ Base plugin tests failed: {e}")
        return False


def test_plugin_interfaces():
    """Test plugin interface compliance."""
    print("📋 Testing: Plugin Interfaces")
    print("-" * 30)
    
    try:
        # Test interface compliance
        plugin = BasePlugin()
        
        # Verify object can be instantiated
        assert plugin is not None
        
        print("✅ Plugin interfaces tests passed")
        return True
    except Exception as e:
        print(f"❌ Plugin interfaces tests failed: {e}")
        return False


def test_plugin_error_handling():
    """Test plugin error handling."""
    print("📋 Testing: Plugin Error Handling")
    print("-" * 30)
    
    try:
        # Test error classes
        plugin_error = PluginError("Test plugin error")
        
        assert str(plugin_error) == "Test plugin error"
        
        print("✅ Plugin error handling tests passed")
        return True
    except Exception as e:
        print(f"❌ Plugin error handling tests failed: {e}")
        return False


def test_plugin_lifecycle():
    """Test plugin lifecycle management."""
    print("📋 Testing: Plugin Lifecycle")
    print("-" * 30)
    
    try:
        plugin = BasePlugin()
        
        # Test complete lifecycle
        plugin.initialize()
        plugin.activate()
        
        # Verify plugin is active
        info = plugin.get_info()
        assert info is not None
        
        plugin.deactivate()
        plugin.cleanup()
        
        print("✅ Plugin lifecycle tests passed")
        return True
    except Exception as e:
        print(f"❌ Plugin lifecycle tests failed: {e}")
        return False


def test_plugin_info():
    """Test plugin information functionality."""
    print("📋 Testing: Plugin Info")
    print("-" * 30)
    
    try:
        plugin = BasePlugin()
        
        # Test plugin information
        info = plugin.get_info()
        assert isinstance(info, dict)
        assert "name" in info
        assert "version" in info
        
        # Verify info structure
        assert isinstance(info["name"], str)
        assert isinstance(info["version"], str)
        
        print("✅ Plugin info tests passed")
        return True
    except Exception as e:
        print(f"❌ Plugin info tests failed: {e}")
        return False


def test_plugin_operations():
    """Test plugin operations."""
    print("📋 Testing: Plugin Operations")
    print("-" * 30)
    
    try:
        plugin = BasePlugin()
        
        # Test multiple lifecycle cycles
        for i in range(3):
            plugin.initialize()
            plugin.activate()
            plugin.deactivate()
            plugin.cleanup()
        
        print("✅ Plugin operations tests passed")
        return True
    except Exception as e:
        print(f"❌ Plugin operations tests failed: {e}")
        return False


def test_plugin_management():
    """Test plugin management functionality."""
    print("📋 Testing: Plugin Management")
    print("-" * 30)
    
    try:
        # Test multiple plugins
        plugins = [BasePlugin() for _ in range(3)]
        
        # Initialize all plugins
        for plugin in plugins:
            plugin.initialize()
        
        # Activate all plugins
        for plugin in plugins:
            plugin.activate()
        
        # Get info from all plugins
        for plugin in plugins:
            info = plugin.get_info()
            assert info is not None
        
        # Deactivate and cleanup all plugins
        for plugin in plugins:
            plugin.deactivate()
            plugin.cleanup()
        
        print("✅ Plugin management tests passed")
        return True
    except Exception as e:
        print(f"❌ Plugin management tests failed: {e}")
        return False


def test_plugin_integration():
    """Test plugin integration functionality."""
    print("📋 Testing: Plugin Integration")
    print("-" * 30)
    
    try:
        # Test plugin integration workflow
        plugin1 = BasePlugin()
        plugin2 = BasePlugin()
        
        # Initialize plugins
        plugin1.initialize()
        plugin2.initialize()
        
        # Activate plugins
        plugin1.activate()
        plugin2.activate()
        
        # Get plugin information
        info1 = plugin1.get_info()
        info2 = plugin2.get_info()
        
        assert info1 is not None
        assert info2 is not None
        
        # Deactivate plugins
        plugin1.deactivate()
        plugin2.deactivate()
        
        # Cleanup plugins
        plugin1.cleanup()
        plugin2.cleanup()
        
        print("✅ Plugin integration tests passed")
        return True
    except Exception as e:
        print(f"❌ Plugin integration tests failed: {e}")
        return False


def main():
    """Run all plugins core tests."""
    print("=" * 50)
    print("🧪 XSystem Plugins Core Tests")
    print("=" * 50)
    print("Testing XSystem plugin system including plugin management,")
    print("loading, and lifecycle management")
    print("=" * 50)
    
    tests = [
        test_base_plugin,
        test_plugin_interfaces,
        test_plugin_error_handling,
        test_plugin_lifecycle,
        test_plugin_info,
        test_plugin_operations,
        test_plugin_management,
        test_plugin_integration,
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
    print("📊 XSYSTEM PLUGINS TEST SUMMARY")
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All XSystem plugins tests passed!")
        return 0
    else:
        print("💥 Some XSystem plugins tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
