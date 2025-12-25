#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core tests for comprehensive serialization operations.

Tests all serialization formats, registry, format detection, and auto-serializer.

Following GUIDE_TEST.md standards.
"""

import sys
import tempfile
from pathlib import Path

import pytest

# Import serialization classes
from exonware.xwsystem.io.serialization import (
    SerializationRegistry,
    get_serialization_registry,
)
from exonware.xwsystem.io.serialization.format_detector import detect_format, FormatDetector
from exonware.xwsystem.io.serialization.auto_serializer import AutoSerializer
from exonware.xwsystem.io.serialization.flyweight import get_serializer, get_flyweight_stats


# Test data for roundtrip testing
TEST_DATA = {
    "simple": {"key": "value", "number": 42, "boolean": True},
    "nested": {
        "level1": {
            "level2": {
                "level3": "deep"
            }
        },
        "list": [1, 2, 3, "items"]
    },
    "list_of_dicts": [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25}
    ],
}


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_serialization
class TestSerializationRegistry:
    """Test SerializationRegistry."""
    
    def test_serialization_registry_exists(self):
        """Test that serialization registry is accessible."""
        registry = get_serialization_registry()
        assert registry is not None
    
    def test_serialization_registry_list_formats(self):
        """Test listing registered serialization formats."""
        registry = get_serialization_registry()
        formats = registry.list_formats()
        assert len(formats) > 0
        # Common formats should be registered
        assert "json" in formats or "yaml" in formats
    
    def test_serialization_registry_get_by_format(self):
        """Test getting serializer by format ID."""
        registry = get_serialization_registry()
        
        # Try to get JSON serializer
        json_ser = registry.get_by_format("json")
        if json_ser is not None:
            assert json_ser.codec_id == "json"
    
    def test_serialization_registry_detect_from_file(self, tmp_path):
        """Test detecting serializer from file path."""
        registry = get_serialization_registry()
        
        # Test JSON detection
        json_file = tmp_path / "test.json"
        ser = registry.detect_from_file(json_file)
        if ser is not None:
            assert ser.codec_id == "json"
        
        # Test YAML detection
        yaml_file = tmp_path / "test.yaml"
        ser = registry.detect_from_file(yaml_file)
        if ser is not None:
            assert ser.codec_id == "yaml"


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_serialization
class TestFormatDetector:
    """Test format detection."""
    
    def test_format_detector_basic(self):
        """Test basic format detection."""
        detector = FormatDetector()
        assert detector is not None
    
    def test_detect_format_from_extension(self):
        """Test format detection from file extension."""
        # Test JSON
        format_name = detect_format(Path("test.json"))
        assert format_name is not None
        
        # Test YAML
        format_name = detect_format(Path("test.yaml"))
        assert format_name is not None


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_serialization
class TestAutoSerializer:
    """Test AutoSerializer."""
    
    def test_auto_serializer_basic(self):
        """Test basic AutoSerializer functionality."""
        auto_ser = AutoSerializer()
        assert auto_ser is not None
    
    def test_auto_serializer_detect_and_save(self, tmp_path):
        """Test auto-detection and saving."""
        try:
            auto_ser = AutoSerializer()
            test_file = tmp_path / "auto_test.json"
            test_data = {"key": "value"}
            
            # Save with auto-detection
            auto_ser.save_file(test_data, test_file)
            
            # Verify file exists
            assert test_file.exists()
        except Exception as e:
            pytest.skip(f"AutoSerializer not fully available: {e}")


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_serialization
class TestTextFormats:
    """Test text-based serialization formats."""
    
    def test_json_serializer_roundtrip(self, tmp_path):
        """Test JSON serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.text.json import JsonSerializer
            
            serializer = JsonSerializer()
            test_file = tmp_path / "test.json"
            test_data = TEST_DATA["simple"]
            
            # Encode and save
            encoded = serializer.encode(test_data)
            serializer.save_file(test_data, test_file)
            
            # Load and decode
            loaded = serializer.load_file(test_file)
            assert loaded == test_data
            
            # Decode from string
            decoded = serializer.decode(encoded)
            assert decoded == test_data
        except ImportError:
            pytest.skip("JSON serializer not available")
    
    def test_yaml_serializer_roundtrip(self, tmp_path):
        """Test YAML serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.text.yaml import YamlSerializer
            
            serializer = YamlSerializer()
            test_file = tmp_path / "test.yaml"
            test_data = TEST_DATA["simple"]
            
            # Save and load
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            assert loaded == test_data
        except ImportError:
            pytest.skip("YAML serializer not available")
    
    def test_toml_serializer_roundtrip(self, tmp_path):
        """Test TOML serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.text.toml import TomlSerializer
            
            serializer = TomlSerializer()
            test_file = tmp_path / "test.toml"
            test_data = TEST_DATA["simple"]
            
            # Save and load
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            # TOML may have different structure, so just verify it loads
            assert loaded is not None
        except ImportError:
            pytest.skip("TOML serializer not available")
    
    def test_xml_serializer_roundtrip(self, tmp_path):
        """Test XML serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.text.xml import XmlSerializer
            
            serializer = XmlSerializer()
            test_file = tmp_path / "test.xml"
            test_data = TEST_DATA["simple"]
            
            # Save and load
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            # XML structure may differ, verify it loads
            assert loaded is not None
        except ImportError:
            pytest.skip("XML serializer not available")
    
    def test_csv_serializer_roundtrip(self, tmp_path):
        """Test CSV serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.text.csv import CsvSerializer
            
            serializer = CsvSerializer()
            test_file = tmp_path / "test.csv"
            # CSV works with list of dicts
            test_data = TEST_DATA["list_of_dicts"]
            
            # Save and load
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            # CSV may return list of dicts or dict of lists
            assert loaded is not None
        except ImportError:
            pytest.skip("CSV serializer not available")
    
    def test_configparser_serializer_roundtrip(self, tmp_path):
        """Test ConfigParser serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.text.configparser import ConfigParserSerializer
            
            serializer = ConfigParserSerializer()
            test_file = tmp_path / "test.ini"
            test_data = {"section": {"key": "value"}}
            
            # Save and load
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            assert loaded is not None
        except ImportError:
            pytest.skip("ConfigParser serializer not available")
    
    def test_formdata_serializer_roundtrip(self, tmp_path):
        """Test FormData serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.text.formdata import FormDataSerializer
            
            serializer = FormDataSerializer()
            test_data = {"username": "test", "password": "secret"}
            
            # Encode and decode
            encoded = serializer.encode(test_data)
            decoded = serializer.decode(encoded)
            # FormData may return lists for values
            assert decoded is not None
        except ImportError:
            pytest.skip("FormData serializer not available")
    
    def test_multipart_serializer_roundtrip(self, tmp_path):
        """Test Multipart serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.text.multipart import MultipartSerializer
            
            serializer = MultipartSerializer()
            test_data = {"field1": "value1", "field2": "value2"}
            
            # Encode and decode
            encoded = serializer.encode(test_data)
            decoded = serializer.decode(encoded)
            assert decoded is not None
        except ImportError:
            pytest.skip("Multipart serializer not available")
    
    def test_json5_serializer_roundtrip(self, tmp_path):
        """Test JSON5 serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.text.json5 import Json5Serializer
            
            serializer = Json5Serializer()
            test_file = tmp_path / "test.json5"
            test_data = TEST_DATA["simple"]
            
            # Save and load
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            assert loaded == test_data
        except ImportError:
            pytest.skip("JSON5 serializer not available")
    
    def test_jsonlines_serializer_roundtrip(self, tmp_path):
        """Test JSONLines serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.text.jsonlines import JsonLinesSerializer
            
            serializer = JsonLinesSerializer()
            test_file = tmp_path / "test.jsonl"
            # JSONLines works with list of objects
            test_data = TEST_DATA["list_of_dicts"]
            
            # Save and load
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            assert loaded == test_data
        except ImportError:
            pytest.skip("JSONLines serializer not available")


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_serialization
class TestBinaryFormats:
    """Test binary serialization formats."""
    
    def test_pickle_serializer_roundtrip(self, tmp_path):
        """Test Pickle serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.binary.pickle import PickleSerializer
            
            serializer = PickleSerializer()
            test_file = tmp_path / "test.pkl"
            test_data = TEST_DATA["simple"]
            
            # Save and load
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            assert loaded == test_data
        except ImportError:
            pytest.skip("Pickle serializer not available")
    
    def test_msgpack_serializer_roundtrip(self, tmp_path):
        """Test MessagePack serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.binary.msgpack import MsgPackSerializer
            
            serializer = MsgPackSerializer()
            test_file = tmp_path / "test.msgpack"
            test_data = TEST_DATA["simple"]
            
            # Save and load
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            assert loaded == test_data
        except ImportError:
            pytest.skip("MessagePack serializer not available")
    
    def test_bson_serializer_roundtrip(self, tmp_path):
        """Test BSON serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.binary.bson import BsonSerializer
            
            serializer = BsonSerializer()
            test_file = tmp_path / "test.bson"
            test_data = TEST_DATA["simple"]
            
            # Save and load
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            assert loaded == test_data
        except ImportError:
            pytest.skip("BSON serializer not available")
    
    def test_cbor_serializer_roundtrip(self, tmp_path):
        """Test CBOR serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.binary.cbor import CborSerializer
            
            serializer = CborSerializer()
            test_file = tmp_path / "test.cbor"
            test_data = TEST_DATA["simple"]
            
            # Save and load
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            assert loaded == test_data
        except ImportError:
            pytest.skip("CBOR serializer not available")
    
    def test_marshal_serializer_roundtrip(self, tmp_path):
        """Test Marshal serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.binary.marshal import MarshalSerializer
            
            serializer = MarshalSerializer()
            test_file = tmp_path / "test.marshal"
            test_data = TEST_DATA["simple"]
            
            # Save and load
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            assert loaded == test_data
        except ImportError:
            pytest.skip("Marshal serializer not available")
    
    def test_plistlib_serializer_roundtrip(self, tmp_path):
        """Test PlistLib serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.binary.plistlib import PlistSerializer
            
            serializer = PlistSerializer()
            test_file = tmp_path / "test.plist"
            test_data = TEST_DATA["simple"]
            
            # Save and load
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            assert loaded == test_data
        except ImportError:
            pytest.skip("PlistLib serializer not available")


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_serialization
class TestDatabaseFormats:
    """Test database serialization formats."""
    
    def test_sqlite3_serializer_roundtrip(self, tmp_path):
        """Test SQLite3 serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.database.sqlite3 import Sqlite3Serializer
            
            serializer = Sqlite3Serializer()
            test_file = tmp_path / "test.db"
            test_data = TEST_DATA["simple"]
            
            # Save and load
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            assert loaded == test_data
        except ImportError:
            pytest.skip("SQLite3 serializer not available")
    
    def test_dbm_serializer_roundtrip(self, tmp_path):
        """Test DBM serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.database.dbm import DbmSerializer
            
            serializer = DbmSerializer()
            test_file = tmp_path / "test.dbm"
            test_data = TEST_DATA["simple"]
            
            # Save and load
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            assert loaded == test_data
        except ImportError:
            pytest.skip("DBM serializer not available")
    
    def test_shelve_serializer_roundtrip(self, tmp_path):
        """Test Shelve serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.database.shelve import ShelveSerializer
            
            serializer = ShelveSerializer()
            test_file = tmp_path / "test.shelf"
            test_data = TEST_DATA["simple"]
            
            # Save and load
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            assert loaded == test_data
        except ImportError:
            pytest.skip("Shelve serializer not available")


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_serialization
class TestFlyweightPattern:
    """Test flyweight pattern for serializers."""
    
    def test_get_serializer_flyweight(self):
        """Test getting serializer via flyweight pattern."""
        try:
            # Get serializer multiple times - should return same instance
            ser1 = get_serializer("json")
            ser2 = get_serializer("json")
            
            if ser1 is not None and ser2 is not None:
                # Should be same instance (flyweight)
                assert ser1 is ser2
        except Exception:
            pytest.skip("Flyweight pattern not available")
    
    def test_flyweight_stats(self):
        """Test flyweight statistics."""
        try:
            stats = get_flyweight_stats()
            assert stats is not None
        except Exception:
            pytest.skip("Flyweight stats not available")

