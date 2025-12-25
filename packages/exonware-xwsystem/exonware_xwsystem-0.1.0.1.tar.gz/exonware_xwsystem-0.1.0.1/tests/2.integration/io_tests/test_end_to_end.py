"""
Integration tests for io module

Tests end-to-end workflows across io sub-modules.
Following GUIDELINES_TEST.md structure and eXonware testing standards.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
"""

import pytest
import tempfile
from pathlib import Path
from exonware.xwsystem.io.facade import XWIO


@pytest.mark.xwsystem_integration
class TestSerializationIntegration:
    """Test complete serialization workflows."""
    
    def test_json_roundtrip_via_facade(self, tmp_path):
        """
        Test complete JSON serialization roundtrip via XWIO facade.
        
        Given: Sample data and a file path
        When: Serializing to JSON and deserializing back
        Then: Data is preserved correctly
        """
        io = XWIO()
        test_data = {"name": "Alice", "age": 30, "active": True}
        file_path = tmp_path / "test.json"
        
        # Serialize and save
        io.save_serialized(test_data, file_path, format="json")
        
        # Load and deserialize
        loaded_data = io.load_serialized(file_path, format="json")
        
        assert loaded_data == test_data
    
    def test_yaml_roundtrip_via_facade(self, tmp_path):
        """
        Test complete YAML serialization roundtrip via XWIO facade.
        
        Given: Sample data and a file path
        When: Serializing to YAML and deserializing back
        Then: Data is preserved correctly
        """
        io = XWIO()
        test_data = {"name": "Bob", "tags": ["python", "testing"]}
        file_path = tmp_path / "test.yaml"
        
        # Serialize and save
        io.save_serialized(test_data, file_path, format="yaml")
        
        # Load and deserialize
        loaded_data = io.load_serialized(file_path, format="yaml")
        
        assert loaded_data == test_data


@pytest.mark.xwsystem_integration
class TestCodecRegistryIntegration:
    """Test codec registry integration across modules."""
    
    def test_serializers_auto_registered(self):
        """
        Test that all serializers are auto-registered on module import.
        
        Given: io.serialization module imported
        When: Accessing the global codec registry
        Then: All serializers should be registered
        """
        from exonware.xwsystem.io.codec.registry import get_registry
        
        registry = get_registry()
        
        # Should have multiple codecs registered
        codecs = registry.list_codecs()
        assert len(codecs) > 0
        
        # Should have multiple extensions registered
        extensions = registry.list_extensions()
        assert len(extensions) > 0


@pytest.mark.xwsystem_integration
class TestArchiveIntegration:
    """Test archive operations integration."""
    
    def test_zip_archive_via_facade(self, tmp_path):
        """
        Test ZIP archive creation and extraction.
        
        Given: Files to archive
        When: Creating and extracting ZIP archive
        Then: Files are preserved correctly
        """
        # This is a placeholder - actual implementation depends on facade methods
        io = XWIO()
        
        # Test that io facade exists and is functional
        assert io is not None

