"""Base JSON parser interface."""

from abc import ABC, abstractmethod
from typing import Any, Union


class IJsonParser(ABC):
    """Abstract JSON parser interface for pluggable implementations."""
    
    @abstractmethod
    def loads(self, s: Union[str, bytes]) -> Any:
        """
        Parse JSON string/bytes to Python object.
        
        Args:
            s: JSON string or bytes
            
        Returns:
            Parsed Python object
        """
        pass
    
    @abstractmethod
    def dumps(self, obj: Any, **kwargs) -> Union[str, bytes]:
        """
        Serialize Python object to JSON.
        
        Args:
            obj: Python object to serialize
            **kwargs: Serialization options (ensure_ascii, indent, etc.)
            
        Returns:
            JSON string or bytes
        """
        pass
    
    @property
    @abstractmethod
    def parser_name(self) -> str:
        """Parser identifier (e.g., 'standard', 'orjson')."""
        pass
    
    @property
    @abstractmethod
    def tier(self) -> int:
        """
        Performance tier:
        0 = stdlib (baseline)
        1 = orjson (3-4x faster)
        2 = Rust extension (5-7x faster, future)
        3 = Pure Rust core (6-8x faster, future)
        """
        pass
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if parser is available (dependencies installed)."""
        pass
