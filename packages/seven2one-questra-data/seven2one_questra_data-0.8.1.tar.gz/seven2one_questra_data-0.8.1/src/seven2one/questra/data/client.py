"""Low-level API client for Questra Data.

Provides direct access to GraphQL and REST operations.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)
from seven2one.questra.authentication import QuestraAuthentication

from .operations import (
    AuditOperations,
    DynamicInventoryOperations,
    FileOperations,
    MutationOperations,
    QueryOperations,
    TimeSeriesOperations,
)
from .rest_transport import RESTTransport
from .transport import GraphQLTransport


class QuestraDataCore:
    """Low-level client for Questra Data API.

    Args:
        graphql_url: GraphQL endpoint URL
        auth_client: Authenticated QuestraAuthentication instance
        rest_base_url: REST API base URL (auto-derived if not provided)

    Raises:
        ValueError: If auth_client is not authenticated

    Example:
        ```python
        from seven2one.questra.authentication import QuestraAuthentication
        from seven2one.questra.data import QuestraDataCore

        auth = QuestraAuthentication(...)
        client = QuestraDataCore(
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
        logger.info(
            f"Initializing QuestraDataCore. graphql_url={graphql_url}, rest_base_url={rest_base_url}"
        )

        self._graphql_url = graphql_url
        self._auth_client = auth_client

        # Derive REST URL from GraphQL URL if not provided
        if rest_base_url is None:
            # Remove '/graphql' from the end of the URL
            self._rest_base_url = graphql_url.replace("/graphql", "/")
            logger.debug(
                f"REST base URL derived from GraphQL URL: {self._rest_base_url}"
            )
        else:
            self._rest_base_url = rest_base_url

        # Check if QuestraAuthentication is authenticated
        if not self._auth_client.is_authenticated():
            logger.error("QuestraAuthentication is not authenticated")
            raise ValueError(
                "QuestraAuthentication is not authenticated. "
                "Please authenticate the client before passing it."
            )

        logger.debug("QuestraAuthentication authentication verified")

        # Initialize GraphQL Transport
        self._transport = GraphQLTransport(
            url=graphql_url,
            get_access_token_func=self._auth_client.get_access_token,
        )

        # Initialize REST Transport
        self._rest_transport = RESTTransport(
            base_url=self._rest_base_url,
            get_access_token_func=self._auth_client.get_access_token,
        )

        # Initialize GraphQL Operations
        self._queries = QueryOperations(execute_func=self._transport.execute)
        self._mutations = MutationOperations(execute_func=self._transport.execute)
        self._inventory = DynamicInventoryOperations(
            execute_func=self._transport.execute
        )

        # Initialize REST Operations
        self._timeseries = TimeSeriesOperations(
            rest_get_func=self._rest_transport.get,
            rest_post_func=self._rest_transport.post,
        )
        self._files = FileOperations(
            rest_get_func=self._rest_transport.get,
            rest_post_func=self._rest_transport.post,
        )
        self._audit = AuditOperations(
            rest_get_func=self._rest_transport.get,
        )

        logger.info("QuestraDataCore initialized successfully")

    @property
    def queries(self) -> QueryOperations:
        """Access to GraphQL query operations."""
        return self._queries

    @property
    def mutations(self) -> MutationOperations:
        """Access to GraphQL mutation operations."""
        return self._mutations

    @property
    def inventory(self) -> DynamicInventoryOperations:
        """Access to dynamic inventory operations."""
        return self._inventory

    @property
    def timeseries(self) -> TimeSeriesOperations:
        """Access to time series operations."""
        return self._timeseries

    @property
    def files(self) -> FileOperations:
        """Access to file operations."""
        return self._files

    @property
    def audit(self) -> AuditOperations:
        """Access to audit operations."""
        return self._audit

    def execute_raw(self, query: str, variables: dict | None = None) -> dict:
        """Execute raw GraphQL query.

        Args:
            query: GraphQL query string
            variables: Optional query variables

        Returns:
            GraphQL response data
        """
        logger.debug("Executing raw GraphQL operation via QuestraDataCore")
        return self._transport.execute(query, variables)

    def is_authenticated(self) -> bool:
        """Check if authentication is valid."""
        return self._auth_client.is_authenticated()

    def reauthenticate(self) -> None:
        """Force reauthentication."""
        logger.info("Forcing reauthentication")
        self._auth_client.reauthenticate()
        logger.info("Reauthentication completed")

    @property
    def graphql_url(self) -> str:
        """GraphQL endpoint URL."""
        return self._graphql_url

    @property
    def rest_base_url(self) -> str:
        """REST API base URL."""
        return self._rest_base_url

    def __repr__(self) -> str:
        auth_status = (
            "authenticated" if self.is_authenticated() else "not authenticated"
        )
        return (
            f"QuestraDataCore(graphql_url='{self._graphql_url}', "
            f"rest_url='{self._rest_base_url}', status='{auth_status}')"
        )
