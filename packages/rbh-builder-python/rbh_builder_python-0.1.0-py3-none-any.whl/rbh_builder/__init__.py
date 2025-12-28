"""
Python client for the Rainbow Hospitality Gateway REST and WebSocket APIs.
"""

from .client import RainbowClient
from .exceptions import ApiError, AuthenticationError, RequestError

__all__ = ["RainbowClient", "ApiError", "AuthenticationError", "RequestError"]
