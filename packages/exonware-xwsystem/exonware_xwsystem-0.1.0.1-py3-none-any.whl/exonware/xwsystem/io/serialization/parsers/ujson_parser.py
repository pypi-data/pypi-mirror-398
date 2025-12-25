"""ujson parser - Tier 1 (C-based, fast)."""

from typing import Any, Union

try:
    import ujson
    UJSON_AVAILABLE = True
except ImportError:
    UJSON_AVAILABLE = False
    ujson = None

from .base import IJsonParser


class UjsonParser(IJsonParser):
    """ujson parser - Tier 1 (C-based, fast)."""
    
    @property
    def parser_name(self) -> str:
        return "ujson"
    
    @property
    def tier(self) -> int:
        return 1
    
    @property
    def is_available(self) -> bool:
        return UJSON_AVAILABLE
    
    def loads(self, s: Union[str, bytes]) -> Any:
        """Parse JSON using ujson.loads()."""
        if isinstance(s, bytes):
            s = s.decode("utf-8")
        return ujson.loads(s)
    
    def dumps(self, obj: Any, **kwargs) -> Union[str, bytes]:
        """Serialize JSON using ujson.dumps()."""
        # ujson supports most stdlib kwargs
        result = ujson.dumps(
            obj,
            ensure_ascii=kwargs.get("ensure_ascii", True),
            indent=kwargs.get("indent", None),
            sort_keys=kwargs.get("sort_keys", False),
        )
        
        # ujson returns str, encode if bytes needed
        if isinstance(result, str) and kwargs.get("return_bytes", False):
            return result.encode("utf-8")
        
        return result
