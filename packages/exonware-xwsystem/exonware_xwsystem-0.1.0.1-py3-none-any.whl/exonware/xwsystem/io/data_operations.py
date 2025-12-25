#!/usr/bin/env python3
"""
#exonware/xwsystem/src/exonware/xwsystem/io/data_operations.py

Generic data-operations layer for large, file-backed datasets.

This module provides:
- A small indexing model for line-oriented files (e.g. NDJSON / JSONL)
- Streaming read / update helpers with atomic guarantees
- Paging helpers built on top of line offsets

The goal is to expose these capabilities in a format-agnostic way so that
higher-level libraries (xwdata, xwnode, xwentity, etc.) can build powerful
lazy, paged, and atomic access features without re-implementing I/O logic.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 15-Dec-2025
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional
from abc import ABC, abstractmethod
import json
import os
import tempfile
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

from .serialization.auto_serializer import AutoSerializer
from exonware.xwsystem.config.logging_setup import get_logger
from exonware.xwsystem.config.performance import get_performance_config


logger = get_logger(__name__)


JsonMatchFn = Callable[[Any], bool]


def _process_chunk_worker(args: tuple[int, int, int, str, str, str | None, int | None, bool]) -> tuple[list[int] | None, dict[str, int], int]:
    """
    Process a single chunk (runs in worker process).
    
    This is a module-level function to make it picklable for multiprocessing.
    """
    chunk_id, start_offset, end_offset, file_path_str, encoding, id_field_arg, max_id_index_arg, build_line_offsets_arg = args
    chunk_line_offsets: list[int] | None = [] if build_line_offsets_arg else None
    chunk_id_index: dict[str, int] = {}
    lines_processed = 0
    
    # Import parser in worker process (can't pickle serializer)
    try:
        from exonware.xwsystem.io.serialization.parsers.registry import get_best_available_parser
        parser = get_best_available_parser()
    except ImportError:
        import json as parser
    
    try:
        with open(file_path_str, "rb") as f:
            f.seek(start_offset)
            current_offset = start_offset
            
            while current_offset < end_offset:
                line_start = current_offset
                line = f.readline()
                
                if not line:
                    break
                
                current_offset = f.tell()
                
                # Skip if we've gone past the end
                if line_start >= end_offset:
                    break
                
                # Optimize: Check empty lines early (match example code pattern)
                raw = line.strip()
                if not raw:
                    continue
                
                # Track line offset if requested, calculate line_idx once
                if build_line_offsets_arg:
                    chunk_line_offsets.append(line_start)
                    line_idx = len(chunk_line_offsets) - 1
                else:
                    line_idx = lines_processed
                
                if id_field_arg and (max_id_index_arg is None or len(chunk_id_index) < max_id_index_arg):
                    try:
                        # Parser accepts bytes directly (hybrid parser handles it)
                        obj = parser.loads(raw)
                        if isinstance(obj, dict) and id_field_arg in obj:
                            id_val = str(obj[id_field_arg])
                            chunk_id_index[id_val] = line_idx
                    except Exception:
                        # Skip invalid lines (best-effort indexing)
                        pass
                
                lines_processed += 1
    except Exception as e:
        # Can't use logger in worker process, just pass
        pass
    
    return (chunk_line_offsets, chunk_id_index, lines_processed)
JsonUpdateFn = Callable[[Any], Any]


@dataclass
class JsonIndexMeta:
    """
    Minimal metadata for a JSONL/NDJSON index.

    This intentionally mirrors the capabilities used in the x5 examples
    without pulling in any of the example code directly.
    """

    path: str
    size: int
    mtime: float
    version: int = 1


@dataclass
class JsonIndex:
    """
    Simple index for line-oriented JSON files.

    - line_offsets: byte offset of each JSON line
    - id_index: optional mapping id_value -> line_number
    """

    meta: JsonIndexMeta
    line_offsets: list[int]
    id_index: Optional[dict[str, int]] = None


class ADataOperations(ABC):
    """
    Abstract, format-agnostic interface for large, file-backed data operations.

    Concrete implementations may target specific physical layouts
    (NDJSON/JSONL, multi-document YAML, binary record stores, etc.), but MUST
    conform to these semantics:

    - Streaming, record-by-record read with a match predicate.
    - Streaming, atomic update using a temp file + replace pattern.
    - Optional indexing for random access and paging.
    """

    @abstractmethod
    def stream_read(
        self,
        file_path: str | Path,
        match: JsonMatchFn,
        path: Optional[list[object]] = None,
        encoding: str = "utf-8",
    ) -> Any:
        """Return the first record (or sub-path) that matches the predicate."""
        raise NotImplementedError

    @abstractmethod
    def stream_update(
        self,
        file_path: str | Path,
        match: JsonMatchFn,
        updater: JsonUpdateFn,
        *,
        encoding: str = "utf-8",
        newline: str = "\n",
        atomic: bool = True,
    ) -> int:
        """
        Stream-copy the backing store, applying `updater` to matching records.

        MUST use atomic replace semantics when `atomic=True`.
        Returns number of updated records.
        """
        raise NotImplementedError

    @abstractmethod
    def build_index(
        self,
        file_path: str | Path,
        *,
        encoding: str = "utf-8",
        id_field: str | None = None,
        max_id_index: int | None = None,
    ) -> JsonIndex:
        """Build an index structure suitable for random access and paging."""
        raise NotImplementedError

    @abstractmethod
    def indexed_get_by_line(
        self,
        file_path: str | Path,
        line_number: int,
        *,
        encoding: str = "utf-8",
        index: Optional[JsonIndex] = None,
    ) -> Any:
        """Random-access a specific logical record by its index position."""
        raise NotImplementedError

    @abstractmethod
    def indexed_get_by_id(
        self,
        file_path: str | Path,
        id_value: Any,
        *,
        encoding: str = "utf-8",
        id_field: str = "id",
        index: Optional[JsonIndex] = None,
    ) -> Any:
        """Random-access a record by logical identifier, with optional index."""
        raise NotImplementedError

    @abstractmethod
    def get_page(
        self,
        file_path: str | Path,
        page_number: int,
        page_size: int,
        *,
        encoding: str = "utf-8",
        index: Optional[JsonIndex] = None,
    ) -> list[Any]:
        """Return a page of logical records using an index for efficiency."""
        raise NotImplementedError


class NDJSONDataOperations(ADataOperations):
    """
    Generic data-operations helper for NDJSON / JSONL style files.

    This class is deliberately low-level and works directly with paths and
    native Python data. XWData and other libraries can wrap it to provide
    higher-level, type-agnostic facades.
    """

    def __init__(self, serializer: Optional[AutoSerializer] = None):
        # Reuse xwsystem's AutoSerializer so we do not re-implement parsing.
        self._serializer = serializer or AutoSerializer(default_format="JSON")

    # ------------------------------------------------------------------
    # Streaming read
    # ------------------------------------------------------------------

    def stream_read(
        self,
        file_path: str | Path,
        match: JsonMatchFn,
        path: Optional[list[object]] = None,
        encoding: str = "utf-8",
    ) -> Any:
        """
        Stream a huge NDJSON file and return the first record (or sub-path)
        matching `match`.

        This is intentionally simple and focused:
        - Reads one line at a time
        - Uses AutoSerializer(JSON) for parsing
        - Optional path extraction
        """
        target = Path(file_path)
        if not target.exists():
            raise FileNotFoundError(str(target))

        with target.open("r", encoding=encoding) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = self._serializer.detect_and_deserialize(
                    line, file_path=target, format_hint="JSON"
                )
                if match(obj):
                    return self._extract_path(obj, path)

        raise KeyError("No matching record found")

    # ------------------------------------------------------------------
    # Streaming update with atomic replace
    # ------------------------------------------------------------------

    def stream_update(
        self,
        file_path: str | Path,
        match: JsonMatchFn,
        updater: JsonUpdateFn,
        *,
        encoding: str = "utf-8",
        newline: str = "\n",
        atomic: bool = True,
    ) -> int:
        """
        Stream-copy a huge NDJSON file, applying `updater` to records
        where `match(obj)` is True.

        Only matching records are fully materialized. All writes go to a
        temporary file, which is atomically replaced on success.

        Returns the number of updated records.
        """
        target = Path(file_path)
        if not target.exists():
            raise FileNotFoundError(str(target))

        updated = 0
        dir_path = target.parent

        # Write to a temp file in the same directory for atomic replace.
        fd, tmp_path_str = tempfile.mkstemp(
            prefix=f".{target.name}.tmp.", dir=str(dir_path)
        )
        tmp_path = Path(tmp_path_str)

        try:
            with os.fdopen(fd, "w", encoding=encoding, newline=newline) as out_f, target.open(
                "r", encoding=encoding
            ) as in_f:
                for line in in_f:
                    raw = line.rstrip("\n")
                    if not raw:
                        out_f.write(line)
                        continue

                    obj = self._serializer.detect_and_deserialize(
                        raw, file_path=target, format_hint="JSON"
                    )
                    if match(obj):
                        updated_obj = updater(obj)
                        updated_line = json.dumps(updated_obj, ensure_ascii=False)
                        out_f.write(updated_line + newline)
                        updated += 1
                    else:
                        out_f.write(line)

            if atomic:
                os.replace(tmp_path, target)
            else:
                tmp_path.replace(target)

            return updated
        finally:
            # Ensure temp file is removed on error
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    # Best-effort cleanup; do not mask original error.
                    logger.debug("Failed to cleanup temp file %s", tmp_path)

    # ------------------------------------------------------------------
    # Indexing and paging
    # ------------------------------------------------------------------

    def build_index(
        self,
        file_path: str | Path,
        *,
        encoding: str = "utf-8",
        id_field: str | None = None,
        max_id_index: int | None = None,
        use_parallel: bool | None = None,
        num_workers: int | None = None,
        chunk_size_mb: int = 100,
        build_line_offsets: bool = True,
    ) -> JsonIndex:
        """
        One-time full scan to build an index:
          - line_offsets: byte offset of each JSON line
          - optional id_index: obj[id_field] -> line_number
        
        Args:
            file_path: Path to JSONL file
            encoding: File encoding (default: utf-8)
            id_field: Optional field name to build id_index
            max_id_index: Maximum entries in id_index (None = unlimited)
            use_parallel: Enable parallel processing (None = auto-detect based on file size)
            num_workers: Number of worker processes (None = CPU count)
            chunk_size_mb: Chunk size in MB for parallel processing (default: 100MB)
            build_line_offsets: If True, build line_offsets list (default: True, set False for faster id_index-only builds)
        
        Returns:
            JsonIndex with line_offsets (if build_line_offsets=True) and optional id_index
        """
        target = Path(file_path)
        if not target.exists():
            raise FileNotFoundError(str(target))

        # Auto-detect parallel based on config
        perf_config = get_performance_config()
        if use_parallel is None:
            if not perf_config.enable_parallel_index:
                use_parallel = False
            else:
                file_size_mb = target.stat().st_size / 1_048_576  # 1024 * 1024
                use_parallel = file_size_mb > perf_config.parallel_index_threshold_mb
        
        # Use config defaults for workers and chunk size
        if num_workers is None:
            num_workers = perf_config.parallel_index_workers
        if chunk_size_mb == 100:  # Only use default if not explicitly set
            chunk_size_mb = perf_config.parallel_index_chunk_size_mb

        # Use parallel processing if enabled and file is large enough
        if use_parallel:
            try:
                return self._build_index_parallel(
                    target,
                    encoding=encoding,
                    id_field=id_field,
                    max_id_index=max_id_index,
                    num_workers=num_workers,
                    chunk_size_mb=chunk_size_mb,
                    build_line_offsets=build_line_offsets,
                )
            except Exception as e:
                logger.warning(f"Parallel index building failed, falling back to single-threaded: {e}")
                # Fall through to single-threaded

        # Single-threaded implementation (optimized - matches example code exactly)
        line_offsets: list[int] | None = [] if build_line_offsets else None
        id_index: dict[str, int] | None = {} if id_field else None

        size = target.stat().st_size
        mtime = target.stat().st_mtime

        # Cache parser instance (matches example code pattern)
        try:
            from exonware.xwsystem.io.serialization.parsers.registry import get_best_available_parser
            parser = get_best_available_parser()
        except ImportError:
            import json as parser

        offset = 0
        with target.open("rb") as f:
            line_no = 0
            while True:
                line = f.readline()
                if not line:
                    break
                if build_line_offsets:
                    line_offsets.append(offset)

                if id_index is not None:
                    try:
                        # Match example code exactly: strip bytes, parse directly
                        raw = line.strip()
                        if raw:
                            # Parser accepts bytes directly (hybrid parser handles it)
                            obj = parser.loads(raw)
                            if isinstance(obj, dict) and id_field in obj:
                                id_val = str(obj[id_field])
                                if max_id_index is None or len(id_index) < max_id_index:
                                    id_index[id_val] = line_no
                    except Exception:
                        # Index should be best-effort and robust to bad lines.
                        # Skip invalid lines silently for performance
                        pass

                offset += len(line)
                line_no += 1

        meta = JsonIndexMeta(path=str(target), size=size, mtime=mtime, version=1)
        return JsonIndex(meta=meta, line_offsets=line_offsets, id_index=id_index)
    
    def _build_index_parallel(
        self,
        file_path: Path,
        *,
        encoding: str = "utf-8",
        id_field: str | None = None,
        max_id_index: int | None = None,
        num_workers: int | None = None,
        chunk_size_mb: int = 100,
        build_line_offsets: bool = True,
    ) -> JsonIndex:
        """
        Parallel index building using multiple CPU cores.
        
        This is an internal method called by build_index() when use_parallel=True.
        """
        if num_workers is None:
            # Optimize: Simple formula - 1 worker per 10MB (capped at ProcessPoolExecutor limit)
            # ProcessPoolExecutor max_workers limit is 61 on Windows
            file_size_mb = file_path.stat().st_size / 1_048_576  # 1024 * 1024
            calculated_workers = int(file_size_mb / 10)  # 1 worker per 10MB
            # Cap at 61 (ProcessPoolExecutor limit) or CPU count, whichever is higher
            cpu_count = mp.cpu_count()
            num_workers = max(cpu_count, min(61, calculated_workers))
        
        file_size = file_path.stat().st_size
        chunk_size_bytes = chunk_size_mb * 1_048_576  # 1024 * 1024
        
        # If file is too small, fall back to single-threaded
        if file_size < chunk_size_bytes * 2:
            raise ValueError("File too small for parallel processing")
        
        # Split file into chunks
        chunks = []
        current_offset = 0
        chunk_id = 0
        
        while current_offset < file_size:
            chunk_end = min(current_offset + chunk_size_bytes, file_size)
            chunks.append((chunk_id, current_offset, chunk_end))
            current_offset = chunk_end
            chunk_id += 1
        
        # Limit number of chunks
        if len(chunks) > num_workers * 2:
            merged_chunks = []
            for i in range(0, len(chunks), max(1, len(chunks) // num_workers)):
                chunk_group = chunks[i:i + max(1, len(chunks) // num_workers)]
                if chunk_group:
                    merged_chunks.append((
                        chunk_group[0][0],
                        chunk_group[0][1],
                        chunk_group[-1][2]
                    ))
            chunks = merged_chunks
        
        logger.debug(f"Processing {len(chunks)} chunks with {num_workers} workers")
        
        # Process chunks in parallel
        line_offsets: list[int] | None = [] if build_line_offsets else None
        id_index: dict[str, int] | None = {} if id_field else None
        
        # Prepare arguments for worker processes
        chunk_args = [
            (chunk[0], chunk[1], chunk[2], str(file_path), encoding, id_field, max_id_index, build_line_offsets)
            for chunk in chunks
        ]
        
        # Execute parallel processing
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = {
                executor.submit(_process_chunk_worker, args): args[0]
                for args in chunk_args
            }
            
            # Optimize: Use dict for O(1) lookup instead of sorting
            chunk_results_dict: dict[int, tuple[list[int], dict[str, int]]] = {}
            for future in as_completed(futures):
                try:
                    chunk_offsets, chunk_ids, _ = future.result()
                    chunk_id = futures[future]
                    chunk_results_dict[chunk_id] = (chunk_offsets, chunk_ids)
                except Exception as e:
                    logger.warning(f"Chunk processing failed: {e}")
                    raise
        
        # Merge results (process in order by chunk_id)
        if build_line_offsets:
            # Optimize: Pre-calculate total size for better memory allocation
            total_offsets = sum(len(offsets) if offsets else 0 for offsets, _ in chunk_results_dict.values())
            if total_offsets > 0:
                # Pre-allocate list for better performance
                line_offsets = [0] * total_offsets
                current_idx = 0
            else:
                line_offsets = []
                current_idx = 0
        else:
            current_idx = 0
        
        for chunk_id in sorted(chunk_results_dict.keys()):
            chunk_offsets, chunk_ids = chunk_results_dict[chunk_id]
            
            # Merge line_offsets if building them
            if build_line_offsets and chunk_offsets:
                # Optimize: Use slice assignment for faster extend
                if total_offsets > 0:
                    line_offsets[current_idx:current_idx + len(chunk_offsets)] = chunk_offsets
                    base_line = current_idx
                    current_idx += len(chunk_offsets)
                else:
                    base_line = len(line_offsets)
                    line_offsets.extend(chunk_offsets)
            else:
                # Calculate base_line for id_index even without line_offsets
                base_line = current_idx
                if chunk_offsets:
                    current_idx += len(chunk_offsets)
                else:
                    # Estimate: assume average line size if we don't have offsets
                    current_idx += 300  # Rough estimate
            
            if id_index is not None and chunk_ids:
                # Optimize: Batch update with dict.update() if no limit
                if max_id_index is None:
                    # Fast path: no limit, use dict comprehension + update
                    id_index.update({id_val: base_line + rel_line for id_val, rel_line in chunk_ids.items()})
                else:
                    # Slower path: check limit per item
                    for id_val, rel_line in chunk_ids.items():
                        if len(id_index) < max_id_index:
                            id_index[id_val] = base_line + rel_line
        
        size = file_path.stat().st_size
        mtime = file_path.stat().st_mtime
        meta = JsonIndexMeta(path=str(file_path), size=size, mtime=mtime, version=1)
        return JsonIndex(meta=meta, line_offsets=line_offsets, id_index=id_index)

    def indexed_get_by_line(
        self,
        file_path: str | Path,
        line_number: int,
        *,
        encoding: str = "utf-8",
        index: Optional[JsonIndex] = None,
    ) -> Any:
        """
        Random-access a specific record by line_number (0-based) using index.
        """
        target = Path(file_path)
        if index is None:
            index = self.build_index(target, encoding=encoding)

        if line_number < 0 or line_number >= len(index.line_offsets):
            raise IndexError("line_number out of range")

        offset = index.line_offsets[line_number]
        with target.open("rb") as f:
            f.seek(offset)
            line = f.readline()
            text = line.decode(encoding).strip()
            if not text:
                raise ValueError("Empty line at indexed position")
            return self._serializer.detect_and_deserialize(
                text, file_path=target, format_hint="JSON"
            )

    def indexed_get_by_id(
        self,
        file_path: str | Path,
        id_value: Any,
        *,
        encoding: str = "utf-8",
        id_field: str = "id",
        index: Optional[JsonIndex] = None,
    ) -> Any:
        """
        Random-access a record by logical id using id_index if available.
        Falls back to linear scan if id_index missing or incomplete.
        """
        target = Path(file_path)
        if index is None:
            index = self.build_index(target, encoding=encoding, id_field=id_field)

        id_index = index.id_index
        if id_index is not None:
            key = str(id_value)
            if key in id_index:
                return self.indexed_get_by_line(
                    target, id_index[key], encoding=encoding, index=index
                )

        # Fallback: linear scan using stream_read semantics
        def _match(obj: Any) -> bool:
            return isinstance(obj, dict) and obj.get(id_field) == id_value

        return self.stream_read(target, _match, path=None, encoding=encoding)

    def get_page(
        self,
        file_path: str | Path,
        page_number: int,
        page_size: int,
        *,
        encoding: str = "utf-8",
        index: Optional[JsonIndex] = None,
    ) -> list[Any]:
        """
        Paging helper using index:
          - page_number: 1-based
          - page_size: number of records per page
        """
        target = Path(file_path)
        if index is None:
            index = self.build_index(target, encoding=encoding)

        if page_number < 1 or page_size <= 0:
            raise ValueError("Invalid page_number or page_size")

        start = (page_number - 1) * page_size
        end = start + page_size

        if start >= len(index.line_offsets):
            return []

        end = min(end, len(index.line_offsets))

        results: list[Any] = []
        with target.open("rb") as f:
            for line_no in range(start, end):
                offset = index.line_offsets[line_no]
                f.seek(offset)
                line = f.readline()
                text = line.decode(encoding).strip()
                if not text:
                    continue
                obj = self._serializer.detect_and_deserialize(
                    text, file_path=target, format_hint="JSON"
                )
                results.append(obj)

        return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_path(self, obj: Any, path: Optional[list[object]]) -> Any:
        """Extract a nested path like ['user', 'email'] or ['tags', 0]."""
        if not path:
            return obj

        current = obj
        for part in path:
            if isinstance(current, dict) and isinstance(part, str):
                if part not in current:
                    raise KeyError(part)
                current = current[part]
            elif isinstance(current, list) and isinstance(part, int):
                current = current[part]
            else:
                raise KeyError(part)
        return current


__all__ = [
    "JsonIndexMeta",
    "JsonIndex",
    "ADataOperations",
    "NDJSONDataOperations",
]


