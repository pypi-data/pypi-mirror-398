#!/usr/bin/env python3
"""
Example: Custom application with embedded FontSearch widget.

This demonstrates advanced integration with custom styling and callbacks.
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Add fontsearch to path for this example
sys.path.insert(0, str(Path(__file__).parent.parent))

from fontsearch.widget import FontPickerWidget


class DesignApp:
    """Design application with integrated font selection."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Design App - FontSearch Integration")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f0f0f0")
        
        # Application state
        self.selected_fonts = []
        self.font_history = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the application UI."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top toolbar
        self._setup_toolbar(main_frame)
        
        # Main content area
        content_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        content_paned.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Left: Font picker
        self._setup_font_picker(content_paned)
        
        # Right: Font collection and preview
        self._setup_font_collection(content_paned)
    
    def _setup_toolbar(self, parent):
        """Setup the application toolbar."""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # App title
        title_label = ttk.Label(toolbar, text="Font Design Studio", 
                               font=("Arial", 14, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # Toolbar buttons
        button_frame = ttk.Frame(toolbar)
        button_frame.pack(side=tk.RIGHT)
        
        ttk.Button(button_frame, text="Clear Collection", 
                  command=self._clear_collection).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Export List", 
                  command=self._export_fonts).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="About", 
                  command=self._show_about).pack(side=tk.LEFT)
    
    def _setup_font_picker(self, parent):
        """Setup the font picker panel."""
        picker_frame = ttk.LabelFrame(parent, text="Font Browser", padding=10)
        parent.add(picker_frame, weight=2)
        
        # Custom FontPicker with specific configuration
        self.font_picker = FontPickerWidget(
            picker_frame,
            width=500,
            height=500,
            show_language_selector=True,
            show_ligature_controls=True,
            show_filter_controls=True,
            show_navigation=True,
            on_font_selected=self._on_font_browsed,
            on_font_double_click=self._on_font_added
        )
        self.font_picker.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        instructions = ttk.Label(picker_frame, 
                                text="• Single-click to preview\n• Double-click to add to collection",
                                font=("Arial", 9), foreground="gray")
        instructions.pack(pady=(5, 0))
    
    def _setup_font_collection(self, parent):
        """Setup the font collection panel."""
        collection_frame = ttk.LabelFrame(parent, text="Font Collection", padding=10)
        parent.add(collection_frame, weight=1)
        
        # Collection list
        list_frame = ttk.Frame(collection_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Listbox with scrollbar
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        self.collection_listbox = tk.Listbox(list_container, font=("Arial", 10))
        collection_scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, 
                                           command=self.collection_listbox.yview)
        self.collection_listbox.configure(yscrollcommand=collection_scrollbar.set)
        
        self.collection_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        collection_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection
        self.collection_listbox.bind('<<ListboxSelect>>', self._on_collection_select)
        self.collection_listbox.bind('<Double-Button-1>', self._on_collection_double_click)
        
        # Collection controls
        controls_frame = ttk.Frame(collection_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(controls_frame, text="Add Current", 
                  command=self._add_current_font).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Remove", 
                  command=self._remove_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Clear All", 
                  command=self._clear_collection).pack(side=tk.LEFT)
        
        # Preview area
        preview_frame = ttk.LabelFrame(collection_frame, text="Preview", padding=5)
        preview_frame.pack(fill=tk.X)
        
        self.preview_text = tk.Text(preview_frame, height=6, wrap=tk.WORD, 
                                   font=("Arial", 12))
        self.preview_text.pack(fill=tk.X)
        
        # Default preview text
        self.preview_text.insert(tk.END, "The quick brown fox jumps over the lazy dog.\nABCDEFGHIJKLMNOPQRSTUVWXYZ\nabcdefghijklmnopqrstuvwxyz\n0123456789")
        
        # Status
        self.status_label = ttk.Label(collection_frame, text="Ready", 
                                     font=("Arial", 9), foreground="gray")
        self.status_label.pack(pady=(5, 0))
    
    def _on_font_browsed(self, font_name):
        """Called when a font is selected in the browser."""
        self._update_preview(font_name)
        self.status_label.config(text=f"Previewing: {font_name}")
    
    def _on_font_added(self, font_name):
        """Called when a font is double-clicked (add to collection)."""
        self._add_font_to_collection(font_name)
    
    def _on_collection_select(self, event):
        """Called when a font is selected in the collection."""
        selection = self.collection_listbox.curselection()
        if selection:
            font_name = self.collection_listbox.get(selection[0])
            self._update_preview(font_name)
            self.status_label.config(text=f"Collection: {font_name}")
    
    def _on_collection_double_click(self, event):
        """Called when a font is double-clicked in the collection."""
        selection = self.collection_listbox.curselection()
        if selection:
            font_name = self.collection_listbox.get(selection[0])
            # Show font details
            self._show_font_details(font_name)
    
    def _add_current_font(self):
        """Add the currently selected font to collection."""
        current_font = self.font_picker.get_selected_font()
        if current_font:
            self._add_font_to_collection(current_font)
        else:
            messagebox.showwarning("No Selection", "Please select a font first.")
    
    def _add_font_to_collection(self, font_name):
        """Add a font to the collection."""
        if font_name not in self.selected_fonts:
            self.selected_fonts.append(font_name)
            self.collection_listbox.insert(tk.END, font_name)
            self.font_history.append(font_name)
            self.status_label.config(text=f"Added: {font_name}")
        else:
            self.status_label.config(text=f"Already in collection: {font_name}")
    
    def _remove_selected(self):
        """Remove selected font from collection."""
        selection = self.collection_listbox.curselection()
        if selection:
            index = selection[0]
            font_name = self.collection_listbox.get(index)
            self.collection_listbox.delete(index)
            self.selected_fonts.remove(font_name)
            self.status_label.config(text=f"Removed: {font_name}")
    
    def _clear_collection(self):
        """Clear the font collection."""
        if self.selected_fonts:
            result = messagebox.askyesno("Clear Collection", 
                                       f"Remove all {len(self.selected_fonts)} fonts from collection?")
            if result:
                self.collection_listbox.delete(0, tk.END)
                self.selected_fonts.clear()
                self.status_label.config(text="Collection cleared")
    
    def _update_preview(self, font_name):
        """Update the preview with the selected font."""
        try:
            font_tuple = (font_name, 12)
            self.preview_text.configure(font=font_tuple)
        except tk.TclError:
            # Font not available for tkinter
            self.status_label.config(text=f"Preview not available for: {font_name}")
    
    def _show_font_details(self, font_name):
        """Show detailed information about a font."""
        # Get font path from FontSearch
        font_path = self.font_picker.font_files.get(font_name, "Unknown")
        
        details = f"""Font Details:

Name: {font_name}
Path: {font_path}
In Collection: Yes
Total Fonts Available: {self.font_picker.get_font_count()}
Collection Size: {len(self.selected_fonts)}"""
        
        messagebox.showinfo("Font Details", details)
    
    def _export_fonts(self):
        """Export the font collection list."""
        if not self.selected_fonts:
            messagebox.showwarning("Empty Collection", "No fonts to export.")
            return
        
        # Simple export to show concept
        export_text = "Font Collection Export\n" + "="*30 + "\n\n"
        for i, font_name in enumerate(self.selected_fonts, 1):
            font_path = self.font_picker.font_files.get(font_name, "Unknown")
            export_text += f"{i}. {font_name}\n   Path: {font_path}\n\n"
        
        # Show in a dialog (in real app, would save to file)
        export_window = tk.Toplevel(self.root)
        export_window.title("Font Collection Export")
        export_window.geometry("600x400")
        
        text_widget = tk.Text(export_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, export_text)
        text_widget.configure(state=tk.DISABLED)
        
        ttk.Button(export_window, text="Close", 
                  command=export_window.destroy).pack(pady=10)
    
    def _show_about(self):
        """Show about dialog."""
        about_text = """Design App with FontSearch Integration

This application demonstrates how to embed the FontSearch widget as a component in your own application.

Features:
• Browse and preview system fonts
• Build a collection of favorite fonts
• Multilingual interface support
• Advanced font filtering and search
• Ligature controls for typography

FontSearch Widget provides:
• Cross-platform font discovery
• Multiple GUI variants
• Internationalization (10 languages)
• Font selection callbacks
• Customizable appearance"""
        
        messagebox.showinfo("About", about_text)


def main():
    """Run the design application."""
    root = tk.Tk()
    app = DesignApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()