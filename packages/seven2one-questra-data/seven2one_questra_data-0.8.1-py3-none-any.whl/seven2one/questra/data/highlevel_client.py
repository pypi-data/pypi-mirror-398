"""
High-Level API for Questra Data.

Provides a simplified interface for common operations,
without the user needing to know the internal details (GraphQL vs REST).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)
from seven2one.questra.authentication import QuestraAuthentication

from .client import QuestraDataCore
from .managers import CatalogManager
from .models import (
    Aggregation,
    ConflictAction,
    DataType,
    Inventory,
    NamedItemResult,
    Namespace,
    Quality,
    QuotationBehavior,
    Role,
    SystemInfo,
    TimeUnit,
    TimeZone,
    Unit,
)
from .models.inputs import (
    BoolProperty,
    DateProperty,
    DateTimeOffsetProperty,
    DateTimeProperty,
    DecimalProperty,
    FileProperty,
    GuidProperty,
    IntProperty,
    InventoryProperty,
    InventoryRelation,
    LongProperty,
    StringProperty,
    TimeProperty,
    TimeSeriesProperty,
)
from .models.rest import SetTimeSeriesDataInput, TimeSeriesValue
from .results import QueryResult, TimeSeriesResult

# Optional pandas Integration
if TYPE_CHECKING:
    import pandas as pd

try:
    import pandas as pd

    _PANDAS_AVAILABLE = True
except ImportError:
    _PANDAS_AVAILABLE = False


class QuestraData:
    """High-level API client for Questra Data.

    Simplified interface for common operations without requiring knowledge
    of internal GraphQL vs REST implementation details.

    Args:
        graphql_url: GraphQL endpoint URL
        auth_client: Authenticated QuestraAuthentication instance
        rest_base_url: REST API base URL (auto-derived if not provided)

    Example:
        ```python
        from seven2one.questra.authentication import QuestraAuthentication
        from seven2one.questra.data import QuestraData

        auth = QuestraAuthentication(...)
        client = QuestraData(
            graphql_url="https://api.example.com/graphql", auth_client=auth
        )
        ```
    """

    def __init__(
        self,
        graphql_url: str,
        auth_client: QuestraAuthentication,
        rest_base_url: str | None = None,
    ):
        logger.info(f"Initializing QuestraData. graphql_url={graphql_url}")

        # Create QuestraDataCore client (low-level API)
        self._client = QuestraDataCore(
            graphql_url=graphql_url,
            auth_client=auth_client,
            rest_base_url=rest_base_url,
        )

        # Initialize internal managers (for code organization)
        self._catalog_manager = CatalogManager(self._client)

        logger.info("QuestraData initialized successfully")

    def _normalize_properties(
        self,
        properties: list[
            InventoryProperty
            | StringProperty
            | IntProperty
            | LongProperty
            | DecimalProperty
            | BoolProperty
            | DateTimeProperty
            | DateTimeOffsetProperty
            | DateProperty
            | TimeProperty
            | GuidProperty
            | FileProperty
            | TimeSeriesProperty
        ],
    ) -> list[InventoryProperty]:
        normalized: list[InventoryProperty] = []
        for prop in properties:
            if isinstance(prop, InventoryProperty):
                normalized.append(prop)
            else:
                # Specialized property classes all have to_inventory_property()
                normalized.append(prop.to_inventory_property())  # type: ignore[union-attr]
        return normalized

    # ===== Time Series Operations =====

    def list_timeseries_values(
        self,
        inventory_name: str,
        timeseries_properties: str | list[str],
        from_time: datetime,
        to_time: datetime,
        namespace_name: str | None = None,
        properties: list[str] | None = None,
        where: dict[str, Any] | None = None,
        aggregation: Aggregation | None = None,
        time_unit: TimeUnit | None = None,
        multiplier: int | None = None,
        exclude_qualities: list[Quality] | None = None,
        time_zone: str | None = None,
    ) -> TimeSeriesResult:
        """Retrieve time series values from inventory items.

        Args:
            inventory_name: Name of inventory
            timeseries_properties: Property name(s) containing time series
            from_time: Start timestamp
            to_time: End timestamp
            namespace_name: Optional namespace filter
            properties: Additional item properties to include
            where: Optional filter conditions
            aggregation: Optional data aggregation
            time_unit: Time interval unit for aggregation
            multiplier: Multiplier for time_unit
            exclude_qualities: Quality flags to exclude
            time_zone: Timezone for timestamps

        Returns:
            TimeSeriesResult with item and time series data
        """
        ts_properties = (
            [timeseries_properties]
            if isinstance(timeseries_properties, str)
            else timeseries_properties
        )

        logger.info(
            f"Listing timeseries values from inventory. inventory_name={inventory_name}, namespace_name={namespace_name}, timeseries_properties={ts_properties}, properties={properties}"
        )

        # Step 1: Lade Inventory Items with Timeseries properties and normal properties
        query_properties = ["_id", "_rowVersion"]

        # Collect Timeseries subfields (z.B. "messwerte_temperatur.timeZone")
        ts_subfields = {ts_prop: set() for ts_prop in ts_properties}

        # Add normal properties hinzu and sammle Timeseries subfields
        if properties:
            for prop in properties:
                # Check whether it is a nested Timeseries Property ist
                is_ts_subfield = False
                for ts_prop in ts_properties:
                    if prop.startswith(f"{ts_prop}."):
                        # Timeseries subfield found (z.B. "messwerte_temperatur.timeZone")
                        subfield = prop.split(".", 1)[1]
                        ts_subfields[ts_prop].add(subfield)
                        is_ts_subfield = True
                        break

                if not is_ts_subfield:
                    # Normal Property
                    query_properties.append(prop)

        # Add Timeseries Properties with ihren Subfeldern hinzu
        for ts_prop in ts_properties:
            # Always query .id (for time series data)
            ts_subfields[ts_prop].add("id")

            # Add all subfields as nested Properties hinzu
            for subfield in ts_subfields[ts_prop]:
                query_properties.append(f"{ts_prop}.{subfield}")

        result = self._client.inventory.list(
            inventory_name=inventory_name,
            namespace_name=namespace_name,
            properties=query_properties,
            where=where,
            first=1000,  # TODO: Implement pagination if more items
        )

        items = result.get("nodes", [])
        logger.debug(f"Found {len(items)} items with TimeSeries properties")

        if not items:
            logger.warning(f"No items found in {inventory_name}")
            return TimeSeriesResult({}, self)

        # Step 2: Extrahiere Timeseries IDs and create Mapping
        # Format: ts_id -> (item_id, property_name)
        ts_to_item_mapping = {}
        timeseries_ids = []

        for item in items:
            item_id = item["_id"]
            for field in ts_properties:
                ts_data = item.get(field)
                if ts_data and isinstance(ts_data, dict) and "id" in ts_data:
                    ts_id = ts_data["id"]
                    ts_to_item_mapping[ts_id] = {
                        "item_id": item_id,
                        "property_name": field,
                    }
                    timeseries_ids.append(ts_id)

        if not timeseries_ids:
            logger.warning("No TimeSeries IDs found in items")
            return TimeSeriesResult({}, self)

        logger.debug(f"Extracted {len(timeseries_ids)} TimeSeries IDs")

        # Step 3: Lade time series values
        # Default: only exclude MISSING
        if exclude_qualities is None:
            exclude_qualities = [Quality.MISSING]

        ts_result = self._client.timeseries.get_data(
            time_series_ids=timeseries_ids,
            from_time=from_time,
            to_time=to_time,
            time_unit=time_unit,
            multiplier=multiplier if time_unit else None,
            aggregation=aggregation,
            time_zone=time_zone,
            exclude_qualities=exclude_qualities,
        )

        # Step 4: Combine Results
        # Uniform structure: ALWAYS with "timeseries" dict
        item_index = {item["_id"]: item for item in items}
        result_dict = {}

        for ts_data in ts_result.data:
            ts_id = ts_data.time_series_id
            if ts_id not in ts_to_item_mapping:
                continue

            mapping = ts_to_item_mapping[ts_id]
            item_id = mapping["item_id"]
            property_name = mapping["property_name"]

            # Initialize item entry if needed
            if item_id not in result_dict:
                result_dict[item_id] = {
                    "item": item_index[item_id],
                    "timeseries": {},
                }

            # Store TimeSeries data ALWAYS under timeseries[property_name]
            result_dict[item_id]["timeseries"][property_name] = {
                "timeseries_id": ts_id,
                "values": ts_data.values,
                "unit": ts_data.unit,
                "interval": ts_data.interval,
                "time_zone": ts_data.time_zone,
            }

        logger.info(f"Listed timeseries values for {len(result_dict)} items")
        return TimeSeriesResult(result_dict, self)

    def _convert_timeseries_to_dataframe(
        self,
        result: dict[str, dict],
        include_metadata: bool = True,
        properties: list[str] | None = None,
    ) -> pd.DataFrame:
        if not _PANDAS_AVAILABLE:
            raise ImportError("pandas is required for DataFrame conversion")

        # Collect all data and item information
        # {(property, unit, item_id): {time: value}}
        data_dict = {}
        # {item_id: {property_name: field_value}}
        item_properties_dict = {}

        def get_nested_value(d: dict, path: str):
            """Extract value from nested dict using dot notation."""
            keys = path.split(".")
            value = d
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    return None
            return value

        for item_id, data in result.items():
            # Collect normal properties for this item
            if properties:
                item_properties_dict[item_id] = {}
                for field in properties:
                    # Support nested properties (e.g. "messwerte_temperatur.timeZone")
                    item_properties_dict[item_id][field] = get_nested_value(
                        data["item"], field
                    )

            # Unitliche Struktur: IMMER data["timeseries"]
            for property_name, ts_data in data["timeseries"].items():
                values = ts_data["values"]
                unit = ts_data.get("unit") or ""

                key = (property_name, unit, item_id)
                data_dict[key] = {
                    ts_value.time: float(ts_value.value) for ts_value in values
                }

        if not data_dict:
            # Leerer DataFrame
            return pd.DataFrame()  # type: ignore

        # Create DataFrame from dict
        # Collect columns as List of Tuples (property_name, unit, item_id)
        columns_list = []
        series_list = []

        for (property_name, unit, item_id), time_values in data_dict.items():
            columns_list.append((property_name, unit, item_id))
            series_list.append(pd.Series(time_values))  # type: ignore

        if not columns_list:
            return pd.DataFrame()  # type: ignore

        # Create DataFrame with MultiIndex columns
        df = pd.DataFrame(dict(enumerate(series_list)))  # type: ignore
        df.index.name = "time"
        df = df.sort_index()

        # Check ob all Units per Timeseries-Field gleich sind
        # If yes, we can simplify the unit level
        field_units = {}
        for ts_field, unit, item in columns_list:
            if ts_field not in field_units:
                field_units[ts_field] = set()
            field_units[ts_field].add(unit)

        # If all TimeSeries properties have only a single unit, simplify
        all_single_unit = all(len(units) == 1 for units in field_units.values())

        # Create MultiIndex with normalen properties as Spalten-Ebenen
        if properties and item_properties_dict:
            # Extend columns_list with field values
            # Struktur: (ts_field, unit, field1_value, field2_value, ..., item_id)
            extended_columns = []
            for ts_field, unit, item_id in columns_list:
                # Get field values for this Item
                field_values = []
                if item_id in item_properties_dict:
                    for field in properties:
                        field_values.append(item_properties_dict[item_id].get(field))
                else:
                    field_values = [None] * len(properties)

                # Baue Spalten-Tuple
                if all_single_unit:
                    # (ts_field [unit], field1, field2, ..., item_id)
                    ts_field_with_unit = f"{ts_field} [{unit}]" if unit else ts_field
                    extended_columns.append(
                        (ts_field_with_unit, *field_values, item_id)
                    )
                else:
                    # (ts_field, unit, field1, field2, ..., item_id)
                    extended_columns.append((ts_field, unit, *field_values, item_id))

            # Create names for the MultiIndex-Ebenen
            if all_single_unit:
                column_names = ["Timeseries-Field [Unit]"] + properties + ["Item-ID"]
            else:
                column_names = ["Timeseries-Field", "Unit"] + properties + ["Item-ID"]

            df.columns = pd.MultiIndex.from_tuples(  # type: ignore
                extended_columns, names=column_names
            )
        else:
            # No normalen properties: like vorher
            if all_single_unit:
                # Vereinfachter MultiIndex: Timeseries-Field and Item-ID
                # Unit is combined with field in the first level
                simplified_columns = []
                for ts_field, unit, item in columns_list:
                    ts_field_with_unit = f"{ts_field} [{unit}]" if unit else ts_field
                    simplified_columns.append((ts_field_with_unit, item))

                df.columns = pd.MultiIndex.from_tuples(  # type: ignore
                    simplified_columns, names=["Timeseries-Field [Unit]", "Item-ID"]
                )
            else:
                # Voller MultiIndex: Timeseries-Field, Unit, Item-ID
                df.columns = pd.MultiIndex.from_tuples(  # type: ignore
                    columns_list, names=["Timeseries-Field", "Unit", "Item-ID"]
                )

        return df

    def save_timeseries_values(
        self,
        inventory_name: str,
        timeseries_property: str,
        item_id: str,
        values: list[TimeSeriesValue],
        namespace_name: str | None = None,
        time_unit: TimeUnit | None = None,
        multiplier: int = 1,
        unit: str | None = None,
        time_zone: str | None = None,
    ) -> None:
        """Save time series values for a single item.

        Args:
            inventory_name: Name of inventory
            timeseries_property: Time series property name
            item_id: Item ID
            values: Time series values to save
            namespace_name: Optional namespace
            time_unit: Time interval unit
            multiplier: Multiplier for time_unit
            unit: Measurement unit
            time_zone: Timezone for values
        """
        logger.info(
            f"Saving timeseries values for single item. inventory_name={inventory_name}, namespace_name={namespace_name}, timeseries_property={timeseries_property}, item_id={item_id}, value_count={len(values)}"
        )

        # Delegiere to Bulk-Methode
        self.save_timeseries_values_bulk(
            inventory_name=inventory_name,
            timeseries_properties=timeseries_property,
            item_values={item_id: values},
            namespace_name=namespace_name,
            time_unit=time_unit,
            multiplier=multiplier,
            unit=unit,
            time_zone=time_zone,
        )

    def save_timeseries_values_bulk(
        self,
        inventory_name: str,
        timeseries_properties: str | list[str],
        item_values: dict[str, list[TimeSeriesValue]]
        | dict[str, dict[str, list[TimeSeriesValue]]],
        namespace_name: str | None = None,
        time_unit: TimeUnit | None = None,
        multiplier: int = 1,
        unit: str | None = None,
        time_zone: str | None = None,
    ) -> None:
        """Save time series values for multiple items.

        Args:
            inventory_name: Name of inventory
            timeseries_properties: Property name(s) containing time series
            item_values: Dict mapping item IDs to values (list or dict)
            namespace_name: Optional namespace
            time_unit: Time interval unit
            multiplier: Multiplier for time_unit
            unit: Measurement unit
            time_zone: Timezone for values
        """
        ts_properties = (
            [timeseries_properties]
            if isinstance(timeseries_properties, str)
            else timeseries_properties
        )

        logger.info(
            f"Saving timeseries values for inventory items. inventory_name={inventory_name}, namespace_name={namespace_name}, item_count={len(item_values)}, timeseries_properties={ts_properties}"
        )

        if not item_values:
            logger.warning("No item values provided")
            return

        # Step 1: Lade Inventory Items with Timeseries properties
        # Note: _id verwendet lowercase Filter (eq, in) statt _eq, _in
        item_ids = list(item_values.keys())
        where = {"_id": {"in": item_ids}}

        # Create properties list with all Timeseries-properties
        properties = ["_id"]
        for field in ts_properties:
            properties.append(f"{field}.id")

        result = self._client.inventory.list(
            inventory_name=inventory_name,
            namespace_name=namespace_name,
            properties=properties,
            where=where,
            first=len(item_ids),
        )

        items = result.get("nodes", [])
        logger.debug(f"Found {len(items)} items")

        # Step 2: Erstelle SetTimeSeriesDataInput for all Timeseries-properties
        from .models import Interval

        data_inputs = []

        # Check whether we are with multiple Timeseries-properties arbeiten
        is_multi_field = len(ts_properties) > 1

        for item in items:
            item_id = item["_id"]
            item_value_data = item_values.get(item_id)

            if not item_value_data:
                continue

            # Verarbeite jedes Timeseries-Field
            for field in ts_properties:
                ts_data = item.get(field)

                if not ts_data or not isinstance(ts_data, dict) or "id" not in ts_data:
                    logger.warning(
                        f"Item {item_id} has no valid TimeSeries field '{field}'"
                    )
                    continue

                ts_id = ts_data["id"]

                # Get Werte basierend auf Modus (single vs. multi field)
                if is_multi_field:
                    # Multi-Field-Modus: item_value_data ist Dict[str, list[TimeSeriesValue]]
                    if not isinstance(item_value_data, dict):
                        expected_fields = ", ".join(
                            f'"{p}": [...]' for p in ts_properties
                        )
                        raise ValueError(
                            f"Item {item_id}: Multi-field mode requires dict structure.\n"
                            f"Expected: {{{expected_fields}}}\n"
                            f"Got {type(item_value_data).__name__}: {item_value_data!r}"
                        )
                    values = item_value_data.get(field, [])
                else:
                    # Single-Field-Modus: item_value_data ist list[TimeSeriesValue]
                    if isinstance(item_value_data, dict):
                        hint_props = ", ".join(f'"{k}"' for k in item_value_data.keys())
                        raise ValueError(
                            f"Item {item_id}: Single-field mode requires list structure.\n"
                            f"Expected: [TimeSeriesValue(...), ...]\n"
                            f"Got dict with keys: {list(item_value_data.keys())}\n"
                            f"Hint: For multiple properties, pass them as list: "
                            f"timeseries_properties=[{hint_props}]"
                        )
                    values = item_value_data

                if values:
                    data_input = SetTimeSeriesDataInput(
                        timeSeriesId=ts_id,
                        values=values,
                        interval=Interval(timeUnit=time_unit, multiplier=multiplier)
                        if time_unit
                        else None,
                        unit=unit,
                        timeZone=time_zone,
                        quotationTime=None,
                    )
                    data_inputs.append(data_input)

        # Step 3: Speichere values via REST API
        if data_inputs:
            self._client.timeseries.set_data(data_inputs)
            total_values = sum(len(di.values) for di in data_inputs)
            logger.info(
                f"Saved {total_values} values for {len(data_inputs)} TimeSeries"
            )
        else:
            logger.warning("No valid data inputs created")

    # ===== Quotation Operations =====

    def list_quotation_timestamps(
        self,
        inventory_name: str,
        timeseries_property: str,
        from_time: datetime,
        to_time: datetime,
        namespace_name: str | None = None,
        where: dict[str, Any] | None = None,
        aggregated: bool = False,
    ) -> dict[str, list[datetime]] | list[datetime]:
        """List available quotation timestamps.

        Args:
            inventory_name: Name of inventory
            timeseries_property: Time series property name
            from_time: Start timestamp
            to_time: End timestamp
            namespace_name: Optional namespace
            where: Optional filter conditions
            aggregated: If True, return unique timestamps across all items

        Returns:
            Dict mapping item IDs to timestamps, or list of unique timestamps if aggregated
        """
        logger.info(
            f"Listing quotation timestamps. inventory_name={inventory_name}, namespace_name={namespace_name}, timeseries_property={timeseries_property}, aggregated={aggregated}"
        )

        # Step 1: Lade Inventory Items with Timeseries Property
        properties = ["_id", f"{timeseries_property}.id"]

        result = self._client.inventory.list(
            inventory_name=inventory_name,
            namespace_name=namespace_name,
            properties=properties,
            where=where,
            first=1000,  # TODO: Implement pagination if more items
        )

        items = result.get("nodes", [])
        logger.debug(f"Found {len(items)} items with TimeSeries property")

        if not items:
            logger.warning(f"No items found in {inventory_name}")
            return [] if aggregated else {}

        # Step 2: Extrahiere Timeseries IDs
        timeseries_ids = []
        ts_to_item_mapping = {}

        for item in items:
            item_id = item["_id"]
            ts_data = item.get(timeseries_property)
            if ts_data and isinstance(ts_data, dict) and "id" in ts_data:
                ts_id = ts_data["id"]
                timeseries_ids.append(ts_id)
                ts_to_item_mapping[ts_id] = item_id

        if not timeseries_ids:
            logger.warning("No TimeSeries IDs found in items")
            return [] if aggregated else {}

        logger.debug(f"Extracted {len(timeseries_ids)} TimeSeries IDs")

        # Step 3: Lade quotations
        quotations_result = self._client.timeseries.get_quotations(
            time_series_ids=timeseries_ids,
            from_time=from_time,
            to_time=to_time,
            aggregated=aggregated,
        )

        # Step 4: Verarbeite Ergebnisse
        if aggregated:
            # Aggregated: Sammle all unique quotation timestamps
            all_timestamps = set()
            for quotations in quotations_result.items:
                if quotations.values:
                    for quot_value in quotations.values:
                        all_timestamps.add(quot_value.time)

            result_list = sorted(list(all_timestamps))
            logger.info(
                f"Found {len(result_list)} unique quotation timestamps (aggregated)"
            )
            return result_list
        else:
            # Pro Item: Mapping Item-ID -> Notierungs-Zeitstempel
            item_quotations = {}
            for quotations in quotations_result.items:
                ts_id = quotations.time_series_id
                if ts_id in ts_to_item_mapping and quotations.values:
                    item_id = ts_to_item_mapping[ts_id]
                    timestamps = [quot_value.time for quot_value in quotations.values]
                    item_quotations[item_id] = sorted(timestamps)

            logger.info(f"Found quotations for {len(item_quotations)} items")
            return item_quotations

    def list_quotation_values(
        self,
        inventory_name: str,
        timeseries_property: str,
        from_time: datetime,
        to_time: datetime,
        quotation_time: datetime | None = None,
        quotation_behavior: QuotationBehavior = QuotationBehavior.LATEST,
        quotation_exactly_at: bool = False,
        namespace_name: str | None = None,
        where: dict[str, Any] | None = None,
        properties: list[str] | None = None,
        aggregation: Aggregation | None = None,
        time_unit: TimeUnit | None = None,
        multiplier: int | None = None,
        exclude_qualities: list[Quality] | None = None,
        time_zone: str | None = None,
    ) -> dict[str, dict]:
        """Retrieve quotation values.

        Args:
            inventory_name: Name of inventory
            timeseries_property: Time series property name
            from_time: Start timestamp
            to_time: End timestamp
            quotation_time: Optional specific quotation timestamp
            quotation_behavior: How to select quotation if not exact
            quotation_exactly_at: Require exact quotation match
            namespace_name: Optional namespace
            where: Optional filter conditions
            properties: Additional item properties to include
            aggregation: Optional data aggregation
            time_unit: Time interval unit
            multiplier: Multiplier for time_unit
            exclude_qualities: Quality flags to exclude
            time_zone: Timezone for timestamps

        Returns:
            Dict mapping item IDs to item and time series data
        """
        logger.info(
            f"Getting quotation data. inventory_name={inventory_name}, namespace_name={namespace_name}, timeseries_property={timeseries_property}, quotation_time={quotation_time}, quotation_behavior={quotation_behavior}"
        )

        # Step 1: Lade Inventory Items with Timeseries Property
        query_properties = ["_id", "_rowVersion"]

        # Add Timeseries Property hinzu
        query_properties.append(f"{timeseries_property}.id")

        # Add additional properties
        if properties:
            for prop in properties:
                if prop not in query_properties:
                    query_properties.append(prop)

        result = self._client.inventory.list(
            inventory_name=inventory_name,
            namespace_name=namespace_name,
            properties=query_properties,
            where=where,
            first=1000,  # TODO: Implement pagination if more items
        )

        items = result.get("nodes", [])
        logger.debug(f"Found {len(items)} items with TimeSeries property")

        if not items:
            logger.warning(f"No items found in {inventory_name}")
            return {}

        # Step 2: Extrahiere Timeseries IDs
        timeseries_ids = []
        ts_to_item_mapping = {}

        for item in items:
            item_id = item["_id"]
            ts_data = item.get(timeseries_property)
            if ts_data and isinstance(ts_data, dict) and "id" in ts_data:
                ts_id = ts_data["id"]
                ts_to_item_mapping[ts_id] = item_id
                timeseries_ids.append(ts_id)

        if not timeseries_ids:
            logger.warning("No TimeSeries IDs found in items")
            return {}

        logger.debug(f"Extracted {len(timeseries_ids)} TimeSeries IDs")

        # Step 3: Lade time series values with Quotation
        # Default: only exclude MISSING
        if exclude_qualities is None:
            exclude_qualities = [Quality.MISSING]

        ts_result = self._client.timeseries.get_data(
            time_series_ids=timeseries_ids,
            from_time=from_time,
            to_time=to_time,
            time_unit=time_unit,
            multiplier=multiplier if time_unit else None,
            aggregation=aggregation,
            time_zone=time_zone,
            quotation_time=quotation_time,
            quotation_exactly_at=quotation_exactly_at,
            quotation_behavior=quotation_behavior,
            exclude_qualities=exclude_qualities,
        )

        # Step 4: Combine Results
        item_index = {item["_id"]: item for item in items}
        result_dict = {}

        for ts_data in ts_result.data:
            ts_id = ts_data.time_series_id
            if ts_id not in ts_to_item_mapping:
                continue

            item_id = ts_to_item_mapping[ts_id]

            # Initialize item entry if needed
            if item_id not in result_dict:
                result_dict[item_id] = {
                    "item": item_index[item_id],
                    "quotation_time": None,  # Set as needed
                    "timeseries": {},
                }

            # Speichere Timeseries Daten
            result_dict[item_id]["timeseries"][timeseries_property] = {
                "timeseries_id": ts_id,
                "values": ts_data.values,
                "unit": ts_data.unit,
                "interval": ts_data.interval,
                "time_zone": ts_data.time_zone,
            }

            # TODO: quotation_time extract from Response if available
            # Currently the API does not return the actually used quotation

        logger.info(f"Loaded quotation data for {len(result_dict)} items")
        return result_dict

    def save_quotation_values(
        self,
        inventory_name: str,
        timeseries_property: str,
        item_id: str,
        values: list[TimeSeriesValue],
        quotation_time: datetime,
        namespace_name: str | None = None,
        time_unit: TimeUnit | None = None,
        multiplier: int = 1,
        unit: str | None = None,
        time_zone: str | None = None,
    ) -> None:
        """Save quotation values for an item.

        Args:
            inventory_name: Name of inventory
            timeseries_property: Time series property name
            item_id: Item ID
            values: Time series values to save
            quotation_time: Quotation timestamp
            namespace_name: Optional namespace
            time_unit: Time interval unit
            multiplier: Multiplier for time_unit
            unit: Measurement unit
            time_zone: Timezone for values
        """
        logger.info(
            f"Saving quotation data for single item. inventory_name={inventory_name}, namespace_name={namespace_name}, timeseries_property={timeseries_property}, item_id={item_id}, quotation_time={quotation_time}, value_count={len(values)}"
        )

        # Step 1: Lade Item with Timeseries Property
        where = {"_id": {"eq": item_id}}
        properties = ["_id", f"{timeseries_property}.id"]

        result = self._client.inventory.list(
            inventory_name=inventory_name,
            namespace_name=namespace_name,
            properties=properties,
            where=where,
            first=1,
        )

        items = result.get("nodes", [])
        if not items:
            raise ValueError(f"Item with ID {item_id} not found in {inventory_name}")

        item = items[0]
        ts_data = item.get(timeseries_property)

        if not ts_data or not isinstance(ts_data, dict) or "id" not in ts_data:
            raise ValueError(
                f"Item {item_id} has no valid TimeSeries property '{timeseries_property}'"
            )

        ts_id = ts_data["id"]
        logger.debug(f"Found TimeSeries ID {ts_id} for item {item_id}")

        # Step 2: Erstelle SetTimeSeriesDataInput with quotation
        from .models import Interval

        data_input = SetTimeSeriesDataInput(
            timeSeriesId=ts_id,
            values=values,
            interval=Interval(timeUnit=time_unit, multiplier=multiplier)
            if time_unit
            else None,
            unit=unit,
            timeZone=time_zone,
            quotationTime=quotation_time,  # ← Notierungs-Zeitstempel!
        )

        # Step 3: Speichere values via REST API
        self._client.timeseries.set_data([data_input])
        logger.info(
            f"Saved {len(values)} values with quotation_time={quotation_time} for TimeSeries {ts_id}"
        )

    def compare_quotations(
        self,
        inventory_name: str,
        timeseries_property: str,
        item_id: str,
        quotation_times: list[datetime],
        from_time: datetime,
        to_time: datetime,
        namespace_name: str | None = None,
        aggregation: Aggregation | None = None,
        time_unit: TimeUnit | None = None,
        multiplier: int | None = None,
    ) -> pd.DataFrame:
        """Compare multiple quotations in a DataFrame.

        Args:
            inventory_name: Name of inventory
            timeseries_property: Time series property name
            item_id: Item ID to compare
            quotation_times: List of quotation timestamps to compare
            from_time: Start timestamp
            to_time: End timestamp
            namespace_name: Optional namespace
            aggregation: Optional data aggregation
            time_unit: Time interval unit
            multiplier: Multiplier for time_unit

        Returns:
            pandas DataFrame with quotation comparison

        Raises:
            ImportError: If pandas is not installed
        """
        if not _PANDAS_AVAILABLE:
            raise ImportError(
                "pandas is required for DataFrame output. "
                "Install with: pip install questra-data[pandas]"
            )

        if not quotation_times:
            raise ValueError("At least one quotation_time is required")

        logger.info(
            f"Comparing quotations. inventory_name={inventory_name}, namespace_name={namespace_name}, timeseries_property={timeseries_property}, item_id={item_id}, quotation_count={len(quotation_times)}"
        )

        # Load Daten for each quotation
        all_data = {}
        for quot_time in quotation_times:
            logger.debug(f"Loading data for quotation {quot_time}")
            data = self.list_quotation_values(
                inventory_name=inventory_name,
                timeseries_property=timeseries_property,
                from_time=from_time,
                to_time=to_time,
                quotation_time=quot_time,
                quotation_exactly_at=True,  # Exakt diese Notierung
                namespace_name=namespace_name,
                where={"_id": {"eq": item_id}},
                aggregation=aggregation,
                time_unit=time_unit,
                multiplier=multiplier,
            )

            # Extract values for this item
            if item_id in data:
                item_data = data[item_id]
                if timeseries_property in item_data["timeseries"]:
                    ts_values = item_data["timeseries"][timeseries_property]["values"]
                    all_data[quot_time] = ts_values
                else:
                    logger.warning(
                        f"No data for quotation {quot_time} and property {timeseries_property}"
                    )
                    all_data[quot_time] = []
            else:
                logger.warning(f"No data for quotation {quot_time} and item {item_id}")
                all_data[quot_time] = []

        # Create DataFrame with MultiIndex columns
        # Format: (quotation_time, "value") and (quotation_time, "quality")
        data_dict = {}

        for quot_time, values in all_data.items():
            # Column for values
            value_series = pd.Series(  # type: ignore
                {val.time: float(val.value) for val in values},
                name=(quot_time, "value"),
            )
            data_dict[(quot_time, "value")] = value_series

            # Column for quality
            quality_series = pd.Series(  # type: ignore
                {
                    val.time: val.quality.value if val.quality else None
                    for val in values
                },
                name=(quot_time, "quality"),
            )
            data_dict[(quot_time, "quality")] = quality_series

        # Create DataFrame
        df = pd.DataFrame(data_dict)  # type: ignore
        df.index.name = "time"
        df = df.sort_index()

        # Set MultiIndex for columns
        df.columns = pd.MultiIndex.from_tuples(  # type: ignore
            df.columns, names=["quotation_time", "metric"]
        )

        logger.info(f"Created comparison DataFrame with {len(df)} rows")
        return df

    # ===== Inventory Operations =====

    def list_items(
        self,
        inventory_name: str,
        properties: list[str] | None = None,
        namespace_name: str | None = None,
        where: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> QueryResult:
        """List inventory items.

        Args:
            inventory_name: Name of inventory
            properties: Properties to retrieve (defaults to _id and _rowVersion)
            namespace_name: Optional namespace filter
            where: Optional filter conditions
            limit: Maximum number of items to return

        Returns:
            QueryResult containing items
        """
        logger.info(
            f"Listing inventory items. inventory_name={inventory_name}, namespace_name={namespace_name}, limit={limit}"
        )

        # If no properties specified, load basic fields
        if properties is None:
            properties = ["_id", "_rowVersion"]

        result = self._client.inventory.list(
            inventory_name=inventory_name,
            namespace_name=namespace_name,
            properties=properties,
            where=where,
            first=limit,
        )

        items = result.get("nodes", [])
        logger.info(f"Listed {len(items)} items from {inventory_name}")
        return QueryResult(items)

    def create_items(
        self,
        inventory_name: str,
        items: list[dict[str, Any]],
        namespace_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Create inventory items.

        Automatically creates time series for TIME_SERIES properties if needed.

        Args:
            inventory_name: Name of inventory
            items: List of item dicts to create
            namespace_name: Optional namespace

        Returns:
            List of created items with IDs
        """
        logger.info(
            f"Creating inventory items. inventory_name={inventory_name}, namespace_name={namespace_name}, item_count={len(items)}"
        )

        # Step 1: Lade Inventory schema to identify TIMESERIES properties
        inventories = self._client.queries.get_inventories(
            where={
                "inventoryNames": [inventory_name],
                "namespaceNames": [namespace_name] if namespace_name else None,
            }
        )

        if not inventories:
            logger.warning(
                f"Inventory {inventory_name} not found, skipping TimeSeries auto-creation"
            )
            result = self._client.inventory.create(
                inventory_name=inventory_name,
                namespace_name=namespace_name,
                items=items,
            )
            logger.info(f"Created {len(result)} items in {inventory_name}")
            return result

        inventory = inventories[0]

        # Step 2: Identify TIMESERIES properties
        timeseries_properties = {}
        if inventory.properties:
            for prop in inventory.properties:
                if prop.data_type == DataType.TIME_SERIES:
                    timeseries_properties[prop.name] = prop

        logger.debug(
            f"Found {len(timeseries_properties)} TIMESERIES properties. properties={list(timeseries_properties.keys())}"
        )

        # Step 3: Erstelle TimeSeries for all Items with TIMESERIES properties
        if timeseries_properties:
            from .models.inputs import CreateTimeSeriesInput

            # Collect all TimeSeries to create
            timeseries_to_create = []
            # Mapping: (item_index, property_name) -> Timeseries Index
            timeseries_mapping = {}

            for item_idx, item in enumerate(items):
                for prop_name, prop in timeseries_properties.items():
                    # Check whether item contains this property (case-insensitive for first letter)
                    item_key = None
                    for key in item.keys():
                        if (
                            key.lower()[0] == prop_name.lower()[0]
                            and key[1:] == prop_name[1:]
                        ):
                            item_key = key
                            break

                    # Create TimeSeries only if property is present in item
                    if item_key is not None:
                        item_value = item[item_key]

                        # Determine whether TimeSeries should be created:
                        # - None -> Create new TimeSeries
                        # - String/Int -> Use existing ID
                        # - Other formats -> Error
                        if item_value is None:
                            # None -> Create new TimeSeries
                            ts_input = CreateTimeSeriesInput(
                                inventoryName=inventory_name,
                                propertyName=prop_name,
                                namespaceName=namespace_name,
                            )
                            timeseries_mapping[(item_idx, item_key)] = len(
                                timeseries_to_create
                            )
                            timeseries_to_create.append(ts_input)
                        elif isinstance(item_value, (str, int)):
                            # Direct ID as string/Int -> Use existing ID
                            items[item_idx][item_key] = int(item_value)
                            logger.debug(
                                f"Using existing TimeSeries ID {item_value} for item {item_idx}, property {item_key}"
                            )
                        else:
                            # Unknown format -> Error
                            raise ValueError(
                                f"Invalid TimeSeries value for item {item_idx}, property {item_key}: {item_value}. "
                                f"Expected None (auto-create) or string/int (existing ID)."
                            )

            # Create all TimeSeries at once via GraphQL mutation
            if timeseries_to_create:
                logger.info(
                    f"Creating {len(timeseries_to_create)} TimeSeries via GraphQL"
                )
                ts_results = self._client.mutations.create_timeseries(
                    timeseries_to_create
                )

                # Step 4: Setze Timeseries IDs in items
                for (item_idx, prop_key), ts_idx in timeseries_mapping.items():
                    ts_id = int(ts_results[ts_idx].id)

                    # Set Timeseries ID in Item
                    # Format: Direct ID as string (will be processed later by _convert_numbers_to_strings)
                    items[item_idx][prop_key] = ts_id

                    logger.debug(
                        f"Assigned TimeSeries ID {ts_id} to item {item_idx}, property {prop_key}"
                    )

        # Step 5: Erstelle Items with assigned Timeseries IDs
        result = self._client.inventory.create(
            inventory_name=inventory_name,
            namespace_name=namespace_name,
            items=items,
        )
        logger.info(f"Created {len(result)} items in {inventory_name}")
        return result

    def update_items(
        self,
        inventory_name: str,
        items: list[dict[str, Any]],
        namespace_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Update inventory items.

        Args:
            inventory_name: Name of inventory
            items: List of items with _id and _rowVersion
            namespace_name: Optional namespace

        Returns:
            List of updated items
        """
        logger.info(
            f"Updating inventory items. inventory_name={inventory_name}, namespace_name={namespace_name}, item_count={len(items)}"
        )

        result = self._client.inventory.update(
            inventory_name=inventory_name,
            namespace_name=namespace_name,
            items=items,
        )
        logger.info(f"Updated {len(result)} items in {inventory_name}")
        return result

    def delete_items(
        self,
        inventory_name: str,
        item_ids: list[int | dict[str, Any]],
        namespace_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Delete inventory items.

        Args:
            inventory_name: Name of inventory
            item_ids: List of item IDs or dicts with _id and _rowVersion
            namespace_name: Optional namespace

        Returns:
            List of deleted items
        """
        logger.info(
            f"Deleting inventory items. inventory_name={inventory_name}, namespace_name={namespace_name}, item_count={len(item_ids)}"
        )

        # Convert IDs to dicts if necessary
        items_to_delete = []
        for item in item_ids:
            if isinstance(item, dict):
                items_to_delete.append(item)
            else:
                # Load Item to get _rowVersion
                # Note: _id verwendet lowercase Filter (eq) statt _eq
                loaded = self._client.inventory.list(
                    inventory_name=inventory_name,
                    namespace_name=namespace_name,
                    properties=["_id", "_rowVersion"],
                    where={"_id": {"eq": item}},
                    first=1,
                )
                if loaded.get("nodes"):
                    items_to_delete.append(loaded["nodes"][0])

        result = self._client.inventory.delete(
            inventory_name=inventory_name,
            namespace_name=namespace_name,
            items=items_to_delete,
        )

        logger.info(f"Deleted {len(result)} items from {inventory_name}")
        return result

    # ===== Management Operations =====

    def create_namespace(
        self,
        name: str,
        description: str | None = None,
        if_exists: ConflictAction = ConflictAction.IGNORE,
    ) -> NamedItemResult:
        """Create a namespace.

        Args:
            name: Namespace name
            description: Optional description
            if_exists: Action if namespace already exists

        Returns:
            NamedItemResult indicating creation status
        """
        logger.info(f"Creating namespace. name={name}")

        result = self._client.mutations.create_namespace(
            namespace_name=name,
            description=description,
            if_exists=if_exists,
        )

        logger.info(f"Namespace created: {name}, existed={result.existed}")
        return result

    def delete_namespace(
        self,
        name: str,
        if_not_exists: ConflictAction = ConflictAction.IGNORE,
    ) -> NamedItemResult:
        """Delete a namespace.

        Args:
            name: Namespace name
            if_not_exists: Action if namespace doesn't exist

        Returns:
            NamedItemResult indicating deletion status
        """
        logger.info(f"Deleting namespace. name={name}")

        result = self._client.mutations.drop_namespace(
            namespace_name=name,
            if_not_exists=if_not_exists,
        )

        logger.info(f"Namespace deleted: {name}, existed={result.existed}")
        return result

    def create_inventory(
        self,
        name: str,
        properties: list[
            InventoryProperty
            | StringProperty
            | IntProperty
            | LongProperty
            | DecimalProperty
            | BoolProperty
            | DateTimeProperty
            | DateTimeOffsetProperty
            | DateProperty
            | TimeProperty
            | GuidProperty
            | FileProperty
            | TimeSeriesProperty
        ],
        namespace_name: str | None = None,
        description: str | None = None,
        enable_audit: bool = False,
        relations: list[InventoryRelation] | None = None,
        if_exists: ConflictAction = ConflictAction.IGNORE,
    ) -> NamedItemResult:
        """Create an inventory.

        Args:
            name: Inventory name
            properties: List of inventory properties
            namespace_name: Optional namespace
            description: Optional description
            enable_audit: Enable audit logging
            relations: Optional inventory relations
            if_exists: Action if inventory already exists

        Returns:
            NamedItemResult indicating creation status
        """
        logger.info(f"Creating inventory. name={name}, namespace_name={namespace_name}")

        normalized_properties = self._normalize_properties(properties)

        result = self._client.mutations.create_inventory(
            inventory_name=name,
            properties=normalized_properties,
            namespace_name=namespace_name,
            description=description,
            enable_audit=enable_audit,
            relations=relations,
            if_exists=if_exists,
        )

        logger.info(f"Inventory created: {name}, existed={result.existed}")
        return result

    def delete_inventory(
        self,
        inventory_name: str,
        namespace_name: str | None = None,
        if_not_exists: ConflictAction = ConflictAction.IGNORE,
    ) -> NamedItemResult:
        """Delete an inventory.

        Args:
            inventory_name: Name of inventory to delete
            namespace_name: Optional namespace
            if_not_exists: Action if inventory doesn't exist

        Returns:
            NamedItemResult indicating deletion status
        """
        logger.info(
            f"Deleting inventory. inventory_name={inventory_name}, namespace_name={namespace_name}"
        )

        result = self._client.mutations.delete_inventory(
            inventory_name=inventory_name,
            namespace_name=namespace_name,
            if_not_exists=if_not_exists,
        )

        logger.info(f"Inventory deleted: {inventory_name}, existed={result.existed}")
        return result

    def get_system_info(self) -> SystemInfo:
        """Get system information."""
        return self._catalog_manager.get_system_info()

    def list_namespaces(self) -> QueryResult[Namespace]:
        """List all namespaces."""
        namespaces = self._catalog_manager.list_namespaces()
        return QueryResult(namespaces)

    def list_roles(self) -> QueryResult[Role]:
        """List all roles."""
        roles = self._catalog_manager.list_roles()
        return QueryResult(roles)

    def list_units(self) -> QueryResult[Unit]:
        """List all measurement units."""
        units = self._catalog_manager.list_units()
        return QueryResult(units)

    def list_time_zones(self) -> QueryResult[TimeZone]:
        """List all time zones."""
        time_zones = self._catalog_manager.list_time_zones()
        return QueryResult(time_zones)

    def list_inventories(
        self,
        namespace_name: str | None = None,
        inventory_names: list[str] | None = None,
    ) -> QueryResult[Inventory]:
        """List inventories.

        Args:
            namespace_name: Optional namespace filter
            inventory_names: Optional inventory name filter

        Returns:
            QueryResult containing inventories
        """
        logger.info(f"Listing inventories. namespace_name={namespace_name}")

        where = {}
        if namespace_name:
            where["namespaceNames"] = [namespace_name]
        if inventory_names:
            where["inventoryNames"] = inventory_names

        inventories = self._client.queries.get_inventories(
            where=where if where else None
        )
        return QueryResult(inventories)

    # ===== Direct Access to Low-Level Client =====

    @property
    def lowlevel(self) -> QuestraDataCore:
        """Access to low-level API client."""
        return self._client

    def is_authenticated(self) -> bool:
        """Check if authentication is valid."""
        return self._client.is_authenticated()

    def __repr__(self) -> str:
        auth_status = (
            "authenticated" if self.is_authenticated() else "not authenticated"
        )
        return f"QuestraData(url='{self._client.graphql_url}', status='{auth_status}')"
