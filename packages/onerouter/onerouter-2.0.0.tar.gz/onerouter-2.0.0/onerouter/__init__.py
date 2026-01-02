"""
OneRouter Python SDK
====================
Unified API client for payments, subscriptions, SMS, and more.

Installation:
    pip install onerouter

Usage:
    from onerouter import OneRouter

    client = OneRouter(api_key="unf_live_xxx")
    order = client.payments.create(amount=500.00, currency="INR")
"""

from .client import OneRouter
from .utils import OneRouterSync
from .exceptions import (
    OneRouterError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    APIError
)

__version__ = "2.0.0"
__all__ = [
    "OneRouter",
    "OneRouterSync",
    "OneRouterError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "APIError",
]