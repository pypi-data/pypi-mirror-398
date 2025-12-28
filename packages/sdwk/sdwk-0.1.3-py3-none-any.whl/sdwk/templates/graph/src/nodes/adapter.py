"""组件适配器

将 Component 包装成 GraphEngine 期望的节点接口
"""

import asyncio
from typing import Any, Dict

from sdwk import Component
from ..models import NodeData, NodeResult, NodeStatus


class ComponentAdapter:
    """组件适配器

    将同步的 Component 包装成异步节点，供 GraphEngine 使用
    """

    def __init__(self, component: Component, node_config: Dict[str, Any]):
        """初始化适配器

        Args:
            component: Component 实例
            node_config: 节点配置
        """
        self.component = component
        self.node_id = node_config.get("id", "unknown")
        self.config = node_config.get("config", {})
        self.status = NodeStatus.PENDING

    async def run(self, input_data: NodeData) -> NodeResult:
        """执行组件

        Args:
            input_data: 输入数据

        Returns:
            NodeResult: 执行结果
        """
        import time

        start_time = time.time()

        try:
            self.status = NodeStatus.RUNNING

            # 从 input_data 中提取数据并设置到 component 的输入
            data_dict = input_data.data if isinstance(input_data.data, dict) else {}

            # 将 data_dict 的键值设置为 component 的输入
            for input_def in self.component.inputs:
                if input_def.name in data_dict:
                    self.component.set_input_value(input_def.name, data_dict[input_def.name])
                elif input_def.name in self.config:
                    # 从配置中获取
                    self.component.set_input_value(input_def.name, self.config[input_def.name])

            # 在线程池中执行同步的 component.execute()
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.component.execute)

            self.status = NodeStatus.SUCCESS

            # 将 Data 转换为 NodeData
            output_node_data = NodeData(
                data=result.value,
                metadata=result.metadata,
                node_id=self.node_id,
            )

            execution_time = time.time() - start_time

            return NodeResult(
                node_id=self.node_id,
                status=NodeStatus.SUCCESS,
                data=output_node_data,
                execution_time=execution_time,
            )

        except Exception as e:
            self.status = NodeStatus.FAILED
            execution_time = time.time() - start_time

            return NodeResult(
                node_id=self.node_id,
                status=NodeStatus.FAILED,
                error=str(e),
                execution_time=execution_time,
            )

    def get_info(self) -> Dict[str, Any]:
        """获取组件信息

        Returns:
            Dict[str, Any]: 组件信息
        """
        return {
            "node_id": self.node_id,
            "component_name": self.component.name,
            "display_name": self.component.display_name,
            "description": self.component.description,
            "status": self.status.value,
            "inputs": [input_def.model_dump() for input_def in self.component.inputs],
            "outputs": [output_def.model_dump() for output_def in self.component.outputs],
        }
