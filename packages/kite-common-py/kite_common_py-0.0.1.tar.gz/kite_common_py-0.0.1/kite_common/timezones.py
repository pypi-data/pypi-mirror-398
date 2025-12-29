"""
Timezones data management module.
"""

from typing import List, Dict, Any, Optional
from .base import BaseDataManager


class TimezonesManager(BaseDataManager):
    """Manager for timezones data."""

    def __init__(self):
        super().__init__('timezones.json')

    def get_by_iana_name(self, iana_name: str) -> Optional[Dict[str, Any]]:
        """Get timezone by IANA name."""
        return self.get_by_field('iana_name', iana_name)

    def get_by_display_name(self, display_name: str) -> Optional[Dict[str, Any]]:
        """Get timezone by display name."""
        return self.get_by_field('display_name', display_name)

    def get_by_abbreviation(self, abbreviation: str) -> Optional[Dict[str, Any]]:
        """Get timezone by abbreviation."""
        return self.get_by_field('abbreviation', abbreviation.upper())

    def get_active_timezones(self) -> List[Dict[str, Any]]:
        """Get all active timezones."""
        return self.get_by_criteria(lambda tz: tz.get('is_active') == True)

    def get_dst_active_timezones(self) -> List[Dict[str, Any]]:
        """Get timezones where DST is currently active."""
        return self.get_by_criteria(lambda tz: tz.get('is_dst_active') == True)

    def get_by_gmt_offset(self, gmt_offset: str) -> List[Dict[str, Any]]:
        """Get timezones by GMT offset."""
        return self.get_multiple_by_field('gmt_offset', gmt_offset)

    def search_timezones(self, query: str) -> List[Dict[str, Any]]:
        """Search timezones by name or abbreviation."""
        return self.search(query, ['iana_name', 'display_name', 'abbreviation'])

    def get_timezones_by_region(self, region: str) -> List[Dict[str, Any]]:
        """Get timezones for a specific region (based on IANA name prefix)."""
        return self.get_by_criteria(lambda tz: tz.get('iana_name', '').startswith(region))


# Create singleton instance
timezones = TimezonesManager()


# Convenience functions
def get_all() -> List[Dict[str, Any]]:
    """Get all timezones."""
    return timezones.get_all()


def get_by_id(timezone_id: int) -> Optional[Dict[str, Any]]:
    """Get timezone by ID."""
    return timezones.get_by_id(timezone_id)


def get_by_iana_name(iana_name: str) -> Optional[Dict[str, Any]]:
    """Get timezone by IANA name."""
    return timezones.get_by_iana_name(iana_name)


def get_by_display_name(display_name: str) -> Optional[Dict[str, Any]]:
    """Get timezone by display name."""
    return timezones.get_by_display_name(display_name)


def get_by_abbreviation(abbreviation: str) -> Optional[Dict[str, Any]]:
    """Get timezone by abbreviation."""
    return timezones.get_by_abbreviation(abbreviation)


def search(query: str) -> List[Dict[str, Any]]:
    """Search timezones by query."""
    return timezones.search_timezones(query)


def get_active_timezones() -> List[Dict[str, Any]]:
    """Get all active timezones."""
    return timezones.get_active_timezones()
