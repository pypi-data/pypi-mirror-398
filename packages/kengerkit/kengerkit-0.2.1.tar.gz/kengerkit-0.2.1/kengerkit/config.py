# coding=utf-8
"""配置管理客户端"""

from typing import Any, Optional, Dict


class ConfigClient:
    """配置管理客户端

    提供配置的增删改查功能。

    Usage:
        client = KengerClient(base_url, token)

        # 获取配置值
        value = client.config.get("my_key")

        # 设置配置
        client.config.set("key", "value", value_type="str", description="描述")

        # 更新配置
        client.config.update(config_id=1, value="new_value")

        # 删除配置
        client.config.delete(config_id=1)

        # 列出配置
        result = client.config.list(page=1, page_size=10)

        # 搜索配置
        result = client.config.search("keyword")
    """

    def __init__(self, http_client):
        self._http = http_client

    def get(self, key: str) -> Optional[Any]:
        """通过 key 获取配置值

        Args:
            key: 配置键名

        Returns:
            配置值，如果不存在返回 None

        Note:
            此方法通过搜索接口实现，返回精确匹配的第一个结果的值
        """
        result = self.search(key, page=1, page_size=100)
        items = result.get("items", [])

        for item in items:
            if item.get("key") == key:
                return item.get("value")

        return None

    def get_detail(self, key: str) -> Optional[Dict[str, Any]]:
        """通过 key 获取配置详情

        Args:
            key: 配置键名

        Returns:
            配置详情字典，包含 id, key, value, value_type, description 等
            如果不存在返回 None
        """
        result = self.search(key, page=1, page_size=100)
        items = result.get("items", [])

        for item in items:
            if item.get("key") == key:
                return item

        return None

    def set(
        self,
        key: str,
        value: Any,
        value_type: str = "str",
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """新增配置

        Args:
            key: 配置键名
            value: 配置值
            value_type: 值类型，支持 str, int, float, bool, json
            description: 配置描述

        Returns:
            新增的配置详情

        Raises:
            ValidationError: key 已存在或参数无效
        """
        payload = {
            "key": key,
            "value": value,
            "value_type": value_type,
        }
        if description is not None:
            payload["description"] = description

        response = self._http.post("/api/config/add", json=payload)
        return response.get("data")

    def update(
        self,
        config_id: int,
        value: Optional[Any] = None,
        value_type: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """更新配置

        Args:
            config_id: 配置 ID
            value: 新的配置值
            value_type: 新的值类型
            description: 新的描述

        Returns:
            更新后的配置详情

        Raises:
            ValidationError: 配置不存在或参数无效
        """
        payload = {"id": config_id}

        if value is not None:
            payload["value"] = value
        if value_type is not None:
            payload["value_type"] = value_type
        if description is not None:
            payload["description"] = description

        response = self._http.post("/api/config/update", json=payload)
        return response.get("data")

    def update_by_key(
        self,
        key: str,
        value: Optional[Any] = None,
        value_type: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """通过 key 更新配置

        Args:
            key: 配置键名
            value: 新的配置值
            value_type: 新的值类型
            description: 新的描述

        Returns:
            更新后的配置详情

        Raises:
            ValidationError: 配置不存在
        """
        detail = self.get_detail(key)
        if detail is None:
            from .exceptions import ValidationError
            raise ValidationError(f"配置 '{key}' 不存在")

        return self.update(
            config_id=detail["id"],
            value=value,
            value_type=value_type,
            description=description,
        )

    def delete(self, config_id: int) -> bool:
        """删除配置

        Args:
            config_id: 配置 ID

        Returns:
            是否删除成功

        Raises:
            ValidationError: 配置不存在
        """
        self._http.post("/api/config/delete", json={"id": config_id})
        return True

    def delete_by_key(self, key: str) -> bool:
        """通过 key 删除配置

        Args:
            key: 配置键名

        Returns:
            是否删除成功

        Raises:
            ValidationError: 配置不存在
        """
        detail = self.get_detail(key)
        if detail is None:
            from .exceptions import ValidationError
            raise ValidationError(f"配置 '{key}' 不存在")

        return self.delete(detail["id"])

    def list(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """分页获取配置列表

        Args:
            page: 页码，从 1 开始
            page_size: 每页数量

        Returns:
            {
                "items": [...],
                "total": int,
                "page": int,
                "page_size": int
            }
        """
        response = self._http.get(
            "/api/config/list",
            params={"page": page, "page_size": page_size},
        )
        return response.get("data")

    def search(self, key: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """通过 key 模糊搜索配置

        Args:
            key: 搜索关键字
            page: 页码，从 1 开始
            page_size: 每页数量

        Returns:
            {
                "items": [...],
                "total": int,
                "page": int,
                "page_size": int
            }
        """
        response = self._http.get(
            "/api/config/search",
            params={"key": key, "page": page, "page_size": page_size},
        )
        return response.get("data")

    def set_or_update(
        self,
        key: str,
        value: Any,
        value_type: str = "str",
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """设置或更新配置（如果存在则更新，不存在则新增）

        Args:
            key: 配置键名
            value: 配置值
            value_type: 值类型
            description: 配置描述

        Returns:
            配置详情
        """
        detail = self.get_detail(key)

        if detail is None:
            return self.set(key, value, value_type, description)
        else:
            return self.update(
                config_id=detail["id"],
                value=value,
                value_type=value_type,
                description=description,
            )

