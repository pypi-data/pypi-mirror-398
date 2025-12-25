#!/usr/bin/env python3
"""
Core Shared Test Runner

Tests shared types, base classes, and contracts.

Following GUIDE_TEST.md standards.
"""

import sys
import pytest
from pathlib import Path


def run_all_shared_tests() -> int:
    """Main entry point for shared core tests using pytest."""
    # Get test directory
    test_dir = Path(__file__).parent
    
    # Run all core shared tests using pytest
    exit_code = pytest.main([
        "-v",
        "--tb=short",
        "-x",  # Stop on first failure
        str(test_dir),
        "-m", "xwsystem_core",
    ])
    
    return exit_code


if __name__ == "__main__":
    sys.exit(run_all_shared_tests())

