# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module defining qBraid IPython magic commands and configurations.

.. currentmodule:: qbraid_core.system.magic

Classes
--------

.. autosummary::
   :toctree: ../stubs/

    SysMagics

Functions
----------

.. autosummary::
   :toctree: ../stubs/

    add_magic_file
    remove_magic_file
"""
from .manager import add_magic_file, remove_magic_file
from .qbraid_magic import SysMagics

__all__ = ["SysMagics", "add_magic_file", "remove_magic_file"]
