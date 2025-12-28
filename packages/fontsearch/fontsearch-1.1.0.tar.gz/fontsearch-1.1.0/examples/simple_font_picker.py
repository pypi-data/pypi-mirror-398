#!/usr/bin/env python3
"""
Example: Simple font picker dialog using FontSearch widget.

This shows how to create a simple font picker dialog that returns
the selected font name.
"""

import sys
import tkinter as tk
from tkinter import ttk
from pathlib import Path

# Add fontsearch to path for this example
sys.path.insert(0, str(Path(__file__).parent.parent))

from fontsearch.widget import FontPickerWidget


class FontPickerDialog:
    """Simple font picker dialog."""
    
    def __init__(self, parent=None, title="Select Font", initial_font=None):
        self.result = None
        self.selected_font = initial_font
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent) if parent else tk.Tk()
        self.dialog.title(title)
        self.dialog.geometry("600x500")
        self.dialog.resizable(True, True)
        
        # Make it modal if parent exists
        if parent:
            self.dialog.transient(parent)
            self.dialog.grab_set()
        
        self._setup_ui()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"600x500+{x}+{y}")
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # FontPicker widget (simplified)
        self.font_picker = FontPickerWidget(
            main_frame,
            width=580,
            height=400,
            show_language_selector=False,  # Simplified
            show_ligature_controls=False,  # Simplified
            show_filter_controls=True,
            show_navigation=True,
            on_font_selected=self._on_font_selected,
            on_font_double_click=self._on_font_double_clicked
        )
        self.font_picker.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Selected font display
        selection_frame = ttk.Frame(main_frame)
        selection_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(selection_frame, text="Selected:").pack(side=tk.LEFT)
        self.selection_label = ttk.Label(selection_frame, text=self.selected_font or "None", 
                                        font=("Arial", 10, "bold"), foreground="blue")
        self.selection_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="OK", command=self._ok).pack(side=tk.RIGHT)
        
        # Set initial sample text
        self.font_picker.set_sample_text("The quick brown fox jumps over the lazy dog")
    
    def _on_font_selected(self, font_name):
        """Called when a font is selected."""
        self.selected_font = font_name
        self.selection_label.config(text=font_name)
    
    def _on_font_double_clicked(self, font_name):
        """Called when a font is double-clicked - auto-accept."""
        self.selected_font = font_name
        self.selection_label.config(text=font_name)
        self._ok()
    
    def _ok(self):
        """Accept the selection."""
        self.result = self.selected_font
        self.dialog.destroy()
    
    def _cancel(self):
        """Cancel the selection."""
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and return the selected font."""
        self.dialog.wait_window()
        return self.result


def show_font_picker(parent=None, title="Select Font", initial_font=None):
    """
    Show a font picker dialog and return the selected font.
    
    Args:
        parent: Parent window (optional)
        title: Dialog title
        initial_font: Initially selected font
    
    Returns:
        Selected font name or None if cancelled
    """
    dialog = FontPickerDialog(parent, title, initial_font)
    return dialog.show()


class DemoApp:
    """Demo application showing the font picker dialog."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Font Picker Dialog Demo")
        self.root.geometry("400x300")
        
        self.current_font = "Arial"
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the demo UI."""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_frame, text="Font Picker Dialog Demo", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Current font display
        font_frame = ttk.Frame(main_frame)
        font_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(font_frame, text="Current Font:").pack(side=tk.LEFT)
        self.font_label = ttk.Label(font_frame, text=self.current_font, 
                                   font=("Arial", 12, "bold"), foreground="blue")
        self.font_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Sample text with current font
        self.sample_text = tk.Text(main_frame, height=8, wrap=tk.WORD)
        self.sample_text.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        sample_content = """This is sample text using the selected font.

The quick brown fox jumps over the lazy dog.
ABCDEFGHIJKLMNOPQRSTUVWXYZ
abcdefghijklmnopqrstuvwxyz
0123456789

Click "Choose Font" to select a different font!"""
        
        self.sample_text.insert(tk.END, sample_content)
        self._update_sample_font()
        
        # Button to open font picker
        ttk.Button(main_frame, text="Choose Font", command=self._choose_font).pack()
    
    def _choose_font(self):
        """Open the font picker dialog."""
        selected_font = show_font_picker(
            parent=self.root,
            title="Choose a Font",
            initial_font=self.current_font
        )
        
        if selected_font:
            self.current_font = selected_font
            self.font_label.config(text=selected_font)
            self._update_sample_font()
    
    def _update_sample_font(self):
        """Update the sample text font."""
        try:
            font_tuple = (self.current_font, 12)
            self.sample_text.configure(font=font_tuple)
        except tk.TclError:
            # Font not available, keep current
            pass


def main():
    """Run the demo application."""
    root = tk.Tk()
    app = DemoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()