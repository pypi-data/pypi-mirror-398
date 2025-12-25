"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

CLI module errors - exception classes for command-line interface functionality.
"""


class CLIError(Exception):
    """Base exception for CLI errors."""
    pass


class ArgumentError(CLIError):
    """Raised when command line argument is invalid."""
    pass


class CommandError(CLIError):
    """Raised when command execution fails."""
    pass


class ConsoleError(CLIError):
    """Raised when console operation fails."""
    pass


class ColorError(CLIError):
    """Raised when color operation fails."""
    pass


class ProgressError(CLIError):
    """Raised when progress bar operation fails."""
    pass


class TableError(CLIError):
    """Raised when table operation fails."""
    pass


class PromptError(CLIError):
    """Raised when user prompt operation fails."""
    pass


class InputError(CLIError):
    """Raised when user input is invalid."""
    pass


class OutputError(CLIError):
    """Raised when output operation fails."""
    pass


class TerminalError(CLIError):
    """Raised when terminal operation fails."""
    pass


class FormatError(CLIError):
    """Raised when formatting operation fails."""
    pass


class CLIValidationError(CLIError):
    """Raised when CLI validation fails."""
    pass
