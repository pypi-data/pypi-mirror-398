"""
Questra Data - Python client for Dyno GraphQL and REST API.

Provides two APIs:
1. High-Level API (QuestraData) - Recommended
2. Low-Level API (QuestraDataCore) - For advanced operations

Example (High-Level API):
    ```python
    from seven2one.questra.authentication import QuestraAuthentication
    from seven2one.questra.data import QuestraData
    from datetime import datetime

    auth = QuestraAuthentication(
        url="https://authentik.example.com", username="user", password="pass"
    )

    client = QuestraData(graphql_url="https://example.com/graphql", auth_client=auth)

    # List inventory items
    items = client.list(inventory_name="Products", namespace="Shop")
    ```

Example (Low-Level API):
    ```python
    from seven2one.questra.authentication import QuestraAuthentication
    from seven2one.questra.data import QuestraDataCore

    auth = QuestraAuthentication(
        url="https://authentik.example.com", username="user", password="pass"
    )

    client = QuestraDataCore(
        graphql_url="https://example.com/graphql", auth_client=auth
    )

    inventories = client.queries.get_inventories()
    ```
"""

import logging
import os
import sys

# Configure root logger based on environment variables
LOG_LEVEL = os.getenv("questra_data_LOG_LEVEL", "WARNING")
LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.WARNING),
    format=LOG_FORMAT,
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

# Optional: File handler if LOG_FILE is set
LOG_FILE = os.getenv("questra_data_LOG_FILE")
if LOG_FILE:
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
    )
    logging.getLogger().addHandler(file_handler)

logger = logging.getLogger(__name__)
logger.debug("Questra Data logger initialized")

from .client import QuestraDataCore
from .exceptions import QuestraError, QuestraGraphQLError
from .highlevel_client import QuestraData
from .models import (
    Aggregation,  # Timeseries Modelle (gemeinsam genutzt)
    AssignableDataType,
    ConflictAction,
    CreateTimeSeriesInput,
    DataType,
    FileConfig,
    FilePropertyConfig,
    Interval,
    IntervalConfig,
    IntervalInfo,
    Inventory,
    InventoryPrivilege,
    InventoryProperty,
    InventoryPropertyPrivilege,
    InventoryRelation,
    InventoryType,
    Namespace,
    PageInfo,
    PermissionState,
    Quality,
    QuotationBehavior,
    RelationType,
    Role,
    SortOrder,
    StringConfig,
    StringPropertyConfig,
    TimeSeries,
    TimeSeriesConfig,
    TimeSeriesPropertyConfig,
    TimeSeriesSpecifics,
    TimeSeriesValue,
    TimeUnit,
    TimeZone,
    Unit,
    ValueAlignment,
    ValueAvailability,
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
    LongProperty,
    StringProperty,
    TimeProperty,
    TimeSeriesProperty,
)
from .models.rest import (
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
from .results import QueryResult, TimeSeriesResult

__version__ = "0.1.0"

__all__ = [
    # Main classes
    "QuestraData",  # High-Level API (recommended)
    "QuestraDataCore",  # Low-Level API
    "QueryResult",  # Query result wrapper with .to_df() support
    "TimeSeriesResult",  # TimeSeries result wrapper with .to_df() support
    # Exceptions
    "QuestraError",  # Base exception
    "QuestraGraphQLError",  # GraphQL errors from server
    # GraphQL Models
    "Inventory",
    "InventoryType",
    "InventoryProperty",
    "InventoryRelation",
    "Namespace",
    "Role",
    "Unit",
    "TimeZone",
    "PageInfo",
    # GraphQL Enums
    "SortOrder",
    "ConflictAction",
    "RelationType",
    "DataType",
    "AssignableDataType",
    # Input Models (for create_inventory)
    "StringPropertyConfig",
    "FilePropertyConfig",
    "TimeSeriesPropertyConfig",
    "TimeSeriesSpecifics",
    "IntervalConfig",
    "CreateTimeSeriesInput",
    # Specialized Property classes (simplified API)
    "StringProperty",
    "IntProperty",
    "LongProperty",
    "DecimalProperty",
    "BoolProperty",
    "DateTimeProperty",
    "DateTimeOffsetProperty",
    "DateProperty",
    "TimeProperty",
    "GuidProperty",
    "FileProperty",
    "TimeSeriesProperty",
    # Output Config Models (from Query Responses)
    "StringConfig",
    "FileConfig",
    "TimeSeriesConfig",
    "IntervalInfo",
    # Permissions
    "InventoryPrivilege",
    "InventoryPropertyPrivilege",
    "PermissionState",
    # TimeSeries Models (shared by GraphQL and REST)
    "TimeUnit",
    "Aggregation",
    "Quality",
    "QuotationBehavior",
    "ValueAlignment",
    "ValueAvailability",
    "Interval",
    "TimeSeries",
    "TimeSeriesValue",
    # REST-specific Models
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
