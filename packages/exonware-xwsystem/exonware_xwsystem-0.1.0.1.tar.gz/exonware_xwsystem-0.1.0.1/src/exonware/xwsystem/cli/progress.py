"""
Progress Bar Utilities
=====================

Production-grade progress indicators for XSystem.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 05, 2025
"""

import sys
import time
import threading
from typing import Optional, TextIO, Union
from dataclasses import dataclass
import math

# Import colors from our existing color module
# Explicit import - colors module is part of the same package
from .colors import colorize, Colors, Style


@dataclass
class ProgressConfig:
    """Configuration for progress indicators."""
    width: int = 50
    show_percentage: bool = True
    show_count: bool = True
    show_rate: bool = True
    show_eta: bool = True
    refresh_rate: float = 0.1  # seconds
    color: str = Colors.GREEN
    style: str = Style.BOLD


class ProgressBar:
    """
    Production-grade progress bar with ETA and rate calculation.
    
    Features:
    - Real-time progress tracking
    - ETA (Estimated Time of Arrival) calculation
    - Rate calculation (items/second)
    - Customizable appearance
    - Thread-safe updates
    - Context manager support
    """
    
    def __init__(self, 
                 total: int,
                 description: str = "",
                 config: ProgressConfig = None,
                 file: TextIO = None):
        """
        Initialize progress bar.
        
        Args:
            total: Total number of items to process
            description: Description text
            config: Progress configuration
            file: Output file (defaults to stderr)
        """
        self.total = total
        self.description = description
        self.config = config or ProgressConfig()
        self.file = file or sys.stderr
        
        # Progress tracking
        self.current = 0
        self.start_time = time.time()
        self.last_update = 0
        
        # Thread safety
        self._lock = threading.Lock()
        self._closed = False
        
        # Rate calculation
        self._rate_samples = []
        self._last_rate_update = self.start_time
    
    def update(self, n: int = 1) -> None:
        """
        Update progress by n items.
        
        Args:
            n: Number of items to add to progress
        """
        with self._lock:
            if self._closed:
                return
            
            self.current = min(self.current + n, self.total)
            current_time = time.time()
            
            # Update rate calculation
            if current_time - self._last_rate_update >= 1.0:  # Update rate every second
                self._update_rate(current_time)
                self._last_rate_update = current_time
            
            # Check if we should refresh display
            if (current_time - self.last_update >= self.config.refresh_rate or 
                self.current >= self.total):
                self._refresh_display()
                self.last_update = current_time
    
    def set_progress(self, current: int) -> None:
        """
        Set absolute progress.
        
        Args:
            current: Current progress value
        """
        with self._lock:
            if self._closed:
                return
            
            self.current = min(max(current, 0), self.total)
            self._refresh_display()
    
    def _update_rate(self, current_time: float):
        """Update rate calculation."""
        elapsed = current_time - self.start_time
        if elapsed > 0:
            current_rate = self.current / elapsed
            self._rate_samples.append(current_rate)
            
            # Keep only recent samples (last 10 seconds)
            if len(self._rate_samples) > 10:
                self._rate_samples.pop(0)
    
    def _get_rate(self) -> float:
        """Get current processing rate."""
        if not self._rate_samples:
            elapsed = time.time() - self.start_time
            return self.current / elapsed if elapsed > 0 else 0
        return sum(self._rate_samples) / len(self._rate_samples)
    
    def _get_eta(self) -> Optional[float]:
        """Get estimated time to completion."""
        if self.current == 0:
            return None
        
        rate = self._get_rate()
        if rate <= 0:
            return None
        
        remaining = self.total - self.current
        return remaining / rate
    
    def _format_time(self, seconds: float) -> str:
        """Format time duration."""
        if seconds is None or seconds < 0:
            return "??:??"
        
        if seconds < 60:
            return f"{int(seconds):02d}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes:02d}:{secs:02d}"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours:02d}:{minutes:02d}h"
    
    def _format_rate(self, rate: float) -> str:
        """Format processing rate."""
        if rate >= 1000:
            return f"{rate/1000:.1f}K/s"
        elif rate >= 1:
            return f"{rate:.1f}/s"
        else:
            return f"{rate:.2f}/s"
    
    def _refresh_display(self):
        """Refresh the progress bar display."""
        if self._closed:
            return
        
        # Calculate percentage
        percentage = (self.current / self.total * 100) if self.total > 0 else 0
        
        # Create progress bar
        filled_width = int(self.config.width * self.current / self.total) if self.total > 0 else 0
        bar = "█" * filled_width + "░" * (self.config.width - filled_width)
        
        # Apply color
        colored_bar = colorize(bar, self.config.color, self.config.style)
        
        # Build status line
        parts = []
        
        if self.description:
            parts.append(self.description)
        
        parts.append(f"|{colored_bar}|")
        
        if self.config.show_percentage:
            parts.append(f"{percentage:5.1f}%")
        
        if self.config.show_count:
            parts.append(f"({self.current}/{self.total})")
        
        if self.config.show_rate:
            rate = self._get_rate()
            parts.append(f"[{self._format_rate(rate)}]")
        
        if self.config.show_eta:
            eta = self._get_eta()
            parts.append(f"ETA: {self._format_time(eta)}")
        
        # Write to output
        line = " ".join(parts)
        self.file.write(f"\r{line}")
        self.file.flush()
        
        # Add newline if complete
        if self.current >= self.total:
            self.file.write("\n")
            self.file.flush()
    
    def close(self):
        """Close the progress bar."""
        with self._lock:
            if not self._closed:
                self._closed = True
                if self.current < self.total:
                    self.file.write("\n")
                    self.file.flush()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class SpinnerProgress:
    """
    Spinning progress indicator for indeterminate tasks.
    
    Features:
    - Multiple spinner styles
    - Custom messages
    - Thread-safe operation
    - Context manager support
    """
    
    SPINNERS = {
        'dots': ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
        'line': ['|', '/', '-', '\\'],
        'arrows': ['←', '↖', '↑', '↗', '→', '↘', '↓', '↙'],
        'bounce': ['⠁', '⠂', '⠄', '⠂'],
        'clock': ['🕐', '🕑', '🕒', '🕓', '🕔', '🕕', '🕖', '🕗', '🕘', '🕙', '🕚', '🕛'],
    }
    
    def __init__(self, 
                 message: str = "Processing...",
                 spinner: str = 'dots',
                 speed: float = 0.1,
                 file: TextIO = None):
        """
        Initialize spinner.
        
        Args:
            message: Message to display
            spinner: Spinner style name
            speed: Animation speed in seconds
            file: Output file
        """
        self.message = message
        self.frames = self.SPINNERS.get(spinner, self.SPINNERS['dots'])
        self.speed = speed
        self.file = file or sys.stderr
        
        self._running = False
        self._thread = None
        self._frame_index = 0
        self._lock = threading.Lock()
    
    def start(self) -> 'SpinnerProgress':
        """Start the spinner animation."""
        with self._lock:
            if not self._running:
                self._running = True
                self._thread = threading.Thread(target=self._animate, daemon=True)
                self._thread.start()
        return self
    
    def stop(self):
        """Stop the spinner animation."""
        with self._lock:
            if self._running:
                self._running = False
                if self._thread and self._thread.is_alive():
                    self._thread.join(timeout=1.0)
                # Clear the line
                self.file.write("\r" + " " * (len(self.message) + 10) + "\r")
                self.file.flush()
    
    def update_message(self, message: str):
        """Update the spinner message."""
        with self._lock:
            self.message = message
    
    def _animate(self):
        """Animation loop."""
        while self._running:
            frame = self.frames[self._frame_index % len(self.frames)]
            colored_frame = colorize(frame, Colors.CYAN, Style.BOLD)
            
            line = f"\r{colored_frame} {self.message}"
            self.file.write(line)
            self.file.flush()
            
            self._frame_index += 1
            time.sleep(self.speed)
    
    def __enter__(self):
        """Context manager entry."""
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


class MultiProgress:
    """
    Multiple progress bars manager.
    
    Features:
    - Multiple concurrent progress bars
    - Dynamic add/remove bars
    - Synchronized display updates
    - Thread-safe operations
    """
    
    def __init__(self, file: TextIO = None):
        """
        Initialize multi-progress manager.
        
        Args:
            file: Output file
        """
        self.file = file or sys.stderr
        self._bars = {}
        self._lock = threading.Lock()
        self._active = False
    
    def add_bar(self, 
                bar_id: str, 
                total: int, 
                description: str = "",
                config: ProgressConfig = None) -> ProgressBar:
        """
        Add a new progress bar.
        
        Args:
            bar_id: Unique identifier for the bar
            total: Total items for this bar
            description: Description text
            config: Progress configuration
            
        Returns:
            ProgressBar instance
        """
        with self._lock:
            if bar_id in self._bars:
                raise ValueError(f"Progress bar '{bar_id}' already exists")
            
            # Create progress bar with custom file to prevent direct output
            bar = ProgressBar(total, description, config, file=self)
            self._bars[bar_id] = bar
            self._active = True
            return bar
    
    def remove_bar(self, bar_id: str):
        """Remove a progress bar."""
        with self._lock:
            if bar_id in self._bars:
                del self._bars[bar_id]
            
            if not self._bars:
                self._active = False
    
    def update_display(self):
        """Update all progress bar displays."""
        with self._lock:
            if not self._active:
                return
            
            # Move cursor to beginning of progress section
            num_bars = len(self._bars)
            if num_bars > 0:
                # Move cursor up to overwrite previous bars
                self.file.write(f"\033[{num_bars}A")
            
            # Redraw all bars
            for bar_id, bar in self._bars.items():
                bar._refresh_display()
                self.file.write("\n")
            
            self.file.flush()
    
    def write(self, text: str):
        """Custom write method for progress bars to use."""
        # This is called by individual progress bars
        # We'll collect the output and display it all at once
        pass
    
    def flush(self):
        """Custom flush method."""
        pass
    
    def close_all(self):
        """Close all progress bars."""
        with self._lock:
            for bar in self._bars.values():
                bar.close()
            self._bars.clear()
            self._active = False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_all()


# Utility functions
def create_progress_bar(total: int, description: str = "") -> ProgressBar:
    """Create a simple progress bar."""
    return ProgressBar(total, description)


def create_spinner(message: str = "Processing...") -> SpinnerProgress:
    """Create a simple spinner."""
    return SpinnerProgress(message)


def progress_range(iterable, description: str = ""):
    """Wrap an iterable with a progress bar."""
    total = len(iterable) if hasattr(iterable, '__len__') else None
    
    if total is not None:
        with ProgressBar(total, description) as pbar:
            for item in iterable:
                yield item
                pbar.update(1)
    else:
        # Use spinner for unknown length iterables
        with SpinnerProgress(description) as spinner:
            for item in iterable:
                yield item
