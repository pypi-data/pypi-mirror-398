#!/usr/bin/env python3
#exonware/xwsystem/plugins/types.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 07-Sep-2025

Plugins types and enums for XWSystem.
"""

from enum import Enum


# ============================================================================
# PLUGIN ENUMS
# ============================================================================

class PluginState(Enum):
    """Plugin states."""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    DISABLED = "disabled"


class PluginType(Enum):
    """Plugin types."""
    CORE = "core"
    EXTENSION = "extension"
    MIDDLEWARE = "middleware"
    SERVICE = "service"
    UTILITY = "utility"
    CUSTOM = "custom"


class PluginPriority(Enum):
    """Plugin priorities."""
    LOWEST = 0
    LOW = 1
    NORMAL = 2
    HIGH = 3
    HIGHEST = 4
    CRITICAL = 5


class HookType(Enum):
    """Hook types."""
    PRE = "pre"
    POST = "post"
    AROUND = "around"
    FILTER = "filter"
    ACTION = "action"


class PluginEvent(Enum):
    """Plugin events."""
    LOADED = "loaded"
    UNLOADED = "unloaded"
    INITIALIZED = "initialized"
    STARTED = "started"
    STOPPED = "stopped"
    ERROR = "error"
    CONFIGURED = "configured"
    DISABLED = "disabled"
    ENABLED = "enabled"
