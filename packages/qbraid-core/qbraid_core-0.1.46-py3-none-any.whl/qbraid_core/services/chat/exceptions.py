# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module defining custom exceptions for the qBraid environments module.

"""

from qbraid_core.exceptions import QbraidException


class ChatServiceRequestError(QbraidException):
    """
    Base class for errors raised by API requests made through
    qBraid chat service clients.

    """
