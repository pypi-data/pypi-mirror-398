"""GraphQL transport layer for Questra Data."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, cast

from gql import Client
from gql.transport.exceptions import TransportQueryError
from gql.transport.requests import RequestsHTTPTransport

from .exceptions import QuestraGraphQLError

logger = logging.getLogger(__name__)


class GraphQLTransport:
    """
    Manages the GraphQL transport layer with authentication.

    Responsible for:
    - Creation and management of GraphQL client connection
    - Authentication via access token
    - Execution of GraphQL operations
    """

    def __init__(self, url: str, get_access_token_func: Callable):
        """
        Initialize the GraphQL transport.

        Args:
            url: GraphQL endpoint URL
            get_access_token_func: Function that returns a valid access token
        """
        self._url = url
        self._get_access_token = get_access_token_func
        self._client: Client | None = None
        logger.debug(f"GraphQL Transport initialized: {url}")

    def _create_transport(self, retries: int = 0) -> RequestsHTTPTransport:
        """
        Create a new HTTP transport with current access token.

        Args:
            retries: Number of retry attempts on errors (default: 0)

        Returns:
            Configured RequestsHTTPTransport
        """
        logger.debug(
            f"Creating new HTTP transport with fresh access token (retries={retries})"
        )
        access_token = self._get_access_token()

        # Mask token for logging (only first/last 4 characters)
        masked_token = (
            f"{access_token[:4]}...{access_token[-4:]}"
            if len(access_token) > 8
            else "***"
        )
        logger.debug(f"Access token retrieved: {masked_token}")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        return RequestsHTTPTransport(
            url=self._url,
            headers=headers,
            verify=True,
            retries=retries,
        )

    def get_client(self, retries: int = 0) -> Client:
        """
        Return the GraphQL client and create it if necessary.

        Args:
            retries: Number of retry attempts on errors (default: 0)

        Returns:
            Configured GQL client
        """
        logger.debug(f"Getting GraphQL client (retries={retries})")
        # Create a new transport on each call,
        # to ensure that the token is current
        transport = self._create_transport(retries=retries)
        self._client = Client(
            transport=transport,
            fetch_schema_from_transport=False,
        )
        logger.debug("GraphQL client created successfully")
        return self._client

    def execute(
        self, query: str, variables: dict[str, Any] | None = None, retries: int = 0
    ) -> dict[str, Any]:
        """
        Execute a GraphQL operation.

        Args:
            query: GraphQL query or mutation string
            variables: Optional variables for the operation
            retries: Number of retry attempts on errors (default: 0)

        Returns:
            Result of the GraphQL operation

        Raises:
            Exception: On GraphQL errors or network problems
        """
        from gql import gql

        # Extract Operation-Namen from Query
        operation_type = "query" if "query" in query.lower()[:50] else "mutation"
        query_preview = query[:100].replace("\n", " ").strip() + (
            "..." if len(query) > 100 else ""
        )

        has_vars = "with" if variables else "without"
        logger.info(
            f"Executing GraphQL {operation_type} {has_vars} variables (retries={retries}): {query_preview}"
        )
        logger.debug(f"GraphQL query: {query[:200]}... Variables: {variables}")

        client = self.get_client(retries=retries)
        document = gql(query)

        try:
            with client as session:
                result = cast(
                    dict[str, Any], session.execute(document, variable_values=variables)
                )
                result_keys = list(result.keys()) if isinstance(result, dict) else None
                logger.info(
                    f"GraphQL {operation_type} completed successfully. Result keys: {result_keys}"
                )
                logger.debug(f"GraphQL operation result: {result}")
                return result
        except TransportQueryError as e:
            # GraphQL error from server (e.g. Validation, Duplicate, etc.)
            logger.warning(
                f"GraphQL {operation_type} returned errors: {e.errors}. Query: {query_preview}"
            )

            # Extract first error (mostly there is only one)
            if e.errors:
                error = e.errors[0]
                error_message = error.get("message", "Unknown GraphQL error")
                extensions = error.get("extensions", {})
                error_code = extensions.get("code")
                placeholders = extensions.get("Placeholders", {})
                locations = error.get("locations", [])
                path = error.get("path", [])

                # Determine category from messageInfos (if available)
                # Heuristic: Categories are often in the code prefix (e.g. DATA_MODEL_*, VALIDATION_*)
                category = None
                if error_code and "_" in error_code:
                    category = error_code.split("_")[0].title()

                logger.debug(
                    f"Raising QuestraGraphQLError: code={error_code}, category={category}, placeholders={placeholders}"
                )

                raise QuestraGraphQLError(
                    message=error_message,
                    code=error_code,
                    category=category,
                    placeholders=placeholders,
                    locations=locations,
                    path=path,
                    extensions=extensions,
                ) from e

            # Fallback: Keine strukturierten Fehler
            logger.error(f"TransportQueryError without structured errors: {e}")
            raise QuestraGraphQLError(
                message=str(e),
                code=None,
                category=None,
            ) from e

        except Exception as e:
            logger.error(f"GraphQL {operation_type} failed: {e}")
            logger.exception("Full exception traceback:")
            raise
