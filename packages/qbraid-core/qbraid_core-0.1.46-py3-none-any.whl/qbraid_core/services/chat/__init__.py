# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module providing client for interacting with qBraid chat service.

.. currentmodule:: qbraid_core.services.chat

Classes
--------

.. autosummary::
   :toctree: ../stubs/

   ChatClient

Exceptions
------------

.. autosummary::
   :toctree: ../stubs/

   ChatServiceRequestError

"""
from .client import ChatClient
from .exceptions import ChatServiceRequestError

__all__ = ["ChatClient", "ChatServiceRequestError"]
