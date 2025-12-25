"""msgspec parser - Tier 1 (Rust-based, very fast)."""

from typing import Any, Union

try:
    import msgspec
    MSGSPEC_AVAILABLE = True
except ImportError:
    MSGSPEC_AVAILABLE = False
    msgspec = None

from .base import IJsonParser


class MsgspecParser(IJsonParser):
    """msgspec parser - Tier 1 (Rust-based, very fast, close to orjson)."""
    
    @property
    def parser_name(self) -> str:
        return "msgspec"
    
    @property
    def tier(self) -> int:
        return 1
    
    @property
    def is_available(self) -> bool:
        return MSGSPEC_AVAILABLE
    
    def loads(self, s: Union[str, bytes]) -> Any:
        """Parse JSON using msgspec.json.decode()."""
        if isinstance(s, str):
            s = s.encode("utf-8")
        # msgspec.json.decode accepts bytes directly
        return msgspec.json.decode(s)
    
    def dumps(self, obj: Any, **kwargs) -> Union[str, bytes]:
        """Serialize JSON using msgspec.json.encode()."""
        result = msgspec.json.encode(obj)
        
        # msgspec returns bytes, decode if string needed
        if isinstance(result, bytes) and kwargs.get("return_str", False):
            return result.decode("utf-8")
        
        return result
