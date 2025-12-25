#!/usr/bin/env python3
"""
Unit test runner for shared module.

Following GUIDE_TEST.md standards.
"""

import sys
import pytest
from pathlib import Path


def main():
    """Run shared module unit tests."""
    # Add src to Python path
    src_path = Path(__file__).parent.parent.parent.parent / "src"
    sys.path.insert(0, str(src_path))
    
    # Get test directory
    test_dir = Path(__file__).parent
    
    # Run unit tests
    exit_code = pytest.main([
        "-v",
        "--tb=short",
        "-x",  # Stop on first failure
        str(test_dir),
        "-m", "xwsystem_unit",
    ])
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

