"""
{{ project_name_title }} - SDW Graph项目主入口
{{ project_description }}
"""
import asyncio
import logging
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .graph import GraphEngine
from .models import (
    GraphExecutionRequest, GraphExecutionResult, HealthResponse,
    NodeData, WorkflowConfig
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="{{ project_name_title }}",
    description="{{ project_description }}",
    version="{{ project_version }}"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局图执行引擎
graph_engine: Optional[GraphEngine] = None


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    global graph_engine

    # 查找工作流文件
    workflow_path = Path("workflow.json")
    if not workflow_path.exists():
        workflow_path = Path("src/workflow.json")

    if workflow_path.exists():
        try:
            graph_engine = GraphEngine(workflow_path)
            logger.info(f"Workflow loaded successfully: {workflow_path}")
        except Exception as e:
            logger.error(f"Failed to load workflow: {e}")
            graph_engine = None
    else:
        logger.warning("No workflow.json found")
        graph_engine = None


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    workflow_loaded = graph_engine is not None
    node_count = 0

    if graph_engine and graph_engine.workflow_config:
        node_count = len(graph_engine.workflow_config.nodes)

    return HealthResponse(
        status="healthy",
        version="{{ project_version }}",
        project_type="{{ project_type }}",
        workflow_loaded=workflow_loaded,
        node_count=node_count
    )


@app.post("/execute", response_model=GraphExecutionResult)
async def execute_workflow(request: GraphExecutionRequest):
    """执行工作流图"""
    if not graph_engine:
        raise HTTPException(
            status_code=500,
            detail="Graph engine not initialized. Check workflow.json file."
        )

    try:
        logger.info(f"Executing workflow with input: {request.input_data.model_dump()}")
        result = await graph_engine.execute(request)
        logger.info(f"Workflow execution completed: {result.status}")
        return result
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflow/info")
async def get_workflow_info():
    """获取工作流信息"""
    if not graph_engine:
        raise HTTPException(
            status_code=500,
            detail="Graph engine not initialized"
        )

    return graph_engine.get_workflow_info()


@app.get("/workflow/config", response_model=WorkflowConfig)
async def get_workflow_config():
    """获取工作流配置"""
    if not graph_engine or not graph_engine.workflow_config:
        raise HTTPException(
            status_code=500,
            detail="Workflow config not available"
        )

    return graph_engine.workflow_config


@app.post("/workflow/validate")
async def validate_workflow_input(input_data: NodeData):
    """验证工作流输入数据"""
    if not graph_engine:
        raise HTTPException(
            status_code=500,
            detail="Graph engine not initialized"
        )

    try:
        # 这里可以添加输入数据验证逻辑
        # 例如：检查数据格式、必需字段等

        return {
            "valid": True,
            "message": "Input data is valid",
            "input_data": input_data.model_dump()
        }
    except Exception as e:
        return {
            "valid": False,
            "message": str(e),
            "input_data": input_data.model_dump()
        }


@app.get("/nodes/types")
async def get_available_node_types():
    """获取可用的节点类型"""
    from .nodes import get_available_node_types

    return {
        "node_types": get_available_node_types(),
        "count": len(get_available_node_types())
    }


@app.get("/")
async def root():
    """根端点"""
    workflow_status = "loaded" if graph_engine else "not_loaded"

    return {
        "message": "{{ project_name_title }} Graph Server is running",
        "version": "{{ project_version }}",
        "project_type": "{{ project_type }}",
        "workflow_status": workflow_status,
        "endpoints": {
            "health": "/health",
            "execute": "/execute",
            "workflow_info": "/workflow/info",
            "workflow_config": "/workflow/config",
            "validate_input": "/workflow/validate",
            "node_types": "/nodes/types",
            "docs": "/docs"
        }
    }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="{{ project_name_title }} Graph Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")
    parser.add_argument("--workflow", help="Path to workflow.json file")

    args = parser.parse_args()

    # 如果指定了工作流文件，设置环境变量或全局变量
    if args.workflow:
        workflow_path = Path(args.workflow)
        if not workflow_path.exists():
            logger.error(f"Workflow file not found: {workflow_path}")
            return

        # 这里可以设置全局变量或环境变量来传递工作流路径
        import os
        os.environ["WORKFLOW_PATH"] = str(workflow_path)

    logger.info(f"Starting {{ project_name_title }} Graph Server on {args.host}:{args.port}")

    uvicorn.run(
        "{{ project_name_snake }}.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )


if __name__ == "__main__":
    main()