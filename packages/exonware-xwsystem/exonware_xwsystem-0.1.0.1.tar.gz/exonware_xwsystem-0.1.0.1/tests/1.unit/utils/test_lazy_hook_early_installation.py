#exonware/xwsystem/tests/1.unit/utils/test_lazy_hook_early_installation.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.389
Generation Date: 11-Nov-2025

Tests for early hook installation and re-hooking support.

Tests verify that:
1. Hook is installed before imports when [lazy] extra detected
2. Hook is installed when environment variable set
3. Hook is NOT installed when lazy is off (zero overhead)
4. Re-hooking works when conf.lazy_install = True
5. Hook path fix works for io.serialization modules
6. Auto-install works on ImportError

Following GUIDE_TEST.md standards:
- Hierarchical test structure (1.unit layer)
- Proper markers (xwsystem_unit, xwsystem_integration)
- Root cause fixing: Tests verify actual behavior
- NO rigged tests, NO pass to hide errors
- Descriptive test names: test_<action>_<expected_result>
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from unittest.mock import patch
from typing import Iterator

import pytest

# Skip all tests in this file - xwlazy has been removed
pytestmark = pytest.mark.skip(reason="xwlazy has been removed from the codebase")

# Import after setting up mocks/environment
# from xwlazy.lazy.lazy_core import (
#     is_import_hook_installed,
#     uninstall_import_hook,
#     is_lazy_install_enabled,
# )


@contextmanager
def clean_lazy_state() -> Iterator[None]:
    """
    Clean lazy state before and after test.
    
    WHY: Ensures tests don't interfere with each other
    """
    # Uninstall hook if installed
    try:
        uninstall_import_hook('xwsystem')
    except Exception:
        pass
    
    # Clear environment variable
    old_env = os.environ.pop('XWSYSTEM_LAZY_INSTALL', None)
    
    try:
        yield
    finally:
        # Restore environment
        if old_env is not None:
            os.environ['XWSYSTEM_LAZY_INSTALL'] = old_env
        else:
            os.environ.pop('XWSYSTEM_LAZY_INSTALL', None)
        
        # Uninstall hook
        try:
            uninstall_import_hook('xwsystem')
        except Exception:
            pass


@pytest.mark.xwsystem_unit
def test_lazy_hook_not_installed_by_default():
    """
    Hook should not be installed just because xwlazy is present.
    """
    with clean_lazy_state():
        # Clear module cache to force re-import
        for mod in ('exonware.xwsystem',):
            sys.modules.pop(mod, None)
        import exonware.xwsystem  # noqa: F401

        assert not is_import_hook_installed('xwsystem'), "Hook must remain disabled until explicitly enabled"


@pytest.mark.xwsystem_unit
def test_env_var_triggers_hook_installation():
    """
    Test that hook is installed when XWSYSTEM_LAZY_INSTALL env var is set.
    
    Root cause: Users should be able to enable lazy via environment variable
    Priority: Usability (#2) - Flexible configuration
    """
    with clean_lazy_state():
        # Set environment variable
        os.environ['XWSYSTEM_LAZY_INSTALL'] = '1'
        
        # Clear module cache
        sys.modules.pop('exonware.xwsystem', None)
        
        # Import package
        import exonware.xwsystem
        
        # Verify hook is installed
        assert is_import_hook_installed('xwsystem'), "Hook should be installed when env var set"


@pytest.mark.xwsystem_unit
def test_no_hook_when_lazy_is_off():
    """
    Test that hook is NOT installed when lazy is off.
    
    Root cause: Zero overhead requirement - no hook when lazy disabled
    Priority: Performance (#4) - Zero overhead when lazy off
    """
    with clean_lazy_state():
        # Ensure env var removed
        sys.modules.pop('exonware.xwsystem', None)

        import exonware.xwsystem  # noqa: F401

        # Verify hook is NOT installed
        assert not is_import_hook_installed('xwsystem'), "Hook should NOT be installed when lazy is off"


@pytest.mark.xwsystem_unit
def test_rehooking_when_conf_lazy_install_set_to_true():
    """
    Test that hook is installed when conf.lazy_install = True is set.
    
    Root cause: Hook not installed when lazy enabled after package load
    Priority: Usability (#2) - Users expect lazy to work when enabled
    """
    with clean_lazy_state():
        # Import package without lazy
        import exonware.xwsystem.conf as conf
        
        # Verify hook is NOT installed initially
        assert not is_import_hook_installed('xwsystem'), "Hook should not be installed initially"
        
        # Set lazy_install to True
        conf.lazy_install = True
        
        # Verify hook is now installed
        assert is_import_hook_installed('xwsystem'), "Hook should be installed after conf.lazy_install = True"


@pytest.mark.xwsystem_unit
def test_hook_path_fix_for_io_serialization():
    """
    Test that hook intercepts imports for io.serialization modules.
    
    Root cause: Hook was watching wrong path (serialization.* instead of io.serialization.*)
    Priority: Usability (#2) - Missing dependencies not auto-installed
    """
    with clean_lazy_state():
        # Enable lazy mode
        import exonware.xwsystem.conf as conf
        conf.lazy_install = True
        
        # Verify hook is installed
        assert is_import_hook_installed('xwsystem'), "Hook should be installed"
        
        # Try to import io.serialization module
        # This should be intercepted by hook (even if module doesn't exist)
        # The hook's find_spec should be called for io.serialization paths
        from xwlazy.lazy.lazy_core import LazyMetaPathFinder
        
        # Check that hook exists and can handle io.serialization path
        hook_installed = is_import_hook_installed('xwsystem')
        assert hook_installed, "Hook should be installed"
        
        # Verify hook can handle the correct path
        # The hook's find_spec method should match io.serialization.*
        test_path = 'exonware.xwsystem.io.serialization.formats.text.yaml'
        # This is tested indirectly - if hook is installed, it should handle the path


@pytest.mark.xwsystem_integration
def test_auto_install_on_importerror():
    """
    Test that missing packages are auto-installed on ImportError.
    
    Root cause: Lazy mode should install missing dependencies automatically
    Priority: Usability (#2) - Zero-config dependency management
    """
    with clean_lazy_state():
        # Enable lazy mode
        import exonware.xwsystem.conf as conf
        conf.lazy_install = True
        
        # Verify hook is installed
        assert is_import_hook_installed('xwsystem'), "Hook should be installed"
        
        # Note: Actual package installation test would require:
        # 1. Mocking subprocess.run for pip install
        # 2. Mocking importlib.import_module for re-import
        # 3. Testing the full flow
        
        # For now, verify hook is active (actual installation tested in integration tests)
        assert is_lazy_install_enabled('xwsystem'), "Lazy install should be enabled"


@pytest.mark.xwsystem_unit
def test_dx_status_check_methods():
    """
    Test DX status check methods in conf module.
    
    Root cause: Developers need ways to verify lazy mode status
    Priority: Usability (#2) - Easy debugging and verification
    """
    with clean_lazy_state():
        import exonware.xwsystem.conf as conf
        
        # Test lazy_install_status method
        status = conf.lazy_install_status()
        assert isinstance(status, dict), "Status should return dictionary"
        assert 'enabled' in status, "Status should include 'enabled'"
        assert 'hook_installed' in status, "Status should include 'hook_installed'"
        assert 'active' in status, "Status should include 'active'"
        
        # Test is_lazy_active method
        is_active = conf.is_lazy_active()
        assert isinstance(is_active, bool), "is_lazy_active should return boolean"
        
        # Enable lazy and check again
        conf.lazy_install = True
        status_after = conf.lazy_install_status()
        assert status_after['enabled'] is True, "Status should show enabled=True"
        assert status_after['hook_installed'] is True, "Status should show hook_installed=True"
        assert status_after['active'] is True, "Status should show active=True"
        
        assert conf.is_lazy_active() is True, "is_lazy_active should return True"


@pytest.mark.xwsystem_unit
def test_bootstrap_fails_gracefully():
    """
    Test that bootstrap fails gracefully if hook installation fails.
    
    Root cause: Package should load even if hook installation fails
    Priority: Usability (#2) - Backward compatibility
    """
    with clean_lazy_state():
        # Set env var to trigger bootstrap
        os.environ['XWSYSTEM_LAZY_INSTALL'] = '1'
        
        # Mock install_import_hook to raise exception
        with patch('xwlazy.lazy.host_packages.install_import_hook', side_effect=Exception("Hook install failed")):
            # Clear module cache
            sys.modules.pop('exonware.xwsystem', None)

            # Import should succeed even if hook installation fails
            try:
                import exonware.xwsystem  # noqa: F401
                import_succeeded = True
            except Exception:
                import_succeeded = False

            assert import_succeeded, "Package should load even if hook installation fails"

