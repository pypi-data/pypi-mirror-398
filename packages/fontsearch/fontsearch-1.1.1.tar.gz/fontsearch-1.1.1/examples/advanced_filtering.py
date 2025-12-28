#!/usr/bin/env python3
"""
Advanced filtering examples for FontSearch.
"""

import sys
from pathlib import Path
from collections import Counter

# Add parent directory to path for importing fontsearch
sys.path.insert(0, str(Path(__file__).parent.parent))

import fontsearch
from fontsearch import FontType


def demonstrate_type_filtering():
    """Show font type filtering capabilities."""
    print("🔍 Font Type Filtering Examples\n")
    
    # Get all fonts
    all_fonts = fontsearch.find_fonts()
    print(f"Total fonts found: {len(all_fonts)}")
    
    # Filter by each type
    type_counts = {}
    for font_type in FontType:
        fonts = fontsearch.find_fonts(types=[font_type])
        type_counts[font_type.name] = len(fonts)
        print(f"   {font_type.name}: {len(fonts)} fonts")
    
    # Multiple types
    common_types = fontsearch.find_fonts(types=[FontType.TTF, FontType.OTF])
    print(f"   TTF + OTF: {len(common_types)} fonts")
    print()


def demonstrate_text_filtering():
    """Show text support filtering."""
    print("📝 Text Support Filtering Examples\n")
    
    try:
        import fontTools
        fonttools_available = True
    except ImportError:
        fonttools_available = False
        print("⚠️  fonttools not available - text filtering examples will be limited")
    
    if fonttools_available:
        # Basic character sets
        test_cases = [
            ("Basic ASCII", "ABCabc123"),
            ("Accented characters", "àáâãäåæçèéêë"),
            ("German", "äöü ß ÄÖÜ"),
            ("French", "àâäçéèêëïîôùûüÿ"),
            ("Spanish", "áéíñóúü ¡¿"),
            ("Symbols", "©®™€£¥"),
            ("Math", "±×÷≠≤≥∞"),
            ("Emojis", "🌷😀🎨"),
        ]
        
        for name, text in test_cases:
            fonts = fontsearch.find_fonts(text=text, max_results=5)
            print(f"   {name} ('{text}'): {len(fonts)} fonts")
            if fonts:
                print(f"     Examples: {', '.join(font.name for font in fonts[:3])}")
        print()
    else:
        print("   Install fonttools for text filtering: pip install fonttools\n")


def demonstrate_random_sampling():
    """Show random sampling capabilities."""
    print("🎲 Random Sampling Examples\n")
    
    # Different sample sizes
    for size in [3, 5, 10]:
        random_fonts = fontsearch.find_fonts(random_order=True, max_results=size)
        print(f"   Random {size} fonts:")
        for font in random_fonts:
            type_name = font.font_type.name if font.font_type else "Unknown"
            print(f"     {font.name} ({type_name})")
        print()


def demonstrate_combined_filtering():
    """Show combining multiple filters."""
    print("🔧 Combined Filtering Examples\n")
    
    try:
        import fontTools
        
        # Complex filtering combinations
        print("   1. TTF fonts supporting German characters:")
        german_ttf = fontsearch.find_fonts(
            text="äöü ß",
            types=[FontType.TTF],
            max_results=5
        )
        for font in german_ttf:
            print(f"      {font.name}")
        
        print(f"\n   2. Random OTF fonts (max 3):")
        random_otf = fontsearch.find_fonts(
            types=[FontType.OTF],
            random_order=True,
            max_results=3
        )
        for font in random_otf:
            print(f"      {font.name}")
        
        print(f"\n   3. Fonts supporting emojis (any type, max 3):")
        emoji_fonts = fontsearch.find_fonts(
            text="🌷😀",
            max_results=3
        )
        for font in emoji_fonts:
            type_name = font.font_type.name if font.font_type else "Unknown"
            print(f"      {font.name} ({type_name})")
        
    except ImportError:
        print("   Text filtering requires fonttools")
    
    print()


def analyze_font_distribution():
    """Analyze the distribution of fonts on the system."""
    print("📊 Font Distribution Analysis\n")
    
    # Get all fonts
    all_fonts = fontsearch.find_fonts()
    
    # Analyze by type
    type_counter = Counter()
    for font in all_fonts:
        type_name = font.font_type.name if font.font_type else "Unknown"
        type_counter[type_name] += 1
    
    print("   Font distribution by type:")
    for font_type, count in type_counter.most_common():
        percentage = (count / len(all_fonts)) * 100
        print(f"     {font_type}: {count} ({percentage:.1f}%)")
    
    # Analyze by name patterns
    print("\n   Common font families:")
    family_patterns = ["Arial", "Times", "Helvetica", "Calibri", "Segoe", "Noto"]
    
    for pattern in family_patterns:
        matching = [f for f in all_fonts if pattern.lower() in f.name.lower()]
        if matching:
            print(f"     {pattern}: {len(matching)} variants")
    
    print()


def find_interesting_fonts():
    """Find fonts with interesting characteristics."""
    print("🎯 Interesting Font Discovery\n")
    
    all_fonts = fontsearch.find_fonts()
    
    # Find fonts with interesting keywords
    categories = {
        "Monospace": ["mono", "consol", "courier", "code", "terminal"],
        "Decorative": ["decorative", "display", "fancy", "ornament"],
        "Script": ["script", "handwriting", "brush", "calligraphy"],
        "Condensed": ["condensed", "narrow", "compressed"],
        "Extended": ["extended", "expanded", "wide"],
    }
    
    for category, keywords in categories.items():
        matching_fonts = []
        for font in all_fonts:
            if any(keyword in font.name.lower() for keyword in keywords):
                matching_fonts.append(font)
        
        if matching_fonts:
            print(f"   {category} fonts ({len(matching_fonts)}):")
            for font in matching_fonts[:3]:  # Show first 3
                print(f"     {font.name}")
            if len(matching_fonts) > 3:
                print(f"     ... and {len(matching_fonts) - 3} more")
        print()


def main():
    """Run all advanced filtering examples."""
    print("🎨 FontSearch Advanced Filtering Examples")
    print("=" * 50)
    
    try:
        demonstrate_type_filtering()
        demonstrate_text_filtering()
        demonstrate_random_sampling()
        demonstrate_combined_filtering()
        analyze_font_distribution()
        find_interesting_fonts()
        
        print("✅ Advanced filtering examples completed!")
        
    except Exception as e:
        print(f"❌ Error in advanced filtering examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()