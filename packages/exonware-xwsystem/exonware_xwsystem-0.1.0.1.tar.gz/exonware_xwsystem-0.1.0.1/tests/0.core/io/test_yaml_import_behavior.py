#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core tests for YAML import behavior.

Tests verify that YAML serialization imports work correctly without
external dependencies like xwlazy. These are fast, high-value core tests.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 11-Oct-2025

Following GUIDE_TEST.md standards:
- Core test layer (0.core)
- Proper markers (xwsystem_core, xwsystem_serialization)
- Fast execution
- Root cause fixing: Tests verify actual import behavior
"""

import sys
import pytest


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_serialization
def test_yaml_direct_import():
    """
    Test direct yaml import (NO xwsystem, NO xwlazy).
    
    Root cause: Verify yaml module works fine by itself
    Priority: Usability (#2) - Basic functionality should work
    """
    try:
        import yaml
        assert hasattr(yaml, '__version__'), "yaml module should have version"
        
        # Test basic functionality
        data = {"test": "value", "number": 42}
        result = yaml.dump(data)
        assert isinstance(result, str), "yaml.dump() should return string"
        assert "test" in result, "yaml.dump() should contain data"
        
    except ImportError:
        pytest.skip("PyYAML not installed - this is expected in some environments")
    except AttributeError as e:
        if "partially initialized module 'yaml'" in str(e) or "'yaml' has no attribute" in str(e):
            pytest.fail(f"Circular import error in yaml module itself: {e}")
        raise


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_serialization
def test_yaml_import_without_xwlazy():
    """
    Test YAML import through xwsystem WITHOUT xwlazy.
    
    Root cause: Verify xwsystem YAML serialization works without lazy loading
    Priority: Usability (#2) - Core functionality should work independently
    """
    try:
        # Import xwsystem version
        from exonware.xwsystem.version import get_version
        version = get_version()
        assert version is not None, "xwsystem version should be available"
        
        # Import YAML serializer
        from exonware.xwsystem.io.serialization import YamlSerializer
        serializer = YamlSerializer()
        assert serializer is not None, "YamlSerializer should be instantiable"
        
        # Test serialization
        data = {"test": "value", "number": 42}
        result = serializer.encode(data)
        assert isinstance(result, (str, bytes)), "YAML encoding should return string or bytes"
        
    except AttributeError as e:
        if "partially initialized module 'yaml'" in str(e):
            pytest.fail(f"Circular import error occurs even without xwlazy: {e}")
        raise


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_serialization
def test_yaml_circular_import_when_installed():
    """
    Test YAML circular import when PyYAML IS installed.
    
    Root cause: Verify circular import doesn't occur when yaml is properly installed
    Priority: Usability (#2) - Properly installed packages should work
    """
    # Check if yaml is installed
    try:
        import yaml
        yaml_version = yaml.__version__
    except ImportError:
        pytest.skip("PyYAML not installed - install it to test this scenario")
    
    try:
        # Import xwsystem version
        from exonware.xwsystem.version import get_version
        version = get_version()
        assert version is not None, "xwsystem version should be available"
        
        # Import YAML serializer
        from exonware.xwsystem.io.serialization import YamlSerializer
        serializer = YamlSerializer()
        assert serializer is not None, "YamlSerializer should be instantiable"
        
        # Test serialization
        data = {"test": "value", "number": 42}
        result = serializer.encode(data)
        assert isinstance(result, (str, bytes)), "YAML encoding should return string or bytes"
        
    except AttributeError as e:
        if "partially initialized module 'yaml'" in str(e) or "'yaml' has no attribute" in str(e):
            pytest.fail(f"Circular import error occurs even with yaml installed: {e}")
        raise

