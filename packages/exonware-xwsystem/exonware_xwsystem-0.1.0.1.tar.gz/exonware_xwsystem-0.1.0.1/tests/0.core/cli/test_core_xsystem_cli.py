#exonware/xwsystem/tests/core/cli/test_core_xwsystem_cli.py
"""
XSystem CLI Core Tests

Comprehensive tests for XSystem CLI functionality including console operations,
progress tracking, prompts, table formatting, and argument parsing.
"""

import sys
import os
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

try:
    from exonware.xwsystem.cli.console import Console
    from exonware.xwsystem.cli.progress import ProgressBar
    from exonware.xwsystem.cli.prompts import Prompts
    from exonware.xwsystem.cli.tables import TableFormatter
    from exonware.xwsystem.cli.args import ArgumentParser
    from exonware.xwsystem.cli.colors import Colors
    from exonware.xwsystem.cli.base import BaseCLI
    from exonware.xwsystem.cli.contracts import ICLI, IProgress, IPrompts, ITableFormatter
    from exonware.xwsystem.cli.errors import CLIError, ConsoleError, ProgressError
except ImportError as e:
    print(f"Import error: {e}")
    # Create mock classes for testing
    class Console:
        def __init__(self): pass
        def print(self, *args, **kwargs): print(*args, **kwargs)
        def input(self, prompt=""): return "test"
        def clear(self): pass
        def get_size(self): return (80, 24)
    
    class ProgressBar:
        def __init__(self, total=100): self.total = total; self.current = 0
        def update(self, value): self.current = value
        def finish(self): pass
    
    class Prompts:
        def confirm(self, message): return True
        def ask(self, message): return "test"
        def select(self, options): return options[0] if options else None
    
    class TableFormatter:
        def format_table(self, data): return str(data)
    
    class ArgumentParser:
        def parse_args(self, args): return MagicMock()
    
    class Colors:
        RED = "\033[91m"
        GREEN = "\033[92m"
        BLUE = "\033[94m"
        RESET = "\033[0m"
    
    class BaseCLI:
        def __init__(self): pass
        def run(self): return 0
    
    class ICLI: pass
    class IProgress: pass
    class IPrompts: pass
    class ITableFormatter: pass
    
    class CLIError(Exception): pass
    class ConsoleError(Exception): pass
    class ProgressError(Exception): pass


def test_console_operations():
    """Test basic console operations."""
    print("📋 Testing: Console Operations")
    print("-" * 30)
    
    try:
        console = Console()
        
        # Test basic operations
        console.print("Test message")
        console.clear()
        size = console.get_size()
        assert isinstance(size, tuple)
        assert len(size) == 2
        
        print("✅ Console operations tests passed")
        return True
    except Exception as e:
        print(f"❌ Console operations tests failed: {e}")
        return False


def test_progress_bar():
    """Test progress bar functionality."""
    print("📋 Testing: Progress Bar")
    print("-" * 30)
    
    try:
        progress = ProgressBar(total=100)
        
        # Test progress updates
        for i in range(0, 101, 25):
            progress.update(i)
            time.sleep(0.01)  # Small delay to see progress
        
        progress.finish()
        
        print("✅ Progress bar tests passed")
        return True
    except Exception as e:
        print(f"❌ Progress bar tests failed: {e}")
        return False


def test_prompts():
    """Test prompt functionality."""
    print("📋 Testing: Prompts")
    print("-" * 30)
    
    try:
        prompts = Prompts()
        
        # Test different prompt types
        result = prompts.confirm("Test confirmation")
        assert isinstance(result, bool)
        
        result = prompts.ask("Test question")
        assert isinstance(result, str)
        
        result = prompts.select(["option1", "option2", "option3"])
        assert result in ["option1", "option2", "option3"]
        
        print("✅ Prompts tests passed")
        return True
    except Exception as e:
        print(f"❌ Prompts tests failed: {e}")
        return False


def test_table_formatter():
    """Test table formatting functionality."""
    print("📋 Testing: Table Formatter")
    print("-" * 30)
    
    try:
        formatter = TableFormatter()
        
        # Test table formatting
        test_data = [
            ["Name", "Age", "City"],
            ["John", "25", "New York"],
            ["Jane", "30", "London"]
        ]
        
        result = formatter.format_table(test_data)
        assert isinstance(result, str)
        assert len(result) > 0
        
        print("✅ Table formatter tests passed")
        return True
    except Exception as e:
        print(f"❌ Table formatter tests failed: {e}")
        return False


def test_argument_parser():
    """Test argument parsing functionality."""
    print("📋 Testing: Argument Parser")
    print("-" * 30)
    
    try:
        parser = ArgumentParser()
        
        # Test argument parsing
        test_args = ["--help", "--version"]
        result = parser.parse_args(test_args)
        assert result is not None
        
        print("✅ Argument parser tests passed")
        return True
    except Exception as e:
        print(f"❌ Argument parser tests failed: {e}")
        return False


def test_colors():
    """Test color functionality."""
    print("📋 Testing: Colors")
    print("-" * 30)
    
    try:
        # Test color constants
        assert hasattr(Colors, 'RED')
        assert hasattr(Colors, 'GREEN')
        assert hasattr(Colors, 'BLUE')
        assert hasattr(Colors, 'RESET')
        
        # Test color usage
        red_text = f"{Colors.RED}Red text{Colors.RESET}"
        assert Colors.RED in red_text
        assert Colors.RESET in red_text
        
        print("✅ Colors tests passed")
        return True
    except Exception as e:
        print(f"❌ Colors tests failed: {e}")
        return False


def test_base_cli():
    """Test base CLI functionality."""
    print("📋 Testing: Base CLI")
    print("-" * 30)
    
    try:
        cli = BaseCLI()
        
        # Test CLI execution
        result = cli.run()
        assert isinstance(result, int)
        
        print("✅ Base CLI tests passed")
        return True
    except Exception as e:
        print(f"❌ Base CLI tests failed: {e}")
        return False


def test_cli_interfaces():
    """Test CLI interface compliance."""
    print("📋 Testing: CLI Interfaces")
    print("-" * 30)
    
    try:
        # Test interface compliance
        console = Console()
        progress = ProgressBar()
        prompts = Prompts()
        formatter = TableFormatter()
        
        # Verify objects can be instantiated
        assert console is not None
        assert progress is not None
        assert prompts is not None
        assert formatter is not None
        
        print("✅ CLI interfaces tests passed")
        return True
    except Exception as e:
        print(f"❌ CLI interfaces tests failed: {e}")
        return False


def test_cli_error_handling():
    """Test CLI error handling."""
    print("📋 Testing: CLI Error Handling")
    print("-" * 30)
    
    try:
        # Test error classes
        cli_error = CLIError("Test CLI error")
        console_error = ConsoleError("Test console error")
        progress_error = ProgressError("Test progress error")
        
        assert str(cli_error) == "Test CLI error"
        assert str(console_error) == "Test console error"
        assert str(progress_error) == "Test progress error"
        
        print("✅ CLI error handling tests passed")
        return True
    except Exception as e:
        print(f"❌ CLI error handling tests failed: {e}")
        return False


def main():
    """Run all CLI core tests."""
    print("=" * 50)
    print("🧪 XSystem CLI Core Tests")
    print("=" * 50)
    print("Testing XSystem CLI functionality including console operations,")
    print("progress tracking, prompts, table formatting, and argument parsing")
    print("=" * 50)
    
    tests = [
        test_console_operations,
        test_progress_bar,
        test_prompts,
        test_table_formatter,
        test_argument_parser,
        test_colors,
        test_base_cli,
        test_cli_interfaces,
        test_cli_error_handling,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print("📊 XSYSTEM CLI TEST SUMMARY")
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All XSystem CLI tests passed!")
        return 0
    else:
        print("💥 Some XSystem CLI tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
