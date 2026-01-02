# coding=utf-8
"""服务注册客户端"""

import atexit
import os
import socket
import threading
import time
from typing import Optional


class ServiceRegistry:
    """服务注册与心跳客户端

    用于 Flask 服务自动注册到 kenger-service 注册中心，并定期发送心跳保活。

    Usage:
        from kengerkit import KengerClient
        from kengerkit.registry import ServiceRegistry

        client = KengerClient(base_url="https://kenger-service.com", token="xxx")

        # 方式1: 显式指定参数
        registry = ServiceRegistry(
            client=client,
            namespace="jrebel",        # 服务命名空间
            port=58081,                # 服务端口
            host="43.143.21.219",      # 可选，默认自动获取本机IP
            weight=100,                # 权重
            health_path="/api/status", # 健康检查路径
            heartbeat_interval=10,     # 心跳间隔（秒）
        )

        # 方式2: 从环境变量读取配置
        registry = ServiceRegistry.from_env(client)

        # 启动（注册 + 心跳）
        registry.start()

        # 程序退出时自动注销（也可手动调用）
        # registry.stop()

    环境变量:
        KENGER_REGISTRY_HOST: 注册的主机地址（公网IP或域名）
        KENGER_REGISTRY_PORT: 注册的端口
        KENGER_REGISTRY_NAMESPACE: 命名空间
        KENGER_REGISTRY_WEIGHT: 权重，默认 100
        KENGER_REGISTRY_HEALTH_PATH: 健康检查路径，默认 /api/status
        KENGER_REGISTRY_HEARTBEAT_INTERVAL: 心跳间隔（秒），默认 10
    """

    def __init__(
        self,
        client,  # KengerClient
        namespace: Optional[str] = None,
        port: Optional[int] = None,
        host: Optional[str] = None,
        weight: Optional[int] = None,
        health_path: Optional[str] = None,
        heartbeat_interval: Optional[int] = None,
        auto_deregister: bool = True,
    ):
        """初始化服务注册器

        参数优先级：显式传参 > 环境变量 > 默认值

        Args:
            client: KengerClient 实例
            namespace: 命名空间名称（必需）
            port: 服务端口（必需）
            host: 主机地址，默认自动获取本机IP
            weight: 权重，默认 100
            health_path: 健康检查路径，默认 /api/status
            heartbeat_interval: 心跳间隔（秒），默认 10
            auto_deregister: 程序退出时是否自动注销，默认 True
        """
        self._client = client

        # 命名空间（必需）
        self.namespace = namespace or os.getenv('KENGER_REGISTRY_NAMESPACE')
        if not self.namespace:
            raise ValueError("namespace 必须通过参数或环境变量 KENGER_REGISTRY_NAMESPACE 指定")

        # 端口（必需）
        env_port = os.getenv('KENGER_REGISTRY_PORT')
        self.port = port or (int(env_port) if env_port else None)
        if not self.port:
            raise ValueError("port 必须通过参数或环境变量 KENGER_REGISTRY_PORT 指定")

        # 主机地址：显式传参 > 环境变量 > 自动检测
        self.host = host or os.getenv('KENGER_REGISTRY_HOST') or self._get_local_ip()

        # 权重
        env_weight = os.getenv('KENGER_REGISTRY_WEIGHT')
        self.weight = weight or (int(env_weight) if env_weight else 100)

        # 健康检查路径
        self.health_path = health_path or os.getenv('KENGER_REGISTRY_HEALTH_PATH', '/api/status')

        # 心跳间隔
        env_interval = os.getenv('KENGER_REGISTRY_HEARTBEAT_INTERVAL')
        self.heartbeat_interval = heartbeat_interval or (int(env_interval) if env_interval else 10)

        self.auto_deregister = auto_deregister

        self._running = False
        self._heartbeat_thread = None
        self._registered = False

    @staticmethod
    def _get_local_ip() -> str:
        """获取本机 IP 地址（内网）"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    @classmethod
    def from_env(cls, client, **overrides):
        """从环境变量创建实例

        Args:
            client: KengerClient 实例
            **overrides: 覆盖环境变量的参数

        Returns:
            ServiceRegistry 实例

        Usage:
            # 完全从环境变量读取
            registry = ServiceRegistry.from_env(client)

            # 覆盖部分配置
            registry = ServiceRegistry.from_env(client, weight=50)
        """
        return cls(client=client, **overrides)

    def register(self) -> bool:
        """注册服务到注册中心

        Returns:
            是否注册成功
        """
        try:
            self._client._http.post("/api/upstream/node/register", json={
                "ns": self.namespace,
                "host": self.host,
                "port": self.port,
                "weight": self.weight,
                "health_path": self.health_path,
            })
            self._registered = True
            return True
        except Exception as e:
            print(f"[ServiceRegistry] 注册失败: {e}")
            return False

    def deregister(self) -> bool:
        """从注册中心注销服务

        Returns:
            是否注销成功
        """
        if not self._registered:
            return True

        try:
            self._client._http.post("/api/upstream/node/deregister", json={
                "ns": self.namespace,
                "host": self.host,
                "port": self.port,
            })
            self._registered = False
            return True
        except Exception as e:
            print(f"[ServiceRegistry] 注销失败: {e}")
            return False

    def heartbeat(self) -> bool:
        """发送心跳

        Returns:
            是否发送成功
        """
        try:
            self._client._http.post("/api/upstream/heartbeat", json={
                "ns": self.namespace,
                "host": self.host,
                "port": self.port,
            })
            self._consecutive_failures = 0
            return True
        except Exception as e:
            self._consecutive_failures = getattr(self, '_consecutive_failures', 0) + 1
            print(f"[ServiceRegistry] 心跳失败 (连续第{self._consecutive_failures}次): {e}")

            # 连续失败3次后尝试重新注册（可能是注册中心重启导致数据丢失）
            if self._consecutive_failures >= 3:
                print(f"[ServiceRegistry] 连续心跳失败，尝试重新注册...")
                if self.register():
                    print(f"[ServiceRegistry] 重新注册成功")
                    self._consecutive_failures = 0
            return False

    def _heartbeat_loop(self):
        """心跳循环"""
        while self._running:
            self.heartbeat()
            time.sleep(self.heartbeat_interval)

    def start(self):
        """启动服务注册和心跳

        Raises:
            RuntimeError: 注册失败时抛出
        """
        if self._running:
            return

        # 注册服务
        if not self.register():
            raise RuntimeError(f"服务注册失败: {self.namespace} -> {self.host}:{self.port}")

        print(f"[ServiceRegistry] 已注册: {self.namespace} -> {self.host}:{self.port} (weight={self.weight})")

        # 启动心跳线程
        self._running = True
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()

        print(f"[ServiceRegistry] 心跳已启动，间隔: {self.heartbeat_interval}秒")

        # 注册退出钩子
        if self.auto_deregister:
            atexit.register(self.stop)

    def stop(self):
        """停止心跳并注销服务"""
        if not self._running:
            return

        self._running = False

        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=2)

        if self.auto_deregister:
            self.deregister()
            print(f"[ServiceRegistry] 已注销: {self.namespace} -> {self.host}:{self.port}")

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._running

    @property
    def is_registered(self) -> bool:
        """是否已注册"""
        return self._registered

    def __repr__(self):
        return (
            f"ServiceRegistry(namespace={self.namespace!r}, "
            f"host={self.host!r}, port={self.port}, "
            f"weight={self.weight}, running={self._running})"
        )

