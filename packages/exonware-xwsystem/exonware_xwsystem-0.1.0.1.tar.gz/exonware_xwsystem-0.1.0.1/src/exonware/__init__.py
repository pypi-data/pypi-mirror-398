"""
exonware package - Enterprise-grade Python framework ecosystem

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

This is a namespace package allowing multiple exonware subpackages
to coexist (xwsystem, xwnode, xwdata, etc.)
"""

# Make this a namespace package FIRST
__path__ = __import__('pkgutil').extend_path(__path__, __name__)

import importlib.metadata
from pathlib import Path


def _load_version() -> str:
    try:
        return importlib.metadata.version("exonware-xwsystem")
    except importlib.metadata.PackageNotFoundError:
        version_path = Path(__file__).parent / "xwsystem" / "version.py"
        ns: dict = {}
        try:
            exec(version_path.read_text(encoding="utf-8"), ns)  # noqa: S102
        except FileNotFoundError as exc:  # pragma: no cover
            raise ImportError(
                f"Version metadata unavailable at {version_path}."
            ) from exc
        return ns["__version__"]


__version__ = _load_version()

__author__ = 'Eng. Muhammad AlShehri'
__email__ = 'connect@exonware.com'
__company__ = 'eXonware.com'
