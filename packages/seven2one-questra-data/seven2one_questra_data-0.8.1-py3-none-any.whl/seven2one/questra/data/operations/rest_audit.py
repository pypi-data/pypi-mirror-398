"""REST operations for Audit endpoints."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime

logger = logging.getLogger(__name__)

from ..models.rest import TimeSeriesData, TimeSeriesDataPayload, TimeSeriesPayload
from ..models.timeseries import Quality, QuotationBehavior


class AuditOperations:
    """REST operations for Audit endpoints."""

    def __init__(self, rest_get_func: Callable):
        """
        Initialize Audit operations.

        Args:
            rest_get_func: GET request function
        """
        self._get = rest_get_func
        logger.debug("AuditOperations initialized")

    def get_file(self, file_id: int) -> bytes:
        """
        Get audit data for a file.

        Args:
            file_id: File ID

        Returns:
            bytes: File content
        """
        logger.info(f"Getting audit data for file {file_id}")
        result = self._get("/audit/file", params={"fileId": file_id})
        logger.info(f"Audit file data retrieved, size: {len(result)} bytes")
        return result

    def get_timeseries(self, time_series_id: int) -> TimeSeriesPayload:
        """
        Get audit metadata for a TimeSeries.

        Args:
            time_series_id: TimeSeries ID

        Returns:
            TimeSeriesPayload: Metadata
        """
        logger.info(f"Getting audit metadata for timeseries {time_series_id}")
        result = self._get("/audit/timeseries", params={"timeSeriesId": time_series_id})

        # Parse Response - Pydantic converts automatically through aliases
        timeseries = TimeSeriesPayload.model_validate(result)

        logger.info("Timeseries audit metadata retrieved successfully")
        return timeseries

    def get_timeseries_data(
        self,
        time_series_id: int,
        from_time: datetime,
        to_time: datetime,
        audit_time: datetime,
        audit_exactly_at: bool = False,
        quotation_time: datetime | None = None,
        quotation_exactly_at: bool = False,
        quotation_behavior: QuotationBehavior | None = None,
        exclude_qualities: list[Quality] | None = None,
    ) -> TimeSeriesDataPayload:
        """
        Get audit data for a TimeSeries.

        Args:
            time_series_id: TimeSeries ID
            from_time: Start time
            to_time: End time
            audit_time: Audit time
            audit_exactly_at: Exactly at audit time (default: False = before)
            quotation_time: Quotation time
            quotation_exactly_at: Exactly at quotation time (default: False)
            quotation_behavior: Quotation behavior
            exclude_qualities: Qualities to exclude

        Returns:
            TimeSeriesDataPayload: Audit data
        """
        logger.info(
            f"Getting audit data for timeseries. time_series_id={time_series_id}, from_time={from_time}, to_time={to_time}, audit_time={audit_time}"
        )

        params = {
            "timeSeriesId": time_series_id,
            "from": from_time.isoformat(),
            "to": to_time.isoformat(),
            "auditTime": audit_time.isoformat(),
            "auditExactlyAt": audit_exactly_at,
        }

        if quotation_time:
            params["quotationTime"] = quotation_time.isoformat()

        params["quotationExactlyAt"] = quotation_exactly_at

        if quotation_behavior:
            params["quotationBehavior"] = quotation_behavior.value

        if exclude_qualities:
            params["excludeQualities"] = [q.value for q in exclude_qualities]

        result = self._get("/audit/timeseries/data", params=params)

        # Parse Response - can be single object or array
        data_objects = result if isinstance(result, list) else [result]

        # Pydantic converts automatically through aliases and type conversions
        data_list = [TimeSeriesData.model_validate(ts_data) for ts_data in data_objects]

        logger.info("Timeseries audit data retrieved successfully")
        return TimeSeriesDataPayload(data=data_list)
