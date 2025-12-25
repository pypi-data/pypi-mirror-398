#!/usr/bin/env python3
#exonware/xwsystem/caching/stats.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 01-Nov-2025

Statistics formatting utilities for caching module.
Usability Priority #2 - Human-readable statistics display.
"""

from typing import Any
from .utils import format_bytes


def format_cache_stats(stats: dict[str, Any], style: str = 'box') -> str:
    """
    Format cache statistics as human-readable string.
    
    Args:
        stats: Cache statistics dictionary
        style: Display style ('box', 'table', 'compact')
        
    Returns:
        Formatted statistics string
    """
    if style == 'box':
        return _format_box_style(stats)
    elif style == 'table':
        return _format_table_style(stats)
    elif style == 'compact':
        return _format_compact_style(stats)
    else:
        return _format_box_style(stats)


def _format_box_style(stats: dict[str, Any]) -> str:
    """Format statistics in box style with borders."""
    name = stats.get('name', 'Unknown')
    cache_type = stats.get('type', 'Unknown')
    capacity = stats.get('capacity', 0)
    size = stats.get('size', 0)
    hits = stats.get('hits', 0)
    misses = stats.get('misses', 0)
    evictions = stats.get('evictions', 0)
    hit_rate = stats.get('hit_rate', 0.0)
    
    # Calculate fill percentage
    fill_pct = (size / capacity * 100) if capacity > 0 else 0
    
    # Build the box
    lines = [
        "╔" + "═" * 58 + "╗",
        f"║  Cache Statistics: {name:<38} ║",
        "╠" + "═" * 58 + "╣",
        f"║  Type:          {cache_type:<40} ║",
        f"║  Capacity:      {capacity:>10,} entries{' ' * 24} ║",
        f"║  Current Size:  {size:>10,} entries ({fill_pct:>5.1f}% full){' ' * 6} ║",
        "║" + " " * 58 + "║",
        f"║  Hit Rate:      {hit_rate:>10.1%}{' ' * 38} ║",
        f"║  Hits:          {hits:>10,}{' ' * 38} ║",
        f"║  Misses:        {misses:>10,}{' ' * 38} ║",
        f"║  Evictions:     {evictions:>10,}{' ' * 38} ║",
    ]
    
    # Add TTL info if present
    if 'ttl' in stats and stats['ttl']:
        lines.append(f"║  TTL:           {stats['ttl']:>10.1f} seconds{' ' * 27} ║")
    
    # Add memory info if present
    if 'memory_bytes' in stats:
        memory_str = format_bytes(stats['memory_bytes'])
        lines.append(f"║  Memory Usage:  {memory_str:>20}{' ' * 28} ║")
    
    lines.append("╚" + "═" * 58 + "╝")
    
    return "\n".join(lines)


def _format_table_style(stats: dict[str, Any]) -> str:
    """Format statistics in table style."""
    name = stats.get('name', 'Unknown')
    cache_type = stats.get('type', 'Unknown')
    
    lines = [
        f"Cache Statistics: {name}",
        "─" * 60,
        f"{'Metric':<25} {'Value':>15} {'Details':>15}",
        "─" * 60,
        f"{'Type':<25} {cache_type:>15}",
        f"{'Capacity':<25} {stats.get('capacity', 0):>15,} {'entries':>15}",
        f"{'Current Size':<25} {stats.get('size', 0):>15,} {'entries':>15}",
        f"{'Hit Rate':<25} {stats.get('hit_rate', 0.0):>14.1%}",
        f"{'Hits':<25} {stats.get('hits', 0):>15,}",
        f"{'Misses':<25} {stats.get('misses', 0):>15,}",
        f"{'Evictions':<25} {stats.get('evictions', 0):>15,}",
    ]
    
    if 'ttl' in stats and stats['ttl']:
        lines.append(f"{'TTL':<25} {stats['ttl']:>15.1f} {'seconds':>15}")
    
    lines.append("─" * 60)
    
    return "\n".join(lines)


def _format_compact_style(stats: dict[str, Any]) -> str:
    """Format statistics in compact one-line style."""
    name = stats.get('name', 'Unknown')
    cache_type = stats.get('type', 'Unknown')
    size = stats.get('size', 0)
    capacity = stats.get('capacity', 0)
    hit_rate = stats.get('hit_rate', 0.0)
    hits = stats.get('hits', 0)
    misses = stats.get('misses', 0)
    
    return (
        f"[{name}] {cache_type} | "
        f"Size: {size:,}/{capacity:,} | "
        f"Hit Rate: {hit_rate:.1%} | "
        f"Hits: {hits:,} | "
        f"Misses: {misses:,}"
    )


def format_cache_stats_table(cache_list: list) -> str:
    """
    Format statistics for multiple caches in a table.
    
    Args:
        cache_list: List of cache objects with get_stats() method
        
    Returns:
        Formatted table string
    """
    lines = [
        "Cache Statistics Summary",
        "=" * 120,
        f"{'Name':<20} {'Type':<12} {'Size':>10} {'Capacity':>10} {'Hit Rate':>10} {'Hits':>12} {'Misses':>12} {'Evictions':>12}",
        "=" * 120,
    ]
    
    for cache in cache_list:
        try:
            stats = cache.get_stats()
            name = stats.get('name', 'Unknown')[:20]
            cache_type = stats.get('type', 'Unknown')[:12]
            size = stats.get('size', 0)
            capacity = stats.get('capacity', 0)
            hit_rate = stats.get('hit_rate', 0.0)
            hits = stats.get('hits', 0)
            misses = stats.get('misses', 0)
            evictions = stats.get('evictions', 0)
            
            lines.append(
                f"{name:<20} {cache_type:<12} {size:>10,} {capacity:>10,} "
                f"{hit_rate:>9.1%} {hits:>12,} {misses:>12,} {evictions:>12,}"
            )
        except Exception as e:
            lines.append(f"{cache!r:<20} ERROR: {e}")
    
    lines.append("=" * 120)
    
    return "\n".join(lines)


def get_stats_summary(stats: dict[str, Any]) -> str:
    """
    Get one-line summary of cache statistics.
    
    Args:
        stats: Cache statistics dictionary
        
    Returns:
        One-line summary string
    """
    return _format_compact_style(stats)


__all__ = [
    'format_cache_stats',
    'format_cache_stats_table',
    'get_stats_summary',
]

