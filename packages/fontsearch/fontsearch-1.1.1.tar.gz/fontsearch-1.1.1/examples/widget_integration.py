#!/usr/bin/env python3
"""
Example: Using FontSearch widget as a component in another application.

This demonstrates how to embed the FontSearch widget into your own
tkinter application as a reusable component.
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Add fontsearch to path for this example
sys.path.insert(0, str(Path(__file__).parent.parent))

from fontsearch.widget import FontPickerWidget


class TextEditorApp:
    """Example text editor application with integrated font picker."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Text Editor with FontSearch Integration")
        self.root.geometry("1200x800")
        
        self.current_font = "Arial"
        self.current_size = 12
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the application UI."""
        # Main paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel: Text editor
        self._setup_text_editor(main_paned)
        
        # Right panel: Font picker
        self._setup_font_picker(main_paned)
    
    def _setup_text_editor(self, parent):
        """Setup the text editor panel."""
        editor_frame = ttk.Frame(parent)
        parent.add(editor_frame, weight=2)
        
        # Toolbar
        toolbar = ttk.Frame(editor_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(toolbar, text="Font:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.font_label = ttk.Label(toolbar, text=self.current_font, 
                                   font=("Arial", 10, "bold"), foreground="blue")
        self.font_label.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(toolbar, text="Size:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.size_var = tk.StringVar(value=str(self.current_size))
        size_spinbox = ttk.Spinbox(toolbar, from_=8, to=72, width=5, 
                                  textvariable=self.size_var, command=self._update_text_font)
        size_spinbox.pack(side=tk.LEFT, padx=(0, 20))
        
        # Apply button
        ttk.Button(toolbar, text="Apply Font", command=self._apply_font).pack(side=tk.LEFT)
        
        # Text area
        text_frame = ttk.Frame(editor_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.text_area = tk.Text(text_frame, wrap=tk.WORD, font=(self.current_font, self.current_size))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=scrollbar.set)
        
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Sample text
        sample_text = """Welcome to the Text Editor with FontSearch Integration!

This is a demonstration of how to embed the FontSearch widget as a component in your own application.

Features:
• Select fonts from the FontSearch widget on the right
• Preview fonts with your own sample text
• Apply selected fonts to this text area
• Multilingual support (10 languages)
• Ligature controls for advanced typography

Try selecting different fonts from the FontSearch panel and see how they look in this text area!

The quick brown fox jumps over the lazy dog.
ABCDEFGHIJKLMNOPQRSTUVWXYZ
abcdefghijklmnopqrstuvwxyz
0123456789 !@#$%^&*()

Ligature examples:
fi fl ff ffi ffl (contextual)
st ct sp (historical)
"""
        self.text_area.insert(tk.END, sample_text)
    
    def _setup_font_picker(self, parent):
        """Setup the font picker panel."""
        picker_frame = ttk.Frame(parent)
        parent.add(picker_frame, weight=1)
        
        # Title
        title_label = ttk.Label(picker_frame, text="FontSearch Widget", 
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))
        
        # FontPicker widget
        self.font_picker = FontPickerWidget(
            picker_frame,
            width=400,
            height=600,
            show_language_selector=True,
            show_ligature_controls=True,
            show_filter_controls=True,
            show_navigation=True,
            on_font_selected=self._on_font_selected,
            on_font_double_click=self._on_font_double_clicked
        )
        self.font_picker.pack(fill=tk.BOTH, expand=True)
        
        # Status
        self.status_label = ttk.Label(picker_frame, text="Click on a font to select it")
        self.status_label.pack(pady=(5, 0))
    
    def _on_font_selected(self, font_name):
        """Called when a font is selected in the FontPicker."""
        self.current_font = font_name
        self.font_label.config(text=font_name)
        self.status_label.config(text=f"Selected: {font_name}")
    
    def _on_font_double_clicked(self, font_name):
        """Called when a font is double-clicked in the FontPicker."""
        self.current_font = font_name
        self.font_label.config(text=font_name)
        self._apply_font()
        self.status_label.config(text=f"Applied: {font_name}")
    
    def _update_text_font(self):
        """Update font size from spinbox."""
        try:
            self.current_size = int(self.size_var.get())
        except ValueError:
            self.current_size = 12
            self.size_var.set("12")
    
    def _apply_font(self):
        """Apply the selected font to the text area."""
        self._update_text_font()
        
        try:
            new_font = (self.current_font, self.current_size)
            self.text_area.configure(font=new_font)
            self.status_label.config(text=f"Applied: {self.current_font} {self.current_size}pt")
        except tk.TclError as e:
            messagebox.showerror("Font Error", f"Could not apply font '{self.current_font}': {e}")


def main():
    """Run the example application."""
    root = tk.Tk()
    app = TextEditorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()