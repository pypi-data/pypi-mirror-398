# coding=utf-8
"""
KengerKit - Kenger Service Python SDK

Usage:
    from kengerkit import KengerClient

    client = KengerClient(base_url="https://your-service.com", token="your_token")

    # 配置管理
    value = client.config.get("my_key")
    client.config.set("key", "value")
"""

from .client import KengerClient
from .exceptions import (
    KengerKitError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    ServerError,
)

__version__ = "0.1.0"
__all__ = [
    "KengerClient",
    "KengerKitError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
    "ServerError",
]

