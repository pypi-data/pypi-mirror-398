#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration tests for YAML import with xwlazy.

Tests verify end-to-end behavior when xwlazy is enabled:
1. YAML import works with xwlazy enabled
2. Circular import issues are resolved
3. Lazy installation works correctly

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 11-Oct-2025

Following GUIDE_TEST.md standards:
- Integration test layer (2.integration)
- Proper markers (xwsystem_integration)
- Real-world scenarios
- Root cause fixing: Tests verify actual integration behavior
"""

import sys
import pytest

# Skip all tests in this file - xwlazy has been removed from the codebase
pytestmark = pytest.mark.skip(reason="xwlazy has been removed from the codebase")


@pytest.mark.xwsystem_integration
@pytest.mark.xwsystem_serialization
def test_yaml_import_with_xwlazy():
    """
    Test YAML import WITH xwlazy enabled.
    
    Root cause: Verify xwsystem works correctly with lazy loading enabled
    Priority: Usability (#2) - Lazy mode should work seamlessly
    
    Note: This test is skipped because xwlazy has been removed from the codebase.
    """
    # Enable lazy mode FIRST (before importing xwsystem)
    try:
        from exonware import conf
        conf.xwsystem.lazy_install = True
    except (ImportError, AttributeError):
        pytest.skip("xwlazy configuration not available")
    
    try:
        # Import xwsystem version (this should work even with lazy mode)
        from exonware.xwsystem.version import get_version
        version = get_version()
        assert version is not None, "xwsystem version should be available with lazy mode"
        
    except AttributeError as e:
        if "partially initialized module 'yaml'" in str(e) or "'yaml' has no attribute" in str(e):
            pytest.fail(f"Circular import error with xwlazy enabled: {e}")
        raise
    except RecursionError as e:
        pytest.fail(f"Recursion error - xwlazy's import hook causing infinite recursion: {e}")


@pytest.mark.xwsystem_integration
@pytest.mark.xwsystem_serialization
def test_yaml_simple_with_lazy():
    """
    Simple YAML import test with xwlazy.
    
    Root cause: Verify basic yaml import works with lazy mode
    Priority: Usability (#2) - Basic functionality should work with lazy mode
    
    Note: This test is skipped because xwlazy has been removed from the codebase.
    """
    try:
        from exonware import conf
        conf.xwsystem.lazy_install = True
    except (ImportError, AttributeError):
        pytest.skip("xwlazy configuration not available")
    
    try:
        import yaml
        assert hasattr(yaml, '__version__'), "yaml module should have version"
        
        # Test that it actually works
        data = {"test": "value"}
        result = yaml.dump(data)
        assert isinstance(result, str), "yaml.dump() should return string"
        
    except ImportError:
        pytest.skip("PyYAML not installed")
    except AttributeError as e:
        if "partially initialized module 'yaml'" in str(e):
            pytest.fail(f"Circular import error: {e}")


@pytest.mark.xwsystem_integration
@pytest.mark.xwsystem_serialization
def test_yaml_fix_verification():
    """
    Test YAML import fix verification.
    
    Root cause: Verify that yaml import fix works correctly
    Priority: Usability (#2) - Fixes should be verified
    
    Note: This test is skipped because xwlazy has been removed from the codebase.
    """
    try:
        from exonware import conf
        conf.xwsystem.lazy_install = True
    except (ImportError, AttributeError):
        pytest.skip("xwlazy configuration not available")
    
    try:
        # This should work now - yaml is importable, so finder shouldn't intercept it
        import yaml
        assert hasattr(yaml, '__version__'), "yaml module should have version"
        
        # Test that it actually works
        data = {"test": "value"}
        result = yaml.dump(data)
        assert isinstance(result, str), "yaml.dump() should return string"
        assert "test" in result, "yaml.dump() should contain data"
        
    except ImportError:
        pytest.skip("PyYAML not installed")
    except AttributeError as e:
        if "partially initialized module 'yaml'" in str(e):
            pytest.fail(f"Circular import error: {e}")
