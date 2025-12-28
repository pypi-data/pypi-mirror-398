"""Build command for converting SDK code to platform format."""

import ast
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel

from sdwk.core.project_config import ProjectConfig

console = Console()


@click.command()
@click.option("--project-dir", default=".", help="项目目录路径")
@click.option("--output", default=None, help="输出文件路径 (默认: src/run_flow.py)")
def build(project_dir: str, output: str | None):
    """构建项目，将run.py转换为langflow平台格式."""
    project_path = Path(project_dir).resolve()

    console.print(Panel.fit(f"[bold cyan]SDW Project Builder[/bold cyan]\n项目路径: {project_path}", border_style="cyan"))

    # 验证项目配置
    try:
        config = ProjectConfig.from_file(project_path / "sdw.json")
        console.print(f"[dim]项目名称:[/dim] {config.name}")
        console.print(f"[dim]项目类型:[/dim] {config.type}")
    except Exception as e:
        console.print(f"[red]✗[/red] 加载项目配置失败: {e}")
        raise click.ClickException("配置文件错误")

    # 仅支持node类型项目
    if config.type != "node":
        console.print("[yellow]警告:[/yellow] build命令目前仅支持node类型项目")
        return

    # 查找run.py文件
    run_py_path = project_path / "src" / f"{config.name.replace('-', '_')}" / "run.py"
    if not run_py_path.exists():
        # 尝试其他可能的路径
        alt_paths = [
            project_path / "src" / "run.py",
            project_path / f"{config.name.replace('-', '_')}" / "run.py",
        ]
        for alt_path in alt_paths:
            if alt_path.exists():
                run_py_path = alt_path
                break
        else:
            console.print("[red]✗[/red] 找不到run.py文件，已尝试路径:")
            console.print(f"  - {run_py_path}")
            for alt_path in alt_paths:
                console.print(f"  - {alt_path}")
            raise click.ClickException("找不到run.py文件")

    console.print(f"[dim]源文件:[/dim] {run_py_path.relative_to(project_path)}")

    # 确定输出路径
    if output:
        output_path = Path(output)
        if not output_path.is_absolute():
            output_path = project_path / output_path
    else:
        output_path = run_py_path.parent / "run_flow.py"

    console.print(f"[dim]输出文件:[/dim] {output_path.relative_to(project_path)}")

    try:
        # 转换代码
        converted_code = convert_to_platform_format(run_py_path)

        # 写入输出文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(converted_code, encoding="utf-8")

        console.print("\n[green]✓[/green] 代码转换成功!")
        console.print(f"[dim]平台格式代码已保存至:[/dim] {output_path}")

    except Exception as e:
        console.print(f"[red]✗[/red] 代码转换失败: {e}")
        raise click.ClickException(str(e))


def convert_to_platform_format(run_py_path: Path) -> str:
    """将SDK格式的run.py转换为平台格式.

    Args:
        run_py_path: run.py文件路径

    Returns:
        转换后的代码字符串

    """
    # 读取源代码
    source_code = run_py_path.read_text(encoding="utf-8")

    # 解析AST
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        raise ValueError(f"源代码语法错误: {e}")

    # 查找Component类定义
    component_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # 检查是否继承自Component
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == "Component":
                    component_class = node
                    break
            if component_class:
                break

    if not component_class:
        raise ValueError("找不到继承自Component的类定义")

    # 提取组件信息
    component_info = extract_component_info(component_class, source_code)

    # 生成平台格式代码
    return generate_platform_code(component_info)


def extract_component_info(class_node: ast.ClassDef, source_code: str) -> dict[str, Any]:
    """从AST节点提取组件信息.

    Args:
        class_node: 类定义AST节点
        source_code: 源代码字符串

    Returns:
        组件信息字典

    """
    info: dict[str, Any] = {
        "class_name": class_node.name,
        "name": None,
        "display_name": None,
        "description": None,
        "documentation": None,
        "icon": None,
        "inputs": [],
        "outputs": [],
        "run_method_body": None,
    }

    # 提取类属性
    for node in class_node.body:
        if isinstance(node, (ast.AnnAssign, ast.Assign)):
            # 处理类属性赋值
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                attr_name = node.target.id
                attr_value = _get_constant_value(node.value)
            elif isinstance(node, ast.Assign):
                if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    attr_name = node.targets[0].id
                    attr_value = _get_constant_value(node.value)
                else:
                    continue
            else:
                continue

            # 保存元信息
            if attr_name in {"name", "display_name", "description", "documentation", "icon"}:
                info[attr_name] = attr_value
            elif attr_name == "inputs":
                info["inputs"] = _extract_io_definitions(node.value, source_code)
            elif attr_name == "outputs":
                info["outputs"] = _extract_io_definitions(node.value, source_code)

        # 提取run方法
        elif isinstance(node, ast.FunctionDef) and node.name == "run":
            # 获取方法体代码
            lines = source_code.split("\n")
            start_line = node.body[0].lineno - 1 if node.body else node.lineno
            end_line = node.end_lineno

            # 提取方法体，保留缩进
            method_lines = lines[start_line:end_line]
            # 移除一级缩进（类方法的缩进）
            info["run_method_body"] = "\n".join(line[8:] if line.startswith("        ") else line.lstrip() for line in method_lines).strip()

    return info


def _get_constant_value(node: ast.expr) -> Any:
    """获取常量值."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Str):  # Python 3.7 compatibility
        return node.s
    if isinstance(node, ast.Num):  # Python 3.7 compatibility
        return node.n
    return None


def _extract_io_definitions(node: ast.expr, source_code: str) -> list[dict[str, Any]]:
    """提取输入/输出定义列表."""
    if not isinstance(node, ast.List):
        return []

    io_defs = []
    lines = source_code.split("\n")

    for element in node.elts:
        if isinstance(element, ast.Call):
            # 提取Input/Output调用的参数
            io_def: dict[str, Any] = {}

            # 提取关键字参数
            for keyword in element.keywords:
                arg_name = keyword.arg
                arg_value = _get_call_arg_value(keyword.value, source_code, lines)
                io_def[arg_name] = arg_value

            io_defs.append(io_def)

    return io_defs


def _get_call_arg_value(node: ast.expr, source_code: str, lines: list[str]) -> Any:
    """获取函数调用参数的值."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Str):
        return node.s
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        # 处理InputType.MESSAGE_TEXT这样的枚举值
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))
    # 对于复杂表达式，返回代码片段
    try:
        return ast.get_source_segment(source_code, node)
    except:
        return None


def generate_platform_code(component_info: dict[str, Any]) -> str:
    """生成平台格式代码.

    Args:
        component_info: 组件信息

    Returns:
        生成的代码字符串

    """
    # 构建导入语句
    imports = [
        "import json",
        "import os",
        "import subprocess",
        "from pathlib import Path",
        "",
        "from sdw_platform.lfx.custom.custom_component.component import Component",
        "from sdw_platform.lfx.io import MessageTextInput, Output",
        "from sdw_platform.lfx.schema.data import Data",
    ]

    # 构建输入定义
    inputs_code = []
    for input_def in component_info["inputs"]:
        input_type = _map_input_type(input_def.get("type", "MessageTextInput"))
        input_code = f"""        {input_type}(
            name="{input_def.get("name", "input_value")}",
            display_name="{input_def.get("display_name", "Input Value")}",
            info="{input_def.get("description", "")}","""

        # 添加默认值
        value = input_def.get("value")
        if value is not None:
            if isinstance(value, str):
                input_code += f'\n            value="{value}",'
            else:
                input_code += f"\n            value={value},"

        # 添加tool_mode
        if input_def.get("tool_mode"):
            input_code += "\n            tool_mode=True,"

        input_code += "\n        )"
        inputs_code.append(input_code)

    inputs_str = ",\n".join(inputs_code) if inputs_code else ""

    # 构建输出定义
    outputs_code = []
    for output_def in component_info["outputs"]:
        output_code = f"""        Output(
            display_name="{output_def.get("display_name", "Output")}",
            name="{output_def.get("name", "output")}",
            method="build_output"
        )"""
        outputs_code.append(output_code)

    outputs_str = ",\n".join(outputs_code) if outputs_code else ""

    # 获取所有输入参数名称，用于构建调用参数
    input_names = [input_def.get("name", "input_value") for input_def in component_info["inputs"]]

    # 构建参数字典生成代码
    params_dict_code = "{\n"
    for input_name in input_names:
        params_dict_code += f'            "{input_name}": self.{input_name},\n'
    params_dict_code += "        }"

    # 生成完整代码
    return f'''"""Langflow平台格式组件代码

此文件由 sdwk build 命令自动生成，用于部署到 Langflow 平台。

该组件通过调用本地 run.py 来执行业务逻辑，保证本地开发和平台部署的一致性。
"""

{chr(10).join(imports)}


class {component_info["class_name"]}(Component):
    display_name = "{component_info.get("display_name", component_info["class_name"])}"
    description = "{component_info.get("description", "Use as a template to create your own component.")}"
    documentation: str = "{component_info.get("documentation", "https://docs.sdwplatform.org/components-custom-components")}"
    icon = "{component_info.get("icon", "code")}"
    name = "{component_info.get("name", component_info["class_name"])}"

    inputs = [
{inputs_str}
    ]

    outputs = [
{outputs_str}
    ]

    def build_output(self) -> Data:
        """构建输出数据

        通过调用 run.py 执行实际的业务逻辑

        Returns:
            Data: 组件输出数据
        """
        # 获取当前文件所在目录
        current_dir = Path(__file__).parent

        # 构建输入参数
        input_params = {params_dict_code}

        # 获取包名（假设包名与目录名一致）
        package_name = current_dir.name

        # 将输入参数序列化为 JSON
        input_json = json.dumps(input_params, ensure_ascii=False)

        try:
            # 构建命令：uv run -m package.run --mode=platform --input-json='...'
            cmd = [
                "uv", "run", "-m", f"{{package_name}}.run",
                "--mode=platform",
                f"--input-json={{input_json}}"
            ]

            # 设置环境变量传递工作流上下文
            # 平台应该在调用组件时设置这些环境变量
            env = os.environ.copy()

            # 从平台上下文获取 user_id 和 workflow_id
            user_id = getattr(self, "_user_id", None) or os.environ.get("USER_ID")
            workflow_id = getattr(self, "_workflow_id", None) or os.environ.get("WORKFLOW_ID")

            if user_id:
                env["USER_ID"] = str(user_id)
            if workflow_id:
                env["WORKFLOW_ID"] = str(workflow_id)

            result = subprocess.run(
                cmd,
                cwd=current_dir.parent.parent,  # 项目根目录
                capture_output=True,
                text=True,
                check=True,
                env=env  # 传递环境变量
            )

            # 解析 JSON 输出
            # run.py 在 platform 模式下会直接输出 JSON 格式的结果
            try:
                output_data = json.loads(result.stdout.strip())
            except json.JSONDecodeError:
                # 如果解析失败，使用整个输出作为值
                output_data = {{
                    "value": result.stdout.strip(),
                    "metadata": {{}}
                }}

            # 创建返回数据
            data = Data(
                value=output_data.get("value"),
                metadata=output_data.get("metadata", {{}})
            )

            # 设置状态
            self.status = data

            return data

        except subprocess.CalledProcessError as e:
            # 命令执行失败
            error_msg = f"执行组件失败: {{e.stderr}}"
            data = Data(
                value=None,
                metadata={{
                    "error": error_msg,
                    "returncode": e.returncode,
                    "stdout": e.stdout if hasattr(e, 'stdout') else None
                }}
            )
            self.status = data
            return data

        except Exception as e:
            # 其他错误
            error_msg = f"组件执行异常: {{str(e)}}"
            data = Data(
                value=None,
                metadata={{"error": error_msg}}
            )
            self.status = data
            return data
'''


def _map_input_type(input_type: str) -> str:
    """映射输入类型到平台类型.

    Args:
        input_type: SDK输入类型

    Returns:
        平台输入类型

    """
    # 如果已经是平台类型，直接返回
    if "Input" in input_type or "." in input_type:
        # 处理 InputType.MESSAGE_TEXT 这样的枚举
        if "." in input_type:
            # InputType.MESSAGE_TEXT -> MessageTextInput
            type_mapping = {
                "InputType.MESSAGE_TEXT": "MessageTextInput",
                "InputType.MULTILINE": "MultilineInput",
                "InputType.SECRET": "SecretStrInput",
                "InputType.BOOL": "BoolInput",
                "InputType.INT": "IntInput",
                "InputType.FLOAT": "FloatInput",
                "InputType.DROPDOWN": "DropdownInput",
                "InputType.FILE": "FileInput",
                "InputType.LIST": "ListInput",
                "InputType.DICT": "DictInput",
            }
            return type_mapping.get(input_type, "MessageTextInput")
        return input_type

    # 默认返回MessageTextInput
    return "MessageTextInput"
