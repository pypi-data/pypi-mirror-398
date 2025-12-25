#exonware/xwsystem/tests/core/cli/runner.py
"""
CLI Core Test Runner

Runs comprehensive CLI core tests for XSystem CLI functionality.
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
        '[TOOL]': '🔧',
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
            '🔧': '[TOOL]',
        }
        for emoji, text_equiv in fallback_map.items():
            text = text.replace(emoji, text_equiv)
        return text

def main():
    """Run CLI core tests."""
    print(apply_emojis("[TEST] Running CORE CLI Tests..."))
    print("=" * 50)
    
    try:
        import sys
        from pathlib import Path
        test_basic_path = Path(__file__).parent / "test_core_xwsystem_cli.py"
        sys.path.insert(0, str(test_basic_path.parent))

        import test_core_xwsystem_cli
        return test_core_xwsystem_cli.main()
    except Exception as e:
        print(apply_emojis(f"[FAIL] Failed to run CLI core tests: {e}"))
        return 1


if __name__ == "__main__":
    sys.exit(main())
