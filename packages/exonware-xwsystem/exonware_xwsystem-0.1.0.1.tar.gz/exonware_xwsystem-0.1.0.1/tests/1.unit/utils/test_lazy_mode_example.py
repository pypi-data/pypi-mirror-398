"""
#exonware/xwsystem/tests/1.unit/utils/test_lazy_mode_example.py

Validate the lazy mode quick check example and configuration helpers.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.387
Generation Date: 08-Nov-2025
"""

from __future__ import annotations

import runpy
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pytest

# Skip all tests in this file - xwlazy has been removed
pytestmark = pytest.mark.skip(reason="xwlazy has been removed from the codebase")

# from xwlazy.lazy import (
#     LazyInstallConfig,
#     config_package_lazy_install_enabled,
#     is_import_hook_installed,
# )

PACKAGE_NAME = "xwsystem"
EXAMPLE_MODULE = "lazy_mode_quick_check"


@contextmanager
def preserve_lazy_configuration(package_name: str = PACKAGE_NAME) -> Iterator[tuple[bool, str]]:
    """
    Preserve existing lazy install configuration for the duration of a test.

    WHY:
    - Prevents cross-test interference by always restoring original settings.
    - Avoids toggling the import hook, which could affect global import behaviour.
    """
    original_enabled = LazyInstallConfig.is_enabled(package_name)
    original_mode = LazyInstallConfig.get_mode(package_name)
    try:
        yield original_enabled, original_mode
    finally:
        config_package_lazy_install_enabled(
            package_name,
            original_enabled,
            original_mode,
            install_hook=False,
        )


def load_example_globals() -> dict:
    """Load the example module using runpy to access helper functions."""
    example_path = Path(__file__).resolve().parents[3] / "examples" / f"{EXAMPLE_MODULE}.py"
    return runpy.run_path(str(example_path))


@pytest.mark.xwsystem_unit
def test_lazy_mode_demo_enables_and_restores_configuration() -> None:
    """
    Ensure the example toggles lazy install and restores previous state.

    WHY:
    - Confirms that lazy mode activation works without leaving residual changes.
    - Validates that the example provides accurate status data for developers.
    """
    example_globals = load_example_globals()
    run_lazy_mode_demo = example_globals["run_lazy_mode_demo"]

    with preserve_lazy_configuration() as (original_enabled, original_mode):
        result = run_lazy_mode_demo(PACKAGE_NAME)

        assert result["demo_enabled"] is True
        assert result["demo_mode"] == "interactive"

        # Ensure the function restored original values.
        assert LazyInstallConfig.is_enabled(PACKAGE_NAME) == original_enabled
        assert LazyInstallConfig.get_mode(PACKAGE_NAME) == original_mode

        # Stats should always provide a dictionary with baseline keys.
        assert isinstance(result["stats"], dict)
        assert "enabled" in result["stats"]
        assert "total_installed" in result["stats"]


@pytest.mark.xwsystem_unit
def test_config_package_lazy_install_enabled_respects_install_hook_flag() -> None:
    """
    Verify that the helper toggles lazy mode without mutating the import hook.

    WHY:
    - Guarantees that tests using lazy mode can run without side effects.
    - Protects security by ensuring no unexpected hook stays installed.
    """
    hook_before = is_import_hook_installed(PACKAGE_NAME)

    with preserve_lazy_configuration():
        config_package_lazy_install_enabled(
            PACKAGE_NAME,
            True,
            mode="interactive",
            install_hook=False,
        )

        assert LazyInstallConfig.is_enabled(PACKAGE_NAME) is True
        assert LazyInstallConfig.get_mode(PACKAGE_NAME) == "interactive"
        assert is_import_hook_installed(PACKAGE_NAME) == hook_before


