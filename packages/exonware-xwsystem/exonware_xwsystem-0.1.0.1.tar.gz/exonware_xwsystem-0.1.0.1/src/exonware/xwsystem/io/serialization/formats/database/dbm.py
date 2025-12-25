"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

DBM serialization - Unix database manager.

Following I→A pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- Concrete: DbmSerializer
"""

import json
import dbm
from typing import Any, Optional, Union
from pathlib import Path

from ...base import ASerialization
from ....contracts import EncodeOptions, DecodeOptions
from ....defs import CodecCapability
from ....errors import SerializationError


class DbmSerializer(ASerialization):
    """DBM serializer - follows the I→A pattern."""
    
    @property
    def codec_id(self) -> str:
        return "dbm"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/x-dbm"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".dbm", ".db"]
    
    @property
    def format_name(self) -> str:
        return "DBM"
    
    @property
    def mime_type(self) -> str:
        return "application/x-dbm"
    
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
        return ["dbm", "DBM"]
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """DBM encode requires file path - use save_file() instead."""
        raise NotImplementedError("DBM requires file-based operations - use save_file()")
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """DBM decode requires file path - use load_file() instead."""
        raise NotImplementedError("DBM requires file-based operations - use load_file()")

    # ---------------------------------------------------------------------
    # FILE-BASED OPERATIONS
    # ---------------------------------------------------------------------

    def save_file(self, data: Any, file_path: Union[str, Path], **options: Any) -> None:
        """
        Save Python data into a DBM database file.

        Root cause: Generic ``save_file`` tried to call ``encode`` which is
        intentionally unimplemented for DBM. Fix by performing file-based
        operations directly and storing a single JSON payload under a fixed
        key.
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with dbm.open(str(path), "c") as db:
                payload = json.dumps(data).encode("utf-8")
                db[b"root"] = payload
        except Exception as e:
            raise SerializationError(
                f"Failed to save DBM file '{path}': {e}",
                format_name=self.format_name,
                original_error=e,
            ) from e

    def load_file(self, file_path: Union[str, Path], **options: Any) -> Any:
        """
        Load Python data from a DBM database file.

        Returns the JSON-decoded payload stored under the ``root`` key.
        """
        path = Path(file_path)

        try:
            with dbm.open(str(path), "r") as db:
                raw = db.get(b"root")
                if raw is None:
                    return None
                return json.loads(raw.decode("utf-8"))
        except FileNotFoundError:
            # Mirror other serializers' behaviour when file is missing
            raise
        except Exception as e:
            raise SerializationError(
                f"Failed to load DBM file '{path}': {e}",
                format_name=self.format_name,
                original_error=e,
            ) from e

