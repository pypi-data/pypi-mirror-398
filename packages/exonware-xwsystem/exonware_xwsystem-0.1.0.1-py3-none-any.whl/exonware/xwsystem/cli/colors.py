"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 05, 2025

Colored terminal output utilities with cross-platform support.
"""

import os
import sys
from typing import Optional, Union
from .defs import Colors, Style

# Explicit import - colorama is a required dependency for CLI functionality
# This ensures consistent cross-platform colored output
# Import colorama - lazy installation system will handle it if missing
import colorama
colorama.init(autoreset=True)

from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.cli.colors")


class ColoredOutput:
    """
    Cross-platform colored terminal output.
    
    Features:
    - Automatic color detection
    - Windows support via colorama
    - Graceful fallback when colors not supported
    - Rich formatting options
    """
    
    def __init__(self, force_color: Optional[bool] = None, auto_reset: bool = True):
        """
        Initialize colored output.
        
        Args:
            force_color: Force color output (None = auto-detect)
            auto_reset: Automatically reset colors after each output
        """
        self.force_color = force_color
        self.auto_reset = auto_reset
        self._supports_color = self._detect_color_support()
        
        if self._supports_color:
            logger.debug("Color support detected")
        else:
            logger.debug("No color support detected")
    
    def _detect_color_support(self) -> bool:
        """Detect if terminal supports colors."""
        if self.force_color is not None:
            return self.force_color
        
        # Check environment variables
        if os.getenv('NO_COLOR'):
            return False
        
        if os.getenv('FORCE_COLOR'):
            return True
        
        # Check if stdout is a TTY
        if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
            return False
        
        # Check TERM environment variable
        term = os.getenv('TERM', '').lower()
        if 'color' in term or term in ('xterm', 'xterm-256color', 'screen', 'tmux'):
            return True
        
        # Lazy installation ensures colorama is always available
        # Works on all platforms
        return True
    
    def supports_color(self) -> bool:
        """Check if colored output is supported."""
        return self._supports_color
    
    def colorize(self, text: str, color: Union[Colors, str], style: Optional[Union[Style, str]] = None) -> str:
        """
        Apply color and style to text.
        
        Args:
            text: Text to colorize
            color: Color to apply
            style: Optional style to apply
            
        Returns:
            Colored text (or plain text if colors not supported)
        """
        if not self._supports_color:
            return text
        
        # Convert string colors to enum
        if isinstance(color, str):
            color = getattr(Colors, color.upper(), Colors.WHITE)
        
        if isinstance(style, str):
            style = getattr(Style, style.upper(), None)
        
        # Build color string
        color_str = color.value
        if style:
            color_str += style.value
        
        # Apply color
        if self.auto_reset:
            return f"{color_str}{text}{Colors.RESET.value}"
        else:
            return f"{color_str}{text}"
    
    def print_colored(self, text: str, color: Union[Colors, str], 
                     style: Optional[Union[Style, str]] = None, **kwargs) -> None:
        """
        Print colored text.
        
        Args:
            text: Text to print
            color: Color to apply
            style: Optional style to apply
            **kwargs: Additional arguments for print()
        """
        colored_text = self.colorize(text, color, style)
        print(colored_text, **kwargs)
    
    def success(self, text: str, **kwargs) -> None:
        """Print success message in green."""
        self.print_colored(f"✓ {text}", Colors.GREEN, **kwargs)
    
    def error(self, text: str, **kwargs) -> None:
        """Print error message in red."""
        self.print_colored(f"✗ {text}", Colors.RED, **kwargs)
    
    def warning(self, text: str, **kwargs) -> None:
        """Print warning message in yellow."""
        self.print_colored(f"⚠ {text}", Colors.YELLOW, **kwargs)
    
    def info(self, text: str, **kwargs) -> None:
        """Print info message in blue."""
        self.print_colored(f"ℹ {text}", Colors.BLUE, **kwargs)
    
    def debug(self, text: str, **kwargs) -> None:
        """Print debug message in dim style."""
        self.print_colored(f"🔧 {text}", Colors.BRIGHT_BLACK, Style.DIM, **kwargs)
    
    def header(self, text: str, **kwargs) -> None:
        """Print header text in bold."""
        self.print_colored(text, Colors.WHITE, Style.BOLD, **kwargs)
    
    def subheader(self, text: str, **kwargs) -> None:
        """Print subheader text in cyan."""
        self.print_colored(text, Colors.CYAN, Style.BOLD, **kwargs)
    
    def highlight(self, text: str, **kwargs) -> None:
        """Print highlighted text in magenta."""
        self.print_colored(text, Colors.MAGENTA, Style.BOLD, **kwargs)
    
    def muted(self, text: str, **kwargs) -> None:
        """Print muted text in dim style."""
        self.print_colored(text, Colors.BRIGHT_BLACK, Style.DIM, **kwargs)
    
    def rainbow(self, text: str, **kwargs) -> None:
        """Print text with rainbow colors (character by character)."""
        if not self._supports_color:
            print(text, **kwargs)
            return
        
        rainbow_colors = [
            Colors.RED, Colors.YELLOW, Colors.GREEN, 
            Colors.CYAN, Colors.BLUE, Colors.MAGENTA
        ]
        
        colored_chars = []
        for i, char in enumerate(text):
            color = rainbow_colors[i % len(rainbow_colors)]
            colored_chars.append(self.colorize(char, color))
        
        print(''.join(colored_chars), **kwargs)
    
    def gradient(self, text: str, start_color: Colors, end_color: Colors, **kwargs) -> None:
        """Print text with gradient colors (simplified version)."""
        if not self._supports_color:
            print(text, **kwargs)
            return
        
        # Simple gradient: alternate between start and end colors
        colored_chars = []
        for i, char in enumerate(text):
            color = start_color if i % 2 == 0 else end_color
            colored_chars.append(self.colorize(char, color))
        
        print(''.join(colored_chars), **kwargs)
    
    def progress_bar(self, current: int, total: int, width: int = 50, 
                    fill_color: Colors = Colors.GREEN, empty_color: Colors = Colors.BRIGHT_BLACK) -> str:
        """
        Generate a colored progress bar.
        
        Args:
            current: Current progress value
            total: Total progress value
            width: Width of progress bar in characters
            fill_color: Color for filled portion
            empty_color: Color for empty portion
            
        Returns:
            Colored progress bar string
        """
        if total == 0:
            percent = 0
        else:
            percent = min(100, max(0, (current / total) * 100))
        
        filled_width = int(width * percent / 100)
        empty_width = width - filled_width
        
        filled_bar = self.colorize('█' * filled_width, fill_color)
        empty_bar = self.colorize('░' * empty_width, empty_color)
        
        percentage_text = f" {percent:5.1f}% ({current}/{total})"
        
        return f"[{filled_bar}{empty_bar}]{percentage_text}"


# Global colored output instance
_colored_output = ColoredOutput()

# Convenience functions
def colorize(text: str, color: Union[Colors, str], style: Optional[Union[Style, str]] = None) -> str:
    """Colorize text using global instance."""
    return _colored_output.colorize(text, color, style)

def print_colored(text: str, color: Union[Colors, str], 
                 style: Optional[Union[Style, str]] = None, **kwargs) -> None:
    """Print colored text using global instance."""
    _colored_output.print_colored(text, color, style, **kwargs)

def success(text: str, **kwargs) -> None:
    """Print success message."""
    _colored_output.success(text, **kwargs)

def error(text: str, **kwargs) -> None:
    """Print error message."""
    _colored_output.error(text, **kwargs)

def warning(text: str, **kwargs) -> None:
    """Print warning message."""
    _colored_output.warning(text, **kwargs)

def info(text: str, **kwargs) -> None:
    """Print info message."""
    _colored_output.info(text, **kwargs)

def debug(text: str, **kwargs) -> None:
    """Print debug message."""
    _colored_output.debug(text, **kwargs)

def header(text: str, **kwargs) -> None:
    """Print header text."""
    _colored_output.header(text, **kwargs)

def subheader(text: str, **kwargs) -> None:
    """Print subheader text."""
    _colored_output.subheader(text, **kwargs)

def highlight(text: str, **kwargs) -> None:
    """Print highlighted text."""
    _colored_output.highlight(text, **kwargs)

def muted(text: str, **kwargs) -> None:
    """Print muted text."""
    _colored_output.muted(text, **kwargs)

def supports_color() -> bool:
    """Check if colored output is supported."""
    return _colored_output.supports_color()
