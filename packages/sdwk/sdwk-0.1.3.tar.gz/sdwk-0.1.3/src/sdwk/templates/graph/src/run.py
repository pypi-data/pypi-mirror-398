"""组件执行入口

这个文件是组件的执行入口，用户可以在这里定义自己的组件。

可以通过以下方式运行：
1. uv run -m {包名}.run           (推荐，例如: uv run -m test_project.run)
2. python -m {包名}.run           (推荐，例如: python -m test_project.run)
3. PYTHONPATH=src python -m {包名}.run
"""

import json

from sdwk import Component, Data, Input, InputType, Output, OutputType


class {{ project_name_pascal }}(Component):
    """示例组件

    这是一个示例组件，展示如何定义输入、输出和执行逻辑。
    """

    # 组件元信息
    display_name = "{{ project_name }}"
    description = "Use as a template to create your own component."
    documentation = "https://docs.sdwplatform.org/components-custom-components"
    icon = "code"
    name = "{{ project_name }}"

    # 定义输入
    inputs = [
        Input(
            name="input_value",
            display_name="Input Value",
            type=InputType.MESSAGE_TEXT,
            info="This is a custom component Input",
            value="Hello, World!",
            tool_mode=True,
        ),
    ]

    # 定义输出
    outputs = [
        Output(
            display_name="Output",
            name="output",
            type=OutputType.DATA,
            description="Component output data",
        ),
    ]

    def run(self) -> Data:
        """执行组件核心逻辑

        这是组件的业务逻辑，你可以在这里实现自己的处理流程。

        Returns:
            Data: 输出数据
        """
        # 获取输入值
        input_value = self.input_value

        # 执行业务逻辑（这里只是简单的返回输入值）
        result = f"Processed: {input_value}"

        # 创建输出数据
        data = Data(
            value=result,
            metadata={
                "input": input_value,
                "component": self.name,
            },
        )

        # 设置状态
        self.status = data

        return data


def main():
    """主函数

    用于本地测试组件
    """
    print("=" * 60)
    print("Running MyComponent...")
    print("=" * 60)

    # 创建组件实例
    component = {{ project_name_pascal }}()

    # 打印组件信息
    print("\nComponent Information:")
    print(json.dumps(component.to_dict(), indent=2, ensure_ascii=False))

    # 执行组件
    print("\n" + "=" * 60)
    print("Executing component...")
    print("=" * 60)

    result = component.execute()

    # 打印执行结果
    print("\nExecution Result:")
    print(f"Value: {result.value}")
    print(f"Metadata: {json.dumps(result.metadata, indent=2, ensure_ascii=False)}")

    # 测试不同的输入值
    print("\n" + "=" * 60)
    print("Testing with custom input...")
    print("=" * 60)

    result2 = component.execute(input_value="Custom Input Value")

    print("\nExecution Result:")
    print(f"Value: {result2.value}")
    print(f"Metadata: {json.dumps(result2.metadata, indent=2, ensure_ascii=False)}")

    # 导出为 LFX 格式
    print("\n" + "=" * 60)
    print("LFX Format Export:")
    print("=" * 60)
    print(json.dumps(component.to_lfx_format(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
