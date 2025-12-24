# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

# pylint: disable=duplicate-code,useless-import-alias

"""
Module defining qBraid service clients.

.. currentmodule:: qbraid_core.services

"""
import importlib
from typing import TYPE_CHECKING

__all__ = []  # type: ignore[var-annotated]

_lazy = {
    "environments": ["EnvironmentManagerClient"],
    "quantum": ["QuantumClient"],
    "chat": ["ChatClient"],
    "storage": ["FileStorageClient"],
}

if TYPE_CHECKING:
    from .chat import ChatClient as ChatClient
    from .environments import EnvironmentManagerClient as EnvironmentManagerClient
    from .quantum import QuantumClient as QuantumClient
    from .storage import FileStorageClient as FileStorageClient


def __getattr__(name):
    for mod_name, objects in _lazy.items():
        if name == mod_name:
            module = importlib.import_module(f".{mod_name}", __name__)
            globals()[mod_name] = module
            return module

        if name in objects:
            module = importlib.import_module(f".{mod_name}", __name__)
            obj = getattr(module, name)
            globals()[name] = obj
            return obj

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(
        __all__ + list(_lazy.keys()) + [item for sublist in _lazy.values() for item in sublist]
    )
