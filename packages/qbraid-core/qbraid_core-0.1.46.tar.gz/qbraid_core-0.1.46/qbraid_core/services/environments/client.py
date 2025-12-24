# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module providing client for interacting with qBraid environments service.

"""
import logging
import time
from pathlib import Path
from typing import Any, Optional

import yaml

from qbraid_core.client import QbraidClient
from qbraid_core.exceptions import AuthError, RequestsApiError
from qbraid_core.registry import register_client
from qbraid_core.system.executables import get_python_executables

from .exceptions import EnvironmentServiceRequestError
from .paths import get_default_envs_paths
from .schema import EnvironmentConfig
from .validate import is_valid_env_name, is_valid_slug

logger = logging.getLogger(__name__)


@register_client()
class EnvironmentManagerClient(QbraidClient):
    """Client for interacting with qBraid environment services."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.envs_paths = get_default_envs_paths()

    @property
    def envs_paths(self) -> list[Path]:
        """Returns a dictionary of environment paths.

        Returns:
            A dictionary containing the environment paths.
        """
        return self._envs_paths

    @envs_paths.setter
    def envs_paths(self, value: list[Path]):
        """Sets the qBraid environments paths."""
        self._envs_paths = value

    def _validate_python_version(self, python_version: str) -> None:
        """Checks if the given python version is valid according to the system and conda
        python installations.

        Args:
            python_version: The python version to check.

        Returns:
            True if the python version is valid, False otherwise.
        """
        python_versions = get_python_executables()

        system_py_versions = python_versions["system"]
        value_in_system = python_version in system_py_versions

        conda_py_versions = python_versions["conda"]
        value_in_conda = python_version in conda_py_versions

        qbraid_client = None

        try:
            qbraid_client = QbraidClient()
        except (AuthError, EnvironmentServiceRequestError) as err:
            logger.error("Error creating QbraidClient: %s", err)

        if qbraid_client and qbraid_client.running_in_lab() is True:
            if value_in_system is False and value_in_conda is False:
                raise ValueError(
                    f"Python version '{python_version}' not found in system or conda"
                    " python installations"
                )
        else:
            if value_in_system is False:
                logger.warning(
                    "Python version '%s' not found in system python installations", python_version
                )
            # set the default here
            python_version = list(python_versions["system"].keys())[0]

        logger.info("Using python version '%s' for custom environment", python_version)

    def remote_publish_environment(
        self,
        config: Optional[EnvironmentConfig] = None,
        file_path: Optional[str] = None,
        persist_env: Optional[bool] = False,
    ) -> dict:
        """Triggers the remote publish of a custom environment.

        Args:
            config: Environment configuration.
            file_path: Path to the environment YAML file.
            persist_env: Whether to persist the environment in user space.

        Returns:
            A dictionary containing the response data.
        """
        if config and file_path:
            raise ValueError(
                "Only one of YAML file or config data can be provided for env creation"
            )

        if not config and not file_path:
            raise ValueError("Either YAML file or config data must be provided for env creation")

        # 1. Prepare files for request
        req_files = {}
        icon_path = str(config.icon) if config else ""

        if file_path:
            # ensure file exists
            if not Path(file_path).exists():
                raise ValueError(f"Env config file not found at path: {file_path}")
            yaml_file = open(file_path, "rb")  # pylint: disable=consider-using-with
            req_files["yamlFile"] = (Path(file_path).stem, yaml_file, "text/yaml")

            with open(file_path, "r", encoding="utf-8") as f:
                icon_path = str(yaml.safe_load(f)["icon"])

        if not Path(icon_path).exists():
            raise ValueError(f"Icon file not found at path: {icon_path}")
        # need to pass an open file object to requests
        img_file = open(icon_path, "rb")  # pylint: disable=consider-using-with
        req_files["iconFile"] = (Path(icon_path).stem, img_file, "image/png")

        # 2. Prepare request body
        req_body = {
            "persistEnv": persist_env,
            "config": config.model_dump_json(by_alias=True) if config else None,
        }
        try:
            env_publish_data = self.session.post(
                "/environments/remote/publish", data=req_body, files=req_files
            ).json()
        except RequestsApiError as err:
            raise EnvironmentServiceRequestError(
                f"Remote publish environment request failed: {err}"
            ) from err

        if (
            env_publish_data is None
            or len(env_publish_data) == 0
            or env_publish_data.get("envSlug") is None
        ):
            raise EnvironmentServiceRequestError(
                f"Remote publish environment request responded with invalid data: "
                f"{env_publish_data}",
            )

        return env_publish_data

    def retrieve_remote_publish_status(self, env_slug: str) -> dict:
        """Retrieves the status of the remote publish request for the given environment slug.

        Args:
            env_slug: The slug of the environment to retrieve the status for.

        Returns:
            A dictionary containing the response data.
        """
        try:
            env_publish_status = self.session.get(
                "/environments/remote/publish/status", params={"envSlug": env_slug}
            ).json()
        except RequestsApiError as err:
            raise EnvironmentServiceRequestError(
                f"Request failed to retrieve remote publish status: {err}"
            ) from err

        if (
            env_publish_status is None
            or len(env_publish_status) == 0
            or env_publish_status.get("status") is None
        ):
            raise EnvironmentServiceRequestError(
                f"Request failed to retrieve remote publish status: {env_publish_status}",
            )

        return env_publish_status["status"]

    def wait_for_env_remote_publish(
        self, env_slug: str, timeout: Optional[int] = None, poll_interval: int = 20
    ) -> bool:
        """Monitors the remote publish status of the given environment slug by polling the remote
        create status field.

        Args:
            env_slug: The slug of the environment to monitor the status for.
            timeout: The maximum time to wait for the remote publish to complete.
            poll_interval: The time interval in seconds to poll the remote publish
                           status.
        Raises:
            TimeoutError: If the remote publish status is not complete within the timeout period.

        Returns:
            success: True if the remote publish was successful, False otherwise.
        """
        # default wait time is 10 minutes
        retries = timeout // poll_interval if timeout else 30
        status = None

        for retry in range(retries):
            status = self.retrieve_remote_publish_status(env_slug)
            logger.info("Remote publish status: %s", status)
            if status in ["COMPLETE", "FAILED"]:
                break

            if retry == retries - 1:
                raise TimeoutError(
                    f"Remote env publish not complete within timeout period, final status: {status}"
                )

            logger.info("Retrying in %d seconds", poll_interval)
            time.sleep(poll_interval)

        return status == "COMPLETE"

    def create_environment(self, config: EnvironmentConfig) -> dict[str, Any]:
        """Creates a new environment with the given configruation

        Args:
            config: Environment configuration.

        Returns:
            A dictionary containing the environment data.

        Raises:
            ValueError: If the environment name is invalid or the description is too long.
            EnvironmentServiceRequestError: If the create environment request fails.
        """
        if not is_valid_env_name(config.name):
            raise ValueError(f"Invalid environment name: {config.name}")

        if config.description and len(config.description) > 300:
            raise ValueError("Description is too long. Maximum length is 300 characters.")

        if config.python_version:
            self._validate_python_version(config.python_version)

        req_body = {}
        req_files = {}

        req_body.update(config.model_dump(by_alias=True))
        # TODO: update API to remove below logic

        # rename fields to conform with API request
        req_body["code"] = req_body.pop("pythonPackages")
        req_body["prompt"] = req_body.pop("shellPrompt")

        if config.icon:
            # need to pass an open file object to requests
            img_file = open(config.icon, "rb")  # pylint: disable=consider-using-with
            req_files["image"] = (Path(config.icon).stem, img_file, "image/png")

        try:
            env_data = self.session.post(
                "/environments/create", data=req_body, files=req_files
            ).json()
        except RequestsApiError as err:
            raise EnvironmentServiceRequestError(
                f"Create environment request failed: {err}"
            ) from err

        if env_data is None or len(env_data) == 0 or env_data.get("slug") is None:
            raise EnvironmentServiceRequestError(
                "Create environment request responded with invalid environment data"
            )

        return env_data

    def delete_environment(self, slug: str) -> None:
        """Deletes the environment with the given slug.

        Args:
            slug: The slug of the environment to delete.

        Returns:
            None

        Raises:
            ValueError: If the environment slug is invalid.
            EnvironmentServiceRequestError: If the delete environment request fails.
        """
        if not is_valid_slug(slug):
            raise ValueError(f"Invalid environment slug: {slug}")

        try:
            self.session.delete(f"/environments/{slug}")
        except RequestsApiError as err:
            raise EnvironmentServiceRequestError(
                f"Delete environment request failed: {err}"
            ) from err
