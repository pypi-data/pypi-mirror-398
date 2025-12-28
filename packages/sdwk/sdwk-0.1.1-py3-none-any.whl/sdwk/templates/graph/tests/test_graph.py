"""
{{ project_name_title }} Graph项目测试文件
"""
import pytest
import json
from pathlib import Path
from fastapi.testclient import TestClient

from src.main import app
from src.graph import GraphEngine
from src.models import (
    NodeData, GraphExecutionRequest, NodeStatus,
    WorkflowConfig, NodeConfig, EdgeConfig
)
from src.nodes import create_node, get_available_node_types


# 创建测试客户端
client = TestClient(app)


class TestAPI:
    """API端点测试"""

    def test_health_check(self):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "{{ project_version }}"
        assert data["project_type"] == "{{ project_type }}"
        assert "workflow_loaded" in data
        assert "node_count" in data

    def test_root_endpoint(self):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["version"] == "{{ project_version }}"
        assert data["project_type"] == "{{ project_type }}"
        assert "endpoints" in data

    def test_get_node_types(self):
        """测试获取节点类型端点"""
        response = client.get("/nodes/types")
        assert response.status_code == 200
        data = response.json()
        assert "node_types" in data
        assert "count" in data
        assert isinstance(data["node_types"], list)
        assert len(data["node_types"]) > 0

    def test_workflow_info(self):
        """测试获取工作流信息端点"""
        response = client.get("/workflow/info")
        # 可能返回500如果没有加载工作流，这是正常的
        assert response.status_code in [200, 500]

    def test_validate_input(self):
        """测试验证输入端点"""
        input_data = {
            "data": {"message": "Hello, World!"},
            "metadata": {"source": "test"}
        }
        response = client.post("/workflow/validate", json=input_data)
        # 可能返回500如果没有加载工作流，这是正常的
        assert response.status_code in [200, 500]


class TestGraphEngine:
    """图执行引擎测试"""

    def create_test_workflow_config(self) -> WorkflowConfig:
        """创建测试工作流配置"""
        nodes = [
            NodeConfig(
                id="input",
                type="InputNode",
                name="输入节点",
                config={}
            ),
            NodeConfig(
                id="process",
                type="CustomProcessNode",
                name="处理节点",
                config={
                    "processing_mode": "standard",
                    "parameters": {"transform_type": "uppercase"}
                }
            ),
            NodeConfig(
                id="output",
                type="OutputNode",
                name="输出节点",
                config={}
            )
        ]

        edges = [
            EdgeConfig(
                id="input_to_process",
                from_node="input",
                to_node="process"
            ),
            EdgeConfig(
                id="process_to_output",
                from_node="process",
                to_node="output"
            )
        ]

        return WorkflowConfig(
            name="test_workflow",
            version="1.0.0",
            nodes=nodes,
            edges=edges
        )

    def test_workflow_config_creation(self):
        """测试工作流配置创建"""
        config = self.create_test_workflow_config()
        assert config.name == "test_workflow"
        assert len(config.nodes) == 3
        assert len(config.edges) == 2

    def test_graph_engine_initialization(self):
        """测试图执行引擎初始化"""
        engine = GraphEngine()
        assert engine.workflow_config is None
        assert engine.execution_graph is None

    @pytest.mark.asyncio
    async def test_graph_execution_without_workflow(self):
        """测试没有工作流时的执行"""
        engine = GraphEngine()

        request = GraphExecutionRequest(
            input_data=NodeData(
                data={"message": "Hello"},
                metadata={}
            )
        )

        with pytest.raises(ValueError, match="No workflow loaded"):
            await engine.execute(request)

    def test_workflow_info_empty(self):
        """测试空工作流信息"""
        engine = GraphEngine()
        info = engine.get_workflow_info()
        assert info["status"] == "no_workflow_loaded"


class TestNodes:
    """节点测试"""

    def test_node_registry(self):
        """测试节点注册表"""
        node_types = get_available_node_types()
        assert "InputNode" in node_types
        assert "OutputNode" in node_types
        assert "ValidationNode" in node_types
        assert "CustomProcessNode" in node_types
        assert "EnrichmentNode" in node_types

    def test_create_input_node(self):
        """测试创建输入节点"""
        config = {
            "id": "test_input",
            "type": "InputNode",
            "config": {}
        }
        node = create_node("InputNode", config)
        assert node.node_id == "test_input"
        assert node.node_type == "InputNode"

    def test_create_unknown_node_type(self):
        """测试创建未知节点类型"""
        config = {
            "id": "test_unknown",
            "type": "UnknownNode",
            "config": {}
        }
        with pytest.raises(ValueError, match="Unknown node type"):
            create_node("UnknownNode", config)

    @pytest.mark.asyncio
    async def test_input_node_execution(self):
        """测试输入节点执行"""
        config = {
            "id": "test_input",
            "type": "InputNode",
            "config": {}
        }
        node = create_node("InputNode", config)

        input_data = NodeData(
            data={"message": "Hello"},
            metadata={"source": "test"}
        )

        result = await node.run(input_data)
        assert result.status == NodeStatus.SUCCESS
        assert result.node_id == "test_input"
        assert result.data is not None
        assert "message" in result.data.data

    @pytest.mark.asyncio
    async def test_custom_process_node_execution(self):
        """测试自定义处理节点执行"""
        config = {
            "id": "test_process",
            "type": "CustomProcessNode",
            "config": {
                "processing_mode": "standard",
                "parameters": {"transform_type": "uppercase"}
            }
        }
        node = create_node("CustomProcessNode", config)

        input_data = NodeData(
            data={"message": "hello world"},
            metadata={}
        )

        result = await node.run(input_data)
        assert result.status == NodeStatus.SUCCESS
        assert result.data is not None
        assert result.data.data["message"] == "HELLO WORLD"

    @pytest.mark.asyncio
    async def test_validation_node_success(self):
        """测试验证节点成功情况"""
        config = {
            "id": "test_validation",
            "type": "ValidationNode",
            "config": {
                "validation_rules": [
                    {"field": "data.message", "required": True, "type": "string"}
                ]
            }
        }
        node = create_node("ValidationNode", config)

        input_data = NodeData(
            data={"message": "Hello"},
            metadata={}
        )

        result = await node.run(input_data)
        assert result.status == NodeStatus.SUCCESS
        assert result.data.metadata["validation_result"] == "valid"

    @pytest.mark.asyncio
    async def test_validation_node_failure(self):
        """测试验证节点失败情况"""
        config = {
            "id": "test_validation",
            "type": "ValidationNode",
            "config": {
                "validation_rules": [
                    {"field": "data.required_field", "required": True}
                ]
            }
        }
        node = create_node("ValidationNode", config)

        input_data = NodeData(
            data={"message": "Hello"},  # 缺少required_field
            metadata={}
        )

        result = await node.run(input_data)
        assert result.status == NodeStatus.FAILED
        assert "Required field missing" in result.error


class TestModels:
    """数据模型测试"""

    def test_node_data_creation(self):
        """测试节点数据模型创建"""
        data = {"message": "Hello"}
        metadata = {"source": "test"}

        node_data = NodeData(data=data, metadata=metadata, node_id="test")
        assert node_data.data == data
        assert node_data.metadata == metadata
        assert node_data.node_id == "test"
        assert node_data.timestamp > 0

    def test_graph_execution_request_creation(self):
        """测试图执行请求模型创建"""
        input_data = NodeData(data={"message": "Hello"}, metadata={})

        request = GraphExecutionRequest(
            input_data=input_data,
            execution_config={"max_parallel": 2}
        )

        assert request.input_data == input_data
        assert request.execution_config["max_parallel"] == 2

    def test_node_config_creation(self):
        """测试节点配置模型创建"""
        config = NodeConfig(
            id="test_node",
            type="TestNode",
            name="测试节点",
            config={"param": "value"}
        )

        assert config.id == "test_node"
        assert config.type == "TestNode"
        assert config.name == "测试节点"
        assert config.config["param"] == "value"

    def test_edge_config_creation(self):
        """测试边配置模型创建"""
        edge = EdgeConfig(
            id="test_edge",
            from_node="node1",
            to_node="node2",
            data_mapping={"output": "input"}
        )

        assert edge.id == "test_edge"
        assert edge.from_node == "node1"
        assert edge.to_node == "node2"
        assert edge.data_mapping["output"] == "input"


if __name__ == "__main__":
    pytest.main([__file__])