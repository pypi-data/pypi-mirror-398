# SDWK - SDW Platform SDK

SDWK 是 SDW Platform 的官方 SDK，为开发者提供了一套完整的工具链，用于创建、开发和发布 SDW 平台应用。

## 概述

SDW Platform 是一个工作流低代码平台，用户可以通过拖拽内置节点组合成工作流图。SDWK SDK 允许开发者：

- 创建自定义节点扩展平台功能
- 开发完整的工作流图应用
- 使用标准化的开发生命周期工具

## 项目类型

SDWK 支持两种项目类型：

### Node 项目
单节点处理项目，用于创建可复用的处理单元，具有：
- 确定的输入和输出接口
- 独立的业务逻辑处理
- 标准化的数据模型

### Graph 项目
工作流图项目，用于创建包含多个节点及其关系的复杂工作流，支持：
- 有向无环图结构
- 节点间数据流转
- 并行执行和错误处理

## 快速开始

### 安装

```bash
# 使用 uv 安装
uv add sdwk

# 或使用 pip 安装
pip install sdwk
```

### 创建项目

```bash
# 交互式创建项目
sdwk create

# 或指定参数创建
sdwk create --name my-project --type node --description "我的第一个节点"
```

### 开发和调试

```bash
# 进入项目目录
cd my-project

# 启动开发模式
sdwk dev

# 检查项目
sdwk check

# 发布项目
sdwk publish
```

## 文档

详细文档请参考 [docs](./docs/) 目录：

- [开发者指南](./docs/developer/) - 快速开始、API 文档、使用指南
- [项目规范](./docs/specifications/) - 包结构、配置文件规范
- [平台集成](./docs/platform/) - 与 SDW Platform 对接说明
- [架构设计](./docs/architecture/) - SDK 架构和设计原理

## 系统要求

- Python >= 3.10
- uv (推荐) 或 pip

## 许可证

本项目采用 MIT 许可证。

## 开发指南

如果您想参与 SDWK SDK 的开发，请按照以下步骤设置开发环境：

### 获取源代码

```bash
# 克隆项目代码
git clone https://172.16.0.120/astri/RI-SDW-III/SDW/Platform/Platform-SDK.git sdwk

# 进入项目目录
cd sdwk

# 切换到开发分支
git checkout develop
```

### 设置开发环境

```bash
# 安装依赖
uv sync

# 安装开发钩子（代码质量检查、格式化等）
uv run prek install
```

### 开发工作流

1. **创建功能分支**：
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **进行开发**：
   - 编写代码
   - 添加测试
   - 更新文档

3. **代码质量检查**：
   ```bash
   # 运行代码检查
   uv run ruff check

   # 运行格式化
   uv run ruff format

   # 运行类型检查
   uv run ty
   ```

4. **提交代码**：
   ```bash
   git add .
   git commit -m "feat: 添加新功能描述"
   ```

5. **推送并创建 Pull Request**：
   ```bash
   git push origin feature/your-feature-name
   ```

### 开发规范

- 遵循 [项目规范](./docs/specifications/) 中的代码规范
- 确保所有测试通过
- 添加适当的文档和注释
- 使用语义化的提交消息

## 贡献

欢迎提交 Issue 和 Pull Request 来改进 SDWK。

## 联系方式

- 作者：徐侨 (xu.qiao@kotei.com.cn)
- 项目主页：[GitHub Repository]