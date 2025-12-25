#!/usr/bin/env python3
#exonware/xwsystem/cli/types.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 07-Sep-2025

CLI types and enums for XWSystem.
"""

from enum import Enum


# ============================================================================
# CLI ENUMS
# ============================================================================

class ColorType(Enum):
    """Color types for CLI output."""
    RESET = "reset"
    BOLD = "bold"
    DIM = "dim"
    UNDERLINE = "underline"
    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"
    BLUE = "blue"
    MAGENTA = "magenta"
    CYAN = "cyan"
    WHITE = "white"
    GRAY = "gray"


class ProgressStyle(Enum):
    """Progress bar styles."""
    BAR = "bar"
    SPINNER = "spinner"
    PERCENTAGE = "percentage"
    COUNTER = "counter"


class TableStyle(Enum):
    """Table display styles."""
    SIMPLE = "simple"
    GRID = "grid"
    FANCY = "fancy"
    MINIMAL = "minimal"


class PromptType(Enum):
    """Prompt input types."""
    TEXT = "text"
    PASSWORD = "password"
    CONFIRM = "confirm"
    SELECT = "select"
    MULTISELECT = "multiselect"


class Alignment(Enum):
    """Text alignment options."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class BorderStyle(Enum):
    """Table border styles."""
    NONE = "none"
    ASCII = "ascii"
    SIMPLE = "simple"
    ROUNDED = "rounded"
    DOUBLE = "double"
    THICK = "thick"


class Colors(Enum):
    """ANSI color codes."""
    # Standard colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    # Reset
    RESET = "\033[0m"


class Style(Enum):
    """ANSI style codes."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"
    STRIKETHROUGH = "\033[9m"


class ArgumentType(Enum):
    """Types of command-line arguments."""
    STRING = "string"
    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "bool"
    FILE = "file"
    DIRECTORY = "dir"
    CHOICE = "choice"
