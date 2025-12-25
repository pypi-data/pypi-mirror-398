#!/usr/bin/env python3
"""
#exonware/xwsystem/tests/1.unit/utils/runner.py

Runner for xwsystem utility unit tests.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.387
Generation Date: 08-Nov-2025
"""

from __future__ import annotations

from pathlib import Path

from exonware.xwsystem.utils.test_runner import TestRunner


def main() -> int:
    """Execute utils-focused unit tests using the shared runner."""
    test_dir = Path(__file__).parent
    runner = TestRunner(
        library_name="xwsystem",
        layer_name="1.unit",
        description="Utils lazy mode regression tests",
        test_dir=test_dir,
        markers=["xwsystem_unit"],
    )
    return runner.run()


if __name__ == "__main__":
    raise SystemExit(main())


