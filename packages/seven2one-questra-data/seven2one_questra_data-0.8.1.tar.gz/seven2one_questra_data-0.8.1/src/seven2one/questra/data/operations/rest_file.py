"""REST operations for File endpoints."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import BinaryIO

logger = logging.getLogger(__name__)

from ..models.rest import File


class FileOperations:
    """
    REST operations for file endpoints.

    Provides methods for uploading and downloading files.
    """

    def __init__(self, rest_get_func: Callable, rest_post_func: Callable):
        """
        Initialize the file operations.

        Args:
            rest_get_func: Function for GET requests
            rest_post_func: Function for POST requests
        """
        self._get = rest_get_func
        self._post = rest_post_func
        logger.debug("FileOperations initialized")

    def download(self, file_id: int) -> bytes:
        """
        Download a file.

        Args:
            file_id: File ID (LongNumberString as str)

        Returns:
            bytes: File content as bytes
        """
        logger.info(f"Downloading file with ID {file_id}")
        result = self._get(f"/file/{file_id}")
        logger.info(f"File downloaded successfully, size: {len(result)} bytes")
        return result

    def upload(
        self,
        files: Sequence[tuple[str, str | Path | BinaryIO, str, str]],
    ) -> list[File]:
        """
        Upload one or more files.

        Args:
            files: List of tuples (name, file_data, filename, content_type)
                - name: Name in format "Namespace.Inventory.Property" or "Inventory.Property"
                - file_data: File path (str/Path) or file object (BinaryIO)
                - filename: Original filename (e.g. 'document.pdf')
                - content_type: MIME type (e.g. 'application/pdf')

        Returns:
            list[File]: List of file objects with metadata

        Examples:
            ```python
            # Upload with Filepfad
            result = client.files.upload(
                [
                    (
                        "MyInventory.DocumentProperty",
                        "/path/to/file.pdf",
                        "file.pdf",
                        "application/pdf",
                    )
                ]
            )

            # Upload with File-Objekt
            with open("file.pdf", "rb") as f:
                result = client.files.upload(
                    [("MyInventory.DocumentProperty", f, "file.pdf", "application/pdf")]
                )
            ```
        """
        logger.info(f"Uploading {len(files)} file(s)")

        # Convert Files to requests-Format
        files_dict = {}
        opened_files = []

        try:
            for idx, (name, file_data, filename, content_type) in enumerate(files):
                # If file_data is a path, open the file
                if isinstance(file_data, (str, Path)):
                    file_obj = open(file_data, "rb")
                    opened_files.append(file_obj)
                else:
                    file_obj = file_data

                # Format: (filename, file_object, content_type)
                files_dict[name] = (filename, file_obj, content_type)

            # POST with multipart/form-data
            result = self._post("/file/upload", files=files_dict)

            # Parse Response - Pydantic converts automatically through aliases
            file_objects = [File.model_validate(file_data) for file_data in result]

            logger.info(f"Successfully uploaded {len(file_objects)} file(s)")
            return file_objects

        finally:
            # Close all opened files
            for file_obj in opened_files:
                try:
                    file_obj.close()
                except Exception as e:
                    logger.warning(f"Failed to close file: {e}")

    def upload_single(
        self,
        name: str,
        file_data: str | Path | BinaryIO,
        filename: str,
        content_type: str,
    ) -> File:
        """
        Uploads a single file (convenience method).

        Args:
            name: Name im Format "Namespace.Inventory.Property" or "Inventory.Property"
            file_data: File path (str/Path) or file object (BinaryIO)
            filename: Original filename (e.g. 'document.pdf')
            content_type: MIME type (e.g. 'application/pdf')

        Returns:
            File: Object with metadata

        Examples:
            ```python
            result = client.files.upload_single(
                name="MyInventory.DocumentProperty",
                file_data="/path/to/file.pdf",
                filename="file.pdf",
                content_type="application/pdf",
            )
            ```
        """
        result = self.upload([(name, file_data, filename, content_type)])
        return result[0]
