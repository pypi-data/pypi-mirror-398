"""SDW Platform SDK.

提供组件开发和工作流构建的核心功能
"""

from .core.component import Component, Data, Input, InputType, Output, OutputType
from .core.platform_client import PlatformAPIError, PlatformClient
from .core.project_settings import get_project_settings, settings

__version__ = "0.1.0"

__all__ = [
    "Component",
    "Data",
    "Input",
    "Output",
    "InputType",
    "OutputType",
    "settings",
    "get_project_settings",
    "PlatformClient",
    "PlatformAPIError",
]


def hello() -> str:
    return "Hello from platform-sdk!"
