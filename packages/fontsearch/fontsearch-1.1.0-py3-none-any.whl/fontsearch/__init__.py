"""
FontSearch - A cross-platform font discovery and analysis library.

This module provides functions to discover, filter, and analyze fonts installed
on Windows, macOS, and Linux systems with minimal dependencies.
"""

from .core import (
    get_fonts,
    get_font_files,
    find_fonts,
    check_font_supports_text,
    FontInfo,
    FontType
)

# GUI components (optional - requires tkinter)
try:
    from .widget import FontPickerWidget
    _GUI_AVAILABLE = True
except ImportError:
    _GUI_AVAILABLE = False
    FontPickerWidget = None

__version__ = "1.1.0"
__author__ = "Michel Weinachter"
__email__ = "michel.weinachter@example.com"

__all__ = [
    "get_fonts",
    "get_font_files", 
    "find_fonts",
    "check_font_supports_text",
    "FontInfo",
    "FontType"
]

# Add GUI components if available
if _GUI_AVAILABLE:
    __all__.append("FontPickerWidget")