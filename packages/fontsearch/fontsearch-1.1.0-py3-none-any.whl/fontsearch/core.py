#!/usr/bin/env python3
"""
FontSearch - Core font discovery and filtering functions.
Minimal dependencies - only uses standard library.

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

import subprocess
import sys
import re
import random as _random
import logging
import warnings
from pathlib import Path
from typing import Optional, List, Dict, Set
from dataclasses import dataclass
from enum import Enum

# Suppress fonttools warnings about font file inconsistencies
logging.getLogger("fontTools.ttLib.tables._p_o_s_t").setLevel(logging.ERROR)
logging.getLogger("fontTools.ttLib.tables.DefaultTable").setLevel(logging.ERROR)
logging.getLogger("fontTools.ttLib").setLevel(logging.ERROR)


def _suppress_fonttools_warnings():
    """Suppress common fonttools warnings that don't affect functionality."""
    # Suppress specific fonttools loggers
    loggers_to_suppress = [
        "fontTools.ttLib.tables._p_o_s_t",
        "fontTools.ttLib.tables.DefaultTable", 
        "fontTools.ttLib.tables._c_m_a_p",
        "fontTools.ttLib.tables._g_l_y_f",
        "fontTools.ttLib.tables._h_e_a_d",
        "fontTools.ttLib.tables._h_h_e_a",
        "fontTools.ttLib.tables._m_a_x_p",
        "fontTools.ttLib.tables._n_a_m_e",
        "fontTools.ttLib.tables._O_S_2f_2",
        "fontTools.ttLib",
        "fontTools.subset",
        "fontTools.varLib"
    ]
    
    for logger_name in loggers_to_suppress:
        logging.getLogger(logger_name).setLevel(logging.ERROR)


# Apply warning suppression
_suppress_fonttools_warnings()


class FontType(Enum):
    """Font file types."""
    TTF = ".ttf"
    OTF = ".otf"
    TTC = ".ttc"
    WOFF = ".woff"
    WOFF2 = ".woff2"
    
    @classmethod
    def from_extension(cls, ext: str) -> Optional['FontType']:
        """Get FontType from file extension."""
        ext_lower = ext.lower()
        for font_type in cls:
            if font_type.value == ext_lower:
                return font_type
        return None


@dataclass
class FontInfo:
    """Information about a font."""
    name: str
    path: Path
    font_type: Optional[FontType] = None
    
    def __post_init__(self):
        if self.font_type is None and self.path:
            self.font_type = FontType.from_extension(self.path.suffix)


def normalize_font_name(name: str) -> str:
    """Normalise un nom de police pour la déduplication."""
    n = name.lower()
    # Supprimer les suffixes de poids/style courants
    for suffix in ['-regular', ' regular', '-bold', ' bold', '-light', ' light',
                   '-medium', ' medium', '-semibold', ' semibold', '-italic', ' italic',
                   '-variablefont_wght', ' variablefont_wght', '-svginot', ' svginot']:
        if n.endswith(suffix):
            n = n[:-len(suffix)]
            break
    # Supprimer espaces, tirets, underscores
    return re.sub(r'[\s\-_]', '', n)


def deduplicate_fonts(fonts: Dict[str, Path]) -> Dict[str, Path]:
    """Déduplique les polices par nom normalisé et par fichier, en privilégiant les noms lisibles."""
    # Étape 1 : Dédupliquer par chemin de fichier (privilégier les noms avec espaces)
    by_path = {}  # path -> (display_name, path)
    for name, path in fonts.items():
        resolved = path.resolve()
        if resolved not in by_path:
            by_path[resolved] = (name, path)
        else:
            existing_name = by_path[resolved][0]
            # Privilégier les noms avec espaces (plus lisibles) ou Regular
            should_replace = (
                (' ' in name and ' ' not in existing_name) or
                ('regular' in name.lower() and 'regular' not in existing_name.lower()) or
                (len(name.split()) > len(existing_name.split()))
            )
            if should_replace:
                by_path[resolved] = (name, path)

    # Étape 2 : Grouper par famille en préservant les noms lisibles
    families = {}  # base_name -> [(display_name, path, score)]
    
    for display_name, path in by_path.values():
        # Extraire le nom de base (sans style)
        base_name = display_name
        
        # Supprimer les styles à la fin
        style_patterns = [
            r'\s+(Bold|Italic|Light|Medium|Semibold|Black|Thin|Regular)(\s+Italic)?$',
            r'-(Bold|Italic|Light|Medium|Semibold|Black|Thin|Regular)(-Italic)?$'
        ]
        
        for pattern in style_patterns:
            match = re.search(pattern, base_name, re.IGNORECASE)
            if match:
                base_name = base_name[:match.start()]
                break
        
        # Calculer un score de lisibilité
        score = 0
        if ' ' in display_name:
            score += 10
        if 'regular' in display_name.lower():
            score += 5
        if not any(style.lower() in display_name.lower() 
                  for style in ['bold', 'italic', 'light', 'medium', 'semibold', 'black', 'thin']):
            score += 3
        
        if base_name not in families:
            families[base_name] = []
        families[base_name].append((display_name, path, score))
    
    # Étape 3 : Pour chaque famille, inclure toutes les variantes
    result = {}
    for base_name, variants in families.items():
        variants.sort(key=lambda x: (-x[2], x[0]))
        for display_name, path, score in variants:
            result[display_name] = path

    return result


def get_font_files_windows() -> Dict[str, Path]:
    """Récupère les polices avec leurs chemins via le registre Windows."""
    import os
    fonts = {}
    system_fonts_dir = Path("C:/Windows/Fonts")
    user_fonts_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Windows/Fonts"

    try:
        import winreg

        # Polices système (HKEY_LOCAL_MACHINE)
        reg_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                i = 0
                while True:
                    try:
                        name, filename, _ = winreg.EnumValue(key, i)
                        clean_name = name.split(" (")[0].strip()
                        filepath = system_fonts_dir / filename if not Path(filename).is_absolute() else Path(filename)
                        if filepath.exists():
                            fonts[clean_name] = filepath
                        i += 1
                    except OSError:
                        break
        except Exception:
            pass

        # Polices utilisateur (HKEY_CURRENT_USER)
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                i = 0
                while True:
                    try:
                        name, filename, _ = winreg.EnumValue(key, i)
                        clean_name = name.split(" (")[0].strip()
                        if Path(filename).is_absolute():
                            filepath = Path(filename)
                        else:
                            filepath = user_fonts_dir / filename
                        if filepath.exists():
                            fonts[clean_name] = filepath
                        i += 1
                    except OSError:
                        break
        except Exception:
            pass

    except Exception:
        pass

    # Ajouter les polices des dossiers sans entrée registre
    for fonts_dir in [system_fonts_dir, user_fonts_dir]:
        if fonts_dir.exists():
            for f in fonts_dir.glob("*.[tToO][tTfF][fFcC]"):
                if f.stem not in fonts:
                    fonts[f.stem] = f

    return fonts


def get_font_files_macos() -> Dict[str, Path]:
    """Récupère les polices avec leurs chemins sur macOS."""
    fonts = {}
    font_dirs = [
        Path("/System/Library/Fonts"),
        Path("/Library/Fonts"),
        Path.home() / "Library/Fonts",
    ]

    for font_dir in font_dirs:
        if font_dir.exists():
            for ext in ["*.ttf", "*.otf", "*.ttc"]:
                for f in font_dir.glob(ext):
                    fonts[f.stem] = f

    return fonts


def get_font_files_linux() -> Dict[str, Path]:
    """Récupère les polices avec leurs chemins sur Linux."""
    fonts = {}

    # Utiliser fc-list pour obtenir les chemins
    try:
        result = subprocess.run(
            ["fc-list", "--format=%{family}|%{file}\n"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if "|" in line:
                    family, filepath = line.split("|", 1)
                    family = family.split(",")[0].strip()
                    if family and Path(filepath).exists():
                        fonts[family] = Path(filepath)
    except Exception:
        pass

    # Fallback : parcourir les dossiers
    if not fonts:
        font_dirs = [
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            Path.home() / ".fonts",
            Path.home() / ".local/share/fonts",
        ]
        for font_dir in font_dirs:
            if font_dir.exists():
                for ext in ["**/*.ttf", "**/*.otf", "**/*.ttc"]:
                    for f in font_dir.glob(ext):
                        fonts[f.stem] = f

    return fonts


def get_font_files() -> Dict[str, Path]:
    """Retourne un dict {nom: chemin} des polices, dédupliqué."""
    if sys.platform == "win32":
        fonts = get_font_files_windows()
    elif sys.platform == "darwin":
        fonts = get_font_files_macos()
    else:
        fonts = get_font_files_linux()

    return deduplicate_fonts(fonts)


def get_fonts() -> List[str]:
    """Retourne la liste des noms de polices installées."""
    return sorted(get_font_files().keys())


def check_font_supports_text(font_path: Path, text: str) -> bool:
    """
    Vérifie si une police contient tous les glyphes pour le texte donné.
    
    Nécessite fonttools (optionnel). Si non disponible, retourne True.
    """
    try:
        from fontTools.ttLib import TTFont
        # Suppress fonttools warnings for this session
        logging.getLogger("fontTools.ttLib.tables._p_o_s_t").setLevel(logging.ERROR)
        logging.getLogger("fontTools.ttLib.tables.DefaultTable").setLevel(logging.ERROR)
    except ImportError:
        return True  # Si fonttools n'est pas disponible, on ne peut pas vérifier

    # Ignorer les fichiers non supportés
    if font_path.suffix.lower() not in (".ttf", ".otf", ".ttc"):
        return False

    try:
        # Suppress warnings during font loading
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            font = TTFont(str(font_path), fontNumber=0)
            cmap = font.getBestCmap()
            font.close()

        if cmap is None:
            return False

        for char in text:
            if ord(char) not in cmap:
                return False
        return True
    except Exception:
        return False


def find_fonts(
    text: Optional[str] = None,
    types: Optional[List[FontType]] = None,
    random_order: bool = False,
    max_results: Optional[int] = None
) -> List[FontInfo]:
    """
    Trouve les polices installées avec filtrage avancé.
    
    Args:
        text: Texte optionnel pour filtrer les polices qui supportent ces caractères.
              Nécessite fonttools pour fonctionner.
        types: Liste des types de polices à inclure (TTF, OTF, etc.).
               Si None, tous les types sont inclus.
        random_order: Si True, retourne les résultats dans un ordre aléatoire.
        max_results: Nombre maximum de polices à retourner. Si None, retourne toutes.
    
    Returns:
        Liste de FontInfo avec les polices trouvées.
    
    Examples:
        >>> # Toutes les polices
        >>> fonts = find_fonts()
        
        >>> # Polices supportant les emojis
        >>> emoji_fonts = find_fonts(text="🌷😀")
        
        >>> # Seulement les polices TrueType
        >>> ttf_fonts = find_fonts(types=[FontType.TTF])
        
        >>> # 10 polices aléatoires
        >>> random_fonts = find_fonts(random_order=True, max_results=10)
        
        >>> # Polices OTF supportant les caractères allemands
        >>> german_fonts = find_fonts(text="äöü ß", types=[FontType.OTF])
    """
    font_files = get_font_files()
    results = []
    
    for name, path in font_files.items():
        # Filtrer par type si spécifié
        if types is not None:
            font_type = FontType.from_extension(path.suffix)
            if font_type not in types:
                continue
        
        # Filtrer par texte si spécifié
        if text is not None:
            if not check_font_supports_text(path, text):
                continue
        
        results.append(FontInfo(name=name, path=path))
    
    # Ordre aléatoire si demandé
    if random_order:
        _random.shuffle(results)
    
    # Limiter le nombre de résultats
    if max_results is not None and max_results > 0:
        results = results[:max_results]
    
    return results