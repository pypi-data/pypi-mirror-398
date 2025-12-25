"""
Unit-Tests für TimeSeriesOperations (REST API).

Testet alle REST-Methoden with gemockten HTTP-Responses
und Payload-Validierung gegen Swagger Schema.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from helpers.rest_validators import RestPayloadValidator

from seven2one.questra.data.models.timeseries import (
    Aggregation,
    Interval,
    Quality,
    QuotationBehavior,
    TimeUnit,
)
from seven2one.questra.data.operations.rest_timeseries import TimeSeriesOperations


@pytest.mark.unit
class TestTimeSeriesOperationsGetData:
    """Tests für get_data() Methode."""

    def test_get_data_basic(
        self, mock_rest_get, mock_rest_post, rest_timeseries_get_data_success
    ):
        """Test get_data with minimalen Parametern."""
        # Setup Mock
        mock_rest_get.return_value = rest_timeseries_get_data_success

        # Test
        ts_ops = TimeSeriesOperations(mock_rest_get, mock_rest_post)
        result = ts_ops.get_data(
            time_series_ids=[123, 456],
            from_time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            to_time=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        )

        # Assertions - Response validieren
        assert result.data is not None
        assert len(result.data) == 2

        # Erste TimeSeries validieren
        ts1 = result.data[0]
        assert ts1.time_series_id == 638301245488316416
        assert ts1.interval is not None
        assert ts1.interval.time_unit == TimeUnit.MINUTE
        assert ts1.interval.multiplier == 15
        assert ts1.unit == "°C"
        assert ts1.time_zone == "Europe/Berlin"
        assert ts1.values is not None
        assert len(ts1.values) == 3

        # Werte validieren
        assert ts1.values[0].value == 21.5
        assert ts1.values[0].quality == Quality.VALID
        assert ts1.values[1].value == 22.0
        assert ts1.values[2].value == 21.8

        # Zweite TimeSeries validieren
        ts2 = result.data[1]
        assert ts2.time_series_id == 638301245496705024
        assert ts2.interval is not None
        assert ts2.interval.time_unit == TimeUnit.HOUR
        assert ts2.unit == "kWh"
        assert ts2.values is not None
        assert len(ts2.values) == 2

        # REST GET was korrekt aufgerufen
        mock_rest_get.assert_called_once()
        call_args = mock_rest_get.call_args

        assert call_args[0][0] == "/timeseries/data"
        params = call_args[1]["params"]
        assert params["timeSeriesIds"] == ["123", "456"]
        assert "2025-01-15T10:00:00" in params["from"]
        assert "2025-01-15T12:00:00" in params["to"]

    def test_get_data_with_aggregation(
        self, mock_rest_get, mock_rest_post, rest_timeseries_get_data_success
    ):
        """Test get_data with Intervall-Aggregation."""
        mock_rest_get.return_value = rest_timeseries_get_data_success

        ts_ops = TimeSeriesOperations(mock_rest_get, mock_rest_post)
        result = ts_ops.get_data(
            time_series_ids=[123],
            from_time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            to_time=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            time_unit=TimeUnit.HOUR,
            multiplier=1,
            aggregation=Aggregation.AVERAGE,
        )

        assert result.data is not None

        # Prüfe Parameter
        call_args = mock_rest_get.call_args
        params = call_args[1]["params"]
        assert params["timeUnit"] == "HOUR"
        assert params["multiplier"] == 1
        assert params["aggregation"] == "AVERAGE"

    def test_get_data_with_unit_conversion(
        self, mock_rest_get, mock_rest_post, rest_timeseries_get_data_success
    ):
        """Test get_data with Unit-Konvertierung."""
        mock_rest_get.return_value = rest_timeseries_get_data_success

        ts_ops = TimeSeriesOperations(mock_rest_get, mock_rest_post)
        result = ts_ops.get_data(
            time_series_ids=[123],
            from_time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            to_time=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            unit="°F",
            time_zone="America/New_York",
        )

        assert result.data is not None

        # Prüfe Parameter
        call_args = mock_rest_get.call_args
        params = call_args[1]["params"]
        assert params["unit"] == "°F"
        assert params["timeZone"] == "America/New_York"

    def test_get_data_with_quotation(
        self, mock_rest_get, mock_rest_post, rest_timeseries_get_data_success
    ):
        """Test get_data with Quotierung."""
        mock_rest_get.return_value = rest_timeseries_get_data_success

        ts_ops = TimeSeriesOperations(mock_rest_get, mock_rest_post)
        quotation_time = datetime(2025, 1, 15, 0, 0, 0, tzinfo=timezone.utc)

        result = ts_ops.get_data(
            time_series_ids=[123],
            from_time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            to_time=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            quotation_time=quotation_time,
            quotation_exactly_at=True,
            quotation_behavior=QuotationBehavior.LATEST_EXACTLY_AT,
        )

        assert result.data is not None

        # Prüfe Parameter
        call_args = mock_rest_get.call_args
        params = call_args[1]["params"]
        assert "quotationTime" in params
        assert params["quotationExactlyAt"] is True
        assert params["quotationBehavior"] == "LATEST_EXACTLY_AT"

    def test_get_data_with_exclude_qualities(
        self, mock_rest_get, mock_rest_post, rest_timeseries_get_data_with_missing
    ):
        """Test get_data with ausgeschlossenen Qualitäten."""
        mock_rest_get.return_value = rest_timeseries_get_data_with_missing

        ts_ops = TimeSeriesOperations(mock_rest_get, mock_rest_post)
        result = ts_ops.get_data(
            time_series_ids=[789],
            from_time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            to_time=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            exclude_qualities=[Quality.MISSING, Quality.FAULTY],
        )

        assert result.data is not None

        # Prüfe Parameter
        call_args = mock_rest_get.call_args
        params = call_args[1]["params"]
        assert params["excludeQualities"] == ["MISSING", "FAULTY"]

    def test_get_data_payload_validation(
        self, mock_rest_get, mock_rest_post, rest_timeseries_get_data_success
    ):
        """Test get_data - validiere Response Payload gegen Schema."""
        mock_rest_get.return_value = rest_timeseries_get_data_success

        ts_ops = TimeSeriesOperations(mock_rest_get, mock_rest_post)
        ts_ops.get_data(
            time_series_ids=[123],
            from_time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            to_time=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        )

        # Validiere Response Payload
        response = mock_rest_get.return_value
        validation = RestPayloadValidator.validate_timeseries_data_payload(response)

        assert validation["valid"] is True, (
            f"Payload-Validierung fehlgeschlagen: {validation['errors']}"
        )


@pytest.mark.unit
class TestTimeSeriesOperationsSetData:
    """Tests für set_data() Methode."""

    def test_set_data_single_timeseries(self, mock_rest_get, mock_rest_post):
        """Test set_data with einer TimeSeries."""
        from seven2one.questra.data.models.rest import SetTimeSeriesDataInput
        from seven2one.questra.data.models.timeseries import TimeSeriesValue

        ts_ops = TimeSeriesOperations(mock_rest_get, mock_rest_post)

        data_input = SetTimeSeriesDataInput(  # type: ignore[call-arg]
            timeSeriesId=123,
            values=[
                TimeSeriesValue(
                    time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
                    value=21.5,
                    quality=Quality.VALID,
                ),
                TimeSeriesValue(
                    time=datetime(2025, 1, 15, 10, 15, 0, tzinfo=timezone.utc),
                    value=22.0,
                    quality=Quality.VALID,
                ),
            ],
        )

        ts_ops.set_data([data_input])

        # Prüfe POST Call
        mock_rest_post.assert_called_once()
        call_args = mock_rest_post.call_args

        assert call_args[0][0] == "/timeseries/data"
        payload = call_args[1]["json"]

        # Validiere Payload
        validation = RestPayloadValidator.validate_set_timeseries_data_input(payload)
        assert validation["valid"] is True, (
            f"Payload-Validierung fehlgeschlagen: {validation['errors']}"
        )

        # Prüfe Payload-Struktur
        assert len(payload) == 1
        assert payload[0]["timeSeriesId"] == "123"  # Wird as string serialisiert
        assert len(payload[0]["values"]) == 2
        assert payload[0]["values"][0]["value"] == 21.5
        assert payload[0]["values"][0]["quality"] == "VALID"

    def test_set_data_multiple_timeseries(self, mock_rest_get, mock_rest_post):
        """Test set_data with mehreren TimeSeries."""
        from seven2one.questra.data.models.rest import SetTimeSeriesDataInput
        from seven2one.questra.data.models.timeseries import TimeSeriesValue

        ts_ops = TimeSeriesOperations(mock_rest_get, mock_rest_post)

        data_inputs = [
            SetTimeSeriesDataInput(  # type: ignore[call-arg]
                timeSeriesId=123,
                values=[
                    TimeSeriesValue(
                        time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
                        value=21.5,
                    ),
                ],
            ),
            SetTimeSeriesDataInput(  # type: ignore[call-arg]
                timeSeriesId=456,
                values=[
                    TimeSeriesValue(
                        time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
                        value=150.5,
                    ),
                ],
                interval=Interval(timeUnit=TimeUnit.HOUR, multiplier=1),  # type: ignore[call-arg]
                unit="kWh",
            ),
        ]

        ts_ops.set_data(data_inputs)

        # Prüfe POST Call
        call_args = mock_rest_post.call_args
        payload = call_args[1]["json"]

        # Validiere Payload
        validation = RestPayloadValidator.validate_set_timeseries_data_input(payload)
        assert validation["valid"] is True

        # Prüfe Payload-Struktur
        assert len(payload) == 2
        assert payload[0]["timeSeriesId"] == "123"  # Wird as string serialisiert
        assert payload[1]["timeSeriesId"] == "456"  # Wird as string serialisiert
        assert payload[1]["interval"]["timeUnit"] == "HOUR"
        assert payload[1]["unit"] == "kWh"

    def test_set_data_with_quotation(self, mock_rest_get, mock_rest_post):
        """Test set_data with Quotierung."""
        from seven2one.questra.data.models.rest import SetTimeSeriesDataInput
        from seven2one.questra.data.models.timeseries import TimeSeriesValue

        ts_ops = TimeSeriesOperations(mock_rest_get, mock_rest_post)

        quotation_time = datetime(2025, 1, 15, 0, 0, 0, tzinfo=timezone.utc)

        data_input = SetTimeSeriesDataInput(  # type: ignore[call-arg]
            timeSeriesId="123",
            values=[
                TimeSeriesValue(
                    time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
                    value=21.5,
                ),
            ],
            quotationTime=quotation_time,
        )

        ts_ops.set_data([data_input])

        # Prüfe POST Call
        call_args = mock_rest_post.call_args
        payload = call_args[1]["json"]

        assert "quotationTime" in payload[0]


@pytest.mark.unit
class TestTimeSeriesOperationsGetQuotations:
    """Tests für get_quotations() Methode."""

    def test_get_quotations_basic(
        self, mock_rest_get, mock_rest_post, rest_timeseries_get_quotations_success
    ):
        """Test get_quotations - einzelne Zeitreihe."""
        mock_rest_get.return_value = rest_timeseries_get_quotations_success

        ts_ops = TimeSeriesOperations(mock_rest_get, mock_rest_post)
        result = ts_ops.get_quotations(
            time_series_ids=[123],
            from_time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            to_time=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        )

        # Assertions
        assert result.items is not None
        assert len(result.items) == 1

        # Quotierung validieren
        quot = result.items[0]
        assert quot.time_series_id == 643076700854632448
        assert quot.values is not None
        assert len(quot.values) == 3

        # Werte validieren
        assert quot.values[0].time.year == 2025
        assert quot.values[0].from_.year == 2025
        assert quot.values[0].to.year == 2025

        # REST GET was korrekt aufgerufen
        mock_rest_get.assert_called_once()
        call_args = mock_rest_get.call_args

        assert call_args[0][0] == "/timeseries/quotations"
        params = call_args[1]["params"]
        assert params["timeSeriesIds"] == ["123"]
        assert params["aggregated"] is False

    def test_get_quotations_aggregated(
        self, mock_rest_get, mock_rest_post, rest_timeseries_get_quotations_success
    ):
        """Test get_quotations with Aggregation."""
        mock_rest_get.return_value = rest_timeseries_get_quotations_success

        ts_ops = TimeSeriesOperations(mock_rest_get, mock_rest_post)
        result = ts_ops.get_quotations(
            time_series_ids=[123],
            from_time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            to_time=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            aggregated=True,
        )

        assert result.items is not None

        # Prüfe Parameter
        call_args = mock_rest_get.call_args
        params = call_args[1]["params"]
        assert params["aggregated"] is True

    def test_get_quotations_multiple(
        self,
        mock_rest_get,
        mock_rest_post,
        rest_timeseries_get_quotations_multiple_success,
    ):
        """Test get_quotations - mehrere Zeitreihen (NDJSON)."""
        mock_rest_get.return_value = rest_timeseries_get_quotations_multiple_success

        ts_ops = TimeSeriesOperations(mock_rest_get, mock_rest_post)
        result = ts_ops.get_quotations(
            time_series_ids=[123, 456],
            from_time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            to_time=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        )

        # Assertions - mehrere Zeitreihen
        assert result.items is not None
        assert len(result.items) == 2

        # Erste Quotierung
        quot1 = result.items[0]
        assert quot1.time_series_id == 643076700854632448
        assert quot1.values is not None
        assert len(quot1.values) == 3

        # Zweite Quotierung
        quot2 = result.items[1]
        assert quot2.time_series_id == 643076700867215360
        assert quot2.values is not None
        assert len(quot2.values) == 3

        # REST GET was korrekt aufgerufen
        mock_rest_get.assert_called_once()
        call_args = mock_rest_get.call_args

        assert call_args[0][0] == "/timeseries/quotations"
        params = call_args[1]["params"]
        assert params["timeSeriesIds"] == ["123", "456"]
        assert params["aggregated"] is False

    def test_get_quotations_payload_validation(
        self, mock_rest_get, mock_rest_post, rest_timeseries_get_quotations_success
    ):
        """Test get_quotations - validiere Response Payload gegen Schema."""
        mock_rest_get.return_value = rest_timeseries_get_quotations_success

        ts_ops = TimeSeriesOperations(mock_rest_get, mock_rest_post)
        ts_ops.get_quotations(
            time_series_ids=[123],
            from_time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            to_time=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        )

        # Validiere Response Payload (einzelnes Objekt -> in Liste wrappen)
        response = mock_rest_get.return_value
        payload = response if isinstance(response, list) else [response]
        validation = RestPayloadValidator.validate_quotations_payload(payload)

        assert validation["valid"] is True, (
            f"Payload-Validierung fehlgeschlagen: {validation['errors']}"
        )


@pytest.mark.unit
class TestTimeSeriesOperationsErrorHandling:
    """Tests für Error-Handling at REST-Requests."""

    def test_get_data_unknown_timeseries_error_response(
        self, mock_rest_get, mock_rest_post, rest_timeseries_error_unknown
    ):
        """Test get_data - dokumentiert Error Response at unbekannten TimeSeries IDs.

        Dieser Test dokumentiert die Error Response Structure, die vom Server
        zurückgegeben wird, wenn unbekannte TimeSeries IDs angegeben werden.

        In der Produktiv-Umgebung würde der RESTTransport eine Exception werfen,
        aber in Unit Tests mocken wir only die Response-Struktur.
        """
        # Dieser Test dokumentiert die Error-Response-Struktur
        error_response = rest_timeseries_error_unknown

        # Validiere Error Response Struktur
        assert "errors" in error_response
        assert len(error_response["errors"]) == 1

        error = error_response["errors"][0]
        assert "message" in error
        assert "Unknown time series" in error["message"]

        # Extensions validieren
        assert "extensions" in error
        assert error["extensions"]["code"] == "TIME_SERIES_UNKNOWN_TIME_SERIES"
        assert "placeholders" in error["extensions"]
        assert "TimeSeriesIds" in error["extensions"]["placeholders"]

    def test_get_quotations_no_quotation_error_response(
        self,
        mock_rest_get,
        mock_rest_post,
        rest_timeseries_quotations_error_no_quotation,
    ):
        """Test get_quotations - dokumentiert Error Response wenn Quotierung nicht aktiviert.

        Dieser Test dokumentiert die Error Response Structure, die vom Server
        zurückgegeben wird, wenn eine TimeSeries keine Quotierung aktiviert hat.
        """
        # Dieser Test dokumentiert die Error-Response-Struktur
        error_response = rest_timeseries_quotations_error_no_quotation

        # Validiere Error Response Struktur
        assert "errors" in error_response
        assert len(error_response["errors"]) == 1

        error = error_response["errors"][0]
        assert "message" in error
        assert "has no quotation" in error["message"]

        # Extensions validieren
        assert "extensions" in error
        assert error["extensions"]["code"] == "TIME_SERIES_TIME_SERIES_HAS_NO_QUOTATION"
        assert "placeholders" in error["extensions"]
        assert "TimeSeriesId" in error["extensions"]["placeholders"]
