#exonware/xwsystem/tests/core/enterprise/runner.py
"""
Enterprise Features Core Test Runner

Runs comprehensive tests for enterprise features distributed across:
- security/ (Authentication: OAuth2, JWT, SAML)
- monitoring/ (Distributed Tracing: OpenTelemetry, Jaeger)
- io/serialization/ (Schema Registry: Confluent, AWS Glue)

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.387
Generation Date: November 04, 2025
"""

import sys
from pathlib import Path

def get_emoji_mapping():
    """Get mapping of text equivalents to emojis."""
    return {
        '[PASS]': '✅',
        '[FAIL]': '❌',
        '[SUCCESS]': '🎉',
        '[ERROR]': '💥',
        '[TEST]': '🧪',
        '[ENTERPRISE]': '🏢',
    }

def apply_emojis(text: str) -> str:
    """Apply emoji replacements to text."""
    emoji_map = get_emoji_mapping()
    for text_equiv, emoji in emoji_map.items():
        text = text.replace(text_equiv, emoji)
    
    # Handle encoding issues on Windows
    try:
        # Test if the text can be encoded
        text.encode('cp1252')
        return text
    except UnicodeEncodeError:
        # Fall back to text equivalents if encoding fails
        fallback_map = {
            '✅': '[PASS]',
            '❌': '[FAIL]', 
            '🎉': '[SUCCESS]',
            '💥': '[ERROR]',
            '🧪': '[TEST]',
            '🏢': '[ENTERPRISE]',
        }
        for emoji, text_equiv in fallback_map.items():
            text = text.replace(emoji, text_equiv)
        return text

def main():
    """Run enterprise features core tests."""
    print(apply_emojis("[TEST] Running CORE Enterprise Features Tests..."))
    print("=" * 50)
    
    try:
        # Add parent directory to path for module import
        test_dir = Path(__file__).parent
        
        # Direct execution of test file
        test_file = test_dir / "test_core_xwsystem_enterprise.py"
        
        # Execute the test module
        import runpy
        result = runpy.run_path(str(test_file), run_name="__main__")
        
        # The test file exits with sys.exit(), so if we get here, it passed
        return 0
        
    except SystemExit as e:
        # Capture exit code from test module
        return e.code if e.code is not None else 0
    except Exception as e:
        print(apply_emojis(f"[FAIL] Failed to run enterprise feature tests: {e}"))
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
