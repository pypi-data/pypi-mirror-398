# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module defining abstract base clas for qBraid micro-service clients.

"""
import datetime
import re
from typing import Optional

import requests

from ._compat import check_version
from .config import DEFAULT_CONFIG_PATH
from .context import ensure_directory
from .exceptions import AuthError, RequestsApiError, ResourceNotFoundError, UserNotFoundError
from .sessions import QbraidSession, QbraidSessionV1


class QbraidClient:
    """Base class for qBraid micro-service clients."""

    def __init__(self, api_key: Optional[str] = None, session: Optional[QbraidSession] = None):
        if api_key and session:
            raise ValueError("Provide either api_key or session, not both.")

        self._user_metadata: Optional[dict[str, str]] = None
        self.session = session or QbraidSession(api_key=api_key)
        check_version("qbraid-core")

    @property
    def session(self) -> QbraidSession:
        """The QbraidSession used to make requests."""
        return self._session

    @session.setter
    def session(self, value: Optional[QbraidSession]) -> None:
        """Set the QbraidSession, ensuring it is a valid QbraidSession instance.

        Raises:
            AuthError: If the provided session is not valid.
            TypeError: If the value is not a QbraidSession instance.
        """
        session = value if value is not None else QbraidSession()

        if not isinstance(session, QbraidSession):
            raise TypeError("The session must be a QbraidSession instance.")

        try:
            user = session.get_user()
            self._user_metadata = {
                "organization": user.get("organization", "qbraid"),
                "role": user.get("role", "user"),
            }
            self._session = session
        except UserNotFoundError as err:
            raise AuthError(f"Access denied due to missing or invalid credentials: {err}") from err

    @staticmethod
    def _is_valid_object_id(candidate_id: str) -> bool:
        """
        Check if the provided string is a valid MongoDB ObjectId format.

        Args:
            candidate_id (str): The string to check.

        Returns:
            bool: True if the string is a valid ObjectId format, False otherwise.
        """
        try:
            return bool(re.match(r"^[0-9a-fA-F]{24}$", candidate_id))
        except (TypeError, SyntaxError):
            return False

    @staticmethod
    def _convert_email_symbols(email: str) -> Optional[str]:
        """Convert email to compatible string format"""
        return (
            email.replace("-", "-2d")
            .replace(".", "-2e")
            .replace("@", "-40")
            .replace("_", "-5f")
            .replace("+", "-2b")
        )

    def running_in_lab(self) -> bool:
        """Check if running in the qBraid Lab environment."""
        try:
            utc_datetime = datetime.datetime.now(datetime.timezone.utc)
        except AttributeError:  # Fallback if datetime.timezone.utc is not available
            utc_datetime = datetime.datetime.utcnow()

        formatted_time = utc_datetime.strftime("%Y%m%d%H%M%S")
        config_dir = DEFAULT_CONFIG_PATH.parent / "certs"
        filepath = config_dir / formatted_time

        try:
            with ensure_directory(config_dir, remove_if_created=False):
                # Create an empty file
                with filepath.open("w", encoding="utf-8"):
                    pass

                response = self.session.get(f"/lab/is-mounted/{formatted_time}")
                is_mounted = bool(response.json().get("isMounted", False))

            # Clean up the temporary file after checking the directory
            filepath.unlink(missing_ok=True)

        except (requests.exceptions.RequestException, KeyError):
            is_mounted = False

        return is_mounted

    def user_credits_value(self) -> float:
        """
        Get the current user's qBraid credits value.

        Returns:
            float: The current user's qBraid credits value.
        """
        try:
            res = self.session.get("/billing/credits/get-user-credits").json()
            credits_value = res["qbraidCredits"]
            return float(credits_value)
        except (RequestsApiError, KeyError, ValueError) as err:
            raise ResourceNotFoundError(f"Credits value not found: {err}") from err


class QbraidClientV1:  # pylint: disable=too-few-public-methods
    """Base class for qBraid micro-service clients interfacing with the new
    qBraid API."""

    def __init__(self, api_key: Optional[str] = None, session: Optional[QbraidSessionV1] = None):
        if api_key and session:
            raise ValueError("Provide either api_key or session, not both.")

        self._user_metadata: Optional[dict[str, str]] = None
        self.session = session or QbraidSessionV1(api_key=api_key)
        check_version("qbraid-core")

    @property
    def session(self) -> QbraidSessionV1:
        """The QbraidSessionV1 used to make requests."""
        return self._session

    @session.setter
    def session(self, value: Optional[QbraidSessionV1]) -> None:
        """Set the QbraidSessionV1, ensuring it is a valid QbraidSessionV1 instance.

        Raises:
            AuthError: If the provided session is not valid.
            TypeError: If the value is not a QbraidSessionV1 instance.
        """
        session = value if value is not None else QbraidSessionV1()

        if not isinstance(session, QbraidSessionV1):
            raise TypeError("The session must be a QbraidSessionV1 instance.")

        try:
            user = session.get_user_auth_metadata()
            self._user_metadata = {
                "organization": user.get("data", {}).get("organizationId", ""),
                "role": user.get("data", {}).get("userRole", []),
            }
            self._session = session
        except UserNotFoundError as err:
            raise AuthError(f"Access denied due to missing or invalid credentials: {err}") from err
