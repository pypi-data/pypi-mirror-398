"""
Crexperium CRM Python SDK

A Python client library for the Crexperium CRM API.

Quick Start:
    Set your API token as an environment variable:
    $ export CREXPERIUM_API_TOKEN="your-api-token"

    Then use the SDK:
    >>> from crexperium import CRMClient
    >>> client = CRMClient()  # Automatically uses env var
    >>> contact, created = client.contacts.identify(
    ...     external_id="user_123",
    ...     email="user@example.com"
    ... )
"""

__version__ = "1.0.5"

from .client import CRMClient
from .config import Config, CREXPERIUM_API_TOKEN_ENV
from .exceptions import (
    CRMError,
    AuthenticationError,
    ResourceNotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
)

__all__ = [
    "CRMClient",
    "Config",
    "CREXPERIUM_API_TOKEN_ENV",
    "CRMError",
    "AuthenticationError",
    "ResourceNotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
]
