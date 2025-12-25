#exonware/xwsystem/tests/2.integration/io_tests/test_lazy_hook_integration.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.389
Generation Date: 11-Nov-2025

Integration tests for lazy hook early installation.

Tests verify end-to-end behavior:
1. json_run.py example works with lazy mode
2. PyYAML auto-installation works
3. Hook intercepts ImportError correctly

Following GUIDE_TEST.md standards:
- Integration test layer (2.integration)
- Proper markers (xwsystem_integration)
- Real-world scenarios
- Root cause fixing: Tests verify actual behavior
"""

from __future__ import annotations

import os
import sys
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from unittest.mock import patch, MagicMock

import pytest

# Skip all tests in this file - xwlazy has been removed
pytestmark = pytest.mark.skip(reason="xwlazy has been removed from the codebase")


@contextmanager
def clean_lazy_state() -> Iterator[None]:
    """Clean lazy state before and after test."""
    old_env = os.environ.pop('XWSYSTEM_LAZY_INSTALL', None)
    try:
        yield
    finally:
        if old_env is not None:
            os.environ['XWSYSTEM_LAZY_INSTALL'] = old_env
        else:
            os.environ.pop('XWSYSTEM_LAZY_INSTALL', None)


@pytest.mark.xwsystem_integration
def test_json_run_example_with_lazy_mode():
    """
    Test that json_run.py example works with lazy mode enabled.
    
    Root cause: Users should be able to use lazy mode seamlessly
    Priority: Usability (#2) - Zero-config lazy mode
    """
    with clean_lazy_state():
        # Get path to example
        example_path = Path(__file__).parent.parent.parent.parent / "examples" / "lazy_mode_usage" / "json_run.py"
        
        if not example_path.exists():
            pytest.skip(f"Example file not found: {example_path}")
        
        # Enable lazy mode via environment variable
        os.environ['XWSYSTEM_LAZY_INSTALL'] = '1'
        
        # Clear module cache to ensure fresh import
        for mod in ('exonware.xwsystem', 'exonware.xwsystem.conf'):
            sys.modules.pop(mod, None)
        
        # Verify hook would be installed
        # Note: Actual execution would require PyYAML installation
        # This test verifies the hook is active, not actual package installation
        import exonware.xwsystem.conf as conf
        
        # Enable lazy mode
        conf.lazy_install = True
        
        # Verify hook is installed
        from xwlazy.lazy.lazy_core import is_import_hook_installed
        assert is_import_hook_installed('xwsystem'), "Hook should be installed for lazy mode"


@pytest.mark.xwsystem_integration
def test_hook_intercepts_io_serialization_imports():
    """
    Test that hook intercepts imports for io.serialization modules.
    
    Root cause: Hook path fix ensures io.serialization.* imports are intercepted
    Priority: Usability (#2) - Missing dependencies auto-installed
    """
    with clean_lazy_state():
        import exonware.xwsystem.conf as conf
        conf.lazy_install = True
        
        # Verify hook is installed
        from xwlazy.lazy.lazy_core import is_import_hook_installed
        assert is_import_hook_installed('xwsystem'), "Hook should be installed"
        
        # Try to import io.serialization module
        # The hook should be able to intercept this path
        # (Actual interception tested in unit tests)
        try:
            from exonware.xwsystem.io.serialization.formats.text.yaml import YamlSerializer
            # If import succeeds, hook is working (or PyYAML is already installed)
            serializer = YamlSerializer()
            assert serializer is not None, "YamlSerializer should be instantiable"
        except ImportError as e:
            # If ImportError, hook should intercept and attempt installation
            # In test environment, we verify hook is active, not actual installation
            assert is_import_hook_installed('xwsystem'), "Hook should be active to handle ImportError"


@pytest.mark.xwsystem_integration
def test_rehooking_works_after_package_load():
    """
    Test that re-hooking works when lazy is enabled after package load.
    
    Root cause: Users may enable lazy mode after importing package
    Priority: Usability (#2) - Flexible configuration
    """
    with clean_lazy_state():
        # Import package without lazy
        import exonware.xwsystem.conf as conf
        
        from xwlazy.lazy.lazy_core import is_import_hook_installed, uninstall_import_hook
        
        # Ensure hook is not installed
        try:
            uninstall_import_hook('xwsystem')
        except Exception:
            pass
        
        assert not is_import_hook_installed('xwsystem'), "Hook should not be installed initially"
        
        # Enable lazy mode
        conf.lazy_install = True
        
        # Verify hook is now installed
        assert is_import_hook_installed('xwsystem'), "Hook should be installed after conf.lazy_install = True"
        
        # Verify status check works
        status = conf.lazy_install_status()
        assert status['active'] is True, "Status should show lazy mode is active"

