"""REST transport layer for Questra Data."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

import requests

logger = logging.getLogger(__name__)


class RESTTransport:
    """
    Manages the REST transport layer with authentication.

    Responsible for:
    - HTTP requests to REST endpoints
    - Authentication via access token
    - Error handling
    """

    def __init__(self, base_url: str, get_access_token_func: Callable):
        """
        Initialize the REST transport.

        Args:
            base_url: Base URL of the REST API (e.g. https://dev.techstack.s2o.dev/dynamic-objects-v2/)
            get_access_token_func: Function that returns a valid access token
        """
        self._base_url = base_url.rstrip("/")
        self._get_access_token = get_access_token_func
        logger.debug(f"REST Transport initialized. base_url={self._base_url}")

    def _get_headers(
        self, additional_headers: dict[str, str] | None = None
    ) -> dict[str, str]:
        """
        Create HTTP headers with authentication.

        Args:
            additional_headers: Additional headers

        Returns:
            Dictionary with headers
        """
        access_token = self._get_access_token()

        # Mask token for logging
        masked_token = (
            f"{access_token[:4]}...{access_token[-4:]}"
            if len(access_token) > 8
            else "***"
        )
        logger.debug(
            f"Access token retrieved for REST request. token_preview={masked_token}"
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        if additional_headers:
            headers.update(additional_headers)

        return headers

    def _handle_response(self, response: requests.Response) -> Any:
        """
        Handle HTTP response and errors.

        Args:
            response: HTTP response object

        Returns:
            Parsed JSON, NDJSON stream or binary content

        Raises:
            Exception: On HTTP errors or ErrorsPayload in NDJSON stream
        """
        logger.debug(
            f"REST response received. status_code={response.status_code}, content_type={response.headers.get('Content-Type')}"
        )

        # Erfolgreiche Anfragen
        if 200 <= response.status_code < 300:
            content_type = response.headers.get("Content-Type", "")

            if response.content:
                # NDJSON (Newline Delimited JSON)
                if (
                    "application/x-ndjson" in content_type
                    or "application/ndjson" in content_type
                ):
                    try:
                        lines = response.text.strip().split("\n")
                        parsed_objects = [
                            json.loads(line) for line in lines if line.strip()
                        ]

                        # Check for ErrorsPayload in stream
                        for obj in parsed_objects:
                            if "errors" in obj:
                                errors = obj.get("errors", [])
                                if errors:
                                    error_msg = errors[0].get(
                                        "message", "Unknown error"
                                    )
                                    logger.error(
                                        f"ErrorsPayload in NDJSON stream. errors={errors}"
                                    )
                                    raise Exception(
                                        f"REST request returned errors: {error_msg}"
                                    )

                        logger.debug(
                            f"Parsed NDJSON response. object_count={len(parsed_objects)}"
                        )
                        return parsed_objects
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse NDJSON response: {e}")
                        raise Exception(f"Invalid NDJSON response: {e}")

                # JSON Content
                if "application/json" in content_type:
                    try:
                        result = response.json()
                        logger.debug(
                            f"Parsed JSON response. result_type={type(result).__name__}"
                        )
                        return result
                    except ValueError as e:
                        logger.warning(f"Failed to parse JSON response: {e}")
                        return response.text

                # Binary Content (z.B. Fileen) - as Fallback
                logger.debug(f"Returning binary content. size={len(response.content)}")
                return response.content

            # Leere Success Response (z.B. 200 OK without Body)
            return None

        # Fehlerbehandlung
        logger.error(
            f"REST request failed. status_code={response.status_code}, url={response.url}, response_text={response.text[:500]}"
        )

        # Versuche Error Payload to parsen
        try:
            error_data = response.json()
            error_msg = error_data.get("message", response.text)
        except ValueError:
            error_msg = response.text

        raise Exception(
            f"REST request failed with status {response.status_code}: {error_msg}"
        )

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        timeout: int = 30,
    ) -> Any:
        """
        Execute a GET request.

        Args:
            path: Path relative to base URL
            params: Query parameters
            timeout: Timeout in seconds

        Returns:
            Response data (JSON or Binary)
        """
        url = f"{self._base_url}{path}"
        headers = self._get_headers()

        logger.info(f"Executing REST GET request. url={url}, params={params}")

        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=timeout,
                verify=True,
            )
            result = self._handle_response(response)
            logger.info("REST GET request completed successfully")
            return result
        except requests.RequestException as e:
            logger.error(f"REST GET request failed. error={str(e)}, url={url}")
            raise

    def post(
        self,
        path: str,
        json: Any | None = None,
        files: dict[str, Any] | None = None,
        timeout: int = 30,
    ) -> Any:
        """
        Execute a POST request.

        Args:
            path: Path relative to base URL
            json: JSON data for the body
            files: Files for multipart upload
            timeout: Timeout in seconds

        Returns:
            Response data (JSON or binary)
        """
        url = f"{self._base_url}{path}"

        # If files are uploaded, do not set Content-Type header
        # (requests setzt automatisch multipart/form-data)
        if files:
            headers = self._get_headers()
            headers.pop("Content-Type", None)
            logger.info(
                f"Executing REST POST request with files. url={url}, file_count={len(files)}"
            )
        else:
            headers = self._get_headers()
            logger.info(
                f"Executing REST POST request. url={url}, has_json={json is not None}"
            )

        try:
            response = requests.post(
                url,
                headers=headers,
                json=json,
                files=files,
                timeout=timeout,
                verify=True,
            )
            result = self._handle_response(response)
            logger.info("REST POST request completed successfully")
            return result
        except requests.RequestException as e:
            logger.error(f"REST POST request failed. error={str(e)}, url={url}")
            raise

    def put(
        self,
        path: str,
        json: Any | None = None,
        timeout: int = 30,
    ) -> Any:
        """
        Execute a PUT request.

        Args:
            path: Path relative to base URL
            json: JSON data for the body
            timeout: Timeout in seconds

        Returns:
            Response data (JSON or binary)
        """
        url = f"{self._base_url}{path}"
        headers = self._get_headers()

        logger.info(
            f"Executing REST PUT request. url={url}, has_json={json is not None}"
        )

        try:
            response = requests.put(
                url,
                headers=headers,
                json=json,
                timeout=timeout,
                verify=True,
            )
            result = self._handle_response(response)
            logger.info("REST PUT request completed successfully")
            return result
        except requests.RequestException as e:
            logger.error(f"REST PUT request failed. error={str(e)}, url={url}")
            raise

    def delete(
        self,
        path: str,
        timeout: int = 30,
    ) -> Any:
        """
        Execute a DELETE request.

        Args:
            path: Path relative to base URL
            timeout: Timeout in seconds

        Returns:
            Response data (JSON or binary)
        """
        url = f"{self._base_url}{path}"
        headers = self._get_headers()

        logger.info(f"Executing REST DELETE request. url={url}")

        try:
            response = requests.delete(
                url,
                headers=headers,
                timeout=timeout,
                verify=True,
            )
            result = self._handle_response(response)
            logger.info("REST DELETE request completed successfully")
            return result
        except requests.RequestException as e:
            logger.error(f"REST DELETE request failed. error={str(e)}, url={url}")
            raise
