#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/serialization/formats/text/jsonlines.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 02-Nov-2025

JSON Lines (JSONL/NDJSON) Serialization - Newline-Delimited JSON

JSON Lines format (also called NDJSON - Newline Delimited JSON):
- One JSON object per line
- Perfect for streaming data
- Log file friendly
- Easy to append

Priority 1 (Security): Safe JSON parsing per line
Priority 2 (Usability): Streaming-friendly format
Priority 3 (Maintainability): Simple line-based processing
Priority 4 (Performance): Memory-efficient streaming
Priority 5 (Extensibility): Compatible with standard JSON
"""

from typing import Any, Optional, Union
from pathlib import Path
import json

from .json import JsonSerializer
from ...parsers.registry import get_parser
from ...parsers.base import IJsonParser
from ....errors import SerializationError
from ....common.atomic import AtomicFileWriter
from exonware.xwsystem.config.logging_setup import get_logger
from exonware.xwsystem.config.performance import get_performance_config

logger = get_logger(__name__)


class JsonLinesSerializer(JsonSerializer):
    """
    JSON Lines (JSONL/NDJSON) serializer for streaming data.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    Concrete: JsonLinesSerializer
    """
    
    def __init__(self, parser_name: Optional[str] = None):
        """
        Initialize JSON Lines serializer with optional parser selection.
        
        Args:
            parser_name: Parser name ("standard", "orjson", or None for auto-detect)
        """
        super().__init__(parser_name=parser_name)
        # Get parser instance for direct use in line-by-line operations
        self._parser: IJsonParser = get_parser(parser_name)
    
    @property
    def codec_id(self) -> str:
        """Codec identifier."""
        return "jsonl"
    
    @property
    def media_types(self) -> list[str]:
        """Supported MIME types."""
        return ["application/x-ndjson", "application/jsonl"]
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported file extensions."""
        return [".jsonl", ".ndjson", ".jsonlines"]
    
    @property
    def aliases(self) -> list[str]:
        """Alternative names."""
        return ["jsonl", "JSONL", "ndjson", "NDJSON", "jsonlines"]
    
    @property
    def codec_types(self) -> list[str]:
        """JSON Lines is a data exchange format."""
        return ["data", "serialization"]

    # -------------------------------------------------------------------------
    # RECORD / STREAMING CAPABILITIES
    # -------------------------------------------------------------------------

    @property
    def supports_record_streaming(self) -> bool:
        """
        JSONL is explicitly designed for record-level streaming.

        This enables stream_read_record / stream_update_record to operate in a
        true streaming fashion (line-by-line) without loading the entire file.
        """
        return True

    @property
    def supports_record_paging(self) -> bool:
        """
        JSONL supports efficient record-level paging.

        Paging is implemented as a lightweight line counter that only parses
        the requested slice of records.
        """
        return True

    # -------------------------------------------------------------------------
    # CORE ENCODE / DECODE
    # -------------------------------------------------------------------------

    def encode(self, data: Any, *, options: Optional[dict[str, Any]] = None) -> str:
        """
        Encode data to JSON Lines string.
        
        Args:
            data: List of objects to encode (each becomes one line)
            options: Encoding options
            
        Returns:
            JSON Lines string (one JSON object per line)
        """
        if not isinstance(data, list):
            # Single object - wrap in list
            data = [data]

        opts = options or {}
        ensure_ascii = opts.get("ensure_ascii", False)

        lines: list[str] = []
        for item in data:
            # Use pluggable parser
            result = self._parser.dumps(item, ensure_ascii=ensure_ascii)
            # Convert bytes to str if needed
            if isinstance(result, bytes):
                result = result.decode("utf-8")
            lines.append(result)

        return "\n".join(lines)

    def decode(self, data: Union[str, bytes], *, options: Optional[dict[str, Any]] = None) -> list[Any]:
        """
        Decode JSON Lines string to list of Python objects.
        
        Args:
            data: JSON Lines string or bytes
            options: Decoding options
            
        Returns:
            List of decoded Python objects
        """
        if isinstance(data, bytes):
            data = data.decode("utf-8")

        # Split by newlines and parse each line
        lines = data.strip().split("\n")
        results: list[Any] = []

        for line in lines:
            line = line.strip()
            if line:  # Skip empty lines
                # Use pluggable parser
                results.append(self._parser.loads(line))

        return results

    # -------------------------------------------------------------------------
    # RECORD-LEVEL OPERATIONS (True streaming, line-by-line)
    # -------------------------------------------------------------------------

    def stream_read_record(
        self,
        file_path: Union[str, Path],
        match: callable,
        projection: Optional[list[Any]] = None,
        **options: Any,
    ) -> Any:
        """
        Stream-style read of a single logical record from a JSONL file.

        Reads the file line-by-line, parsing each JSON object and returning the
        first record that satisfies match(record). Optional projection is
        applied using the base helper to avoid duplicating logic.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Line-by-line scan – no full-file load
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Use pluggable parser
                record = self._parser.loads(line)
                if match(record):
                    return self._apply_projection(record, projection)

        raise KeyError("No matching record found")

    def stream_update_record(
        self,
        file_path: Union[str, Path],
        match: callable,
        updater: callable,
        *,
        atomic: bool = True,
        **options: Any,
    ) -> int:
        """
        Stream-style update of logical records in a JSONL file.

        Implementation uses a temp file + AtomicFileWriter pattern to ensure
        atomicity when atomic=True. Records are processed line-by-line and only
        the matching records are materialized and updated.
        
        Supports append-only log optimization for large files (use_append_log=True).
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Check if append-only log should be used
        perf_config = get_performance_config()
        use_append_log = options.get("use_append_log", None)
        if use_append_log is None:
            if not perf_config.enable_append_log:
                use_append_log = False
            else:
                # Auto-detect: use for files above threshold
                file_size_mb = path.stat().st_size / (1024 * 1024)
                use_append_log = file_size_mb > perf_config.append_log_threshold_mb

        # Try append-only log if enabled
        if use_append_log:
            try:
                from .append_only_log import AppendOnlyLog
                log = AppendOnlyLog(path)
                
                # For append-only log, we need to find matching records first
                # and apply updates, then append to log
                # This is a simplified version - full implementation would
                # integrate with index for O(1) lookups
                updated = 0
                with path.open("r", encoding="utf-8") as src:
                    for line in src:
                        raw = line.rstrip("\n")
                        if not raw.strip():
                            continue
                        
                        try:
                            record = self._parser.loads(raw)
                            if match(record):
                                # Apply updater
                                updated_record = updater(record)
                                
                                # Extract type and id for log entry
                                type_name = record.get("@type") or record.get("type") or "Record"
                                id_value = str(record.get("id", ""))
                                
                                # Append to log
                                log.update_record(type_name, id_value, lambda x: updated_record)
                                updated += 1
                        except Exception:
                            continue
                
                return updated
            except Exception as e:
                # Fall back to full rewrite if append-only log fails
                logger.debug(f"Append-only log failed, falling back to full rewrite: {e}")

        # Original full-rewrite implementation
        updated = 0
        backup = options.get("backup", True)
        ensure_ascii = options.get("ensure_ascii", False)

        try:
            if atomic:
                # Atomic path: use AtomicFileWriter for temp+replace semantics
                with AtomicFileWriter(path, backup=backup) as writer:
                    with path.open("r", encoding="utf-8") as src:
                        for line in src:
                            raw = line.rstrip("\n")
                            if not raw.strip():
                                # Preserve structural empty lines
                                writer.write("\n")
                                continue

                            # Use pluggable parser
                            record = self._parser.loads(raw)
                            if match(record):
                                record = updater(record)
                                updated += 1

                            # Use pluggable parser for serialization
                            result = self._parser.dumps(record, ensure_ascii=ensure_ascii)
                            if isinstance(result, bytes):
                                result = result.decode("utf-8")
                            out_line = result + "\n"
                            writer.write(out_line)
            else:
                # Non-atomic fallback: read + rewrite line-by-line
                new_lines: list[str] = []
                with path.open("r", encoding="utf-8") as src:
                    for line in src:
                        raw = line.rstrip("\n")
                        if not raw.strip():
                            new_lines.append("\n")
                            continue

                        # Use pluggable parser
                        record = self._parser.loads(raw)
                        if match(record):
                            record = updater(record)
                            updated += 1

                        # Use pluggable parser for serialization
                        result = self._parser.dumps(record, ensure_ascii=ensure_ascii)
                        if isinstance(result, bytes):
                            result = result.decode("utf-8")
                        new_lines.append(result + "\n")

                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("".join(new_lines), encoding="utf-8")

            return updated
        except Exception as e:
            raise SerializationError(
                f"Failed to stream-update JSONL records in {path}: {e}",
                format_name=self.format_name,
                original_error=e,
            ) from e

    def get_record_page(
        self,
        file_path: Union[str, Path],
        page_number: int,
        page_size: int,
        **options: Any,
    ) -> list[Any]:
        """
        Retrieve a logical page of records from a JSONL file.

        Pages are computed by counting logical records (non-empty lines). Only
        the requested slice is parsed and returned, keeping memory usage
        proportional to page_size rather than file size.
        """
        if page_number < 1 or page_size <= 0:
            raise ValueError("Invalid page_number or page_size")

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        start_index = (page_number - 1) * page_size
        end_index = start_index + page_size

        results: list[Any] = []
        current_index = 0

        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                if current_index >= end_index:
                    break

                if current_index >= start_index:
                    # Use pluggable parser
                    results.append(self._parser.loads(line))

                current_index += 1

        return results

    def get_record_by_id(
        self,
        file_path: Union[str, Path],
        id_value: Any,
        *,
        id_field: str = "id",
        **options: Any,
    ) -> Any:
        """
        Retrieve a logical record by identifier from a JSONL file.

        Performs a streaming linear scan over records, returning the first
        record where record[id_field] == id_value.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Use pluggable parser
                record = self._parser.loads(line)
                if isinstance(record, dict) and record.get(id_field) == id_value:
                    return record

        raise KeyError(f"Record with {id_field}={id_value!r} not found")

