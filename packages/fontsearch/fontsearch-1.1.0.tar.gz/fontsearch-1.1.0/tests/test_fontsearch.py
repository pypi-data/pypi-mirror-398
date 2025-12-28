#!/usr/bin/env python3
"""
Simple tests for FontSearch module without external dependencies.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import fontsearch
from fontsearch import FontType, FontInfo


def test_basic_functionality():
    """Test basic FontSearch functionality."""
    print("🧪 Testing basic functionality...")
    
    # Test get_fonts
    fonts = fontsearch.get_fonts()
    assert isinstance(fonts, list), "get_fonts should return a list"
    assert len(fonts) > 0, "Should find at least some fonts"
    assert all(isinstance(name, str) for name in fonts), "All font names should be strings"
    print(f"✅ get_fonts: Found {len(fonts)} fonts")
    
    # Test get_font_files
    font_files = fontsearch.get_font_files()
    assert isinstance(font_files, dict), "get_font_files should return a dict"
    assert len(font_files) > 0, "Should find at least some font files"
    
    for name, path in list(font_files.items())[:5]:  # Test first 5
        assert isinstance(name, str), f"Font name should be string: {name}"
        assert isinstance(path, Path), f"Font path should be Path: {path}"
        assert path.exists(), f"Font file should exist: {path}"
    print(f"✅ get_font_files: Found {len(font_files)} font files")


def test_font_type_enum():
    """Test FontType enum."""
    print("🧪 Testing FontType enum...")
    
    assert FontType.TTF.value == ".ttf"
    assert FontType.OTF.value == ".otf"
    
    # Test from_extension
    assert FontType.from_extension(".ttf") == FontType.TTF
    assert FontType.from_extension(".TTF") == FontType.TTF
    assert FontType.from_extension(".xyz") is None
    print("✅ FontType enum works correctly")


def test_font_info():
    """Test FontInfo dataclass."""
    print("🧪 Testing FontInfo dataclass...")
    
    path = Path("test.ttf")
    font = FontInfo(name="Test Font", path=path)
    
    assert font.name == "Test Font"
    assert font.path == path
    assert font.font_type == FontType.TTF  # Auto-detected
    print("✅ FontInfo dataclass works correctly")


def test_find_fonts():
    """Test find_fonts function."""
    print("🧪 Testing find_fonts...")
    
    # Basic usage
    fonts = fontsearch.find_fonts(max_results=5)
    assert isinstance(fonts, list), "find_fonts should return a list"
    assert len(fonts) <= 5, "Should respect max_results"
    assert all(isinstance(font, FontInfo) for font in fonts), "Should return FontInfo objects"
    print(f"✅ find_fonts basic: Found {len(fonts)} fonts")
    
    # Test with type filtering
    ttf_fonts = fontsearch.find_fonts(types=[FontType.TTF], max_results=3)
    assert all(font.font_type == FontType.TTF for font in ttf_fonts if font.font_type)
    print(f"✅ find_fonts with TTF filter: Found {len(ttf_fonts)} fonts")
    
    # Test random order
    random_fonts = fontsearch.find_fonts(random_order=True, max_results=5)
    assert len(random_fonts) <= 5
    print(f"✅ find_fonts random order: Found {len(random_fonts)} fonts")


def test_text_filtering():
    """Test text filtering (if fonttools available)."""
    print("🧪 Testing text filtering...")
    
    try:
        import fontTools
        fonttools_available = True
    except ImportError:
        fonttools_available = False
        print("⚠️  fonttools not available - skipping text filtering tests")
        return
    
    # Test with basic ASCII
    ascii_fonts = fontsearch.find_fonts(text="ABC", max_results=3)
    assert len(ascii_fonts) > 0, "Should find fonts supporting ASCII"
    print(f"✅ Text filtering (ASCII): Found {len(ascii_fonts)} fonts")
    
    # Test with emoji (might not find any, that's OK)
    emoji_fonts = fontsearch.find_fonts(text="🌷", max_results=3)
    print(f"✅ Text filtering (emoji): Found {len(emoji_fonts)} fonts")


def test_cli_import():
    """Test that CLI module can be imported."""
    print("🧪 Testing CLI import...")
    
    try:
        from fontsearch import cli
        print("✅ CLI module imports successfully")
    except ImportError as e:
        print(f"❌ CLI import failed: {e}")
        raise


def run_all_tests():
    """Run all tests."""
    print("🚀 FontSearch Module Tests")
    print("=" * 50)
    
    tests = [
        test_basic_functionality,
        test_font_type_enum,
        test_font_info,
        test_find_fonts,
        test_text_filtering,
        test_cli_import
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
        print()
    
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)