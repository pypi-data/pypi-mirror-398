"""REST API models - Re-exports from generated REST models."""

from __future__ import annotations

# For compatibility - QuotationsPayload and TimeSeriesDataPayload are not generated
# These are manually defined as wrappers, as they are not in the Swagger schema
from dataclasses import dataclass, field

# Re-exports from generated.rest_models
from ..generated.rest_models import (
    ErrorPayload,
    ErrorsPayload,
    File,
    Quotations,
    QuotationValue,
    SetTimeSeriesDataInput,
    TimeSeriesData,
    TimeSeriesPayload,
    TimeSeriesValue,
)


@dataclass
class QuotationsPayload:
    """
    Quotations payload.

    Attributes:
        items: List of quotations
    """

    items: list[Quotations] = field(default_factory=list)


@dataclass
class TimeSeriesDataPayload:
    """
    Time series data payload.

    Attributes:
        data: List of time series data
    """

    data: list[TimeSeriesData] = field(default_factory=list)


__all__ = [
    "ErrorPayload",
    "ErrorsPayload",
    "File",
    "Quotations",
    "QuotationsPayload",
    "QuotationValue",
    "SetTimeSeriesDataInput",
    "TimeSeriesData",
    "TimeSeriesDataPayload",
    "TimeSeriesValue",
    "TimeSeriesPayload",
]
