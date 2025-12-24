# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module providing client for interacting with the qBraid file management service.

"""
from __future__ import annotations

import base64
import logging
import mimetypes
import os
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Optional, Union

from qbraid_core.client import QbraidClient
from qbraid_core.exceptions import RequestsApiError
from qbraid_core.registry import register_client

from .exceptions import FileStorageServiceRequestError

logger = logging.getLogger(__name__)


@register_client()
class FileStorageClient(QbraidClient):
    """Client for interacting with the qBraid file management service."""

    def __init__(self, *args, namespace: Optional[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._default_namespace = namespace or "user"

    @property
    def default_namespace(self) -> str:
        """Return the default namespace."""
        return self._default_namespace

    def set_default_namespace(self, namespace: str) -> None:
        """Set the default namespace."""
        self._default_namespace = namespace

    def upload_file(
        self,
        file_path: Union[str, Path],
        namespace: Optional[str] = None,
        object_path: Optional[str] = None,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Upload a file to the qBraid file management service.

        Args:
            file_path (str): The path to the file to upload.
            namespace (str, optional): The qBraid namespace, or top-level container, in which
                to upload the file. Defaults to FileStorageClient.default_namespace.
            object_path (str, optional): The folder + filename in which to upload the file.
                Defaults to namespace home directory, and original filename.
            overwrite (bool): Whether to overwrite an existing file with the same name.
                Defaults to False.

        Raises:
            FileStorageServiceRequestError: If the file upload request fails.
            FileNotFoundError: If the file does not exist.
            ValueError: If the path is not a file, or file extension mismatch.

        Returns:
            dict[str, Any]: The response from the file upload request.
        """
        fpath = Path(file_path)
        file_path = str(fpath.resolve())

        if not fpath.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not fpath.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        payload = {"namespace": namespace or self.default_namespace, "overwrite": overwrite}

        if object_path:
            opath = Path(object_path)
            if opath.suffix and opath.suffix != fpath.suffix:
                raise ValueError(
                    f"File extension mismatch: {file_path} has extension '{fpath.suffix}', "
                    f"but object_path ends with extension '{opath.suffix}'."
                )

            payload["objectPath"] = object_path

        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = "application/octet-stream"

        try:
            with open(file_path, "rb") as file:
                file_data = (fpath.name, file, mime_type)
                files = {"file": file_data}

                response = self.session.post("/files/upload", files=files, data=payload)

                return response.json()
        except RequestsApiError as err:
            raise FileStorageServiceRequestError(f"Failed to upload file: {err}") from err
        except JSONDecodeError as err:
            raise FileStorageServiceRequestError(
                f"Failed to parse file upload response: {err}"
            ) from err

    def download_file(
        self,
        object_path: str,
        namespace: Optional[str] = None,
        save_path: Optional[Union[str, Path]] = None,
        overwrite: bool = False,
    ) -> Path:
        """Upload a file to the qBraid file management service.

        Args:
            object_path (str): The folder + filename describing the file to download.
                If just a filename is provided, the folder defaults to the namespace home directory.
            namespace (str, optional): The qBraid namespace, or top-level container, from which
                to download the file. Defaults to FileStorageClient.default_namespace.
            save_path (str, optional): The path to save the downloaded file. If not provided,
                the file will be saved to the current working directory.
            overwrite (bool): Whether to overwrite an existing file with the same name.
                Defaults to False.

        Raises:
            FileStorageServiceRequestError: If the file download request fails.
            FileExistsError: If the file already exists and overwrite is False.

        Returns:
            pathlib.Path: The path where the file was saved.

        """
        base64_obj = self._encode_to_base64(object_path)

        namespace = namespace or self.default_namespace

        try:
            response = self.session.get(f"/files/download/{namespace}/{base64_obj}")
        except RequestsApiError as err:
            raise FileStorageServiceRequestError(f"Failed to download file: {err}") from err

        content_disposition = response.headers.get("Content-Disposition", "")
        filename = (
            content_disposition.split("filename=")[-1].strip('"')
            if "filename=" in content_disposition
            else os.path.basename(object_path)
        )

        save_path = Path(save_path or os.getcwd()).resolve()
        file_save_path = save_path if save_path.suffix else save_path / filename

        if file_save_path.exists():
            if not overwrite:
                raise FileExistsError(f"The file already exists: {file_save_path}")

            logger.warning("Overwriting existing file: %s", file_save_path)

        with open(str(file_save_path), "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        logger.debug("File downloaded successfully: %s", file_save_path)

        return Path(file_save_path).resolve()

    @staticmethod
    def _encode_to_base64(s: str) -> str:
        """Encode a string to base64."""
        input_bytes = s.encode("utf-8")
        base64_bytes = base64.b64encode(input_bytes)
        return base64_bytes.decode("utf-8")
