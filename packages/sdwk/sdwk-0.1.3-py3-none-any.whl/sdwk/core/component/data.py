"""数据模型定义."""

from typing import Any

from pydantic import BaseModel, Field


class Data(BaseModel):
    """数据模型.

    用于在组件之间传递数据
    """

    value: Any = Field(..., description="数据值")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"Data(value={self.value!r}, metadata={self.metadata!r})"
