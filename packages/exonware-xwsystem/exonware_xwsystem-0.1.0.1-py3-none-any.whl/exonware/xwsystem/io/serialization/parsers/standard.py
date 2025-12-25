"""Standard library JSON parser (baseline implementation)."""

import json
from typing import Any, Union

from .base import IJsonParser


class StandardJsonParser(IJsonParser):
    """Standard library JSON parser - Tier 0 (baseline)."""
    
    @property
    def parser_name(self) -> str:
        return "standard"
    
    @property
    def tier(self) -> int:
        return 0
    
    @property
    def is_available(self) -> bool:
        return True  # Always available (stdlib)
    
    def loads(self, s: Union[str, bytes]) -> Any:
        """Parse JSON using stdlib json.loads()."""
        if isinstance(s, bytes):
            s = s.decode("utf-8")
        return json.loads(s)
    
    def dumps(self, obj: Any, **kwargs) -> Union[str, bytes]:
        """Serialize JSON using stdlib json.dumps()."""
        ensure_ascii = kwargs.get("ensure_ascii", False)
        indent = kwargs.get("indent", None)
        sort_keys = kwargs.get("sort_keys", False)
        
        return json.dumps(
            obj,
            ensure_ascii=ensure_ascii,
            indent=indent,
            sort_keys=sort_keys,
            default=kwargs.get("default", None),
            cls=kwargs.get("cls", None),
        )
