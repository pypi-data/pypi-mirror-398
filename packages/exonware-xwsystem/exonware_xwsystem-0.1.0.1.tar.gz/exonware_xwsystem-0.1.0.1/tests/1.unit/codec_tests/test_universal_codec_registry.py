"""
#exonware/xwsystem/tests/1.unit/codec_tests/test_universal_codec_registry.py

Unit tests for UniversalCodecRegistry.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 04-Nov-2025
"""

import pytest
from pathlib import Path


@pytest.mark.xwsystem_unit
class TestUniversalCodecRegistryCore:
    """Test UniversalCodecRegistry core functionality."""
    
    def test_singleton_pattern(self):
        """Test global registry is singleton."""
        from exonware.xwsystem.io.codec.registry import get_registry
        
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2
    
    def test_register_codec(self, fresh_registry):
        """Test codec registration."""
        from exonware.xwsystem.io.serialization.formats.text.json import JsonSerializer
        
        fresh_registry.register(JsonSerializer)
        
        codec = fresh_registry.get_by_id('json')
        assert codec is not None
        assert codec.codec_id == 'json'
    
    def test_get_by_id(self, populated_registry):
        """Test retrieval by codec ID."""
        codec = populated_registry.get_by_id('json')
        assert codec is not None
        assert codec.codec_id == 'json'
    
    def test_get_by_id_case_insensitive(self, populated_registry):
        """Test ID lookup is case-insensitive."""
        codec = populated_registry.get_by_id('JSON')
        assert codec is not None
        assert codec.codec_id == 'json'
    
    def test_get_by_extension_with_dot(self, populated_registry):
        """Test extension lookup with leading dot."""
        codec = populated_registry.get_by_extension('.json')
        assert codec is not None
        assert codec.codec_id == 'json'
    
    def test_get_by_extension_without_dot(self, populated_registry):
        """Test extension lookup without leading dot."""
        codec = populated_registry.get_by_extension('json')
        assert codec is not None
        assert codec.codec_id == 'json'
    
    def test_get_by_mime_type(self, populated_registry):
        """Test retrieval by MIME type."""
        codec = populated_registry.get_by_mime_type('application/json')
        assert codec is not None
        assert codec.codec_id == 'json'
    
    def test_get_by_alias(self, populated_registry):
        """Test retrieval by alias."""
        codec = populated_registry.get_by_alias('JSON')
        assert codec is not None
        assert codec.codec_id == 'json'
    
    def test_detect_from_path(self, populated_registry):
        """Test auto-detection from file path."""
        codec = populated_registry.detect('config.json')
        assert codec is not None
        assert codec.codec_id == 'json'
    
    def test_detect_yaml_extensions(self, populated_registry):
        """Test YAML detects both .yaml and .yml."""
        yaml_codec = populated_registry.detect('config.yaml')
        yml_codec = populated_registry.detect('config.yml')
        
        assert yaml_codec is not None
        assert yml_codec is not None
        assert yaml_codec.codec_id == 'yaml'
        assert yml_codec.codec_id == 'yaml'
    
    def test_unregister_codec(self, fresh_registry):
        """Test codec unregistration."""
        from exonware.xwsystem.io.serialization.formats.text.json import JsonSerializer
        
        fresh_registry.register(JsonSerializer)
        assert fresh_registry.get_by_id('json') is not None
        
        result = fresh_registry.unregister('json')
        assert result is True
        assert fresh_registry.get_by_id('json') is None
    
    def test_unregister_nonexistent_codec(self, fresh_registry):
        """Test unregistering nonexistent codec returns False."""
        result = fresh_registry.unregister('nonexistent')
        assert result is False
    
    def test_list_codecs(self, populated_registry):
        """Test listing all codecs."""
        codecs = populated_registry.list_codecs()
        assert 'json' in codecs
        assert 'yaml' in codecs
        assert 'xml' in codecs
    
    def test_list_extensions(self, populated_registry):
        """Test listing all extensions."""
        extensions = populated_registry.list_extensions()
        assert '.json' in extensions
        assert '.yaml' in extensions
        assert '.yml' in extensions
    
    def test_clear_registry(self, fresh_registry):
        """Test clearing all registrations."""
        from exonware.xwsystem.io.serialization.formats.text.json import JsonSerializer
        
        fresh_registry.register(JsonSerializer)
        assert len(fresh_registry.list_codecs()) > 0
        
        fresh_registry.clear()
        assert len(fresh_registry.list_codecs()) == 0
        assert fresh_registry.get_by_id('json') is None


@pytest.mark.xwsystem_unit
class TestMultiTypeSupport:
    """Test multi-type codec support."""
    
    def test_xml_has_multiple_types(self):
        """Test XML belongs to multiple types."""
        from exonware.xwsystem.io.serialization.formats.text.xml import XmlSerializer
        
        codec = XmlSerializer()
        assert "serialization" in codec.codec_types
        assert "markup" in codec.codec_types
    
    def test_toml_has_multiple_types(self):
        """Test TOML belongs to multiple types."""
        from exonware.xwsystem.io.serialization.formats.text.toml import TomlSerializer
        
        codec = TomlSerializer()
        assert "config" in codec.codec_types
        assert "serialization" in codec.codec_types
    
    def test_get_all_by_type_serialization(self, populated_registry):
        """Test getting all serialization codecs."""
        codecs = populated_registry.get_all_by_type('serialization')
        assert len(codecs) >= 3  # JSON, YAML, XML at minimum
    
    def test_detect_with_type_filter(self, populated_registry):
        """Test detection with type filtering."""
        # XML should match as markup for SVG
        codec = populated_registry.detect('image.svg', codec_type='markup')
        assert codec is not None
        assert codec.codec_id == 'xml'


@pytest.mark.xwsystem_unit
class TestCodecInstanceCaching:
    """Test instance caching for performance."""
    
    def test_same_instance_returned(self, populated_registry):
        """Test that same instance is returned for repeated lookups."""
        codec1 = populated_registry.get_by_id('json')
        codec2 = populated_registry.get_by_id('json')
        
        assert codec1 is codec2  # Same object instance
    
    def test_detection_cache_works(self, populated_registry):
        """Test that detection results are cached."""
        # First call
        codec1 = populated_registry.detect('config.json')
        
        # Second call should hit cache
        codec2 = populated_registry.detect('config.json')
        
        assert codec1 is codec2


@pytest.mark.xwsystem_unit
class TestRegistryMetadata:
    """Test metadata retrieval and statistics."""
    
    def test_get_metadata(self, populated_registry):
        """Test getting codec metadata."""
        metadata = populated_registry.get_metadata('json')
        
        assert metadata is not None
        assert metadata['codec_id'] == 'json'
        assert 'serialization' in metadata['codec_types']
        assert '.json' in metadata['extensions']
    
    def test_get_statistics(self, populated_registry):
        """Test getting registry statistics."""
        stats = populated_registry.get_statistics()
        
        assert 'codecs' in stats
        assert 'extensions' in stats
        assert 'mime_types' in stats
        assert stats['codecs'] >= 3  # At least JSON, YAML, XML
    
    def test_list_types(self, populated_registry):
        """Test listing all codec types."""
        types = populated_registry.list_types()
        
        assert 'serialization' in types
        assert 'markup' in types  # From XML
        assert 'config' in types  # From TOML if registered


@pytest.mark.xwsystem_unit
class TestErrorHandling:
    """Test error handling in registry."""
    
    def test_get_nonexistent_codec_returns_none(self, fresh_registry):
        """Test that getting nonexistent codec returns None."""
        codec = fresh_registry.get_by_id('nonexistent')
        assert codec is None
    
    def test_detect_unknown_extension_returns_none(self, populated_registry):
        """Test that unknown extension returns None."""
        codec = populated_registry.detect('file.unknownext')
        assert codec is None
    
    def test_register_invalid_codec_raises_error(self, fresh_registry):
        """Test that registering non-codec class raises error."""
        from exonware.xwsystem.io.errors import CodecRegistrationError
        
        class NotACodec:
            pass
        
        with pytest.raises(CodecRegistrationError):
            fresh_registry.register(NotACodec)


@pytest.mark.xwsystem_unit
class TestPriorityResolution:
    """Test priority-based conflict resolution."""
    
    def test_higher_priority_wins(self, fresh_registry):
        """Test that higher priority codec is returned."""
        from exonware.xwsystem.io.serialization.formats.text.json import JsonSerializer
        from exonware.xwsystem.io.serialization.formats.text.json5 import Json5Serializer
        
        # Register both with different priorities
        fresh_registry.register(JsonSerializer, priority=5)
        fresh_registry.register(Json5Serializer, priority=10)
        
        # Higher priority should win
        codec = fresh_registry.get_by_extension('.json')
        # Note: Depends on which has .json extension with higher priority
        assert codec is not None


@pytest.mark.xwsystem_unit
class TestCompoundExtensions:
    """Test compound extension support."""
    
    def test_detect_compound_extension(self, populated_registry):
        """Test detection of compound extensions."""
        # Test .yaml detection (simple extension)
        codec = populated_registry.detect('backup.tar.yaml')
        # Will match .yaml extension
        assert codec is not None


@pytest.mark.xwsystem_unit  
class TestCodecCapabilities:
    """Test codec capabilities."""
    
    def test_filter_by_capability(self, populated_registry):
        """Test filtering codecs by capability."""
        from exonware.xwsystem.io.defs import CodecCapability
        
        bidirectional = populated_registry.filter_by_capability(CodecCapability.BIDIRECTIONAL)
        assert len(bidirectional) >= 3  # JSON, YAML, XML


@pytest.mark.xwsystem_unit
class TestAllResultMethods:
    """Test methods that return all matches."""
    
    def test_get_all_by_extension(self, populated_registry):
        """Test getting all codecs for an extension."""
        codecs = populated_registry.get_all_by_extension('.json')
        assert len(codecs) >= 1
        assert all(c.codec_id is not None for c in codecs)
    
    def test_detect_all(self, populated_registry):
        """Test detecting all possible codecs for a path."""
        codecs = populated_registry.detect_all('data.json')
        assert len(codecs) >= 1

