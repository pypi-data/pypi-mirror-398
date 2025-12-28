# 组件系统使用指南

## 概述

这是一个简化的组件系统，用于替代 langflow 的 lfx 框架。通过这个系统，你可以定义自己的组件，并将其导出到 langflow 平台。

## 核心概念

### 1. 输入类型 (InputType)

支持以下输入类型：

- `MESSAGE_TEXT`: 单行文本输入
- `MULTILINE`: 多行文本输入
- `MULTILINE_SECRET`: 多行密文输入
- `SECRET`: 单行密文输入
- `BOOL`: 布尔值输入
- `INT`: 整数输入
- `FLOAT`: 浮点数输入
- `DROPDOWN`: 下拉选择
- `FILE`: 文件上传
- `LIST`: 列表输入
- `DICT`: 字典输入

### 2. 输入定义 (Input)

使用 `Input` 类定义组件的输入参数：

```python
Input(
    name="input_name",           # 参数名称（必填）
    display_name="显示名称",      # 显示名称（必填）
    type=InputType.MESSAGE_TEXT,  # 输入类型（必填）
    info="参数说明",              # 参数说明
    value="默认值",               # 默认值
    required=True,                # 是否必填
    tool_mode=False,              # 是否为工具模式
    options=["选项1", "选项2"],   # 可选项（用于下拉选择）
)
```

### 3. 输出定义 (Output)

使用 `Output` 类定义组件的输出：

```python
Output(
    name="output_name",          # 输出名称（必填）
    display_name="输出显示名称",  # 显示名称（必填）
    method="method_name",         # 执行方法名称（必填）
    description="输出说明",       # 输出说明
)
```

### 4. 数据模型 (Data)

使用 `Data` 类传递数据：

```python
Data(
    value="数据值",              # 数据值（必填）
    metadata={"key": "value"},  # 元数据（可选）
)
```

## 创建组件

### 基本步骤

1. 继承 `Component` 类
2. 定义组件元信息
3. 定义输入列表
4. 定义输出列表
5. 实现输出方法

### 示例

```python
from component import Component, Data, Input, InputType, Output


class MyComponent(Component):
    """我的自定义组件"""

    # 组件元信息
    display_name = "My Component"
    description = "这是我的自定义组件"
    documentation = "https://docs.example.com"
    icon = "code"
    name = "MyComponent"

    # 定义输入
    inputs = [
        Input(
            name="text_input",
            display_name="文本输入",
            type=InputType.MESSAGE_TEXT,
            info="请输入文本",
            value="Hello",
        ),
        Input(
            name="enable_feature",
            display_name="启用功能",
            type=InputType.BOOL,
            info="是否启用此功能",
            value=True,
        ),
    ]

    # 定义输出
    outputs = [
        Output(
            display_name="处理结果",
            name="output",
            method="process",
            description="处理后的结果",
        ),
    ]

    def process(self) -> Data:
        """处理逻辑"""
        # 获取输入值
        text = self.text_input
        enabled = self.enable_feature

        # 执行业务逻辑
        if enabled:
            result = f"Processed: {text}"
        else:
            result = text

        # 返回数据
        return Data(
            value=result,
            metadata={
                "input": text,
                "enabled": enabled,
            },
        )
```

## 运行组件

### 方式 1: 直接运行

```bash
python src/run.py
```

### 方式 2: 使用 uv 运行

```bash
uv run src/run.py
```

### 方式 3: 在代码中使用

```python
# 创建组件实例
component = MyComponent()

# 执行组件（使用默认值）
result = component.execute()
print(result.value)

# 执行组件（传入自定义值）
result = component.execute(
    text_input="Custom text",
    enable_feature=False
)
print(result.value)
```

## 导出到 Langflow 平台

### 获取组件信息

```python
# 获取组件字典
component_dict = component.to_dict()

# 获取 LFX 格式（用于导出到 langflow）
lfx_format = component.to_lfx_format()
```

### LFX 映射

组件系统会自动将输入类型映射到 langflow 平台的对应组件：

- `InputType.MESSAGE_TEXT` → `MessageTextInput`
- `InputType.MULTILINE` → `MultilineInput`
- `InputType.SECRET` → `SecretStrInput`
- 等等...

## 示例组件

项目中包含了多个示例组件，展示不同输入类型的使用：

### 1. TextProcessorComponent
展示文本输入和布尔输入的使用

### 2. ConfigurationComponent
展示密文输入和下拉选择的使用

### 3. CalculatorComponent
展示数值输入的使用

### 4. DataStructureComponent
展示列表和字典输入的使用

运行示例：

```bash
python src/examples.py
```

## 最佳实践

1. **命名规范**
   - 组件类名使用 PascalCase
   - 输入参数名使用 snake_case
   - 显示名称使用人类可读的格式

2. **输入验证**
   - 在处理方法中验证输入值
   - 处理可能的异常情况
   - 提供有意义的错误信息

3. **元数据**
   - 在返回的 Data 对象中包含有用的元数据
   - 记录处理过程中的关键信息
   - 便于调试和追踪

4. **文档**
   - 为组件添加详细的 docstring
   - 为输入参数添加清晰的说明
   - 提供使用示例

## 目录结构

```
src/
├── component/              # 组件系统核心
│   ├── __init__.py        # 导出核心类
│   ├── component.py       # Component 基类
│   ├── data.py            # Data 数据模型
│   ├── io.py              # Input/Output 定义
│   └── types.py           # InputType 枚举
├── run.py                 # 组件执行入口
└── examples.py            # 示例组件
```

## 常见问题

### Q: 如何添加自定义验证？

在组件的处理方法中添加验证逻辑：

```python
def process(self) -> Data:
    if not self.text_input:
        raise ValueError("text_input cannot be empty")
    # 处理逻辑...
```

### Q: 如何处理多个输出？

定义多个 Output 并实现对应的方法：

```python
outputs = [
    Output(name="output1", display_name="输出1", method="method1"),
    Output(name="output2", display_name="输出2", method="method2"),
]

def method1(self) -> Data:
    return Data(value="output1")

def method2(self) -> Data:
    return Data(value="output2")
```

### Q: 如何在本地测试组件？

在 `run.py` 的 `main()` 函数中添加测试代码：

```python
def main():
    component = MyComponent()
    result = component.execute(input_value="test")
    print(result.value)
```

## 更新日志

- 2024-01-01: 初始版本，实现基础组件系统
