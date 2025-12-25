"""pysimdjson parser - Tier 1 (C++ simdjson, excellent for partial parsing)."""

from typing import Any, Union

try:
    import simdjson
    PYSIMDJSON_AVAILABLE = True
except ImportError:
    PYSIMDJSON_AVAILABLE = False
    simdjson = None

from .base import IJsonParser


class PysimdjsonParser(IJsonParser):
    """pysimdjson parser - Tier 1 (C++ simdjson, excellent for partial parsing)."""
    
    @property
    def parser_name(self) -> str:
        return "pysimdjson"
    
    @property
    def tier(self) -> int:
        return 1
    
    @property
    def is_available(self) -> bool:
        return PYSIMDJSON_AVAILABLE
    
    def loads(self, s: Union[str, bytes]) -> Any:
        """Parse JSON using simdjson.loads()."""
        if isinstance(s, str):
            s = s.encode("utf-8")
        return simdjson.loads(s)
    
    def dumps(self, obj: Any, **kwargs) -> Union[str, bytes]:
        """Serialize JSON using pysimdjson.dumps()."""
        # pysimdjson doesn't have dumps, fallback to orjson or stdlib
        # For now, use orjson if available, else stdlib
        try:
            import orjson
            result = orjson.dumps(obj)
            if isinstance(result, bytes) and kwargs.get("return_str", False):
                return result.decode("utf-8")
            return result
        except ImportError:
            import json
            result = json.dumps(obj, **kwargs)
            if isinstance(result, str) and kwargs.get("return_bytes", False):
                return result.encode("utf-8")
            return result
