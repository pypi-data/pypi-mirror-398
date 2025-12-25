"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

CLI module contracts - interfaces and enums for command-line interface functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union

# Import enums from types module
from .defs import (
    ColorType,
    ProgressStyle,
    TableStyle,
    PromptType,
    Alignment,
    BorderStyle,
    Colors,
    Style,
    ArgumentType
)


class IConsole(ABC):
    """Interface for console operations."""
    
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


class IProgressBar(ABC):
    """Interface for progress bar operations."""
    
    @abstractmethod
    def start(self, total: int, description: str = "") -> None:
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


class ITable(ABC):
    """Interface for table operations."""
    
    @abstractmethod
    def add_row(self, *values: Any) -> None:
        """Add row to table."""
        pass
    
    @abstractmethod
    def render(self) -> str:
        """Render table as string."""
        pass


class IPrompt(ABC):
    """Interface for user prompts."""
    
    @abstractmethod
    def ask(self, question: str, **kwargs) -> Any:
        """Ask user a question."""
        pass


class IArgumentParser(ABC):
    """Interface for argument parsing."""
    
    @abstractmethod
    def add_argument(self, *args, **kwargs) -> None:
        """Add argument to parser."""
        pass
    
    @abstractmethod
    def parse_args(self, args: Optional[list[str]] = None) -> Any:
        """Parse command line arguments."""
        pass


class ICLI(ABC):
    """Interface for CLI operations."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get CLI name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Get CLI version."""
        pass
    
    @abstractmethod
    def add_command(self, name: str, command: Any) -> None:
        """Add a command to the CLI."""
        pass
    
    @abstractmethod
    def add_option(self, name: str, option: Any) -> None:
        """Add an option to the CLI."""
        pass
    
    @abstractmethod
    def run(self, args: Optional[list[str]] = None) -> int:
        """Run the CLI."""
        pass
    
    @abstractmethod
    def get_help(self) -> str:
        """Get help text."""
        pass


class IProgress(ABC):
    """Interface for progress operations."""
    
    @abstractmethod
    def start(self, total: int, description: str = "") -> None:
        """Start progress tracking."""
        pass
    
    @abstractmethod
    def update(self, increment: int = 1) -> None:
        """Update progress."""
        pass
    
    @abstractmethod
    def finish(self) -> None:
        """Finish progress tracking."""
        pass


class IPrompts(ABC):
    """Interface for user prompts."""
    
    @abstractmethod
    def ask(self, question: str, **kwargs) -> Any:
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


class ITableFormatter(ABC):
    """Interface for table formatting."""
    
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