"""输入输出类型定义."""

from enum import Enum


class InputType(str, Enum):
    """输入类型枚举.

    这些类型会映射到 langflow 平台的对应输入组件
    """

    # 文本输入
    MESSAGE_TEXT = "MessageTextInput"  # 单行文本输入
    MULTILINE = "MultilineInput"  # 多行文本输入
    MULTILINE_SECRET = "MultilineSecretInput"  # 多行密文输入

    # 密文输入
    SECRET = "SecretStrInput"  # 单行密文输入

    # 布尔输入
    BOOL = "BoolInput"  # 布尔值输入

    # 数值输入
    INT = "IntInput"  # 整数输入
    FLOAT = "FloatInput"  # 浮点数输入

    # 选择输入
    DROPDOWN = "DropdownInput"  # 下拉选择

    # 文件输入
    FILE = "FileInput"  # 文件上传

    # 列表输入
    LIST = "ListInput"  # 列表输入

    # 字典输入
    DICT = "DictInput"  # 字典输入


class OutputType(str, Enum):
    """输出类型枚举.

    定义组件的输出数据类型
    """

    # 基础类型
    TEXT = "Text"  # 文本输出
    DATA = "Data"  # 通用数据输出
    JSON = "JSON"  # JSON 格式输出

    # 结构化类型
    DICT = "Dict"  # 字典输出
    LIST = "List"  # 列表输出

    # 特殊类型
    MESSAGE = "Message"  # 消息输出
    DOCUMENT = "Document"  # 文档输出
    ANY = "Any"  # 任意类型


# LFX 映射表（用于导出到 langflow 平台）
LFX_INPUT_MAPPING = {
    InputType.MESSAGE_TEXT: "MessageTextInput",
    InputType.MULTILINE: "MultilineInput",
    InputType.MULTILINE_SECRET: "MultilineSecretInput",
    InputType.SECRET: "SecretStrInput",
    InputType.BOOL: "BoolInput",
    InputType.INT: "IntInput",
    InputType.FLOAT: "FloatInput",
    InputType.DROPDOWN: "DropdownInput",
    InputType.FILE: "FileInput",
    InputType.LIST: "ListInput",
    InputType.DICT: "DictInput",
}

LFX_OUTPUT_MAPPING = {
    OutputType.TEXT: "Text",
    OutputType.DATA: "Data",
    OutputType.JSON: "JSON",
    OutputType.DICT: "Dict",
    OutputType.LIST: "List",
    OutputType.MESSAGE: "Message",
    OutputType.DOCUMENT: "Document",
    OutputType.ANY: "Any",
}
