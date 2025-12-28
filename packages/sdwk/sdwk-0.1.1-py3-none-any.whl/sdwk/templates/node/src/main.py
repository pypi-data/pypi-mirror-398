"""
{{ project_name_title }} - SDW Node项目主入口
{{ project_description }}
"""
import asyncio
import logging
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .node import process
from .models import InputData, OutputData, HealthResponse

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


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    return HealthResponse(
        status="healthy",
        version="{{ project_version }}",
        node_type="{{ project_type }}"
    )


@app.post("/process", response_model=OutputData)
async def process_data(input_data: InputData):
    """处理数据的主要端点"""
    try:
        logger.info(f"Processing data: {input_data.model_dump()}")
        result = await process(input_data)
        logger.info(f"Processing completed: {result.model_dump()}")
        return result
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "{{ project_name_title }} is running",
        "version": "{{ project_version }}",
        "docs": "/docs"
    }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="{{ project_name_title }}")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")

    args = parser.parse_args()

    logger.info(f"Starting {{ project_name_title }} on {args.host}:{args.port}")

    uvicorn.run(
        "{{ project_name_snake }}.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )


if __name__ == "__main__":
    main()