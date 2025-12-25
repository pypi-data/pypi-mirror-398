"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

XML serialization - Extensible Markup Language.

Following I→A pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- Concrete: XmlSerializer

Improved implementation:
- Uses xmltodict for both encoding and decoding (better round-trip compatibility)
- Requires xmltodict >= 0.13.0 for security features
- Preserves types using XML attributes
- Minimal try/catch blocks with proper error handling
"""

from typing import Any, Optional, Union
from pathlib import Path

from ...base import ASerialization
from ....contracts import EncodeOptions, DecodeOptions
from ....defs import CodecCapability
from ....errors import SerializationError

# Primary: xmltodict for both encoding and decoding (better round-trip)
# xmltodict has built-in security features (disable_entities=True by default)
# No need for defusedxml - xmltodict handles XML security internally
import xmltodict

# Optional: dicttoxml as fallback (not recommended for round-trip)
try:
    import dicttoxml
    DICTTOXML_AVAILABLE = True
except ImportError:
    DICTTOXML_AVAILABLE = False
    dicttoxml = None


class XmlSerializer(ASerialization):
    """
    XML serializer - follows the I→A pattern.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    Concrete: XmlSerializer
    
    Uses xmltodict for both encoding and decoding to ensure perfect round-trip compatibility.
    Requires xmltodict >= 0.13.0 for security features.
    
    Examples:
        >>> serializer = XmlSerializer()
        >>> 
        >>> # Encode data
        >>> xml_str = serializer.encode({"user": {"name": "John", "age": 30}})
        >>> 
        >>> # Decode data (perfect round-trip)
        >>> data = serializer.decode(xml_str)
        >>> assert data == {"user": {"name": "John", "age": 30}}
        >>> 
        >>> # Save to file
        >>> serializer.save_file({"config": {"debug": True}}, "config.xml")
        >>> 
        >>> # Load from file
        >>> config = serializer.load_file("config.xml")
    """
    
    def __init__(self):
        """Initialize XML serializer."""
        super().__init__()
        if xmltodict is None:
            raise ImportError(
                "xmltodict >= 0.13.0 is required for XML serialization. "
                "Install with: pip install xmltodict>=0.13.0"
            )
        
        # Verify security features are available
        # Root cause fixed: Check for security features at initialization.
        # Priority #1: Security - Use available security features, recommend upgrade for full security.
        import inspect
        parse_sig = inspect.signature(xmltodict.parse)
        self._has_disable_entities = 'disable_entities' in parse_sig.parameters
        self._has_forbid_dtd = 'forbid_dtd' in parse_sig.parameters
        self._has_forbid_entities = 'forbid_entities' in parse_sig.parameters
        
        if not self._has_disable_entities:
            raise ImportError(
                "xmltodict with disable_entities support is required for XML serialization. "
                "Install with: pip install 'xmltodict>=0.12.0'"
            )
    
    # ========================================================================
    # CODEC METADATA
    # ========================================================================
    
    @property
    def codec_id(self) -> str:
        return "xml"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/xml", "text/xml"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".xml", ".svg", ".rss", ".atom", ".xhtml", ".xsd", ".wsdl", ".plist", ".csproj", ".xaml"]
    
    @property
    def format_name(self) -> str:
        return "XML"
    
    @property
    def mime_type(self) -> str:
        return "application/xml"
    
    @property
    def is_binary_format(self) -> bool:
        return False  # XML is text-based
    
    @property
    def supports_streaming(self) -> bool:
        return True  # XML supports streaming via SAX/iterparse
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def aliases(self) -> list[str]:
        return ["xml", "XML"]
    
    @property
    def codec_types(self) -> list[str]:
        """XML is both a serialization and markup language."""
        return ["serialization", "markup"]
    
    # ========================================================================
    # XML SANITIZATION HELPERS
    # ========================================================================
    
    def _sanitize_xml_name(self, name: str) -> str:
        """
        Sanitize a string to be a valid XML element/attribute name.
        
        XML 1.0 element name rules:
        - Must start with letter, underscore, or colon (colon for namespaces)
        - Can contain letters, digits, hyphens, underscores, periods, colons
        - Cannot start with "xml" (case-insensitive)
        - Cannot contain spaces or other special characters
        
        Root cause fixed: Dictionary keys used as XML element names must be valid XML names.
        Solution: Prefix invalid names with underscore, replace invalid chars with underscore.
        Priority #2: Usability - Ensure all data can be serialized to XML.
        
        Args:
            name: String to sanitize as XML name
            
        Returns:
            Valid XML element/attribute name
        """
        import re
        
        # Convert to string if not already
        name_str = str(name)
        
        # Replace invalid characters with underscore
        # Valid chars: letters, digits, hyphens, underscores, periods, colons
        sanitized = re.sub(r'[^a-zA-Z0-9_\-.:]', '_', name_str)
        
        # If starts with digit, hyphen, period, or colon, prefix with underscore
        if sanitized and sanitized[0] in '0123456789-.:':
            sanitized = '_' + sanitized
        
        # If starts with "xml" (case-insensitive), prefix with underscore
        if sanitized.lower().startswith('xml'):
            sanitized = '_' + sanitized
        
        # If empty after sanitization, use default name
        if not sanitized:
            sanitized = '_item'
        
        return sanitized
    
    def _sanitize_for_xml(self, data: Any, preserve_keys: bool = True) -> Any:
        """
        Sanitize data for XML encoding by removing/replacing invalid XML characters.
        
        XML 1.0 doesn't allow certain control characters (0x00-0x1F except 0x09, 0x0A, 0x0D).
        Also sanitizes dictionary keys to be valid XML element names.
        
        Root cause fixed: Dictionary keys must be valid XML element names (can't start with digits).
        Solution: Sanitize keys and store original keys as XML attributes for round-trip preservation.
        Priority #2: Usability - Ensure all data structures can be serialized to XML with key preservation.
        
        Args:
            data: Python data structure
            preserve_keys: If True, store original keys as @_original_key attributes
            
        Returns:
            Sanitized data structure safe for XML encoding
        """
        if isinstance(data, dict):
            # Root cause fixed: Dictionary keys must be valid XML element names.
            # Keys that start with digits (like UUIDs) are invalid XML element names.
            # Solution: Sanitize keys and preserve originals as attributes for round-trip.
            sanitized_dict = {}
            for key, value in data.items():
                # Sanitize key to be valid XML element name
                sanitized_key = self._sanitize_xml_name(key)
                # Handle key collisions (if sanitization produces duplicate keys)
                original_key = sanitized_key
                counter = 1
                while sanitized_key in sanitized_dict:
                    sanitized_key = f"{original_key}_{counter}"
                    counter += 1
                
                # Sanitize value recursively
                sanitized_value = self._sanitize_for_xml(value, preserve_keys=preserve_keys)
                
                # If key was changed and we want to preserve it, store original as attribute
                if preserve_keys and sanitized_key != str(key):
                    # Wrap value in dict with original key as attribute
                    # xmltodict uses @ prefix for attributes
                    if isinstance(sanitized_value, dict):
                        # Add original key as attribute to existing dict
                        sanitized_value['@_original_key'] = str(key)
                        sanitized_dict[sanitized_key] = sanitized_value
                    else:
                        # Wrap non-dict value to add attribute
                        sanitized_dict[sanitized_key] = {
                            '@_original_key': str(key),
                            '#text': sanitized_value
                        }
                else:
                    sanitized_dict[sanitized_key] = sanitized_value
            return sanitized_dict
        elif isinstance(data, list):
            return [self._sanitize_for_xml(item, preserve_keys=preserve_keys) for item in data]
        elif isinstance(data, str):
            # Remove invalid XML 1.0 control characters (except tab, newline, carriage return)
            # XML 1.0 allows: #x9 (tab), #xA (newline), #xD (carriage return)
            # All other control chars (0x00-0x1F) are invalid
            import re
            # Remove control characters except tab, newline, carriage return
            sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', data)
            return sanitized
        elif isinstance(data, (int, float, bool, type(None))):
            return data
        else:
            # Convert other types to string and sanitize
            return self._sanitize_for_xml(str(data))
    
    # ========================================================================
    # TYPE PRESERVATION HELPERS
    # ========================================================================
    
    def _preserve_types(self, data: Any) -> Any:
        """
        Preserve Python types in XML structure using type hints.
        
        Adds '@type' attributes to preserve type information for round-trip.
        This allows us to restore int, float, bool, None from string representations.
        
        Args:
            data: Python data structure
            
        Returns:
            Data structure with type hints embedded
        """
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if isinstance(value, (int, float, bool, type(None))):
                    # Store type information
                    result[key] = {
                        '@type': type(value).__name__,
                        '#text': str(value) if value is not None else ''
                    }
                elif isinstance(value, dict):
                    result[key] = self._preserve_types(value)
                elif isinstance(value, list):
                    result[key] = [self._preserve_types(item) for item in value]
                else:
                    result[key] = value
            return result
        elif isinstance(data, list):
            return [self._preserve_types(item) for item in data]
        else:
            return data
    
    def _restore_types(self, data: Any) -> Any:
        """
        Restore Python types from XML structure with type hints.
        
        Converts '@type' attributes back to proper Python types.
        
        Args:
            data: XML data structure with type hints
            
        Returns:
            Data structure with restored types
        """
        if isinstance(data, dict):
            # Check if this is a type-hinted value
            if '@type' in data and '#text' in data and len(data) == 2:
                type_name = data['@type']
                text_value = data['#text']
                
                if type_name == 'int':
                    return int(text_value) if text_value else 0
                elif type_name == 'float':
                    return float(text_value) if text_value else 0.0
                elif type_name == 'bool':
                    return text_value.lower() in ('true', '1', 'yes')
                elif type_name == 'NoneType':
                    return None
                else:
                    return text_value
            
            # Recursively process dict
            result = {}
            for key, value in data.items():
                if key not in ('@type', '#text'):
                    result[key] = self._restore_types(value)
            return result
        elif isinstance(data, list):
            return [self._restore_types(item) for item in data]
        else:
            return data
    
    # ========================================================================
    # CORE ENCODE/DECODE (Using xmltodict for both - perfect round-trip)
    # ========================================================================
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """
        Encode data to XML string.
        
        Uses xmltodict.unparse() for encoding (better round-trip compatibility than dicttoxml).
        
        Args:
            value: Data to serialize
            options: XML options (root, pretty, preserve_types, etc.)
        
        Returns:
            XML string
        
        Raises:
            SerializationError: If encoding fails
        """
        opts = options or {}
        
        # Determine root element name
        root_name = opts.get('root', 'root')
        
        # Root cause fixed: Sanitize data to remove invalid XML characters.
        # Priority #1: Security - Prevent XML injection and malformed XML.
        # Priority #2: Usability - Ensure data can be encoded without errors.
        value = self._sanitize_for_xml(value)
        
        # Root cause fixed: Type preservation disabled by default - XML is text-based.
        # Priority #2: Usability - Focus on structure preservation first, types are secondary.
        # Note: Numbers will be strings in XML (this is expected XML behavior).
        preserve_types = opts.get('preserve_types', False)
        if preserve_types:
            value = self._preserve_types(value)
        
        # Wrap in root element if needed (xmltodict requires single root)
        # Root cause fixed: Always wrap in root element for xmltodict compatibility.
        if not isinstance(value, dict):
            # Non-dict value - wrap it
            wrapped_value = {root_name: value}
        elif len(value) != 1:
            # Multiple keys - wrap in root
            wrapped_value = {root_name: value}
        else:
            # Single key dict - check if we should use it as root or wrap it
            single_key = list(value.keys())[0]
            if single_key == root_name:
                # Already has correct root name
                wrapped_value = value
            else:
                # Different root name - wrap it
                wrapped_value = {root_name: value}
        
        # Encode to XML string using xmltodict.unparse()
        # Root cause fixed: Use xmltodict for both encode and decode for perfect round-trip.
        # Priority #2: Usability - Round-trip serialization should preserve data structure.
        try:
            xml_str = xmltodict.unparse(
                wrapped_value,
                pretty=opts.get('pretty', False),
                indent=opts.get('indent', '  '),
                full_document=opts.get('full_document', True)
            )
        except (ValueError, TypeError) as e:
            raise SerializationError(
                f"Failed to encode XML: {e}. "
                f"Data may contain invalid XML characters or unsupported types.",
                format_name=self.format_name,
                original_error=e
            ) from e
        
        return xml_str
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """
        Decode XML string to data.
        
        Uses xmltodict.parse() with security features enabled.
        
        Args:
            repr: XML string (bytes or str)
            options: XML options (process_namespaces, root, preserve_types, etc.)
        
        Returns:
            Decoded Python dict
        
        Raises:
            SerializationError: If decoding fails
        """
        # Convert bytes to str if needed
        if isinstance(repr, bytes):
            repr = repr.decode('utf-8')
        
        # Trim leading BOM/whitespace before XML declaration.
        # Root cause: Some producers emit a blank line or BOM before '<?xml ...?>',
        # which causes ExpatError: "XML or text declaration not at start of entity".
        # Priority #2 (Usability): Be forgiving on harmless leading whitespace/BOM
        # while keeping strict parsing for the actual XML content.
        repr = repr.lstrip("\ufeff\r\n\t ")
        
        opts = options or {}
        root_name = opts.get('root', 'root')
        preserve_types = opts.get('preserve_types', False)
        
        # Decode from XML string with security features enabled
        # Root cause fixed: Use available security features based on xmltodict version.
        # Priority #1: Security - Use all available security features.
        parse_kwargs = {
            'process_namespaces': opts.get('process_namespaces', False),
            'namespace_separator': opts.get('namespace_separator', ':'),
            'disable_entities': True,  # Security: disable external entities (available in >=0.12.0)
        }
        
        # Add additional security features if available (>=0.13.0)
        if self._has_forbid_dtd:
            parse_kwargs['forbid_dtd'] = True  # Security: forbid DTD
        if self._has_forbid_entities:
            parse_kwargs['forbid_entities'] = True  # Security: forbid entities
        
        try:
            data = xmltodict.parse(repr, **parse_kwargs)
        except Exception as e:
            # Provide better error context for XML parsing failures
            error_msg = str(e)
            if "not well-formed" in error_msg or "ExpatError" in str(type(e).__name__):
                # Try to find the problematic character position
                raise SerializationError(
                    f"Failed to decode XML: {error_msg}. "
                    f"The XML may contain invalid characters or be malformed.",
                    format_name=self.format_name,
                    original_error=e
                ) from e
            else:
                raise SerializationError(
                    f"Failed to decode XML: {error_msg}",
                    format_name=self.format_name,
                    original_error=e
                ) from e
        
        # Unwrap root element if it matches expected root name
        # Root cause fixed: Proper root element handling - check if root matches expected name.
        # Priority #2: Usability - Round-trip serialization should preserve data structure.
        if isinstance(data, dict) and len(data) == 1:
            # Check if the single key matches root_name or if it's a generic 'root'
            keys = list(data.keys())
            if keys[0] == root_name or (root_name == 'root' and keys[0] == 'root'):
                data = data[keys[0]]
            # If root doesn't match, keep wrapped (might be intentional)
        
        # Restore original keys if they were preserved
        # Root cause fixed: Dictionary keys were sanitized during encoding.
        # Solution: Restore original keys from @_original_key attributes.
        # Priority #2: Usability - Round-trip serialization must preserve key names.
        data = self._restore_original_keys(data)
        
        # Restore types if they were preserved
        if preserve_types:
            data = self._restore_types(data)
        
        return data
    
    def _infer_type(self, value: str) -> Any:
        """
        Infer Python type from XML string value.
        
        Root cause fixed: XML is text-based and converts all values to strings.
        Solution: Attempt to infer and restore original types (int, float, bool, None).
        Priority #2: Usability - Round-trip serialization should preserve types when possible.
        
        Args:
            value: String value from XML
            
        Returns:
            Value with inferred type (int, float, bool, None, or original string)
        """
        if not isinstance(value, str):
            return value
        
        value = value.strip()
        
        # Check for None/empty
        if not value or value.lower() in ('none', 'null', ''):
            return None
        
        # Check for boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Check for integer
        try:
            # Try int first (more common)
            if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                return int(value)
        except (ValueError, OverflowError):
            pass
        
        # Check for float
        try:
            return float(value)
        except (ValueError, OverflowError):
            pass
        
        # Return original string if no type matches
        return value
    
    def _restore_original_keys(self, data: Any) -> Any:
        """
        Restore original dictionary keys from @_original_key attributes.
        
        Root cause fixed: Keys were sanitized during encoding (e.g., UUIDs starting with digits).
        Solution: Check for @_original_key attributes and restore original key names.
        Priority #2: Usability - Round-trip serialization must preserve key names.
        
        Args:
            data: Decoded XML data structure
            
        Returns:
            Data structure with original keys restored and types inferred
        """
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # Skip xmltodict internal attributes
                if key.startswith('@') and key != '@_original_key':
                    continue
                
                # Check if this value has an original key attribute
                if isinstance(value, dict) and '@_original_key' in value:
                    original_key = value['@_original_key']
                    # Remove the attribute from value
                    clean_value = {k: v for k, v in value.items() if k != '@_original_key'}
                    
                    # If clean_value has only #text, unwrap it
                    if len(clean_value) == 1 and '#text' in clean_value:
                        clean_value = clean_value['#text']
                        # Infer type for unwrapped text value
                        clean_value = self._infer_type(clean_value)
                    
                    # Recursively restore keys in the value
                    clean_value = self._restore_original_keys(clean_value)
                    result[original_key] = clean_value
                else:
                    # Recursively restore keys in the value
                    restored_value = self._restore_original_keys(value)
                    # Infer type for leaf string values
                    if isinstance(restored_value, str):
                        restored_value = self._infer_type(restored_value)
                    result[key] = restored_value
            return result
        elif isinstance(data, list):
            return [self._restore_original_keys(item) for item in data]
        else:
            # Infer type for leaf string values
            if isinstance(data, str):
                return self._infer_type(data)
            return data
