"""日志配置加载模块

从平台 API 动态获取 RabbitMQ 日志配置。
"""

import os
from typing import Any

from loguru import logger


def load_logging_config() -> dict[str, Any]:
    """加载日志配置

    从平台 API 动态获取 RabbitMQ 配置。

    Returns:
        日志配置字典，包含以下字段：
        - enabled: 是否启用 RabbitMQ 日志
        - rabbitmq_host: RabbitMQ 服务器地址
        - rabbitmq_port: RabbitMQ 端口
        - rabbitmq_user: RabbitMQ 用户名
        - rabbitmq_password: RabbitMQ 密码
        - enable_local_log: 是否启用本地日志

    """
    try:
        # 导入 SDK 配置和平台客户端
        from ..platform_client import PlatformClient
        from ..project_settings import settings

        # 获取平台地址
        platform_url = settings.get("platform.url")
        if not platform_url:
            logger.warning("未配置平台地址，RabbitMQ 日志功能将被禁用")
            return _get_default_config()

        # 从配置中获取本地日志开关
        enable_local_log = settings.get("logging.enable_local_log", True)

        # 调用平台 API 获取 RabbitMQ 配置
        try:
            with PlatformClient(platform_url) as client:
                rabbitmq_config = client.get_rabbitmq_config()

            # 构建日志配置
            logging_config = {
                "enabled": rabbitmq_config.get("enabled", False),
                "rabbitmq_host": rabbitmq_config.get("host"),
                "rabbitmq_port": rabbitmq_config.get("port", 5672),
                "rabbitmq_user": rabbitmq_config.get("user", "guest"),
                "rabbitmq_password": rabbitmq_config.get("password", "guest"),
                "enable_local_log": enable_local_log,
            }

            if logging_config["enabled"]:
                logger.info(f"已从平台获取 RabbitMQ 配置: {rabbitmq_config.get('host')}:{rabbitmq_config.get('port')}")

            return logging_config

        except Exception as e:
            logger.warning(f"从平台获取 RabbitMQ 配置失败: {e}，RabbitMQ 日志功能将被禁用")
            return _get_default_config(enable_local_log=enable_local_log)

    except Exception as e:
        # 配置加载失败，返回默认配置
        logger.warning(f"加载日志配置失败: {e}，使用默认配置")
        return _get_default_config()


def _get_default_config(enable_local_log: bool = True) -> dict[str, Any]:
    """获取默认配置

    Args:
        enable_local_log: 是否启用本地日志

    Returns:
        默认日志配置
    """
    return {
        "enabled": False,
        "rabbitmq_host": None,
        "rabbitmq_port": 5672,
        "rabbitmq_user": "guest",
        "rabbitmq_password": "guest",
        "enable_local_log": enable_local_log,
    }


def get_workflow_context() -> dict[str, str | None]:
    """获取工作流上下文信息

    从环境变量中获取 user_id 和 workflow_id

    Returns:
        包含 user_id 和 workflow_id 的字典

    # 这里的 user_id 和 workflow_id 应该是平台传参带过来的
    

    """
    return {
        "user_id": "test_user",  
        "workflow_id": "test_workflow"
    }
