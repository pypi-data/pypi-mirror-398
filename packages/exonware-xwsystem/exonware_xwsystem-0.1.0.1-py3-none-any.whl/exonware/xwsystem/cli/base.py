#exonware/xwsystem/cli/base.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

CLI module base classes - abstract classes for command-line interface functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union
from .contracts import ColorType, ProgressStyle, TableStyle, PromptType, ICLI
from ..version import __version__


class AConsoleBase(ABC):
    """Abstract base class for console operations."""
    
    @abstractmethod
    def print(self, text: str, color: Optional[ColorType] = None, **kwargs) -> None:
        """Print text to console."""
        pass
    
    @abstractmethod
    def input(self, prompt: str, **kwargs) -> str:
        """Get input from user."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear console screen."""
        pass
    
    @abstractmethod
    def get_size(self) -> tuple[int, int]:
        """Get console size."""
        pass
    
    @abstractmethod
    def is_interactive(self) -> bool:
        """Check if console is interactive."""
        pass


class AProgressBarBase(ABC):
    """Abstract base class for progress bar operations."""
    
    def __init__(self, total: int, description: str = "", style: ProgressStyle = ProgressStyle.BAR):
        """
        Initialize progress bar.
        
        Args:
            total: Total number of items
            description: Progress description
            style: Progress bar style
        """
        self.total = total
        self.description = description
        self.style = style
        self.current = 0
    
    @abstractmethod
    def start(self) -> None:
        """Start progress bar."""
        pass
    
    @abstractmethod
    def update(self, increment: int = 1) -> None:
        """Update progress."""
        pass
    
    @abstractmethod
    def finish(self) -> None:
        """Finish progress bar."""
        pass
    
    @abstractmethod
    def set_description(self, description: str) -> None:
        """Set progress description."""
        pass


class ATableBase(ABC):
    """Abstract base class for table operations."""
    
    def __init__(self, headers: list[str], style: TableStyle = TableStyle.SIMPLE):
        """
        Initialize table.
        
        Args:
            headers: Table headers
            style: Table style
        """
        self.headers = headers
        self.style = style
        self.rows: list[list[str]] = []
    
    @abstractmethod
    def add_row(self, *values: Any) -> None:
        """Add row to table."""
        pass
    
    @abstractmethod
    def render(self) -> str:
        """Render table as string."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all rows."""
        pass
    
    @abstractmethod
    def get_row_count(self) -> int:
        """Get number of rows."""
        pass


class APromptBase(ABC):
    """Abstract base class for user prompts."""
    
    @abstractmethod
    def ask(self, question: str, prompt_type: PromptType = PromptType.TEXT, **kwargs) -> Any:
        """Ask user a question."""
        pass
    
    @abstractmethod
    def confirm(self, message: str, default: bool = False) -> bool:
        """Ask for confirmation."""
        pass
    
    @abstractmethod
    def select(self, message: str, choices: list[str], default: Optional[str] = None) -> str:
        """Ask user to select from choices."""
        pass
    
    @abstractmethod
    def multiselect(self, message: str, choices: list[str], default: Optional[list[str]] = None) -> list[str]:
        """Ask user to select multiple choices."""
        pass


class AArgumentParserBase(ABC):
    """Abstract base class for argument parsing."""
    
    def __init__(self, description: str = ""):
        """
        Initialize argument parser.
        
        Args:
            description: Parser description
        """
        self.description = description
        self.arguments: list[dict[str, Any]] = []
    
    @abstractmethod
    def add_argument(self, *args, **kwargs) -> None:
        """Add argument to parser."""
        pass
    
    @abstractmethod
    def parse_args(self, args: Optional[list[str]] = None) -> Any:
        """Parse command line arguments."""
        pass
    
    @abstractmethod
    def print_help(self) -> None:
        """Print help message."""
        pass
    
    @abstractmethod
    def print_usage(self) -> None:
        """Print usage message."""
        pass


class AColorBase(ABC):
    """Abstract base class for color operations."""
    
    @abstractmethod
    def colorize(self, text: str, color: ColorType) -> str:
        """Apply color to text."""
        pass
    
    @abstractmethod
    def supports_color(self) -> bool:
        """Check if color is supported."""
        pass
    
    @abstractmethod
    def get_color_codes(self) -> dict[ColorType, str]:
        """Get color codes mapping."""
        pass


class BaseCLI(ICLI):
    """Base CLI implementation."""
    
    def __init__(self, name: str = "xwsystem", version: str = None):
        """Initialize the CLI.
        
        Args:
            name: CLI name
            version: CLI version (defaults to package version)
        """
        self._name = name
        self._version = version or __version__
        self._commands: dict[str, Any] = {}
        self._options: dict[str, Any] = {}
    
    @property
    def name(self) -> str:
        """Get CLI name."""
        return self._name
    
    @property
    def version(self) -> str:
        """Get CLI version."""
        return self._version
    
    def add_command(self, name: str, command: Any) -> None:
        """Add a command to the CLI.
        
        Args:
            name: Command name
            command: Command implementation
        """
        self._commands[name] = command
    
    def add_option(self, name: str, option: Any) -> None:
        """Add an option to the CLI.
        
        Args:
            name: Option name
            option: Option implementation
        """
        self._options[name] = option
    
    def run(self, args: Optional[list[str]] = None) -> int:
        """Run the CLI.
        
        Args:
            args: Command line arguments
            
        Returns:
            Exit code
        """
        # Basic implementation - can be overridden
        return 0
    
    def get_help(self) -> str:
        """Get help text."""
        return f"{self._name} v{self._version} - XWSystem CLI"


class BaseCLI(ICLI):
    """Base CLI implementation for backward compatibility."""
    
    def __init__(self, name: str = "xwsystem", version: str = None):
        """Initialize base CLI."""
        self._name = name
        self._version = version or __version__
        self._commands: dict[str, Any] = {}
        self._options: dict[str, Any] = {}
    
    @property
    def name(self) -> str:
        """Get CLI name."""
        return self._name
    
    @property
    def version(self) -> str:
        """Get CLI version."""
        return self._version
    
    def add_command(self, name: str, command: Any) -> None:
        """Add a command to the CLI."""
        self._commands[name] = command
    
    def add_option(self, name: str, option: Any) -> None:
        """Add an option to the CLI."""
        self._options[name] = option
    
    def run(self, args: Optional[list[str]] = None) -> int:
        """Run the CLI."""
        if not args:
            args = []
        
        if not args or args[0] in ['-h', '--help']:
            print(self.get_help())
            return 0
        
        command_name = args[0]
        if command_name in self._commands:
            command = self._commands[command_name]
            if hasattr(command, 'run'):
                return command.run(args[1:])
            else:
                print(f"Command '{command_name}' is not executable")
                return 1
        else:
            print(f"Unknown command: {command_name}")
            print(self.get_help())
            return 1
    
    def get_help(self) -> str:
        """Get help text."""
        help_text = f"{self._name} v{self._version} - XWSystem CLI\n\n"
        help_text += "Available commands:\n"
        for cmd_name in self._commands.keys():
            help_text += f"  {cmd_name}\n"
        help_text += "\nUse -h or --help for this help message."
        return help_text
