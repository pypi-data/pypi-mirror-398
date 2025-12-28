"""SDW Platform SDK

提供组件开发和工作流构建的核心功能
"""

from .core.component import Component, Data, Input, InputType, Output, OutputType

__version__ = "0.1.0"

__all__ = [
    "Component",
    "Data",
    "Input",
    "Output",
    "InputType",
    "OutputType",
]


def hello() -> str:
    return "Hello from platform-sdk!"
