#!/usr/bin/env python3
"""
Example showing how to integrate FontSearch with a GUI application.
"""

import sys
from pathlib import Path

# Add parent directory to path for importing fontsearch
sys.path.insert(0, str(Path(__file__).parent.parent))

import fontsearch
from fontsearch import FontType


def demonstrate_gui_integration():
    """Show how to use FontSearch in a GUI context."""
    print("🖥️  FontSearch GUI Integration Examples\n")
    
    # Example 1: Get all fonts for a font selector
    print("1. Font selector population:")
    all_fonts = fontsearch.find_fonts()
    font_names = [font.name for font in all_fonts]
    print(f"   Available for font selector: {len(font_names)} fonts")
    print(f"   Sample: {font_names[:3]}")
    print()
    
    # Example 2: Filter fonts by type for different categories
    print("2. Font categorization:")
    ttf_fonts = fontsearch.find_fonts(types=[FontType.TTF])
    otf_fonts = fontsearch.find_fonts(types=[FontType.OTF])
    print(f"   TrueType fonts: {len(ttf_fonts)}")
    print(f"   OpenType fonts: {len(otf_fonts)}")
    print()
    
    # Example 3: Real-time text filtering (like search-as-you-type)
    print("3. Real-time text filtering:")
    search_terms = ["A", "AB", "ABC"]
    
    for term in search_terms:
        try:
            matching_fonts = fontsearch.find_fonts(text=term, max_results=5)
            print(f"   '{term}' → {len(matching_fonts)} fonts")
        except Exception:
            print(f"   '{term}' → text filtering requires fonttools")
    print()
    
    # Example 4: Random font suggestions
    print("4. Random font suggestions:")
    suggestions = fontsearch.find_fonts(random_order=True, max_results=3)
    print("   Random suggestions:")
    for font in suggestions:
        print(f"     {font.name} ({font.font_type.name if font.font_type else 'Unknown'})")
    print()
    
    # Example 5: Font information for tooltips/details
    print("5. Font details for tooltips:")
    sample_font = fontsearch.find_fonts(max_results=1)[0]
    print(f"   Font: {sample_font.name}")
    print(f"   Path: {sample_font.path}")
    print(f"   Type: {sample_font.font_type.name if sample_font.font_type else 'Unknown'}")
    print(f"   Exists: {sample_font.path.exists()}")


def create_simple_font_selector():
    """Create a simple tkinter font selector using FontSearch."""
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        print("❌ tkinter not available - skipping GUI example")
        return
    
    print("6. Simple font selector GUI:")
    
    # Create window
    root = tk.Tk()
    root.title("FontSearch - Simple Font Selector")
    root.geometry("400x300")
    
    # Get fonts
    fonts = fontsearch.find_fonts()
    font_names = [font.name for font in fonts]
    
    # Create UI
    frame = ttk.Frame(root, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(frame, text="Select a font:").pack(anchor=tk.W)
    
    # Font listbox
    listbox = tk.Listbox(frame)
    listbox.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
    
    # Populate listbox
    for name in font_names[:50]:  # Limit for demo
        listbox.insert(tk.END, name)
    
    # Preview label
    preview_var = tk.StringVar(value="Sample text: AaBbCc 123")
    preview_label = tk.Label(frame, textvariable=preview_var, font=("Arial", 14))
    preview_label.pack(pady=5)
    
    def on_select(event):
        selection = listbox.curselection()
        if selection:
            font_name = listbox.get(selection[0])
            try:
                preview_label.config(font=(font_name, 14))
                preview_var.set(f"Sample text: {font_name}")
            except tk.TclError:
                preview_var.set(f"Font not available: {font_name}")
    
    listbox.bind('<<ListboxSelect>>', on_select)
    
    ttk.Label(frame, text=f"Showing {min(50, len(font_names))} of {len(font_names)} fonts").pack()
    
    print(f"   Created font selector with {len(font_names)} fonts")
    print("   Close the window to continue...")
    
    # Don't actually show the window in automated examples
    # root.mainloop()
    root.destroy()


def main():
    """Run all GUI integration examples."""
    print("🎨 FontSearch GUI Integration Examples")
    print("=" * 50)
    
    try:
        demonstrate_gui_integration()
        create_simple_font_selector()
        
        print("\n✅ GUI integration examples completed!")
        print("\nFor a full GUI implementation, see:")
        print("   fontsearch --gui")
        print("   python -m fontsearch.gui")
        
    except Exception as e:
        print(f"❌ Error in GUI examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()