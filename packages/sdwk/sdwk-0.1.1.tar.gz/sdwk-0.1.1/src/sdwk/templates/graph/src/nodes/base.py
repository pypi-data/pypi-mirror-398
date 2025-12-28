"""
基础节点类 - 所有节点的基类
"""
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..models import NodeData, NodeResult, NodeStatus


class BaseNode(ABC):
    """
    基础节点类

    所有自定义节点都应该继承这个类并实现 execute 方法
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化节点

        Args:
            config: 节点配置字典，包含节点的所有配置参数
        """
        self.node_id = config.get("id", "unknown")
        self.node_type = config.get("type", self.__class__.__name__)
        self.name = config.get("name", self.node_id)
        self.description = config.get("description", "")
        self.config = config.get("config", {})
        self.position = config.get("position", {})

        # 执行状态
        self.status = NodeStatus.PENDING
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.error: Optional[str] = None

    @abstractmethod
    async def execute(self, input_data: NodeData) -> NodeData:
        """
        执行节点逻辑

        Args:
            input_data: 输入数据

        Returns:
            NodeData: 输出数据

        Raises:
            Exception: 执行过程中的任何错误
        """
        pass

    async def run(self, input_data: NodeData) -> NodeResult:
        """
        运行节点并返回执行结果

        Args:
            input_data: 输入数据

        Returns:
            NodeResult: 节点执行结果
        """
        self.start_time = time.time()
        self.status = NodeStatus.RUNNING

        try:
            # 执行前置处理
            await self.before_execute(input_data)

            # 执行主要逻辑
            output_data = await self.execute(input_data)

            # 执行后置处理
            output_data = await self.after_execute(output_data)

            self.status = NodeStatus.SUCCESS
            self.end_time = time.time()

            return NodeResult(
                node_id=self.node_id,
                status=self.status,
                data=output_data,
                execution_time=self.end_time - self.start_time,
                start_time=self.start_time,
                end_time=self.end_time
            )

        except Exception as e:
            self.status = NodeStatus.FAILED
            self.error = str(e)
            self.end_time = time.time()

            return NodeResult(
                node_id=self.node_id,
                status=self.status,
                error=self.error,
                execution_time=self.end_time - self.start_time,
                start_time=self.start_time,
                end_time=self.end_time
            )

    async def before_execute(self, input_data: NodeData) -> None:
        """
        执行前的预处理

        Args:
            input_data: 输入数据
        """
        # 默认实现：添加节点信息到元数据
        if input_data.metadata is None:
            input_data.metadata = {}

        input_data.metadata.update({
            "current_node": self.node_id,
            "node_type": self.node_type,
            "processing_start": self.start_time
        })

    async def after_execute(self, output_data: NodeData) -> NodeData:
        """
        执行后的后处理

        Args:
            output_data: 输出数据

        Returns:
            NodeData: 处理后的输出数据
        """
        # 默认实现：更新元数据
        if output_data.metadata is None:
            output_data.metadata = {}

        output_data.metadata.update({
            "processed_by": self.node_id,
            "processing_end": time.time(),
            "node_config": self.config
        })

        return output_data

    def validate_config(self) -> bool:
        """
        验证节点配置

        Returns:
            bool: 配置是否有效
        """
        # 基础验证：检查必需字段
        if not self.node_id:
            return False

        # 子类可以重写此方法添加特定的验证逻辑
        return True

    def get_info(self) -> Dict[str, Any]:
        """
        获取节点信息

        Returns:
            Dict[str, Any]: 节点信息字典
        """
        return {
            "id": self.node_id,
            "type": self.node_type,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "config": self.config,
            "position": self.position
        }

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.node_id}, status={self.status.value})"

    def __repr__(self) -> str:
        return self.__str__()