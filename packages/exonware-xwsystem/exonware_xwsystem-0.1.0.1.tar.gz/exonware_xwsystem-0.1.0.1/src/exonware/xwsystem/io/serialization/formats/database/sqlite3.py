"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

SQLite3 serialization - Embedded database storage.

Following I→A pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- Concrete: Sqlite3Serializer
"""

import json
import sqlite3
from typing import Any, Optional, Union
from pathlib import Path

from ...base import ASerialization
from ....contracts import EncodeOptions, DecodeOptions
from ....defs import CodecCapability
from ....errors import SerializationError


class Sqlite3Serializer(ASerialization):
    """SQLite3 serializer - follows the I→A pattern."""
    
    @property
    def codec_id(self) -> str:
        return "sqlite3"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/x-sqlite3", "application/vnd.sqlite3"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".db", ".sqlite", ".sqlite3"]
    
    @property
    def format_name(self) -> str:
        return "SQLite3"
    
    @property
    def mime_type(self) -> str:
        return "application/x-sqlite3"
    
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
        return ["sqlite3", "sqlite", "db"]
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """SQLite3 encode requires file path - use save_file() instead."""
        raise NotImplementedError("SQLite3 requires file-based operations - use save_file()")
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """SQLite3 decode requires file path - use load_file() instead."""
        raise NotImplementedError("SQLite3 requires file-based operations - use load_file()")

    # ---------------------------------------------------------------------
    # FILE-BASED OPERATIONS (override ASerialization defaults)
    # ---------------------------------------------------------------------

    def save_file(self, data: Any, file_path: Union[str, Path], **options: Any) -> None:
        """
        Save Python data into a SQLite3 database file.

        Root cause: The generic ``ASerialization.save_file`` implementation
        expects an in-memory ``encode`` operation, but SQLite3 is inherently
        file-backed and our ``encode``/``decode`` are intentionally
        unimplemented. Calling the base implementation raised a
        ``NotImplementedError`` wrapped in ``SerializationError``.

        Solution: Override ``save_file`` / ``load_file`` to perform
        file-based operations directly using ``sqlite3`` while still
        presenting a simple dict-like API to callers and tests.
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # For now we implement a minimal schema:
        # - Single table ``data``
        # - Single row with id=1 storing JSON representation of ``data``
        try:
            conn = sqlite3.connect(path)
            try:
                cur = conn.cursor()
                cur.execute(
                    "CREATE TABLE IF NOT EXISTS data ("
                    "id INTEGER PRIMARY KEY, "
                    "json TEXT NOT NULL"
                    ")"
                )
                json_str = json.dumps(data)
                # Ensure id=1 holds the latest payload
                cur.execute("DELETE FROM data WHERE id = 1")
                cur.execute("INSERT INTO data (id, json) VALUES (1, ?)", (json_str,))
                conn.commit()
            finally:
                conn.close()
        except sqlite3.Error as e:
            raise SerializationError(
                f"Failed to save SQLite3 file '{path}': {e}",
                format_name=self.format_name,
                original_error=e,
            ) from e

    def load_file(self, file_path: Union[str, Path], **options: Any) -> Any:
        """
        Load Python data from a SQLite3 database file.

        Reads row with ``id = 1`` from the ``data`` table and returns the
        JSON-decoded payload. This mirrors the simple dict-based contract
        used by the tests and higher-level APIs.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"SQLite3 file not found: {path}")

        try:
            conn = sqlite3.connect(path)
            try:
                cur = conn.cursor()
                cur.execute(
                    "SELECT json FROM data WHERE id = 1"
                )
                row = cur.fetchone()
                if row is None or row[0] is None:
                    # No payload stored yet – mirror behaviour of other
                    # serializers by returning None.
                    return None

                return json.loads(row[0])
            finally:
                conn.close()
        except sqlite3.Error as e:
            raise SerializationError(
                f"Failed to load SQLite3 file '{path}': {e}",
                format_name=self.format_name,
                original_error=e,
            ) from e

