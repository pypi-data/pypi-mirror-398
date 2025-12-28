"""示例组件集合

这个文件包含多个示例组件,展示如何使用不同的输入类型。
"""

import json

from sdwk import Component, Data, Input, InputType, Output, OutputType


class TextProcessorComponent(Component):
    """文本处理组件

    展示如何使用多种文本输入类型
    """

    display_name = "Text Processor"
    description = "Process text with various input types"
    icon = "text"
    name = "TextProcessor"

    inputs = [
        Input(
            name="single_line_text",
            display_name="Single Line Text",
            type=InputType.MESSAGE_TEXT,
            info="Enter a single line of text",
            value="Hello",
        ),
        Input(
            name="multi_line_text",
            display_name="Multi Line Text",
            type=InputType.MULTILINE,
            info="Enter multiple lines of text",
            value="Line 1\nLine 2\nLine 3",
        ),
        Input(
            name="uppercase",
            display_name="Convert to Uppercase",
            type=InputType.BOOL,
            info="Convert text to uppercase",
            value=True,
        ),
    ]

    outputs = [
        Output(
            display_name="Processed Text",
            name="output",
            type=OutputType.DATA,
            description="Processed text output",
        ),
    ]

    def run(self) -> Data:
        """处理文本"""
        # 合并文本
        combined_text = f"{self.single_line_text}\n{self.multi_line_text}"

        # 根据选项转换大小写
        if self.uppercase:
            result = combined_text.upper()
        else:
            result = combined_text.lower()

        return Data(
            value=result,
            metadata={
                "original_single": self.single_line_text,
                "original_multi": self.multi_line_text,
                "uppercase": self.uppercase,
            },
        )


class ConfigurationComponent(Component):
    """配置组件

    展示如何使用密文输入和下拉选择
    """

    display_name = "Configuration"
    description = "Component with secret and dropdown inputs"
    icon = "settings"
    name = "Configuration"

    inputs = [
        Input(
            name="api_key",
            display_name="API Key",
            type=InputType.SECRET,
            info="Enter your API key",
            value="",
            required=True,
        ),
        Input(
            name="environment",
            display_name="Environment",
            type=InputType.DROPDOWN,
            info="Select the environment",
            value="development",
            options=["development", "staging", "production"],
        ),
        Input(
            name="config_text",
            display_name="Configuration",
            type=InputType.MULTILINE_SECRET,
            info="Enter sensitive configuration",
            value="",
        ),
    ]

    outputs = [
        Output(
            display_name="Config Output",
            name="output",
            type=OutputType.DATA,
            description="Configuration data",
        ),
    ]

    def run(self) -> Data:
        """构建配置"""
        # 注意：在实际使用中，不应该在输出中暴露密文
        config = {
            "environment": self.environment,
            "api_key_length": len(self.api_key) if self.api_key else 0,
            "has_config": bool(self.config_text),
        }

        return Data(
            value=config,
            metadata={
                "environment": self.environment,
                "timestamp": "2024-01-01T00:00:00Z",
            },
        )


class CalculatorComponent(Component):
    """计算器组件

    展示如何使用数值输入
    """

    display_name = "Calculator"
    description = "Perform calculations with numeric inputs"
    icon = "calculator"
    name = "Calculator"

    inputs = [
        Input(
            name="number1",
            display_name="Number 1",
            type=InputType.INT,
            info="Enter the first number",
            value=10,
        ),
        Input(
            name="number2",
            display_name="Number 2",
            type=InputType.INT,
            info="Enter the second number",
            value=5,
        ),
        Input(
            name="multiplier",
            display_name="Multiplier",
            type=InputType.FLOAT,
            info="Enter a multiplier",
            value=1.5,
        ),
        Input(
            name="operation",
            display_name="Operation",
            type=InputType.DROPDOWN,
            info="Select the operation",
            value="add",
            options=["add", "subtract", "multiply", "divide"],
        ),
    ]

    outputs = [
        Output(
            display_name="Result",
            name="output",
            type=OutputType.DATA,
            description="Calculation result",
        ),
    ]

    def run(self) -> Data:
        """执行计算"""
        # 执行基本运算
        if self.operation == "add":
            result = self.number1 + self.number2
        elif self.operation == "subtract":
            result = self.number1 - self.number2
        elif self.operation == "multiply":
            result = self.number1 * self.number2
        elif self.operation == "divide":
            result = self.number1 / self.number2 if self.number2 != 0 else 0
        else:
            result = 0

        # 应用乘数
        final_result = result * self.multiplier

        return Data(
            value=final_result,
            metadata={
                "number1": self.number1,
                "number2": self.number2,
                "operation": self.operation,
                "multiplier": self.multiplier,
                "intermediate_result": result,
            },
        )


class DataStructureComponent(Component):
    """数据结构组件

    展示如何使用列表和字典输入
    """

    display_name = "Data Structure"
    description = "Work with lists and dictionaries"
    icon = "database"
    name = "DataStructure"

    inputs = [
        Input(
            name="items",
            display_name="Items List",
            type=InputType.LIST,
            info="Enter a list of items",
            value=["item1", "item2", "item3"],
        ),
        Input(
            name="metadata",
            display_name="Metadata",
            type=InputType.DICT,
            info="Enter metadata as a dictionary",
            value={"key1": "value1", "key2": "value2"},
        ),
        Input(
            name="filter_empty",
            display_name="Filter Empty",
            type=InputType.BOOL,
            info="Filter out empty items",
            value=True,
        ),
    ]

    outputs = [
        Output(
            display_name="Processed Data",
            name="output",
            type=OutputType.DATA,
            description="Processed data structure",
        ),
    ]

    def run(self) -> Data:
        """处理数据结构"""
        # 处理列表
        items = self.items if isinstance(self.items, list) else []
        if self.filter_empty:
            items = [item for item in items if item]

        # 处理字典
        metadata = self.metadata if isinstance(self.metadata, dict) else {}

        # 组合结果
        result = {
            "items": items,
            "count": len(items),
            "metadata": metadata,
        }

        return Data(
            value=result,
            metadata={
                "original_count": len(self.items) if isinstance(self.items, list) else 0,
                "filtered": self.filter_empty,
            },
        )


def demo_all_components():
    """演示所有组件"""
    import json

    components = [
        TextProcessorComponent(),
        ConfigurationComponent(),
        CalculatorComponent(),
        DataStructureComponent(),
    ]

    for component in components:
        print("\n" + "=" * 60)
        print(f"Component: {component.display_name}")
        print("=" * 60)

        # 打印组件信息
        print("\nComponent Info:")
        print(json.dumps(component.to_dict(), indent=2, ensure_ascii=False))

        # 执行组件
        print("\nExecuting...")
        try:
            result = component.execute()
            print(f"\nResult: {result.value}")
            print(f"Metadata: {json.dumps(result.metadata, indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    demo_all_components()
