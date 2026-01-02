# coding=utf-8
"""KengerKit 主客户端"""

from typing import Optional

from .config import ConfigClient
from .email import EmailClient
from .http import HttpClient


class KengerClient:
    """Kenger Service 客户端

    统一入口，提供配置管理、邮件发送等功能。

    Usage:
        from kengerkit import KengerClient

        # 初始化客户端
        client = KengerClient(
            base_url="https://your-kenger-service.com",
            token="your_api_token"
        )

        # 配置管理
        value = client.config.get("my_key")
        client.config.set("new_key", "value")

        # 邮件发送（需要额外的 email_token）
        client.email.send(
            to="recipient@example.com",
            title="主题",
            content="内容",
            token="email_token"
        )

    Attributes:
        config: 配置管理客户端
        email: 邮件发送客户端
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: int = 30,
        email_token: Optional[str] = None,
    ):
        """初始化客户端

        Args:
            base_url: Kenger Service 的基础 URL
            token: API 认证 Token
            timeout: 请求超时时间（秒），默认 30
            email_token: 邮件发送 Token（可选，也可在发送时传入）
        """
        self._http = HttpClient(base_url, token, timeout)

        # 子模块
        self.config = ConfigClient(self._http)
        self.email = EmailClient(self._http, email_token)

    @property
    def base_url(self) -> str:
        """获取基础 URL"""
        return self._http.base_url

    @property
    def timeout(self) -> int:
        """获取超时时间"""
        return self._http.timeout

