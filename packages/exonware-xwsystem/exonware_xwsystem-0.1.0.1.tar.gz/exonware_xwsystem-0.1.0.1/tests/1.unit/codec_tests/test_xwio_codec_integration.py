"""
#exonware/xwsystem/tests/1.unit/codec_tests/test_xwio_codec_integration.py

Unit tests for XWIO facade codec integration.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 04-Nov-2025
"""

import pytest
from pathlib import Path
import tempfile
import os


@pytest.mark.xwsystem_unit
class TestXWIOCodecIntegration:
    """Test XWIO facade with UniversalCodecRegistry."""
    
    def test_serialize_deserialize_json(self, test_data):
        """Test serialize and deserialize with JSON."""
        from exonware.xwsystem import XWIO
        
        io = XWIO()
        
        # Serialize
        json_str = io.serialize(test_data, 'json')
        assert json_str is not None
        assert 'Alice' in json_str
        
        # Deserialize
        result = io.deserialize(json_str, 'json')
        assert result == test_data
    
    def test_load_as_save_as(self, test_data, tmp_path):
        """Test load_as and save_as methods."""
        from exonware.xwsystem import XWIO
        
        io = XWIO()
        test_file = tmp_path / 'test.json'
        
        # Save
        io.save_as(test_file, test_data, 'json')
        assert test_file.exists()
        
        # Load
        loaded = io.load_as(test_file, 'json')
        assert loaded == test_data
    
    def test_read_as_write_as_auto_detect(self, test_data, tmp_path):
        """Test read_as and write_as with auto-detection."""
        from exonware.xwsystem import XWIO
        
        io = XWIO()
        test_file = tmp_path / 'config.json'
        
        # Write (auto-detect from extension)
        io.write_as(test_file, test_data)
        assert test_file.exists()
        
        # Read (auto-detect from extension)
        loaded = io.read_as(test_file)
        assert loaded == test_data
    
    def test_format_conversion(self, test_data, tmp_path):
        """Test converting between formats."""
        from exonware.xwsystem import XWIO
        
        io = XWIO()
        
        json_file = tmp_path / 'data.json'
        yaml_file = tmp_path / 'data.yaml'
        
        # Save as JSON
        io.write_as(json_file, test_data)
        
        # Load and save as YAML
        data = io.read_as(json_file)
        io.write_as(yaml_file, data)
        
        # Verify YAML
        yaml_data = io.read_as(yaml_file)
        assert yaml_data == test_data
    
    def test_invalid_format_raises_error(self):
        """Test that invalid format raises proper error."""
        from exonware.xwsystem import XWIO
        
        io = XWIO()
        
        with pytest.raises(ValueError, match="Unknown format"):
            io.serialize({}, 'invalid_format')


@pytest.mark.xwsystem_unit
class TestMultipleFormats:
    """Test operations with multiple formats."""
    
    @pytest.mark.parametrize("format_id,extension", [
        pytest.param('json', '.json', id='json'),
        pytest.param('yaml', '.yaml', id='yaml'),
        pytest.param('toml', '.toml', id='toml'),
        pytest.param('ini', '.ini', id='ini'),
    ])
    def test_roundtrip_all_formats(self, test_data, tmp_path, format_id, extension):
        """Test roundtrip for all common formats."""
        from exonware.xwsystem import XWIO
        
        io = XWIO()
        test_file = tmp_path / f'data{extension}'
        
        # INI format requires sections, so wrap data in a section
        if format_id == 'ini':
            ini_data = {'user': test_data}
        else:
            ini_data = test_data
        
        # Write
        io.save_as(test_file, ini_data, format_id)
        
        # Read
        loaded = io.load_as(test_file, format_id)
        
        # INI format wraps flat dicts in DEFAULT section and converts values to strings
        if format_id == 'ini':
            # INI format returns dict with sections, and values are strings
            assert 'user' in loaded or 'DEFAULT' in loaded
            if 'user' in loaded:
                # Values are strings in INI format
                assert loaded['user']['name'] == 'Alice'
                assert loaded['user']['age'] == '30'
                assert loaded['user']['active'] == 'True'
            else:
                # Flat dict wrapped in DEFAULT
                assert loaded['DEFAULT']['name'] == 'Alice'
                assert loaded['DEFAULT']['age'] == '30'
                assert loaded['DEFAULT']['active'] == 'True'
        else:
            assert loaded == test_data

