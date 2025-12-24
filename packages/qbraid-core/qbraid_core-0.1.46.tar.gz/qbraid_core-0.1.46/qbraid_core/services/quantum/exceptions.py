# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module defining custom exceptions for the qBraid quantum services module.

"""

from qbraid_core.exceptions import QbraidException


class QuantumServiceRequestError(QbraidException):
    """Base class for errors raised by API requests made through qBraid quantum service clients."""


class QuantumServiceRuntimeError(QbraidException):
    """Base class for runtime errors raised by qBraid quantum service clients."""
