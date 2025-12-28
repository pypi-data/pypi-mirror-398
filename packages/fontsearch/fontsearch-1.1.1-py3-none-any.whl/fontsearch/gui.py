#!/usr/bin/env python3
"""
GUI font viewer using FontSearch as backend.
"""

import sys
import tkinter as tk
from tkinter import ttk, font as tkfont
from pathlib import Path
from typing import Optional, Union

from . import find_fonts, FontType, FontInfo
from .i18n import _, set_language, get_available_languages, get_current_language

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


class FontViewerApp:
    """Interface graphique pour visualiser les polices utilisant FontSearch."""

    DEFAULT_TEXT = "AaBbCc 0123 àéïöü ÆŒß"
    ITEMS_PER_PAGE = 20
    DEBOUNCE_MS = 2000

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("FontSearch GUI - Visualiseur de polices")
        self.root.geometry("900x700")
        self.root.minsize(600, 400)

        # Font selection tracking
        self.selected_font = None
        self.selection_mode = True  # Enable font selection mode

        # Données - utiliser FontSearch
        all_fonts = find_fonts()
        self.font_files = {info.name: info.path for info in all_fonts}
        self.font_names = sorted(self.font_files.keys())
        self.filtered_fonts = self.font_names.copy()

        # Pagination
        self.current_page = 0

        # Timer pour debounce
        self._debounce_timer = None

        # Cache pour les images PIL
        self._images = []

        # Variables
        self.sample_text = tk.StringVar(value=self.DEFAULT_TEXT)
        self.filter_glyphs = tk.BooleanVar(value=False)
        self.contextual_ligatures = tk.BooleanVar(value=True)
        self.historical_ligatures = tk.BooleanVar(value=False)

        self._setup_ui()
        
        # Force initial display after UI is fully set up
        self.root.after(100, self._refresh_list)

    def _setup_ui(self):
        """Configure l'interface utilisateur."""
        # Style
        style = ttk.Style()
        style.configure("TFrame", background="#f5f5f5")
        style.configure("Header.TFrame", background="#ffffff")

        # Frame principale
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header : champ de texte + checkboxes
        header_frame = ttk.Frame(main_frame, style="Header.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Première ligne : texte d'aperçu
        text_row = ttk.Frame(header_frame)
        text_row.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(text_row, text="Texte d'aperçu :").pack(side=tk.LEFT, padx=(0, 10))

        text_entry = ttk.Entry(text_row, textvariable=self.sample_text, width=40, font=("Segoe UI", 12))
        text_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 20))
        text_entry.bind("<KeyRelease>", lambda e: self._on_text_change())

        # Deuxième ligne : options et filtres
        options_row = ttk.Frame(header_frame)
        options_row.pack(fill=tk.X)

        # Checkbox pour filtrer par glyphes
        glyph_check = ttk.Checkbutton(
            options_row,
            text="Filtrer polices compatibles (FontSearch)",
            variable=self.filter_glyphs,
            command=self._on_filter_change
        )
        glyph_check.pack(side=tk.LEFT, padx=(0, 20))

        # Checkbox pour ligatures contextuelles
        contextual_check = ttk.Checkbutton(
            options_row,
            text="Ligatures contextuelles",
            variable=self.contextual_ligatures,
            command=self._on_ligature_change
        )
        contextual_check.pack(side=tk.LEFT, padx=(0, 15))

        # Checkbox pour ligatures historiques
        historical_check = ttk.Checkbutton(
            options_row,
            text="Ligatures historiques",
            variable=self.historical_ligatures,
            command=self._on_ligature_change
        )
        historical_check.pack(side=tk.LEFT)

        # Info label
        self.info_label = ttk.Label(main_frame, text="", font=("Segoe UI", 10))
        self.info_label.pack(fill=tk.X, pady=(0, 5))

        # Zone scrollable pour les polices
        container = ttk.Frame(main_frame)
        container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(container, bg="#ffffff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.canvas.yview)

        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Ajuster la largeur du frame interne
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Scroll avec la molette
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))

        # Barre de navigation (pagination)
        nav_frame = ttk.Frame(main_frame)
        nav_frame.pack(fill=tk.X, pady=(10, 0))

        self.btn_first = ttk.Button(nav_frame, text="⏮ Début", command=self._go_first, width=10)
        self.btn_first.pack(side=tk.LEFT, padx=2)

        self.btn_prev = ttk.Button(nav_frame, text="◀ Précédent", command=self._go_prev, width=12)
        self.btn_prev.pack(side=tk.LEFT, padx=2)

        self.page_label = ttk.Label(nav_frame, text="", font=("Segoe UI", 10))
        self.page_label.pack(side=tk.LEFT, expand=True)

        # Ordre corrigé : Fin à droite, puis Suivant
        self.btn_last = ttk.Button(nav_frame, text="Fin ⏭", command=self._go_last, width=10)
        self.btn_last.pack(side=tk.RIGHT, padx=2)

        self.btn_next = ttk.Button(nav_frame, text="Suivant ▶", command=self._go_next, width=12)
        self.btn_next.pack(side=tk.RIGHT, padx=2)

    def _on_canvas_configure(self, event):
        """Ajuste la largeur du contenu scrollable."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        """Gère le scroll molette."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_font_selected(self, font_name: str):
        """Handle font selection and exit gracefully."""
        self.selected_font = font_name
        
        # Exit immediately without showing confirmation dialog for CLI usage
        self._exit_with_selection()

    def _exit_with_selection(self):
        """Exit the application with the selected font."""
        self.root.quit()  # Exit the mainloop
        self.root.destroy()  # Destroy the window

    def get_selected_font(self) -> Optional[str]:
        """Get the selected font name."""
        return self.selected_font

    def _on_text_change(self):
        """Appelé quand le texte change - avec temporisation."""
        if self._debounce_timer is not None:
            self.root.after_cancel(self._debounce_timer)

        if not self.filter_glyphs.get():
            self.current_page = 0
            self._refresh_list()
        else:
            self._debounce_timer = self.root.after(self.DEBOUNCE_MS, self._do_filtered_refresh)

    def _do_filtered_refresh(self):
        """Effectue le rafraîchissement avec filtre après la temporisation."""
        self._debounce_timer = None
        self._apply_filter()
        self.current_page = 0
        self._refresh_list()

    def _on_ligature_change(self):
        """Appelé quand les options de ligatures changent."""
        if self._debounce_timer is not None:
            self.root.after_cancel(self._debounce_timer)
            self._debounce_timer = None

        self.current_page = 0
        self._refresh_list()

    def _on_filter_change(self):
        """Appelé quand la checkbox change."""
        if self._debounce_timer is not None:
            self.root.after_cancel(self._debounce_timer)
            self._debounce_timer = None

        self._apply_filter()
        self.current_page = 0
        self._refresh_list()

    def _apply_filter(self):
        """Applique le filtre de glyphes en utilisant FontSearch."""
        if not self.filter_glyphs.get():
            self.filtered_fonts = self.font_names.copy()
            return

        text = self.sample_text.get()
        if not text:
            self.filtered_fonts = self.font_names.copy()
            return

        try:
            # Utiliser FontSearch pour le filtrage
            compatible_fonts = find_fonts(text=text)
            self.filtered_fonts = [font.name for font in compatible_fonts if font.name in self.font_names]
        except Exception as e:
            print(f"Erreur FontSearch: {e}")
            self.filtered_fonts = self.font_names.copy()

    def _total_pages(self):
        """Retourne le nombre total de pages."""
        return max(1, (len(self.filtered_fonts) + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE)

    def _go_first(self):
        """Va à la première page."""
        self.current_page = 0
        self._refresh_list()

    def _go_prev(self):
        """Va à la page précédente."""
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh_list()

    def _go_next(self):
        """Va à la page suivante."""
        if self.current_page < self._total_pages() - 1:
            self.current_page += 1
            self._refresh_list()

    def _go_last(self):
        """Va à la dernière page."""
        self.current_page = self._total_pages() - 1
        self._refresh_list()

    def _refresh_list(self):
        """Rafraîchit la liste des polices affichées."""
        # Supprimer les anciens widgets et vider le cache d'images
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self._images.clear()

        text = self.sample_text.get() or self.DEFAULT_TEXT
        total = len(self.font_names)
        shown = len(self.filtered_fonts)
        total_pages = self._total_pages()

        # Info label
        if self.filter_glyphs.get():
            info_text = f"FontSearch: {shown} / {total} polices compatibles avec le texte"
        else:
            info_text = f"FontSearch: {total} polices trouvées"
        self.info_label.config(text=info_text)

        # Pagination label
        self.page_label.config(text=f"Page {self.current_page + 1} / {total_pages}")

        # Activer/désactiver les boutons
        self.btn_first.config(state="normal" if self.current_page > 0 else "disabled")
        self.btn_prev.config(state="normal" if self.current_page > 0 else "disabled")
        self.btn_next.config(state="normal" if self.current_page < total_pages - 1 else "disabled")
        self.btn_last.config(state="normal" if self.current_page < total_pages - 1 else "disabled")

        # Calculer les indices pour la page courante
        start_idx = self.current_page * self.ITEMS_PER_PAGE
        end_idx = start_idx + self.ITEMS_PER_PAGE
        page_fonts = self.filtered_fonts[start_idx:end_idx]

        # Créer les entrées pour la page courante
        for i, font_name in enumerate(page_fonts):
            self._create_font_row(font_name, text, start_idx + i)

        # Remettre le scroll en haut
        self.canvas.yview_moveto(0)

    def _render_with_pil(self, font_path: Path, text: str, size: int = 32):
        """Rend le texte avec PIL."""
        if not PIL_AVAILABLE:
            return None

        try:
            # Vérifier si c'est Gilbert Color
            is_gilbert_font = 'gilbert' in font_path.name.lower()
            
            if is_gilbert_font:
                return None  # Utiliser le fallback avec message

            # Charger la police standard avec PIL
            pil_font = ImageFont.truetype(str(font_path), size)

            # Calculer la taille nécessaire
            bbox = pil_font.getbbox(text)
            if bbox is None:
                return None

            width = bbox[2] - bbox[0] + 20
            height = bbox[3] - bbox[1] + 10

            # Créer l'image avec fond blanc
            img = Image.new("RGBA", (width, height), (255, 255, 255, 255))
            draw = ImageDraw.Draw(img)

            # Préparer les features OpenType pour les ligatures
            features = []
            
            if self.contextual_ligatures.get():
                features.extend(['calt', 'clig', 'liga'])
            else:
                features.extend(['-liga', '-clig', '-calt'])
            
            if self.historical_ligatures.get():
                features.extend(['hlig', 'dlig'])
            else:
                features.extend(['-hlig', '-dlig'])

            # Dessiner le texte
            try:
                draw.text(
                    (-bbox[0] + 10, -bbox[1] + 5), 
                    text, 
                    font=pil_font, 
                    fill=(0, 0, 0, 255),
                    embedded_color=True,
                    features=features if features else None
                )
            except TypeError:
                draw.text(
                    (-bbox[0] + 10, -bbox[1] + 5), 
                    text, 
                    font=pil_font, 
                    fill=(0, 0, 0, 255),
                    embedded_color=True
                )

            # Vérifier si l'image est vide
            pixels = list(img.getdata())
            if all(p[0] >= 250 and p[1] >= 250 and p[2] >= 250 for p in pixels):
                return None

            return ImageTk.PhotoImage(img)
        except Exception as e:
            return None

    def _create_font_row(self, font_name: str, sample_text: str, index: int):
        """Crée une ligne pour afficher une police."""
        bg_color = "#ffffff" if index % 2 == 0 else "#f8f8f8"

        row_frame = tk.Frame(self.scrollable_frame, bg=bg_color, padx=10, pady=8)
        row_frame.pack(fill=tk.X, padx=2, pady=1)
        
        # Add click handler to row frame
        row_frame.bind("<Button-1>", lambda e: self._on_font_selected(font_name))

        # Nom de la police
        name_label = tk.Label(
            row_frame,
            text=font_name,
            font=("Segoe UI", 10),
            bg=bg_color,
            fg="#666666",
            anchor="w",
            width=30
        )
        name_label.pack(side=tk.LEFT)
        
        # Add click handler to name label and make it look clickable
        name_label.bind("<Button-1>", lambda e: self._on_font_selected(font_name))
        name_label.bind("<Enter>", lambda e: name_label.configure(fg="blue", cursor="hand2"))
        name_label.bind("<Leave>", lambda e: name_label.configure(fg="#666666", cursor=""))

        # Aperçu avec la police
        font_path = self.font_files.get(font_name)
        preview_created = False

        if PIL_AVAILABLE and font_path:
            photo = self._render_with_pil(font_path, sample_text)
            if photo:
                self._images.append(photo)
                preview_label = tk.Label(row_frame, image=photo, bg=bg_color, anchor="w")
                preview_label.pack(side=tk.LEFT, padx=(20, 0))
                preview_created = True
                
                # Add click handler to preview image
                preview_label.bind("<Button-1>", lambda e: self._on_font_selected(font_name))
                preview_label.bind("<Enter>", lambda e: preview_label.configure(cursor="hand2"))
                preview_label.bind("<Leave>", lambda e: preview_label.configure(cursor=""))

        # Fallback sur tkinter si PIL n'a pas fonctionné
        if not preview_created:
            try:
                # Vérifier si c'est Gilbert Color
                is_gilbert_font = 'gilbert' in font_name.lower()
                
                if is_gilbert_font:
                    error_label = tk.Label(
                        row_frame,
                        text="(Police SVG complexe - rendu limité)",
                        font=("Segoe UI", 9, "italic"),
                        bg=bg_color,
                        fg="#ff8800"
                    )
                    error_label.pack(side=tk.LEFT, padx=(20, 0))
                    
                    # Add click handler to error label
                    error_label.bind("<Button-1>", lambda e: self._on_font_selected(font_name))
                    error_label.bind("<Enter>", lambda e: error_label.configure(cursor="hand2"))
                    error_label.bind("<Leave>", lambda e: error_label.configure(cursor=""))
                    return

                # Créer la police tkinter
                preview_font = tkfont.Font(family=font_name, size=18)
                
                display_text = sample_text
                
                if self.contextual_ligatures.get():
                    if sample_text == self.DEFAULT_TEXT:
                        display_text = "fi fl ff ffi ffl " + sample_text
                
                if self.historical_ligatures.get():
                    if sample_text == self.DEFAULT_TEXT:
                        display_text = "st ct sp " + display_text
                
                preview_label = tk.Label(
                    row_frame,
                    text=display_text,
                    font=preview_font,
                    bg=bg_color,
                    anchor="w"
                )
                preview_label.pack(side=tk.LEFT, padx=(20, 0))
                
                # Add click handler to preview label
                preview_label.bind("<Button-1>", lambda e: self._on_font_selected(font_name))
                preview_label.bind("<Enter>", lambda e: preview_label.configure(cursor="hand2", bg="#f0f0f0"))
                preview_label.bind("<Leave>", lambda e: preview_label.configure(cursor="", bg=bg_color))

                # Indicateur de fallback
                if PIL_AVAILABLE and font_path:
                    hint_text = "(aperçu système"
                    if self.contextual_ligatures.get() or self.historical_ligatures.get():
                        hint_text += ", ligatures limitées"
                    hint_text += ")"
                    
                    hint_label = tk.Label(
                        row_frame,
                        text=hint_text,
                        font=("Segoe UI", 8),
                        bg=bg_color,
                        fg="#999999",
                        anchor="w"
                    )
                    hint_label.pack(side=tk.LEFT, padx=(10, 0))
            except Exception:
                error_label = tk.Label(
                    row_frame,
                    text="(Police compatible mais aperçu indisponible)",
                    font=("Segoe UI", 9, "italic"),
                    bg=bg_color,
                    fg="#ff8800"
                )
                error_label.pack(side=tk.LEFT, padx=(20, 0))
                
                # Add click handler to error label
                error_label.bind("<Button-1>", lambda e: self._on_font_selected(font_name))
                error_label.bind("<Enter>", lambda e: error_label.configure(cursor="hand2"))
                error_label.bind("<Leave>", lambda e: error_label.configure(cursor=""))


def main():
    """Point d'entrée principal pour la GUI."""
    root = tk.Tk()
    app = FontViewerApp(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        pass
    
    # Return the selected font name (if any)
    selected_font = app.get_selected_font()
    return selected_font


if __name__ == "__main__":
    main()