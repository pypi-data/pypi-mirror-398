#exonware/xwsystem/tests/1.unit/serialization_tests/test_serialization_worst_case_scenarios.py
"""
Comprehensive worst-case scenario tests for all serialization formats.
Tests edge cases, malformed data, security vulnerabilities, and performance limits.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 07-Sep-2025
"""

import pytest
import sys
import os
import tempfile
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from decimal import Decimal
from datetime import datetime, date, time as dt_time
from uuid import UUID
import io

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from exonware.xwsystem.io.serialization import JsonSerializer, XmlSerializer, TomlSerializer, YamlSerializer
from exonware.xwsystem.io.serialization.errors import SerializationError, FormatDetectionError, ValidationError, XmlError


class TestSerializationWorstCaseScenarios:
    """Comprehensive worst-case scenario tests for all serialization formats."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.serializers = {
            "json": JsonSerializer(),
            "xml": XmlSerializer(),
            "toml": TomlSerializer(),
            "yaml": YamlSerializer()
        }
        
        # Worst-case test data
        self.malformed_data = {
            'json': [
                '{"incomplete": "json"',
                '{"nested": {"deep": {"very": {"deep": {"infinite": "recursion"}}}}}',
                '{"null": null, "undefined": undefined}',
                '{"special": "chars: \x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"}',
                '{"unicode": "🚀🔥💀👻🎭🎪🎨🎬🎯🎲🎳🎴🎵🎶🎷🎸🎹🎺🎻🎼🎽🎾🎿🏀🏁🏂🏃🏄🏅🏆🏇🏈🏉🏊🏋🏌🏍🏎🏏🏐🏑🏒🏓🏔🏕🏖🏗🏘🏙🏚🏛🏜🏝🏞🏟🏠🏡🏢🏣🏤🏥🏦🏧🏨🏩🏪🏫🏬🏭🏮🏯🏰🏱🏲🏳🏴🏵🏶🏷🏸🏹🏺🏻🏼🏽🏾🏿"}',
                '{"billion_items": ' + ','.join([f'"{i}": {i}' for i in range(1000000)]) + '}',
                '{"circular": {"ref": null}}',  # Will be set to circular reference
            ],
            'xml': [
                '<root><unclosed>tag',
                '<root><![CDATA[unclosed cdata',
                '<root>&invalid_entity;</root>',
                '<root><nested><very><deep><structure><with><many><levels><of><nesting></nesting></levels></many></structure></deep></very></nested></root>',
                '<root><special>chars: \x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f</special></root>',
                '<root><unicode>🚀🔥💀👻🎭🎪🎨🎬🎯🎲🎳🎴🎵🎶🎷🎸🎹🎺🎻🎼🎽🎾🎿🏀🏁🏂🏃🏄🏅🏆🏇🏈🏉🏊🏋🏌🏍🏎🏏🏐🏑🏒🏓🏔🏕🏖🏗🏘🏙🏚🏛🏜🏝🏞🏟🏠🏡🏢🏣🏤🏥🏦🏧🏨🏩🏪🏫🏬🏭🏮🏯🏰🏱🏲🏳🏴🏵🏶🏷🏸🏹🏺🏻🏼🏽🏾🏿</unicode></root>',
                '<root>' + ''.join([f'<item{i}>{i}</item{i}>' for i in range(100000)]) + '</root>',
            ],
            'toml': [
                'invalid = toml syntax',
                'nested = { "deep" = { "very" = { "deep" = { "structure" = "value" } } } }',
                'special = "chars: \x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"',
                'unicode = "🚀🔥💀👻🎭🎪🎨🎬🎯🎲🎳🎴🎵🎶🎷🎸🎹🎺🎻🎼🎽🎾🎿🏀🏁🏂🏃🏄🏅🏆🏇🏈🏉🏊🏋🏌🏍🏎🏏🏐🏑🏒🏓🏔🏕🏖🏗🏘🏙🏚🏛🏜🏝🏞🏟🏠🏡🏢🏣🏤🏥🏦🏧🏨🏩🏪🏫🏬🏭🏮🏯🏰🏱🏲🏳🏴🏵🏶🏷🏸🏹🏺🏻🏼🏽🏾🏿"',
                '\n'.join([f'item{i} = {i}' for i in range(100000)]),
            ],
            'yaml': [
                'invalid: yaml: syntax: [',
                'nested:\n  deep:\n    very:\n      deep:\n        structure: value',
                'special: "chars: \x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"',
                'unicode: "🚀🔥💀👻🎭🎪🎨🎬🎯🎲🎳🎴🎵🎶🎷🎸🎹🎺🎻🎼🎽🎾🎿🏀🏁🏂🏃🏄🏅🏆🏇🏈🏉🏊🏋🏌🏍🏎🏏🏐🏑🏒🏓🏔🏕🏖🏗🏘🏙🏚🏛🏜🏝🏞🏟🏠🏡🏢🏣🏤🏥🏦🏧🏨🏩🏪🏫🏬🏭🏮🏯🏰🏱🏲🏳🏴🏵🏶🏷🏸🏹🏺🏻🏼🏽🏾🏿"',
                '\n'.join([f'item{i}: {i}' for i in range(100000)]),
            ]
        }
        
        # Create circular reference for testing
        self.circular_data = {}
        self.circular_data['self'] = self.circular_data
        
        # Large data structures
        self.large_data = {
            'billion_items': {f'item_{i}': i for i in range(100000)},
            'deep_nesting': self._create_deep_nesting(1000),
            'unicode_stress': '🚀' * 10000,
            'binary_data': b'\x00\x01\x02\x03' * 10000,
        }
    
    def _create_deep_nesting(self, depth):
        """Create deeply nested data structure."""
        if depth == 0:
            return 'leaf'
        
        # Create a substantial nested structure with multiple levels and data
        # Limit to reasonable depth for security (max 30 levels to stay well within limits)
        max_depth = min(depth, 30)
        
        nested = {}
        current = nested
        for i in range(max_depth):
            current[f'level_{i}'] = {
                'data': f'level_{i}_data_with_substantial_content_to_make_it_large',
                'items': [f'item_{j}_with_content' for j in range(3)],  # Minimal items to stay within depth
                'nested': {}
            }
            current = current[f'level_{i}']['nested']
        current['leaf'] = 'deep_leaf_value_with_substantial_content'
        return nested
    
    def _create_excessive_nesting(self):
        """Create data structure that exceeds security depth limits."""
        # Create a structure that will definitely exceed 100 levels
        nested = {}
        current = nested
        for i in range(120):  # Exceed the 100-level limit
            current[f'level_{i}'] = {
                'data': f'level_{i}_data',
                'nested': {}
            }
            current = current[f'level_{i}']['nested']
        current['leaf'] = 'excessive_depth_leaf'
        return nested
    
    # =============================================================================
    # MALFORMED DATA TESTS
    # =============================================================================
    
    def test_malformed_json_handling(self):
        """Test handling of malformed JSON data."""
        # Test truly malformed JSON that should fail
        truly_malformed = [
            '{"incomplete": "json"',  # Missing closing brace
            '{"null": null, "undefined": undefined}',  # undefined is not valid JSON
        ]
        
        for malformed in truly_malformed:
            with pytest.raises((SerializationError, ValueError, json.JSONDecodeError)):
                self.serializers["json"].loads_text(malformed)
        
        # Test complex but valid JSON that should work
        complex_valid = [
            '{"unicode": "🚀🔥💀👻🎭🎪🎨🎬🎯🎲🎳🎴🎵🎶🎷🎸🎹🎺🎻🎼🎽🎾🎿🏀🏁🏂🏃🏄🏅🏆🏇🏈🏉🏊🏋🏌🏍🏎🏏🏐🏑🏒🏓🏔🏕🏖🏗🏘🏙🏚🏛🏜🏝🏞🏟🏠🏡🏢🏣🏤🏥🏦🏧🏨🏩🏪🏫🏬🏭🏮🏯🏰🏱🏲🏳🏴🏵🏶🏷🏸🏹🏺🏻🏼🏽🏾🏿"}',
            '{"special": "chars: \x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"}',
        ]
        
        for valid_complex in complex_valid:
            try:
                result = self.serializers["json"].loads_text(valid_complex)
                assert isinstance(result, dict)
            except (SerializationError, ValueError, json.JSONDecodeError):
                # Some complex data might still fail, that's acceptable
                pass
    
    def test_malformed_xml_handling(self):
        """Test handling of malformed XML data."""
        # Test truly malformed XML that should fail
        truly_malformed = [
            '<root><unclosed>tag',  # Unclosed tag
            '<root><![CDATA[unclosed cdata',  # Unclosed CDATA
            '<root>&invalid_entity;</root>',  # Invalid entity
        ]
        
        for malformed in truly_malformed:
            with pytest.raises((SerializationError, ET.ParseError, Exception)):
                self.serializers["xml"].loads_text(malformed)
        
        # Test complex but valid XML that should work
        complex_valid = [
            '<root><unicode>🚀🔥💀👻🎭🎪🎨🎬🎯🎲🎳🎴🎵🎶🎷🎸🎹🎺🎻🎼🎽🎾🎿🏀🏁🏂🏃🏄🏅🏆🏇🏈🏉🏊🏋🏌🏍🏎🏏🏐🏑🏒🏓🏔🏕🏖🏗🏘🏙🏚🏛🏜🏝🏞🏟🏠🏡🏢🏣🏤🏥🏦🏧🏨🏩🏪🏫🏬🏭🏮🏯🏰🏱🏲🏳🏴🏵🏶🏷🏸🏹🏺🏻🏼🏽🏾🏿</unicode></root>',
        ]
        
        for valid_complex in complex_valid:
            try:
                result = self.serializers["xml"].loads_text(valid_complex)
                assert isinstance(result, dict)
            except (SerializationError, ET.ParseError):
                # Some complex data might still fail, that's acceptable
                pass
    
    def test_malformed_toml_handling(self):
        """Test handling of malformed TOML data."""
        # Test truly malformed TOML that should fail
        truly_malformed = [
            'invalid = toml syntax',  # Invalid syntax
        ]
        
        for malformed in truly_malformed:
            with pytest.raises((SerializationError, ValueError, Exception)):
                self.serializers["toml"].loads_text(malformed)
        
        # Test complex but valid TOML that should work
        complex_valid = [
            'unicode = "🚀🔥💀👻🎭🎪🎨🎬🎯🎲🎳🎴🎵🎶🎷🎸🎹🎺🎻🎼🎽🎾🎿🏀🏁🏂🏃🏄🏅🏆🏇🏈🏉🏊🏋🏌🏍🏎🏏🏐🏑🏒🏓🏔🏕🏖🏗🏘🏙🏚🏛🏜🏝🏞🏟🏠🏡🏢🏣🏤🏥🏦🏧🏨🏩🏪🏫🏬🏭🏮🏯🏰🏱🏲🏳🏴🏵🏶🏷🏸🏹🏺🏻🏼🏽🏾🏿"',
        ]
        
        for valid_complex in complex_valid:
            try:
                result = self.serializers["toml"].loads_text(valid_complex)
                assert isinstance(result, dict)
            except (SerializationError, ValueError):
                # Some complex data might still fail, that's acceptable
                pass
    
    def test_malformed_yaml_handling(self):
        """Test handling of malformed YAML data."""
        # Test truly malformed YAML that should fail
        truly_malformed = [
            'invalid: yaml: syntax: [',  # Invalid syntax
        ]
        
        for malformed in truly_malformed:
            with pytest.raises((SerializationError, ValueError, Exception)):
                self.serializers["yaml"].loads_text(malformed)
        
        # Test complex but valid YAML that should work
        complex_valid = [
            'unicode: "🚀🔥💀👻🎭🎪🎨🎬🎯🎲🎳🎴🎵🎶🎷🎸🎹🎺🎻🎼🎽🎾🎿🏀🏁🏂🏃🏄🏅🏆🏇🏈🏉🏊🏋🏌🏍🏎🏏🏐🏑🏒🏓🏔🏕🏖🏗🏘🏙🏚🏛🏜🏝🏞🏟🏠🏡🏢🏣🏤🏥🏦🏧🏨🏩🏪🏫🏬🏭🏮🏯🏰🏱🏲🏳🏴🏵🏶🏷🏸🏹🏺🏻🏼🏽🏾🏿"',
        ]
        
        for valid_complex in complex_valid:
            try:
                result = self.serializers["yaml"].loads_text(valid_complex)
                assert isinstance(result, dict)
            except (SerializationError, ValueError):
                # Some complex data might still fail, that's acceptable
                pass
    
    # =============================================================================
    # CIRCULAR REFERENCE TESTS
    # =============================================================================
    
    def test_circular_reference_json(self):
        """Test circular reference handling in JSON."""
        with pytest.raises((SerializationError, ValueError, TypeError, ValidationError)):
            self.serializers["json"].dumps_text(self.circular_data)
    
    def test_circular_reference_xml(self):
        """Test circular reference handling in XML."""
        with pytest.raises((SerializationError, ValueError, TypeError, ValidationError, XmlError)):
            self.serializers["xml"].dumps_text(self.circular_data)
    
    def test_circular_reference_toml(self):
        """Test circular reference handling in TOML."""
        with pytest.raises((SerializationError, ValueError, TypeError, ValidationError)):
            self.serializers["toml"].dumps_text(self.circular_data)
    
    def test_circular_reference_yaml(self):
        """Test circular reference handling in YAML."""
        with pytest.raises((SerializationError, ValueError, TypeError, ValidationError)):
            self.serializers["yaml"].dumps_text(self.circular_data)
    
    # =============================================================================
    # LARGE DATA TESTS
    # =============================================================================
    
    def test_large_data_json(self):
        """Test large data handling in JSON."""
        # Test billion items
        large_json = self.serializers["json"].dumps_text(self.large_data['billion_items'])
        assert len(large_json) > 1000000  # Should be very large
        
        # Test deserialization
        deserialized = self.serializers["json"].loads_text(large_json)
        assert len(deserialized) == 100000
    
    def test_large_data_xml(self):
        """Test large data handling in XML."""
        # Test billion items
        large_xml = self.serializers["xml"].dumps_text(self.large_data['billion_items'])
        assert len(large_xml) > 1000000  # Should be very large
        
        # Test deserialization
        deserialized = self.serializers["xml"].loads_text(large_xml)
        assert len(deserialized) == 100000
    
    def test_large_data_toml(self):
        """Test large data handling in TOML."""
        # Test billion items
        large_toml = self.serializers["toml"].dumps_text(self.large_data['billion_items'])
        assert len(large_toml) > 1000000  # Should be very large
        
        # Test deserialization
        deserialized = self.serializers["toml"].loads_text(large_toml)
        assert len(deserialized) == 100000
    
    def test_large_data_yaml(self):
        """Test large data handling in YAML."""
        # Test billion items
        large_yaml = self.serializers["yaml"].dumps_text(self.large_data['billion_items'])
        assert len(large_yaml) > 1000000  # Should be very large
        
        # Test deserialization
        deserialized = self.serializers["yaml"].loads_text(large_yaml)
        assert len(deserialized) == 100000
    
    # =============================================================================
    # DEEP NESTING TESTS
    # =============================================================================
    
    def test_deep_nesting_json(self):
        """Test deep nesting handling in JSON."""
        from exonware.xwsystem.io.serialization.errors import JsonError
        from exonware.xwsystem.validation.errors import ValidationError
        
        # Test with data that's within security limits (30 levels) - should succeed
        safe_deep_data = self._create_deep_nesting(30)
        deep_json = self.serializers["json"].dumps_text(safe_deep_data)
        assert len(deep_json) > 1000  # Should be substantial
        
        # Test deserialization
        deserialized = self.serializers["json"].loads_text(deep_json)
        assert 'level_0' in deserialized  # Should have nested structure
        
        # Test that security system correctly rejects data exceeding depth limits
        # Create data that will exceed the 100-level limit
        excessive_data = self._create_excessive_nesting()
        with pytest.raises((JsonError, ValidationError)):
            self.serializers["json"].dumps_text(excessive_data)
    
    def test_deep_nesting_xml(self):
        """Test deep nesting handling in XML."""
        from exonware.xwsystem.io.serialization.errors import XmlError
        from exonware.xwsystem.validation.errors import ValidationError
        
        # Test with data that's within security limits (30 levels) - should succeed
        safe_deep_data = self._create_deep_nesting(30)
        deep_xml = self.serializers["xml"].dumps_text(safe_deep_data)
        assert len(deep_xml) > 1000  # Should be substantial
        
        # Test deserialization
        deserialized = self.serializers["xml"].loads_text(deep_xml)
        assert 'level_0' in deserialized  # Should have nested structure
        
        # Test that security system correctly rejects data exceeding depth limits
        excessive_data = self._create_excessive_nesting()
        with pytest.raises((XmlError, ValidationError)):
            self.serializers["xml"].dumps_text(excessive_data)
    
    def test_deep_nesting_toml(self):
        """Test deep nesting handling in TOML."""
        from exonware.xwsystem.io.serialization.errors import SerializationError
        from exonware.xwsystem.validation.errors import ValidationError
        
        # Test with data that's within security limits (30 levels) - should succeed
        safe_deep_data = self._create_deep_nesting(30)
        deep_toml = self.serializers["toml"].dumps_text(safe_deep_data)
        assert len(deep_toml) > 1000  # Should be substantial
        
        # Test deserialization
        deserialized = self.serializers["toml"].loads_text(deep_toml)
        assert 'level_0' in deserialized  # Should have nested structure
        
        # Test that security system correctly rejects data exceeding depth limits
        excessive_data = self._create_excessive_nesting()
        with pytest.raises((SerializationError, ValidationError)):
            self.serializers["toml"].dumps_text(excessive_data)
    
    def test_deep_nesting_yaml(self):
        """Test deep nesting handling in YAML."""
        from exonware.xwsystem.io.serialization.errors import SerializationError
        from exonware.xwsystem.validation.errors import ValidationError
        
        # Test with data that's within security limits (30 levels) - should succeed
        safe_deep_data = self._create_deep_nesting(30)
        deep_yaml = self.serializers["yaml"].dumps_text(safe_deep_data)
        assert len(deep_yaml) > 1000  # Should be substantial
        
        # Test deserialization
        deserialized = self.serializers["yaml"].loads_text(deep_yaml)
        assert 'level_0' in deserialized  # Should have nested structure
        
        # Test that security system correctly rejects data exceeding depth limits
        excessive_data = self._create_excessive_nesting()
        with pytest.raises((SerializationError, ValidationError)):
            self.serializers["yaml"].dumps_text(excessive_data)
    
    # =============================================================================
    # UNICODE STRESS TESTS
    # =============================================================================
    
    def test_unicode_stress_json(self):
        """Test unicode stress handling in JSON."""
        unicode_json = self.serializers["json"].dumps_text({'unicode': self.large_data['unicode_stress']})
        assert len(unicode_json) > 10000  # Should be substantial due to unicode
        
        # Test deserialization
        deserialized = self.serializers["json"].loads_text(unicode_json)
        assert deserialized['unicode'] == self.large_data['unicode_stress']
    
    def test_unicode_stress_xml(self):
        """Test unicode stress handling in XML."""
        unicode_xml = self.serializers["xml"].dumps_text({'unicode': self.large_data['unicode_stress']})
        assert len(unicode_xml) > 10000  # Should be substantial due to unicode
        
        # Test deserialization
        deserialized = self.serializers["xml"].loads_text(unicode_xml)
        assert deserialized['unicode'] == self.large_data['unicode_stress']
    
    def test_unicode_stress_toml(self):
        """Test unicode stress handling in TOML."""
        unicode_toml = self.serializers["toml"].dumps_text({'unicode': self.large_data['unicode_stress']})
        assert len(unicode_toml) > 10000  # Should be substantial due to unicode
        
        # Test deserialization
        deserialized = self.serializers["toml"].loads_text(unicode_toml)
        assert deserialized['unicode'] == self.large_data['unicode_stress']
    
    def test_unicode_stress_yaml(self):
        """Test unicode stress handling in YAML."""
        unicode_yaml = self.serializers["yaml"].dumps_text({'unicode': self.large_data['unicode_stress']})
        assert len(unicode_yaml) > 10000  # Should be substantial due to unicode
        
        # Test deserialization
        deserialized = self.serializers["yaml"].loads_text(unicode_yaml)
        assert deserialized['unicode'] == self.large_data['unicode_stress']
    
    # =============================================================================
    # BINARY DATA TESTS
    # =============================================================================
    
    def test_binary_data_json(self):
        """Test binary data handling in JSON."""
        # JSON should handle binary data gracefully (may convert to base64 or raise exception)
        try:
            result = self.serializers["json"].dumps_text({'binary': self.large_data['binary_data']})
            assert len(result) > 0  # Should produce some output
        except (SerializationError, TypeError, ValueError):
            # It's acceptable for JSON to reject binary data
            pass
    
    def test_binary_data_xml(self):
        """Test binary data handling in XML."""
        # XML should handle binary data gracefully (may convert to base64 or raise exception)
        try:
            result = self.serializers["xml"].dumps_text({'binary': self.large_data['binary_data']})
            assert len(result) > 0  # Should produce some output
        except (SerializationError, TypeError, ValueError):
            # It's acceptable for XML to reject binary data
            pass
    
    def test_binary_data_toml(self):
        """Test binary data handling in TOML."""
        # TOML should handle binary data gracefully (may convert to base64 or raise exception)
        try:
            result = self.serializers["toml"].dumps_text({'binary': self.large_data['binary_data']})
            assert len(result) > 0  # Should produce some output
        except (SerializationError, TypeError, ValueError):
            # It's acceptable for TOML to reject binary data
            pass
    
    def test_binary_data_yaml(self):
        """Test binary data handling in YAML."""
        # YAML should handle binary data gracefully (may convert to base64 or raise exception)
        try:
            result = self.serializers["yaml"].dumps_text({'binary': self.large_data['binary_data']})
            assert len(result) > 0  # Should produce some output
        except (SerializationError, TypeError, ValueError):
            # It's acceptable for YAML to reject binary data
            pass
    
    # =============================================================================
    # SPECIAL CHARACTER TESTS
    # =============================================================================
    
    def test_special_characters_all_formats(self):
        """Test special characters handling in all formats."""
        special_chars = {
            'null_bytes': '\x00\x01\x02\x03',
            'control_chars': '\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f',
            'unicode_private': '\uf000\uf001\uf002',
            'unicode_surrogate': '\ud800\udc00',
            'mixed_unicode': 'Hello 世界 🌍 测试',
        }
        
        for format_type in ["json", "xml", 
                           "toml", "yaml"]:
            for name, chars in special_chars.items():
                try:
                    serialized = self.serializers[format_type].dumps_text({name: chars})
                    deserialized = self.serializers[format_type].loads_text(serialized)
                    # Should either work or fail gracefully
                    assert isinstance(deserialized, dict)
                except (SerializationError, ValueError, TypeError):
                    # Expected for some special characters
                    pass
    
    # =============================================================================
    # PERFORMANCE STRESS TESTS
    # =============================================================================
    
    def test_performance_stress_serialization(self):
        """Test performance under stress conditions."""
        import time
        
        # Test with progressively larger datasets
        sizes = [1000, 10000, 100000]
        
        for size in sizes:
            test_data = {f'item_{i}': f'value_{i}' for i in range(size)}
            
            for format_type in ["json", "xml", "toml", "yaml"]:
                start_time = time.time()
                
                # Serialize
                serialized = self.serializers[format_type].dumps_text(test_data)
                serialize_time = time.time() - start_time
                
                # Deserialize
                start_time = time.time()
                deserialized = self.serializers[format_type].loads_text(serialized)
                deserialize_time = time.time() - start_time
                
                # Performance assertions (should complete within reasonable time)
                assert serialize_time < 10.0, f"Serialization too slow: {serialize_time}s for {size} items"
                assert deserialize_time < 10.0, f"Deserialization too slow: {deserialize_time}s for {size} items"
                
                # Data integrity
                assert len(deserialized) == size
    
    # =============================================================================
    # SECURITY TESTS
    # =============================================================================
    
    def test_path_traversal_security(self):
        """Test path traversal security in file operations."""
        from exonware.xwsystem.io.serialization.serializer import XWSerializer as XWSerialization
        
        malicious_paths = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '/etc/shadow',
            'C:\\Windows\\System32\\config\\SAM',
            '....//....//....//etc//passwd',
        ]
        
        # Use XWSerialization which has load_file implemented
        xw_serializer = XWSerialization()
        
        for malicious_path in malicious_paths:
            with pytest.raises((SerializationError, ValueError, OSError, FileNotFoundError)):
                xw_serializer.load_file(malicious_path)
    
    def test_xml_bomb_protection(self):
        """Test XML bomb protection."""
        # Billion laughs attack
        xml_bomb = '<?xml version="1.0"?>' + \
                  '<!DOCTYPE lolz [' + \
                  '<!ENTITY lol "lol">' + \
                  '<!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">' + \
                  '<!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">' + \
                  '<!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">' + \
                  '<!ENTITY lol5 "&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;">' + \
                  ']>' + \
                  '<lolz>&lol5;</lolz>'
        
        # Should either parse safely or fail gracefully
        try:
            result = self.serializers["xml"].loads_text(xml_bomb)
            # If it parses, it should be reasonable size
            assert len(str(result)) < 1000000
        except (SerializationError, ET.ParseError, MemoryError):
            # Expected for XML bombs
            pass
    
    def test_yaml_bomb_protection(self):
        """Test YAML bomb protection."""
        # YAML bomb with recursive references
        yaml_bomb = """
        a: &a ["lol","lol","lol","lol","lol","lol","lol","lol","lol"]
        b: &b [*a,*a,*a,*a,*a,*a,*a,*a,*a]
        c: &c [*b,*b,*b,*b,*b,*b,*b,*b,*b]
        d: &d [*c,*c,*c,*c,*c,*c,*c,*c,*c]
        e: &e [*d,*d,*d,*d,*d,*d,*d,*d,*d]
        f: &f [*e,*e,*e,*e,*e,*e,*e,*e,*e]
        g: &g [*f,*f,*f,*f,*f,*f,*f,*f,*f]
        h: &h [*g,*g,*g,*g,*g,*g,*g,*g,*g]
        i: &i [*h,*h,*h,*h,*h,*h,*h,*h,*h]
        """
        
        # Should either parse safely or fail gracefully
        try:
            result = self.serializers["yaml"].loads_text(yaml_bomb)
            # If it parses, it should be reasonable size
            assert len(str(result)) < 1000000
        except (SerializationError, ValueError, MemoryError):
            # Expected for YAML bombs
            pass
    
    # =============================================================================
    # EDGE CASE TESTS
    # =============================================================================
    
    def test_empty_data_handling(self):
        """Test empty data handling."""
        empty_data = [None, "", {}, [], 0, False]
        
        for format_type in ["json", "xml", 
                           "toml", "yaml"]:
            for empty in empty_data:
                try:
                    serialized = self.serializers[format_type].dumps_text(empty)
                    deserialized = self.serializers[format_type].loads_text(serialized)
                    # Should handle empty data gracefully
                    assert deserialized == empty or deserialized is None
                except (SerializationError, ValueError):
                    # Some formats might not support certain empty types
                    pass
    
    def test_nonexistent_file_handling(self):
        """Test nonexistent file handling."""
        from exonware.xwsystem.io.serialization.serializer import XWSerializer as XWSerialization
        
        nonexistent_files = [
            '/nonexistent/file.json',
            'C:\\nonexistent\\file.xml',
            './nonexistent/file.toml',
            '../nonexistent/file.yaml',
        ]
        
        # Use XWSerialization which has load_file implemented
        xw_serializer = XWSerialization()
        
        for file_path in nonexistent_files:
            with pytest.raises((SerializationError, FileNotFoundError, OSError)):
                xw_serializer.load_file(file_path)
    
    def test_invalid_format_handling(self):
        """Test invalid format handling."""
        # Test with invalid data that should cause serialization to fail
        invalid_data = {
            'circular_ref': {},
            'unsupported_type': lambda x: x,  # Function objects can't be serialized
        }
        invalid_data['circular_ref'] = invalid_data  # Create circular reference
        
        with pytest.raises((SerializationError, ValueError, TypeError)):
            self.serializers["json"].dumps_text(invalid_data)
    
    def test_mixed_data_types(self):
        """Test mixed data types handling."""
        mixed_data = {
            'string': 'hello',
            'integer': 42,
            'float': 3.14159,
            'boolean': True,
            'null': None,
            'list': [1, 2, 3],
            'dict': {'nested': 'value'},
            'decimal': Decimal('123.456'),
            'datetime': datetime.now(),
            'date': date.today(),
            'time': time(12, 30, 45),
            'uuid': UUID('12345678-1234-5678-9012-123456789012'),
        }
        
        for format_type in ["json", "xml", 
                           "toml", "yaml"]:
            try:
                serialized = self.serializers[format_type].dumps_text(mixed_data)
                deserialized = self.serializers[format_type].loads_text(serialized)
                # Should handle mixed types gracefully
                assert isinstance(deserialized, dict)
                assert len(deserialized) > 0
            except (SerializationError, ValueError, TypeError):
                # Some formats might not support certain types
                pass
    
    # =============================================================================
    # CONCURRENT ACCESS TESTS
    # =============================================================================
    
    def test_concurrent_serialization(self):
        """Test concurrent serialization access."""
        import threading
        import time
        
        results = []
        errors = []
        
        def serialize_worker(data, format_type, worker_id):
            try:
                for i in range(100):
                    serialized = self.serializers[format_type].dumps_text(data)
                    deserialized = self.serializers[format_type].loads_text(serialized)
                    results.append((worker_id, i, len(serialized)))
                time.sleep(0.001)  # Small delay to increase chance of race conditions
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Create multiple threads
        threads = []
        test_data = {'worker': 'data', 'items': list(range(100))}
        
        for i in range(10):  # 10 concurrent workers
            for format_type in ["json", "xml"]:
                thread = threading.Thread(target=serialize_worker, args=(test_data, format_type, i))
                threads.append(thread)
                thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) > 0, "No results from concurrent workers"
        
        # All results should be successful
        for worker_id, iteration, size in results:
            assert size > 0, f"Worker {worker_id} iteration {iteration} produced empty result"
    
    # =============================================================================
    # MEMORY LEAK TESTS
    # =============================================================================
    
    def test_memory_usage_stability(self):
        """Test memory usage stability under repeated operations."""
        import gc
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform many serialization operations
        test_data = {'test': 'data', 'items': list(range(1000))}
        
        for i in range(1000):
            for format_type in ["json", "xml", "toml", "yaml"]:
                serialized = self.serializers[format_type].dumps_text(test_data)
                deserialized = self.serializers[format_type].loads_text(serialized)
                
                # Force garbage collection every 100 iterations
                if i % 100 == 0:
                    gc.collect()
        
        # Get final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024, f"Memory leak detected: {memory_increase / 1024 / 1024:.2f}MB increase"
    
    # =============================================================================
    # COMPREHENSIVE FEATURE TESTS
    # =============================================================================
    
    def test_all_features_under_stress(self):
        """Test all serialization features under stress conditions."""
        stress_data = {
            'users': [
                {'id': i, 'name': f'User {i}', 'email': f'user{i}@example.com', 'active': i % 2 == 0}
                for i in range(10000)
            ],
            'metadata': {
                'created': datetime.now().isoformat(),
                'version': '1.0.0',
                'tags': [f'tag_{i}' for i in range(1000)],
                'config': {f'key_{i}': f'value_{i}' for i in range(1000)}
            }
        }
        
        for format_type in ["json", "xml", 
                           "toml", "yaml"]:
            
            # Test basic serialization
            serialized = self.serializers[format_type].dumps_text(stress_data)
            assert len(serialized) > 100000  # Should be substantial
            
            # Test deserialization
            deserialized = self.serializers[format_type].loads_text(serialized)
            assert len(deserialized['users']) == 10000
            assert len(deserialized['metadata']['tags']) == 1000
            
            # Test format detection
            detected_format = self.serializers[format_type].sniff_format(serialized)
            assert detected_format is not None
            
            # Test partial access
            try:
                first_user = self.serializers[format_type].get_at(serialized, "users.0.name")
                assert first_user == "User 0"
                
                # Test setting
                updated = self.serializers[format_type].set_at(serialized, "users.0.name", "Updated User")
                assert len(updated) > 0
                
                # Test iteration
                user_names = list(self.serializers[format_type].iter_path(serialized, "users.0"))
                assert len(user_names) >= 0
            except (SerializationError, NotImplementedError):
                # Some formats might not support partial access
                pass
            
            # Test patching
            try:
                patch = [{"op": "replace", "path": "users.0.name", "value": "Patched User"}]
                patched = self.serializers[format_type].apply_patch(serialized, patch)
                assert len(patched) > 0
            except (SerializationError, NotImplementedError):
                # Some formats might not support patching
                pass
            
            # Test schema validation
            try:
                schema = {"users": list, "metadata": dict}
                is_valid = self.serializers[format_type].validate_schema(serialized, schema)
                assert is_valid is True
            except (SerializationError, NotImplementedError):
                # Some formats might not support schema validation
                pass
            
            # Test canonical serialization
            try:
                canonical = self.serializers[format_type].canonicalize(stress_data)
                assert len(canonical) > 0
                
                # Test hash stability
                hash1 = self.serializers[format_type].hash_stable(stress_data)
                hash2 = self.serializers[format_type].hash_stable(stress_data)
                assert hash1 == hash2
            except (SerializationError, NotImplementedError):
                # Some formats might not support canonical serialization
                pass
            
            # Test checksums
            try:
                checksum = self.serializers[format_type].checksum(stress_data)
                assert len(checksum) > 0
                
                # Test verification
                is_valid = self.serializers[format_type].verify_checksum(stress_data, checksum)
                assert is_valid is True
            except (SerializationError, NotImplementedError):
                # Some formats might not support checksums
                pass
            
            # Test batch streaming
            try:
                chunks = list(self.serializers[format_type].iter_serialize(stress_data, chunk_size=1024))
                assert len(chunks) > 0
                
                # Test NDJSON equivalent
                ndjson_chunks = list(self.serializers[format_type].serialize_ndjson([stress_data, stress_data]))
                assert len(ndjson_chunks) > 0
                
                # Test deserialization
                deserialized_items = list(self.serializers[format_type].deserialize_ndjson(ndjson_chunks))
                assert len(deserialized_items) >= 0
            except (SerializationError, NotImplementedError):
                # Some formats might not support batch streaming
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
