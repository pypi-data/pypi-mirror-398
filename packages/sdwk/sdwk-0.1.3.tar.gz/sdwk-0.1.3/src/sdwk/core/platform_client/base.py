"""平台 API 客户端基础模块.

提供与 SDW 平台交互的 HTTP 客户端封装。
"""

import os
from typing import Any

import httpx
from loguru import logger


class PlatformAPIError(Exception):
    """平台 API 错误."""

    def __init__(self, message: str, status_code: int | None = None, response_data: Any = None):
        """初始化错误.

        Args:
            message: 错误消息
            status_code: HTTP 状态码
            response_data: 响应数据
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class PlatformHTTPClient:
    """平台 HTTP 客户端基础类.

    提供统一的 HTTP 请求封装,包括:
    - 自动认证
    - 错误处理
    - 重试机制
    - 日志记录
    """

    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """初始化客户端.

        Args:
            base_url: 平台基础 URL
            token: 认证令牌,如果为 None 则从环境变量读取
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
        """
        self.base_url = base_url.rstrip("/")
        self.token = token or os.getenv("SDWK_PLATFORM_TOKEN")
        self.timeout = timeout
        self.max_retries = max_retries

        # 创建 httpx 客户端
        self._client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
        )

    def _get_headers(self, extra_headers: dict[str, str] | None = None) -> dict[str, str]:
        """获取请求头.

        Args:
            extra_headers: 额外的请求头

        Returns:
            完整的请求头字典
        """
        headers = {
            "User-Agent": "SDW-Platform-SDK/0.1.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # 添加认证令牌
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        # 合并额外的请求头
        if extra_headers:
            headers.update(extra_headers)

        return headers

    def _handle_response(self, response: httpx.Response) -> Any:
        """处理响应.

        Args:
            response: HTTP 响应对象

        Returns:
            解析后的响应数据

        Raises:
            PlatformAPIError: 当请求失败时
        """
        # 记录响应
        logger.debug(f"Response status: {response.status_code}")

        # 检查状态码
        if response.status_code >= 400:
            # 尝试解析错误信息
            try:
                error_data = response.json()
                error_message = error_data.get("message") or error_data.get("detail") or response.text
            except Exception:
                error_message = response.text or f"HTTP {response.status_code}"

            raise PlatformAPIError(
                message=f"平台 API 请求失败: {error_message}",
                status_code=response.status_code,
                response_data=error_data if "error_data" in locals() else None,
            )

        # 解析响应
        try:
            return response.json()
        except Exception:
            # 如果不是 JSON,返回文本
            return response.text

    def request(
        self,
        method: str,
        endpoint: str,
        data: Any = None,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        files: dict[str, Any] | None = None,
    ) -> Any:
        """发送 HTTP 请求.

        Args:
            method: HTTP 方法 (GET, POST, PUT, DELETE 等)
            endpoint: API 端点路径
            data: 表单数据
            json: JSON 数据
            params: URL 参数
            headers: 额外的请求头
            files: 文件上传

        Returns:
            响应数据

        Raises:
            PlatformAPIError: 当请求失败时
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = self._get_headers(headers)

        logger.debug(f"Request: {method} {url}")

        # 重试逻辑
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self._client.request(
                    method=method,
                    url=url,
                    data=data,
                    json=json,
                    params=params,
                    headers=request_headers,
                    files=files,
                )
                return self._handle_response(response)

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_error = e
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    continue
                raise PlatformAPIError(f"请求超时或网络错误: {e}") from e

            except PlatformAPIError:
                # API 错误不重试
                raise

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error: {e}")
                raise PlatformAPIError(f"请求失败: {e}") from e

        # 如果所有重试都失败
        raise PlatformAPIError(f"请求失败,已重试 {self.max_retries} 次") from last_error

    def get(self, endpoint: str, params: dict[str, Any] | None = None, **kwargs) -> Any:
        """发送 GET 请求."""
        return self.request("GET", endpoint, params=params, **kwargs)

    def post(self, endpoint: str, json: Any = None, data: Any = None, **kwargs) -> Any:
        """发送 POST 请求."""
        return self.request("POST", endpoint, json=json, data=data, **kwargs)

    def put(self, endpoint: str, json: Any = None, **kwargs) -> Any:
        """发送 PUT 请求."""
        return self.request("PUT", endpoint, json=json, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> Any:
        """发送 DELETE 请求."""
        return self.request("DELETE", endpoint, **kwargs)

    def close(self):
        """关闭客户端."""
        self._client.close()

    def __enter__(self):
        """上下文管理器入口."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出."""
        self.close()
