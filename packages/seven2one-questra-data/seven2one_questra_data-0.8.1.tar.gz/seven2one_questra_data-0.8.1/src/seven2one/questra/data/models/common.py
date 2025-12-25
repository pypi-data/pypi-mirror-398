"""Common type models - re-exports and manual definitions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# Re-exports from generated.models
from ..generated.models import FieldConflictActionEnumType as ConflictAction
from ..generated.models import FieldPageInfoType as PageInfo


# Manuell definiert - nicht im Schema
class SortOrder(str, Enum):
    """
    Sort order.

    Attributes:
        ASC: Ascending (A-Z, 0-9)
        DESC: Descending (Z-A, 9-0)
    """

    ASC = "ASC"
    DESC = "DESC"


# Helper Result Classes (nicht generiert, da spezielle from_dict Logik)


@dataclass
class NamedItemResult:
    """
    Result of mutations that create/delete a named item.

    Corresponds to _NamedItem__PayloadType from the GraphQL schema.

    Attributes:
        name: Name of the item
        existed: True if item already existed, False if newly created
    """

    name: str
    existed: bool

    @staticmethod
    def from_dict(data: dict) -> NamedItemResult:
        """Creates NamedItemResult from GraphQL Response."""
        return NamedItemResult(
            name=data["name"],
            existed=data["existed"],
        )


@dataclass
class BackgroundJobResult:
    """
    Result of mutations that start a background job.

    Corresponds to _BackgroundJobId__PayloadType from the GraphQL schema.

    Attributes:
        background_job_id: ID of the background job
    """

    background_job_id: str

    @staticmethod
    def from_dict(data: dict) -> BackgroundJobResult:
        """Creates BackgroundJobResult from GraphQL Response."""
        return BackgroundJobResult(
            background_job_id=data["backgroundJobId"],
        )


@dataclass
class TimeSeriesIdResult:
    """
    Result of timeseries creation.

    Corresponds to _Id__PayloadType from the GraphQL schema.

    Attributes:
        id: ID of the created timeseries
    """

    id: str  # LongNumberString

    @staticmethod
    def from_dict(data: dict) -> TimeSeriesIdResult:
        """Creates TimeSeriesIdResult from GraphQL Response."""
        return TimeSeriesIdResult(
            id=data["_id"],
        )


__all__ = [
    "PageInfo",
    "SortOrder",
    "ConflictAction",
    "NamedItemResult",
    "BackgroundJobResult",
    "TimeSeriesIdResult",
]
