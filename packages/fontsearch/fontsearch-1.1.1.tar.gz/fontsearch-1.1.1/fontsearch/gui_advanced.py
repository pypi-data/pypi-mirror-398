#!/usr/bin/env python3
"""
Advanced GUI font viewer with SVG rendering support.
This version includes the SVG rendering capabilities from the original list_fonts.py.
"""

import sys
import tkinter as tk
from tkinter import ttk, font as tkfont
from pathlib import Path
from typing import Optional
import logging
import warnings

from . import find_fonts, FontType, FontInfo

# Suppress fonttools warnings
logging.getLogger("fontTools").setLevel(logging.ERROR)

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
except ImportError:
    PIL_AVAILABLE = False

# Optionnel : pour le rendu des polices SVG
try:
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM
    import io
    import gzip
    SVG_RENDER_AVAILABLE = True
except ImportError:
    SVG_RENDER_AVAILABLE = False

# Optionnel : pour fonttools
try:
    from fontTools.ttLib import TTFont
    FONTTOOLS_AVAILABLE = True
except ImportError:
    FONTTOOLS_AVAILABLE = False


def render_svg_glyph(font_path: Path, text: str, size: int = 32):
    """Rend un glyphe SVG depuis une police OpenType-SVG avec CairoSVG prioritaire pour Noto."""
    if not SVG_RENDER_AVAILABLE or not FONTTOOLS_AVAILABLE or not text:
        return None

    # Essayer d'importer cairosvg
    try:
        import cairosvg
        CAIRO_AVAILABLE = True
    except ImportError:
        CAIRO_AVAILABLE = False

    try:
        font = TTFont(str(font_path), fontNumber=0)
        
        # Vérifier si la table SVG existe
        if 'SVG ' not in font:
            font.close()
            return None
            
        # Obtenir le glyphe ID pour le premier caractère
        cmap = font.getBestCmap()
        if not cmap:
            font.close()
            return None
            
        char_code = ord(text[0])
        if char_code not in cmap:
            font.close()
            return None
            
        glyph_name = cmap[char_code]
        glyph_id = font.getGlyphID(glyph_name)
        
        # Chercher le document SVG correspondant à ce glyphe
        svg_table = font['SVG ']
        
        svg_doc_data = None
        
        if hasattr(svg_table, 'docList'):
            for doc in svg_table.docList:
                if doc.startGlyphID <= glyph_id <= doc.endGlyphID:
                    if hasattr(doc, 'data'):
                        svg_doc_data = doc.data
                    elif hasattr(doc, 'svgDoc'):
                        svg_doc_data = doc.svgDoc
                    break
        
        font.close()
        
        if svg_doc_data is None:
            return None
            
        # Assurer que c'est des bytes
        if isinstance(svg_doc_data, str):
            svg_doc_data = svg_doc_data.encode('utf-8')

        # Décompresser si gzippé
        if svg_doc_data.startswith(b'\x1f\x8b'):
            svg_doc_data = gzip.decompress(svg_doc_data)
            
        svg_text = svg_doc_data.decode('utf-8')
        
        # Détecter le type de police pour appliquer le bon préprocessing
        is_noto_font = 'noto' in font_path.name.lower() or 'noto' in str(font_path).lower()
        is_emojione_font = 'emojione' in font_path.name.lower() or 'emojione' in str(font_path).lower()
        is_gilbert_font = 'gilbert' in font_path.name.lower() or 'gilbert' in str(font_path).lower()
        
        # PRIORITÉ CAIROSVG pour Noto et polices emoji
        if CAIRO_AVAILABLE:
            try:
                # Préprocesser le SVG selon le type de police
                if is_noto_font:
                    processed_svg = _preprocess_noto_svg(svg_text)
                elif is_emojione_font:
                    processed_svg = _preprocess_emojione_svg(svg_text)
                elif is_gilbert_font:
                    processed_svg = _preprocess_gilbert_svg(svg_text)
                else:
                    processed_svg = svg_text
                
                # Configuration optimisée pour CairoSVG
                png_data = cairosvg.svg2png(
                    bytestring=processed_svg.encode('utf-8'),
                    output_width=size,
                    output_height=size,
                    background_color=None
                )
                
                pil_image = Image.open(io.BytesIO(png_data))
                pil_image.load()
                
                # Vérifier la qualité du rendu CairoSVG
                pixels = list(pil_image.getdata())
                if pil_image.mode == 'RGBA':
                    non_transparent = [p for p in pixels if p[3] > 10]
                else:
                    non_transparent = [p for p in pixels if not (p[0] > 240 and p[1] > 240 and p[2] > 240)]
                
                coverage = len(non_transparent) / len(pixels) * 100
                
                if coverage > 0.1:
                    return _center_glyph_image(pil_image, size)
                
            except Exception:
                pass
        
        # Fallback sur svglib
        if not CAIRO_AVAILABLE or not is_noto_font:
            drawing = svg2rlg(io.BytesIO(svg_text.encode('utf-8')))
            
            if not drawing:
                return None
                
            # Obtenir les dimensions et rendre
            width = drawing.width
            height = drawing.height
            bounds = drawing.getBounds()

            if width <= 0 or height <= 0:
                if bounds:
                    width = bounds[2] - bounds[0]
                    height = bounds[3] - bounds[1]

            if height > 0:
                scale_factor = size / height
            else:
                scale_factor = 1.0

            if bounds:
                content_width = bounds[2] - bounds[0]
                content_height = bounds[3] - bounds[1]
            else:
                content_width = width
                content_height = height

            if content_height > 0:
                scale_factor = size / content_height
            else:
                scale_factor = 1.0

            final_width = int(content_width * scale_factor) if content_width > 0 else size
            final_height = int(content_height * scale_factor) if content_height > 0 else size

            max_dimension = size * 2
            
            if final_width > max_dimension or final_height > max_dimension:
                ratio = min(max_dimension / final_width, max_dimension / final_height)
                final_width = int(final_width * ratio)
                final_height = int(final_height * ratio)
                scale_factor *= ratio

            from reportlab.graphics.shapes import Drawing as RLDrawing, Group

            canvas = RLDrawing(final_width, final_height)
            g = Group()
            g.add(drawing)
            g.scale(scale_factor, scale_factor)
            if bounds:
                g.translate(-bounds[0], -bounds[1])
            canvas.add(g)

            png_data = renderPM.drawToString(canvas, fmt='PNG')
            pil_image = Image.open(io.BytesIO(png_data))
            pil_image.load()

            return _center_glyph_image(pil_image, size)

        return None

    except Exception:
        return None


def _center_glyph_image(img, target_size: int):
    """Centre un glyphe dans un canvas de taille donnée."""
    if img.size == (target_size, target_size):
        if img.mode == 'RGBA':
            bbox = img.getbbox()
            if bbox:
                content_width = bbox[2] - bbox[0]
                content_height = bbox[3] - bbox[1]
                
                if content_width < target_size * 0.8 or content_height < target_size * 0.8:
                    content_img = img.crop(bbox)
                    canvas = Image.new('RGBA', (target_size, target_size), (255, 255, 255, 0))
                    x = (target_size - content_width) // 2
                    y = (target_size - content_height) // 2
                    canvas.paste(content_img, (x, y), content_img)
                    return canvas
        return img
    
    if img.mode == 'RGBA':
        canvas = Image.new('RGBA', (target_size, target_size), (255, 255, 255, 0))
    else:
        canvas = Image.new('RGB', (target_size, target_size), (255, 255, 255))
    
    orig_width, orig_height = img.size
    
    if orig_width > target_size or orig_height > target_size:
        ratio = min(target_size / orig_width, target_size / orig_height)
        new_width = int(orig_width * ratio)
        new_height = int(orig_height * ratio)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        orig_width, orig_height = new_width, new_height
    
    x = (target_size - orig_width) // 2
    y = (target_size - orig_height) // 2
    
    if img.mode == 'RGBA':
        canvas.paste(img, (x, y), img)
    else:
        canvas.paste(img, (x, y))
    
    return canvas


def _preprocess_noto_svg(svg_text: str) -> str:
    """Préprocesse les SVG Noto pour corriger les problèmes de coordonnées."""
    import re
    
    transform_pattern = r'<g transform="translate\([^)]+\)\s*translate\([^)]+\)\s*scale\([^)]+\)">'
    
    if re.search(transform_pattern, svg_text):
        content_match = re.search(r'<g transform="[^"]*">(.*?)</g>\s*</svg>', svg_text, re.DOTALL)
        
        if content_match:
            inner_content = content_match.group(1)
            
            new_svg = f'''<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:ns1="http://www.w3.org/1999/xlink" 
     viewBox="0 0 128 128" width="128" height="128">
<g transform="scale(0.8) translate(10, 10)">
{inner_content}
</g>
</svg>'''
            return new_svg
    
    if 'viewBox=' not in svg_text:
        svg_text = svg_text.replace('<svg ', '<svg viewBox="0 0 128 128" ')
    
    return svg_text


def _preprocess_emojione_svg(svg_text: str) -> str:
    """Préprocesse les SVG EmojiOne pour corriger les problèmes de positionnement."""
    import re
    
    emojione_pattern = r'<g transform="translate\([^)]+\)\s*translate\([^)]+\)\s*scale\([^)]+\)">'
    
    if re.search(emojione_pattern, svg_text):
        content_match = re.search(r'<g transform="[^"]*">(.*?)</g>\s*</svg>', svg_text, re.DOTALL)
        
        if content_match:
            inner_content = content_match.group(1)
            
            new_svg = f'''<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
<g transform="scale(0.9) translate(16, 40)">
{inner_content}
</g>
</svg>'''
            return new_svg
    
    if 'viewBox=' not in svg_text:
        svg_text = svg_text.replace('<svg ', '<svg viewBox="0 0 64 64" ')
    
    return svg_text


def _preprocess_gilbert_svg(svg_text: str) -> str:
    """Préprocesse les SVG Gilbert Color pour corriger les problèmes de rendu."""
    import re
    
    if 'viewBox=' not in svg_text:
        svg_text = svg_text.replace('<svg ', '<svg viewBox="0 0 1000 1000" ')
    
    gradient_pattern = r'<defs>.*?</defs>'
    if re.search(gradient_pattern, svg_text, re.DOTALL):
        svg_text = re.sub(r'fill="url\(#[^)]+\)"', 'fill="#FF6B35"', svg_text)
        svg_text = re.sub(r'stroke="url\(#[^)]+\)"', 'stroke="#333333"', svg_text)
        svg_text = re.sub(gradient_pattern, '', svg_text, flags=re.DOTALL)
    
    return svg_text


class AdvancedFontViewerApp:
    """Interface graphique avancée pour visualiser les polices avec rendu SVG."""

    DEFAULT_TEXT = "AaBbCc 0123 àéïöü ÆŒß"
    ITEMS_PER_PAGE = 20
    DEBOUNCE_MS = 2000

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("FontSearch Advanced GUI - Visualiseur de polices avec SVG")
        self.root.geometry("1000x800")
        self.root.minsize(700, 500)

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
        self.enable_svg_rendering = tk.BooleanVar(value=True)

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
            text="Filtrer polices compatibles",
            variable=self.filter_glyphs,
            command=self._on_filter_change
        )
        glyph_check.pack(side=tk.LEFT, padx=(0, 15))

        # Checkbox pour rendu SVG
        svg_check = ttk.Checkbutton(
            options_row,
            text="Rendu SVG avancé",
            variable=self.enable_svg_rendering,
            command=self._on_svg_change
        )
        svg_check.pack(side=tk.LEFT, padx=(0, 15))

        if not (SVG_RENDER_AVAILABLE and FONTTOOLS_AVAILABLE):
            svg_check.configure(state="disabled")

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

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Scroll avec la molette
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))  # Linux scroll up
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))  # Linux scroll down

        # Barre de navigation
        nav_frame = ttk.Frame(main_frame)
        nav_frame.pack(fill=tk.X, pady=(10, 0))

        self.btn_first = ttk.Button(nav_frame, text="⏮ Début", command=self._go_first, width=10)
        self.btn_first.pack(side=tk.LEFT, padx=2)

        self.btn_prev = ttk.Button(nav_frame, text="◀ Précédent", command=self._go_prev, width=12)
        self.btn_prev.pack(side=tk.LEFT, padx=2)

        self.page_label = ttk.Label(nav_frame, text="", font=("Segoe UI", 10))
        self.page_label.pack(side=tk.LEFT, expand=True)

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

    def _on_text_change(self):
        """Appelé quand le texte change."""
        if self._debounce_timer is not None:
            self.root.after_cancel(self._debounce_timer)

        if not self.filter_glyphs.get():
            self.current_page = 0
            self._refresh_list()
        else:
            self._debounce_timer = self.root.after(self.DEBOUNCE_MS, self._do_filtered_refresh)

    def _do_filtered_refresh(self):
        """Effectue le rafraîchissement avec filtre."""
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

    def _on_svg_change(self):
        """Appelé quand l'option SVG change."""
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
        """Applique le filtre de glyphes."""
        if not self.filter_glyphs.get():
            self.filtered_fonts = self.font_names.copy()
            return

        text = self.sample_text.get()
        if not text:
            self.filtered_fonts = self.font_names.copy()
            return

        try:
            compatible_fonts = find_fonts(text=text)
            self.filtered_fonts = [font.name for font in compatible_fonts if font.name in self.font_names]
        except Exception:
            self.filtered_fonts = self.font_names.copy()

    def _total_pages(self):
        """Retourne le nombre total de pages."""
        return max(1, (len(self.filtered_fonts) + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE)

    def _go_first(self):
        self.current_page = 0
        self._refresh_list()

    def _go_prev(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh_list()

    def _go_next(self):
        if self.current_page < self._total_pages() - 1:
            self.current_page += 1
            self._refresh_list()

    def _go_last(self):
        self.current_page = self._total_pages() - 1
        self._refresh_list()

    def _refresh_list(self):
        """Rafraîchit la liste des polices affichées."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self._images.clear()

        text = self.sample_text.get() or self.DEFAULT_TEXT
        total = len(self.font_names)
        shown = len(self.filtered_fonts)
        total_pages = self._total_pages()

        # Info label
        svg_status = "✅ SVG" if self.enable_svg_rendering.get() and SVG_RENDER_AVAILABLE else "❌ SVG"
        if self.filter_glyphs.get():
            info_text = f"FontSearch Advanced ({svg_status}): {shown} / {total} polices compatibles"
        else:
            info_text = f"FontSearch Advanced ({svg_status}): {total} polices trouvées"
        self.info_label.config(text=info_text)

        # Pagination
        self.page_label.config(text=f"Page {self.current_page + 1} / {total_pages}")

        # Boutons
        self.btn_first.config(state="normal" if self.current_page > 0 else "disabled")
        self.btn_prev.config(state="normal" if self.current_page > 0 else "disabled")
        self.btn_next.config(state="normal" if self.current_page < total_pages - 1 else "disabled")
        self.btn_last.config(state="normal" if self.current_page < total_pages - 1 else "disabled")

        # Polices de la page courante
        start_idx = self.current_page * self.ITEMS_PER_PAGE
        end_idx = start_idx + self.ITEMS_PER_PAGE
        page_fonts = self.filtered_fonts[start_idx:end_idx]

        for i, font_name in enumerate(page_fonts):
            self._create_font_row(font_name, text, start_idx + i)

        self.canvas.yview_moveto(0)

    def _render_with_pil(self, font_path: Path, text: str, size: int = 32):
        """Rend le texte avec PIL et support SVG avancé."""
        if not PIL_AVAILABLE:
            return None

        try:
            is_gilbert_font = 'gilbert' in font_path.name.lower()
            
            if is_gilbert_font:
                return None

            # Essayer le rendu SVG si activé
            if self.enable_svg_rendering.get() and SVG_RENDER_AVAILABLE and FONTTOOLS_AVAILABLE:
                try:
                    font = TTFont(str(font_path), fontNumber=0)
                    is_svg_font = 'SVG ' in font
                    font.close()
                    
                    if is_svg_font:
                        svg_image = render_svg_glyph(font_path, text, size)
                        if svg_image:
                            return ImageTk.PhotoImage(svg_image)
                except Exception:
                    pass

            # Rendu PIL standard
            pil_font = ImageFont.truetype(str(font_path), size)
            bbox = pil_font.getbbox(text)
            if bbox is None:
                return None

            width = bbox[2] - bbox[0] + 20
            height = bbox[3] - bbox[1] + 10

            img = Image.new("RGBA", (width, height), (255, 255, 255, 255))
            draw = ImageDraw.Draw(img)

            # Features OpenType pour ligatures
            features = []
            
            if self.contextual_ligatures.get():
                features.extend(['calt', 'clig', 'liga'])
            else:
                features.extend(['-liga', '-clig', '-calt'])
            
            if self.historical_ligatures.get():
                features.extend(['hlig', 'dlig'])
            else:
                features.extend(['-hlig', '-dlig'])

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

            pixels = list(img.getdata())
            if all(p[0] >= 250 and p[1] >= 250 and p[2] >= 250 for p in pixels):
                return None

            return ImageTk.PhotoImage(img)
        except Exception:
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
            width=35
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

        # Fallback tkinter
        if not preview_created:
            try:
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


def main():
    """Point d'entrée principal pour la GUI avancée."""
    root = tk.Tk()
    app = AdvancedFontViewerApp(root)
    
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