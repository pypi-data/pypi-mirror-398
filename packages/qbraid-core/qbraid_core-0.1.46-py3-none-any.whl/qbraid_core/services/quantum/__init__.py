# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module providing client for interacting with qBraid quantum services.

.. currentmodule:: qbraid_core.services.quantum

Classes
--------

.. autosummary::
   :toctree: ../stubs/

   QuantumClient

Exceptions
------------

.. autosummary::
   :toctree: ../stubs/

   QuantumServiceRequestError
   QuantumServiceRuntimeError

"""
from qbraid_core._import import LazyLoader

from .adapter import process_device_data, process_job_data
from .client import QuantumClient
from .exceptions import QuantumServiceRequestError, QuantumServiceRuntimeError
from .proxy import quantum_lib_proxy_state

runner = LazyLoader("runner", globals(), "qbraid_core.services.quantum.runner")

__all__ = [
    "process_device_data",
    "process_job_data",
    "QuantumClient",
    "QuantumServiceRequestError",
    "QuantumServiceRuntimeError",
    "quantum_lib_proxy_state",
    "runner",
]
