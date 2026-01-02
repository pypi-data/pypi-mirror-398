"""
Jokoor Python SDK

Official Python SDK for the Jokoor API. This SDK provides a simple and type-safe
way to integrate Jokoor's SMS and payment services into your Python applications.

Example:
    >>> from jokoor import Jokoor
    >>>
    >>> client = Jokoor('sk_test_your_api_key')
    >>>
    >>> # Send an SMS
    >>> sms, error = client.sms.send(
    ...     recipient_phone='+2207123456',
    ...     message_body='Hello from Jokoor!'
    ... )
    >>>
    >>> # Create a payment link
    >>> link, error = client.payment_links.create(
    ...     title='Product Purchase',
    ...     amount='100.00'
    ... )
"""

__version__ = "2.0.0"

from .client import Jokoor
from .errors import (
    JokoorError,
    JokoorAPIError,
    JokoorAuthenticationError,
    JokoorPermissionError,
    JokoorNotFoundError,
    JokoorValidationError,
    JokoorRateLimitError,
    JokoorServerError,
    JokoorNetworkError,
    JokoorTimeoutError,
)
from .result import Result, Ok, Err, is_ok, is_err, unwrap, unwrap_or

__all__ = [
    # Main client
    "Jokoor",
    # Result type helpers
    "Result",
    "Ok",
    "Err",
    "is_ok",
    "is_err",
    "unwrap",
    "unwrap_or",
    # Error types
    "JokoorError",
    "JokoorAPIError",
    "JokoorAuthenticationError",
    "JokoorPermissionError",
    "JokoorNotFoundError",
    "JokoorValidationError",
    "JokoorRateLimitError",
    "JokoorServerError",
    "JokoorNetworkError",
    "JokoorTimeoutError",
]
