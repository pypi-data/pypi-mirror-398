# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module defining package version.
"""

import importlib.metadata

try:
    __version__ = importlib.metadata.version("qbraid-core")
except Exception:  # pylint: disable=broad-exception-caught # pragma: no cover
    __version__ = "dev"

__version_tuple__ = tuple(int(part) if part.isdigit() else part for part in __version__.split("."))

__all__ = ["__version__", "__version_tuple__"]
