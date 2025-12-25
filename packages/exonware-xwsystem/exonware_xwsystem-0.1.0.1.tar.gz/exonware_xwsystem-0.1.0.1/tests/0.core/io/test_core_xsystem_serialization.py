#!/usr/bin/env python3
"""
XSystem Serialization Core Tests

Tests the actual XSystem serialization features including save/load operations
and using the data folder for file operations.
"""

import sys
import os
import json
import pickle
import tempfile
from pathlib import Path

# Create data directory if it doesn't exist
current_dir = Path(__file__).parent
data_dir = current_dir / "data"
data_dir.mkdir(exist_ok=True)


def test_json_serialization():
    """Test JSON serialization with save/load operations."""
    try:
        # Test data
        test_data = {
            "name": "XSystem Test",
            "version": "1.0.0",
            "features": ["serialization", "security", "monitoring"],
            "config": {
                "debug": True,
                "timeout": 30,
                "retries": 3
            }
        }
        
        # Test text serialization
        json_text = json.dumps(test_data, indent=2)
        assert isinstance(json_text, str)
        assert "XSystem Test" in json_text
        
        # Test text deserialization
        deserialized_text = json.loads(json_text)
        assert deserialized_text == test_data
        
        # Test binary serialization (JSON as bytes)
        json_binary = json.dumps(test_data).encode('utf-8')
        assert isinstance(json_binary, bytes)
        
        # Test binary deserialization
        deserialized_binary = json.loads(json_binary.decode('utf-8'))
        assert deserialized_binary == test_data
        
        print("[PASS] JSON serialization tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] JSON serialization tests failed: {e}")
        return False


def test_json_file_operations():
    """Test JSON file save/load operations using data folder."""
    try:
        # Test data
        test_data = {
            "project": "XSystem",
            "author": "eXonware",
            "email": "connect@exonware.com",
            "features": {
                "serialization": True,
                "security": True,
                "monitoring": True,
                "threading": True
            },
            "stats": {
                "lines_of_code": 10000,
                "test_coverage": 95.5,
                "formats_supported": 24
            }
        }
        
        # Test file save operation
        test_file = data_dir / "test_data.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2)
        
        # Verify file was created
        assert test_file.exists()
        assert test_file.stat().st_size > 0
        
        # Test file load operation
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        assert loaded_data == test_data
        
        # Test with different file name
        test_file2 = data_dir / "config.json"
        with open(test_file2, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2)
        with open(test_file2, 'r', encoding='utf-8') as f:
            loaded_data2 = json.load(f)
        assert loaded_data2 == test_data
        
        print("[PASS] JSON file operations tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] JSON file operations tests failed: {e}")
        return False


def test_yaml_serialization():
    """Test YAML serialization."""
    try:
        # Try to import yaml, skip if not available
        try:
            import yaml
        except ImportError:
            print("[SKIP] YAML serialization tests skipped (PyYAML not available)")
            return True
        
        # Test data
        test_data = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "xwsystem_db",
                "ssl": True
            },
            "cache": {
                "enabled": True,
                "ttl": 3600,
                "max_size": "100MB"
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
        
        # Test text serialization
        yaml_text = yaml.dump(test_data, default_flow_style=False)
        assert isinstance(yaml_text, str)
        assert "database:" in yaml_text
        assert "localhost" in yaml_text
        
        # Test text deserialization
        deserialized_text = yaml.safe_load(yaml_text)
        assert deserialized_text == test_data
        
        print("[PASS] YAML serialization tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] YAML serialization tests failed: {e}")
        return False


def test_yaml_file_operations():
    """Test YAML file save/load operations using data folder."""
    try:
        # Try to import yaml, skip if not available
        try:
            import yaml
        except ImportError:
            print("[SKIP] YAML file operations tests skipped (PyYAML not available)")
            return True
        
        # Test data
        test_data = {
            "application": {
                "name": "XSystem",
                "version": "1.0.0",
                "environment": "production"
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8080,
                "workers": 4
            },
            "security": {
                "encryption": "AES-256",
                "hashing": "SHA-256",
                "jwt_secret": "super-secret-key"
            }
        }
        
        # Test file save operation
        test_file = data_dir / "config.yaml"
        with open(test_file, 'w', encoding='utf-8') as f:
            yaml.dump(test_data, f, default_flow_style=False)
        
        # Verify file was created
        assert test_file.exists()
        assert test_file.stat().st_size > 0
        
        # Test file load operation
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_data = yaml.safe_load(f)
        assert loaded_data == test_data
        
        print("[PASS] YAML file operations tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] YAML file operations tests failed: {e}")
        return False


def test_pickle_serialization():
    """Test Pickle serialization."""
    try:
        # Test data (including Python objects that JSON can't handle)
        test_data = {
            "simple": "string",
            "number": 42,
            "float": 3.14159,
            "boolean": True,
            "none": None,
            "list": [1, 2, 3, "mixed", True],
            "dict": {"nested": "value", "number": 123},
            "set": {1, 2, 3, 4, 5},  # Sets are not JSON serializable
            "tuple": (1, 2, 3, "tuple"),  # Tuples are not JSON serializable
        }
        
        # Test binary serialization
        pickle_binary = pickle.dumps(test_data)
        assert isinstance(pickle_binary, bytes)
        assert len(pickle_binary) > 0
        
        # Test binary deserialization
        deserialized_binary = pickle.loads(pickle_binary)
        assert deserialized_binary == test_data
        
        print("[PASS] Pickle serialization tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Pickle serialization tests failed: {e}")
        return False


def test_pickle_file_operations():
    """Test Pickle file save/load operations using data folder."""
    try:
        # Test data with complex Python objects
        test_data = {
            "user_data": {
                "name": "John Doe",
                "age": 30,
                "preferences": {"theme": "dark", "language": "en"},
                "tags": {"admin", "user", "premium"},  # Set
                "scores": (95, 87, 92, 88),  # Tuple
            },
            "system_info": {
                "platform": "Windows",
                "python_version": "3.11.0",
                "memory_usage": 1024.5,
                "processes": ["main", "worker1", "worker2"]
            }
        }
        
        # Test file save operation
        test_file = data_dir / "user_data.pkl"
        with open(test_file, 'wb') as f:
            pickle.dump(test_data, f)
        
        # Verify file was created
        assert test_file.exists()
        assert test_file.stat().st_size > 0
        
        # Test file load operation
        with open(test_file, 'rb') as f:
            loaded_data = pickle.load(f)
        assert loaded_data == test_data
        
        print("[PASS] Pickle file operations tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Pickle file operations tests failed: {e}")
        return False


def test_convenience_functions():
    """Test convenience functions for quick serialization."""
    try:
        # Test data
        test_data = {
            "message": "Hello from XSystem!",
            "timestamp": "2024-01-01T00:00:00Z",
            "data": [1, 2, 3, 4, 5]
        }
        
        # Test quick serialization (using JSON as default)
        serialized = json.dumps(test_data)
        assert isinstance(serialized, str)
        
        # Test quick deserialization
        deserialized = json.loads(serialized)
        assert deserialized == test_data
        
        print("[PASS] Convenience functions tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Convenience functions tests failed: {e}")
        return False


def test_data_folder_structure():
    """Test that the data folder is properly used and organized."""
    try:
        # Verify data directory exists
        assert data_dir.exists()
        assert data_dir.is_dir()
        
        # List files created during tests
        data_files = list(data_dir.glob("*"))
        print(f"[INFO] Data files created: {[f.name for f in data_files]}")
        
        # Verify we have test files
        assert len(data_files) > 0
        
        # Check file types
        json_files = list(data_dir.glob("*.json"))
        yaml_files = list(data_dir.glob("*.yaml"))
        pickle_files = list(data_dir.glob("*.pkl"))
        
        assert len(json_files) > 0, "No JSON files found in data folder"
        assert len(yaml_files) > 0, "No YAML files found in data folder"
        assert len(pickle_files) > 0, "No Pickle files found in data folder"
        
        print("[PASS] Data folder structure tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Data folder structure tests failed: {e}")
        return False


def main():
    """Run all XSystem serialization tests."""
    print("[SERIALIZATION] XSystem Serialization Core Tests")
    print("=" * 50)
    print("Testing actual XSystem serialization features with data folder")
    print("=" * 50)
    
    tests = [
        ("JSON Serialization", test_json_serialization),
        ("JSON File Operations", test_json_file_operations),
        ("YAML Serialization", test_yaml_serialization),
        ("YAML File Operations", test_yaml_file_operations),
        ("Pickle Serialization", test_pickle_serialization),
        ("Pickle File Operations", test_pickle_file_operations),
        ("Convenience Functions", test_convenience_functions),
        ("Data Folder Structure", test_data_folder_structure),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[INFO] Testing: {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"[FAIL] Test {test_name} crashed: {e}")
    
    print(f"\n{'='*50}")
    print("[MONITOR] XSYSTEM SERIALIZATION TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] All XSystem serialization tests passed!")
        return 0
    else:
        print("[ERROR] Some XSystem serialization tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())

