"""
Languages data management module.
"""

from typing import List, Dict, Any, Optional
from .base import BaseDataManager


class LanguagesManager(BaseDataManager):
    """Manager for languages data."""

    def __init__(self):
        super().__init__('languages.json')

    def get_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Get language by ISO 639-1 code."""
        return self.get_by_field('code', code.lower())

    def get_by_code3(self, code3: str) -> Optional[Dict[str, Any]]:
        """Get language by ISO 639-3 code."""
        return self.get_by_field('code_3', code3.lower())

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get language by name (exact match)."""
        return self.get_by_field('name', name)

    def get_by_native_name(self, native_name: str) -> Optional[Dict[str, Any]]:
        """Get language by native name (exact match)."""
        return self.get_by_field('native_name', native_name)

    def get_rtl_languages(self) -> List[Dict[str, Any]]:
        """Get languages that are written right-to-left."""
        return self.get_by_criteria(lambda lang: lang.get('is_rtl') == True)

    def get_ltr_languages(self) -> List[Dict[str, Any]]:
        """Get languages that are written left-to-right."""
        return self.get_by_criteria(lambda lang: lang.get('is_rtl') == False)

    def get_by_script(self, script: str) -> List[Dict[str, Any]]:
        """Get languages by writing system."""
        return self.get_multiple_by_field('script', script)

    def search_languages(self, query: str) -> List[Dict[str, Any]]:
        """Search languages by name, native name, or codes."""
        return self.search(query, ['name', 'native_name', 'code', 'code_3'])


# Create singleton instance
languages = LanguagesManager()


# Convenience functions
def get_all() -> List[Dict[str, Any]]:
    """Get all languages."""
    return languages.get_all()


def get_by_id(language_id: int) -> Optional[Dict[str, Any]]:
    """Get language by ID."""
    return languages.get_by_id(language_id)


def get_by_code(code: str) -> Optional[Dict[str, Any]]:
    """Get language by ISO code."""
    return languages.get_by_code(code)


def get_by_code3(code3: str) -> Optional[Dict[str, Any]]:
    """Get language by ISO 639-3 code."""
    return languages.get_by_code3(code3)


def get_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get language by name."""
    return languages.get_by_name(name)


def search(query: str) -> List[Dict[str, Any]]:
    """Search languages by query."""
    return languages.search_languages(query)


def get_rtl_languages() -> List[Dict[str, Any]]:
    """Get right-to-left languages."""
    return languages.get_rtl_languages()


def get_ltr_languages() -> List[Dict[str, Any]]:
    """Get left-to-right languages."""
    return languages.get_ltr_languages()
