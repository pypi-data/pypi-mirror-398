"""
Countries data management module.
"""

from typing import List, Dict, Any, Optional
from .base import BaseDataManager


class CountriesManager(BaseDataManager):
    """Manager for countries data."""

    def __init__(self):
        super().__init__('countries.json')

    def get_by_iso2(self, iso2: str) -> Optional[Dict[str, Any]]:
        """Get country by 2-letter ISO code."""
        return self.get_by_field('iso2', iso2.upper())

    def get_by_iso3(self, iso3: str) -> Optional[Dict[str, Any]]:
        """Get country by 3-letter ISO code."""
        return self.get_by_field('iso3', iso3.upper())

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get country by name (exact match)."""
        return self.get_by_field('name', name)

    def get_rtl_countries(self) -> List[Dict[str, Any]]:
        """Get countries with right-to-left languages."""
        return self.get_by_criteria(lambda c: c.get('is_rtl') == True)

    def get_ltr_countries(self) -> List[Dict[str, Any]]:
        """Get countries with left-to-right languages."""
        return self.get_by_criteria(lambda c: c.get('is_rtl') == False)

    def get_by_phone_code(self, phone_code: str) -> List[Dict[str, Any]]:
        """Get countries by phone code."""
        return self.get_multiple_by_field('phone_code', phone_code)

    def get_by_currency_id(self, currency_id: int) -> List[Dict[str, Any]]:
        """Get countries by currency ID."""
        return self.get_multiple_by_field('currency_id', currency_id)

    def get_with_currencies(self) -> List[Dict[str, Any]]:
        """Get countries with currency information joined."""
        from . import currencies

        countries_data = self.get_all()
        currencies_data = {c['id']: c for c in currencies.get_all()}

        for country in countries_data:
            currency_id = country.get('currency_id')
            if currency_id and currency_id in currencies_data:
                country['currency'] = currencies_data[currency_id]

        return countries_data

    def search_countries(self, query: str) -> List[Dict[str, Any]]:
        """Search countries by name or ISO codes."""
        return self.search(query, ['name', 'iso2', 'iso3'])


# Create singleton instance
countries = CountriesManager()


# Convenience functions
def get_all() -> List[Dict[str, Any]]:
    """Get all countries."""
    return countries.get_all()


def get_by_id(country_id: int) -> Optional[Dict[str, Any]]:
    """Get country by ID."""
    return countries.get_by_id(country_id)


def get_by_iso2(iso2: str) -> Optional[Dict[str, Any]]:
    """Get country by 2-letter ISO code."""
    return countries.get_by_iso2(iso2)


def get_by_iso3(iso3: str) -> Optional[Dict[str, Any]]:
    """Get country by 3-letter ISO code."""
    return countries.get_by_iso3(iso3)


def get_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get country by name."""
    return countries.get_by_name(name)


def search(query: str) -> List[Dict[str, Any]]:
    """Search countries by query."""
    return countries.search_countries(query)


def get_with_currencies() -> List[Dict[str, Any]]:
    """Get countries with currency information."""
    return countries.get_with_currencies()
