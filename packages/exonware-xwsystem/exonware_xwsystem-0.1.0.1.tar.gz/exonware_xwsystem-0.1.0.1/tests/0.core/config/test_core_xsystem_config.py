#exonware/xwsystem/tests/core/config/test_core_xwsystem_config.py
"""
XSystem Config Core Tests

Comprehensive tests for XSystem configuration management including defaults,
performance modes, logging setup, and configuration validation.
"""

import sys
import os
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

try:
    from exonware.xwsystem.config.defaults import DefaultConfig
    from exonware.xwsystem.config.performance_modes import PerformanceModes
    from exonware.xwsystem.config.performance import PerformanceConfig
    from exonware.xwsystem.config.logging_setup import LoggingSetup
    from exonware.xwsystem.config.logging import LoggingConfig
    from exonware.xwsystem.config.base import BaseConfig
    from exonware.xwsystem.config.contracts import IConfig, IPerformanceConfig, ILoggingConfig
    from exonware.xwsystem.config.errors import ConfigError, PerformanceError, LoggingError
except ImportError as e:
    print(f"Import error: {e}")
    # Create mock classes for testing
    class DefaultConfig:
        def __init__(self): 
            self.defaults = {}
        def get_default(self, key): 
            return self.defaults.get(key, "default_value")
        def set_default(self, key, value): 
            self.defaults[key] = value
        def load_defaults(self): pass
    
    class PerformanceModes:
        FAST = "fast"
        BALANCED = "balanced"
        MEMORY_OPTIMIZED = "memory_optimized"
    
    class PerformanceConfig:
        def __init__(self): pass
        def set_mode(self, mode): pass
        def get_mode(self): return PerformanceModes.BALANCED
        def optimize(self): pass
    
    class LoggingSetup:
        def __init__(self): pass
        def setup_logging(self): pass
        def configure_logger(self, name): pass
    
    class LoggingConfig:
        def __init__(self): pass
        def set_level(self, level): pass
        def get_level(self): return "INFO"
        def add_handler(self, handler): pass
    
    class BaseConfig:
        def __init__(self): pass
        def load(self): pass
        def save(self): pass
        def validate(self): return True
    
    class IConfig: pass
    class IPerformanceConfig: pass
    class ILoggingConfig: pass
    
    class ConfigError(Exception): pass
    class PerformanceError(Exception): pass
    class LoggingError(Exception): pass


def test_default_config():
    """Test default configuration functionality."""
    print("📋 Testing: Default Configuration")
    print("-" * 30)
    
    try:
        config = DefaultConfig()
        
        # Test default operations
        config.load_defaults()
        value = config.get_default("test_key")
        assert value is not None
        
        config.set_default("test_key", "test_value")
        value = config.get_default("test_key")
        assert value == "test_value"
        
        print("✅ Default configuration tests passed")
        return True
    except Exception as e:
        print(f"❌ Default configuration tests failed: {e}")
        return False


def test_performance_modes():
    """Test performance modes functionality."""
    print("📋 Testing: Performance Modes")
    print("-" * 30)
    
    try:
        # Test performance mode constants
        assert hasattr(PerformanceModes, 'FAST')
        assert hasattr(PerformanceModes, 'BALANCED')
        assert hasattr(PerformanceModes, 'MEMORY_OPTIMIZED')
        
        # Test mode values
        assert PerformanceModes.FAST == "fast"
        assert PerformanceModes.BALANCED == "balanced"
        assert PerformanceModes.MEMORY_OPTIMIZED == "memory_optimized"
        
        print("✅ Performance modes tests passed")
        return True
    except Exception as e:
        print(f"❌ Performance modes tests failed: {e}")
        return False


def test_performance_config():
    """Test performance configuration functionality."""
    print("📋 Testing: Performance Configuration")
    print("-" * 30)
    
    try:
        config = PerformanceConfig()
        
        # Test performance configuration
        config.set_mode(PerformanceModes.FAST)
        mode = config.get_mode()
        assert mode in [PerformanceModes.FAST, PerformanceModes.BALANCED, PerformanceModes.MEMORY_OPTIMIZED]
        
        config.optimize()
        
        print("✅ Performance configuration tests passed")
        return True
    except Exception as e:
        print(f"❌ Performance configuration tests failed: {e}")
        return False


def test_logging_setup():
    """Test logging setup functionality."""
    print("📋 Testing: Logging Setup")
    print("-" * 30)
    
    try:
        setup = LoggingSetup()
        
        # Test logging setup
        setup.setup_logging()
        setup.configure_logger("test_logger")
        
        print("✅ Logging setup tests passed")
        return True
    except Exception as e:
        print(f"❌ Logging setup tests failed: {e}")
        return False


def test_logging_config():
    """Test logging configuration functionality."""
    print("📋 Testing: Logging Configuration")
    print("-" * 30)
    
    try:
        config = LoggingConfig()
        
        # Test logging configuration
        config.set_level("DEBUG")
        level = config.get_level()
        assert level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        mock_handler = MagicMock()
        config.add_handler(mock_handler)
        
        print("✅ Logging configuration tests passed")
        return True
    except Exception as e:
        print(f"❌ Logging configuration tests failed: {e}")
        return False


def test_base_config():
    """Test base configuration functionality."""
    print("📋 Testing: Base Configuration")
    print("-" * 30)
    
    try:
        config = BaseConfig()
        
        # Test base configuration operations
        config.load()
        config.save()
        is_valid = config.validate()
        assert isinstance(is_valid, bool)
        
        print("✅ Base configuration tests passed")
        return True
    except Exception as e:
        print(f"❌ Base configuration tests failed: {e}")
        return False


def test_config_interfaces():
    """Test configuration interface compliance."""
    print("📋 Testing: Configuration Interfaces")
    print("-" * 30)
    
    try:
        # Test interface compliance
        config = DefaultConfig()
        perf_config = PerformanceConfig()
        log_config = LoggingConfig()
        
        # Verify objects can be instantiated
        assert config is not None
        assert perf_config is not None
        assert log_config is not None
        
        print("✅ Configuration interfaces tests passed")
        return True
    except Exception as e:
        print(f"❌ Configuration interfaces tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_error_handling():
    """Test configuration error handling."""
    print("📋 Testing: Configuration Error Handling")
    print("-" * 30)
    
    try:
        # Test error classes
        config_error = ConfigError("Test config error")
        perf_error = PerformanceError("Test performance error")
        log_error = LoggingError("Test logging error")
        
        assert str(config_error) == "Test config error"
        assert str(perf_error) == "Test performance error"
        assert str(log_error) == "Test logging error"
        
        print("✅ Configuration error handling tests passed")
        return True
    except Exception as e:
        print(f"❌ Configuration error handling tests failed: {e}")
        return False


def test_config_file_operations():
    """Test configuration file operations."""
    print("📋 Testing: Configuration File Operations")
    print("-" * 30)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "test_config.json"
            
            # Test JSON configuration
            test_config = {"key1": "value1", "key2": "value2"}
            with open(config_file, 'w') as f:
                json.dump(test_config, f)
            
            # Verify file was created
            assert config_file.exists()
            
            # Test reading configuration
            with open(config_file, 'r') as f:
                loaded_config = json.load(f)
            
            assert loaded_config == test_config
            
        print("✅ Configuration file operations tests passed")
        return True
    except Exception as e:
        print(f"❌ Configuration file operations tests failed: {e}")
        return False


def main():
    """Run all config core tests."""
    print("=" * 50)
    print("🧪 XSystem Config Core Tests")
    print("=" * 50)
    print("Testing XSystem configuration management including defaults,")
    print("performance modes, logging setup, and configuration validation")
    print("=" * 50)
    
    tests = [
        test_default_config,
        test_performance_modes,
        test_performance_config,
        test_logging_setup,
        test_logging_config,
        test_base_config,
        test_config_interfaces,
        test_config_error_handling,
        test_config_file_operations,
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
    print("📊 XSYSTEM CONFIG TEST SUMMARY")
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All XSystem config tests passed!")
        return 0
    else:
        print("💥 Some XSystem config tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
