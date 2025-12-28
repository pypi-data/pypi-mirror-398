"""
数据模型定义
"""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class InputData(BaseModel):
    """输入数据模型"""
    data: Dict[str, Any] = Field(..., description="输入数据")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")

    class Config:
        json_schema_extra = {
            "example": {
                "data": {"message": "Hello, World!"},
                "metadata": {"source": "user_input"}
            }
        }


class OutputData(BaseModel):
    """输出数据模型"""
    result: Dict[str, Any] = Field(..., description="处理结果")
    status: str = Field(default="success", description="处理状态")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="输出元数据")

    class Config:
        json_schema_extra = {
            "example": {
                "result": {"processed_message": "Hello, World! (processed)"},
                "status": "success",
                "metadata": {"processing_time": 0.1}
            }
        }


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="版本号")
    node_type: str = Field(..., description="节点类型")
    timestamp: Optional[str] = Field(default=None, description="时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "node_type": "node",
                "timestamp": "2023-12-17T10:00:00Z"
            }
        }