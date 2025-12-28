"""
Internationalization (i18n) support for FontSearch.
Supports 10 major languages with automatic locale detection.
"""

import os
import locale
import json
from pathlib import Path
from typing import Dict, Optional

# Supported languages with their codes and native names
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'zh': '中文',           # Mandarin Chinese
    'hi': 'हिन्दी',         # Hindi  
    'es': 'Español',        # Spanish
    'ar': 'العربية',        # Arabic
    'fr': 'Français',       # French
    'bn': 'বাংলা',          # Bengali
    'pt': 'Português',      # Portuguese
    'ru': 'Русский',        # Russian
    'ja': '日本語',         # Japanese
}

# Current language (default to English)
_current_language = 'en'
_translations = {}

def get_translations_dir() -> Path:
    """Get the translations directory path."""
    return Path(__file__).parent / 'translations'

def detect_system_language() -> str:
    """Detect system language and return supported language code."""
    try:
        # Try environment variables first
        lang = os.environ.get('LANG', '').split('.')[0].split('_')[0]
        if lang in SUPPORTED_LANGUAGES:
            return lang
        
        # Try locale
        system_locale = locale.getdefaultlocale()[0]
        if system_locale:
            lang = system_locale.split('_')[0]
            if lang in SUPPORTED_LANGUAGES:
                return lang
    except:
        pass
    
    # Default to English
    return 'en'

def load_translations(language: str) -> Dict[str, str]:
    """Load translations for a specific language."""
    translations_file = get_translations_dir() / f'{language}.json'
    
    if translations_file.exists():
        try:
            with open(translations_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    
    # Fallback to English if language not found
    if language != 'en':
        english_file = get_translations_dir() / 'en.json'
        if english_file.exists():
            try:
                with open(english_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
    
    return {}

def set_language(language: str) -> bool:
    """Set the current language."""
    global _current_language, _translations
    
    if language not in SUPPORTED_LANGUAGES:
        return False
    
    _current_language = language
    _translations = load_translations(language)
    return True

def get_current_language() -> str:
    """Get the current language code."""
    return _current_language

def get_language_name(language: str) -> str:
    """Get the native name of a language."""
    return SUPPORTED_LANGUAGES.get(language, language)

def _(key: str, **kwargs) -> str:
    """
    Translate a key to the current language.
    
    Args:
        key: Translation key
        **kwargs: Variables to substitute in the translation
    
    Returns:
        Translated string with variables substituted
    """
    translation = _translations.get(key, key)
    
    # Substitute variables
    if kwargs:
        try:
            translation = translation.format(**kwargs)
        except (KeyError, ValueError):
            # If substitution fails, return the original translation
            pass
    
    return translation

def get_available_languages() -> Dict[str, str]:
    """Get all available languages with their native names."""
    available = {}
    translations_dir = get_translations_dir()
    
    if translations_dir.exists():
        for lang_code in SUPPORTED_LANGUAGES:
            lang_file = translations_dir / f'{lang_code}.json'
            if lang_file.exists():
                available[lang_code] = SUPPORTED_LANGUAGES[lang_code]
    
    # Always include English as fallback
    if 'en' not in available:
        available['en'] = SUPPORTED_LANGUAGES['en']
    
    return available

# Initialize with system language
_current_language = detect_system_language()
_translations = load_translations(_current_language)

# Export main functions
__all__ = [
    '_', 'set_language', 'get_current_language', 'get_language_name',
    'get_available_languages', 'detect_system_language', 'SUPPORTED_LANGUAGES'
]