#!/usr/bin/env python3
"""
FontSearch - Reusable GUI widget component for embedding in other applications.

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
import tkinter as tk
from tkinter import ttk, font as tkfont
from pathlib import Path
from typing import Optional, Union, Callable

from . import find_fonts, FontType, FontInfo
from .i18n import _, set_language, get_available_languages, get_current_language, get_language_name

# Forcer UTF-8 pour la sortie console Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        # Python < 3.7
        pass

# Optionnel : pour le rendu correct des polices
try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
    PIL_AVAILABLE = True
    PhotoImageType = ImageTk.PhotoImage
except ImportError:
    PIL_AVAILABLE = False
    PhotoImageType = None


class FontPickerWidget(ttk.Frame):
    """
    Reusable FontSearch widget that can be embedded in other applications.
    
    This widget provides a complete font selection interface that can be
    integrated into any tkinter application as a component.
    """

    ITEMS_PER_PAGE = 15
    DEBOUNCE_MS = 1500

    def __init__(self, parent, 
                 width: int = 800, 
                 height: int = 500,
                 show_language_selector: bool = True,
                 show_ligature_controls: bool = True,
                 show_filter_controls: bool = True,
                 show_navigation: bool = True,
                 on_font_selected: Optional[Callable[[str], None]] = None,
                 on_font_double_click: Optional[Callable[[str], None]] = None,
                 **kwargs):
        """
        Initialize the FontPicker widget.
        
        Args:
            parent: Parent tkinter widget
            width: Widget width in pixels
            height: Widget height in pixels
            show_language_selector: Show language selection dropdown
            show_ligature_controls: Show ligature control checkboxes
            show_filter_controls: Show font filtering controls
            show_navigation: Show pagination navigation
            on_font_selected: Callback when font is selected (single click)
            on_font_double_click: Callback when font is double-clicked
            **kwargs: Additional ttk.Frame arguments
        """
        super().__init__(parent, **kwargs)
        
        # Configuration
        self.width = width
        self.height = height
        self.show_language_selector = show_language_selector
        self.show_ligature_controls = show_ligature_controls
        self.show_filter_controls = show_filter_controls
        self.show_navigation = show_navigation
        
        # Callbacks
        self.on_font_selected = on_font_selected
        self.on_font_double_click = on_font_double_click
        
        # Font selection tracking
        self.selected_font = None
        
        # Données - utiliser FontSearch
        all_fonts = find_fonts()
        self.font_files = {info.name: info.path for info in all_fonts}
        self.font_names = sorted(self.font_files.keys())
        self.filtered_fonts = self.font_names.copy()
        
        # Variables d'interface
        self.current_page = 0
        self.total_pages = 0
        self._debounce_timer = None
        self._image_cache = {}  # Cache pour éviter le garbage collection
        
        # Variables de contrôle
        self.sample_text = tk.StringVar(value=_("sample_text_default"))
        self.filter_glyphs = tk.BooleanVar(value=False)
        self.contextual_ligatures = tk.BooleanVar(value=True)
        self.historical_ligatures = tk.BooleanVar(value=False)
        
        # Variable pour la langue
        self.current_language = tk.StringVar(value=get_current_language())
        self.current_language.trace('w', self._on_language_change)
        
        self._setup_ui()
        
        # Force initial display after UI is fully set up
        self.after(100, self._refresh_list)

    def _setup_ui(self):
        """Configure l'interface utilisateur."""
        self.configure(width=self.width, height=self.height)
        
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Controls row (optional)
        if (self.show_language_selector or self.show_ligature_controls or 
            self.show_filter_controls):
            self._setup_controls(main_frame)

        # Font list area
        self._setup_font_list(main_frame)

        # Navigation (optional)
        if self.show_navigation:
            self._setup_navigation(main_frame)

    def _setup_controls(self, parent):
        """Setup control widgets."""
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        # Sample text
        text_row = ttk.Frame(controls_frame)
        text_row.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(text_row, text=_("sample_text_label")).pack(side=tk.LEFT, padx=(0, 10))
        
        text_entry = ttk.Entry(text_row, textvariable=self.sample_text, width=30, font=("Segoe UI", 10))
        text_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 20))
        text_entry.bind("<KeyRelease>", lambda e: self._on_text_change())

        # Language selector (optional)
        if self.show_language_selector:
            language_combo = ttk.Combobox(text_row, textvariable=self.current_language, 
                                        width=12, state="readonly")
            available_langs = get_available_languages()
            language_combo['values'] = [f"{code} - {name}" for code, name in available_langs.items()]
            
            current_lang = get_current_language()
            current_display = f"{current_lang} - {get_language_name(current_lang)}"
            language_combo.set(current_display)
            language_combo.pack(side=tk.RIGHT)
            
            ttk.Label(text_row, text=_("language_label")).pack(side=tk.RIGHT, padx=(20, 5))

        # Options row (optional)
        if self.show_ligature_controls or self.show_filter_controls:
            options_row = ttk.Frame(controls_frame)
            options_row.pack(fill=tk.X)

            if self.show_filter_controls:
                glyph_check = ttk.Checkbutton(
                    options_row,
                    text=_("filter_compatible"),
                    variable=self.filter_glyphs,
                    command=self._on_filter_change
                )
                glyph_check.pack(side=tk.LEFT, padx=(0, 20))

            if self.show_ligature_controls:
                contextual_check = ttk.Checkbutton(
                    options_row,
                    text=_("contextual_ligatures"),
                    variable=self.contextual_ligatures,
                    command=self._on_ligature_change
                )
                contextual_check.pack(side=tk.LEFT, padx=(0, 15))

                historical_check = ttk.Checkbutton(
                    options_row,
                    text=_("historical_ligatures"),
                    variable=self.historical_ligatures,
                    command=self._on_ligature_change
                )
                historical_check.pack(side=tk.LEFT)

    def _setup_font_list(self, parent):
        """Setup the font list display area."""
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Canvas et scrollbar pour la liste
        self.canvas = tk.Canvas(list_frame, bg="white")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel globally for better responsiveness
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))  # Linux scroll up
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))   # Linux scroll down
        
        self.bind("<Configure>", self._on_widget_resize)

    def _setup_navigation(self, parent):
        """Setup navigation controls."""
        nav_frame = ttk.Frame(parent)
        nav_frame.pack(fill=tk.X)

        # Boutons de navigation
        ttk.Button(nav_frame, text=_("navigation_first"), command=self._first_page).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(nav_frame, text=_("navigation_previous"), command=self._prev_page).pack(side=tk.LEFT, padx=(0, 5))
        
        self.page_label = ttk.Label(nav_frame, text="")
        self.page_label.pack(side=tk.LEFT, padx=20)
        
        ttk.Button(nav_frame, text=_("navigation_next"), command=self._next_page).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(nav_frame, text=_("navigation_last"), command=self._last_page).pack(side=tk.RIGHT, padx=(5, 0))

    def _on_language_change(self, *args):
        """Called when language selection changes."""
        if not self.show_language_selector:
            return
            
        selection = self.current_language.get()
        if " - " in selection:
            lang_code = selection.split(" - ")[0]
            if set_language(lang_code):
                # Update sample text to new language default
                self.sample_text.set(_("sample_text_default"))
                # Refresh display if UI is ready
                if hasattr(self, 'scrollable_frame'):
                    self._refresh_list()

    def _on_text_change(self):
        """Appelé quand le texte d'aperçu change."""
        if self._debounce_timer is not None:
            self.after_cancel(self._debounce_timer)
        
        self._debounce_timer = self.after(self.DEBOUNCE_MS, self._refresh_list)

    def _on_filter_change(self):
        """Appelé quand le filtre de compatibilité change."""
        if self._debounce_timer is not None:
            self.after_cancel(self._debounce_timer)
        
        self._debounce_timer = self.after(self.DEBOUNCE_MS, self._refresh_list)

    def _on_ligature_change(self):
        """Appelé quand les options de ligatures changent."""
        if self._debounce_timer is not None:
            self.after_cancel(self._debounce_timer)
        
        self._debounce_timer = self.after(500, self._refresh_display)

    def _refresh_list(self):
        """Rafraîchit la liste des polices selon les filtres."""
        sample_text = self.sample_text.get().strip()
        
        if self.filter_glyphs.get() and sample_text:
            # Utiliser FontSearch pour filtrer par texte
            compatible_fonts = find_fonts(text=sample_text)
            self.filtered_fonts = [font.name for font in compatible_fonts if font.name in self.font_names]
        else:
            self.filtered_fonts = self.font_names.copy()
        
        # Calculer la pagination
        self.total_pages = max(1, (len(self.filtered_fonts) + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE)
        self.current_page = min(self.current_page, self.total_pages - 1)
        
        self._refresh_display()

    def _refresh_display(self):
        """Rafraîchit l'affichage de la page courante."""
        # Nettoyer le frame
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self._image_cache.clear()
        
        if not self.filtered_fonts:
            ttk.Label(self.scrollable_frame, text=_("no_fonts_message"), 
                     font=("Segoe UI", 10)).pack(pady=20)
            if hasattr(self, 'page_label'):
                self.page_label.config(text="")
            return
        
        # Calculer les indices pour la page courante
        start_idx = self.current_page * self.ITEMS_PER_PAGE
        end_idx = min(start_idx + self.ITEMS_PER_PAGE, len(self.filtered_fonts))
        
        # Afficher les polices de la page courante
        sample_text = self.sample_text.get() or _("sample_text_default")
        
        for i, font_name in enumerate(self.filtered_fonts[start_idx:end_idx]):
            self._create_font_row(font_name, sample_text, i)
        
        # Mettre à jour le label de pagination
        if hasattr(self, 'page_label'):
            if len(self.filtered_fonts) > self.ITEMS_PER_PAGE:
                page_text = _("page_info").format(current=self.current_page + 1, total=self.total_pages)
            else:
                page_text = _("fonts_found").format(count=len(self.filtered_fonts))
            
            self.page_label.config(text=page_text)
        
        # Remettre le scroll en haut
        self.canvas.yview_moveto(0)
        
        # Force canvas update
        self.canvas.update_idletasks()

    def _create_font_row(self, font_name: str, sample_text: str, row_index: int):
        """Crée une ligne pour une police."""
        font_path = self.font_files.get(font_name)
        
        # Frame pour cette police
        font_frame = ttk.Frame(self.scrollable_frame)
        font_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Add click handlers
        font_frame.bind("<Button-1>", lambda e: self._on_font_click(font_name))
        font_frame.bind("<Double-Button-1>", lambda e: self._on_font_double_click_event(font_name))
        
        # Nom de la police
        name_label = ttk.Label(font_frame, text=font_name, font=("Segoe UI", 9, "bold"))
        name_label.pack(anchor=tk.W)
        
        # Add click handlers to name label and make it look clickable
        name_label.bind("<Button-1>", lambda e: self._on_font_click(font_name))
        name_label.bind("<Double-Button-1>", lambda e: self._on_font_double_click_event(font_name))
        name_label.bind("<Enter>", lambda e: name_label.configure(foreground="blue", cursor="hand2"))
        name_label.bind("<Leave>", lambda e: name_label.configure(foreground="black", cursor=""))
        
        # Aperçu avec PIL si disponible
        if PIL_AVAILABLE and font_path:
            try:
                preview_image = self._render_with_pil(font_path, sample_text)
                if preview_image:
                    self._image_cache[f"{font_name}_{row_index}"] = preview_image
                    
                    preview_label = ttk.Label(font_frame, image=preview_image)
                    preview_label.pack(anchor=tk.W, pady=(2, 0))
                    
                    # Add click handlers to preview image
                    preview_label.bind("<Button-1>", lambda e: self._on_font_click(font_name))
                    preview_label.bind("<Double-Button-1>", lambda e: self._on_font_double_click_event(font_name))
                    preview_label.bind("<Enter>", lambda e: preview_label.configure(cursor="hand2"))
                    preview_label.bind("<Leave>", lambda e: preview_label.configure(cursor=""))
                else:
                    # Fallback vers aperçu système
                    self._create_system_preview(font_frame, font_name, sample_text)
            except Exception:
                # Fallback vers aperçu système
                self._create_system_preview(font_frame, font_name, sample_text)
        else:
            # Aperçu système
            self._create_system_preview(font_frame, font_name, sample_text)

    def _create_system_preview(self, parent_frame, font_name: str, sample_text: str):
        """Crée un aperçu système pour une police."""
        try:
            # Modifier le texte d'affichage selon les ligatures
            display_text = sample_text
            
            if self.show_ligature_controls:
                if self.contextual_ligatures.get():
                    if sample_text == _("sample_text_default"):
                        display_text = _("ligature_test_contextual") + " " + sample_text
                
                if self.historical_ligatures.get():
                    if sample_text == _("sample_text_default"):
                        display_text = _("ligature_test_historical") + " " + display_text
            
            # Créer le label avec la police système
            try:
                system_font = tkfont.Font(family=font_name, size=12)
                preview_label = tk.Label(parent_frame, text=display_text, font=system_font, 
                                       bg="white", anchor=tk.W, justify=tk.LEFT)
                preview_label.pack(fill=tk.X, pady=(2, 0))
                
                # Add click handlers to preview label and make it look clickable
                preview_label.bind("<Button-1>", lambda e: self._on_font_click(font_name))
                preview_label.bind("<Double-Button-1>", lambda e: self._on_font_double_click_event(font_name))
                preview_label.bind("<Enter>", lambda e: preview_label.configure(cursor="hand2", bg="#f0f0f0"))
                preview_label.bind("<Leave>", lambda e: preview_label.configure(cursor="", bg="white"))
                
            except tk.TclError:
                # Police non disponible pour tkinter
                fallback_label = ttk.Label(parent_frame, text=f"{display_text} (système)", 
                                         font=("Segoe UI", 10))
                fallback_label.pack(anchor=tk.W, pady=(2, 0))
                
                # Add click handlers to fallback label
                fallback_label.bind("<Button-1>", lambda e: self._on_font_click(font_name))
                fallback_label.bind("<Double-Button-1>", lambda e: self._on_font_double_click_event(font_name))
                fallback_label.bind("<Enter>", lambda e: fallback_label.configure(cursor="hand2"))
                fallback_label.bind("<Leave>", lambda e: fallback_label.configure(cursor=""))
                
        except Exception:
            # Fallback ultime
            error_text = _("error_font_load").format(error="Preview error") if hasattr(self, '_') else "Preview error"
            error_label = ttk.Label(parent_frame, text=error_text, foreground="red")
            error_label.pack(anchor=tk.W, pady=(2, 0))

    def _render_with_pil(self, font_path: Path, text: str, size: int = 24):
        """Rend le texte avec PIL."""
        if not PIL_AVAILABLE:
            return None
        
        try:
            # Créer une image temporaire pour mesurer
            temp_img = Image.new('RGB', (1, 1), 'white')
            temp_draw = ImageDraw.Draw(temp_img)
            
            # Charger la police
            try:
                pil_font = ImageFont.truetype(str(font_path), size)
            except (OSError, IOError):
                return None
            
            # Features OpenType pour ligatures
            features = []
            
            if self.show_ligature_controls:
                if self.contextual_ligatures.get():
                    features.extend(['calt', 'clig', 'liga'])
                else:
                    features.extend(['-liga', '-clig', '-calt'])
                
                if self.historical_ligatures.get():
                    features.extend(['hlig', 'dlig'])
                else:
                    features.extend(['-hlig', '-dlig'])
            
            # Mesurer le texte avec les features
            try:
                if hasattr(pil_font, 'getmask') and features:
                    bbox = temp_draw.textbbox((0, 0), text, font=pil_font, features=features)
                else:
                    bbox = temp_draw.textbbox((0, 0), text, font=pil_font)
                
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
            except Exception:
                try:
                    text_width, text_height = temp_draw.textsize(text, font=pil_font)
                except:
                    return None
            
            # Créer l'image finale avec marge
            margin = 8
            img_width = max(text_width + 2 * margin, 150)
            img_height = max(text_height + 2 * margin, 30)
            
            img = Image.new('RGB', (img_width, img_height), 'white')
            draw = ImageDraw.Draw(img)
            
            # Dessiner le texte avec les features
            try:
                if hasattr(pil_font, 'getmask') and features:
                    draw.text((margin, margin), text, font=pil_font, fill='black', features=features)
                else:
                    draw.text((margin, margin), text, font=pil_font, fill='black')
            except Exception:
                return None
            
            # Redimensionner si trop grand
            max_width = 400
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            return ImageTk.PhotoImage(img)
            
        except Exception:
            return None

    def _on_font_click(self, font_name: str):
        """Handle font selection (single click)."""
        self.selected_font = font_name
        
        if self.on_font_selected:
            self.on_font_selected(font_name)

    def _on_font_double_click_event(self, font_name: str):
        """Handle font double-click."""
        self.selected_font = font_name
        
        if self.on_font_double_click:
            self.on_font_double_click(font_name)

    def _on_mousewheel(self, event):
        """Gère le scroll avec la molette."""
        if hasattr(self, 'canvas'):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_widget_resize(self, event):
        """Gère le redimensionnement du widget."""
        if event.widget == self and hasattr(self, 'canvas'):
            # Update canvas window width
            canvas_width = self.canvas.winfo_width()
            if canvas_width > 1:
                self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def _first_page(self):
        """Va à la première page."""
        self.current_page = 0
        self._refresh_display()

    def _prev_page(self):
        """Va à la page précédente."""
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh_display()

    def _next_page(self):
        """Va à la page suivante."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._refresh_display()

    def _last_page(self):
        """Va à la dernière page."""
        self.current_page = self.total_pages - 1
        self._refresh_display()

    # Public API methods
    
    def get_selected_font(self) -> Optional[str]:
        """Get the currently selected font name."""
        return self.selected_font

    def set_sample_text(self, text: str):
        """Set the sample text for font preview."""
        self.sample_text.set(text)

    def get_sample_text(self) -> str:
        """Get the current sample text."""
        return self.sample_text.get()

    def set_language(self, language_code: str):
        """Set the interface language."""
        if self.show_language_selector:
            available_langs = get_available_languages()
            if language_code in available_langs:
                display_text = f"{language_code} - {available_langs[language_code]}"
                self.current_language.set(display_text)

    def refresh(self):
        """Refresh the font list."""
        self._refresh_list()

    def get_font_count(self) -> int:
        """Get the total number of fonts available."""
        return len(self.font_names)

    def get_filtered_font_count(self) -> int:
        """Get the number of fonts after filtering."""
        return len(self.filtered_fonts)