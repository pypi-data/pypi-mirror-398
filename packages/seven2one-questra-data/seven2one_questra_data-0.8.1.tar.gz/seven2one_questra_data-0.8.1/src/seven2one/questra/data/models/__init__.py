"""Type Models for Dyno GraphQL Schema."""

from .common import (
    BackgroundJobResult,
    ConflictAction,
    NamedItemResult,
    PageInfo,
    SortOrder,
    TimeSeriesIdResult,
)
from .inputs import (
    CreateTimeSeriesInput,
    FilePropertyConfig,
    IntervalConfig,
    InventoryProperty,
    InventoryRelation,
    StringPropertyConfig,
    TimeSeriesPropertyConfig,
    TimeSeriesSpecifics,
)
from .inventory import (
    AssignableDataType,
    DataType,
    FileConfig,
    IntervalInfo,
    Inventory,
    InventoryType,
    RelationType,
    StringConfig,
    TimeSeriesConfig,
)
from .inventory import InventoryProperty as InventoryPropertyOutput
from .inventory import InventoryRelation as InventoryRelationOutput
from .namespace import Namespace
from .permissions import InventoryPrivilege, InventoryPropertyPrivilege, PermissionState
from .rest import (
    ErrorPayload,
    ErrorsPayload,
    File,
    Quotations,
    QuotationsPayload,
    QuotationValue,
    SetTimeSeriesDataInput,
    TimeSeriesData,
    TimeSeriesDataPayload,
    TimeSeriesPayload,
)
from .role import Role
from .system import (
    Charset,
    MediaType,
    MemoryInfo,
    MessageInfo,
    SystemInfo,
    TimeZone,
    Unit,
    UnitConversion,
)
from .timeseries import (
    Aggregation,
    Interval,
    Quality,
    QuotationBehavior,
    TimeSeries,
    TimeSeriesValue,
    TimeUnit,
    ValueAlignment,
    ValueAvailability,
)

__all__ = [
    # Common
    "PageInfo",
    "SortOrder",
    "ConflictAction",
    "NamedItemResult",
    "BackgroundJobResult",
    "TimeSeriesIdResult",
    # Inventory (Output)
    "Inventory",
    "InventoryType",
    "InventoryPropertyOutput",
    "InventoryRelationOutput",
    "RelationType",
    "DataType",
    "AssignableDataType",
    # Property Config (Output from GraphQL Queries)
    "StringConfig",
    "FileConfig",
    "TimeSeriesConfig",
    "IntervalInfo",
    # Inventory (Input)
    "InventoryProperty",
    "InventoryRelation",
    "StringPropertyConfig",
    "FilePropertyConfig",
    "TimeSeriesPropertyConfig",
    "IntervalConfig",
    "TimeSeriesSpecifics",
    "CreateTimeSeriesInput",
    # Namespace
    "Namespace",
    # Role
    "Role",
    # Permissions
    "InventoryPrivilege",
    "InventoryPropertyPrivilege",
    "PermissionState",
    # TimeSeries (gemeinsam genutzt of GraphQL and REST)
    "TimeUnit",
    "Aggregation",
    "Quality",
    "QuotationBehavior",
    "ValueAlignment",
    "ValueAvailability",
    "Interval",
    "TimeSeries",
    "TimeSeriesValue",
    # System
    "SystemInfo",
    "MemoryInfo",
    "MessageInfo",
    "TimeZone",
    "Unit",
    "UnitConversion",
    "Charset",
    "MediaType",
    # REST
    "TimeSeriesData",
    "TimeSeriesDataPayload",
    "SetTimeSeriesDataInput",
    "TimeSeriesPayload",
    "QuotationValue",
    "Quotations",
    "QuotationsPayload",
    "File",
    "ErrorPayload",
    "ErrorsPayload",
]
