"""
节点模块 - 包含所有节点类型的实现

从 BaseNode 迁移到 Component 系统。
现在所有节点都是 Component，通过 ComponentAdapter 包装供 GraphEngine 使用。
"""

from .adapter import ComponentAdapter
from .components import (
    COMPONENT_REGISTRY,
    InputComponent,
    OutputComponent,
    ValidationComponent,
    CustomProcessComponent,
    EnrichmentComponent,
    create_component,
    get_available_components,
)

# 为了兼容性，保留旧的导入（但实际使用 Component）
# 这些 import 语句会在后续版本中移除
try:
    from .base import BaseNode
    from .custom import (
        InputNode,
        OutputNode,
        ValidationNode,
        CustomProcessNode as OldCustomProcessNode,
        EnrichmentNode,
    )

    _has_old_nodes = True
except ImportError:
    _has_old_nodes = False
    BaseNode = None


# 节点注册表 - 使用 Component 系统
NODE_REGISTRY = COMPONENT_REGISTRY.copy()


def create_node(node_type: str, node_config: dict) -> ComponentAdapter:
    """
    根据节点类型创建节点实例

    Args:
        node_type: 节点类型名称
        node_config: 节点配置

    Returns:
        ComponentAdapter: 节点适配器实例

    Raises:
        ValueError: 当节点类型不存在时
    """
    if node_type not in NODE_REGISTRY:
        raise ValueError(f"Unknown node type: {node_type}")

    # 创建 Component 实例
    component_class = NODE_REGISTRY[node_type]

    # 从 config 中提取初始化参数
    config = node_config.get("config", {})
    component = component_class(**config)

    # 使用适配器包装
    adapter = ComponentAdapter(component, node_config)

    return adapter


def get_available_node_types() -> list[str]:
    """获取所有可用的节点类型"""
    return list(NODE_REGISTRY.keys())


__all__ = [
    "ComponentAdapter",
    "InputComponent",
    "OutputComponent",
    "ValidationComponent",
    "CustomProcessComponent",
    "EnrichmentComponent",
    "COMPONENT_REGISTRY",
    "NODE_REGISTRY",
    "create_node",
    "create_component",
    "get_available_node_types",
    "get_available_components",
]

# 向后兼容性导出（如果旧节点还存在）
if _has_old_nodes:
    __all__.extend([
        "BaseNode",
        "InputNode",
        "OutputNode",
        "ValidationNode",
        "EnrichmentNode",
    ])