# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module for checking state of qBraid Quantum Jobs proxies.

"""
import logging
from pathlib import Path
from typing import Optional

from qbraid_core.system.packages import get_active_site_packages_path, get_venv_site_packages_path

from .exceptions import QbraidException
from .proxy_braket import _check_proxy_braket

logger = logging.getLogger(__name__)

SUPPORTED_QJOB_LIBS = {"braket": ("botocore", "httpsession.py")}


def _check_proxy(
    proxy_spec: tuple[str, ...], slug_path: Optional[Path] = None
) -> tuple[bool, bool, Optional[Path]]:
    """
    Checks if the specified proxy file exists and contains the string 'qbraid'.

    Args:
        proxy_spec (tuple[str, ...]): A tuple specifying the path components from 'site-packages'
                                      to the target proxy file, e.g. ("botocore", "httpsession.py").
        slug_path (optional, Path): The base path to prepend to the 'pyenv' directory.

    Returns:
        A tuple of two booleans and sitepackages path: The first bool indicates whether the
        specified proxy file exists; the second bool, if the file exists, is True if it contains
        'qbraid', False otherwise. The sitepackages path gives the location of the site-packages
        directory where the proxy file is located.
    """
    site_packages_path = None

    try:
        if slug_path is None:
            site_packages_path = get_active_site_packages_path()
        else:
            site_packages_path = get_venv_site_packages_path(slug_path / "pyenv")
    except QbraidException as err:
        logger.debug(err)
        return False, False, site_packages_path

    target_file_path = site_packages_path.joinpath(*proxy_spec)

    if not target_file_path.exists():
        return False, False, site_packages_path

    try:
        with target_file_path.open("r", encoding="utf-8") as file:
            for line in file:
                if "qbraid" in line:
                    return True, True, site_packages_path
        return True, False, site_packages_path
    except Exception as err:  # pylint: disable=broad-exception-caught
        logger.debug("Unexpected error checking qBraid proxy: %s", err)

    return True, False, site_packages_path


def quantum_lib_proxy_state(
    device_lib: str, is_default_python: bool = True, **kwargs
) -> dict[str, bool]:
    """Checks if qBraid Quantum Jobs are supported and if so, checks whether they are enabled.
    Returns dictionary providing information about the state of qBraid Quantum Jobs support
    and configuration for the given quantum device library.

    Args:
        device_lib (str): The name of the quantum device library, e.g., "braket".
        is_default_python (bool): Indicates whether the Python environment is known to
                                  be the default system Python. Default assumption is True.

    Returns:
        dict: A dictionary containing the following keys:
            - 'supported' (bool): Indicates whether the necessary proxy file exists for the
                                  specified quantum device library.
            - 'enabled' (bool): True if the library is configured to support qBraid Quantum Jobs,
                                False otherwise.
    """
    if device_lib not in SUPPORTED_QJOB_LIBS:
        raise ValueError(
            f"Unsupported quantum job library. Expected one of {list(SUPPORTED_QJOB_LIBS.keys())}"
        )

    supported = False
    enabled = False

    proxy_spec = SUPPORTED_QJOB_LIBS[device_lib]

    if device_lib == "braket":
        if is_default_python:
            supported, enabled = _check_proxy_braket()
            if supported and not enabled:
                supported, enabled, _ = _check_proxy(proxy_spec, **kwargs)
        else:
            supported, enabled, _ = _check_proxy(proxy_spec, **kwargs)

    # add more device libraries here as needed

    return {
        "supported": supported,
        "enabled": enabled,
    }
