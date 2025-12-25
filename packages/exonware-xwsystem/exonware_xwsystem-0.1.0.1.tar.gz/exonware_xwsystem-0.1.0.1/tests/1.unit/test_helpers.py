"""
Test Helper Functions for Serialization Examples

Utility functions for testing and displaying results.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: October 12, 2025
"""

import time
from typing import Any, Callable
from pathlib import Path


def print_result(title: str, result: Any, max_length: int = 100):
    """Print formatted result"""
    print(f"\n{title}:")
    result_str = str(result)
    if len(result_str) > max_length:
        result_str = result_str[:max_length] + "..."
    print(f"  {result_str}")


def compare_performance(operations: dict[str, Callable], iterations: int = 100) -> dict[str, float]:
    """Compare performance of multiple operations"""
    results = {}
    
    for name, operation in operations.items():
        start = time.perf_counter()
        for _ in range(iterations):
            operation()
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        results[name] = elapsed / iterations
    
    return results


def save_to_file(data: Any, filepath: Path, mode: str = 'w'):
    """Save data to file"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    if mode == 'wb':
        with open(filepath, 'wb') as f:
            f.write(data if isinstance(data, bytes) else str(data).encode())
    else:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(data if isinstance(data, str) else str(data))
    
    print(f"✓ Saved to: {filepath}")


def print_separator(char='=', length=80):
    """Print separator line"""
    print(char * length)


def print_section(title: str):
    """Print section header"""
    print_separator()
    print(f" {title}")
    print_separator()

