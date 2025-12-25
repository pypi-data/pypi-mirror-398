"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

Shelve serialization - Persistent dictionary storage.

Following I→A pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- Concrete: ShelveSerializer
"""

import shelve
from typing import Any, Optional, Union
from pathlib import Path

from ...base import ASerialization
from ....contracts import EncodeOptions, DecodeOptions
from ....defs import CodecCapability
from ....errors import SerializationError


class ShelveSerializer(ASerialization):
    """Shelve serializer - follows the I→A pattern."""
    
    @property
    def codec_id(self) -> str:
        return "shelve"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/x-shelve"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".shelve", ".db"]
    
    @property
    def format_name(self) -> str:
        return "Shelve"
    
    @property
    def mime_type(self) -> str:
        return "application/x-shelve"
    
    @property
    def is_binary_format(self) -> bool:
        return True
    
    @property
    def supports_streaming(self) -> bool:
        return False
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def aliases(self) -> list[str]:
        return ["shelve", "Shelve"]
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """Shelve encode requires file path - use save_file() instead."""
        raise NotImplementedError("Shelve requires file-based operations - use save_file()")
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """Shelve decode requires file path - use load_file() instead."""
        raise NotImplementedError("Shelve requires file-based operations - use load_file()")

    # ---------------------------------------------------------------------
    # FILE-BASED OPERATIONS
    # ---------------------------------------------------------------------

    def save_file(self, data: Any, file_path: Union[str, Path], **options: Any) -> None:
        """
        Save Python data into a shelve database file.

        Uses a single key ``'root'`` to store the provided object, which is
        sufficient for the dict-style usage expected by the tests and APIs.
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with shelve.open(str(path)) as db:
                db["root"] = data
        except Exception as e:
            raise SerializationError(
                f"Failed to save Shelve file '{path}': {e}",
                format_name=self.format_name,
                original_error=e,
            ) from e

    def load_file(self, file_path: Union[str, Path], **options: Any) -> Any:
        """
        Load Python data from a shelve database file.

        Returns the object stored under the ``'root'`` key (or ``None`` if
        not present), mirroring the behaviour of other serializers that
        operate on a single top-level payload.
        """
        path = Path(file_path)

        try:
            with shelve.open(str(path)) as db:
                return db.get("root")
        except FileNotFoundError:
            # Mirror other serializers' behaviour when file is missing
            raise
        except Exception as e:
            raise SerializationError(
                f"Failed to load Shelve file '{path}': {e}",
                format_name=self.format_name,
                original_error=e,
            ) from e

