"""Input type models for Questra Data API.

These dataclasses provide type-safe wrappers for GraphQL input types.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# Re-exports for Property-Helper from generated models
from ..generated.models import FieldAssignableDataTypeEnumType as AssignableDataType
from ..generated.models import FieldRelationTypeEnumType as RelationType
from ..generated.rest_models import (
    Aggregation,
    QuotationBehavior,
    TimeUnit,
    ValueAlignment,
    ValueAvailability,
)


@dataclass
class StringPropertyConfig:
    """
    String property configuration.

    Attributes:
        maxLength: Maximum length in characters
        isCaseSensitive: Case sensitive (default: False)
    """

    maxLength: int  # Converted to LongNumberString (str)
    isCaseSensitive: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to Dictionary with maxLength as string for GraphQL."""
        return {
            "maxLength": str(self.maxLength),  # int -> str for GraphQL LongNumberString
            "isCaseSensitive": self.isCaseSensitive,
        }


@dataclass
class FilePropertyConfig:
    """
    File property configuration.

    Attributes:
        maxLength: Maximum length in bytes
    """

    maxLength: int  # Python 3 int is unlimited, converted to LongNumberString (str)

    def to_dict(self) -> dict[str, Any]:
        """Convert to Dictionary with maxLength as string for GraphQL."""
        return {
            "maxLength": str(self.maxLength)  # int -> str for GraphQL LongNumberString
        }


@dataclass
class IntervalConfig:
    """
    Time interval configuration.

    Attributes:
        timeUnit: Time unit (TimeUnit enum)
        multiplier: Interval multiplier (default: 1)
    """

    timeUnit: TimeUnit
    multiplier: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with enum values and multiplier as string for GraphQL."""
        return {
            "timeUnit": self.timeUnit.value,  # Enum -> str
            "multiplier": str(
                self.multiplier
            ),  # int -> str for GraphQL IntNumberString
        }


@dataclass
class TimeSeriesPropertyConfig:
    """
    Configuration for TimeSeries properties.

    Corresponds to _CreateInventoryPropertyTimeSeries__InputType from the GraphQL schema.

    Attributes:
        interval: Time interval (IntervalConfig)
        unit: Unit (z.B. "kW", "kWh", "g")
        valueAlignment: Value alignment (ValueAlignment Enum, default: LEFT)
        valueAvailability: Availability (ValueAvailability Enum, default: AT_INTERVAL_BEGIN)
        timeZone: Time zone (default: "Europe/Berlin")
        defaultAggregation: Default aggregation (Aggregation Enum, optional)
        startOfTime: Start time (optional, ISO-8601 with microseconds)
        enableAudit: Enable audit (default: False)
        enableQuotation: Enable quotation (default: False)
        defaultQuotationBehavior: Default quotation behavior (QuotationBehavior Enum, default: LATEST)
        allowSpecificsPerInstance: Allow specifications per instance (default: False)
    """

    interval: IntervalConfig
    unit: str
    valueAlignment: ValueAlignment = ValueAlignment.LEFT
    valueAvailability: ValueAvailability = ValueAvailability.AT_INTERVAL_BEGIN
    timeZone: str = "Europe/Berlin"
    defaultAggregation: Aggregation | None = None
    startOfTime: str | None = None
    enableAudit: bool = False
    enableQuotation: bool = False
    defaultQuotationBehavior: QuotationBehavior = QuotationBehavior.LATEST
    allowSpecificsPerInstance: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to Dictionary with enum values, filters None values."""
        result = {}
        for key in [
            "interval",
            "unit",
            "valueAlignment",
            "valueAvailability",
            "timeZone",
            "defaultAggregation",
            "startOfTime",
            "enableAudit",
            "enableQuotation",
            "defaultQuotationBehavior",
            "allowSpecificsPerInstance",
        ]:
            value = getattr(self, key, None)

            if value is None:
                continue

            # Convert IntervalConfig to Dict (calls its to_dict())
            if key == "interval":
                result[key] = value.to_dict()
            # Convert Enum to String
            elif hasattr(value, "value"):
                result[key] = value.value
            else:
                result[key] = value

        return result


@dataclass
class InventoryProperty:
    """
    Property definition for inventory creation.

    Corresponds to _CreateInventoryProperty__InputType from the GraphQL schema.

    Attributes:
        propertyName: Name of the Property
        dataType: Data type (DataType Enum)
        isRequired: Required field (default: True)
        isUnique: Unique (default: False)
        isArray: Array field (default: False)
        description: Optional description
        string: String-specific configuration (for AssignableDataType.STRING)
        file: File-specific configuration (for AssignableDataType.FILE)
        timeSeries: TimeSeries specific configuration (for AssignableDataType.TIME_SERIES)

    Examples:
        # Simple string property
        InventoryProperty(
            propertyName="Name",
            dataType=AssignableDataType.STRING,
            isRequired=True,
            string=StringPropertyConfig(maxLength=200)
        )

        # Integer property
        InventoryProperty(
            propertyName="Age",
            dataType=AssignableDataType.INT,
            isRequired=False
        )

        # TimeSeries property
        InventoryProperty(
            propertyName="messwerte_Energie",
            dataType=AssignableDataType.TIME_SERIES,
            timeSeries=TimeSeriesPropertyConfig(
                interval=IntervalConfig(timeUnit="MINUTE", multiplier="15"),
                unit="kWh"
            )
        )
    """

    propertyName: str
    dataType: AssignableDataType
    isRequired: bool = True
    isUnique: bool = False
    isArray: bool = False
    description: str | None = None
    string: StringPropertyConfig | None = None
    file: FilePropertyConfig | None = None
    timeSeries: TimeSeriesPropertyConfig | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Converts the dataclass to a dictionary for GraphQL input.

        Filters None values and converts nested dataclasses.
        Calls to_dict() on config objects that have this method.

        Returns:
            Dictionary ready for GraphQL variables
        """
        result = {}

        # Iterate over the actual attributes (not asdict, as we need control)
        for key in [
            "propertyName",
            "dataType",
            "isRequired",
            "isUnique",
            "isArray",
            "description",
            "string",
            "file",
            "timeSeries",
        ]:
            value = getattr(self, key, None)

            if value is None:
                continue

            # Convert Enum to String
            if hasattr(value, "value"):
                result[key] = value.value
            # Call to_dict() on config objects
            elif hasattr(value, "to_dict"):
                result[key] = value.to_dict()
            else:
                result[key] = value

        return result


@dataclass
class TimeSeriesSpecifics:
    """
    Optional specifications for TimeSeries during creation.

    Corresponds to _TimeSeriesSpecifics__InputType from the GraphQL schema.

    Attributes:
        interval: Zeitintervall (IntervalConfig, optional)
        valueAlignment: Wert-Ausrichtung (ValueAlignment Enum, optional)
        valueAvailability: Availability (ValueAvailability Enum, optional)
        unit: Unit (str, optional)
        timeZone: Zeitzone (str, optional)
        defaultAggregation: Default aggregation (Aggregation Enum, optional)
        startOfTime: Start-Zeitpunkt (str, optional, ISO-8601 with Mikrosekunden)
        defaultQuotationBehavior: Standard-Quotierungsverhalten (QuotationBehavior Enum, optional)

    Examples:
        # With all options
        TimeSeriesSpecifics(
            interval=IntervalConfig(timeUnit=TimeUnit.MINUTE, multiplier=15),
            valueAlignment=ValueAlignment.LEFT,
            valueAvailability=ValueAvailability.AT_INTERVAL_BEGIN,
            unit="kWh",
            timeZone="Europe/Berlin",
            defaultAggregation=Aggregation.AVERAGE,
            defaultQuotationBehavior=QuotationBehavior.LATEST
        )

        # Minimal (all fields optional)
        TimeSeriesSpecifics(
            interval=IntervalConfig(timeUnit=TimeUnit.HOUR, multiplier=1),
            unit="kW"
        )
    """

    interval: IntervalConfig | None = None
    valueAlignment: ValueAlignment | None = None
    valueAvailability: ValueAvailability | None = None
    unit: str | None = None
    timeZone: str | None = None
    defaultAggregation: Aggregation | None = None
    startOfTime: str | None = None
    defaultQuotationBehavior: QuotationBehavior | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to Dictionary with enum values, filters None values."""
        result = {}
        for key in [
            "interval",
            "valueAlignment",
            "valueAvailability",
            "unit",
            "timeZone",
            "defaultAggregation",
            "startOfTime",
            "defaultQuotationBehavior",
        ]:
            value = getattr(self, key, None)

            if value is None:
                continue

            # Convert IntervalConfig to Dict (calls its to_dict())
            if key == "interval":
                result[key] = value.to_dict()
            # Convert Enum to String
            elif hasattr(value, "value"):
                result[key] = value.value
            else:
                result[key] = value

        return result


@dataclass
class CreateTimeSeriesInput:
    """
    Input for creating a TimeSeries.

    Corresponds to _CreateTimeSeries__InputType from the GraphQL schema.

    Attributes:
        inventoryName: Name of the inventory
        propertyName: Name of the Property
        namespaceName: Optional Namespace (Standard: None)
        specifics: Optional Timeseries Spezifikationen (TimeSeriesSpecifics)

    Examples:
        # With Spezifikationen
        CreateTimeSeriesInput(
            inventoryName="Sensoren",
            propertyName="messwerte_temperatur",
            namespaceName="TestDaten",
            specifics=TimeSeriesSpecifics(
                interval=IntervalConfig(timeUnit=TimeUnit.MINUTE, multiplier=15),
                unit="°C"
            )
        )

        # Without specifications (uses property defaults)
        CreateTimeSeriesInput(
            inventoryName="Sensoren",
            propertyName="messwerte_energie"
        )
    """

    inventoryName: str
    propertyName: str
    namespaceName: str | None = None
    specifics: TimeSeriesSpecifics | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to Dictionary for GraphQL input, filters None values."""
        result = {}
        for key in ["inventoryName", "propertyName", "namespaceName", "specifics"]:
            value = getattr(self, key, None)

            if value is None:
                continue

            # Rufe to_dict() auf TimeSeriesSpecifics auf
            if hasattr(value, "to_dict"):
                result[key] = value.to_dict()
            else:
                result[key] = value

        return result


@dataclass
class InventoryRelation:
    """
    Relation definition for inventory creation.

    Corresponds to _CreateInventoryRelation__InputType from the GraphQL schema.

    Attributes:
        propertyName: Name of the Relation-Property im Child-Inventory
        relationType: Relation type (RelationType Enum)
        parentInventoryName: Name of the Parent-inventory
        parentPropertyName: Name of the Relation-Property im Parent-Inventory
        isRequired: Pflicht-Relation (optional)
        parentNamespaceName: Namespace of the parent inventory (optional)

    Examples:
        # One-to-Many Relation: Anlagen -> Technologie
        InventoryRelation(
            propertyName="Technologie",
            relationType=RelationType.ONE_TO_MANY,
            parentInventoryName="TEC",
            parentPropertyName="Anlagen"
        )

        # One-to-Many: Many employees belong to one department
        InventoryRelation(
            propertyName="Abteilung",
            relationType=RelationType.ONE_TO_MANY,
            parentInventoryName="Departments",
            parentPropertyName="Mitarbeiter",
            parentNamespaceName="HR",
            isRequired=True
        )
    """

    propertyName: str
    relationType: RelationType
    parentInventoryName: str
    parentPropertyName: str
    isRequired: bool | None = None
    parentNamespaceName: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Converts the dataclass to a dictionary for GraphQL input.

        Filters None values and converts enums.

        Returns:
            Dictionary ready for GraphQL variables
        """
        result = {}

        for key, value in asdict(self).items():
            if value is None:
                continue

            # Convert Enum to String
            if hasattr(value, "value"):
                result[key] = value.value
            else:
                result[key] = value

        return result


# ==============================================================================
# Spezialisierte Property-Klassen (flache Hierarchie)
# ==============================================================================


@dataclass
class BaseProperty:
    """
    Base class for all specialized property classes.

    Attributes:
        propertyName: Name of the Property
        isRequired: Required field (default: True)
        isUnique: Unique (default: False)
        isArray: Array field (default: False)
        description: Optional description
    """

    propertyName: str
    isRequired: bool = field(default=True, kw_only=True)
    isUnique: bool = field(default=False, kw_only=True)
    isArray: bool = field(default=False, kw_only=True)
    description: str | None = field(default=None, kw_only=True)


@dataclass
class StringProperty(BaseProperty):
    """
    String-Property. Ersetzt InventoryProperty(dataType=STRING, string=StringPropertyConfig(...)).

    Attributes:
        propertyName: Name of the Property
        maxLength: Maximum length in characters
        isCaseSensitive: Case-sensitive (default: False)
        isRequired: Required field (default: True)
        isUnique: Unique (default: False)
        isArray: Array field (default: False)
        description: Optional description

    Beispiel:
        ```python
        StringProperty(
            propertyName="gebaeudename", maxLength=100, isRequired=True, isUnique=True
        )
        ```
    """

    maxLength: int
    isCaseSensitive: bool = False

    def to_inventory_property(self) -> InventoryProperty:
        """Convert to InventoryProperty for GraphQL compatibility."""
        return InventoryProperty(
            propertyName=self.propertyName,
            dataType=AssignableDataType.STRING,
            isRequired=self.isRequired,
            isUnique=self.isUnique,
            isArray=self.isArray,
            description=self.description,
            string=StringPropertyConfig(
                maxLength=self.maxLength, isCaseSensitive=self.isCaseSensitive
            ),
        )


@dataclass
class IntProperty(BaseProperty):
    """
    Integer-Property. Ersetzt InventoryProperty(dataType=INT).

    Attributes:
        propertyName: Name of the Property
        isRequired: Required field (default: True)
        isUnique: Unique (default: False)
        isArray: Array field (default: False)
        description: Optional description

    Beispiel:
        ```python
        IntProperty(propertyName="baujahr", isRequired=False)
        ```
    """

    def to_inventory_property(self) -> InventoryProperty:
        """Convert to InventoryProperty for GraphQL compatibility."""
        return InventoryProperty(
            propertyName=self.propertyName,
            dataType=AssignableDataType.INT,
            isRequired=self.isRequired,
            isUnique=self.isUnique,
            isArray=self.isArray,
            description=self.description,
        )


@dataclass
class DecimalProperty(BaseProperty):
    """
    Decimal-Property. Ersetzt InventoryProperty(dataType=DECIMAL).

    Attributes:
        propertyName: Name of the Property
        isRequired: Required field (default: True)
        isUnique: Unique (default: False)
        isArray: Array field (default: False)
        description: Optional description

    Beispiel:
        ```python
        DecimalProperty(propertyName="preis", isRequired=True)
        ```
    """

    def to_inventory_property(self) -> InventoryProperty:
        """Convert to InventoryProperty for GraphQL compatibility."""
        return InventoryProperty(
            propertyName=self.propertyName,
            dataType=AssignableDataType.DECIMAL,
            isRequired=self.isRequired,
            isUnique=self.isUnique,
            isArray=self.isArray,
            description=self.description,
        )


@dataclass
class LongProperty(BaseProperty):
    """
    Long-Property. Ersetzt InventoryProperty(dataType=LONG).

    Attributes:
        propertyName: Name of the Property
        isRequired: Required field (default: True)
        isUnique: Unique (default: False)
        isArray: Array field (default: False)
        description: Optional description

    Beispiel:
        ```python
        LongProperty(propertyName="artikel_nummer", isRequired=False)
        ```
    """

    def to_inventory_property(self) -> InventoryProperty:
        """Convert to InventoryProperty for GraphQL compatibility."""
        return InventoryProperty(
            propertyName=self.propertyName,
            dataType=AssignableDataType.LONG,
            isRequired=self.isRequired,
            isUnique=self.isUnique,
            isArray=self.isArray,
            description=self.description,
        )


@dataclass
class BoolProperty(BaseProperty):
    """
    Boolean-Property. Ersetzt InventoryProperty(dataType=BOOLEAN).

    Attributes:
        propertyName: Name of the Property
        isRequired: Required field (default: True)
        isUnique: Unique (default: False)
        isArray: Array field (default: False)
        description: Optional description

    Beispiel:
        ```python
        BoolProperty(propertyName="aktiv", isRequired=True)
        ```
    """

    def to_inventory_property(self) -> InventoryProperty:
        """Convert to InventoryProperty for GraphQL compatibility."""
        return InventoryProperty(
            propertyName=self.propertyName,
            dataType=AssignableDataType.BOOLEAN,
            isRequired=self.isRequired,
            isUnique=self.isUnique,
            isArray=self.isArray,
            description=self.description,
        )


@dataclass
class DateTimeProperty(BaseProperty):
    """
    DateTime-Property. Ersetzt InventoryProperty(dataType=DATE_TIME).

    Attributes:
        propertyName: Name of the Property
        isRequired: Required field (default: True)
        isUnique: Unique (default: False)
        isArray: Array field (default: False)
        description: Optional description

    Beispiel:
        ```python
        DateTimeProperty(propertyName="erstellt_am", isRequired=True)
        ```
    """

    def to_inventory_property(self) -> InventoryProperty:
        """Convert to InventoryProperty for GraphQL compatibility."""
        return InventoryProperty(
            propertyName=self.propertyName,
            dataType=AssignableDataType.DATE_TIME,
            isRequired=self.isRequired,
            isUnique=self.isUnique,
            isArray=self.isArray,
            description=self.description,
        )


@dataclass
class DateTimeOffsetProperty(BaseProperty):
    """
    DateTimeOffset-Property. Ersetzt InventoryProperty(dataType=DATE_TIME_OFFSET).

    Attributes:
        propertyName: Name of the Property
        isRequired: Required field (default: True)
        isUnique: Unique (default: False)
        isArray: Array field (default: False)
        description: Optional description

    Beispiel:
        ```python
        DateTimeOffsetProperty(propertyName="letzte_aenderung", isRequired=True)
        ```
    """

    def to_inventory_property(self) -> InventoryProperty:
        """Convert to InventoryProperty for GraphQL compatibility."""
        return InventoryProperty(
            propertyName=self.propertyName,
            dataType=AssignableDataType.DATE_TIME_OFFSET,
            isRequired=self.isRequired,
            isUnique=self.isUnique,
            isArray=self.isArray,
            description=self.description,
        )


@dataclass
class DateProperty(BaseProperty):
    """
    Date-Property. Ersetzt InventoryProperty(dataType=DATE).

    Attributes:
        propertyName: Name of the Property
        isRequired: Required field (default: True)
        isUnique: Unique (default: False)
        isArray: Array field (default: False)
        description: Optional description

    Beispiel:
        ```python
        DateProperty(propertyName="geburtsdatum", isRequired=True)
        ```
    """

    def to_inventory_property(self) -> InventoryProperty:
        """Convert to InventoryProperty for GraphQL compatibility."""
        return InventoryProperty(
            propertyName=self.propertyName,
            dataType=AssignableDataType.DATE,
            isRequired=self.isRequired,
            isUnique=self.isUnique,
            isArray=self.isArray,
            description=self.description,
        )


@dataclass
class TimeProperty(BaseProperty):
    """
    Time-Property. Ersetzt InventoryProperty(dataType=TIME).

    Attributes:
        propertyName: Name of the Property
        isRequired: Required field (default: True)
        isUnique: Unique (default: False)
        isArray: Array field (default: False)
        description: Optional description

    Beispiel:
        ```python
        TimeProperty(propertyName="oeffnungszeit", isRequired=True)
        ```
    """

    def to_inventory_property(self) -> InventoryProperty:
        """Convert to InventoryProperty for GraphQL compatibility."""
        return InventoryProperty(
            propertyName=self.propertyName,
            dataType=AssignableDataType.TIME,
            isRequired=self.isRequired,
            isUnique=self.isUnique,
            isArray=self.isArray,
            description=self.description,
        )


@dataclass
class GuidProperty(BaseProperty):
    """
    GUID-Property. Ersetzt InventoryProperty(dataType=GUID).

    Attributes:
        propertyName: Name of the Property
        isRequired: Required field (default: True)
        isUnique: Unique (default: False)
        isArray: Array field (default: False)
        description: Optional description

    Beispiel:
        ```python
        GuidProperty(propertyName="external_id", isRequired=False)
        ```
    """

    def to_inventory_property(self) -> InventoryProperty:
        """Convert to InventoryProperty for GraphQL compatibility."""
        return InventoryProperty(
            propertyName=self.propertyName,
            dataType=AssignableDataType.GUID,
            isRequired=self.isRequired,
            isUnique=self.isUnique,
            isArray=self.isArray,
            description=self.description,
        )


@dataclass
class FileProperty(BaseProperty):
    """
    File-Property. Ersetzt InventoryProperty(dataType=FILE, file=FilePropertyConfig(...)).

    Attributes:
        propertyName: Name of the Property
        maxLength: Maximum length in bytes
        isRequired: Required field (default: True)
        isUnique: Unique (default: False)
        isArray: Array field (default: False)
        description: Optional description

    Beispiel:
        ```python
        FileProperty(
            propertyName="dokument",
            maxLength=10485760,  # 10 MB
            isRequired=False,
        )
        ```
    """

    maxLength: int

    def to_inventory_property(self) -> InventoryProperty:
        """Convert to InventoryProperty for GraphQL compatibility."""
        return InventoryProperty(
            propertyName=self.propertyName,
            dataType=AssignableDataType.FILE,
            isRequired=self.isRequired,
            isUnique=self.isUnique,
            isArray=self.isArray,
            description=self.description,
            file=FilePropertyConfig(maxLength=self.maxLength),
        )


@dataclass
class TimeSeriesProperty(BaseProperty):
    """
    Timeseries Property. Ersetzt InventoryProperty(dataType=TIME_SERIES, timeSeries=TimeSeriesPropertyConfig(...)).

    Attributes:
        propertyName: Name of the Property
        timeUnit: Zeiteinheit (z.B. TimeUnit.MINUTE, TimeUnit.HOUR)
        unit: Unit of the measured values (e.g. "°C", "kWh", "%")
        multiplier: Multiplier for interval (default: 1)
        timeZone: Time zone (default: "Europe/Berlin")
        valueAlignment: Wert-Ausrichtung (Standard: ValueAlignment.LEFT)
        valueAvailability: Availability (default: ValueAvailability.AT_INTERVAL_BEGIN)
        isRequired: Pflichtfeld (Standard: False, da TimeSeries optional sind)
        description: Optional description
        defaultAggregation: Standard-Aggregation (optional)
        startOfTime: Start-Zeitpunkt (optional, ISO-8601)
        enableAudit: Enable audit (default: False)
        enableQuotation: Enable quotation (default: False)
        defaultQuotationBehavior: Standard-Quotierungsverhalten (Standard: QuotationBehavior.LATEST)
        allowSpecificsPerInstance: Allow specifications per instance (default: False)

    Beispiel:
        ```python
        TimeSeriesProperty(
            propertyName="messwerte_temperatur",
            timeUnit=TimeUnit.MINUTE,
            multiplier=15,
            unit="°C",
            timeZone="Europe/Berlin",
        )
        ```
    """

    timeUnit: TimeUnit
    unit: str
    multiplier: int = 1
    timeZone: str = "Europe/Berlin"
    valueAlignment: ValueAlignment = ValueAlignment.LEFT
    valueAvailability: ValueAvailability = ValueAvailability.AT_INTERVAL_BEGIN
    defaultAggregation: Aggregation | None = None
    startOfTime: str | None = None
    enableAudit: bool = False
    enableQuotation: bool = False
    defaultQuotationBehavior: QuotationBehavior = QuotationBehavior.LATEST
    allowSpecificsPerInstance: bool = False

    def to_inventory_property(self) -> InventoryProperty:
        """Convert to InventoryProperty for GraphQL compatibility."""
        return InventoryProperty(
            propertyName=self.propertyName,
            dataType=AssignableDataType.TIME_SERIES,
            isRequired=self.isRequired,
            isUnique=False,  # TimeSeries are never unique
            isArray=False,  # TimeSeries are never arrays
            description=self.description,
            timeSeries=TimeSeriesPropertyConfig(
                interval=IntervalConfig(
                    timeUnit=self.timeUnit, multiplier=self.multiplier
                ),
                unit=self.unit,
                valueAlignment=self.valueAlignment,
                valueAvailability=self.valueAvailability,
                timeZone=self.timeZone,
                defaultAggregation=self.defaultAggregation,
                startOfTime=self.startOfTime,
                enableAudit=self.enableAudit,
                enableQuotation=self.enableQuotation,
                defaultQuotationBehavior=self.defaultQuotationBehavior,
                allowSpecificsPerInstance=self.allowSpecificsPerInstance,
            ),
        )
