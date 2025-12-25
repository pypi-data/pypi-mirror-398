"""
Result wrappers for query results with optional DataFrame conversion.

These wrapper classes enable transparent use of query results
as lists/dictionaries with optional .to_df() conversion.
"""

from __future__ import annotations

from collections import UserDict
from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, Generic, TypeVar, overload

if TYPE_CHECKING:
    import pandas as pd

    from .highlevel_client import QuestraData

# Optional pandas Integration
try:
    import pandas as pd

    _PANDAS_AVAILABLE = True
except ImportError:
    _PANDAS_AVAILABLE = False


T = TypeVar("T")


class _CaseInsensitiveDict(dict):
    """
    Dictionary wrapper that provides case-insensitive key access.

    GraphQL fields can be returned in camelCase (e.g., _rowVersion), but properties
    can be defined case-sensitively. This wrapper stores keys in their original form
    but provides case-insensitive lookup via a mapping.

    Examples:
        ```python
        # GraphQL returns: {"_id": 1, "_rowVersion": 2, "Name": "Test"}
        item = _CaseInsensitiveDict({"_id": 1, "_rowVersion": 2, "Name": "Test"})

        # Original keys preserved: {"_id": 1, "_rowVersion": 2, "Name": "Test"}
        # All access methods work case-insensitively:
        item["_id"]  # Returns 1
        item["_rowversion"]  # Returns 2 (finds _rowVersion)
        item["_rowVersion"]  # Returns 2
        item["Name"]  # Returns "Test"
        item["name"]  # Returns "Test"
        ```
    """

    def __init__(self, data):
        """Initialize with case-insensitive key mapping."""
        # Store original keys
        super().__init__(data)
        # Build lowercase -> original key mapping
        self._key_map = {k.lower() if isinstance(k, str) else k: k for k in data.keys()}

    def _get_actual_key(self, key):
        """Get the actual key from lowercase lookup."""
        if isinstance(key, str):
            return self._key_map.get(key.lower(), key)
        return key

    def __getitem__(self, key):
        """Get item by key (case-insensitive)."""
        return super().__getitem__(self._get_actual_key(key))

    def get(self, key, default=None):
        """Get item by key with default (case-insensitive)."""
        return super().get(self._get_actual_key(key), default)

    def __contains__(self, key):
        """Check if key exists (case-insensitive)."""
        if isinstance(key, str):
            return key.lower() in self._key_map
        return super().__contains__(key)

    def __setitem__(self, key, value):
        """Set item and update key mapping."""
        actual_key = self._get_actual_key(key)
        super().__setitem__(actual_key, value)
        if isinstance(key, str):
            self._key_map[key.lower()] = actual_key


class QueryResult(Sequence[T], Generic[T]):
    """
    Wrapper for query results with optional DataFrame conversion.

    Behaves transparently like a list, but additionally offers
    the method `to_df()` for pandas DataFrame conversion (only with dict data).

    Args:
        data: List of objects (query results)

    Examples:
        ```python
        # Direct usage like list (with dictionaries)
        items = client.list_items("Devices")
        for item in items:
            print(item["Name"])

        first_device = items[0]
        device_count = len(items)

        # Optional: DataFrame conversion (only with dict data)
        df = items.to_df()

        # Usage with model objects
        namespaces = client.list_namespaces()
        for ns in namespaces:
            print(ns.name)
        ```
    """

    def __init__(self, data: list[T]):
        # Wrap dict items in case-insensitive wrapper
        wrapped_data = []
        for item in data:
            if isinstance(item, dict):
                wrapped_data.append(_CaseInsensitiveDict(item))
            else:
                wrapped_data.append(item)
        self._data = wrapped_data  # type: ignore

    def to_df(self) -> pd.DataFrame:
        """
        Convert the results to a pandas DataFrame.

        Only works when the data are dictionaries.
        With model objects, they are automatically converted to dicts (via model_dump()).

        Returns:
            pandas DataFrame with the query results

        Raises:
            ImportError: When pandas is not installed
        """
        if not _PANDAS_AVAILABLE:
            raise ImportError(
                "pandas is not installed. Install it with: pip install pandas"
            )

        # If data are already dicts, use them directly
        if self._data and isinstance(self._data[0], dict):
            return pd.DataFrame(self._data)

        # With model objects: convert to dicts
        # Use model_dump() if available (Pydantic), otherwise __dict__
        data_dicts = []
        for item in self._data:
            if hasattr(item, "model_dump"):
                data_dicts.append(item.model_dump())  # type: ignore
            elif hasattr(item, "__dict__"):
                data_dicts.append(vars(item))
            else:
                # Fallback for primitive types
                data_dicts.append({"value": item})

        return pd.DataFrame(data_dicts)

    def __iter__(self) -> Iterator[T]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    @overload
    def __getitem__(self, index: int) -> T: ...

    @overload
    def __getitem__(self, index: slice) -> list[T]: ...

    def __getitem__(self, index: int | slice) -> T | list[T]:
        return self._data[index]

    def __repr__(self) -> str:
        return f"QueryResult({self._data!r})"

    def __str__(self) -> str:
        return str(self._data)

    def __eq__(self, other: object) -> bool:
        """Compare QueryResult with other sequences or QueryResults."""
        if isinstance(other, QueryResult):
            return self._data == other._data
        if isinstance(other, list):
            return self._data == other
        return NotImplemented


class TimeSeriesResult(UserDict[str, dict]):
    """
    Wrapper for timeseries query results with DataFrame conversion.

    Behaves like a normal dictionary, but additionally offers
    the method `to_df()` for pandas DataFrame conversion.

    Uses UserDict as base to ensure consistent behavior with dict operations
    (in contrast to direct dict inheritance).

    Args:
        data: Dictionary with item ID as key and timeseries data as value
        client: Reference to QuestraData client for DataFrame conversion

    Examples:
        ```python
        # Direct usage like dictionary
        result = client.list_timeseries_values(...)
        for item_id, data in result.items():
            print(f"Item {item_id}: {len(data['timeseries'])} properties")

        # Optional: DataFrame conversion
        df = result.to_df()
        df = result.to_df(properties=["stromzaehlernummer"])
        ```
    """

    def __init__(self, data: dict[str, dict], client: QuestraData):
        super().__init__(data)
        self._client = client

    def to_df(
        self, include_metadata: bool = True, properties: list[str] | None = None
    ) -> pd.DataFrame:
        """
        Convert the timeseries results to a pandas DataFrame.

        Args:
            include_metadata: Include item metadata as columns (ignored in pivot format)
            properties: List of normal properties to add as column levels

        Returns:
            pandas DataFrame in pivot format with time as index

        Raises:
            ImportError: When pandas is not installed

        Examples:
            ```python
            result = client.list_timeseries_values(...)

            # Simple DataFrame
            df = result.to_df()

            # With additional properties as columns
            df = result.to_df(properties=["stromzaehlernummer", "standort"])
            ```
        """
        return self._client._convert_timeseries_to_dataframe(
            self.data, include_metadata=include_metadata, properties=properties
        )
