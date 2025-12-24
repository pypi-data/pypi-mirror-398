# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module for making requests to the qBraid API.

"""
import configparser
import logging
import os
import warnings
from typing import TYPE_CHECKING, Any, Optional, Union
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.exceptions import InsecureRequestWarning

from ._compat import __version__
from .config import (
    DEFAULT_CONFIG_SECTION,
    DEFAULT_ENDPOINT_URL,
    DEFAULT_ENDPOINT_URL_V1,
    DEFAULT_ORGANIZATION,
    DEFAULT_WORKSPACE,
    SUPPORTED_WORKSPACES,
    load_config,
)
from .config import save_config as save_user_config
from .config import (
    update_config_option,
)
from .exceptions import AuthError, ConfigError, RequestsApiError, UserNotFoundError
from .registry import client_registry, discover_services
from .retry import STATUS_FORCELIST, PostForcelistRetry

if TYPE_CHECKING:
    import qbraid_core

logger = logging.getLogger(__name__)


class Session(requests.Session):
    """Custom session with handling of request urls and authentication.

    This is a child class of :py:class:`requests.Session`. It handles
    authentication with custom headers,and retries on specific 5xx errors.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *args,
        base_url: Optional[str] = None,
        headers: Optional[dict[str, Any]] = None,
        auth_headers: Optional[dict[str, Any]] = None,
        **kwargs,
    ):
        """
        Initialize custom session with default base_url and auth_headers.

        Args:
            base_url (optional, str): Base URL to prepend to all requests.
            headers (optional, dict): Dictionary of headers to include in all requests.
            auth_headers (optional, dict): Dictionary of authorization headers to include in all
                requests. Values will be masked in error messages.
        """
        super().__init__(*args, **kwargs)
        self.base_url = base_url
        self.auth_headers = {}
        if auth_headers:
            self.auth_headers.update(auth_headers)
        if headers:
            self.headers.update(headers)
        self.headers.update(self.auth_headers)
        self.headers["User-Agent"] = self._user_agent()
        self._raise_for_status = True

    @property
    def base_url(self) -> Optional[str]:
        """Return the base URL."""
        return self._base_url

    @base_url.setter
    def base_url(self, value: Optional[str]) -> None:
        """Set the base URL."""
        self._base_url = value

    def _user_agent(self) -> str:
        """Return the user agent string."""
        return f"QbraidCore/{__version__}"

    def add_user_agent(self, user_agent: str) -> None:
        """Updates the User-Agent header with additional information.

        Args:
            user_agent (str): Additional user agent information to append.
        """
        if user_agent not in self.headers["User-Agent"]:
            self.headers["User-Agent"] = f"{self.headers['User-Agent']} {user_agent}"

    def initialize_retry(
        self,
        total: int = 2,
        connect: int = 1,
        backoff_factor: float = 0.5,
        status_forcelist: Union[list[int], set[int], tuple[int, ...]] = STATUS_FORCELIST,
        **kwargs,
    ) -> None:
        """Set the session retry policy.

        Args:
            total (int): Number of total retries for the requests. Default 2.
            connect (int): Number of connect retries for the requests. Default 1.
            backoff_factor (float): Backoff factor between retry attempts. Default 0.5.
            status_forcelist (Union[list[int], set[int], tuple[int, ...]]): List of status
                codes to force a retry on.
        """
        # Raising an exception on status code is handled by the request method.
        raise_on_status = kwargs.pop("raise_on_status", True)
        if not isinstance(raise_on_status, bool):
            raise ValueError("raise_on_status must be a boolean.")

        self._raise_for_status = raise_on_status

        retry = PostForcelistRetry(
            total=total,
            connect=connect,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            raise_on_status=False,
            **kwargs,
        )

        retry_adapter = HTTPAdapter(max_retries=retry)
        self.mount("http://", retry_adapter)
        self.mount("https://", retry_adapter)

    @staticmethod
    def _get_error_message_from_json(error_json: dict[str, Any]) -> Optional[str]:
        """Extracts the error message from the JSON response."""
        if not error_json or not isinstance(error_json, dict):
            return None

        msg = error_json.get("message")

        if not msg:
            error_data = error_json.get("error")
            if isinstance(error_data, dict):
                msg = error_data.get("message")
            elif isinstance(error_data, str):
                msg = error_data

        return msg

    @staticmethod
    def _mask_sensitive_data(message: str, auth_headers: dict[str, str]) -> str:
        """Replaces sensitive data in the message with a placeholder."""
        for _, value in auth_headers.items():
            message = message.replace(value, "...")
        return message

    def request(self, method: str, url: str, *args, **kwargs) -> requests.Response:
        """Construct, prepare, and send a ``Request``.
        Override the request method to prepend base_url to the URL and include additional headers.

        Args:
            method (str): HTTP method (e.g., 'get', 'post').
            url (str): URL for the request. Prepend base_url if url is a relative URL.
            **kwargs: Additional arguments for the request

        Returns:
            Response object.

        Raises:
            RequestsApiError: If the request failed.
        """
        if self.base_url and not url.startswith(("http://", "https://")):
            base_url = self.base_url.rstrip("/") + "/"
            url = url.lstrip("/")
            url = urljoin(base_url, url)

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", InsecureRequestWarning)
                response = super().request(method, url, *args, **kwargs)
                if self._raise_for_status:
                    response.raise_for_status()

        except requests.RequestException as err:
            message = None

            if err.response is not None:
                try:
                    error_json: dict[str, Any] = err.response.json()
                    message = self._get_error_message_from_json(error_json)
                except ValueError:
                    message = err.response.text

            message = message or str(err)
            message = message if message.endswith(".") else message + "."
            message = self._mask_sensitive_data(message, self.auth_headers)

            raise RequestsApiError(message) from err

        return response


class QbraidSession(Session):  # pylint: disable=too-many-instance-attributes
    """Custom session with handling of request urls and authentication.

    This is a child class of :py:class:`qbraid_core.sessions.Session`.
    It handles qbraid authentication with custom headers and has SSL
    verification disabled for compatibility with qBraid Lab.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        organization: Optional[str] = None,
        workspace: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Initialize custom session with default base_url and auth_headers.

        Args:
            api_key (optional, str): Authenticated qBraid API key.
            organization (optional, str): Organization name.
            workspace (optional, str): Workspace name.
        """
        self._api_key: Optional[str] = None
        self._user_email: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._organization: Optional[str] = None
        self._workspace: Optional[str] = None

        self.api_key = api_key
        self.organization = organization
        self.workspace = workspace
        self.user_email = kwargs.pop("user_email", None)
        self.refresh_token = kwargs.pop("refresh_token", None)
        self.verify = False

        if "headers" not in kwargs:
            kwargs["headers"] = {}
        if "domain" not in kwargs["headers"]:
            kwargs["headers"]["domain"] = kwargs.pop("pool", "qbraid")
        if self.organization:
            kwargs["headers"]["organization"] = self.organization
        if self.workspace:
            kwargs["headers"]["workspace"] = self.workspace

        if "auth_headers" not in kwargs:
            kwargs["auth_headers"] = {}
        if self.api_key:
            kwargs["auth_headers"]["api-key"] = self.api_key
        if self.refresh_token:
            kwargs["auth_headers"]["refresh-token"] = self.refresh_token
        if self.user_email:
            kwargs["auth_headers"]["email"] = self.user_email
        super().__init__(**kwargs)
        self.initialize_retry()

    @property
    def base_url(self) -> Optional[str]:
        """Return the base URL."""
        return super().base_url

    @base_url.setter
    def base_url(self, value: Optional[str]) -> None:
        """Set the qbraid api url."""
        url = value or self.get_config("url")
        value = url or DEFAULT_ENDPOINT_URL
        value = value.rstrip("/") + "/"
        self._base_url = value

    @property
    def api_key(self) -> Optional[str]:
        """Return the api key."""
        return self._api_key

    @api_key.setter
    def api_key(self, value: Optional[str]) -> None:
        """Set the api key."""
        api_key = value or self.get_config("api-key")
        self._api_key = api_key or os.getenv("QBRAID_API_KEY")

    @property
    def user_email(self) -> Optional[str]:
        """Return the session user email."""
        return self._user_email

    @user_email.setter
    def user_email(self, value: Optional[str]) -> None:
        """Set the session user email."""
        user_email = value or self.get_config("email")
        self._user_email = user_email or os.getenv("JUPYTERHUB_USER")

    @property
    def refresh_token(self) -> Optional[str]:
        """Return the session refresh token."""
        return self._refresh_token

    @refresh_token.setter
    def refresh_token(self, value: Optional[str]) -> None:
        """Set the session refresh token."""
        refresh_token = value or self.get_config("refresh-token")
        self._refresh_token = refresh_token or os.getenv("REFRESH")

    @property
    def organization(self) -> Optional[str]:
        """Return the session organization."""
        return self._organization

    @organization.setter
    def organization(self, value: Optional[str]) -> None:
        """Set the session organization."""
        organization = value or self.get_config("organization")
        self._organization = organization or os.getenv("QBRAID_ORGANIZATION", DEFAULT_ORGANIZATION)

    @property
    def workspace(self) -> Optional[str]:
        """Return the session workspace."""
        return self._workspace

    @workspace.setter
    def workspace(self, value: Optional[str]) -> None:
        """Set the session workspace."""
        curr_value = value or self.get_config("workspace")
        workspace = curr_value or os.getenv("QBRAID_WORKSPACE", DEFAULT_WORKSPACE)

        if workspace not in SUPPORTED_WORKSPACES:
            raise ValueError(
                f"Invalid workspace '{workspace}'. Supported workspaces are: "
                f"{', '.join(SUPPORTED_WORKSPACES)}."
            )
        self._workspace = workspace

    def get_config(self, config_name: str) -> Optional[str]:
        """Returns the config value of specified config.

        Args:
            config_name: The name of the config
        """
        try:
            config = load_config()
        except ConfigError:
            return None

        section = DEFAULT_CONFIG_SECTION
        if section in config.sections():
            if config_name in config[section]:
                return config[section][config_name]
        return None

    def get_user(self) -> dict[str, Any]:
        """Get user metadata.

        Returns:
            Dictionary containing user metadata.

        Raises:
            UserNotFoundError: If user metadata is invalid or not found.
        """
        try:
            metadata = self.get("/identity").json()
        except RequestsApiError as err:
            raise UserNotFoundError(str(err)) from err

        if not metadata:
            raise UserNotFoundError("User metadata invalid or not found.")

        return metadata

    def get_jupyter_token_data(self) -> dict[str, str]:
        """Get the user's JupyterHub token data.

        Returns:
            dict[str, str]: The user's JupyterHub token data.

        Raises:
            RequestsApiError: If the request fails.
            ValueError: If the token data is empty or invalid.
        """
        try:
            response = self.get("/lab/compute/tokens")
            data = response.json()

            if not isinstance(data, dict):
                raise RequestsApiError("Invalid response format from token endpoint")

            token_data: dict[str, str] = data.get("token", {})
            if not token_data:
                raise ValueError("Token data not found in response")

            return token_data
        except requests.RequestException as err:
            raise RequestsApiError(f"Failed to retrieve Jupyter token: {err}") from err
        except ValueError as err:
            if "Expecting value" in str(err):
                raise RequestsApiError("Invalid JSON response from token endpoint") from err
            raise

    # pylint: disable-next=too-many-arguments,too-many-positional-arguments
    def save_config(
        self,
        api_key: Optional[str] = None,
        organization: Optional[str] = None,
        workspace: Optional[str] = None,
        base_url: Optional[str] = None,
        verify: bool = True,
        overwrite: bool = False,
        **kwargs,
    ) -> None:
        """Create qbraidrc file. In qBraid Lab, qbraidrc is automatically present in filesystem.

        Raises:
            UserNotFoundError: If user metadata is invalid or not found.
            AuthError: If there is a credential mismatch.
            ConfigError: If there is an error saving the config.
        """
        self.api_key = api_key or self.api_key
        self.organization = organization or self.organization
        self.workspace = workspace or self.workspace
        self.user_email = kwargs.get("user_email", self.user_email)
        self.refresh_token = kwargs.get("refresh_token", self.refresh_token)

        if base_url:
            value = base_url.rstrip("/") + "/"
            self._base_url = value
        config = configparser.ConfigParser()

        if overwrite:
            # Starting with a clean config if overwrite is True
            section = DEFAULT_CONFIG_SECTION
            config.add_section(section)
        else:
            # Load existing config if overwrite is False
            try:
                config = load_config()
            except ConfigError:
                config.add_section(DEFAULT_CONFIG_SECTION)

        section = DEFAULT_CONFIG_SECTION
        if section not in config.sections():
            config.add_section(section)

        # Set or update configurations
        options: dict[str, Any] = {
            "email": self.user_email,
            "api-key": self.api_key,
            # TODO: refresh-token should just be set to self.refresh_token
            # but switching it to that causes a mypy error for some reason...
            "refresh-token": kwargs.get("refresh_token", self.refresh_token),
            "organization": self.organization,
            "workspace": self.workspace,
            "url": self.base_url,
        }

        for option, value in options.items():
            config = update_config_option(config, section, option, value)

        save_user_config(config)

        if verify:
            res_json = self.get_user()
            res_email = res_json.get("email")

            if self.user_email and self.user_email != res_email:
                raise AuthError(
                    f"Credential mismatch: Session initialized for '{self.user_email}', "
                    f"but API key corresponds to '{res_email}'."
                )

    def get_available_services(self) -> list[str]:
        """
        Get a list of available services that can be loaded as low-level
        clients via :py:meth:`Session.client`.

        Returns:
            List: List of service names.
        """
        services_path = os.path.join(os.path.dirname(__file__), "services")
        return list(discover_services(services_path))

    def client(
        self, service_name: str, api_key: Optional[str] = None, **kwargs
    ) -> "qbraid_core.QbraidClient":
        """Return a client for the specified service.

        Args:
            service_name (str): Name of the service.
            api_key (optional, str): API key for the client service.

        Returns:
            qbraid_core.QbraidClient: Client for the specified service.
        """
        if len(client_registry) == 0:
            self.get_available_services()
        client_class = client_registry.get(service_name)
        if not client_class:
            raise ValueError(f"Service '{service_name}' not registered")

        session = None if api_key else self
        return client_class(session=session, api_key=api_key, **kwargs)


class QbraidSessionV1(Session):
    """Custom session with handling of request urls and authentication.

    This is a child class of :py:class:`qbraid_core.sessions.Session`.
    It handles qbraid authentication with custom headers and has SSL
    verification disabled for compatibility with qBraid Lab.

    This class uses the v1 API endpoints.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Initialize custom session with default base_url and auth_headers.

        Args:
            api_key (optional, str): Authenticated qBraid API key.
        """
        self._api_key: Optional[str] = None

        self.api_key = api_key
        self.verify = False

        if "headers" not in kwargs:
            kwargs["headers"] = {}
        if "X-Domain" not in kwargs["headers"]:
            kwargs["headers"]["X-Domain"] = "qbraid"

        if "auth_headers" not in kwargs:
            kwargs["auth_headers"] = {}
        if self.api_key:
            kwargs["auth_headers"]["X-API-Key"] = self.api_key
        super().__init__(**kwargs)
        self.initialize_retry()

    @property
    def base_url(self) -> Optional[str]:
        """Return the base URL."""
        return super().base_url

    @base_url.setter
    def base_url(self, value: Optional[str]) -> None:
        """Set the qbraid api url."""
        url = value or self.get_config("url")
        value = url or DEFAULT_ENDPOINT_URL_V1
        value = value.rstrip("/") + "/"
        self._base_url = value

    @property
    def api_key(self) -> Optional[str]:
        """Return the api key."""
        return self._api_key

    @api_key.setter
    def api_key(self, value: Optional[str]) -> None:
        """Set the api key."""
        api_key = value or self.get_config("api-key")
        self._api_key = api_key or os.getenv("QBRAID_API_KEY")

    def get_config(self, config_name: str) -> Optional[str]:
        """Returns the config value of specified config.

        Args:
            config_name: The name of the config
        """
        try:
            config = load_config()
        except ConfigError:
            return None

        section = DEFAULT_CONFIG_SECTION
        if section in config.sections():
            if config_name in config[section]:
                return config[section][config_name]
        return None

    def get_user_auth_metadata(self) -> dict[str, Any]:
        """Get user metadata.

        Returns:
            Dictionary containing user metadata.

        Raises:
            UserNotFoundError: If user metadata is invalid or not found.
        """
        try:
            metadata = self.get("/users/verify").json()
        except RequestsApiError as err:
            raise UserNotFoundError(str(err)) from err

        if not metadata:
            raise UserNotFoundError("User metadata invalid or not found.")

        return metadata

    def save_config(
        self,
        verify: bool = True,
        overwrite: bool = False,
    ) -> None:
        """Create or update qbraidrc file.

        Args:
            verify (bool): Whether to verify the config values before saving.
            overwrite (bool): Whether to overwrite the existing config.

        Raises:
            UserNotFoundError: If verify is True and user authentication fails.
            ConfigError: If there is an error saving the config.
            ValueError: If a given config value is invalid or if overwrite is
                False and there is a conflict with the existing config.
        """
        if verify:
            self.get_user_auth_metadata()

        clean_config = configparser.ConfigParser()

        if overwrite:
            # Starting with a clean config if overwrite is True
            config = clean_config
        else:
            # Load existing config if overwrite is False
            try:
                config = load_config()
            except ConfigError:
                config = clean_config

        section = DEFAULT_CONFIG_SECTION
        if section not in config.sections():
            config.add_section(section)

        # Set or update configurations
        options: dict[str, Any] = {
            "api-key": self.api_key,
            "url": self.base_url,
        }

        for option, value in options.items():
            if not overwrite and config.has_option(section, option):
                existing_value = config.get(section, option)
                if existing_value != value:
                    raise ValueError(
                        f"Config value for '{option}' is already set to '{existing_value}'. "
                        f"Use overwrite=True to overwrite with '{value}'."
                    )
            config = update_config_option(config, section, option, value)

        save_user_config(config)
