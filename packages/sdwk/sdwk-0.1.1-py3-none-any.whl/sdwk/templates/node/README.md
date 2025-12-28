# {{ project_name_title }}

{{ project_description }}

## 项目信息

- **项目类型**: Node项目（单个组件/节点）
- **版本**: {{ project_version }}
- **平台地址**: {{ platform_url }}

## 什么是 Node 项目？

Node 项目用于创建**单个组件**（Component），这个组件可以：
- 独立运行和测试
- 导出到 langflow 平台使用
- 在 Graph 工作流中作为节点使用

一个 Component = 一个 Node

## 快速开始

### 安装依赖

```bash
uv sync
```

### 本地运行组件

```bash
# 方式 1: 直接运行
python src/run.py

# 方式 2: 使用 uv
uv run src/run.py

# 方式 3: 运行示例
python src/examples.py
```

### 开发模式运行

```bash
sdwk dev
```

### 检查代码质量

```bash
sdwk check
```

### 发布到平台

```bash
sdwk publish
```

## 项目结构

```
{{ project_name_kebab }}/
├── src/
│   ├── component/          # 组件系统核心
│   │   ├── __init__.py    # 导出核心类
│   │   ├── component.py   # Component 基类
│   │   ├── data.py        # Data 数据模型
│   │   ├── io.py          # Input/Output 定义
│   │   └── types.py       # InputType 枚举
│   ├── run.py             # 组件执行入口（主文件）
│   ├── examples.py        # 示例组件
│   ├── main.py            # FastAPI 服务入口
│   ├── node.py            # 旧版节点逻辑（可选）
│   └── models.py          # 数据模型
├── tests/
│   └── test_node.py       # 测试文件
├── pyproject.toml         # 项目配置
├── sdw.json              # SDW平台配置
├── COMPONENT_GUIDE.md    # 组件开发指南
└── README.md             # 项目说明
```

## 开发指南

### 1. 定义组件

在 `src/run.py` 中定义你的组件：

```python
from component import Component, Data, Input, InputType, Output


class MyComponent(Component):
    """我的自定义组件"""

    # 组件元信息
    display_name = "My Component"
    description = "这是我的自定义组件"
    icon = "code"
    name = "MyComponent"

    # 定义输入
    inputs = [
        Input(
            name="input_value",
            display_name="Input Value",
            type=InputType.MESSAGE_TEXT,
            info="请输入值",
            value="Hello",
        ),
    ]

    # 定义输出
    outputs = [
        Output(
            display_name="Output",
            name="output",
            method="build_output",
        ),
    ]

    def build_output(self) -> Data:
        """执行组件逻辑"""
        result = f"Processed: {self.input_value}"
        return Data(value=result)
```

### 2. 本地测试

在 `src/run.py` 的 `main()` 函数中测试组件：

```python
def main():
    component = MyComponent()
    result = component.execute()
    print(result.value)
```

### 3. 导出到 Langflow 平台

```python
# 获取 LFX 格式
lfx_format = component.to_lfx_format()
```

### 4. 支持的输入类型

- `MESSAGE_TEXT`: 单行文本
- `MULTILINE`: 多行文本
- `SECRET`: 密文输入
- `BOOL`: 布尔值
- `INT`: 整数
- `FLOAT`: 浮点数
- `DROPDOWN`: 下拉选择
- `FILE`: 文件上传
- `LIST`: 列表
- `DICT`: 字典

详细使用方法请参考 [COMPONENT_GUIDE.md](COMPONENT_GUIDE.md)

## 示例

项目中包含多个示例组件：

```bash
python src/examples.py
```

查看示例组件：
- TextProcessorComponent - 文本处理
- ConfigurationComponent - 配置管理
- CalculatorComponent - 计算器
- DataStructureComponent - 数据结构

## 测试

运行测试：

```bash
pytest
```

## 代码格式化

```bash
ruff check --fix
ruff format
```

## 部署

使用 `sdwk publish` 命令将组件发布到 SDW 平台。

## 进一步学习

- 📖 [组件开发完整指南](COMPONENT_GUIDE.md)
- 📝 查看 `src/examples.py` 了解更多示例
- 🌐 访问 {{ platform_url }} 了解平台文档