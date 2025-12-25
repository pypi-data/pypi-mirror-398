"""
Table Formatting Utilities
==========================

Production-grade table formatting for XWSystem.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 05, 2025
"""

import sys
from typing import Any, Optional, Union, TextIO, Callable
from dataclasses import dataclass
# Import colors from our existing color module
# Explicit import - colors module is part of the same package
from .colors import colorize, Colors, Style
from .defs import Alignment, BorderStyle


@dataclass
class Column:
    """
    Table column definition.
    
    Features:
    - Custom alignment and width
    - Header and data formatting
    - Color and style customization
    - Data validation and transformation
    """
    
    header: str
    width: Optional[int] = None
    alignment: Alignment = Alignment.LEFT
    color: Optional[str] = None
    style: Optional[str] = None
    header_color: Optional[str] = None
    header_style: Optional[str] = None
    formatter: Optional[Callable[[Any], str]] = None
    min_width: int = 1
    max_width: Optional[int] = None
    
    def __post_init__(self):
        """Initialize column defaults."""
        if self.width is not None:
            self.width = max(self.width, self.min_width)
            if self.max_width is not None:
                self.width = min(self.width, self.max_width)


class TableFormatter:
    """
    Production-grade table formatter.
    
    Features:
    - Multiple border styles
    - Custom column formatting
    - Color and styling support
    - Auto-sizing and word wrapping
    - Header and footer support
    - Export to different formats
    """
    
    BORDER_CHARS = {
        BorderStyle.NONE: {
            'top_left': '', 'top_right': '', 'bottom_left': '', 'bottom_right': '',
            'horizontal': '', 'vertical': '', 'cross': '', 
            'top_cross': '', 'bottom_cross': '', 'left_cross': '', 'right_cross': ''
        },
        BorderStyle.ASCII: {
            'top_left': '+', 'top_right': '+', 'bottom_left': '+', 'bottom_right': '+',
            'horizontal': '-', 'vertical': '|', 'cross': '+',
            'top_cross': '+', 'bottom_cross': '+', 'left_cross': '+', 'right_cross': '+'
        },
        BorderStyle.ROUNDED: {
            'top_left': '╭', 'top_right': '╮', 'bottom_left': '╰', 'bottom_right': '╯',
            'horizontal': '─', 'vertical': '│', 'cross': '┼',
            'top_cross': '┬', 'bottom_cross': '┴', 'left_cross': '├', 'right_cross': '┤'
        }
    }
    
    def __init__(self, 
                 border_style: BorderStyle = BorderStyle.ROUNDED,
                 padding: int = 1):
        """Initialize table formatter."""
        self.border_style = border_style
        self.padding = padding
        self.border_chars = self.BORDER_CHARS.get(border_style, self.BORDER_CHARS[BorderStyle.ROUNDED])
    
    def format_cell(self, value: Any, column: Column, width: int) -> str:
        """Format a cell value according to column specifications."""
        # Apply custom formatter if provided
        if column.formatter:
            text = column.formatter(value)
        else:
            text = str(value) if value is not None else ""
        
        # Truncate if too long
        if len(text) > width:
            text = text[:width-3] + "..."
        
        # Apply alignment
        if column.alignment == Alignment.LEFT:
            text = text.ljust(width)
        elif column.alignment == Alignment.RIGHT:
            text = text.rjust(width)
        else:  # CENTER
            text = text.center(width)
        
        # Apply color and style
        if column.color or column.style:
            text = colorize(text, column.color, column.style)
        
        return text
    
    def calculate_widths(self, columns: list[Column], data: list[list[Any]]) -> list[int]:
        """Calculate optimal column widths."""
        widths = []
        
        for i, column in enumerate(columns):
            if column.width is not None:
                width = column.width
            else:
                width = len(column.header)
                for row in data:
                    if i < len(row):
                        cell_text = str(row[i]) if row[i] is not None else ""
                        width = max(width, len(cell_text))
                width = max(width, column.min_width)
                if column.max_width is not None:
                    width = min(width, column.max_width)
            
            widths.append(width)
        
        return widths


class Table:
    """
    Production-grade table with advanced formatting capabilities.
    
    Features:
    - Flexible column definitions
    - Multiple output formats
    - Sorting and filtering
    - Export capabilities
    """
    
    def __init__(self, 
                 columns: list[Union[str, Column]] = None,
                 formatter: TableFormatter = None,
                 title: str = ""):
        """Initialize table."""
        self.title = title
        self.formatter = formatter or TableFormatter()
        
        # Process columns
        self.columns = []
        if columns:
            for col in columns:
                if isinstance(col, str):
                    self.columns.append(Column(header=col))
                else:
                    self.columns.append(col)
        
        # Data storage
        self.rows = []
    
    def add_column(self, column: Union[str, Column]) -> 'Table':
        """Add a column to the table."""
        if isinstance(column, str):
            self.columns.append(Column(header=column))
        else:
            self.columns.append(column)
        return self
    
    def add_row(self, *values) -> 'Table':
        """Add a row to the table."""
        self.rows.append(list(values))
        return self
    
    def add_rows(self, rows: list[list[Any]]) -> 'Table':
        """Add multiple rows to the table."""
        self.rows.extend(rows)
        return self
    
    def to_string(self) -> str:
        """Convert table to string representation."""
        if not self.columns:
            return ""
        
        # Calculate column widths
        widths = self.formatter.calculate_widths(self.columns, self.rows)
        
        lines = []
        
        # Title
        if self.title:
            title_line = colorize(self.title, Colors.CYAN, Style.BOLD)
            lines.append(title_line)
            lines.append("")
        
        # Header row
        header_values = [col.header for col in self.columns]
        header_parts = []
        for i, (header, width) in enumerate(zip(header_values, widths)):
            formatted_header = colorize(header.ljust(width), Colors.BLUE, Style.BOLD)
            header_parts.append(formatted_header)
        lines.append(" | ".join(header_parts))
        
        # Separator
        separator_parts = ["-" * width for width in widths]
        lines.append("-|-".join(separator_parts))
        
        # Data rows
        for row in self.rows:
            row_parts = []
            for i, (value, column, width) in enumerate(zip(row, self.columns, widths)):
                if i >= len(row):
                    value = ""
                formatted_cell = self.formatter.format_cell(value, column, width)
                row_parts.append(formatted_cell)
            lines.append(" | ".join(row_parts))
        
        return '\n'.join(lines)
    
    def print(self, file: TextIO = None):
        """Print table to file or stdout."""
        output = file or sys.stdout
        output.write(self.to_string())
        output.write('\n')
        output.flush()


# Utility functions
def create_simple_table(headers: list[str], rows: list[list[Any]]) -> Table:
    """Create a simple table with basic formatting."""
    table = Table(headers)
    table.add_rows(rows)
    return table


def print_key_value_table(data: dict[str, Any], title: str = ""):
    """Print a key-value table."""
    table = Table([
        Column("Property", header_color=Colors.BLUE, header_style=Style.BOLD),
        Column("Value", header_color=Colors.GREEN, header_style=Style.BOLD)
    ], title=title)
    
    for key, value in data.items():
        table.add_row(key, value)
    
    table.print()
