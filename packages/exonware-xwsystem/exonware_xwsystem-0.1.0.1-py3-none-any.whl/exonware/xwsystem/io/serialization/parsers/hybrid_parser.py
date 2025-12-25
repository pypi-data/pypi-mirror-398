"""Hybrid parser: msgspec for reading, orjson for writing (direct, no try/catch)."""

from typing import Any, Union
import msgspec  # Direct import for reading
import orjson  # Direct import for writing

from .base import IJsonParser


class HybridParser(IJsonParser):
    """
    Hybrid parser - fastest combination:
    - msgspec for reading (1.36x faster than orjson)
    - orjson for writing (2.27x faster than msgspec)
    
    Direct imports (no try/catch) - assumes both are available.
    """
    
    @property
    def parser_name(self) -> str:
        return "hybrid"
    
    @property
    def tier(self) -> int:
        return 1
    
    @property
    def is_available(self) -> bool:
        return True  # Assumes both msgspec and orjson are available
    
    def loads(self, s: Union[str, bytes]) -> Any:
        """Parse JSON using msgspec.json.decode() - fastest for reading."""
        if isinstance(s, str):
            s = s.encode("utf-8")
        # msgspec.json.decode accepts bytes directly
        return msgspec.json.decode(s)
    
    def dumps(self, obj: Any, **kwargs) -> Union[str, bytes]:
        """Serialize JSON using orjson.dumps() - fastest for writing."""
        option = 0
        
        # orjson options
        if not kwargs.get("ensure_ascii", True):
            # orjson always outputs UTF-8, so ensure_ascii=False is default
            pass
        
        # Handle indent (orjson doesn't support indent directly)
        indent = kwargs.get("indent", None)
        if indent:
            # For pretty printing, use orjson.OPT_INDENT_2
            option |= orjson.OPT_INDENT_2
        
        # Sort keys
        if kwargs.get("sort_keys", False):
            option |= orjson.OPT_SORT_KEYS
        
        result = orjson.dumps(obj, option=option)
        
        # Return as bytes (orjson returns bytes)
        # Caller can decode if string is needed
        return result
