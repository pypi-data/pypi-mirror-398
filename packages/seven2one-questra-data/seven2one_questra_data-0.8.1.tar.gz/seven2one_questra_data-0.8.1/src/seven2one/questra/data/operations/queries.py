"""GraphQL query operations for Questra Data."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

from ..models import Inventory, Namespace, Role, SystemInfo, TimeZone, Unit


class QueryOperations:
    """
    Query operations for Dyno GraphQL API.

    Responsible for:
    - Querying inventories
    - Querying namespaces
    - Querying roles
    - Querying system information
    """

    def __init__(self, execute_func: Callable):
        """
        Initialize the query operations.

        Args:
            execute_func: Function to execute GraphQL queries
        """
        self._execute = execute_func

    def get_inventories(
        self,
        where: dict[str, Any] | None = None,
        order: dict[str, str] | None = None,
    ) -> list[Inventory]:
        """
        Retrieve a list of inventories.

        Args:
            where: Filter conditions (namespaceNames, inventoryNames).
                Example: {"namespaceNames": ["MyNamespace"], "inventoryNames": ["MyInventory"]}
            order: Sorting (by: NAME)

        Returns:
            list[Inventory]: List of inventories (without pagination)
        """
        logger.debug(f"Getting inventories. where={where}, order={order}")

        query = """
            query GetInventories(
                $where: _InventoryFilter__InputType
                $order: _InventorySort__InputType
            ) {
                _inventories(
                    where: $where
                    order: $order
                ) {
                    name
                    description
                    inventoryType
                    auditEnabled
                    createdBy
                    createdAt
                    alteredBy
                    alteredAt
                    selectFieldName
                    insertFieldName
                    updateFieldName
                    deleteFieldName
                    namespace {
                        name
                    }
                    properties {
                        name
                        fieldName
                        sortOrder
                        dataType
                        isRequired
                        isUnique
                        isArray
                        description
                        string {
                            maxLength
                            isCaseSensitive
                        }
                        file {
                            maxLength
                        }
                        timeSeries {
                            interval {
                                multiplier
                                timeUnit
                            }
                            unit
                            timeZone
                            specificsPerInstanceAllowed
                            valueAlignment
                            valueAvailability
                            defaultAggregation
                            startOfTime
                            auditEnabled
                            quotationEnabled
                            defaultQuotationBehavior
                        }
                    }
                    parentRelations {
                        relationType
                        isRequired
                    }
                    childRelations {
                        relationType
                        isRequired
                    }
                }
            }
        """

        variables = {
            "where": where,
            "order": order,
        }

        result = self._execute(query, variables)
        inventories_data = result["_inventories"]

        inventories = [
            Inventory.model_validate(inv_data) for inv_data in inventories_data
        ]
        logger.info(f"Retrieved {len(inventories)} inventories")
        return inventories

    def get_namespaces(self) -> list[Namespace]:
        """
        Retrieve a list of namespaces.

        Returns:
            list[Namespace]: List of namespaces
        """
        logger.debug("Getting namespaces")

        query = """
            query GetNamespaces {
                _namespaces {
                    name
                    description
                    isSystem
                    createdBy
                    createdAt
                    alteredBy
                    alteredAt
                }
            }
        """

        result = self._execute(query)
        namespaces_data = result["_namespaces"]

        namespaces = [Namespace.model_validate(ns_data) for ns_data in namespaces_data]
        logger.info(f"Retrieved {len(namespaces)} namespaces")
        return namespaces

    def get_roles(self) -> list[Role]:
        """
        Retrieve a list of roles.

        Returns:
            list[Role]: List of roles (without pagination)
        """
        logger.debug("Getting roles")

        query = """
            query GetRoles {
                _roles {
                    name
                    description
                    isSystem
                    createdBy
                    createdAt
                    alteredBy
                    alteredAt
                }
            }
        """

        result = self._execute(query)
        roles_data = result["_roles"]

        roles = [Role.model_validate(role_data) for role_data in roles_data]
        logger.info(f"Retrieved {len(roles)} roles")
        return roles

    def get_system_info(self, include_message_infos: bool = False) -> SystemInfo:
        """
        Retrieve system information.

        Args:
            include_message_infos: If True, messageInfos will be included

        Returns:
            SystemInfo: Object with system information
        """
        logger.debug(
            f"Getting system info. include_message_infos={include_message_infos}"
        )

        message_infos_fragment = (
            """
                    messageInfos {
                        code
                        template
                        category
                    }
        """
            if include_message_infos
            else ""
        )

        query = f"""
            query GetSystemInfo {{
                _systemInfo {{
                    dynamicObjectsVersion
                    databaseVersion
                    memoryInfo {{
                        totalMb
                        usedMb
                        freeMb
                        availablePercent
                    }}{message_infos_fragment}
                }}
            }}
        """

        result = self._execute(query)
        system_info_data = result["_systemInfo"]
        system_info = SystemInfo.model_validate(system_info_data)
        logger.info(
            f"Retrieved system info. version={system_info.dynamic_objects_version}"
        )
        return system_info

    def get_units(self) -> list[Unit]:
        """
        Retrieve all units.

        Returns:
            list[Unit]: List of units
        """
        logger.debug("Getting units")

        query = """
            query GetUnits {
                _units {
                    symbol
                    aggregation
                }
            }
        """

        result = self._execute(query)
        units_data = result["_units"]
        units = [Unit.model_validate(u) for u in units_data]
        logger.info(f"Retrieved {len(units)} units")
        return units

    def get_time_zones(self) -> list[TimeZone]:
        """
        Retrieve all time zones.

        Returns:
            list[TimeZone]: List of time zones
        """
        logger.debug("Getting time zones")

        query = """
            query GetTimeZones {
                _timeZones {
                    name
                    baseUtcOffset
                    supportsDaylightSavingTime
                }
            }
        """

        result = self._execute(query)
        time_zones_data = result["_timeZones"]
        time_zones = [TimeZone.model_validate(tz) for tz in time_zones_data]
        logger.info(f"Retrieved {len(time_zones)} time zones")
        return time_zones

    def get_timeseries(self, timeseries_ids: list[int]) -> list:
        """
        Retrieve timeseries metadata for the specified IDs.

        Args:
            timeseries_ids: List of timeseries IDs

        Returns:
            list: List of timeseries objects
        """
        from ..models.timeseries import TimeSeries

        logger.debug(f"Getting {len(timeseries_ids)} timeseries metadata")

        query = """
            query GetTimeSeries($input: _GetTimeSeries__InputType!) {
                _timeSeries(input: $input) {
                    id
                    createdBy
                    createdAt
                    alteredBy
                    alteredAt
                    interval {
                        timeUnit
                        multiplier
                    }
                    valueAlignment
                    valueAvailability
                    unit
                    timeZone
                    defaultAggregation
                    startOfTime
                    auditEnabled
                    quotationEnabled
                    defaultQuotationBehavior
                    inventoryItemId
                }
            }
        """

        variables = {
            "input": {"timeSeriesIds": [str(ts_id) for ts_id in timeseries_ids]}
        }

        result = self._execute(query, variables)
        timeseries_data = result["_timeSeries"]
        timeseries = [TimeSeries.model_validate(ts) for ts in timeseries_data]
        logger.info(f"Retrieved {len(timeseries)} timeseries metadata")
        return timeseries
