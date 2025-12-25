"""
Manager classes for specialized operations.

Organizes the high-level API into focused, reusable components.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

from typing import TYPE_CHECKING

from .models import Namespace, Role, SystemInfo, TimeZone, Unit

if TYPE_CHECKING:
    from .client import QuestraDataCore


class BaseManager:
    """Base class for all managers."""

    def __init__(self, client: QuestraDataCore):
        """
        Initialize the Manager.

        Args:
            client: QuestraDataCore client for low-level operations
        """
        self._client = client


class CatalogManager(BaseManager):
    """
    Manager for catalog operations (system info, roles, units, time zones).

    Provides access to system-wide metadata and catalog information.
    """

    def get_system_info(self) -> SystemInfo:
        """
        Retrieve system information.

        Returns:
            SystemInfo: System information including version

        Examples:
            ```python
            info = client.catalog.get_system_info()
            print(f"System Version: {info.version}")
            ```
        """
        logger.info("Getting system info")
        return self._client.queries.get_system_info()

    def list_namespaces(self) -> list[Namespace]:
        """
        List all namespaces.

        Returns:
            list[Namespace]: List of namespace objects

        Examples:
            ```python
            namespaces = client.catalog.list_namespaces()
            for ns in namespaces:
                print(f"- {ns.name}: {ns.description}")
            ```
        """
        logger.info("Listing namespaces")
        return self._client.queries.get_namespaces()

    def list_roles(self) -> list[Role]:
        """
        List all roles.

        Returns:
            list[Role]: List of role objects

        Examples:
            ```python
            roles = client.catalog.list_roles()
            for role in roles:
                print(f"- {role.name}: {role.description}")
            ```
        """
        logger.info("Listing roles")
        return self._client.queries.get_roles()

    def list_units(self) -> list[Unit]:
        """
        List all units.

        Returns:
            list[Unit]: List of unit objects

        Examples:
            ```python
            units = client.catalog.list_units()
            for unit in units:
                print(f"- {unit.symbol}: {unit.aggregation}")
            ```
        """
        logger.info("Listing units")
        return self._client.queries.get_units()

    def list_time_zones(self) -> list[TimeZone]:
        """
        List all available time zones.

        Returns:
            list[TimeZone]: List of time zone objects

        Examples:
            ```python
            time_zones = client.catalog.list_time_zones()
            for tz in time_zones:
                print(f"- {tz.name}: UTC{tz.base_utc_offset}")
            ```
        """
        logger.info("Listing time zones")
        return self._client.queries.get_time_zones()
