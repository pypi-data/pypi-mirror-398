"""TimeSeries Type Models - Re-Exports from generierten REST-Modellen."""

from __future__ import annotations

# Re-exports from generated.rest_models
from ..generated.rest_models import (
    Aggregation,
    Interval,
    Quality,
    QuotationBehavior,
    TimeSeriesValue,
    TimeUnit,
    ValueAlignment,
    ValueAvailability,
)
from ..generated.rest_models import TimeSeriesPayload as TimeSeries

__all__ = [
    "Aggregation",
    "Interval",
    "Quality",
    "QuotationBehavior",
    "TimeSeries",
    "TimeSeriesValue",
    "TimeUnit",
    "ValueAlignment",
    "ValueAvailability",
]
