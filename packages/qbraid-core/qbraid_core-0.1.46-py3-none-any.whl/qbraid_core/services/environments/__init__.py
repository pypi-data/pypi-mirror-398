# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module providing utilities for interfacing with qBraid environments

.. currentmodule:: qbraid_core.services.environments

Classes
----------

.. autosummary::
   :toctree: ../stubs/

   EnvironmentConfig
   EnvironmentManagerClient

Exceptions
------------

.. autosummary::
   :toctree: ../stubs/

   EnvironmentServiceRequestError

"""
from .client import EnvironmentManagerClient
from .create import create_local_venv
from .exceptions import EnvironmentServiceRequestError
from .kernels import add_kernels, get_all_kernels, remove_kernels
from .magic import add_magic_config, remove_magic_config
from .paths import (
    get_default_envs_paths,
    get_env_path,
    get_next_tmpn,
    get_tmp_dir_names,
    which_python,
)
from .schema import EnvironmentConfig
from .state import install_status_codes, update_state_json
from .validate import is_valid_env_name, is_valid_slug

__all__ = [
    "EnvironmentConfig",
    "EnvironmentManagerClient",
    "EnvironmentServiceRequestError",
    "create_local_venv",
    "add_magic_config",
    "remove_magic_config",
    "get_default_envs_paths",
    "get_env_path",
    "get_next_tmpn",
    "get_tmp_dir_names",
    "which_python",
    "install_status_codes",
    "update_state_json",
    "is_valid_env_name",
    "is_valid_slug",
    "get_all_kernels",
    "add_kernels",
    "remove_kernels",
]
