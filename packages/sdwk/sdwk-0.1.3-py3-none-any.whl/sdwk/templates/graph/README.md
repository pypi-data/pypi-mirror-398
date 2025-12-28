# {{ project_name_title }}

{{ project_description }}

## 项目信息

- **项目类型**: Graph项目 (工作流图)
- **版本**: {{ project_version }}
- **平台地址**: {{ platform_url }}

## 什么是 Graph 项目？

Graph 项目用于创建**工作流图**，将多个组件（Component/Node）连接成完整的处理流程。

- **Node 项目** = 单个 Component（组件）
- **Graph 项目** = 多个 Component 组成的工作流

## 快速开始

### 安装依赖

```bash
uv sync
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
│   ├── nodes/             # 节点实现
│   │   ├── __init__.py
│   │   ├── adapter.py     # ComponentAdapter（将 Component 包装成节点）
│   │   ├── components.py  # 内置组件
│   │   ├── base.py        # [已弃用] 旧版 BaseNode
│   │   └── custom.py      # [已弃用] 旧版自定义节点
│   ├── main.py            # FastAPI 主入口
│   ├── graph.py           # 图执行引擎
│   ├── models.py          # 数据模型
│   ├── run.py             # 组件执行入口
│   └── examples.py        # 示例组件
├── tests/
│   └── test_graph.py      # 测试文件
├── workflow.json          # 工作流定义
├── pyproject.toml         # 项目配置
├── sdw.json              # SDW平台配置
├── COMPONENT_GUIDE.md    # 组件开发指南
└── README.md             # 项目说明
```

## 工作流定义

在 `workflow.json` 中定义你的工作流图：

```json
{
  "name": "{{ project_name }}",
  "version": "{{ project_version }}",
  "nodes": [
    {
      "id": "input",
      "type": "InputNode",
      "config": {
        "data": {}
      }
    },
    {
      "id": "process",
      "type": "CustomProcessNode",
      "config": {
        "input_data": {},
        "processing_mode": "standard",
        "transform_type": "uppercase"
      }
    },
    {
      "id": "output",
      "type": "OutputNode",
      "config": {
        "final_data": {},
        "include_metadata": true
      }
    }
  ],
  "edges": [
    {"from": "input", "to": "process"},
    {"from": "process", "to": "output"}
  ]
}
```

## 内置组件

项目包含以下内置组件（在 `src/nodes/components.py`）：

- **InputComponent** (InputNode) - 工作流入口
- **ValidationComponent** (ValidationNode) - 数据验证
- **CustomProcessComponent** (CustomProcessNode) - 自定义处理
- **EnrichmentComponent** (EnrichmentNode) - 数据增强
- **OutputComponent** (OutputNode) - 工作流出口

## 创建自定义组件

### 方法 1: 在工作流中使用

在 `src/nodes/components.py` 中添加新组件：

```python
from component import Component, Data, Input, InputType, Output


class MyCustomComponent(Component):
    display_name = "My Custom"
    description = "我的自定义组件"
    icon = "code"
    name = "MyCustomNode"

    inputs = [
        Input(
            name="input_data",
            display_name="Input Data",
            type=InputType.DICT,
            value={},
        ),
    ]

    outputs = [
        Output(
            display_name="Output",
            name="output",
            method="build_output",
        ),
    ]

    def build_output(self) -> Data:
        # 你的处理逻辑
        result = {"processed": self.input_data}
        return Data(value=result)
```

然后在 `COMPONENT_REGISTRY` 中注册：

```python
COMPONENT_REGISTRY = {
    ...
    "MyCustomNode": MyCustomComponent,
}
```

### 方法 2: 独立测试组件

在 `src/run.py` 中创建和测试单个组件：

```bash
python src/run.py
```

## 核心概念

### Component (组件)

- 所有节点都是 Component
- Component 定义了输入（inputs）、输出（outputs）和处理逻辑（methods）
- Component 可以导出为 LFX 格式供 langflow 平台使用

### ComponentAdapter (适配器)

- 将同步的 Component 包装成异步节点
- 供 GraphEngine 执行使用
- 自动处理数据转换

### GraphEngine (图执行引擎)

- 加载 workflow.json
- 构建有向无环图（DAG）
- 按拓扑排序执行节点
- 支持并行执行和错误处理

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

使用 `sdwk publish` 命令将项目发布到SDW平台。

## Graph项目特性

- **并行执行**: 支持节点的并行执行（max_parallel_nodes 配置）
- **条件分支**: 支持基于条件的流程控制（edges.condition）
- **数据映射**: 支持节点间的数据字段映射（edges.data_mapping）
- **错误处理**: 内置错误处理和重试机制
- **状态管理**: 跟踪工作流执行状态
- **异步执行**: 基于 asyncio 的高性能异步执行

## 进一步学习

- 📖 [组件开发完整指南](COMPONENT_GUIDE.md)
- 📝 查看 `src/examples.py` 了解更多示例
- 🔍 查看 `src/nodes/components.py` 了解内置组件实现
- 🌐 访问 {{ platform_url }} 了解平台文档