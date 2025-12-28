#!/usr/bin/env python3
"""
FontSearch - Command-line interface.

Copyright (C) 2024 Michel Weinachter

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import sys
import argparse
import logging
import warnings
from typing import List, Optional

from .core import find_fonts, FontType, FontInfo


def suppress_warnings():
    """Suppress fonttools and other non-critical warnings."""
    # Suppress fonttools warnings
    loggers_to_suppress = [
        "fontTools.ttLib.tables._p_o_s_t",
        "fontTools.ttLib.tables.DefaultTable", 
        "fontTools.ttLib",
    ]
    
    for logger_name in loggers_to_suppress:
        logging.getLogger(logger_name).setLevel(logging.ERROR)
    
    # Suppress general warnings that don't affect functionality
    warnings.filterwarnings("ignore", category=UserWarning, module="fontTools")
    warnings.filterwarnings("ignore", message=".*extra bytes.*")


# Apply warning suppression immediately
suppress_warnings()


def print_font_list(fonts: List[FontInfo], show_paths: bool = False) -> None:
    """Print a formatted list of fonts."""
    if not fonts:
        print("No fonts found matching the criteria.")
        return
    
    print(f"{'=' * 60}")
    print(f" {len(fonts)} fonts found")
    print(f"{'=' * 60}")
    
    for i, font in enumerate(fonts, 1):
        if show_paths:
            print(f"{i:4d}. {font.name}")
            print(f"      Path: {font.path}")
            if font.font_type:
                print(f"      Type: {font.font_type.name}")
        else:
            type_info = f" ({font.font_type.name})" if font.font_type else ""
            print(f"{i:4d}. {font.name}{type_info}")


def parse_font_types(type_str: str) -> List[FontType]:
    """Parse comma-separated font types."""
    types = []
    for t in type_str.upper().split(','):
        t = t.strip()
        try:
            types.append(FontType[t])
        except KeyError:
            valid_types = ', '.join([ft.name for ft in FontType])
            raise ValueError(f"Invalid font type '{t}'. Valid types: {valid_types}")
    return types


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="FontSearch - Discover and analyze system fonts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  fontsearch                           # List all fonts
  fontsearch --gui                     # Launch graphical interface
  fontsearch --gui-advanced            # Launch advanced GUI with SVG support
  fontsearch --gui-i18n                # Launch internationalized GUI (10 languages)
  fontsearch --text "🌷😀"             # Fonts supporting emojis
  fontsearch --types TTF,OTF           # Only TrueType and OpenType fonts
  fontsearch --random --max 10        # 10 random fonts
  fontsearch --text "äöü ß" --paths   # German fonts with file paths
        """
    )
    
    parser.add_argument(
        '--text', '-t',
        help='Filter fonts that support this text (requires fonttools)'
    )
    
    parser.add_argument(
        '--types',
        help='Comma-separated font types to include (TTF,OTF,TTC,WOFF,WOFF2)'
    )
    
    parser.add_argument(
        '--random', '-r',
        action='store_true',
        help='Return results in random order'
    )
    
    parser.add_argument(
        '--max', '-m',
        type=int,
        help='Maximum number of fonts to return'
    )
    
    parser.add_argument(
        '--paths', '-p',
        action='store_true',
        help='Show font file paths and types'
    )
    
    parser.add_argument(
        '--gui', '-g',
        action='store_true',
        help='Launch graphical user interface'
    )
    
    parser.add_argument(
        '--gui-advanced',
        action='store_true',
        help='Launch advanced GUI with SVG rendering support'
    )
    
    parser.add_argument(
        '--gui-i18n',
        action='store_true',
        help='Launch internationalized GUI (supports 10 languages)'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='FontSearch 1.1.0'
    )
    
    args = parser.parse_args()
    
    # Launch GUI if requested
    if args.gui:
        try:
            from .gui import main as gui_main
            selected_font = gui_main()
            if selected_font:
                print(selected_font)
            return
        except ImportError as e:
            print(f"Error: GUI not available - {e}", file=sys.stderr)
            print("GUI requires tkinter and optionally PIL for better rendering", file=sys.stderr)
            sys.exit(1)
    
    if args.gui_advanced:
        try:
            from .gui_advanced import main as gui_advanced_main
            selected_font = gui_advanced_main()
            if selected_font:
                print(selected_font)
            return
        except ImportError as e:
            print(f"Error: Advanced GUI not available - {e}", file=sys.stderr)
            print("Advanced GUI requires tkinter, PIL, and optionally fonttools/cairosvg for SVG rendering", file=sys.stderr)
            sys.exit(1)
    
    if args.gui_i18n:
        try:
            from .gui_i18n import main as gui_i18n_main
            selected_font = gui_i18n_main()
            if selected_font:
                print(selected_font)
            return
        except ImportError as e:
            print(f"Error: Internationalized GUI not available - {e}", file=sys.stderr)
            print("I18n GUI requires tkinter and optionally PIL for better rendering", file=sys.stderr)
            sys.exit(1)
    
    # Parse font types
    types = None
    if args.types:
        try:
            types = parse_font_types(args.types)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Check for fonttools if text filtering is requested
    if args.text:
        try:
            import fontTools
        except ImportError:
            print("Warning: fonttools not installed. Text filtering may not work properly.", 
                  file=sys.stderr)
            print("Install with: pip install fonttools", file=sys.stderr)
    
    try:
        # Find fonts
        fonts = find_fonts(
            text=args.text,
            types=types,
            random_order=args.random,
            max_results=args.max
        )
        
        # Print results
        print_font_list(fonts, show_paths=args.paths)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()