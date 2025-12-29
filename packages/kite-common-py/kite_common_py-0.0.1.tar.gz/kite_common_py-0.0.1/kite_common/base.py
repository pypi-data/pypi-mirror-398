"""
Base module for kite-common package.
Provides common functionality for data loading and management.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable


class DataLoader:
    """Base class for loading and managing JSON data."""

    def __init__(self, data_file: str):
        self.data_file = data_file
        self._data: Optional[List[Dict[str, Any]]] = None

    def _load_data(self) -> List[Dict[str, Any]]:
        """Load data from JSON file."""
        if self._data is not None:
            return self._data

        data_path = Path(__file__).parent / "data" / self.data_file

        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Data file not found: {data_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in data file {data_path}: {e}")

        return self._data

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all records."""
        return self._load_data()

    def get_by_id(self, id_value: int) -> Optional[Dict[str, Any]]:
        """Get record by ID."""
        data = self._load_data()
        for item in data:
            if item.get('id') == id_value:
                return item
        return None

    def get_by_criteria(self, criteria_func: Callable[[Dict[str, Any]], bool]) -> List[Dict[str, Any]]:
        """Get records matching custom criteria function."""
        data = self._load_data()
        return [item for item in data if criteria_func(item)]

    def search(self, query: str, fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search records by query string in specified fields."""
        data = self._load_data()
        query_lower = query.lower()

        if fields is None:
            # Search in all string fields
            results = []
            for item in data:
                for value in item.values():
                    if isinstance(value, str) and query_lower in value.lower():
                        results.append(item)
                        break
            return results
        else:
            # Search in specified fields
            results = []
            for item in data:
                for field in fields:
                    value = item.get(field)
                    if isinstance(value, str) and query_lower in value.lower():
                        results.append(item)
                        break
            return results


class BaseDataManager(DataLoader):
    """Enhanced base class with additional functionality."""

    def __init__(self, data_file: str, primary_key: str = 'id'):
        super().__init__(data_file)
        self.primary_key = primary_key

    def exists(self, id_value: Any) -> bool:
        """Check if record exists by primary key."""
        return self.get_by_id(id_value) is not None

    def count(self) -> int:
        """Get total count of records."""
        return len(self.get_all())

    def get_by_field(self, field: str, value: Any) -> Optional[Dict[str, Any]]:
        """Get record by specific field value."""
        data = self._load_data()
        for item in data:
            if item.get(field) == value:
                return item
        return None

    def get_multiple_by_field(self, field: str, value: Any) -> List[Dict[str, Any]]:
        """Get multiple records by field value."""
        data = self._load_data()
        return [item for item in data if item.get(field) == value]

    def filter_by_field(self, **kwargs) -> List[Dict[str, Any]]:
        """Filter records by multiple field criteria."""
        data = self._load_data()
        results = data

        for field, value in kwargs.items():
            results = [item for item in results if item.get(field) == value]

        return results
