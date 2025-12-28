"""RabbitMQ 日志发布器 - 将日志推送到消息队列."""

import json
import time
from typing import Any

import pika
from loguru import logger


class LogPublisher:
    """RabbitMQ 日志发布器.

    负责将日志消息发送到 RabbitMQ 的 Topic Exchange，
    平台服务可以订阅对应的队列接收日志流。
    """

    def __init__(
        self,
        rabbitmq_host: str,
        rabbitmq_port: int = 5672,
        rabbitmq_user: str = "guest",
        rabbitmq_password: str = "guest",
        user_id: str | None = None,
        workflow_id: str | None = None,
        exchange_name: str = "logs_exchange",
        enable_local_log: bool = True,
    ):
        """初始化日志发布器.

        Args:
            rabbitmq_host: RabbitMQ 服务器地址
            rabbitmq_port: RabbitMQ 端口
            rabbitmq_user: RabbitMQ 用户名
            rabbitmq_password: RabbitMQ 密码
            user_id: 用户ID（用于路由）
            workflow_id: 工作流ID（用于路由）
            exchange_name: Exchange 名称
            enable_local_log: 是否同时输出到本地日志

        """
        self.rabbitmq_host = rabbitmq_host
        self.rabbitmq_port = rabbitmq_port
        self.rabbitmq_user = rabbitmq_user
        self.rabbitmq_password = rabbitmq_password
        self.user_id = user_id or "unknown"
        self.workflow_id = workflow_id or "unknown"
        self.exchange_name = exchange_name
        self.enable_local_log = enable_local_log

        # RabbitMQ 连接和通道
        self.connection: pika.BlockingConnection | None = None
        self.channel: pika.channel.Channel | None = None

        # 初始化连接
        self._connect()

    def _connect(self) -> None:
        """建立 RabbitMQ 连接."""
        try:
            # 创建连接参数
            credentials = pika.PlainCredentials(self.rabbitmq_user, self.rabbitmq_password)
            parameters = pika.ConnectionParameters(
                host=self.rabbitmq_host,
                port=self.rabbitmq_port,
                credentials=credentials,
                heartbeat=600,  # 心跳间隔
                blocked_connection_timeout=300,  # 阻塞超时
            )

            # 建立连接
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # 声明 Topic Exchange
            self.channel.exchange_declare(exchange=self.exchange_name, exchange_type="topic", durable=True)

            if self.enable_local_log:
                logger.info(f"RabbitMQ 日志发布器已连接: {self.rabbitmq_host}:{self.rabbitmq_port}")

        except Exception as e:
            error_msg = f"连接 RabbitMQ 失败: {e}"
            if self.enable_local_log:
                logger.error(error_msg)
            # 不抛出异常，允许降级到本地日志
            self.connection = None
            self.channel = None

    def publish(self, level: str, message: str, **extra: Any) -> None:
        """发布日志消息到 RabbitMQ.

        Args:
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: 日志消息
            **extra: 额外的日志字段

        """
        # 构建日志数据
        log_data = {
            "level": level.upper(),
            "message": message,
            "timestamp": time.time(),
            "user_id": self.user_id,
            "workflow_id": self.workflow_id,
            **extra,
        }

        # 本地日志输出
        if self.enable_local_log:
            logger.log(level.upper(), f"[{self.workflow_id}] {message}")

        # 发送到 RabbitMQ
        if self.channel and self.connection and not self.connection.is_closed:
            try:
                # 构建 Routing Key: workflow.<user_id>.<workflow_id>.logs
                routing_key = f"workflow.{self.user_id}.{self.workflow_id}.logs"

                # 发布消息
                self.channel.basic_publish(
                    exchange=self.exchange_name,
                    routing_key=routing_key,
                    body=json.dumps(log_data, ensure_ascii=False),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # 持久化消息
                        content_type="application/json",
                    ),
                )

            except Exception as e:
                if self.enable_local_log:
                    logger.error(f"发送日志到 RabbitMQ 失败: {e}")
                # 尝试重连
                self._reconnect()

    def _reconnect(self) -> None:
        """重新连接 RabbitMQ."""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception:
            pass

        self._connect()

    def close(self) -> None:
        """关闭连接."""
        try:
            # 检查 channel 是否存在且未关闭
            if self.channel and self.channel.is_open:
                self.channel.close()

            # 检查 connection 是否存在且未关闭
            if self.connection and not self.connection.is_closed:
                self.connection.close()

            if self.enable_local_log:
                logger.info("RabbitMQ 日志发布器已关闭")

        except Exception as e:
            if self.enable_local_log:
                logger.error(f"关闭 RabbitMQ 连接失败: {e}")

    def __enter__(self):
        """上下文管理器入口."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出."""
        self.close()


def setup_component_logger(
    rabbitmq_host: str | None = None,
    rabbitmq_port: int = 5672,
    rabbitmq_user: str = "guest",
    rabbitmq_password: str = "guest",
    user_id: str | None = None,
    workflow_id: str | None = None,
    enable_local_log: bool = True,
) -> LogPublisher | None:
    """设置组件日志发布器.

    Args:
        rabbitmq_host: RabbitMQ 服务器地址（如果为 None，则不启用 RabbitMQ）
        rabbitmq_port: RabbitMQ 端口
        rabbitmq_user: RabbitMQ 用户名
        rabbitmq_password: RabbitMQ 密码
        user_id: 用户ID
        workflow_id: 工作流ID
        enable_local_log: 是否启用本地日志

    Returns:
        LogPublisher 实例，如果未启用则返回 None

    """
    if not rabbitmq_host:
        # 未配置 RabbitMQ，仅使用本地日志
        if enable_local_log:
            logger.info("未配置 RabbitMQ，仅使用本地日志")
        return None

    # 创建日志发布器
    return LogPublisher(
        rabbitmq_host=rabbitmq_host,
        rabbitmq_port=rabbitmq_port,
        rabbitmq_user=rabbitmq_user,
        rabbitmq_password=rabbitmq_password,
        user_id=user_id,
        workflow_id=workflow_id,
        enable_local_log=enable_local_log,
    )
