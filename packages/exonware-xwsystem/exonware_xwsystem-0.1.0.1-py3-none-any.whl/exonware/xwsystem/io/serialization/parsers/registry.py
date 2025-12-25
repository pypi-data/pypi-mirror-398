"""Parser registry for JSON parser selection and auto-detection."""

from typing import Optional, Dict, Type

from .base import IJsonParser
from .standard import StandardJsonParser

# Import hybrid parser (direct, no try/catch - assumes msgspec and orjson available)
from .hybrid_parser import HybridParser

# Registry of available parsers
_PARSERS: Dict[str, Type[IJsonParser]] = {
    "hybrid": HybridParser,  # Default: msgspec for reading, orjson for writing
    "standard": StandardJsonParser,  # Fallback only
}

# Cache of parser instances
_PARSER_INSTANCES: Dict[str, IJsonParser] = {}


def get_best_available_parser() -> IJsonParser:
    """
    Auto-detect and return the best available parser.
    
    Default: hybrid (msgspec for reading, orjson for writing)
    - Fastest combination: msgspec reads 1.36x faster, orjson writes 2.27x faster
    - Direct imports (no try/catch) - assumes both are available
    
    Fallback: standard (stdlib json)
    
    Returns:
        Best available parser instance
    """
    # Try hybrid first (default)
    parser_class = _PARSERS.get("hybrid")
    if parser_class:
        parser = parser_class()
        if parser.is_available:
            return parser
    
    # Fallback to standard (always available)
    return StandardJsonParser()


def get_parser(name: Optional[str] = None) -> IJsonParser:
    """
    Get parser by name or auto-detect best available.
    
    Args:
        name: Parser name ("standard", "orjson", or None for auto-detect)
    
    Returns:
        Parser instance (falls back to best available if requested parser unavailable)
    """
    if name is None:
        return get_best_available_parser()
    
    # Check cache first
    if name in _PARSER_INSTANCES:
        parser = _PARSER_INSTANCES[name]
        if parser.is_available:
            return parser
    
    # Create new instance
    parser_class = _PARSERS.get(name, StandardJsonParser)
    parser = parser_class()
    
    # Cache if available
    if parser.is_available:
        _PARSER_INSTANCES[name] = parser
    else:
        # Fallback to best available if requested parser unavailable
        if name != "standard":
            return get_best_available_parser()
    
    return parser


def register_parser(name: str, parser_class: Type[IJsonParser]):
    """
    Register a new parser implementation.
    
    Args:
        name: Parser identifier
        parser_class: Parser class implementing IJsonParser
    """
    _PARSERS[name] = parser_class
    # Clear cache to allow new parser to be used
    if name in _PARSER_INSTANCES:
        del _PARSER_INSTANCES[name]
