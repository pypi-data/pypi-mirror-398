"""
Unit-Tests für AuditOperations (REST API).

Testet Audit-Endpoints with gemockten HTTP-Responses
und Payload-Validierung gegen Swagger Schema.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from helpers.rest_validators import RestPayloadValidator

from seven2one.questra.data.models.timeseries import (
    Aggregation,
    Quality,
    QuotationBehavior,
    TimeUnit,
    ValueAlignment,
    ValueAvailability,
)
from seven2one.questra.data.operations.rest_audit import AuditOperations


@pytest.mark.unit
class TestAuditOperationsGetFile:
    """Tests für get_file() Methode."""

    def test_get_file_basic(self, mock_rest_get):
        """Test get_file - erfolgreich."""
        # Setup Mock - binäre Audit-Datei simulieren
        file_content = b"Audit file content - historical version"
        mock_rest_get.return_value = file_content

        # Test
        audit_ops = AuditOperations(mock_rest_get)
        result = audit_ops.get_file(file_id=12345)

        # Assertions
        assert result == file_content
        assert isinstance(result, bytes)

        # REST GET was korrekt aufgerufen
        mock_rest_get.assert_called_once()
        call_args = mock_rest_get.call_args

        assert call_args[0][0] == "/audit/file"
        params = call_args[1]["params"]
        assert params["fileId"] == 12345

    def test_get_file_empty(self, mock_rest_get):
        """Test get_file - leere Datei."""
        mock_rest_get.return_value = b""

        audit_ops = AuditOperations(mock_rest_get)
        result = audit_ops.get_file(file_id=999)

        assert result == b""


@pytest.mark.unit
class TestAuditOperationsGetTimeSeries:
    """Tests für get_timeseries() Methode (Metadaten)."""

    def test_get_timeseries_basic(
        self, mock_rest_get, rest_audit_get_timeseries_success
    ):
        """Test get_timeseries - erfolgreich."""
        mock_rest_get.return_value = rest_audit_get_timeseries_success

        audit_ops = AuditOperations(mock_rest_get)
        result = audit_ops.get_timeseries(time_series_id=123)

        # Assertions - Metadaten validieren
        assert result.id == 123
        assert str(result.created_by) == "00000000-0000-0000-0000-000000000001"
        assert str(result.altered_by) == "00000000-0000-0000-0000-000000000002"
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.altered_at, datetime)

        # Interval validieren
        assert result.interval.time_unit == TimeUnit.MINUTE
        assert result.interval.multiplier == 15

        # Enums validieren
        assert result.value_alignment == ValueAlignment.LEFT
        assert result.value_availability == ValueAvailability.AT_INTERVAL_BEGIN
        assert result.default_aggregation == Aggregation.AVERAGE

        # Optionale Felder
        assert result.unit == "°C"
        assert result.time_zone == "Europe/Berlin"

        # Flags
        assert result.audit_enabled is True
        assert result.quotation_enabled is False
        assert result.default_quotation_behavior == QuotationBehavior.LATEST

        # REST GET was korrekt aufgerufen
        mock_rest_get.assert_called_once()
        call_args = mock_rest_get.call_args

        assert call_args[0][0] == "/audit/timeseries"
        params = call_args[1]["params"]
        assert params["timeSeriesId"] == 123

        # Payload validieren
        validation = RestPayloadValidator.validate_timeseries_payload(
            mock_rest_get.return_value
        )
        assert validation["valid"] is True, (
            f"Payload-Validierung fehlgeschlagen: {validation['errors']}"
        )


@pytest.mark.unit
class TestAuditOperationsGetTimeSeriesData:
    """Tests für get_timeseries_data() Methode (Audit-Daten)."""

    def test_get_timeseries_data_basic(
        self, mock_rest_get, rest_audit_get_timeseries_data_success
    ):
        """Test get_timeseries_data - minimale Parameter."""
        mock_rest_get.return_value = rest_audit_get_timeseries_data_success

        audit_ops = AuditOperations(mock_rest_get)
        result = audit_ops.get_timeseries_data(
            time_series_id=123,
            from_time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            to_time=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            audit_time=datetime(2025, 1, 14, 20, 0, 0, tzinfo=timezone.utc),
        )

        # Assertions
        assert result.data is not None
        assert len(result.data) == 1

        ts_data = result.data[0]
        assert ts_data.time_series_id == 123
        assert ts_data.interval is not None
        assert ts_data.interval.time_unit == TimeUnit.MINUTE
        assert ts_data.interval.multiplier == 15
        assert ts_data.unit == "°C"
        assert ts_data.time_zone == "Europe/Berlin"
        assert ts_data.values is not None
        assert len(ts_data.values) == 2

        # Werte validieren
        assert ts_data.values[0].value == 20.5
        assert ts_data.values[0].quality == Quality.VALID
        assert ts_data.values[1].value == 20.8

        # REST GET was korrekt aufgerufen
        mock_rest_get.assert_called_once()
        call_args = mock_rest_get.call_args

        assert call_args[0][0] == "/audit/timeseries/data"
        params = call_args[1]["params"]
        assert params["timeSeriesId"] == 123
        assert "2025-01-15T10:00:00" in params["from"]
        assert "2025-01-15T12:00:00" in params["to"]
        assert "2025-01-14T20:00:00" in params["auditTime"]
        assert params["auditExactlyAt"] is False
        assert params["quotationExactlyAt"] is False

    def test_get_timeseries_data_exact_audit_time(
        self, mock_rest_get, rest_audit_get_timeseries_data_success
    ):
        """Test get_timeseries_data - with auditExactlyAt=True."""
        mock_rest_get.return_value = rest_audit_get_timeseries_data_success

        audit_ops = AuditOperations(mock_rest_get)
        result = audit_ops.get_timeseries_data(
            time_series_id=123,
            from_time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            to_time=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            audit_time=datetime(2025, 1, 14, 20, 0, 0, tzinfo=timezone.utc),
            audit_exactly_at=True,
        )

        assert result.data is not None

        # Prüfe Parameter
        call_args = mock_rest_get.call_args
        params = call_args[1]["params"]
        assert params["auditExactlyAt"] is True

    def test_get_timeseries_data_with_quotation(
        self, mock_rest_get, rest_audit_get_timeseries_data_success
    ):
        """Test get_timeseries_data - with Quotierung."""
        mock_rest_get.return_value = rest_audit_get_timeseries_data_success

        audit_ops = AuditOperations(mock_rest_get)
        quotation_time = datetime(2025, 1, 14, 0, 0, 0, tzinfo=timezone.utc)

        result = audit_ops.get_timeseries_data(
            time_series_id=123,
            from_time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            to_time=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            audit_time=datetime(2025, 1, 14, 20, 0, 0, tzinfo=timezone.utc),
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

    def test_get_timeseries_data_with_exclude_qualities(
        self, mock_rest_get, rest_audit_get_timeseries_data_success
    ):
        """Test get_timeseries_data - with ausgeschlossenen Qualitäten."""
        mock_rest_get.return_value = rest_audit_get_timeseries_data_success

        audit_ops = AuditOperations(mock_rest_get)
        result = audit_ops.get_timeseries_data(
            time_series_id=123,
            from_time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            to_time=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            audit_time=datetime(2025, 1, 14, 20, 0, 0, tzinfo=timezone.utc),
            exclude_qualities=[Quality.MISSING, Quality.FAULTY],
        )

        assert result.data is not None

        # Prüfe Parameter
        call_args = mock_rest_get.call_args
        params = call_args[1]["params"]
        assert params["excludeQualities"] == ["MISSING", "FAULTY"]

    def test_get_timeseries_data_payload_validation(
        self, mock_rest_get, rest_audit_get_timeseries_data_success
    ):
        """Test get_timeseries_data - validiere Response Payload."""
        mock_rest_get.return_value = rest_audit_get_timeseries_data_success

        audit_ops = AuditOperations(mock_rest_get)
        audit_ops.get_timeseries_data(
            time_series_id=123,
            from_time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            to_time=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            audit_time=datetime(2025, 1, 14, 20, 0, 0, tzinfo=timezone.utc),
        )

        # Validiere Response Payload (einzelnes Objekt -> in Liste wrappen)
        response = mock_rest_get.return_value
        payload = response if isinstance(response, list) else [response]
        validation = RestPayloadValidator.validate_timeseries_data_payload(payload)

        assert validation["valid"] is True, (
            f"Payload-Validierung fehlgeschlagen: {validation['errors']}"
        )

    def test_get_timeseries_data_multiple(
        self, mock_rest_get, rest_audit_get_timeseries_data_multiple_success
    ):
        """Test get_timeseries_data - mehrere TimeSeries (NDJSON)."""
        mock_rest_get.return_value = rest_audit_get_timeseries_data_multiple_success

        audit_ops = AuditOperations(mock_rest_get)
        result = audit_ops.get_timeseries_data(
            time_series_id=123,
            from_time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            to_time=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            audit_time=datetime(2025, 1, 14, 20, 0, 0, tzinfo=timezone.utc),
        )

        # Assertions - mehrere TimeSeries
        assert result.data is not None
        assert len(result.data) == 2

        # Erste TimeSeries
        ts1 = result.data[0]
        assert ts1.time_series_id == 123
        assert ts1.interval is not None
        assert ts1.interval.time_unit == TimeUnit.MINUTE
        assert ts1.interval.multiplier == 15
        assert ts1.unit == "°C"
        assert ts1.values is not None
        assert len(ts1.values) == 2

        # Zweite TimeSeries
        ts2 = result.data[1]
        assert ts2.time_series_id == 456
        assert ts2.interval is not None
        assert ts2.interval.time_unit == TimeUnit.HOUR
        assert ts2.interval.multiplier == 1
        assert ts2.unit == "kWh"
        assert ts2.values is not None
        assert len(ts2.values) == 1
