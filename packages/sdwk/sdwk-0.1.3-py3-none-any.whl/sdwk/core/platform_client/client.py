"""平台 API 客户端.

提供与 SDW 平台交互的高级 API 封装。
"""

from typing import Any

from .base import PlatformAPIError, PlatformHTTPClient


class PlatformClient:
    """平台 API 客户端.

    提供与 SDW 平台交互的完整功能,包括:
    - 获取平台配置(如 RabbitMQ 配置)
    - 推送节点执行成果物
    - 通用 API 调用
    """

    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """初始化平台客户端.

        Args:
            base_url: 平台基础 URL
            token: 认证令牌
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
        """
        self._http_client = PlatformHTTPClient(
            base_url=base_url,
            token=token,
            timeout=timeout,
            max_retries=max_retries,
        )

    def get_rabbitmq_config(self) -> dict[str, Any]:
        """获取 RabbitMQ 配置.

        从平台获取 RabbitMQ 连接配置信息。

        Returns:
            RabbitMQ 配置字典,包含:
            - enabled: 是否启用
            - host: 服务器地址
            - port: 端口
            - user: 用户名
            - password: 密码
            - exchange: 交换机名称
            - routing_key: 路由键

        Raises:
            PlatformAPIError: 当请求失败时

        Example:
            >>> client = PlatformClient("https://platform.sdw.com")
            >>> config = client.get_rabbitmq_config()
            >>> print(config["host"])
        """
        try:
            response = self._http_client.get("/api/config/rabbitmq")
            return response
        except PlatformAPIError:
            raise
        except Exception as e:
            raise PlatformAPIError(f"获取 RabbitMQ 配置失败: {e}") from e

    def get_platform_config(self, config_key: str | None = None) -> dict[str, Any]:
        """获取平台配置.

        获取平台的通用配置信息。

        Args:
            config_key: 配置键,如果为 None 则获取所有配置

        Returns:
            配置字典

        Raises:
            PlatformAPIError: 当请求失败时

        Example:
            >>> client = PlatformClient("https://platform.sdw.com")
            >>> config = client.get_platform_config("logging")
        """
        endpoint = "/api/config"
        if config_key:
            endpoint = f"{endpoint}/{config_key}"

        try:
            response = self._http_client.get(endpoint)
            return response
        except PlatformAPIError:
            raise
        except Exception as e:
            raise PlatformAPIError(f"获取平台配置失败: {e}") from e

    def push_artifact(
        self,
        workflow_id: str,
        node_id: str,
        artifact_data: Any,
        artifact_type: str = "result",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """推送节点执行成果物到平台.

        Args:
            workflow_id: 工作流 ID
            node_id: 节点 ID
            artifact_data: 成果物数据
            artifact_type: 成果物类型 (result, log, file 等)
            metadata: 额外的元数据

        Returns:
            推送结果,包含 artifact_id 等信息

        Raises:
            PlatformAPIError: 当请求失败时

        Example:
            >>> client = PlatformClient("https://platform.sdw.com")
            >>> result = client.push_artifact(
            ...     workflow_id="wf_123",
            ...     node_id="node_456",
            ...     artifact_data={"result": "success"},
            ...     artifact_type="result"
            ... )
        """
        payload = {
            "workflow_id": workflow_id,
            "node_id": node_id,
            "artifact_type": artifact_type,
            "data": artifact_data,
            "metadata": metadata or {},
        }

        try:
            response = self._http_client.post("/api/artifacts", json=payload)
            return response
        except PlatformAPIError:
            raise
        except Exception as e:
            raise PlatformAPIError(f"推送成果物失败: {e}") from e

    def upload_file(
        self,
        file_path: str,
        workflow_id: str | None = None,
        node_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """上传文件到平台.

        Args:
            file_path: 文件路径
            workflow_id: 工作流 ID (可选)
            node_id: 节点 ID (可选)
            metadata: 额外的元数据

        Returns:
            上传结果,包含 file_id, url 等信息

        Raises:
            PlatformAPIError: 当请求失败时

        Example:
            >>> client = PlatformClient("https://platform.sdw.com")
            >>> result = client.upload_file("/path/to/file.txt")
            >>> print(result["file_id"])
        """
        import os
        from pathlib import Path

        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise PlatformAPIError(f"文件不存在: {file_path}")

        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_path_obj.name, f)}
                data = {}
                if workflow_id:
                    data["workflow_id"] = workflow_id
                if node_id:
                    data["node_id"] = node_id
                if metadata:
                    import json
                    data["metadata"] = json.dumps(metadata)

                response = self._http_client.post("/api/files/upload", files=files, data=data)
                return response
        except PlatformAPIError:
            raise
        except Exception as e:
            raise PlatformAPIError(f"上传文件失败: {e}") from e

    def call_api(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> Any:
        """通用 API 调用方法.

        提供灵活的 API 调用能力,支持任意 HTTP 方法和参数。

        Args:
            method: HTTP 方法 (GET, POST, PUT, DELETE 等)
            endpoint: API 端点路径
            **kwargs: 其他参数,如 json, data, params, headers 等

        Returns:
            API 响应数据

        Raises:
            PlatformAPIError: 当请求失败时

        Example:
            >>> client = PlatformClient("https://platform.sdw.com")
            >>> # GET 请求
            >>> result = client.call_api("GET", "/api/users", params={"page": 1})
            >>> # POST 请求
            >>> result = client.call_api("POST", "/api/data", json={"key": "value"})
        """
        return self._http_client.request(method, endpoint, **kwargs)

    def close(self):
        """关闭客户端."""
        self._http_client.close()

    def __enter__(self):
        """上下文管理器入口."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出."""
        self.close()
