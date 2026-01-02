# coding=utf-8
"""邮件发送客户端"""

from typing import Optional, List, Dict


class EmailClient:
    """邮件发送客户端

    提供邮件发送功能。

    Usage:
        client = KengerClient(base_url, token)

        # 发送简单邮件
        client.email.send(
            to="recipient@example.com",
            title="邮件主题",
            content="邮件内容"
        )

        # 发送 HTML 邮件
        client.email.send(
            to="recipient@example.com",
            title="邮件主题",
            content="<h1>HTML 内容</h1>",
            is_html=True
        )

        # 发送带附件的邮件
        client.email.send(
            to="recipient@example.com",
            title="邮件主题",
            content="请查收附件",
            attachments=[{"path": "/path/to/file.pdf", "name": "文件.pdf"}]
        )
    """

    def __init__(self, http_client, email_token: Optional[str] = None):
        self._http = http_client
        self._email_token = email_token

    def send(
        self,
        to: str,
        title: str,
        content: str,
        is_html: bool = True,
        attachments: Optional[List[Dict[str, str]]] = None,
        token: Optional[str] = None,
    ) -> bool:
        """发送邮件

        Args:
            to: 收件人邮箱
            title: 邮件主题
            content: 邮件正文
            is_html: 是否为 HTML 格式，默认 True
            attachments: 附件列表，格式: [{"path": "文件路径", "name": "显示名称"}]
            token: 邮件发送 token（如果初始化时未设置）

        Returns:
            是否发送成功

        Raises:
            ValidationError: 参数无效或 token 未设置
        """
        email_token = token or self._email_token
        if not email_token:
            from .exceptions import ValidationError
            raise ValidationError("邮件发送需要 token，请在初始化时设置 email_token 或调用时传入 token")

        payload = {
            "target_email": to,
            "title": title,
            "content": content,
            "token": email_token,
            "is_html": is_html,
        }

        if attachments:
            payload["attachments"] = attachments

        self._http.post("/api/tools/email/_send", json=payload)
        return True

