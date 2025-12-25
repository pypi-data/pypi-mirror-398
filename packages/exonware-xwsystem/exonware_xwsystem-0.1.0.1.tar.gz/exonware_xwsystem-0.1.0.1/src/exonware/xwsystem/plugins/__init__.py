"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

XSystem Plugins Package

Provides plugin discovery, registration and management system
with support for entry points and dynamic loading.
"""

from .base import APluginManager, APlugin, APluginRegistry

# Convenience aliases following DEV_GUIDELINES.md naming conventions
PluginManager = APluginManager
PluginBase = APlugin
PluginRegistry = APluginRegistry

__all__ = [
    "APluginManager",
    "APlugin", 
    "APluginRegistry",
    "PluginManager",
    "PluginBase", 
    "PluginRegistry",
]
