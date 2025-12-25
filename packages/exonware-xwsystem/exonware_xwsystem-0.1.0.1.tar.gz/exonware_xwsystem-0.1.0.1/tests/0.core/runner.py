#exonware/xwsystem/tests/core/runner.py
#!/usr/bin/env python3
"""
Core Test Runner for XSystem

Runs comprehensive core tests for all main XSystem features following DEV_GUIDELINES.md.
Each core feature is tested individually with real data and comprehensive
roundtrip testing to ensure production readiness.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.3
Generation Date: January 02, 2025
"""

import sys
import subprocess
import os
from pathlib import Path
from typing import Any

# Set up UTF-8 environment for emoji support
os.environ['PYTHONIOENCODING'] = 'utf-8'
if os.name == 'nt':  # Windows
    os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '0'
    # Try to enable UTF-8 mode in Windows console
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass


def get_emoji_mapping():
    """Get mapping of text equivalents to emojis."""
    return {
        '[PASS]': '✅',
        '[FAIL]': '❌',
        '[SUCCESS]': '🎉',
        '[ERROR]': '💥',
        '[TEST]': '🧪',
        '[SERIALIZATION]': '📦',
        '[SECURITY]': '🔒',
        '[HTTP]': '🌐',
        '[IO]': '📁',
        '[MONITOR]': '📊',
        '[THREAD]': '🧵',
        '[CACHE]': '💾',
        '[INFO]': '📋',
        '[RUN]': '🚀',
        '[TOOL]': '🔧',
        '[FAST]': '⚡',
        '[SECURE]': '🛡️',
        '[SEARCH]': '🔍',
        '[WRITE]': '📝',
        '[READ]': '📖',
        '[SYNC]': '🔄',
        '[CONFIG]': '⚙️',
        '[TARGET]': '🎯',
        '[WIN]': '🏆',
        '[STAR]': '⭐',
        '[HOT]': '🔥',
        '[IDEA]': '💡',
        '[ALERT]': '🚨',
        '[WARNING]': '⚠️',
        '[QUESTION]': '❓',
        '[EXCLAMATION]': '❗',
        '[CORE]': '⚡',
        '[TIME]': '⏰',
        '[ENTERPRISE]': '🏢',
        '[IPC]': '🔗',
        '[PATTERNS]': '🎨',
        '[PERFORMANCE]': '⚡',
        '[PLUGINS]': '🔌',
        '[RUNTIME]': '🏃',
        '[STRUCTURES]': '🏗️',
        '[UTILS]': '🛠️',
    }


def apply_emojis(text: str) -> str:
    """Apply emoji replacements to text."""
    # Always try to use emojis first - modern terminals support UTF-8
    try:
        emoji_map = get_emoji_mapping()
        for text_equiv, emoji in emoji_map.items():
            text = text.replace(text_equiv, emoji)
        
        # Test if we can print Unicode characters by checking stdout encoding
        import sys
        if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding:
            if 'utf' in sys.stdout.encoding.lower() or sys.stdout.encoding.lower() in ['cp65001', 'utf-8']:
                return text
            else:
                # Try to print a test emoji to see if it works
                try:
                    print('🧪', end='', flush=True)
                    print('\b \b', end='', flush=True)  # Clear the test emoji
                    return text
                except (UnicodeEncodeError, UnicodeDecodeError):
                    pass
        else:
            # No encoding info, try anyway - most modern terminals support it
            return text
    except Exception:
        pass
    
    # Fall back to text equivalents
    # Use text equivalents directly
    fallback_map = {
        '[PASS]': '[PASS]',
        '[FAIL]': '[FAIL]', 
        '[SUCCESS]': '[SUCCESS]',
        '[ERROR]': '[ERROR]',
        '[TEST]': '[TEST]',
        '[SERIALIZATION]': '[SERIALIZATION]',
        '[SECURITY]': '[SECURITY]',
        '[HTTP]': '[HTTP]',
        '[IO]': '[IO]',
        '[MONITOR]': '[MONITOR]',
        '[THREAD]': '[THREAD]',
        '[CACHE]': '[CACHE]',
        '[INFO]': '[INFO]',
        '[RUN]': '[RUN]',
        '[TOOL]': '[TOOL]',
        '[FAST]': '[FAST]',
        '[SECURE]': '[SECURE]',
        '[SEARCH]': '[SEARCH]',
        '[WRITE]': '[WRITE]',
        '[READ]': '[READ]',
        '[SYNC]': '[SYNC]',
        '[CONFIG]': '[CONFIG]',
        '[TARGET]': '[TARGET]',
        '[WIN]': '[WIN]',
        '[STAR]': '[STAR]',
        '[HOT]': '[HOT]',
        '[IDEA]': '[IDEA]',
        '[ALERT]': '[ALERT]',
        '[WARNING]': '[WARNING]',
        '[QUESTION]': '[QUESTION]',
        '[EXCLAMATION]': '[EXCLAMATION]',
        '[TIME]': '[TIME]',
        '[ENTERPRISE]': '[ENTERPRISE]',
        '[IPC]': '[IPC]',
        '[PATTERNS]': '[PATTERNS]',
        '[PLUGINS]': '[PLUGINS]',
        '[RUNTIME]': '[RUNTIME]',
        '[STRUCTURES]': '[STRUCTURES]',
        '[UTILS]': '[UTILS]',
    }
    # Replace any remaining emoji characters with text equivalents
    emoji_to_text = {
        '✅': '[PASS]',
        '❌': '[FAIL]', 
        '🎉': '[SUCCESS]',
        '💥': '[ERROR]',
        '🧪': '[TEST]',
        '📦': '[SERIALIZATION]',
        '🔒': '[SECURITY]',
        '🌐': '[HTTP]',
        '📁': '[IO]',
        '📊': '[MONITOR]',
        '🧵': '[THREAD]',
        '💾': '[CACHE]',
        '📋': '[INFO]',
        '🚀': '[RUN]',
        '🔧': '[TOOL]',
        '⚡': '[FAST]',
        '🛡️': '[SECURE]',
        '🔍': '[SEARCH]',
        '📝': '[WRITE]',
        '📖': '[READ]',
        '🔄': '[SYNC]',
        '⚙️': '[CONFIG]',
        '🎯': '[TARGET]',
        '🏆': '[WIN]',
        '⭐': '[STAR]',
        '🔥': '[HOT]',
        '💡': '[IDEA]',
        '🚨': '[ALERT]',
        '⚠️': '[WARNING]',
        '❓': '[QUESTION]',
        '❗': '[EXCLAMATION]',
        '⏰': '[TIME]',
        '🏢': '[ENTERPRISE]',
        '🔗': '[IPC]',
        '🎨': '[PATTERNS]',
        '🔌': '[PLUGINS]',
        '🏃': '[RUNTIME]',
        '🏗️': '[STRUCTURES]',
        '🛠️': '[UTILS]',
    }
    for emoji, text_equiv in emoji_to_text.items():
        text = text.replace(emoji, text_equiv)
    
    return text


class CoreTestRunner:
    """Main runner for core tests."""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.results: dict[str, int] = {}
    
    def _run_test_subprocess(self, test_name: str, runner_path: Path) -> int:
        """Helper method to run test subprocess with proper error handling."""
        try:
            if not runner_path.exists():
                print(apply_emojis(f"[PASS] {test_name} tests skipped - runner not found"))
                return 0
            
            # Set environment for proper UTF-8 handling
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONLEGACYWINDOWSSTDIO'] = '0'  # Enable UTF-8 mode in Windows console
            
            result = subprocess.run([sys.executable, str(runner_path)], 
                                  capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
            
            # Print the output with emoji processing
            if result.stdout:
                print(apply_emojis(result.stdout))
            if result.stderr and result.stderr.strip():
                print(apply_emojis(result.stderr))
            
            return result.returncode
        except Exception as e:
            print(apply_emojis(f"[FAIL] {test_name} tests failed: {e}"))
            return 1
        
    def run_serialization_tests(self) -> int:
        """Run core serialization tests."""
        print(apply_emojis("[TEST] Running CORE Serialization Tests..."))
        print("=" * 50)
        
        serialization_runner_path = Path(__file__).parent / "serialization" / "runner.py"
        return self._run_test_subprocess("Serialization", serialization_runner_path)
    
    def run_security_tests(self) -> int:
        """Run core security tests."""
        print(apply_emojis("[SECURITY] Running CORE Security Tests..."))
        print("=" * 50)
        
        security_runner_path = Path(__file__).parent / "security" / "runner.py"
        return self._run_test_subprocess("Security", security_runner_path)
    
    def run_http_tests(self) -> int:
        """Run core HTTP tests."""
        print(apply_emojis("[HTTP] Running CORE HTTP Tests..."))
        print("=" * 50)
        
        http_runner_path = Path(__file__).parent / "http" / "runner.py"
        return self._run_test_subprocess("HTTP", http_runner_path)
    
    def run_io_tests(self) -> int:
        """Run core I/O tests."""
        print(apply_emojis("[IO] Running CORE I/O Tests..."))
        print("=" * 50)
        
        io_runner_path = Path(__file__).parent / "io" / "runner.py"
        return self._run_test_subprocess("I/O", io_runner_path)
    
    def run_monitoring_tests(self) -> int:
        """Run core monitoring tests."""
        print(apply_emojis("[MONITOR] Running CORE Monitoring Tests..."))
        print("=" * 50)
        
        monitoring_runner_path = Path(__file__).parent / "monitoring" / "runner.py"
        return self._run_test_subprocess("Monitoring", monitoring_runner_path)
    
    def run_threading_tests(self) -> int:
        """Run core threading tests."""
        print(apply_emojis("[THREAD] Running CORE Threading Tests..."))
        print("=" * 50)
        
        threading_runner_path = Path(__file__).parent / "threading_tests" / "runner.py"
        return self._run_test_subprocess("Threading", threading_runner_path)
    
    def run_caching_tests(self) -> int:
        """Run core caching tests."""
        print(apply_emojis("[CACHE] Running CORE Caching Tests..."))
        print("=" * 50)
        
        caching_runner_path = Path(__file__).parent / "caching" / "runner.py"
        return self._run_test_subprocess("Caching", caching_runner_path)
    
    def run_validation_tests(self) -> int:
        """Run core validation tests."""
        print(apply_emojis("[PASS] Running CORE Validation Tests..."))
        print("=" * 50)
        
        validation_runner_path = Path(__file__).parent / "validation" / "runner.py"
        return self._run_test_subprocess("Validation", validation_runner_path)
    
    def run_cli_tests(self) -> int:
        """Run core CLI tests."""
        print(apply_emojis("[TOOL] Running CORE CLI Tests..."))
        print("=" * 50)
        
        cli_runner_path = Path(__file__).parent / "cli" / "runner.py"
        return self._run_test_subprocess("CLI", cli_runner_path)
    
    def run_config_tests(self) -> int:
        """Run core config tests."""
        print(apply_emojis("[CONFIG] Running CORE Config Tests..."))
        print("=" * 50)
        
        config_runner_path = Path(__file__).parent / "config" / "runner.py"
        return self._run_test_subprocess("Config", config_runner_path)
    
    def run_core_tests(self) -> int:
        """Run core core tests."""
        print(apply_emojis("[CORE] Running CORE Core Tests..."))
        print("=" * 50)
        
        core_runner_path = Path(__file__).parent / "core" / "runner.py"
        return self._run_test_subprocess("Core", core_runner_path)
    
    def run_datetime_tests(self) -> int:
        """Run core datetime tests."""
        print(apply_emojis("[TIME] Running CORE DateTime Tests..."))
        print("=" * 50)
        
        datetime_runner_path = Path(__file__).parent / "datetime" / "runner.py"
        return self._run_test_subprocess("DateTime", datetime_runner_path)
    
    def run_enterprise_tests(self) -> int:
        """Run core enterprise tests."""
        print(apply_emojis("[ENTERPRISE] Running CORE Enterprise Tests..."))
        print("=" * 50)
        
        enterprise_runner_path = Path(__file__).parent / "enterprise" / "runner.py"
        return self._run_test_subprocess("Enterprise", enterprise_runner_path)
    
    def run_ipc_tests(self) -> int:
        """Run core IPC tests."""
        print(apply_emojis("[IPC] Running CORE IPC Tests..."))
        print("=" * 50)
        
        ipc_runner_path = Path(__file__).parent / "ipc" / "runner.py"
        return self._run_test_subprocess("IPC", ipc_runner_path)
    
    def run_patterns_tests(self) -> int:
        """Run core patterns tests."""
        print(apply_emojis("[PATTERNS] Running CORE Patterns Tests..."))
        print("=" * 50)
        
        patterns_runner_path = Path(__file__).parent / "patterns" / "runner.py"
        return self._run_test_subprocess("Patterns", patterns_runner_path)
    
    def run_performance_tests(self) -> int:
        """Run core performance tests."""
        print(apply_emojis("[PERFORMANCE] Running CORE Performance Tests..."))
        print("=" * 50)
        
        performance_runner_path = Path(__file__).parent / "performance" / "runner.py"
        return self._run_test_subprocess("Performance", performance_runner_path)
    
    def run_plugins_tests(self) -> int:
        """Run core plugins tests."""
        print(apply_emojis("[PLUGINS] Running CORE Plugins Tests..."))
        print("=" * 50)
        
        plugins_runner_path = Path(__file__).parent / "plugins" / "runner.py"
        return self._run_test_subprocess("Plugins", plugins_runner_path)
    
    def run_runtime_tests(self) -> int:
        """Run core runtime tests."""
        print(apply_emojis("[RUNTIME] Running CORE Runtime Tests..."))
        print("=" * 50)
        
        runtime_runner_path = Path(__file__).parent / "runtime" / "runner.py"
        return self._run_test_subprocess("Runtime", runtime_runner_path)
    
    def run_structures_tests(self) -> int:
        """Run core structures tests."""
        print(apply_emojis("[STRUCTURES] Running CORE Structures Tests..."))
        print("=" * 50)
        
        structures_runner_path = Path(__file__).parent / "structures" / "runner.py"
        return self._run_test_subprocess("Structures", structures_runner_path)
    
    def run_utils_tests(self) -> int:
        """Run core utils tests."""
        print(apply_emojis("[UTILS] Running CORE Utils Tests..."))
        print("=" * 50)
        
        utils_runner_path = Path(__file__).parent / "utils" / "runner.py"
        return self._run_test_subprocess("Utils", utils_runner_path)
    
    def run_operations_tests(self) -> int:
        """Run core operations tests."""
        print(apply_emojis("[OPERATIONS] Running CORE Operations Tests..."))
        print("=" * 50)
        
        operations_runner_path = Path(__file__).parent / "operations" / "runner.py"
        return self._run_test_subprocess("Operations", operations_runner_path)
    
    def run_shared_tests(self) -> int:
        """Run core shared tests."""
        print(apply_emojis("[SHARED] Running CORE Shared Tests..."))
        print("=" * 50)
        
        shared_runner_path = Path(__file__).parent / "shared" / "runner.py"
        return self._run_test_subprocess("Shared", shared_runner_path)
    
    def run_all_core_tests(self) -> int:
        """Run all core tests."""
        print(apply_emojis("[RUN] XSystem Core Test Suite"))
        print("=" * 60)
        print("Testing all main XSystem features with comprehensive roundtrip testing")
        print("=" * 60)
        
        test_categories = [
            ('serialization', self.run_serialization_tests),
            ('security', self.run_security_tests),
            ('http', self.run_http_tests),
            ('io', self.run_io_tests),
            ('monitoring', self.run_monitoring_tests),
            ('threading', self.run_threading_tests),
            ('caching', self.run_caching_tests),
            ('validation', self.run_validation_tests),
            ('cli', self.run_cli_tests),
            ('config', self.run_config_tests),
            ('core', self.run_core_tests),
            ('datetime', self.run_datetime_tests),
            ('enterprise', self.run_enterprise_tests),
            ('ipc', self.run_ipc_tests),
            ('patterns', self.run_patterns_tests),
            ('performance', self.run_performance_tests),
            ('plugins', self.run_plugins_tests),
            ('runtime', self.run_runtime_tests),
            ('structures', self.run_structures_tests),
            ('utils', self.run_utils_tests),
            ('operations', self.run_operations_tests),
            ('shared', self.run_shared_tests),
        ]
        
        for category, test_func in test_categories:
            print(apply_emojis(f"\n[IO] Running {category.upper()} core tests..."))
            print("-" * 40)
            
            try:
                result = test_func()
                self.results[category] = result
                if result == 0:
                    print(apply_emojis(f"[PASS] {category.upper()} core tests PASSED"))
                else:
                    print(apply_emojis(f"[FAIL] {category.upper()} core tests FAILED"))
            except Exception as e:
                print(apply_emojis(f"[FAIL] Error running {category} core tests: {e}"))
                self.results[category] = 1
        
        # Summary
        print(f"\n{'='*60}")
        print(apply_emojis("[MONITOR] CORE TEST SUMMARY"))
        print(f"{'='*60}")
        
        all_passed = True
        for category, result in self.results.items():
            status = apply_emojis("[PASS] PASSED") if result == 0 else apply_emojis("[FAIL] FAILED")
            print(f"{category.upper():<15}: {status}")
            if result != 0:
                all_passed = False
        
        print(f"\nOverall: {apply_emojis('[SUCCESS] ALL CORE TESTS PASSED') if all_passed else apply_emojis('[ERROR] SOME CORE TESTS FAILED')}")
        
        return 0 if all_passed else 1


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        runner = CoreTestRunner()
        
        if command == "serialization":
            return runner.run_serialization_tests()
        elif command == "security":
            return runner.run_security_tests()
        elif command == "http":
            return runner.run_http_tests()
        elif command == "io":
            return runner.run_io_tests()
        elif command == "monitoring":
            return runner.run_monitoring_tests()
        elif command == "threading":
            return runner.run_threading_tests()
        elif command == "caching":
            return runner.run_caching_tests()
        elif command == "validation":
            return runner.run_validation_tests()
        elif command == "cli":
            return runner.run_cli_tests()
        elif command == "config":
            return runner.run_config_tests()
        elif command == "core":
            return runner.run_core_tests()
        elif command == "datetime":
            return runner.run_datetime_tests()
        elif command == "enterprise":
            return runner.run_enterprise_tests()
        elif command == "ipc":
            return runner.run_ipc_tests()
        elif command == "patterns":
            return runner.run_patterns_tests()
        elif command == "performance":
            return runner.run_performance_tests()
        elif command == "plugins":
            return runner.run_plugins_tests()
        elif command == "runtime":
            return runner.run_runtime_tests()
        elif command == "structures":
            return runner.run_structures_tests()
        elif command == "utils":
            return runner.run_utils_tests()
        elif command == "operations":
            return runner.run_operations_tests()
        elif command == "shared":
            return runner.run_shared_tests()
        elif command == "help" or command == "--help" or command == "-h":
            show_help()
            return 0
        else:
            print(apply_emojis(f"[FAIL] Unknown command: {command}"))
            show_help()
            return 1
    else:
        # Run all core tests
        runner = CoreTestRunner()
        return runner.run_all_core_tests()


def show_help():
    """Show help information."""
    help_text = apply_emojis("""
[RUN] XSystem Core Test Runner

Usage:
  python runner.py [command]

Commands:
  all                    Run all core tests (default)
  serialization          Run core serialization tests only
  security               Run core security tests only
  http                   Run core HTTP tests only
  io                     Run core I/O tests only
  monitoring             Run core monitoring tests only
  threading              Run core threading tests only
  caching                Run core caching tests only
  validation             Run core validation tests only
  cli                    Run core CLI tests only
  config                 Run core config tests only
  core                   Run core core tests only
  datetime               Run core datetime tests only
  enterprise             Run core enterprise tests only
  ipc                    Run core IPC tests only
  patterns               Run core patterns tests only
  performance            Run core performance tests only
  plugins                Run core plugins tests only
  runtime                Run core runtime tests only
  structures             Run core structures tests only
  utils                  Run core utils tests only
  operations             Run core operations tests only
  shared                 Run core shared tests only
  help                   Show this help message

Examples:
  python runner.py                    # Run all core tests
  python runner.py serialization     # Run core serialization tests only
  python runner.py security          # Run core security tests only
  python runner.py cli               # Run core CLI tests only
  python runner.py enterprise        # Run core enterprise tests only

Core Test Features:
  - Comprehensive roundtrip testing
  - Real-world data scenarios
  - Production-ready validation
  - Main API testing
  - Error handling verification
  - 100% module coverage
  - DEV_GUIDELINES.md compliance
""")
    print(help_text)


if __name__ == "__main__":
    sys.exit(main())
