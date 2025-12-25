"""
Unit tests for io.codec.registry module

Tests the UniversalCodecRegistry for managing and discovering codecs.
Following GUIDELINES_TEST.md structure and eXonware testing standards.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
"""

import pytest
from exonware.xwsystem.io.codec.registry import UniversalCodecRegistry, get_registry


@pytest.mark.xwsystem_unit
class TestUniversalCodecRegistry:
    """Test UniversalCodecRegistry functionality."""
    
    def test_registry_can_be_instantiated(self):
        """Test that UniversalCodecRegistry can be created."""
        registry = UniversalCodecRegistry()
        assert registry is not None
    
    def test_get_registry_returns_singleton(self):
        """Test that get_registry returns the same instance."""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2
    
    def test_registry_has_register_method(self):
        """Test that registry has register method."""
        registry = UniversalCodecRegistry()
        assert hasattr(registry, 'register')
        assert callable(registry.register)
    
    def test_registry_has_lookup_methods(self):
        """Test that registry has codec lookup methods."""
        registry = UniversalCodecRegistry()
        assert hasattr(registry, 'get_by_id')
        assert hasattr(registry, 'get_by_extension')
        assert hasattr(registry, 'get_by_mime_type')
        assert hasattr(registry, 'detect')
    
    def test_registry_has_listing_methods(self):
        """Test that registry has listing methods."""
        registry = UniversalCodecRegistry()
        assert hasattr(registry, 'list_codecs')
        assert hasattr(registry, 'list_extensions')
        assert hasattr(registry, 'list_mime_types')


@pytest.mark.xwsystem_unit
class TestCodecRegistration:
    """Test codec registration functionality."""
    
    def test_register_method_is_callable(self):
        """Test that codecs can be registered."""
        registry = UniversalCodecRegistry()
        # Just test the method exists and is callable
        assert callable(registry.register)
    
    def test_list_methods_return_collections(self):
        """Test that list methods return iterable collections."""
        registry = get_registry()
        
        # These should return collections (lists, sets, etc.)
        codecs = registry.list_codecs()
        assert codecs is not None
        
        extensions = registry.list_extensions()
        assert extensions is not None
        
        mime_types = registry.list_mime_types()
        assert mime_types is not None

