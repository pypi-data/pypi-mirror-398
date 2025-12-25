"""
Unit tests for io.serialization.registry module

Tests the SerializationRegistry.
Following GUIDELINES_TEST.md structure and eXonware testing standards.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
"""

import pytest
from exonware.xwsystem.io.serialization.registry import SerializationRegistry, get_serialization_registry


@pytest.mark.xwsystem_unit
class TestSerializationRegistry:
    """Test SerializationRegistry functionality."""
    
    def test_registry_can_be_instantiated(self):
        """Test that SerializationRegistry can be created."""
        registry = SerializationRegistry()
        assert registry is not None
    
    def test_get_serialization_registry_function(self):
        """Test global serialization registry accessor."""
        registry = get_serialization_registry()
        assert registry is not None
        assert isinstance(registry, SerializationRegistry)
    
    def test_registry_has_lookup_methods(self):
        """Test that registry has serialization-specific lookup methods."""
        registry = SerializationRegistry()
        assert hasattr(registry, 'get_by_format')
        assert hasattr(registry, 'detect_from_file')
        assert hasattr(registry, 'get_by_extension')
        assert hasattr(registry, 'get_by_mime_type')
    
    def test_registry_has_listing_methods(self):
        """Test that registry has listing methods."""
        registry = SerializationRegistry()
        assert hasattr(registry, 'list_formats')
        assert hasattr(registry, 'list_extensions')
        assert hasattr(registry, 'list_mime_types')


@pytest.mark.xwsystem_unit
class TestSerializationRegistryIntegration:
    """Test SerializationRegistry integration with UniversalCodecRegistry."""
    
    def test_registry_delegates_to_universal_registry(self):
        """Test that SerializationRegistry uses UniversalCodecRegistry."""
        registry = get_serialization_registry()
        
        # Should be able to list formats (delegates to universal registry)
        formats = registry.list_formats()
        assert formats is not None

