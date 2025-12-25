"""REST operations for TimeSeries endpoints."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime

logger = logging.getLogger(__name__)

from ..models.rest import (
    Quotations,
    QuotationsPayload,
    QuotationValue,
    SetTimeSeriesDataInput,
    TimeSeriesData,
    TimeSeriesDataPayload,
)
from ..models.timeseries import (
    Aggregation,
    Interval,
    Quality,
    QuotationBehavior,
    TimeSeriesValue,
    TimeUnit,
)


class TimeSeriesOperations:
    """REST operations for TimeSeries endpoints."""

    def __init__(self, rest_get_func: Callable, rest_post_func: Callable):
        """
        Initialize TimeSeries operations.

        Args:
            rest_get_func: GET request function
            rest_post_func: POST request function
        """
        self._get = rest_get_func
        self._post = rest_post_func
        logger.debug("TimeSeriesOperations initialized")

    def get_data(
        self,
        time_series_ids: list[int],
        from_time: datetime,
        to_time: datetime,
        time_unit: TimeUnit | None = None,
        multiplier: int | None = None,
        aggregation: Aggregation | None = None,
        unit: str | None = None,
        time_zone: str | None = None,
        quotation_time: datetime | None = None,
        quotation_exactly_at: bool = False,
        quotation_behavior: QuotationBehavior | None = None,
        exclude_qualities: list[Quality] | None = [Quality.MISSING],
    ) -> TimeSeriesDataPayload:
        """
        Get time series data.

        Args:
            time_series_ids: TimeSeries IDs
            from_time: Start time
            to_time: End time
            time_unit: Time unit for interval aggregation
            multiplier: Multiplier for interval aggregation
            aggregation: Aggregation type
            unit: Target unit for value conversion
            time_zone: Output timezone
            quotation_time: Quotation time
            quotation_exactly_at: Exact quotation at specified time
            quotation_behavior: Quotation behavior
            exclude_qualities: Qualities to exclude

        Returns:
            TimeSeriesDataPayload: Data for all requested TimeSeries
        """
        logger.info(
            f"Getting timeseries data. time_series_ids={time_series_ids}, from_time={from_time}, to_time={to_time}"
        )

        params = {
            "timeSeriesIds": [str(ts_id) for ts_id in time_series_ids],
            "from": from_time.isoformat(),
            "to": to_time.isoformat(),
        }

        if time_unit and multiplier:
            params["timeUnit"] = time_unit.value
            params["multiplier"] = multiplier

        if aggregation:
            params["aggregation"] = aggregation.value

        if unit:
            params["unit"] = unit

        if time_zone:
            params["timeZone"] = time_zone

        if quotation_time:
            params["quotationTime"] = quotation_time.isoformat()

        params["quotationExactlyAt"] = quotation_exactly_at

        if quotation_behavior:
            params["quotationBehavior"] = quotation_behavior.value

        if exclude_qualities:
            params["excludeQualities"] = [q.value for q in exclude_qualities]

        result = self._get("/timeseries/data", params=params)

        # Parse JSON/NDJSON Response
        # Single TS (JSON): {timeSeriesId: "...", interval: {...}, values: [...]}
        # Multiple TS (NDJSON): [{...}, {...}]
        data_objects = result if isinstance(result, list) else [result]

        data_list = []
        for ts_data in data_objects:
            interval_data = ts_data.get("interval", {})
            interval = Interval.model_validate(interval_data)

            values = [
                TimeSeriesValue.model_validate(val) for val in ts_data.get("values", [])
            ]

            ts_data_obj = TimeSeriesData.model_validate(
                {
                    **ts_data,
                    "interval": interval,
                    "values": values,
                }
            )
            data_list.append(ts_data_obj)

        logger.info(f"Retrieved data for {len(data_list)} timeseries")
        return TimeSeriesDataPayload(data=data_list)

    def set_data(
        self,
        data_inputs: list[SetTimeSeriesDataInput],
    ) -> None:
        """
        Set time series data.

        Args:
            data_inputs: List of SetTimeSeriesDataInput objects
        """
        logger.info(f"Setting timeseries data for {len(data_inputs)} timeseries")

        # Convert to JSON
        payload = []
        for data_input in data_inputs:
            item = {
                "timeSeriesId": str(data_input.time_series_id),
                "values": [
                    {
                        "time": val.time.isoformat(),
                        "value": val.value,
                        **({"quality": val.quality.value} if val.quality else {}),
                    }
                    for val in data_input.values
                ],
            }

            if data_input.interval:
                item["interval"] = {
                    "timeUnit": data_input.interval.time_unit.value,
                    "multiplier": data_input.interval.multiplier,
                }

            if data_input.unit:
                item["unit"] = data_input.unit

            if data_input.time_zone:
                item["timeZone"] = data_input.time_zone

            if data_input.quotation_time:
                item["quotationTime"] = data_input.quotation_time.isoformat()

            payload.append(item)

        logger.debug(f"Posting {len(payload)} timeseries data entries")
        self._post("/timeseries/data", json=payload)
        logger.info("Timeseries data set successfully")

    def get_quotations(
        self,
        time_series_ids: list[int],
        from_time: datetime,
        to_time: datetime,
        aggregated: bool = False,
    ) -> QuotationsPayload:
        """
        Get quotations for time series.

        Args:
            time_series_ids: TimeSeries IDs
            from_time: Start time
            to_time: End time
            aggregated: Return aggregated quotations

        Returns:
            QuotationsPayload: Quotations for all requested TimeSeries
        """
        logger.info(
            f"Getting timeseries quotations. time_series_ids={time_series_ids}, from_time={from_time}, to_time={to_time}, aggregated={aggregated}"
        )

        params = {
            "timeSeriesIds": [str(ts_id) for ts_id in time_series_ids],
            "from": from_time.isoformat(),
            "to": to_time.isoformat(),
            "aggregated": aggregated,
        }

        result = self._get("/timeseries/quotations", params=params)

        # Parse Response - can be single object or array
        quotations = result if isinstance(result, list) else [result]

        items = []
        for quotation in quotations:
            values = [
                QuotationValue.model_validate(val)
                for val in quotation.get("values", [])
            ]

            quot_obj = Quotations.model_validate(
                {
                    **quotation,
                    "values": values,
                }
            )
            items.append(quot_obj)

        logger.info(f"Retrieved quotations for {len(items)} timeseries")
        return QuotationsPayload(items=items)
