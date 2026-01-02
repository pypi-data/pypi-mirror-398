# coding=utf-8
"""
KengerKit - Kenger Service Python SDK

Usage:
    from kengerkit import KengerClient

    client = KengerClient(base_url="https://your-service.com", token="your_token")

    # 配置管理
    value = client.config.get("my_key")
    client.config.set("key", "value")

    # 服务注册
    from kengerkit import ServiceRegistry

    registry = ServiceRegistry(
        client=client,
        namespace="my-service",
        port=5000,
    )
    registry.start()
"""

from .client import KengerClient
from .exceptions import (
    KengerKitError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    ServerError,
)
from .registry import ServiceRegistry

__version__ = "0.2.0"
__all__ = [
    "KengerClient",
    "ServiceRegistry",
    "KengerKitError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
    "ServerError",
]

