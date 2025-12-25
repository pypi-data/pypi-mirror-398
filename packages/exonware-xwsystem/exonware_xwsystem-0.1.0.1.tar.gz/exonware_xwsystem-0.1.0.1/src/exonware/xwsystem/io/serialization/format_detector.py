#exonware\xwsystem\serialization\format_detector.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Intelligent format detection for automatic serialization format selection.
"""

import re
from pathlib import Path
from typing import Any, Optional, Union

from ...config.logging_setup import get_logger

logger = get_logger("xwsystem.serialization.format_detector")


class FormatDetector:
    """
    Intelligent format detector that can identify serialization formats
    from file extensions, content analysis, and magic bytes.
    """
    
    __slots__ = ('_extension_map', '_magic_bytes', '_content_patterns', '_confidence_threshold')
    
    def __init__(self, confidence_threshold: float = 0.3):
        """
        Initialize format detector.
        
        Args:
            confidence_threshold: Minimum confidence level for format detection.
                Default is 0.3 so that simple, high-signal heuristics like
                extension-only detection (e.g. ``test.json``) are accepted
                without requiring magic-bytes or content analysis.
        """
        self._confidence_threshold = confidence_threshold
        self._extension_map = self._build_extension_map()
        self._magic_bytes = self._build_magic_bytes_map()
        self._content_patterns = self._build_content_patterns()
    
    def _build_extension_map(self) -> dict[str, list[str]]:
        """Build mapping from file extensions to format names."""
        return {
            # Text formats
            '.json': ['JSON'],
            '.yaml': ['YAML'], '.yml': ['YAML'],
            '.toml': ['TOML'],
            '.xml': ['XML'],
            '.csv': ['CSV'],
            '.ini': ['ConfigParser'], '.cfg': ['ConfigParser'],
            
            # Binary formats
            '.bson': ['BSON'],
            '.msgpack': ['MessagePack'], '.mp': ['MessagePack'],
            '.cbor': ['CBOR'],
            '.pkl': ['Pickle'], '.pickle': ['Pickle'], '.p': ['Pickle'],
            '.marshal': ['Marshal'],
            '.db': ['SQLite3'], '.sqlite': ['SQLite3'], '.sqlite3': ['SQLite3'],
            '.dbm': ['DBM'],
            '.shelf': ['Shelve'],
            '.plist': ['Plistlib'],
            
            # Schema-based formats
            '.avro': ['Avro'],
            '.proto': ['Protobuf'], '.pb': ['Protobuf'],
            '.thrift': ['Thrift'],
            '.parquet': ['Parquet'],
            '.orc': ['ORC'],
            '.capnp': ['CapnProto'],
            '.fbs': ['FlatBuffers'],
        }
    
    def _build_magic_bytes_map(self) -> dict[bytes, list[str]]:
        """Build mapping from magic bytes to format names."""
        return {
            # Binary formats with clear magic bytes
            b'BSON': ['BSON'],
            b'\x93NUMPYARRAY': ['MessagePack'],  # Some MessagePack implementations
            b'SQLite format 3\x00': ['SQLite3'],
            b'bplist': ['Plistlib'],  # Binary plist
            
            # Schema-based formats
            b'Obj\x01': ['Avro'],  # Avro object container
            b'PAR1': ['Parquet'],  # Parquet magic
            b'ORC': ['ORC'],  # ORC magic
            b'\xc0\x01\x00\x00': ['CapnProto'],  # Cap'n Proto magic
            b'FLATB': ['FlatBuffers'],  # FlatBuffers magic
        }
    
    def _build_content_patterns(self) -> dict[str, list[tuple[re.Pattern, float]]]:
        """Build regex patterns for content-based detection with confidence scores."""
        return {
            'JSON': [
                (re.compile(r'^\s*[\{\[].*[\}\]]\s*$', re.DOTALL), 0.9),
                (re.compile(r'^\s*"[^"]*"\s*:\s*', re.MULTILINE), 0.8),
                (re.compile(r'["\{\}\[\],:]', re.MULTILINE), 0.6),
            ],
            'YAML': [
                (re.compile(r'^---\s*$', re.MULTILINE), 0.9),
                (re.compile(r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*:\s*', re.MULTILINE), 0.8),
                (re.compile(r'^\s*-\s+', re.MULTILINE), 0.7),
                (re.compile(r'^\s*#.*$', re.MULTILINE), 0.5),
            ],
            'TOML': [
                (re.compile(r'^\s*\[[^\]]+\]\s*$', re.MULTILINE), 0.9),
                (re.compile(r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*', re.MULTILINE), 0.8),
                (re.compile(r'^\s*#.*$', re.MULTILINE), 0.4),
            ],
            'XML': [
                (re.compile(r'^\s*<\?xml\s+version\s*=', re.IGNORECASE), 1.0),
                (re.compile(r'<[^>]+>.*</[^>]+>', re.DOTALL), 0.9),
                (re.compile(r'<[^/>]+/>', re.MULTILINE), 0.8),
                (re.compile(r'<[^>]+>', re.MULTILINE), 0.6),
            ],
            'CSV': [
                (re.compile(r'^[^,\n]*,[^,\n]*,', re.MULTILINE), 0.8),
                (re.compile(r'^"[^"]*","[^"]*"', re.MULTILINE), 0.9),
                (re.compile(r'\r?\n', re.MULTILINE), 0.3),
            ],
            'ConfigParser': [
                (re.compile(r'^\s*\[[^\]]+\]\s*$', re.MULTILINE), 0.8),
                (re.compile(r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*[:=]\s*', re.MULTILINE), 0.7),
                (re.compile(r'^\s*[;#].*$', re.MULTILINE), 0.5),
            ],
        }
    
    def detect_from_extension(self, file_path: Union[str, Path]) -> list[str]:
        """
        Detect format from file extension.
        
        Args:
            file_path: Path to analyze
            
        Returns:
            List of possible format names
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        return self._extension_map.get(extension, [])
    
    def detect_from_magic_bytes(self, data: bytes, max_bytes: int = 64) -> list[str]:
        """
        Detect format from magic bytes at the beginning of data.
        
        Args:
            data: Binary data to analyze
            max_bytes: Maximum number of bytes to check
            
        Returns:
            List of possible format names
        """
        if not data:
            return []
        
        header = data[:max_bytes]
        
        for magic_bytes, formats in self._magic_bytes.items():
            if header.startswith(magic_bytes):
                return formats.copy()
        
        return []
    
    def detect_from_content(self, content: Union[str, bytes]) -> dict[str, float]:
        """
        Detect format from content analysis with confidence scores.
        
        Args:
            content: Content to analyze (string or bytes)
            
        Returns:
            Dictionary mapping format names to confidence scores
        """
        if isinstance(content, bytes):
            try:
                text_content = content.decode('utf-8', errors='ignore')
            except UnicodeDecodeError:
                # Binary content, check magic bytes
                magic_formats = self.detect_from_magic_bytes(content)
                return {fmt: 0.8 for fmt in magic_formats}
        else:
            text_content = content
        
        # Limit content size for performance
        if len(text_content) > 10000:
            text_content = text_content[:10000]
        
        results = {}
        
        for format_name, patterns in self._content_patterns.items():
            confidence = 0.0
            matches = 0
            
            for pattern, weight in patterns:
                if pattern.search(text_content):
                    confidence += weight
                    matches += 1
            
            # Normalize confidence based on number of patterns
            if matches > 0:
                confidence = min(confidence / len(patterns), 1.0)
                results[format_name] = confidence
        
        return results
    
    def detect_format(
        self, 
        file_path: Optional[Union[str, Path]] = None,
        content: Optional[Union[str, bytes]] = None,
        data: Optional[bytes] = None
    ) -> dict[str, float]:
        """
        Comprehensive format detection using all available methods.
        
        Args:
            file_path: Optional file path for extension-based detection
            content: Optional content for pattern-based detection
            data: Optional binary data for magic byte detection
            
        Returns:
            Dictionary mapping format names to confidence scores
        """
        results = {}
        
        # Extension-based detection (high confidence)
        if file_path:
            extension_formats = self.detect_from_extension(file_path)
            for fmt in extension_formats:
                results[fmt] = results.get(fmt, 0) + 0.8
        
        # Magic bytes detection (highest confidence)
        if data:
            magic_formats = self.detect_from_magic_bytes(data)
            for fmt in magic_formats:
                results[fmt] = results.get(fmt, 0) + 0.9
        
        # Content-based detection
        if content is not None:
            content_results = self.detect_from_content(content)
            for fmt, confidence in content_results.items():
                results[fmt] = results.get(fmt, 0) + confidence * 0.7
        
        # Normalize scores
        max_possible = 2.4  # 0.8 + 0.9 + 0.7
        for fmt in results:
            results[fmt] = min(results[fmt] / max_possible, 1.0)
        
        return results
    
    def get_best_format(
        self, 
        file_path: Optional[Union[str, Path]] = None,
        content: Optional[Union[str, bytes]] = None,
        data: Optional[bytes] = None
    ) -> Optional[str]:
        """
        Get the most likely format with highest confidence.
        
        Args:
            file_path: Optional file path for extension-based detection
            content: Optional content for pattern-based detection  
            data: Optional binary data for magic byte detection
            
        Returns:
            Format name with highest confidence, or None if below threshold
        """
        results = self.detect_format(file_path, content, data)
        
        if not results:
            return None
        
        best_format = max(results.items(), key=lambda x: x[1])
        
        if best_format[1] >= self._confidence_threshold:
            logger.debug(f"Detected format: {best_format[0]} (confidence: {best_format[1]:.2f})")
            return best_format[0]
        
        logger.debug(f"No format detected above threshold {self._confidence_threshold}")
        return None
    
    def get_format_suggestions(
        self, 
        file_path: Optional[Union[str, Path]] = None,
        content: Optional[Union[str, bytes]] = None,
        data: Optional[bytes] = None,
        max_suggestions: int = 3
    ) -> list[tuple[str, float]]:
        """
        Get ranked format suggestions with confidence scores.
        
        Args:
            file_path: Optional file path for extension-based detection
            content: Optional content for pattern-based detection
            data: Optional binary data for magic byte detection
            max_suggestions: Maximum number of suggestions to return
            
        Returns:
            List of (format_name, confidence) tuples sorted by confidence
        """
        results = self.detect_format(file_path, content, data)
        
        # Sort by confidence descending
        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_results[:max_suggestions]
    
    def is_binary_format(self, format_name: str) -> bool:
        """
        Check if a format is binary or text-based.
        
        Args:
            format_name: Format name to check
            
        Returns:
            True if binary format, False if text format
        """
        binary_formats = {
            'BSON', 'MessagePack', 'CBOR', 'Pickle', 'Marshal', 
            'SQLite3', 'DBM', 'Shelve', 'Plistlib',
            'Avro', 'Protobuf', 'Parquet', 'ORC', 'CapnProto', 'FlatBuffers'
        }
        
        return format_name in binary_formats
    
    def get_serializer_class_name(self, format_name: str) -> str:
        """
        Get the serializer class name for a detected format.
        
        Args:
            format_name: Detected format name
            
        Returns:
            Serializer class name
        """
        return f"{format_name}Serializer"


# Global format detector instance
_global_detector = FormatDetector()

def detect_format(
    file_path: Optional[Union[str, Path]] = None,
    content: Optional[Union[str, bytes]] = None,
    data: Optional[bytes] = None
) -> Optional[str]:
    """
    Convenience function for format detection using global detector.
    
    Args:
        file_path: Optional file path for extension-based detection
        content: Optional content for pattern-based detection
        data: Optional binary data for magic byte detection
        
    Returns:
        Most likely format name or None
    """
    return _global_detector.get_best_format(file_path, content, data)

def get_format_suggestions(
    file_path: Optional[Union[str, Path]] = None,
    content: Optional[Union[str, bytes]] = None,
    data: Optional[bytes] = None,
    max_suggestions: int = 3
) -> list[tuple[str, float]]:
    """
    Convenience function for format suggestions using global detector.
    
    Args:
        file_path: Optional file path for extension-based detection
        content: Optional content for pattern-based detection
        data: Optional binary data for magic byte detection
        max_suggestions: Maximum number of suggestions
        
    Returns:
        List of (format_name, confidence) tuples
    """
    return _global_detector.get_format_suggestions(file_path, content, data, max_suggestions)

def is_binary_format(format_name: str) -> bool:
    """
    Convenience function to check if format is binary.
    
    Args:
        format_name: Format name to check
        
    Returns:
        True if binary format
    """
    return _global_detector.is_binary_format(format_name)
