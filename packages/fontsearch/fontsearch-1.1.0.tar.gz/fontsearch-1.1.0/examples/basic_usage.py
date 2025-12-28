#!/usr/bin/env python3
"""
Basic usage examples for FontSearch.
"""

import sys
from pathlib import Path

# Add parent directory to path for importing fontsearch
sys.path.insert(0, str(Path(__file__).parent.parent))

import fontsearch
from fontsearch import FontType


def main():
    """Demonstrate basic FontSearch usage."""
    print("🎨 FontSearch Basic Usage Examples\n")
    
    # Get all font names
    print("1. Getting all installed fonts:")
    fonts = fontsearch.get_fonts()
    print(f"   Found {len(fonts)} fonts")
    print(f"   First 5: {fonts[:5]}")
    print()
    
    # Get detailed font information
    print("2. Getting detailed font information:")
    font_info = fontsearch.find_fonts(max_results=5)
    for font in font_info:
        type_name = font.font_type.name if font.font_type else "Unknown"
        print(f"   {font.name} ({type_name})")
        print(f"     Path: {font.path}")
    print()
    
    # Filter by font type
    print("3. TrueType fonts only:")
    ttf_fonts = fontsearch.find_fonts(types=[FontType.TTF], max_results=5)
    for font in ttf_fonts:
        print(f"   {font.name}")
    print()
    
    # Random sampling
    print("4. Random font sample:")
    random_fonts = fontsearch.find_fonts(random_order=True, max_results=5)
    for font in random_fonts:
        print(f"   {font.name}")
    print()
    
    # Text support (if fonttools available)
    try:
        import fontTools
        print("5. Fonts supporting emojis:")
        emoji_fonts = fontsearch.find_fonts(text="🌷😀", max_results=3)
        if emoji_fonts:
            for font in emoji_fonts:
                print(f"   {font.name}")
        else:
            print("   No emoji fonts found")
    except ImportError:
        print("5. Text filtering requires fonttools (pip install fonttools)")
    
    print("\n✅ Examples completed!")


if __name__ == "__main__":
    main()