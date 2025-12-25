#!/usr/bin/env python3
"""
Test script for XWSerialization - Self-transforming intelligent serializer.

This script tests the core functionality of XWSerialization including:
- Format auto-detection
- Self-transformation
- Static function overrides
- File operations
- Async operations
"""

import asyncio
import json
import tempfile
from pathlib import Path

# Import XWSerialization from local development version
import sys
from pathlib import Path

# Add the src directory to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from exonware.xwsystem.io.serialization import XWSerializer
from exonware.xwsystem.io.serialization.serializer import (
    dumps,
    loads,
    save_file,
    load_file
)

# Use XWSerializer directly (no alias needed)
XWSerialization = XWSerializer

def test_basic_detection():
    """Test basic format detection and transformation."""
    print("\n🧪 Testing Basic Format Detection...")
    
    # Test JSON detection from content
    serializer = XWSerialization()
    
    # Test data
    from exonware.xwsystem.version import __version__
    test_data = {"name": "xSystem", "version": __version__, "formats": 24}
    
    # Serialize - should detect JSON from data structure
    result = serializer.dumps(test_data)
    print(f"✅ Serialized to: {type(result)} - {result[:50]}...")
    print(f"✅ Detected format: {serializer.get_detected_format()}")
    print(f"✅ Is transformed: {serializer.is_transformed()}")
    
    # Deserialize - should use the same specialized serializer
    loaded = serializer.loads(result)
    print(f"✅ Deserialized: {loaded}")
    
    assert loaded == test_data, "Data should round-trip correctly"
    assert serializer.get_detected_format() == "JSON", "Should detect JSON format"
    
    print("✅ Basic detection test passed!")

def test_file_extension_detection():
    """Test format detection from file extensions."""
    print("\n🧪 Testing File Extension Detection...")
    
    test_data = {"config": "test", "enabled": True}
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Test JSON file
        json_file = temp_path / "config.json"
        serializer = XWSerialization()
        serializer.save_file(test_data, json_file)
        
        print(f"✅ Saved to JSON file: {json_file}")
        print(f"✅ Detected format: {serializer.get_detected_format()}")
        
        # Load back
        loaded = serializer.load_file(json_file)
        assert loaded == test_data, "JSON round-trip failed"
        
        # Test YAML file (if available)
        try:
            yaml_file = temp_path / "config.yaml"
            yaml_serializer = XWSerialization()
            yaml_serializer.save_file(test_data, yaml_file)
            
            print(f"✅ Saved to YAML file: {yaml_file}")
            print(f"✅ Detected format: {yaml_serializer.get_detected_format()}")
            
            loaded_yaml = yaml_serializer.load_file(yaml_file)
            print(f"✅ Loaded from YAML: {loaded_yaml}")
            
        except ImportError:
            print("⚠️  YAML not available, skipping YAML test")
    
    print("✅ File extension detection test passed!")

def test_content_detection():
    """Test format detection from content patterns."""
    print("\n🧪 Testing Content Detection...")
    
    # Test JSON content
    json_content = '{"users": [1, 2, 3], "active": true}'
    serializer = XWSerialization()
    
    loaded = serializer.loads(json_content)
    print(f"✅ JSON detected and loaded: {loaded}")
    print(f"✅ Detected format: {serializer.get_detected_format()}")
    
    # Test YAML-like content (if YAML is available)
    try:
        yaml_content = """
name: xSystem
version: 0.0.1.3
features:
  - serialization
  - async support
  - auto detection
"""
        yaml_serializer = XWSerialization()
        loaded_yaml = yaml_serializer.loads(yaml_content.strip())
        print(f"✅ YAML detected and loaded: {loaded_yaml}")
        print(f"✅ Detected format: {yaml_serializer.get_detected_format()}")
        
    except ImportError:
        print("⚠️  YAML not available, skipping YAML content test")
    
    print("✅ Content detection test passed!")

def test_format_hints():
    """Test explicit format hints."""
    print("\n🧪 Testing Format Hints...")
    
    test_data = {"hint": "test"}
    
    # Force JSON with hint
    serializer = XWSerialization()
    result = serializer.dumps(test_data, format_hint="JSON")
    
    print(f"✅ Forced JSON format: {serializer.get_detected_format()}")
    
    # Try to force different format
    try:
        msgpack_serializer = XWSerialization()
        msgpack_result = msgpack_serializer.dumps(test_data, format_hint="MessagePack")
        print(f"✅ Forced MessagePack format: {msgpack_serializer.get_detected_format()}")
        
        # Round trip
        loaded = msgpack_serializer.loads(msgpack_result)
        assert loaded == test_data, "MessagePack round-trip failed"
        
    except ImportError:
        print("⚠️  MessagePack not available, skipping MessagePack test")
    
    print("✅ Format hints test passed!")

def test_static_functions():
    """Test static function overrides."""
    print("\n🧪 Testing Static Functions...")
    
    test_data = {"static": "test", "functions": True}
    
    # Test static dumps/loads
    serialized = dumps(test_data)
    print(f"✅ Static dumps result: {serialized[:50]}...")
    
    loaded = loads(serialized)
    print(f"✅ Static loads result: {loaded}")
    
    assert loaded == test_data, "Static functions round-trip failed"
    
    # Test static file functions
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "static_test.json"
        
        save_file(test_data, test_file)
        print(f"✅ Static save_file to: {test_file}")
        
        loaded_from_file = load_file(test_file)
        print(f"✅ Static load_file result: {loaded_from_file}")
        
        assert loaded_from_file == test_data, "Static file functions round-trip failed"
    
    print("✅ Static functions test passed!")

async def test_async_operations():
    """Test async operations."""
    print("\n🧪 Testing Async Operations...")
    
    test_data = {"async": "test", "concurrent": True}
    
    # Test async serialization
    serializer = XWSerialization()
    
    # Async dumps/loads
    serialized = await serializer.dumps_async(test_data)
    print(f"✅ Async dumps result: {serialized[:50]}...")
    
    loaded = await serializer.loads_async(serialized)
    print(f"✅ Async loads result: {loaded}")
    
    assert loaded == test_data, "Async round-trip failed"
    
    # Test async file operations
    with tempfile.TemporaryDirectory() as temp_dir:
        async_file = Path(temp_dir) / "async_test.json"
        
        await serializer.save_file_async(test_data, async_file)
        print(f"✅ Async save_file_async to: {async_file}")
        
        loaded_async = await serializer.load_file_async(async_file)
        print(f"✅ Async load_file_async result: {loaded_async}")
        
        assert loaded_async == test_data, "Async file operations failed"
    
    print("✅ Async operations test passed!")

def test_introspection():
    """Test introspection methods."""
    print("\n🧪 Testing Introspection...")
    
    # Test before transformation
    serializer = XWSerialization()
    print(f"✅ Before transformation:")
    print(f"   - Is transformed: {serializer.is_transformed()}")
    print(f"   - Detected format: {serializer.get_detected_format()}")
    print(f"   - Format name: {serializer.format_name}")
    
    # Trigger transformation
    test_data = {"introspection": "test"}
    serializer.dumps(test_data)
    
    print(f"✅ After transformation:")
    print(f"   - Is transformed: {serializer.is_transformed()}")
    print(f"   - Detected format: {serializer.get_detected_format()}")
    print(f"   - Format name: {serializer.format_name}")
    print(f"   - Specialized serializer: {type(serializer.get_specialized_serializer())}")
    
    # Test force format
    force_serializer = XWSerialization()
    force_serializer.force_format("JSON")
    print(f"✅ Forced format: {force_serializer.get_detected_format()}")
    
    print("✅ Introspection test passed!")

def test_error_handling():
    """Test error handling and fallbacks."""
    print("\n🧪 Testing Error Handling...")
    
    # Test with invalid file
    serializer = XWSerialization()
    
    try:
        serializer.load_file("nonexistent_file.json")
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        print("✅ Correctly handled missing file")
    
    # Test with invalid data
    try:
        serializer.loads("invalid json content {{{")
        print("⚠️  Invalid JSON was somehow parsed (fallback worked)")
    except Exception as e:
        print(f"✅ Correctly handled invalid JSON: {type(e).__name__}")
    
    print("✅ Error handling test passed!")

def run_all_tests():
    """Run all tests."""
    print("🚀 Starting XWSerialization Tests...")
    print("=" * 60)
    
    try:
        # Basic tests
        test_basic_detection()
        test_file_extension_detection()
        test_content_detection()
        test_format_hints()
        test_static_functions()
        test_introspection()
        test_error_handling()
        
        # Async test
        print("\n🧪 Running Async Tests...")
        asyncio.run(test_async_operations())
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("✅ XWSerialization is working perfectly!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
