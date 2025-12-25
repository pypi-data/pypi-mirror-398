"""
Validation Helfer für REST-API Tests.

Validiert POST/GET Payloads gegen das Swagger/OpenAPI Schema.
"""

from __future__ import annotations

from typing import Any


class RestPayloadValidator:
    """
    Validiert REST-API Request/Response Payloads.

    Prüft Payloads gegen das Swagger/OpenAPI Schema (schemas/swagger.json).
    """

    # Erlaubte TimeUnitvalues (aus Schema)
    VALID_TIME_UNITS = {
        "MICROSECOND",
        "MILLISECOND",
        "SECOND",
        "MINUTE",
        "HOUR",
        "DAY",
        "WEEK",
        "MONTH",
        "QUARTER",
        "YEAR",
    }

    # Erlaubte Qualityvalues (aus models/timeseries.py)
    VALID_QUALITIES = {
        "NO_VALUE",
        "MANUALLY_REPLACED",
        "FAULTY",
        "VALID",
        "SCHEDULE",
        "MISSING",
        "ACCOUNTED",
        "ESTIMATED",
        "INTERPOLATED",
    }

    # Erlaubte Aggregationvalues (aus models/timeseries.py)
    VALID_AGGREGATIONS = {
        "SUM",
        "AVERAGE",
        "MIN",
        "MAX",
        "MOST_FREQUENTLY",
        "ABS_MIN",
        "ABS_MAX",
        "FIRST_VALUE",
        "LAST_VALUE",
    }

    # Erlaubte QuotationBehaviorvalues
    VALID_QUOTATION_BEHAVIORS = {
        "LATEST_EXACTLY_AT",
        "LATEST",
        "LATEST_NO_FUTURE",
    }

    # Erlaubte ValueAlignmentvalues
    VALID_VALUE_ALIGNMENTS = {
        "LEFT",
        "RIGHT",
        "NONE",
    }

    # Erlaubte ValueAvailabilityvalues
    VALID_VALUE_AVAILABILITIES = {
        "AT_INTERVAL_BEGIN",
        "AT_INTERVAL_END",
    }

    @classmethod
    def validate_timeseries_data_payload(
        cls, payload: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Validiert TimeSeriesData NDJSON Response (GET /timeseries/data Response).

        Args:
            payload: Response-Payload (list of TimeSeriesData-Objekten)

        Returns:
            dict with Validierungsergebnis:
                - valid: bool
                - errors: list[str]
                - warnings: list[str]

        Examples:
            >>> payload = [{"timeSeriesId": 123, "interval": {...}, ...}]
            >>> result = RestPayloadValidator.validate_timeseries_data_payload(payload)
            >>> result["valid"]
            True
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Prüfe Root-Struktur (NDJSON = liste of Objekten)
        if not isinstance(payload, list):
            errors.append("Payload muss eine Liste sein (NDJSON)")
            return {"valid": False, "errors": errors, "warnings": warnings}

        # Validiere jedes TimeSeriesData-Objekt
        for idx, ts_data in enumerate(payload):
            if not isinstance(ts_data, dict):
                errors.append(f"payload[{idx}] muss ein dict sein")
                continue

            # Prüfe auf ErrorsPayload
            if "errors" in ts_data:
                errors.append(
                    f"payload[{idx}] ist ErrorsPayload: {ts_data.get('errors')}"
                )
                continue

            # timeSeriesId (required)
            if "timeSeriesId" not in ts_data:
                errors.append(f"payload[{idx}] fehlt 'timeSeriesId'")
            elif not isinstance(ts_data["timeSeriesId"], str):
                errors.append(
                    f"payload[{idx}].timeSeriesId muss str (LongNumberString) sein, ist {type(ts_data['timeSeriesId'])}"
                )

            # interval (required)
            if "interval" not in ts_data:
                errors.append(f"payload[{idx}] fehlt 'interval'")
            else:
                interval_errors = cls._validate_interval(
                    ts_data["interval"], f"payload[{idx}].interval"
                )
                errors.extend(interval_errors)

            # values (required)
            if "values" not in ts_data:
                errors.append(f"payload[{idx}] fehlt 'values'")
            else:
                values_errors = cls._validate_timeseries_values(
                    ts_data["values"], f"payload[{idx}].values"
                )
                errors.extend(values_errors)

            # unit (optional)
            if "unit" in ts_data and ts_data["unit"] is not None:
                if not isinstance(ts_data["unit"], str):
                    errors.append(f"payload[{idx}].unit muss string sein")

            # timeZone (optional)
            if "timeZone" in ts_data and ts_data["timeZone"] is not None:
                if not isinstance(ts_data["timeZone"], str):
                    errors.append(f"payload[{idx}].timeZone muss string sein")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    @classmethod
    def validate_set_timeseries_data_input(
        cls, payload: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Validiert POST /timeseries/data Payload (SetTimeSeriesDataInput[]).

        Args:
            payload: Liste of SetTimeSeriesDataInput-Objekten

        Returns:
            dict with Validierungsergebnis
        """
        errors: list[str] = []
        warnings: list[str] = []

        if not isinstance(payload, list):
            errors.append("Payload muss eine Liste sein")
            return {"valid": False, "errors": errors, "warnings": warnings}

        for idx, item in enumerate(payload):
            if not isinstance(item, dict):
                errors.append(f"payload[{idx}] muss ein dict sein")
                continue

            # timeSeriesId (required)
            if "timeSeriesId" not in item:
                errors.append(f"payload[{idx}] fehlt 'timeSeriesId'")
            elif not isinstance(item["timeSeriesId"], str):
                errors.append(
                    f"payload[{idx}].timeSeriesId muss str (LongNumberString) sein, ist {type(item['timeSeriesId'])}"
                )

            # values (required)
            if "values" not in item:
                errors.append(f"payload[{idx}] fehlt 'values'")
            else:
                values_errors = cls._validate_timeseries_values(
                    item["values"], f"payload[{idx}].values"
                )
                errors.extend(values_errors)

            # interval (optional)
            if "interval" in item and item["interval"] is not None:
                interval_errors = cls._validate_interval(
                    item["interval"], f"payload[{idx}].interval"
                )
                errors.extend(interval_errors)

            # unit (optional)
            if "unit" in item and item["unit"] is not None:
                if not isinstance(item["unit"], str):
                    errors.append(f"payload[{idx}].unit muss string sein")

            # timeZone (optional)
            if "timeZone" in item and item["timeZone"] is not None:
                if not isinstance(item["timeZone"], str):
                    errors.append(f"payload[{idx}].timeZone muss string sein")

            # quotationTime (optional)
            if "quotationTime" in item and item["quotationTime"] is not None:
                if not isinstance(item["quotationTime"], str):
                    errors.append(
                        f"payload[{idx}].quotationTime muss string (ISO format) sein"
                    )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    @classmethod
    def validate_quotations_payload(
        cls, payload: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Validiert Quotations NDJSON Response (GET /timeseries/quotations Response).

        Args:
            payload: Response-Payload (list of Quotations-Objekten)

        Returns:
            dict with Validierungsergebnis
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Prüfe Root-Struktur (NDJSON = liste of Objekten)
        if not isinstance(payload, list):
            errors.append("Payload muss eine Liste sein (NDJSON)")
            return {"valid": False, "errors": errors, "warnings": warnings}

        # Validiere jedes Quotation-Objekt
        for idx, quot in enumerate(payload):
            if not isinstance(quot, dict):
                errors.append(f"payload[{idx}] muss ein dict sein")
                continue

            # Prüfe auf ErrorsPayload
            if "errors" in quot:
                errors.append(f"payload[{idx}] ist ErrorsPayload: {quot.get('errors')}")
                continue

            # timeSeriesId (required)
            if "timeSeriesId" not in quot:
                errors.append(f"payload[{idx}] fehlt 'timeSeriesId'")
            elif not isinstance(quot["timeSeriesId"], str):
                errors.append(
                    f"payload[{idx}].timeSeriesId muss str (LongNumberString) sein"
                )

            # values (required)
            if "values" not in quot:
                errors.append(f"payload[{idx}] fehlt 'values'")
            elif not isinstance(quot["values"], list):
                errors.append(f"payload[{idx}].values muss eine Liste sein")
            else:
                for val_idx, val in enumerate(quot["values"]):
                    if not isinstance(val, dict):
                        errors.append(
                            f"payload[{idx}].values[{val_idx}] muss ein dict sein"
                        )
                        continue

                    # time, from, to (all required)
                    for field in ["time", "from", "to"]:
                        if field not in val:
                            errors.append(
                                f"payload[{idx}].values[{val_idx}] fehlt '{field}'"
                            )
                        elif not isinstance(val[field], str):
                            errors.append(
                                f"payload[{idx}].values[{val_idx}].{field} muss string (ISO format) sein"
                            )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    @classmethod
    def validate_file_upload_response(
        cls, payload: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Validiert File Upload Response (POST /file/upload).

        Args:
            payload: Liste of File-Objekten

        Returns:
            dict with Validierungsergebnis
        """
        errors: list[str] = []
        warnings: list[str] = []

        if not isinstance(payload, list):
            errors.append("Payload muss eine Liste sein")
            return {"valid": False, "errors": errors, "warnings": warnings}

        # Validiere jedes File-Objekt
        for idx, file_obj in enumerate(payload):
            if not isinstance(file_obj, dict):
                errors.append(f"payload[{idx}] muss ein dict sein")
                continue

            # Pflichtfelder
            required_fields = {
                "id": str,  # LongNumberString
                "createdBy": str,
                "createdAt": str,
                "size": int,  # LongNumberString converted to int
                "inventoryPropertyId": str,  # LongNumberString
                "storageDeleteAttempts": int,  # IntNumberString converted to int
                "auditEnabled": bool,
            }

            for field, expected_type in required_fields.items():
                if field not in file_obj:
                    errors.append(f"payload[{idx}] fehlt '{field}'")
                elif not isinstance(file_obj[field], expected_type):
                    errors.append(
                        f"payload[{idx}].{field} muss {expected_type.__name__} sein"
                    )

            # Optionale Felder
            optional_fields = {
                "name": (str, type(None)),
                "mediaType": (str, type(None)),
                "charset": (str, type(None)),
                "hashAlgorithm": (str, type(None)),
                "hashBase64": (str, type(None)),
                "inventoryItemId": (str, type(None)),  # LongNumberString
                "deletedAt": (str, type(None)),
            }

            for field, expected_types in optional_fields.items():
                if field in file_obj:
                    if not isinstance(file_obj[field], expected_types):
                        errors.append(
                            f"payload[{idx}].{field} hat falschen Typ: {type(file_obj[field])}"
                        )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    @classmethod
    def validate_timeseries_payload(cls, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Validiert TimeSeriesPayload (GET /audit/timeseries Response).

        Args:
            payload: Response-Payload (dict)

        Returns:
            dict with Validierungsergebnis
        """
        errors: list[str] = []
        warnings: list[str] = []

        if not isinstance(payload, dict):
            errors.append("Payload muss ein dict sein")
            return {"valid": False, "errors": errors, "warnings": warnings}

        # Pflichtfelder
        required_fields = {
            "id": (int, str),
            "createdBy": str,
            "createdAt": str,
            "alteredBy": str,
            "alteredAt": str,
            "valueAlignment": str,
            "valueAvailability": str,
            "defaultAggregation": str,
            "startOfTime": str,
            "auditEnabled": bool,
            "quotationEnabled": bool,
            "defaultQuotationBehavior": str,
        }

        for field, expected_type in required_fields.items():
            if field not in payload:
                errors.append(f"Payload fehlt '{field}'")
            elif not isinstance(payload[field], expected_type):
                errors.append(f"{field} muss {expected_type.__name__} sein")

        # interval (required)
        if "interval" not in payload:
            errors.append("Payload fehlt 'interval'")
        else:
            interval_errors = cls._validate_interval(payload["interval"], "interval")
            errors.extend(interval_errors)

        # Enum-Validierung
        if "valueAlignment" in payload:
            if payload["valueAlignment"] not in cls.VALID_VALUE_ALIGNMENTS:
                errors.append(
                    f"valueAlignment '{payload['valueAlignment']}' ist ungültig"
                )

        if "valueAvailability" in payload:
            if payload["valueAvailability"] not in cls.VALID_VALUE_AVAILABILITIES:
                errors.append(
                    f"valueAvailability '{payload['valueAvailability']}' ist ungültig"
                )

        if "defaultAggregation" in payload:
            if payload["defaultAggregation"] not in cls.VALID_AGGREGATIONS:
                errors.append(
                    f"defaultAggregation '{payload['defaultAggregation']}' ist ungültig"
                )

        if "defaultQuotationBehavior" in payload:
            if payload["defaultQuotationBehavior"] not in cls.VALID_QUOTATION_BEHAVIORS:
                errors.append(
                    f"defaultQuotationBehavior '{payload['defaultQuotationBehavior']}' ist ungültig"
                )

        # Optionale Felder
        if "unit" in payload and payload["unit"] is not None:
            if not isinstance(payload["unit"], str):
                errors.append("unit muss string sein")

        if "timeZone" in payload and payload["timeZone"] is not None:
            if not isinstance(payload["timeZone"], str):
                errors.append("timeZone muss string sein")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    @classmethod
    def _validate_interval(cls, interval: Any, context: str) -> list[str]:
        """
        Validiert ein Interval-Objekt.

        Args:
            interval: Interval-Objekt (dict)
            context: Kontext für Fehlermeldungen (z.B. "data[0].interval")

        Returns:
            list[str]: Liste of Fehlermeldungen
        """
        errors: list[str] = []

        if not isinstance(interval, dict):
            errors.append(f"{context} muss ein dict sein")
            return errors

        # timeUnit (required)
        if "timeUnit" not in interval:
            errors.append(f"{context} fehlt 'timeUnit'")
        elif not isinstance(interval["timeUnit"], str):
            errors.append(f"{context}.timeUnit muss string sein")
        elif interval["timeUnit"] not in cls.VALID_TIME_UNITS:
            errors.append(f"{context}.timeUnit '{interval['timeUnit']}' ist ungültig")

        # multiplier (required)
        if "multiplier" not in interval:
            errors.append(f"{context} fehlt 'multiplier'")
        elif not isinstance(interval["multiplier"], (int, str)):
            errors.append(f"{context}.multiplier muss int or string sein")
        else:
            # Convert to int für Werteprüfung
            try:
                multiplier_val = int(interval["multiplier"])
                if multiplier_val <= 0:
                    errors.append(f"{context}.multiplier muss > 0 sein")
            except (ValueError, TypeError):
                errors.append(f"{context}.multiplier ist keine gültige Zahl")

        return errors

    @classmethod
    def _validate_timeseries_values(cls, values: Any, context: str) -> list[str]:
        """
        Validiert eine Liste of TimeSeriesValue-Objekten.

        Args:
            values: Liste of TimeSeriesValue-Objekten
            context: Kontext für Fehlermeldungen

        Returns:
            list[str]: Liste of Fehlermeldungen
        """
        errors: list[str] = []

        if not isinstance(values, list):
            errors.append(f"{context} muss eine Liste sein")
            return errors

        for idx, val in enumerate(values):
            if not isinstance(val, dict):
                errors.append(f"{context}[{idx}] muss ein dict sein")
                continue

            # time (required)
            if "time" not in val:
                errors.append(f"{context}[{idx}] fehlt 'time'")
            elif not isinstance(val["time"], str):
                errors.append(f"{context}[{idx}].time muss string (ISO format) sein")

            # value (required)
            if "value" not in val:
                errors.append(f"{context}[{idx}] fehlt 'value'")
            elif not isinstance(val["value"], (int, float, str)):
                errors.append(f"{context}[{idx}].value muss number or string sein")

            # quality (optional)
            if "quality" in val and val["quality"] is not None:
                if not isinstance(val["quality"], str):
                    errors.append(f"{context}[{idx}].quality muss string sein")
                elif val["quality"] not in cls.VALID_QUALITIES:
                    errors.append(
                        f"{context}[{idx}].quality '{val['quality']}' ist ungültig"
                    )

        return errors
