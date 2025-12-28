"""
Graph项目数据模型定义
"""
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field
import time


class NodeStatus(str, Enum):
    """节点执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class NodeData(BaseModel):
    """节点数据模型"""
    data: Dict[str, Any] = Field(..., description="节点数据")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    node_id: Optional[str] = Field(default=None, description="节点ID")
    timestamp: float = Field(default_factory=time.time, description="时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "data": {"message": "Hello, World!"},
                "metadata": {"source": "input"},
                "node_id": "input",
                "timestamp": 1703664000.0
            }
        }


class NodeResult(BaseModel):
    """节点执行结果"""
    node_id: str = Field(..., description="节点ID")
    status: NodeStatus = Field(..., description="执行状态")
    data: Optional[NodeData] = Field(default=None, description="输出数据")
    error: Optional[str] = Field(default=None, description="错误信息")
    execution_time: float = Field(default=0.0, description="执行时间(秒)")
    start_time: float = Field(default_factory=time.time, description="开始时间")
    end_time: Optional[float] = Field(default=None, description="结束时间")

    class Config:
        json_schema_extra = {
            "example": {
                "node_id": "process",
                "status": "success",
                "data": {
                    "data": {"processed_message": "HELLO, WORLD!"},
                    "metadata": {"processing_type": "uppercase"}
                },
                "execution_time": 0.1,
                "start_time": 1703664000.0,
                "end_time": 1703664000.1
            }
        }


class GraphExecutionRequest(BaseModel):
    """图执行请求"""
    input_data: NodeData = Field(..., description="输入数据")
    execution_config: Optional[Dict[str, Any]] = Field(default=None, description="执行配置")
    start_node: Optional[str] = Field(default=None, description="起始节点ID")

    class Config:
        json_schema_extra = {
            "example": {
                "input_data": {
                    "data": {"message": "Hello, World!"},
                    "metadata": {"source": "api"}
                },
                "execution_config": {
                    "max_parallel": 2,
                    "timeout": 60
                }
            }
        }


class GraphExecutionResult(BaseModel):
    """图执行结果"""
    execution_id: str = Field(..., description="执行ID")
    status: NodeStatus = Field(..., description="整体执行状态")
    node_results: List[NodeResult] = Field(default_factory=list, description="节点执行结果")
    final_output: Optional[NodeData] = Field(default=None, description="最终输出")
    total_execution_time: float = Field(default=0.0, description="总执行时间")
    error_summary: Optional[str] = Field(default=None, description="错误摘要")

    class Config:
        json_schema_extra = {
            "example": {
                "execution_id": "exec_123456",
                "status": "success",
                "node_results": [],
                "final_output": {
                    "data": {"result": "Final processed data"},
                    "metadata": {"execution_id": "exec_123456"}
                },
                "total_execution_time": 1.5
            }
        }


class NodeConfig(BaseModel):
    """节点配置"""
    id: str = Field(..., description="节点ID")
    type: str = Field(..., description="节点类型")
    name: Optional[str] = Field(default=None, description="节点名称")
    description: Optional[str] = Field(default=None, description="节点描述")
    config: Dict[str, Any] = Field(default_factory=dict, description="节点配置参数")
    position: Optional[Dict[str, float]] = Field(default=None, description="节点位置")


class EdgeConfig(BaseModel):
    """边配置"""
    id: str = Field(..., description="边ID")
    from_node: str = Field(..., alias="from", description="源节点ID")
    to_node: str = Field(..., alias="to", description="目标节点ID")
    condition: Optional[Dict[str, Any]] = Field(default=None, description="执行条件")
    data_mapping: Optional[Dict[str, str]] = Field(default=None, description="数据映射")


class WorkflowConfig(BaseModel):
    """工作流配置"""
    name: str = Field(..., description="工作流名称")
    version: str = Field(..., description="版本")
    description: Optional[str] = Field(default=None, description="描述")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    config: Dict[str, Any] = Field(default_factory=dict, description="全局配置")
    nodes: List[NodeConfig] = Field(..., description="节点配置列表")
    edges: List[EdgeConfig] = Field(..., description="边配置列表")
    error_handling: Optional[Dict[str, Any]] = Field(default=None, description="错误处理配置")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="版本号")
    project_type: str = Field(..., description="项目类型")
    workflow_loaded: bool = Field(..., description="工作流是否已加载")
    node_count: int = Field(..., description="节点数量")
    timestamp: Optional[str] = Field(default=None, description="时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "project_type": "graph",
                "workflow_loaded": True,
                "node_count": 5,
                "timestamp": "2023-12-17T10:00:00Z"
            }
        }