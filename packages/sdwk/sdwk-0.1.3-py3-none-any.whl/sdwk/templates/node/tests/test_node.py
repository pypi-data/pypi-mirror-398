"""
{{ project_name_title }} 测试文件
"""
import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models import InputData, OutputData
from src.node import process, validate_input, preprocess, postprocess


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
        assert data["node_type"] == "{{ project_type }}"

    def test_root_endpoint(self):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["version"] == "{{ project_version }}"

    def test_process_endpoint(self):
        """测试处理端点"""
        input_data = {
            "data": {"message": "Hello, World!"},
            "metadata": {"source": "test"}
        }
        response = client.post("/process", json=input_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "result" in data
        assert "metadata" in data

    def test_process_endpoint_invalid_data(self):
        """测试处理端点 - 无效数据"""
        input_data = {}
        response = client.post("/process", json=input_data)
        # 根据你的验证逻辑，这可能返回400或500
        assert response.status_code in [400, 422, 500]


class TestNodeLogic:
    """节点处理逻辑测试"""

    @pytest.mark.asyncio
    async def test_process_with_message(self):
        """测试处理包含消息的数据"""
        input_data = InputData(
            data={"message": "Hello, World!"},
            metadata={"source": "test"}
        )
        result = await process(input_data)

        assert isinstance(result, OutputData)
        assert result.status == "success"
        assert "processed_message" in result.result
        assert result.result["processed_message"] == "Hello, World! (processed by {{ project_name }})"
        assert result.metadata["processing_time"] >= 0

    @pytest.mark.asyncio
    async def test_process_without_message(self):
        """测试处理不包含消息的数据"""
        input_data = InputData(
            data={"value": 42, "type": "number"},
            metadata={"source": "test"}
        )
        result = await process(input_data)

        assert isinstance(result, OutputData)
        assert result.status == "success"
        assert "processed_data" in result.result
        assert result.result["processed_data"]["value"] == 42

    @pytest.mark.asyncio
    async def test_validate_input_valid(self):
        """测试输入验证 - 有效数据"""
        input_data = InputData(
            data={"message": "Hello"},
            metadata={"source": "test"}
        )
        is_valid = await validate_input(input_data)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_input_empty(self):
        """测试输入验证 - 空数据"""
        input_data = InputData(data={})
        is_valid = await validate_input(input_data)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_preprocess(self):
        """测试预处理"""
        data = {
            "message": "  Hello World  ",
            "value": 42,
            "flag": True
        }
        processed = await preprocess(data)

        assert processed["message"] == "hello world"
        assert processed["value"] == 42
        assert processed["flag"] is True

    @pytest.mark.asyncio
    async def test_postprocess(self):
        """测试后处理"""
        result = {"message": "processed"}
        processed = await postprocess(result)

        assert "timestamp" in processed
        assert processed["message"] == "processed"
        assert isinstance(processed["timestamp"], float)


class TestModels:
    """数据模型测试"""

    def test_input_data_creation(self):
        """测试输入数据模型创建"""
        data = {"message": "Hello"}
        metadata = {"source": "test"}

        input_data = InputData(data=data, metadata=metadata)
        assert input_data.data == data
        assert input_data.metadata == metadata

    def test_input_data_without_metadata(self):
        """测试输入数据模型创建 - 无元数据"""
        data = {"message": "Hello"}

        input_data = InputData(data=data)
        assert input_data.data == data
        assert input_data.metadata is None

    def test_output_data_creation(self):
        """测试输出数据模型创建"""
        result = {"processed": True}
        metadata = {"time": 0.1}

        output_data = OutputData(result=result, metadata=metadata)
        assert output_data.result == result
        assert output_data.status == "success"  # 默认值
        assert output_data.metadata == metadata

    def test_output_data_custom_status(self):
        """测试输出数据模型创建 - 自定义状态"""
        result = {"error": "Something went wrong"}

        output_data = OutputData(result=result, status="error")
        assert output_data.result == result
        assert output_data.status == "error"


if __name__ == "__main__":
    pytest.main([__file__])