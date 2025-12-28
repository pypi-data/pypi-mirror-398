"""内置组件定义

这个文件包含一些内置的示例组件，用于演示如何在工作流中使用组件。
用户可以参考这些组件创建自己的自定义组件。
"""

from sdwk import Component, Data, Input, InputType, Output, OutputType


class InputComponent(Component):
    """输入组件

    工作流的入口组件，接收外部输入数据
    """

    display_name = "Input"
    description = "接收外部输入数据"
    icon = "input"
    name = "InputNode"

    inputs = [
        Input(
            name="data",
            display_name="Input Data",
            description="输入数据",
            type=InputType.DICT,
            value={},
            required=True,
        ),
    ]

    outputs = [
        Output(
            name="output",
            display_name="Output",
            description="输入数据输出",
            type=OutputType.DATA,
        ),
    ]

    def run(self) -> Data:
        """构建输出"""
        return Data(
            value=self.data,
            metadata={
                "component": self.name,
                "type": "input",
            },
        )


class ValidationComponent(Component):
    """验证组件

    验证输入数据的有效性
    """

    display_name = "Validation"
    description = "验证输入数据的有效性"
    icon = "check"
    name = "ValidationNode"

    inputs = [
        Input(
            name="data",
            display_name="Data to Validate",
            description="需要验证的数据",
            type=InputType.DICT,
            value={},
            required=True,
        ),
        Input(
            name="validation_rules",
            display_name="Validation Rules",
            description="验证规则列表",
            type=InputType.LIST,
            value=[],
        ),
    ]

    outputs = [
        Output(
            name="output",
            display_name="Validated Data",
            description="验证后的数据",
            type=OutputType.DATA,
        ),
    ]

    def run(self) -> Data:
        """验证数据"""
        data = self.data
        rules = self.validation_rules

        # 执行验证
        validation_errors = []
        for rule in rules:
            if isinstance(rule, dict):
                field = rule.get("field")
                required = rule.get("required", False)
                field_type = rule.get("type")

                # 检查必填字段
                if required and field not in data:
                    validation_errors.append(f"Missing required field: {field}")

                # 检查类型
                if field in data and field_type:
                    value = data[field]
                    if field_type == "string" and not isinstance(value, str):
                        validation_errors.append(f"Field {field} must be string")
                    elif field_type == "int" and not isinstance(value, int):
                        validation_errors.append(f"Field {field} must be int")

        # 返回验证结果
        is_valid = len(validation_errors) == 0

        return Data(
            value=data if is_valid else {},
            metadata={
                "component": self.name,
                "valid": is_valid,
                "errors": validation_errors,
            },
        )


class CustomProcessComponent(Component):
    """自定义处理组件

    执行主要的数据处理逻辑
    """

    display_name = "Custom Process"
    description = "执行主要的数据处理逻辑"
    icon = "cpu"
    name = "CustomProcessNode"

    inputs = [
        Input(
            name="input_data",
            display_name="Input Data",
            description="输入数据",
            type=InputType.DICT,
            value={},
            required=True,
        ),
        Input(
            name="processing_mode",
            display_name="Processing Mode",
            description="处理模式",
            type=InputType.DROPDOWN,
            value="standard",
            options=["standard", "advanced", "custom"],
        ),
        Input(
            name="transform_type",
            display_name="Transform Type",
            description="转换类型",
            type=InputType.DROPDOWN,
            value="uppercase",
            options=["uppercase", "lowercase", "capitalize"],
        ),
    ]

    outputs = [
        Output(
            name="output",
            display_name="Processed Data",
            description="处理后的数据",
            type=OutputType.DATA,
        ),
    ]

    def run(self) -> Data:
        """处理数据"""
        data = self.input_data.copy() if isinstance(self.input_data, dict) else {}
        mode = self.processing_mode
        transform = self.transform_type

        # 执行处理逻辑
        if mode == "standard":
            # 标准处理：转换文本
            if "message" in data:
                message = str(data["message"])
                if transform == "uppercase":
                    data["message"] = message.upper()
                elif transform == "lowercase":
                    data["message"] = message.lower()
                elif transform == "capitalize":
                    data["message"] = message.capitalize()

        result = {
            "processed_data": data,
            "processing_mode": mode,
            "transform_type": transform,
        }

        return Data(
            value=result,
            metadata={
                "component": self.name,
                "mode": mode,
                "transform": transform,
            },
        )


class EnrichmentComponent(Component):
    """数据增强组件

    为处理后的数据添加额外信息
    """

    display_name = "Enrichment"
    description = "为处理后的数据添加额外信息"
    icon = "plus"
    name = "EnrichmentNode"

    inputs = [
        Input(
            name="base_data",
            display_name="Base Data",
            description="基础数据",
            type=InputType.DICT,
            value={},
            required=True,
        ),
        Input(
            name="enrichment_sources",
            display_name="Enrichment Sources",
            type=InputType.LIST,
            description="增强数据源",
            value=["metadata"],
        ),
    ]

    outputs = [
        Output(
            name="output",
            display_name="Enriched Data",
            description="增强后的数据",
            type=OutputType.DATA,
        ),
    ]

    def run(self) -> Data:
        """增强数据"""
        data = self.base_data.copy() if isinstance(self.base_data, dict) else {}
        sources = self.enrichment_sources

        # 添加增强信息
        enrichment = {}
        if "metadata" in sources:
            enrichment["enriched_at"] = "2024-01-01T00:00:00Z"
            enrichment["enrichment_version"] = "1.0"

        if "context" in sources:
            enrichment["context"] = {"source": "enrichment_component"}

        result = {
            **data,
            "enrichment": enrichment,
        }

        return Data(
            value=result,
            metadata={
                "component": self.name,
                "sources": sources,
            },
        )


class OutputComponent(Component):
    """输出组件

    工作流的出口组件，输出最终处理结果
    """

    display_name = "Output"
    description = "输出最终处理结果"
    icon = "output"
    name = "OutputNode"

    inputs = [
        Input(
            name="final_data",
            display_name="Final Data",
            description="最终数据",
            type=InputType.DICT,
            value={},
            required=True,
        ),
        Input(
            name="include_metadata",
            display_name="Include Metadata",
            description="是否包含元数据",
            type=InputType.BOOL,
            value=True,
        ),
    ]

    outputs = [
        Output(
            name="output",
            display_name="Output",
            description="最终输出",
            type=OutputType.DATA,
        ),
    ]

    def run(self) -> Data:
        """构建输出"""
        data = self.final_data
        include_meta = self.include_metadata

        result = {"data": data}

        if include_meta:
            result["metadata"] = {
                "component": self.name,
                "output_at": "2024-01-01T00:00:00Z",
            }

        return Data(
            value=result,
            metadata={
                "component": self.name,
                "type": "output",
            },
        )


# 组件注册表
COMPONENT_REGISTRY = {
    "InputNode": InputComponent,
    "ValidationNode": ValidationComponent,
    "CustomProcessNode": CustomProcessComponent,
    "EnrichmentNode": EnrichmentComponent,
    "OutputNode": OutputComponent,
}


def create_component(component_type: str, **kwargs) -> Component:
    """创建组件实例

    Args:
        component_type: 组件类型
        **kwargs: 组件初始化参数

    Returns:
        Component: 组件实例

    Raises:
        ValueError: 组件类型不存在
    """
    if component_type not in COMPONENT_REGISTRY:
        raise ValueError(f"Unknown component type: {component_type}")

    component_class = COMPONENT_REGISTRY[component_type]
    return component_class(**kwargs)


def get_available_components() -> list[str]:
    """获取所有可用的组件类型

    Returns:
        list[str]: 组件类型列表
    """
    return list(COMPONENT_REGISTRY.keys())
