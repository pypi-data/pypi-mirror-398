"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.411
Generation Date: 11-Oct-2025

Reusable test runner utilities with colored output and Markdown generation.
Designed to minimize code duplication across all eXonware test runners.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

# Set UTF-8 encoding for Windows console to support emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        # If reconfigure not available or fails, continue without it
        pass

# Import colors from xwsystem CLI module
try:
    from exonware.xwsystem.cli.colors import ColoredOutput, Colors, Style
except ImportError:
    # Fallback if running standalone
    class ColoredOutput:
        def colorize(self, text, color, style=None):
            return text
        def success(self, text, **kwargs):
            print(f"✅ {text}", **kwargs)
        def error(self, text, **kwargs):
            print(f"❌ {text}", **kwargs)
        def warning(self, text, **kwargs):
            print(f"⚠️  {text}", **kwargs)
        def header(self, text, **kwargs):
            print(text, **kwargs)
        def subheader(self, text, **kwargs):
            print(text, **kwargs)
        def info(self, text, **kwargs):
            print(f"ℹ️  {text}", **kwargs)
    
    Colors = None
    Style = None


class DualOutput:
    """
    Capture output for both terminal (with colors/emojis) and Markdown file.
    
    Features:
    - Colored terminal output with emojis
    - Clean Markdown output without ANSI codes
    - Automatic file path formatting
    - Timestamped output
    """
    
    def __init__(self, output_file: Path):
        """
        Initialize dual output handler.
        
        Args:
            output_file: Path to Markdown output file
        """
        self.output_file = output_file
        self.colored = ColoredOutput()
        self.markdown_lines = []
        
    def print(self, text: str = "", markdown_format: Optional[str] = None, 
              color: Optional[str] = None, emoji: Optional[str] = None):
        """
        Print to terminal and capture for Markdown.
        
        Args:
            text: Text to print
            markdown_format: Optional Markdown-specific format
            color: Optional color name (success, error, info, header, subheader)
            emoji: Optional emoji to prepend
        """
        # Terminal output with color and emoji
        display_text = text
        if emoji:
            display_text = f"{emoji} {text}"
        
        # Handle Unicode encoding errors gracefully
        try:
            if color:
                if color == 'success':
                    self.colored.success(display_text)
                elif color == 'error':
                    self.colored.error(display_text)
                elif color == 'info':
                    self.colored.info(display_text)
                elif color == 'header':
                    self.colored.header(display_text)
                elif color == 'subheader':
                    self.colored.subheader(display_text)
                else:
                    print(display_text)
            else:
                print(display_text)
        except UnicodeEncodeError:
            # Fallback without emoji if encoding fails
            if color:
                if color == 'success':
                    self.colored.success(text)
                elif color == 'error':
                    self.colored.error(text)
                elif color == 'info':
                    self.colored.info(text)
                elif color == 'header':
                    self.colored.header(text)
                elif color == 'subheader':
                    self.colored.subheader(text)
                else:
                    print(text)
            else:
                print(text)
        
        # Markdown output (clean, no colors)
        if markdown_format:
            self.markdown_lines.append(markdown_format)
        else:
            # Clean emoji and special chars for Markdown
            cleaned = text.replace("="*80, "---")
            if emoji:
                cleaned = f"{emoji} {cleaned}"
            self.markdown_lines.append(cleaned)
    
    def save(self, header_info: dict):
        """
        Save Markdown output to file.
        
        Args:
            header_info: Dictionary with header information
                - library: Library name
                - layer: Test layer
                - description: Description
        """
        header = f"""# Test Runner Output

**Library:** {header_info.get('library', 'unknown')}  
**Layer:** {header_info.get('layer', 'unknown')}  
**Generated:** {datetime.now().strftime("%d-%b-%Y %H:%M:%S")}  
**Description:** {header_info.get('description', 'Test execution')}

---

"""
        content = header + "\n".join(self.markdown_lines) + "\n"
        self.output_file.write_text(content, encoding='utf-8')


def format_path(path: Path, relative_to: Optional[Path] = None) -> str:
    """
    Format path for display with full absolute path.
    
    Args:
        path: Path to format
        relative_to: Optional base path to show relative path alongside absolute
        
    Returns:
        Formatted path string
    """
    abs_path = path.resolve()
    
    if relative_to:
        try:
            rel_path = path.relative_to(relative_to)
            return f"{abs_path} (relative: {rel_path})"
        except ValueError:
            # Not relative to the base
            pass
    
    return str(abs_path)


def print_header(title: str, output: Optional[DualOutput] = None):
    """
    Print a formatted header with separator.
    
    Args:
        title: Header title
        output: Optional DualOutput instance for dual output
    """
    separator = "=" * 80
    
    if output:
        output.print(separator, "---")
        output.print(title, f"# {title}", color='header')  # No extra emoji - colored.header adds ℹ
        output.print(separator, "---")
    else:
        colored = ColoredOutput()
        print(separator)
        colored.header(f"🎯 {title}")
        print(separator)


def print_section(title: str, output: Optional[DualOutput] = None):
    """
    Print a formatted section header.
    
    Args:
        title: Section title
        output: Optional DualOutput instance for dual output
    """
    if output:
        output.print(f"\n{title}", f"\n## {title}", color='subheader')  # No extra emoji
    else:
        colored = ColoredOutput()
        colored.subheader(f"\n📋 {title}")


def print_status(success: bool, message: str, output: Optional[DualOutput] = None):
    """
    Print a status message with appropriate color and emoji.
    
    Args:
        success: True for success, False for failure
        message: Status message
        output: Optional DualOutput instance for dual output
    """
    if success:
        emoji = '✅'
        color = 'success'
    else:
        emoji = '❌'
        color = 'error'
    
    if output:
        output.print(message, f"{emoji} {message}", color=color)  # No extra emoji - colored method adds ✓/✗
    else:
        colored = ColoredOutput()
        if success:
            colored.success(message)
        else:
            colored.error(message)


def run_pytest(
    test_dir: Path,
    markers: list[str],
    options: Optional[list[str]] = None,
    output: Optional[DualOutput] = None
) -> tuple[int, str, str]:
    """
    Run pytest with specified options and capture output.
    
    Args:
        test_dir: Directory containing tests
        markers: List of pytest markers to run
        options: Additional pytest options
        output: Optional DualOutput instance for logging
        
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    if options is None:
        options = ["-v", "--tb=short"]
    
    cmd = [sys.executable, "-m", "pytest"] + options + [str(test_dir)]
    
    # Add markers
    if markers:
        cmd.extend(["-m", " or ".join(markers)])
    
    # Print command
    cmd_str = " ".join(cmd)
    if output:
        output.print(f"Command: {cmd_str}", f"```bash\n{cmd_str}\n```", color='info')  # No extra emoji
        output.print(f"Working directory: {format_path(test_dir.parent)}", 
                    f"**Working directory:** `{format_path(test_dir.parent)}`",
                    color='info')
    
    # Run pytest
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=test_dir.parent
    )
    
    return result.returncode, result.stdout, result.stderr


class TestRunner:
    """
    Reusable test runner with colored output and Markdown generation.
    
    Features:
    - Automatic path formatting (full absolute paths)
    - Colored terminal output with emojis
    - Markdown output generation
    - Exit code handling
    - Summary statistics
    
    Usage:
        runner = TestRunner(
            library_name="xwnode",
            layer_name="0.core",
            description="Core Tests - Fast, High-Value Checks"
        )
        runner.run()
    """
    
    def __init__(
        self,
        library_name: str,
        layer_name: str,
        description: str,
        test_dir: Optional[Path] = None,
        markers: Optional[list[str]] = None,
        output_file: Optional[Path] = None
    ):
        """
        Initialize test runner.
        
        Args:
            library_name: Name of library (e.g., 'xwnode', 'xwsystem')
            layer_name: Test layer (e.g., '0.core', '1.unit')
            description: Description of test layer
            test_dir: Directory containing tests (auto-detected if None)
            markers: Pytest markers to run (auto-detected if None)
            output_file: Output file path (auto-detected if None)
        """
        self.library_name = library_name
        self.layer_name = layer_name
        self.description = description
        
        # Auto-detect paths
        if test_dir is None:
            # Assume runner is in the test directory
            self.test_dir = Path.cwd()
        else:
            self.test_dir = test_dir
        
        # Default markers based on layer
        if markers is None:
            marker_name = library_name.lower().replace('-', '_').replace('exonware-', '')
            if 'core' in layer_name:
                markers = [f"{marker_name}_core"]
            elif 'unit' in layer_name:
                markers = [f"{marker_name}_unit"]
            elif 'integration' in layer_name:
                markers = [f"{marker_name}_integration"]
            elif 'advance' in layer_name:
                markers = [f"{marker_name}_advance"]
            else:
                markers = []
        self.markers = markers
        
        # Output file
        if output_file is None:
            self.output_file = self.test_dir / "runner_out.md"
        else:
            self.output_file = output_file
        
        # Create output handler
        self.output = DualOutput(self.output_file)
    
    def run(self) -> int:
        """
        Run tests and generate output.
        Auto-discovers sub-runners and test files.
        
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        # Print header
        print_header(f"{self.library_name} - {self.description}", self.output)
        
        # Print paths
        self.output.print(f"Test Directory: {format_path(self.test_dir)}", 
                         f"**Test Directory:** `{format_path(self.test_dir)}`",
                         color='info')  # No extra emoji - colored.info adds ℹ
        self.output.print(f"Output File: {format_path(self.output_file)}",
                         f"**Output File:** `{format_path(self.output_file)}`",
                         color='info')
        
        # Add src to Python path
        src_path = self.test_dir.parent.parent / "src"
        if src_path.exists():
            sys.path.insert(0, str(src_path))
            self.output.print(f"Added to path: {format_path(src_path)}",
                            f"**Added to path:** `{format_path(src_path)}`",
                            color='info')
        
        # Auto-discovery: Check for sub-runners first
        sub_runners = []
        for subdir in sorted(self.test_dir.iterdir()):
            if subdir.is_dir() and not subdir.name.startswith('__'):
                runner_path = subdir / "runner.py"
                if runner_path.exists():
                    sub_runners.append((subdir.name, runner_path))
        
        # If sub-runners found, execute them
        if sub_runners:
            self.output.print(f"\nDiscovered {len(sub_runners)} sub-module(s) with runners", 
                            f"\n**Discovered:** {len(sub_runners)} sub-module(s) with runners",
                            color='info')
            
            exit_codes = []
            for subdir_name, runner_path in sub_runners:
                self.output.print(f"   Sub-module: {subdir_name}",
                                f"- Sub-module: `{subdir_name}`",
                                color='subheader')
                result = subprocess.run([sys.executable, str(runner_path)])
                exit_codes.append(result.returncode)
            
            # Aggregate results
            success = all(code == 0 for code in exit_codes)
            exit_code = 0 if success else 1
            
            # Print final status
            status_emoji = "✅" if success else "❌"
            status_text = "ALL SUB-MODULES PASSED" if success else "SOME SUB-MODULES FAILED"
            
            if self.output.colored:
                if success:
                    self.output.colored.success(f"\n{status_emoji} {status_text}")
                else:
                    self.output.colored.error(f"\n{status_emoji} {status_text}")
            else:
                print(f"\n{status_emoji} {status_text}")
            
            # Add status to markdown
            self.output.markdown_lines.append(f"\n**Status:** {status_emoji} {status_text}\n")
            self.output.markdown_lines.append(f"\n**Sub-module Results:** {sum(1 for c in exit_codes if c == 0)}/{len(exit_codes)} passed\n")
        
        else:
            # No sub-runners: scan for test files and run pytest directly
            test_files = list(self.test_dir.glob("test_*.py"))
            self.output.print(f"\nDiscovered {len(test_files)} test file(s)",
                            f"\n**Discovered:** {len(test_files)} test file(s)",
                            color='info')
            
            print_section("Running Tests", self.output)
            exit_code, stdout, stderr = run_pytest(
                self.test_dir,
                self.markers,
                output=self.output
            )
            
            # Show pytest output to terminal
            if stdout:
                print(stdout)
            
            if stderr:
                print(stderr, file=sys.stderr)
            
            # Add full output to markdown
            if stdout:
                self.output.markdown_lines.append("\n### Test Output\n```")
                self.output.markdown_lines.append(stdout)
                self.output.markdown_lines.append("```")
            
            if stderr:
                self.output.markdown_lines.append("\n### Errors\n```")
                self.output.markdown_lines.append(stderr)
                self.output.markdown_lines.append("```")
            
            # Extract summary line (the line with === and test counts)
            summary_line = None
            for line in stdout.split('\n'):
                if '===' in line and ('passed' in line.lower() or 'failed' in line.lower()):
                    summary_line = line.strip()
                    break
            
            # Print colorful summary as separator
            print()  # Blank line before summary
            if summary_line:
                # Color the summary line
                if self.output.colored:
                    # Parse the summary to colorize different parts
                    if 'passed' in summary_line.lower() and 'failed' not in summary_line.lower():
                        # All passed - show in green
                        self.output.colored.success(f"\n{summary_line}\n")
                    elif 'failed' in summary_line.lower():
                        # Some failed - show in red
                        self.output.colored.error(f"\n{summary_line}\n")
                    else:
                        # Other status - show normally
                        print(f"\n{summary_line}\n")
                else:
                    print(f"\n{summary_line}\n")
                
                # Add summary to markdown
                self.output.markdown_lines.append(f"\n### Summary\n\n```\n{summary_line}\n```")
            
            # Print final status (concise - no duplication)
            success = exit_code == 0
            status_emoji = "✅" if success else "❌"
            status_text = "PASSED" if success else "FAILED"
            
            if self.output.colored:
                if success:
                    self.output.colored.success(f"{status_emoji} {status_text}")
                else:
                    self.output.colored.error(f"{status_emoji} {status_text}")
            else:
                print(f"{status_emoji} {status_text}")
            
            # Add status to markdown only
            self.output.markdown_lines.append(f"\n**Status:** {status_emoji} {status_text}\n")
        
        # Save output
        self.output.save({
            'library': self.library_name,
            'layer': self.layer_name,
            'description': self.description
        })
        
        # Print save location
        save_msg = f"Results saved to: {format_path(self.output_file)}"
        if self.output.colored:
            self.output.colored.info(save_msg)
        else:
            print(f"💾 {save_msg}")
        
        return exit_code

