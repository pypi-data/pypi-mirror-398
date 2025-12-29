"""
Error codes data management module.
"""

from typing import List, Dict, Any, Optional
from .base import BaseDataManager


class ErrorCodesManager(BaseDataManager):
    """Manager for error codes data."""

    def __init__(self):
        super().__init__('error_codes.json', 'code')

    def get_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Get error code by code string."""
        return self.get_by_field('code', code)

    def get_by_http_status(self, http_status: int) -> List[Dict[str, Any]]:
        """Get error codes by HTTP status code."""
        return self.get_multiple_by_field('http_status', http_status)

    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get error codes by category."""
        return self.get_multiple_by_field('category', category)

    def get_retryable_errors(self) -> List[Dict[str, Any]]:
        """Get error codes that are retryable."""
        return self.get_by_criteria(lambda err: err.get('is_retryable') == True)

    def get_non_retryable_errors(self) -> List[Dict[str, Any]]:
        """Get error codes that are not retryable."""
        return self.get_by_criteria(lambda err: err.get('is_retryable') == False)

    def search_error_codes(self, query: str) -> List[Dict[str, Any]]:
        """Search error codes by message or description."""
        return self.search(query, ['code', 'message', 'description'])

    def get_categories(self) -> List[str]:
        """Get all unique error categories."""
        data = self.get_all()
        categories = set()
        for item in data:
            category = item.get('category')
            if category:
                categories.add(category)
        return sorted(list(categories))

    def get_http_status_codes(self) -> List[int]:
        """Get all unique HTTP status codes."""
        data = self.get_all()
        status_codes = set()
        for item in data:
            status = item.get('http_status')
            if status:
                status_codes.add(status)
        return sorted(list(status_codes))


# Create singleton instance
error_codes = ErrorCodesManager()


# Convenience functions
def get_all() -> List[Dict[str, Any]]:
    """Get all error codes."""
    return error_codes.get_all()


def get_by_code(code: str) -> Optional[Dict[str, Any]]:
    """Get error code by code string."""
    return error_codes.get_by_code(code)


def get_by_http_status(http_status: int) -> List[Dict[str, Any]]:
    """Get error codes by HTTP status."""
    return error_codes.get_by_http_status(http_status)


def get_by_category(category: str) -> List[Dict[str, Any]]:
    """Get error codes by category."""
    return error_codes.get_by_category(category)


def search(query: str) -> List[Dict[str, Any]]:
    """Search error codes by query."""
    return error_codes.search_error_codes(query)


def get_categories() -> List[str]:
    """Get all error categories."""
    return error_codes.get_categories()


def get_http_status_codes() -> List[int]:
    """Get all HTTP status codes."""
    return error_codes.get_http_status_codes()


def get_retryable_errors() -> List[Dict[str, Any]]:
    """Get retryable error codes."""
    return error_codes.get_retryable_errors()


def get_non_retryable_errors() -> List[Dict[str, Any]]:
    """Get non-retryable error codes."""
    return error_codes.get_non_retryable_errors()
