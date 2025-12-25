#exonware/xwsystem/tests/1.unit/serialization_tests/runner.py
"""
Test runner for serialization worst-case scenarios and security/performance tests.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 07-Sep-2025
"""

import sys
import os
import pytest
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))


def run_serialization_tests():
    """Run all serialization tests including worst-case scenarios and security/performance tests."""
    
    # Get the test directory
    test_dir = Path(__file__).parent
    
    # Test files to run
    test_files = [
        'test_serialization_basic_features.py',
        'test_serialization_worst_case_scenarios.py',
        'test_serialization_security_performance.py',
    ]
    
    # Build test paths
    test_paths = [str(test_dir / test_file) for test_file in test_files]
    
    # Run tests with verbose output
    pytest_args = [
        '-v',  # Verbose output
        '--tb=short',  # Short traceback format
        '--strict-markers',  # Strict marker handling
        '--disable-warnings',  # Disable warnings for cleaner output
        '--color=yes',  # Colored output
    ] + test_paths
    
    print("🧪 Running Comprehensive Serialization Tests")
    print("=" * 60)
    print("📋 Test Categories:")
    print("  • Basic feature tests")
    print("  • Worst-case scenario tests")
    print("  • Security vulnerability tests")
    print("  • Performance stress tests")
    print("  • Production readiness tests")
    print("=" * 60)
    
    # Run the tests
    exit_code = pytest.main(pytest_args)
    
    if exit_code == 0:
        print("\n🎉 All serialization tests passed!")
        print("✅ Production-grade quality confirmed")
        print("✅ Security vulnerabilities protected against")
        print("✅ Performance benchmarks met")
        print("✅ Worst-case scenarios handled gracefully")
    else:
        print(f"\n❌ Some tests failed (exit code: {exit_code})")
        print("🔍 Review test output above for details")
    
    return exit_code


if __name__ == "__main__":
    exit_code = run_serialization_tests()
    sys.exit(exit_code)
