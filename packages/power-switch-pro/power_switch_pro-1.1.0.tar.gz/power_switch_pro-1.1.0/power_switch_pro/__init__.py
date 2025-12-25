"""
Power Switch Pro Python Library

A Python library for communicating with Digital Loggers Power Switch Pro devices.

Author: Bryan Kemp <bryan@kempville.com>
License: BSD-3-Clause
"""

from .client import PowerSwitchPro
from .exceptions import (
    APIError,
    AuthenticationError,
    ConnectionError,
    PowerSwitchError,
    ValidationError,
)

__version__ = "0.1.0"
__author__ = "Bryan Kemp"
__email__ = "bryan@kempville.com"
__license__ = "BSD-3-Clause"

__all__ = [
    "PowerSwitchPro",
    "PowerSwitchError",
    "AuthenticationError",
    "ConnectionError",
    "APIError",
    "ValidationError",
]
