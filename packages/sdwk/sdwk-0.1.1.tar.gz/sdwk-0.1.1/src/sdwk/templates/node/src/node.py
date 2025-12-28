"""
{{ project_name_title }} - 节点处理逻辑
在这里实现你的核心业务逻辑
"""
import asyncio
import time
from typing import Dict, Any

from .models import InputData, OutputData


async def process(input_data: InputData) -> OutputData:
    """
    处理输入数据并返回结果

    Args:
        input_data: 输入数据

    Returns:
        OutputData: 处理后的输出数据
    """
    start_time = time.time()

    # 获取输入数据
    data = input_data.data
    metadata = input_data.metadata or {}

    # TODO: 在这里实现你的处理逻辑
    # 这是一个示例实现，你可以根据需要修改

    # 示例：简单的文本处理
    if "message" in data:
        processed_message = f"{data['message']} (processed by {{ project_name_title }})"
        result = {
            "processed_message": processed_message,
            "original_message": data["message"]
        }
    else:
        # 默认处理：返回输入数据的副本
        result = {"processed_data": data}

    # 计算处理时间
    processing_time = time.time() - start_time

    # 构建输出元数据
    output_metadata = {
        "processing_time": processing_time,
        "node_name": "{{ project_name }}",
        "node_version": "{{ project_version }}",
        **metadata  # 保留输入元数据
    }

    return OutputData(
        result=result,
        status="success",
        metadata=output_metadata
    )


async def validate_input(input_data: InputData) -> bool:
    """
    验证输入数据的有效性

    Args:
        input_data: 输入数据

    Returns:
        bool: 数据是否有效
    """
    # TODO: 实现你的输入验证逻辑

    # 基本验证：检查数据是否为空
    if not input_data.data:
        return False

    # 你可以在这里添加更多的验证规则
    # 例如：检查必需字段、数据类型、值范围等

    return True


async def preprocess(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    预处理数据

    Args:
        data: 原始数据

    Returns:
        Dict[str, Any]: 预处理后的数据
    """
    # TODO: 实现你的预处理逻辑

    # 示例：数据清理和标准化
    processed_data = {}

    for key, value in data.items():
        # 示例：将字符串转换为小写
        if isinstance(value, str):
            processed_data[key] = value.strip().lower()
        else:
            processed_data[key] = value

    return processed_data


async def postprocess(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    后处理结果

    Args:
        result: 处理结果

    Returns:
        Dict[str, Any]: 后处理后的结果
    """
    # TODO: 实现你的后处理逻辑

    # 示例：添加时间戳
    result["timestamp"] = time.time()

    return result