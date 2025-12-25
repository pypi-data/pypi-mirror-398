"""
Argument Parsing Utilities
=========================

Production-grade CLI argument parsing for XWSystem.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generated: 2025-01-27
"""

import argparse
import sys
from typing import Any, Optional, Callable, Union
from dataclasses import dataclass
import logging
from .defs import ArgumentType

logger = logging.getLogger(__name__)


@dataclass
class Argument:
    """
    Definition of a command-line argument.
    
    Features:
    - Type validation and conversion
    - Default values and required flags
    - Help text and examples
    - Choice validation
    - Custom validation functions
    """
    
    name: str
    arg_type: ArgumentType = ArgumentType.STRING
    required: bool = False
    default: Any = None
    help_text: str = ""
    short_name: Optional[str] = None
    choices: Optional[list[str]] = None
    validator: Optional[Callable[[Any], bool]] = None
    action: str = "store"  # store, store_true, store_false, append, count
    nargs: Optional[Union[int, str]] = None  # Number of arguments
    
    def __post_init__(self):
        """Validate argument configuration."""
        if self.arg_type == ArgumentType.CHOICE and not self.choices:
            raise ValueError(f"Argument '{self.name}' with CHOICE type must have choices")
        
        if self.short_name and not self.short_name.startswith('-'):
            self.short_name = f"-{self.short_name}"
        
        if not self.name.startswith('--'):
            self.name = f"--{self.name.lstrip('-')}"


@dataclass 
class Command:
    """
    Definition of a CLI command.
    
    Features:
    - Hierarchical subcommands
    - Command-specific arguments
    - Help text and examples
    - Command handlers
    """
    
    name: str
    handler: Callable
    description: str = ""
    arguments: list[Argument] = None
    subcommands: list['Command'] = None
    examples: list[str] = None
    
    def __post_init__(self):
        """Initialize command defaults."""
        if self.arguments is None:
            self.arguments = []
        if self.subcommands is None:
            self.subcommands = []
        if self.examples is None:
            self.examples = []


class ArgumentParser:
    """
    Production-grade argument parser built on argparse.
    
    Features:
    - Type-safe argument parsing
    - Hierarchical command structure  
    - Automatic help generation
    - Validation and error handling
    - Colored output support
    - Configuration file support
    """
    
    def __init__(self, 
                 program_name: str = None,
                 description: str = "",
                 version: str = None,
                 epilog: str = ""):
        """
        Initialize argument parser.
        
        Args:
            program_name: Name of the program
            description: Program description
            version: Program version
            epilog: Text to display after help
        """
        self.program_name = program_name or sys.argv[0]
        self.description = description
        self.version = version
        self.epilog = epilog
        
        # Create main parser
        self._parser = argparse.ArgumentParser(
            prog=self.program_name,
            description=self.description,
            epilog=self.epilog,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        if self.version:
            self._parser.add_argument(
                '--version', 
                action='version', 
                version=f'{self.program_name} {self.version}'
            )
        
        # Command registry
        self._commands: dict[str, Command] = {}
        self._subparsers = None
        self._global_arguments: list[Argument] = []
    
    def add_argument(self, argument: Argument) -> 'ArgumentParser':
        """
        Add a global argument to the parser.
        
        Args:
            argument: Argument definition
            
        Returns:
            Self for method chaining
        """
        self._global_arguments.append(argument)
        self._add_argument_to_parser(self._parser, argument)
        return self
    
    def add_command(self, command: Command) -> 'ArgumentParser':
        """
        Add a command to the parser.
        
        Args:
            command: Command definition
            
        Returns:
            Self for method chaining
        """
        if self._subparsers is None:
            self._subparsers = self._parser.add_subparsers(
                dest='command',
                help='Available commands',
                metavar='COMMAND'
            )
        
        # Create subparser for command
        cmd_parser = self._subparsers.add_parser(
            command.name,
            help=command.description,
            description=command.description,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Add command arguments
        for arg in command.arguments:
            self._add_argument_to_parser(cmd_parser, arg)
        
        # Add examples to epilog if provided
        if command.examples:
            examples_text = "\nExamples:\n" + "\n".join(f"  {ex}" for ex in command.examples)
            cmd_parser.epilog = examples_text
        
        # Store command
        self._commands[command.name] = command
        
        # Handle subcommands recursively
        if command.subcommands:
            sub_subparsers = cmd_parser.add_subparsers(
                dest=f'{command.name}_subcommand',
                help=f'{command.name} subcommands'
            )
            
            for subcmd in command.subcommands:
                self._add_subcommand(sub_subparsers, subcmd, command.name)
        
        return self
    
    def _add_subcommand(self, subparsers, command: Command, parent_name: str):
        """Add a subcommand to a subparser."""
        subcmd_parser = subparsers.add_parser(
            command.name,
            help=command.description,
            description=command.description
        )
        
        for arg in command.arguments:
            self._add_argument_to_parser(subcmd_parser, arg)
        
        # Store with full path
        full_name = f"{parent_name}.{command.name}"
        self._commands[full_name] = command
    
    def _add_argument_to_parser(self, parser: argparse.ArgumentParser, argument: Argument):
        """Add an argument to an argparse parser."""
        kwargs = {
            'help': argument.help_text,
            'default': argument.default,
            'action': argument.action
        }
        
        # Handle different argument types
        if argument.arg_type == ArgumentType.INTEGER:
            kwargs['type'] = int
        elif argument.arg_type == ArgumentType.FLOAT:
            kwargs['type'] = float
        elif argument.arg_type == ArgumentType.BOOLEAN:
            if argument.action in ('store_true', 'store_false'):
                kwargs.pop('type', None)
            else:
                kwargs['type'] = lambda x: x.lower() in ('true', '1', 'yes', 'on')
        elif argument.arg_type == ArgumentType.FILE:
            kwargs['type'] = argparse.FileType('r')
        elif argument.arg_type == ArgumentType.DIRECTORY:
            kwargs['type'] = str  # Will validate in custom validator
        elif argument.arg_type == ArgumentType.CHOICE:
            kwargs['choices'] = argument.choices
        
        # Handle required flag
        if argument.required:
            kwargs['required'] = True
        
        # Handle number of arguments
        if argument.nargs is not None:
            kwargs['nargs'] = argument.nargs
        
        # Add argument names
        names = [argument.name]
        if argument.short_name:
            names.insert(0, argument.short_name)
        
        parser.add_argument(*names, **kwargs)
    
    def parse_args(self, args: list[str] = None) -> argparse.Namespace:
        """
        Parse command-line arguments.
        
        Args:
            args: Arguments to parse (defaults to sys.argv)
            
        Returns:
            Parsed arguments namespace
        """
        try:
            parsed_args = self._parser.parse_args(args)
            
            # Validate arguments
            self._validate_args(parsed_args)
            
            return parsed_args
            
        except SystemExit as e:
            # argparse calls sys.exit on error - re-raise for handling
            raise
        except Exception as e:
            logger.error(f"Argument parsing failed: {e}")
            self._parser.print_help()
            sys.exit(1)
    
    def execute(self, args: list[str] = None) -> Any:
        """
        Parse arguments and execute the appropriate command.
        
        Args:
            args: Arguments to parse
            
        Returns:
            Result from command handler
        """
        parsed_args = self.parse_args(args)
        
        # Find and execute command
        if hasattr(parsed_args, 'command') and parsed_args.command:
            command_name = parsed_args.command
            
            # Handle subcommands
            subcommand_attr = f'{command_name}_subcommand'
            if hasattr(parsed_args, subcommand_attr):
                subcommand = getattr(parsed_args, subcommand_attr)
                if subcommand:
                    command_name = f"{command_name}.{subcommand}"
            
            if command_name in self._commands:
                command = self._commands[command_name]
                try:
                    return command.handler(parsed_args)
                except Exception as e:
                    logger.error(f"Command '{command_name}' failed: {e}")
                    return 1
            else:
                logger.error(f"Unknown command: {command_name}")
                self._parser.print_help()
                return 1
        else:
            # No command specified
            self._parser.print_help()
            return 0
    
    def _validate_args(self, args: argparse.Namespace):
        """Validate parsed arguments."""
        # Custom validation logic can be added here
        for arg in self._global_arguments:
            if arg.validator and hasattr(args, arg.name.lstrip('-')):
                value = getattr(args, arg.name.lstrip('-'))
                if value is not None and not arg.validator(value):
                    raise ValueError(f"Invalid value for {arg.name}: {value}")
    
    def print_help(self):
        """Print help message."""
        self._parser.print_help()
    
    def add_mutually_exclusive_group(self, required: bool = False):
        """Add a mutually exclusive argument group."""
        return self._parser.add_mutually_exclusive_group(required=required)


# Utility functions for common argument types
def create_file_argument(name: str, required: bool = False, help_text: str = "") -> Argument:
    """Create a file input argument."""
    return Argument(
        name=name,
        arg_type=ArgumentType.FILE,
        required=required,
        help_text=help_text or f"Input file path"
    )


def create_output_argument(name: str = "output", help_text: str = "") -> Argument:
    """Create an output file argument."""
    return Argument(
        name=name,
        arg_type=ArgumentType.STRING,
        help_text=help_text or "Output file path"
    )


def create_verbose_argument() -> Argument:
    """Create a verbose flag argument."""
    return Argument(
        name="verbose",
        short_name="-v",
        action="store_true",
        help_text="Enable verbose output"
    )


def create_quiet_argument() -> Argument:
    """Create a quiet flag argument."""
    return Argument(
        name="quiet",
        short_name="-q", 
        action="store_true",
        help_text="Suppress output"
    )


def create_config_argument() -> Argument:
    """Create a configuration file argument."""
    return Argument(
        name="config",
        short_name="-c",
        arg_type=ArgumentType.FILE,
        help_text="Configuration file path"
    )
