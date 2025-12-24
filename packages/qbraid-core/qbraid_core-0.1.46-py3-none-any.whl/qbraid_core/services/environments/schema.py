# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module for the qBraid environment configuration schema.

"""
import logging
from pathlib import Path
from typing import Any, Optional, Union

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, field_serializer, field_validator
from pydantic.alias_generators import to_camel

from qbraid_core.system.versions import is_valid_semantic_version, package_has_match_on_pypi

logger = logging.getLogger(__name__)


class EnvironmentConfig(BaseModel):
    """Model for the qBraid environment configuration."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        extra="forbid",
    )

    name: str
    description: Optional[str] = None
    tags: Optional[list[str]] = None

    # this needs to be a path to an image file.
    # read and added as file in the request
    icon: Optional[Path] = None

    python_version: Optional[str] = None
    kernel_name: Optional[str] = None
    shell_prompt: Optional[str] = None
    python_packages: Optional[dict[str, str]] = None  # code request param
    visibility: str = "private"

    @field_validator("python_version")
    @classmethod
    def _check_python_version(cls, value: Optional[str]):
        if value is None:
            return value

        if not value.startswith("3."):
            raise ValueError("Python version must start with 3.")

        if not is_valid_semantic_version(value):
            raise ValueError("Python version must be a valid semantic version x.y.z")

        return value

    @classmethod
    def parse_version_specifier(cls, version: str) -> tuple[str, str]:
        """Parse the version specifier.

        Args:
            version (str): The version string.

        Returns:
            tuple[str, str]: The operator and version number.
        """
        operators = ["==", ">=", "<=", ">", "<", "~="]
        for op in operators:
            if version.startswith(op):
                return op, version[len(op) :]
        return "", version

    @field_validator("python_packages")
    @classmethod
    def _check_package_versions(cls, value: Optional[dict[str, str]]):
        if value is None:
            return value

        for name, version in value.items():
            operator, version_number = cls.parse_version_specifier(version)
            if version_number and not is_valid_semantic_version(version_number):
                raise ValueError(
                    f"Invalid package '{name}{version}'. "
                    "Version must be a valid combination of a binary op and semantic version x.y.z"
                )
            if not package_has_match_on_pypi(name, operator, version_number):
                raise ValueError(f"Package '{name}' 'v{version_number}' not found on PyPI")

            if operator == "" and version:  # default case
                version = f"=={version}"
            value[name] = version

        return value

    @field_serializer("python_packages")
    @classmethod
    def _serialize_package_versions(cls, value: Optional[dict[str, str]]):
        if value is None:
            return value
        # add the python packages as a newline separated string of packages
        return "\n".join(f"{name}{version}" for name, version in value.items())

    @field_validator("icon")
    @classmethod
    def _check_icon_path(cls, value: Optional[Union[Path, str]]):
        if value is None:
            return value

        file_path = Path(value)

        if not file_path.is_file():
            raise ValueError(f'Icon file not found at path "{file_path}"')

        if file_path.suffix != ".png":
            raise ValueError(f'Icon file must be a .png file, found "{file_path.suffix}"')

        return file_path

    @field_serializer("icon")
    @classmethod
    def _serialize_icon(cls, value):
        if value is None:
            return value
        return str(value)

    @field_serializer("tags")
    @classmethod
    def _serialize_tags(cls, value: Optional[list[str]]):
        if value is None:
            return value

        # TODO: update to return a list of tags and conform with API spec
        return ",".join(value)

    @classmethod
    def from_yaml(cls, file_path: Union[str, Path]) -> "EnvironmentConfig":
        """Create an EnvironmentConfig object from a YAML file."""

        def _load_yaml(file_path: Union[str, Path]) -> dict[str, Any]:
            """Load a YAML file."""
            with open(file_path, "r", encoding="utf-8") as file:
                return yaml.safe_load(file)

        def _adjust_icon_path(data: dict[str, Any], file_path: Union[str, Path]) -> dict[str, Any]:
            """Adjust the icon path to be an absolute path if it is relative to the
            YAML file path."""
            if data.get("icon"):
                icon_path = Path(data["icon"])
                # assume that if only a file name is given, it is in the same
                # directory as the yaml file
                if icon_path.name == str(icon_path):
                    # add the prefix of the yaml file path to make icon
                    # path absolute
                    yaml_parent = Path(file_path).parent
                    icon_path = yaml_parent / icon_path
                    data["icon"] = str(icon_path)
            return data

        data = _load_yaml(file_path)
        data = _adjust_icon_path(data, file_path)
        try:
            return cls(**data)
        except ValidationError as err:
            raise ValueError(f"Invalid YAML data: {err}") from err

    def to_yaml(self, file_path: Union[str, Path]) -> None:
        """Write the EnvironmentConfig object to a YAML file."""

        data = self.model_dump()

        # Override serializers to get original format

        # 1. transform python packages back to dict
        if data.get("python_packages"):
            data["python_packages"] = self.python_packages
            for name, version in data["python_packages"].items():
                if version.startswith("=="):
                    data["python_packages"][name] = version[2:]

        # 2. transform tags to list
        if data.get("tags"):
            data["tags"] = self.tags

        # 3. remove visibility
        data.pop("visibility", None)

        with open(file_path, "w", encoding="utf-8") as file:
            yaml.dump(data, file)
