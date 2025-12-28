"""组件执行入口

这个文件是组件的执行入口，用户可以在这里定义自己的组件。

可以通过以下方式运行：
1. 本地测试: uv run -m {包名}.run
2. 平台调用: uv run -m {包名}.run --mode=platform --input-json='{"input_value": "xxx"}'

日志配置：
- 日志配置在 src/sdwk/config/default.yaml 中管理
- 通过环境变量 USER_ID 和 WORKFLOW_ID 指定工作流上下文
- 通过环境变量 SDWK_ENV 切换环境（development/production）
"""

import json
import sys

import click

from sdwk import Component, Data, Input, InputType, Output, OutputType

class {{ project_name_pascal }}(Component):
    """示例组件

    这是一个示例组件，展示如何定义输入、输出和执行逻辑。
    """

    # 组件元信息
    name = "{{ project_name }}"
    display_name = "{{ project_name }}"
    description = "Use as a template to create your own component."
    documentation = "https://docs.sdwplatform.org/components-custom-components"
    icon = "code"

    # 定义输入
    inputs = [
        Input(
            name="input_value",
            display_name="Input Value",
            description="This is a custom component Input",
            type=InputType.MESSAGE_TEXT,
            value="Hello, World!",
            tool_mode=True,
        ),
    ]

    # 定义输出
    outputs = [
        Output(
            name="output",
            display_name="Output",
            description="Component output data",
            type=OutputType.DATA,
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

        # 记录日志示例
        self.log("INFO", f"开始处理输入: {input_value}")

        # 执行业务逻辑（这里只是简单的返回输入值）
        result = f"Processed: {input_value}"

        self.log("INFO", f"处理完成，结果: {result}")

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


@click.command()
@click.option("--mode", default="test", type=click.Choice(["test", "platform"]), help="运行模式：test=本地测试, platform=平台调用")
@click.option("--input-json", default=None, help="输入参数的 JSON 字符串（平台模式）")
@click.option("--input-file-path", default=None, help="输入参数的文件路径（平台模式）")
def main(mode: str, input_json: str | None, input_file_path: str | None):
    """主函数

    支持两种运行模式：
    1. test 模式：本地测试，执行完整的测试流程
    2. platform 模式：平台调用，只执行组件并输出 JSON 结果

    日志配置通过项目配置文件管理（src/sdwk/config/default.yaml）
    工作流上下文通过环境变量 USER_ID 和 WORKFLOW_ID 传递
    """
    # 创建组件实例（配置会自动从项目配置系统加载）
    component = {{ project_name_pascal }}()

    if mode == "platform":
        # 平台调用模式：解析输入参数，执行组件，输出 JSON
        try:
            if input_file_path:
                with open(input_file_path, "r") as f:
                    input_json = f.read()
            if input_json:
                input_params = json.loads(input_json)
            else:
                input_params = {}

            # 执行组件
            result = component.execute(**input_params)

            # 输出 JSON 格式结果（平台会解析这个输出）
            output = {"value": result.value, "metadata": result.metadata}
            print(json.dumps(output, ensure_ascii=False))

        except Exception as e:
            # 输出错误信息
            error_output = {"value": None, "metadata": {"error": str(e), "error_type": type(e).__name__}}
            print(json.dumps(error_output, ensure_ascii=False))
            sys.exit(1)

    else:
        # 本地测试模式：执行完整的测试流程
        print("=" * 60)
        print("Running MyComponent...")
        print("=" * 60)

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
