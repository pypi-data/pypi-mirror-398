"""
Internationalization (i18n) module for Claux.

Provides multilingual support with automatic language detection
and fallback to English.
"""

import json
import os
from pathlib import Path
from typing import Dict


class I18n:
    """Internationalization handler for Claux."""

    def __init__(self, default_lang: str = "en"):
        """
        Initialize i18n handler.

        Args:
            default_lang: Default language code (default: "en")
        """
        self.default_lang = default_lang
        self.current_lang = self._detect_language()
        self.translations: Dict[str, Dict[str, str]] = {}
        self._load_translations()

    def _detect_language(self) -> str:
        """
        Detect user's preferred language from environment.

        Priority:
        1. CLAUX_LANG environment variable (temporary override)
        2. User config file (~/.claux/config.yaml)
        3. LANG environment variable (parse locale)
        4. Default language

        Returns:
            Language code (e.g., "en", "ru")
        """
        # Check CLAUX_LANG first (temporary override)
        claux_lang = os.getenv("CLAUX_LANG")
        if claux_lang:
            return claux_lang.lower()[:2]

        # Check user config file
        try:
            from claux.core.user_config import get_config

            config = get_config()
            config_lang = config.get("language")
            if config_lang:
                return config_lang.lower()[:2]
        except Exception:
            pass

        # Check system LANG
        system_lang = os.getenv("LANG", "")
        if system_lang:
            # Parse locale like "ru_RU.UTF-8" -> "ru"
            lang_code = system_lang.split("_")[0].split(".")[0].lower()
            if lang_code:
                return lang_code

        return self.default_lang

    def _load_translations(self):
        """Load all available translation files."""
        locales_dir = Path(__file__).parent / "locales"

        if not locales_dir.exists():
            return

        for locale_file in locales_dir.glob("*.json"):
            lang_code = locale_file.stem
            try:
                with open(locale_file, "r", encoding="utf-8") as f:
                    self.translations[lang_code] = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load locale {lang_code}: {e}")

    def t(self, key: str, **kwargs) -> str:
        """
        Translate a key to current language.

        Args:
            key: Translation key (e.g., "cli.version.title")
            **kwargs: Variables to substitute in translation

        Returns:
            Translated string, or key if translation not found
        """
        # Try current language
        translation = self._get_translation(self.current_lang, key)

        # Fallback to default language
        if translation == key and self.current_lang != self.default_lang:
            translation = self._get_translation(self.default_lang, key)

        # Substitute variables
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except (KeyError, ValueError):
                pass

        return translation

    def _get_translation(self, lang: str, key: str) -> str:
        """
        Get translation for specific language and key.

        Args:
            lang: Language code
            key: Translation key (supports dot notation)

        Returns:
            Translated string or original key if not found
        """
        if lang not in self.translations:
            return key

        # Support dot notation: "cli.version.title"
        parts = key.split(".")
        value = self.translations[lang]

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return key

        return value if isinstance(value, str) else key

    def set_language(self, lang: str):
        """
        Change current language.

        Args:
            lang: Language code (e.g., "en", "ru")
        """
        if lang in self.translations:
            self.current_lang = lang
        else:
            print(f"Warning: Language '{lang}' not available, using {self.current_lang}")

    def get_available_languages(self) -> list:
        """
        Get list of available languages.

        Returns:
            List of language codes
        """
        return list(self.translations.keys())


# Global i18n instance
_i18n = I18n()


def t(key: str, **kwargs) -> str:
    """
    Translate a key to current language (shorthand function).

    Args:
        key: Translation key
        **kwargs: Variables to substitute

    Returns:
        Translated string
    """
    return _i18n.t(key, **kwargs)


def set_language(lang: str):
    """
    Set current language and save to user config.

    Args:
        lang: Language code
    """
    _i18n.set_language(lang)

    # Save to user config for persistence across sessions
    try:
        from claux.core.user_config import get_config

        config = get_config()
        config.set("language", lang)
    except Exception as e:
        print(f"Warning: Failed to save language preference: {e}")

    # Also set environment variable for this session
    os.environ["CLAUX_LANG"] = lang


def get_language() -> str:
    """
    Get current language code.

    Returns:
        Current language code
    """
    return _i18n.current_lang


def get_available_languages() -> list:
    """
    Get available languages.

    Returns:
        List of language codes
    """
    return _i18n.get_available_languages()
