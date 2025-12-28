"""
自定义节点实现 - 包含各种具体的节点类型
"""
import time
from typing import Dict, Any, List

from .base import BaseNode
from ..models import NodeData


class InputNode(BaseNode):
    """
    输入节点 - 工作流的入口点
    """

    async def execute(self, input_data: NodeData) -> NodeData:
        """
        处理输入数据

        Args:
            input_data: 输入数据

        Returns:
            NodeData: 处理后的输入数据
        """
        # 验证输入数据格式
        schema = self.config.get("schema", {})
        if schema:
            # 这里可以添加更复杂的schema验证逻辑
            pass

        # 添加输入节点的元数据
        output_data = NodeData(
            data=input_data.data.copy(),
            metadata={
                **input_data.metadata,
                "input_received_at": time.time(),
                "input_node_id": self.node_id
            },
            node_id=self.node_id
        )

        return output_data


class OutputNode(BaseNode):
    """
    输出节点 - 工作流的出口点
    """

    async def execute(self, input_data: NodeData) -> NodeData:
        """
        处理输出数据

        Args:
            input_data: 输入数据

        Returns:
            NodeData: 最终输出数据
        """
        output_format = self.config.get("output_format", "json")
        include_metadata = self.config.get("include_metadata", True)

        # 构建最终输出
        final_data = input_data.data.copy()

        # 根据配置决定是否包含元数据
        output_metadata = input_data.metadata.copy() if include_metadata else {}
        output_metadata.update({
            "output_generated_at": time.time(),
            "output_format": output_format,
            "final_node_id": self.node_id
        })

        return NodeData(
            data=final_data,
            metadata=output_metadata,
            node_id=self.node_id
        )


class ValidationNode(BaseNode):
    """
    验证节点 - 验证数据的有效性
    """

    async def execute(self, input_data: NodeData) -> NodeData:
        """
        验证输入数据

        Args:
            input_data: 输入数据

        Returns:
            NodeData: 验证后的数据

        Raises:
            ValueError: 当数据验证失败时
        """
        validation_rules = self.config.get("validation_rules", [])
        data = input_data.data

        validation_results = []

        for rule in validation_rules:
            field = rule.get("field")
            required = rule.get("required", False)
            field_type = rule.get("type")

            # 检查必需字段
            if required:
                if not self._has_field(data, field):
                    raise ValueError(f"Required field missing: {field}")

            # 检查字段类型
            if field_type and self._has_field(data, field):
                field_value = self._get_field_value(data, field)
                if not self._validate_type(field_value, field_type):
                    raise ValueError(f"Field {field} has invalid type. Expected: {field_type}")

            validation_results.append({
                "field": field,
                "status": "valid"
            })

        # 添加验证结果到元数据
        output_metadata = input_data.metadata.copy()
        output_metadata.update({
            "validation_result": "valid",
            "validation_details": validation_results,
            "validated_at": time.time()
        })

        return NodeData(
            data=data,
            metadata=output_metadata,
            node_id=self.node_id
        )

    def _has_field(self, data: Dict[str, Any], field_path: str) -> bool:
        """检查字段是否存在"""
        keys = field_path.split(".")
        current = data

        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return False
            current = current[key]

        return True

    def _get_field_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """获取字段值"""
        keys = field_path.split(".")
        current = data

        for key in keys:
            current = current[key]

        return current

    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """验证字段类型"""
        type_mapping = {
            "string": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict
        }

        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type is None:
            return True  # 未知类型，跳过验证

        return isinstance(value, expected_python_type)


class CustomProcessNode(BaseNode):
    """
    自定义处理节点 - 执行主要的业务逻辑
    """

    async def execute(self, input_data: NodeData) -> NodeData:
        """
        执行自定义处理逻辑

        Args:
            input_data: 输入数据

        Returns:
            NodeData: 处理后的数据
        """
        processing_mode = self.config.get("processing_mode", "standard")
        parameters = self.config.get("parameters", {})

        data = input_data.data.copy()
        processed_data = {}

        # 根据处理模式执行不同的逻辑
        if processing_mode == "standard":
            processed_data = await self._standard_processing(data, parameters)
        elif processing_mode == "advanced":
            processed_data = await self._advanced_processing(data, parameters)
        else:
            # 默认处理：简单的数据转换
            processed_data = await self._default_processing(data, parameters)

        # 添加处理元数据
        output_metadata = input_data.metadata.copy()
        output_metadata.update({
            "processing_mode": processing_mode,
            "processing_parameters": parameters,
            "processed_at": time.time(),
            "processing_node": self.node_id
        })

        return NodeData(
            data=processed_data,
            metadata=output_metadata,
            node_id=self.node_id
        )

    async def _standard_processing(self, data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """标准处理模式"""
        transform_type = parameters.get("transform_type", "none")
        add_timestamp = parameters.get("add_timestamp", False)

        processed = data.copy()

        # 文本转换
        if transform_type == "uppercase" and "message" in processed:
            processed["message"] = str(processed["message"]).upper()
        elif transform_type == "lowercase" and "message" in processed:
            processed["message"] = str(processed["message"]).lower()

        # 添加时间戳
        if add_timestamp:
            processed["processed_timestamp"] = time.time()

        return processed

    async def _advanced_processing(self, data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """高级处理模式"""
        # TODO: 实现更复杂的处理逻辑
        processed = data.copy()
        processed["advanced_processing"] = True
        processed["processing_parameters"] = parameters
        return processed

    async def _default_processing(self, data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """默认处理模式"""
        processed = data.copy()
        processed["default_processing"] = True
        return processed


class EnrichmentNode(BaseNode):
    """
    数据增强节点 - 为数据添加额外信息
    """

    async def execute(self, input_data: NodeData) -> NodeData:
        """
        增强数据

        Args:
            input_data: 输入数据

        Returns:
            NodeData: 增强后的数据
        """
        enrichment_sources = self.config.get("enrichment_sources", [])
        merge_strategy = self.config.get("merge_strategy", "append")

        data = input_data.data.copy()
        enriched_data = data.copy()

        # 根据不同的增强源添加信息
        for source in enrichment_sources:
            if source == "metadata":
                enriched_data = await self._enrich_from_metadata(enriched_data, input_data.metadata)
            elif source == "context":
                enriched_data = await self._enrich_from_context(enriched_data)
            elif source == "external":
                enriched_data = await self._enrich_from_external(enriched_data)

        # 添加增强元数据
        output_metadata = input_data.metadata.copy()
        output_metadata.update({
            "enrichment_sources": enrichment_sources,
            "merge_strategy": merge_strategy,
            "enriched_at": time.time(),
            "enrichment_node": self.node_id
        })

        return NodeData(
            data=enriched_data,
            metadata=output_metadata,
            node_id=self.node_id
        )

    async def _enrich_from_metadata(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """从元数据中增强"""
        enriched = data.copy()
        enriched["metadata_info"] = {
            "processing_history": [
                node for node in metadata.keys()
                if node.endswith("_node") or node.endswith("_node_id")
            ],
            "total_processing_nodes": len([
                k for k in metadata.keys()
                if k.endswith("_node") or k.endswith("_node_id")
            ])
        }
        return enriched

    async def _enrich_from_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """从上下文中增强"""
        enriched = data.copy()
        enriched["context_info"] = {
            "execution_environment": "{{ project_name }}",
            "node_type": "graph",
            "enrichment_timestamp": time.time()
        }
        return enriched

    async def _enrich_from_external(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """从外部源增强"""
        # TODO: 实现从外部API或数据库获取数据的逻辑
        enriched = data.copy()
        enriched["external_info"] = {
            "source": "external_api",
            "status": "not_implemented"
        }
        return enriched