"""
Exception classes for Questra Data Client.

Defines exceptions for GraphQL errors and client operations.
Error codes are directly taken from the server.
"""

from __future__ import annotations


class QuestraError(Exception):
    """Base exception for all Questra-related errors."""

    pass


class QuestraGraphQLError(QuestraError):
    """
    Exception for GraphQL errors from the server.

    The server delivers structured errors with error codes from the messageInfos list
    (see _systemInfo query).

    Attributes:
        message: Error message from the server
        code: Error code from the server (e.g. "DATA_MODEL_DUPLICATE_INVENTORY_NAME")
        category: Error category (e.g. "DataModel", "Validation", "TimeSeries")
        placeholders: Dictionary with placeholder values from extensions
        locations: List of error positions in the query
        path: Path to the faulty field in the query
        extensions: Complete extensions from the error response

    Examples:
        >>> try:
        ...     client.mutations.create_inventory(...)
        ... except QuestraGraphQLError as e:
        ...     print(f"Code: {e.code}")
        ...     print(f"Message: {e.message}")
        ...     print(f"Placeholders: {e.placeholders}")
        Code: DATA_MODEL_DUPLICATE_INVENTORY_NAME
        Message: Duplicate inventory name 'TestInventory'...
        Placeholders: {'InventoryName': 'TestInventory', 'NamespaceName': 'Test'}
    """

    def __init__(
        self,
        message: str,
        code: str | None = None,
        category: str | None = None,
        placeholders: dict[str, str] | None = None,
        locations: list[dict] | None = None,
        path: list[str] | None = None,
        extensions: dict | None = None,
    ):
        """
        Initialize a GraphQL-Error-Exception.

        Args:
            message: Error message from the server
            code: Optional - Error code
            category: Optional - Error category
            placeholders: Optional - Placeholder values
            locations: Optional - Error positions
            path: Optional - Path to field
            extensions: Optional - Complete extensions
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.category = category
        self.placeholders = placeholders or {}
        self.locations = locations or []
        self.path = path or []
        self.extensions = extensions or {}

    def __str__(self) -> str:
        """String representation with code and message."""
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"code={self.code!r}, "
            f"category={self.category!r}, "
            f"placeholders={self.placeholders!r})"
        )

    def is_duplicate_error(self) -> bool:
        """Checks if this is a duplicate error."""
        return self.code is not None and "DUPLICATE" in self.code

    def is_validation_error(self) -> bool:
        """Checks if this is a validation error."""
        return self.category == "Validation"

    def is_not_found_error(self) -> bool:
        """Checks if this is a not-found error ."""
        return self.code is not None and "UNKNOWN" in self.code
