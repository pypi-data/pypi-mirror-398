# coding=utf-8
"""KengerKit 异常定义"""


class KengerKitError(Exception):
    """KengerKit 基础异常"""

    def __init__(self, message: str, code: int = -1, data=None):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(self.message)


class AuthenticationError(KengerKitError):
    """认证失败异常"""
    pass


class NotFoundError(KengerKitError):
    """资源不存在异常"""
    pass


class ValidationError(KengerKitError):
    """参数验证异常"""
    pass


class ServerError(KengerKitError):
    """服务端异常"""
    pass

