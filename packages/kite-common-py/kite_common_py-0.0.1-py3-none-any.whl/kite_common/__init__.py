"""
Kite Common - Framework-agnostic Python package for common data and utilities.

This package provides standardized data for countries, currencies, timezones,
languages, and error codes that can be used across different Python frameworks
and applications.
"""

__version__ = "0.1.0"
__author__ = "Kite Team"
__email__ = "team@kite.com"

from . import countries
from . import currencies
from . import timezones
from . import languages
from . import error_codes

__all__ = [
    'countries',
    'currencies',
    'timezones',
    'languages',
    'error_codes',
]
