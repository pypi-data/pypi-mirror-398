"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Console utilities for CLI operations.
"""

import sys
import os
from typing import Optional
from .contracts import IConsole, ColorType
from .errors import ConsoleError


class Console(IConsole):
    """Console implementation for CLI operations."""
    
    def __init__(self):
        """Initialize console."""
        self._supports_color = self._check_color_support()
        self._is_interactive = self._check_interactive()
    
    def _check_color_support(self) -> bool:
        """Check if terminal supports color."""
        try:
            # Check if we're in a terminal that supports color
            return (
                hasattr(sys.stdout, 'isatty') and 
                sys.stdout.isatty() and 
                os.getenv('TERM') != 'dumb' and
                os.getenv('NO_COLOR') is None
            )
        except:
            return False
    
    def _check_interactive(self) -> bool:
        """Check if console is interactive."""
        try:
            return hasattr(sys.stdin, 'isatty') and sys.stdin.isatty()
        except:
            return False
    
    def print(self, text: str, color: Optional[ColorType] = None, **kwargs) -> None:
        """Print text to console."""
        try:
            if color and self._supports_color:
                text = self._apply_color(text, color)
            
            print(text, **kwargs)
        except Exception as e:
            raise ConsoleError(f"Failed to print to console: {e}")
    
    def input(self, prompt: str, **kwargs) -> str:
        """Get input from user."""
        try:
            if not self._is_interactive:
                raise ConsoleError("Console is not interactive")
            
            return input(prompt, **kwargs)
        except Exception as e:
            raise ConsoleError(f"Failed to get input: {e}")
    
    def clear(self) -> None:
        """Clear console screen."""
        try:
            if os.name == 'nt':  # Windows
                os.system('cls')
            else:  # Unix/Linux/macOS
                os.system('clear')
        except Exception as e:
            raise ConsoleError(f"Failed to clear console: {e}")
    
    def _apply_color(self, text: str, color: ColorType) -> str:
        """Apply color to text."""
        color_codes = {
            ColorType.RESET: '\033[0m',
            ColorType.BOLD: '\033[1m',
            ColorType.DIM: '\033[2m',
            ColorType.UNDERLINE: '\033[4m',
            ColorType.RED: '\033[31m',
            ColorType.GREEN: '\033[32m',
            ColorType.YELLOW: '\033[33m',
            ColorType.BLUE: '\033[34m',
            ColorType.MAGENTA: '\033[35m',
            ColorType.CYAN: '\033[36m',
            ColorType.WHITE: '\033[37m',
            ColorType.GRAY: '\033[90m',
        }
        
        code = color_codes.get(color, '')
        return f"{code}{text}\033[0m" if code else text
    
    def get_size(self) -> tuple[int, int]:
        """Get console size."""
        try:
            if hasattr(os, 'get_terminal_size'):
                size = os.get_terminal_size()
                return (size.columns, size.lines)
            else:
                return (80, 24)  # Default size
        except:
            return (80, 24)
    
    def is_interactive(self) -> bool:
        """Check if console is interactive."""
        return self._is_interactive
    
    def supports_color(self) -> bool:
        """Check if console supports color."""
        return self._supports_color