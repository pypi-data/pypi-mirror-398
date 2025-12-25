"""orjson parser - DIRECT (no try/catch, assumes orjson is available)."""

from typing import Any, Union
import orjson  # Direct import, no try/catch

from .base import IJsonParser


class OrjsonDirectParser(IJsonParser):
    """orjson parser - DIRECT (no try/catch, assumes orjson is available)."""
    
    @property
    def parser_name(self) -> str:
        return "orjson_direct"
    
    @property
    def tier(self) -> int:
        return 1
    
    @property
    def is_available(self) -> bool:
        return True  # Assumes orjson is available
    
    def loads(self, s: Union[str, bytes]) -> Any:
        """Parse JSON using orjson.loads()."""
        if isinstance(s, str):
            s = s.encode("utf-8")
        return orjson.loads(s)
    
    def dumps(self, obj: Any, **kwargs) -> Union[str, bytes]:
        """Serialize JSON using orjson.dumps()."""
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
