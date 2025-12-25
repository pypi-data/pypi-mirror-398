"""python-rapidjson parser - Tier 1 (C++ rapidjson)."""

from typing import Any, Union

try:
    import rapidjson
    RAPIDJSON_AVAILABLE = True
except ImportError:
    RAPIDJSON_AVAILABLE = False
    rapidjson = None

from .base import IJsonParser


class RapidjsonParser(IJsonParser):
    """python-rapidjson parser - Tier 1 (C++ rapidjson)."""
    
    @property
    def parser_name(self) -> str:
        return "rapidjson"
    
    @property
    def tier(self) -> int:
        return 1
    
    @property
    def is_available(self) -> bool:
        return RAPIDJSON_AVAILABLE
    
    def loads(self, s: Union[str, bytes]) -> Any:
        """Parse JSON using rapidjson.loads()."""
        if isinstance(s, bytes):
            s = s.decode("utf-8")
        return rapidjson.loads(s)
    
    def dumps(self, obj: Any, **kwargs) -> Union[str, bytes]:
        """Serialize JSON using rapidjson.dumps()."""
        # rapidjson supports most stdlib kwargs
        result = rapidjson.dumps(
            obj,
            ensure_ascii=kwargs.get("ensure_ascii", True),
            indent=kwargs.get("indent", None),
            sort_keys=kwargs.get("sort_keys", False),
        )
        
        # rapidjson returns str, encode if bytes needed
        if isinstance(result, str) and kwargs.get("return_bytes", False):
            return result.encode("utf-8")
        
        return result
