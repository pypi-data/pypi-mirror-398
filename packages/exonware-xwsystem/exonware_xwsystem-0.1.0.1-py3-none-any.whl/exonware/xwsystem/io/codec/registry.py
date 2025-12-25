"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 04, 2025

Universal Codec Registry - High-performance registry for all codec types.
"""

from typing import Optional, Union, Any, Callable
from pathlib import Path
from threading import RLock
from functools import lru_cache
import mimetypes

from .contracts import ICodec, ICodecMetadata
from ..errors import CodecNotFoundError, CodecRegistrationError
from ..contracts import CodecCapability


class CompoundExtensionTrie:
    """
    Trie data structure for fast compound extension matching (e.g., .tar.gz).
    
    Optimized for O(k) lookup where k is the number of extension segments.
    """
    
    def __init__(self):
        """Initialize the trie."""
        self.root: dict[str, Any] = {}
    
    def insert(self, extensions: list[str], codec_id: str, priority: int = 0) -> None:
        """
        Insert a compound extension path.
        
        Args:
            extensions: List of extensions in reverse order (e.g., ['.gz', '.tar'])
            codec_id: Codec ID to associate
            priority: Priority for resolution (higher = preferred)
        """
        node = self.root
        for ext in extensions:
            if ext not in node:
                node[ext] = {}
            node = node[ext]
        
        # Store codec info at leaf
        if '_codecs' not in node:
            node['_codecs'] = []
        node['_codecs'].append((codec_id, priority))
        # Sort by priority (highest first)
        node['_codecs'].sort(key=lambda x: x[1], reverse=True)
    
    def search(self, extensions: list[str]) -> list[str]:
        """
        Search for matching codec IDs.
        
        Args:
            extensions: List of extensions in reverse order (e.g., ['.gz', '.tar'])
        
        Returns:
            List of codec IDs sorted by priority
        """
        results = []
        node = self.root
        
        # Try to match as many extensions as possible
        for i, ext in enumerate(extensions):
            if ext not in node:
                break
            node = node[ext]
            
            # Check if there are codecs at this level
            if '_codecs' in node:
                results.extend([codec_id for codec_id, _ in node['_codecs']])
        
        return results


class UniversalCodecRegistry:
    """
    Universal high-performance codec registry with advanced features.
    
    Features:
    - Thread-safe operations with RLock
    - Magic bytes detection for content-based identification
    - Compound extension support (.tar.gz, .json.gz, etc.)
    - Multiple codec support per extension/MIME type
    - Priority-based resolution for conflicts
    - Type-based filtering (serialization, archive, query, etc.)
    - Metadata retrieval
    - Unregister support
    - Instance caching for O(1) lookups
    - LRU caching for detection results
    
    Performance Targets:
    - Codec lookup: < 1ms (O(1) hash map)
    - Detection: < 2ms (cached)
    - Registration: < 5ms per codec
    - Thread-safe with minimal lock contention
    """
    
    def __init__(self):
        """Initialize the universal codec registry."""
        # Core mappings (codec_id is always lowercase)
        self._by_id: dict[str, type[ICodec]] = {}
        self._by_extension: dict[str, list[tuple[str, int]]] = {}  # ext -> [(codec_id, priority)]
        self._by_mime_type: dict[str, list[tuple[str, int]]] = {}  # mime -> [(codec_id, priority)]
        self._by_alias: dict[str, str] = {}  # alias -> codec_id (1:1 mapping)
        self._by_type: dict[str, set[str]] = {}  # codec_type -> set of codec_ids
        
        # Magic bytes support (for content detection)
        self._magic_bytes: dict[bytes, list[tuple[str, int]]] = {}  # magic -> [(codec_id, priority)]
        
        # Compound extension support
        self._compound_trie = CompoundExtensionTrie()
        
        # Instance cache
        self._instances: dict[str, ICodec] = {}
        
        # Metadata cache
        self._metadata: dict[str, dict[str, Any]] = {}
        
        # Priority tracking (codec_id -> priority)
        self._priorities: dict[str, int] = {}
        
        # Thread safety
        self._lock = RLock()
    
    def register(
        self,
        codec_class: type[ICodec],
        codec_instance: Optional[ICodec] = None,
        priority: int = 0,
        magic_bytes: Optional[list[bytes]] = None
    ) -> None:
        """
        Register a codec class or instance with optional priority and magic bytes.
        
        Args:
            codec_class: Codec class to register
            codec_instance: Optional codec instance (if None, creates one)
            priority: Priority for conflict resolution (higher = preferred, default=0)
            magic_bytes: Optional list of magic byte sequences for content detection
        
        Raises:
            CodecRegistrationError: If codec doesn't implement ICodecMetadata
        """
        with self._lock:
            # Create instance if not provided
            if codec_instance is None:
                try:
                    codec_instance = codec_class()
                except Exception as e:
                    raise CodecRegistrationError(
                        f"Failed to instantiate {codec_class.__name__}: {e}"
                    ) from e
            
            # Verify metadata protocol
            if not isinstance(codec_instance, ICodecMetadata):
                raise CodecRegistrationError(
                    f"{codec_class.__name__} must implement ICodecMetadata protocol"
                )
            
            codec_id = codec_instance.codec_id.lower()
            codec_types = [ct.lower() for ct in codec_instance.codec_types]  # List of types
            
            # Register by ID (overwrite if exists)
            self._by_id[codec_id] = codec_class
            self._priorities[codec_id] = priority
            
            # Register by type (support multiple types per codec)
            for codec_type in codec_types:
                if codec_type not in self._by_type:
                    self._by_type[codec_type] = set()
                self._by_type[codec_type].add(codec_id)
            
            # Register by extensions (support multiple codecs per extension)
            for ext in codec_instance.file_extensions:
                normalized_ext = ext.lower()
                if not normalized_ext.startswith('.'):
                    normalized_ext = f'.{normalized_ext}'
                
                if normalized_ext not in self._by_extension:
                    self._by_extension[normalized_ext] = []
                
                # Remove old entry for this codec if exists
                self._by_extension[normalized_ext] = [
                    (cid, p) for cid, p in self._by_extension[normalized_ext] 
                    if cid != codec_id
                ]
                
                # Add new entry and sort by priority
                self._by_extension[normalized_ext].append((codec_id, priority))
                self._by_extension[normalized_ext].sort(key=lambda x: x[1], reverse=True)
                
                # Handle compound extensions (.tar.gz, .json.gz, etc.)
                if '.' in normalized_ext[1:]:  # Has multiple dots
                    parts = normalized_ext.split('.')
                    ext_list = ['.' + p for p in parts[1:]]
                    ext_list.reverse()  # Reverse for trie matching
                    self._compound_trie.insert(ext_list, codec_id, priority)
            
            # Register by MIME types (support multiple codecs per MIME)
            for mime_type in codec_instance.media_types:
                normalized_mime = mime_type.lower()
                
                if normalized_mime not in self._by_mime_type:
                    self._by_mime_type[normalized_mime] = []
                
                # Remove old entry for this codec if exists
                self._by_mime_type[normalized_mime] = [
                    (cid, p) for cid, p in self._by_mime_type[normalized_mime]
                    if cid != codec_id
                ]
                
                # Add new entry and sort by priority
                self._by_mime_type[normalized_mime].append((codec_id, priority))
                self._by_mime_type[normalized_mime].sort(key=lambda x: x[1], reverse=True)
            
            # Register by aliases (1:1 mapping, aliases are unique)
            aliases = getattr(codec_instance, 'aliases', [])
            for alias in aliases:
                self._by_alias[alias.lower()] = codec_id
            
            # Register magic bytes if provided
            if magic_bytes:
                for magic in magic_bytes:
                    if magic not in self._magic_bytes:
                        self._magic_bytes[magic] = []
                    
                    # Remove old entry for this codec if exists
                    self._magic_bytes[magic] = [
                        (cid, p) for cid, p in self._magic_bytes[magic]
                        if cid != codec_id
                    ]
                    
                    # Add new entry and sort by priority
                    self._magic_bytes[magic].append((codec_id, priority))
                    self._magic_bytes[magic].sort(key=lambda x: x[1], reverse=True)
            
            # Cache instance
            self._instances[codec_id] = codec_instance
            
            # Cache metadata
            self._metadata[codec_id] = {
                'codec_id': codec_id,
                'codec_types': codec_types,  # List of types
                'class': codec_class.__name__,
                'module': codec_class.__module__,
                'extensions': codec_instance.file_extensions,
                'media_types': codec_instance.media_types,
                'aliases': aliases,
                'priority': priority,
                'capabilities': codec_instance.capabilities,
            }
            
            # Clear detection cache since registry changed
            self._detect_cache_clear()
    
    def unregister(self, codec_id: str) -> bool:
        """
        Unregister a codec by ID.
        
        Args:
            codec_id: Codec identifier
        
        Returns:
            True if codec was unregistered, False if not found
        """
        with self._lock:
            codec_id_lower = codec_id.lower()
            
            if codec_id_lower not in self._by_id:
                return False
            
            # Get metadata before removing
            metadata = self._metadata.get(codec_id_lower, {})
            codec_types = metadata.get('codec_types', [])  # List of types
            
            # Remove from ID mapping
            del self._by_id[codec_id_lower]
            
            # Remove from type mappings (all types)
            if codec_types:
                for codec_type in codec_types:
                    if codec_type in self._by_type:
                        self._by_type[codec_type].discard(codec_id_lower)
                        if not self._by_type[codec_type]:
                            del self._by_type[codec_type]
            
            # Remove from extension mappings
            for ext_list in self._by_extension.values():
                ext_list[:] = [(cid, p) for cid, p in ext_list if cid != codec_id_lower]
            
            # Remove from MIME mappings
            for mime_list in self._by_mime_type.values():
                mime_list[:] = [(cid, p) for cid, p in mime_list if cid != codec_id_lower]
            
            # Remove from alias mappings
            self._by_alias = {
                alias: cid for alias, cid in self._by_alias.items()
                if cid != codec_id_lower
            }
            
            # Remove from magic bytes
            for magic_list in self._magic_bytes.values():
                magic_list[:] = [(cid, p) for cid, p in magic_list if cid != codec_id_lower]
            
            # Remove from caches
            self._instances.pop(codec_id_lower, None)
            self._metadata.pop(codec_id_lower, None)
            self._priorities.pop(codec_id_lower, None)
            
            # Clear detection cache
            self._detect_cache_clear()
            
            return True
    
    # ========================================================================
    # SINGLE RESULT METHODS (Priority-based resolution)
    # ========================================================================
    
    def get_by_id(self, codec_id: str) -> Optional[ICodec]:
        """
        Get codec by ID (unique lookup).
        
        Args:
            codec_id: Codec identifier
        
        Returns:
            Codec instance or None
        """
        with self._lock:
            codec_id_lower = codec_id.lower()
            
            # Check instance cache first
            if codec_id_lower in self._instances:
                return self._instances[codec_id_lower]
            
            # Get class and instantiate
            codec_class = self._by_id.get(codec_id_lower)
            if not codec_class:
                return None
            
            instance = codec_class()
            self._instances[codec_id_lower] = instance
            return instance
    
    def get_by_extension(self, ext: str) -> Optional[ICodec]:
        """
        Get codec by extension (highest priority match).
        
        Args:
            ext: File extension (with or without dot)
        
        Returns:
            Highest priority codec instance or None
        """
        with self._lock:
            normalized_ext = ext.lower()
            if not normalized_ext.startswith('.'):
                normalized_ext = f'.{normalized_ext}'
            
            codec_list = self._by_extension.get(normalized_ext, [])
            if not codec_list:
                return None
            
            # Return highest priority (first in sorted list)
            codec_id = codec_list[0][0]
            return self.get_by_id(codec_id)
    
    def get_by_mime_type(self, mime: str) -> Optional[ICodec]:
        """
        Get codec by MIME type (highest priority match).
        
        Args:
            mime: MIME type string
        
        Returns:
            Highest priority codec instance or None
        """
        with self._lock:
            codec_list = self._by_mime_type.get(mime.lower(), [])
            if not codec_list:
                return None
            
            # Return highest priority (first in sorted list)
            codec_id = codec_list[0][0]
            return self.get_by_id(codec_id)
    
    def get_by_alias(self, alias: str) -> Optional[ICodec]:
        """
        Get codec by alias (unique lookup).
        
        Args:
            alias: Codec alias
        
        Returns:
            Codec instance or None
        """
        with self._lock:
            codec_id = self._by_alias.get(alias.lower())
            if not codec_id:
                return None
            return self.get_by_id(codec_id)
    
    @lru_cache(maxsize=256)
    def detect(self, path: Union[str, Path], codec_type: Optional[str] = None) -> Optional[ICodec]:
        """
        Auto-detect codec from file path (best match with optional type filter).
        
        Uses multiple detection strategies with caching:
        1. Compound extensions (.tar.gz)
        2. File extension
        3. MIME type from extension
        4. Alias matching from stem
        
        Args:
            path: File path to detect from
            codec_type: Optional codec type filter (e.g., 'serialization', 'archive')
                       Matches if codec has this type in its list
        
        Returns:
            Best matching codec instance or None
        """
        # Note: This is cached, so we need to handle the lock carefully
        with self._lock:
            return self._detect_internal(path, codec_type)
    
    def _detect_internal(self, path: Union[str, Path], codec_type: Optional[str] = None) -> Optional[ICodec]:
        """Internal detection implementation (not cached)."""
        path_obj = Path(path)
        
        def matches_type(codec: ICodec) -> bool:
            """Check if codec matches the type filter."""
            if not codec_type:
                return True
            codec_types_lower = [ct.lower() for ct in codec.codec_types]
            return codec_type.lower() in codec_types_lower
        
        # Try compound extensions first (.tar.gz, .json.gz, etc.)
        suffixes = path_obj.suffixes
        if len(suffixes) >= 2:
            # Try matching from longest to shortest
            for i in range(len(suffixes)):
                compound = ''.join(suffixes[i:]).lower()
                codec = self.get_by_extension(compound)
                if codec and matches_type(codec):
                    return codec
        
        # Try simple extension
        if path_obj.suffix:
            codec = self.get_by_extension(path_obj.suffix)
            if codec and matches_type(codec):
                return codec
        
        # Try MIME type
        mime_type, _ = mimetypes.guess_type(str(path_obj))
        if mime_type:
            codec = self.get_by_mime_type(mime_type)
            if codec and matches_type(codec):
                return codec
        
        # Try stem as alias
        codec = self.get_by_alias(path_obj.stem)
        if codec and matches_type(codec):
            return codec
        
        return None
    
    def detect_by_content(self, content: bytes, codec_type: Optional[str] = None) -> Optional[ICodec]:
        """
        Detect codec from content using magic bytes.
        
        Args:
            content: File content (at least first 16 bytes)
            codec_type: Optional codec type filter (matches if codec has this type)
        
        Returns:
            Best matching codec or None
        """
        with self._lock:
            def matches_type(codec: ICodec) -> bool:
                """Check if codec matches the type filter."""
                if not codec_type:
                    return True
                codec_types_lower = [ct.lower() for ct in codec.codec_types]
                return codec_type.lower() in codec_types_lower
            
            # Try different magic byte lengths (from longest to shortest)
            for length in [16, 8, 4, 2]:
                if len(content) < length:
                    continue
                
                magic = content[:length]
                codec_list = self._magic_bytes.get(magic, [])
                
                if codec_list:
                    # Return highest priority match
                    for codec_id, _ in codec_list:
                        codec = self.get_by_id(codec_id)
                        if codec and matches_type(codec):
                            return codec
            
            return None
    
    # ========================================================================
    # MULTIPLE RESULT METHODS (All matches)
    # ========================================================================
    
    def get_all_by_extension(self, ext: str) -> list[ICodec]:
        """
        Get all codecs matching an extension (sorted by priority).
        
        Args:
            ext: File extension
        
        Returns:
            List of codec instances sorted by priority (highest first)
        """
        with self._lock:
            normalized_ext = ext.lower()
            if not normalized_ext.startswith('.'):
                normalized_ext = f'.{normalized_ext}'
            
            codec_list = self._by_extension.get(normalized_ext, [])
            return [self.get_by_id(codec_id) for codec_id, _ in codec_list if self.get_by_id(codec_id)]
    
    def get_all_by_mime_type(self, mime: str) -> list[ICodec]:
        """
        Get all codecs matching a MIME type (sorted by priority).
        
        Args:
            mime: MIME type string
        
        Returns:
            List of codec instances sorted by priority (highest first)
        """
        with self._lock:
            codec_list = self._by_mime_type.get(mime.lower(), [])
            return [self.get_by_id(codec_id) for codec_id, _ in codec_list if self.get_by_id(codec_id)]
    
    def get_all_by_type(self, codec_type: str) -> list[ICodec]:
        """
        Get all codecs of a specific type.
        
        Args:
            codec_type: Codec type (e.g., 'serialization', 'archive', 'query')
        
        Returns:
            List of codec instances
        """
        with self._lock:
            codec_ids = self._by_type.get(codec_type.lower(), set())
            return [self.get_by_id(codec_id) for codec_id in codec_ids if self.get_by_id(codec_id)]
    
    def filter_by_capability(self, cap: CodecCapability) -> list[ICodec]:
        """
        Get all codecs with a specific capability.
        
        Args:
            cap: Codec capability flag
        
        Returns:
            List of codec instances with the capability
        """
        with self._lock:
            results = []
            for codec_id in self._by_id.keys():
                codec = self.get_by_id(codec_id)
                if codec and (codec.capabilities & cap):
                    results.append(codec)
            return results
    
    def detect_all(self, path: Union[str, Path], codec_type: Optional[str] = None) -> list[ICodec]:
        """
        Detect all possible codecs for a file path.
        
        Args:
            path: File path
            codec_type: Optional codec type filter (matches if codec has this type)
        
        Returns:
            List of possible codec instances
        """
        with self._lock:
            path_obj = Path(path)
            results = []
            seen = set()
            
            def matches_type(codec: ICodec) -> bool:
                """Check if codec matches the type filter."""
                if not codec_type:
                    return True
                codec_types_lower = [ct.lower() for ct in codec.codec_types]
                return codec_type.lower() in codec_types_lower
            
            # Try compound extensions
            suffixes = path_obj.suffixes
            if len(suffixes) >= 2:
                for i in range(len(suffixes)):
                    compound = ''.join(suffixes[i:]).lower()
                    codecs = self.get_all_by_extension(compound)
                    for codec in codecs:
                        if codec.codec_id not in seen:
                            if matches_type(codec):
                                results.append(codec)
                                seen.add(codec.codec_id)
            
            # Try simple extension
            if path_obj.suffix:
                codecs = self.get_all_by_extension(path_obj.suffix)
                for codec in codecs:
                    if codec.codec_id not in seen:
                        if matches_type(codec):
                            results.append(codec)
                            seen.add(codec.codec_id)
            
            return results
    
    # ========================================================================
    # METADATA & MANAGEMENT METHODS
    # ========================================================================
    
    def get_metadata(self, codec_id: str) -> Optional[dict[str, Any]]:
        """
        Get full metadata for a codec.
        
        Args:
            codec_id: Codec identifier
        
        Returns:
            Metadata dictionary or None
        """
        with self._lock:
            return self._metadata.get(codec_id.lower())
    
    def list_types(self) -> list[str]:
        """
        List all registered codec types.
        
        Returns:
            List of codec type strings
        """
        with self._lock:
            return list(self._by_type.keys())
    
    def list_codecs(self, codec_type: Optional[str] = None) -> list[str]:
        """
        List all codec IDs, optionally filtered by type.
        
        Args:
            codec_type: Optional codec type filter
        
        Returns:
            List of codec ID strings
        """
        with self._lock:
            if codec_type:
                return list(self._by_type.get(codec_type.lower(), set()))
            else:
                return list(self._by_id.keys())
    
    def list_extensions(self) -> list[str]:
        """List all registered file extensions."""
        with self._lock:
            return list(self._by_extension.keys())
    
    def list_mime_types(self) -> list[str]:
        """List all registered MIME types."""
        with self._lock:
            return list(self._by_mime_type.keys())
    
    def list_aliases(self) -> list[str]:
        """List all registered aliases."""
        with self._lock:
            return list(self._by_alias.keys())
    
    def clear(self) -> None:
        """Clear all registrations."""
        with self._lock:
            self._by_id.clear()
            self._by_extension.clear()
            self._by_mime_type.clear()
            self._by_alias.clear()
            self._by_type.clear()
            self._magic_bytes.clear()
            self._instances.clear()
            self._metadata.clear()
            self._priorities.clear()
            self._compound_trie = CompoundExtensionTrie()
            self._detect_cache_clear()
    
    def _detect_cache_clear(self) -> None:
        """Clear the detection cache."""
        # Clear the LRU cache for detect method
        self.detect.cache_clear()
    
    # ========================================================================
    # BULK OPERATIONS
    # ========================================================================
    
    def register_bulk(self, codec_classes: list[type[ICodec]], priorities: Optional[list[int]] = None) -> int:
        """
        Register multiple codecs efficiently.
        
        Args:
            codec_classes: List of codec classes
            priorities: Optional list of priorities (same length as codec_classes)
        
        Returns:
            Number of successfully registered codecs
        """
        if priorities is None:
            priorities = [0] * len(codec_classes)
        
        count = 0
        for codec_class, priority in zip(codec_classes, priorities):
            try:
                self.register(codec_class, priority=priority)
                count += 1
            except CodecRegistrationError:
                pass  # Skip failed registrations
        
        return count
    
    # ========================================================================
    # STATISTICS & INTROSPECTION
    # ========================================================================
    
    def get_statistics(self) -> dict[str, int]:
        """
        Get registry statistics.
        
        Returns:
            Dictionary with counts of registered items
        """
        with self._lock:
            return {
                'codecs': len(self._by_id),
                'extensions': len(self._by_extension),
                'mime_types': len(self._by_mime_type),
                'aliases': len(self._by_alias),
                'types': len(self._by_type),
                'magic_bytes': len(self._magic_bytes),
                'cached_instances': len(self._instances),
            }


# ============================================================================
# GLOBAL REGISTRY SINGLETON
# ============================================================================

_global_registry: Optional[UniversalCodecRegistry] = None
_global_lock = RLock()


def get_registry() -> UniversalCodecRegistry:
    """
    Get the global universal codec registry (thread-safe singleton).
    
    Returns:
        Global UniversalCodecRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        with _global_lock:
            if _global_registry is None:  # Double-check locking
                _global_registry = UniversalCodecRegistry()
    return _global_registry


def reset_registry() -> None:
    """Reset the global registry (mainly for testing)."""
    global _global_registry
    with _global_lock:
        _global_registry = None
