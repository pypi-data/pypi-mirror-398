"""
Currencies data management module.
"""

from typing import List, Dict, Any, Optional
from .base import BaseDataManager


class CurrenciesManager(BaseDataManager):
    """Manager for currencies data."""

    def __init__(self):
        super().__init__('currencies.json')

    def get_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Get currency by ISO code."""
        return self.get_by_field('code', code.upper())

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get currency by name (exact match)."""
        return self.get_by_field('name', name)

    def get_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get currency by symbol."""
        return self.get_by_field('symbol', symbol)

    def search_currencies(self, query: str) -> List[Dict[str, Any]]:
        """Search currencies by name, code, or symbol."""
        return self.search(query, ['name', 'code', 'symbol'])

    def get_countries_using_currency(self, currency_id: int) -> List[Dict[str, Any]]:
        """Get countries that use a specific currency."""
        from . import countries
        return countries.get_by_currency_id(currency_id)


# Create singleton instance
currencies = CurrenciesManager()


# Convenience functions
def get_all() -> List[Dict[str, Any]]:
    """Get all currencies."""
    return currencies.get_all()


def get_by_id(currency_id: int) -> Optional[Dict[str, Any]]:
    """Get currency by ID."""
    return currencies.get_by_id(currency_id)


def get_by_code(code: str) -> Optional[Dict[str, Any]]:
    """Get currency by ISO code."""
    return currencies.get_by_code(code)


def get_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get currency by name."""
    return currencies.get_by_name(name)


def get_by_symbol(symbol: str) -> Optional[Dict[str, Any]]:
    """Get currency by symbol."""
    return currencies.get_by_symbol(symbol)


def search(query: str) -> List[Dict[str, Any]]:
    """Search currencies by query."""
    return currencies.search_currencies(query)
