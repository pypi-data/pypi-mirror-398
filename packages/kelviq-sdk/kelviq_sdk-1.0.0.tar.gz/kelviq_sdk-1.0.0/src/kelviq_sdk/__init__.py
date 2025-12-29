# kelviq_sdk/__init__.py
"""
Kelviq Python SDK

A Python SDK for interacting with the Kelviq API to report usage and events.
Supports both synchronous and asynchronous operations using a single client class,
instantiated via static factory methods `Kelviq.create_sync_client` or
`Kelviq.create_async_client`.
"""

__version__ = "1.0.0"

# Import constants to be available at the package level
import logging
from .constants import BEHAVIOUR_CHOICES

logger = logging.getLogger(__name__)  # Using __name__ will make it 'kelviq_sdk'
if not logger.handlers:  # Add handler only if no handlers are already configured
    logger.addHandler(logging.NullHandler())

# Import exceptions to be available at the package level
from .exceptions import (
    APIError,
    AuthenticationError,
    InvalidRequestError,
    ServerError,
    NotFoundError
)

# Import the unified client class
from .client import Kelviq

__all__ = [
    # Logger (optional to export, but can be useful for users to configure)
    "logger",

    # Constants
    "BEHAVIOUR_CHOICES",

    # Exceptions
    "APIError",
    "AuthenticationError",
    "InvalidRequestError",
    "ServerError",
    "NotFoundError",

    # Client Class (factories are part of this class)
    "Kelviq",

    # Version
    "__version__",
]
