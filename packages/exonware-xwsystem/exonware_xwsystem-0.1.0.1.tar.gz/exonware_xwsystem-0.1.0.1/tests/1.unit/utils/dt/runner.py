#exonware/xwsystem/tests/1.unit/utils/dt/runner.py
"""
DateTime Unit Test Runner

Runs datetime unit tests for XSystem datetime utilities.
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
        '[TIME]': '⏰',
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
            '⏰': '[TIME]',
        }
        for emoji, text_equiv in fallback_map.items():
            text = text.replace(emoji, text_equiv)
        return text

def main():
    """Run datetime unit tests."""
    if sys.platform == "win32":
        try:
            import io

            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
        except Exception:
            pass

    print(apply_emojis("[TEST] Running UNIT DateTime Tests..."))
    print("=" * 50)
    
    try:
        import importlib.util
        test_basic_path = Path(__file__).with_name("test_core_xwsystem_utls_dt.py")
        spec = importlib.util.spec_from_file_location("test_core_xwsystem_utls_dt", test_basic_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to load spec from {test_basic_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.main()
    except Exception as e:
        print(apply_emojis(f"[FAIL] Failed to run datetime unit tests: {e}"))
        return 1


if __name__ == "__main__":
    sys.exit(main())
