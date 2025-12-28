"""输入输出定义."""

from typing import Any

from pydantic import BaseModel, Field

from .types import InputType, OutputType


class Input(BaseModel):
    """输入定义.

    用于定义组件的输入参数
    """

    name: str = Field(..., description="输入参数名称")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(default="", description="输入说明")
    type: InputType = Field(..., description="输入类型")
    value: Any = Field(default=None, description="默认值")
    required: bool = Field(default=True, description="是否必填")
    tool_mode: bool = Field(default=False, description="是否为工具模式")
    options: list[str] | None = Field(default=None, description="可选项（用于下拉选择）")

    class Config:
        use_enum_values = True


class Output(BaseModel):
    """输出定义.

    用于定义组件的输出
    """

    name: str = Field(..., description="输出名称")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(default="", description="输出说明")
    type: OutputType = Field(default=OutputType.DATA, description="输出类型")

    class Config:
        use_enum_values = True
