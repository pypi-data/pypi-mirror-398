# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module for serving environment paths information.

"""

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Optional, Union

from qbraid_core.system.executables import is_valid_python

from .schema import EnvironmentConfig
from .validate import is_valid_slug

logger = logging.getLogger(__name__)

DEFAULT_LOCAL_ENVS_PATH = Path.home() / ".qbraid" / "environments"


def get_default_envs_paths() -> list[Path]:
    """
    Returns a list of paths to qBraid environments.

    If the QBRAID_ENVS_PATH environment variable is set, it splits the variable by ':' to
    accommodate multiple paths. If QBRAID_ENVS_PATH is not set, returns a list containing
    the default qBraid environments path (~/.qbraid/environments).

    Returns:
        A list of pathlib.Path objects representing the qBraid environments paths.
    """
    qbraid_envs_path = os.getenv("QBRAID_ENVS_PATH", str(DEFAULT_LOCAL_ENVS_PATH))
    return [Path(path) for path in qbraid_envs_path.split(os.pathsep)]


def get_env_path(slug: str) -> Path:
    """
    Return path to qbraid environment.

    Args:
        slug (str): The environment directory to search for.

    Returns:
        pathlib.Path: The path to the environment directory.

    Raises:
        FileNotFoundError: If the environment directory does not exist.
    """
    qbraid_env_paths = get_default_envs_paths()
    searched_paths = []  # Keep track of paths that were searched

    for env_path in qbraid_env_paths:
        target_path = env_path / slug  # Directly create the path to the target
        if target_path.is_dir():
            return target_path
        searched_paths.append(target_path)

    # Improving error message by showing all searched paths
    raise FileNotFoundError(
        f"Environment '{slug}' not found. Searched in: {', '.join(str(p) for p in searched_paths)}"
    )


def get_tmp_dir_names(envs_path: Union[str, Path]) -> list[str]:
    """Return list of tmp directories paths in envs_path"""
    pattern = re.compile(r"^tmp\d{1,2}$")  # Regex for tmp directories

    envs_dir = Path(envs_path)

    return [d.name for d in envs_dir.iterdir() if d.is_dir() and pattern.match(d.name)]


def get_next_tmpn(tmpd_names: list[str]) -> str:
    """Return next tmp directory name"""
    tmpd_names_sorted = sorted(tmpd_names, key=lambda x: int(x[3:]))
    next_tmp_int = int(tmpd_names_sorted[-1][3:]) + 1 if tmpd_names_sorted else 0
    return f"tmp{next_tmp_int}"


def which_python(slug: str, fallback_to_executable: bool = True) -> Optional[str]:
    """Return environment's python path

    Args:
        slug (str): Identifier for the environment.
        fallback_to_executable (bool): If True, falls back to sys.executable when
            no path is found. If False, returns None. Defaults to True.

    Returns:
        Optional[str]: The path to the Python executable associated with the given slug
            environment or None/sys.executable based on fallback_to_executable.
    """
    try:
        slug_path = Path(get_env_path(slug))
        kernels_dir = slug_path.joinpath("kernels")
        for resource_dir in kernels_dir.iterdir():
            if "python" in resource_dir.name:
                kernel_json = resource_dir.joinpath("kernel.json")
                if kernel_json.exists():
                    with kernel_json.open(encoding="utf-8") as file:
                        data = json.load(file)
                        if data["language"] == "python":
                            python_path = data["argv"][0]
                            if is_valid_python(python_path):
                                return python_path

        # fallback: check pyenv bin for python executable
        if sys.platform == "win32":
            python_path = slug_path.joinpath("pyenv", "Scripts", "python.exe")
        else:
            python_path = slug_path.joinpath("pyenv", "bin", "python")
        if is_valid_python(python_path):
            return str(python_path)
    except Exception as err:  # pylint: disable=broad-exception-caught
        logger.error("Error determining Python path: %s", err)

    return sys.executable if fallback_to_executable else None


def installed_envs_data() -> tuple[dict[str, Path], dict[str, str]]:
    """Gather paths and aliases for all installed qBraid environments."""
    installed: dict[str, Path] = {}
    aliases: dict[str, str] = {}

    def _process_entry(entry: Path):
        if not entry.is_dir() or not is_valid_slug(entry.name):
            return

        installed[entry.name] = entry

        if entry.name == "qbraid_000000":
            aliases["default"] = entry.name
            return

        alias = None

        if (state_json_path := entry / "state.json").exists():
            try:
                with open(state_json_path, "r", encoding="utf-8") as file:
                    data: dict = json.load(file)
                    alias = data.get("name")
            # pylint: disable-next=broad-exception-caught
            except (json.JSONDecodeError, Exception):
                pass

        if alias is None and (env_config_path := entry / "qbraid.yaml").exists():
            try:
                config = EnvironmentConfig.from_yaml(env_config_path)
                if config.shell_prompt:
                    alias = config.shell_prompt
            # pylint: disable-next=broad-exception-caught
            except (ValueError, Exception):
                pass

        if alias is None:
            alias = entry.name[:-7]

        aliases[alias if alias not in aliases else entry.name] = entry.name

    for env_path in get_default_envs_paths():
        for entry in env_path.iterdir():
            _process_entry(entry)

    return installed, aliases
