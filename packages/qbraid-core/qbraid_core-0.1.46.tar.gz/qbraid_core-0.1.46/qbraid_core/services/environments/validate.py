# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module for validating qBraid environments.

"""
import keyword
import re


def is_valid_env_name(env_name: str) -> bool:
    """
    Validates a Python virtual environment name against best practices.

    Args:
        env_name (str): The name of the Python virtual environment to validate.

    Returns:
        bool: True if the name is valid, False otherwise.

    Raises:
        ValueError: If the environment name is not a string or is empty.
    """
    is_valid = True

    # Basic checks for empty names or purely whitespace names
    if not env_name or not isinstance(env_name, str) or env_name == "" or env_name.isspace():
        is_valid = False

    # Check for invalid characters, including shell metacharacters and spaces
    elif re.search(r'[<>:"/\\|?*\s&;()$[\]#~!{}]', env_name):
        is_valid = False

    # Reserved names for Windows (example list, can be expanded)
    elif env_name.upper() in [
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    ]:
        is_valid = False

    elif len(env_name) > 20:
        is_valid = False

    # Check against Python reserved words
    elif keyword.iskeyword(env_name):
        is_valid = False

    # Check if it starts with a number, which is not a good practice
    elif env_name[0].isdigit():
        is_valid = False

    return is_valid


def is_valid_slug(slug: str) -> bool:
    """Validates whether a slug meets the defined criteria."""
    # Initialize result as False
    result = False

    # Define the length constraints
    max_total_length = 20
    slug_alphanumeric_length = 6
    max_name_part_length = max_total_length - slug_alphanumeric_length - 1

    legacy = ["cirq__openfer_5f52ck"]

    if slug in legacy:
        result = True
    if len(slug) <= max_total_length and slug:
        # Split the slug into name part and alphanumeric part
        parts = slug.rsplit("_", 1)
        if 2 <= len(parts) <= 3 and len(parts[0]) <= max_name_part_length:
            name_part = parts[0]
            alphanumeric_part = parts[-1]

            # Check the alphanumeric and name parts
            if (
                re.fullmatch(r"^[a-z0-9]{6}$", alphanumeric_part)
                and 0 < len(name_part) <= max_name_part_length
                and re.fullmatch(r"^[a-z0-9]+(_[a-z0-9]+)*$", name_part)
            ):
                result = True

    return result
