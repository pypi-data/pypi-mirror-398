"""
Internationalization support for Mac Cleaner.
Detects system language and loads appropriate translations.
"""

import gettext
import locale
import os
from pathlib import Path
from typing import Callable

# Default to English
_translator = gettext.NullTranslations()


def detect_system_language() -> str:
    """
    Detect the system language.
    Returns language code like 'es_ES', 'en_US', etc.
    """
    try:
        # Try to get system locale
        lang, _ = locale.getdefaultlocale()
        if lang:
            return lang
    except Exception:
        pass

    # Fallback to environment variables
    for var in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
        lang = os.environ.get(var)
        if lang:
            # Extract language code (e.g., 'es_ES.UTF-8' -> 'es_ES')
            lang = lang.split('.')[0]
            return lang

    # Default to English
    return 'en_US'


def setup_i18n() -> Callable[[str], str]:
    """
    Setup internationalization.
    Returns a translation function.
    """
    global _translator

    # Get locale directory
    locale_dir = Path(__file__).parent / 'locales'

    # Detect system language
    system_lang = detect_system_language()

    # Try to load translations for detected language
    try:
        # Try exact match first (e.g., es_ES)
        _translator = gettext.translation(
            'mac_cleaner',
            localedir=str(locale_dir),
            languages=[system_lang],
            fallback=False
        )
    except FileNotFoundError:
        try:
            # Try language without region (e.g., es)
            lang_short = system_lang.split('_')[0]
            _translator = gettext.translation(
                'mac_cleaner',
                localedir=str(locale_dir),
                languages=[lang_short],
                fallback=False
            )
        except FileNotFoundError:
            # Fallback to NullTranslations (English)
            _translator = gettext.NullTranslations()

    return _translator.gettext


# Initialize translation function
_ = setup_i18n()
