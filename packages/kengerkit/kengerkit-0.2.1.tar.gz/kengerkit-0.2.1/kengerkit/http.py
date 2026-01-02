# coding=utf-8
"""HTTP 请求封装"""

from typing import Optional, Dict, Any

import requests

from .exceptions import (
    KengerKitError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    ServerError,
)


class HttpClient:
    """HTTP 客户端封装"""

    def __init__(self, base_url: str, token: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.session = requests.Session()
        self._setup_headers()

    def _setup_headers(self):
        """设置默认请求头"""
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        })

    def _build_url(self, path: str) -> str:
        """构建完整 URL"""
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """处理响应"""
        # HTTP 状态码检查
        if response.status_code == 401:
            raise AuthenticationError("认证失败，请检查 token")
        elif response.status_code == 404:
            raise NotFoundError("请求的资源不存在")

        try:
            data = response.json()
        except ValueError:
            if response.status_code >= 500:
                raise ServerError(f"服务端错误: {response.text}")
            raise KengerKitError(f"响应解析失败: {response.text}")

        # 业务状态码检查
        code = data.get("code", 0)
        if code != 0:
            message = data.get("message", "未知错误")
            if response.status_code == 400:
                raise ValidationError(message, code, data.get("data"))
            elif response.status_code >= 500:
                raise ServerError(message, code, data.get("data"))
            else:
                raise KengerKitError(message, code, data.get("data"))

        return data

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """GET 请求"""
        url = self._build_url(path)
        response = self.session.get(url, params=params, timeout=self.timeout)
        return self._handle_response(response)

    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """POST 请求"""
        url = self._build_url(path)
        response = self.session.post(url, json=json, timeout=self.timeout)
        return self._handle_response(response)

