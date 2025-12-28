"""Dev command for running SDW projects in development mode."""

from pathlib import Path
import subprocess
import sys

import click
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner

from sdwk.core.project_config import ProjectConfig
from sdwk.core.template_manager import TemplateManager

console = Console()


@click.command()
@click.option("--project-dir", default=".", help="项目目录路径")
@click.option("--port", default=8000, help="开发服务器端口")
@click.option("--host", default="localhost", help="开发服务器主机")
@click.option("--reload", is_flag=True, default=True, help="启用自动重载")
def dev(project_dir: str, port: int, host: str, reload: bool):
    """在开发模式下运行SDW项目."""
    project_path = Path(project_dir).resolve()

    console.print(Panel.fit(f"[bold green]SDW Development Server[/bold green]\n项目路径: {project_path}", border_style="green"))

    # 验证项目
    template_manager = TemplateManager()
    if not template_manager.validate_project(project_path):
        console.print("[red]✗[/red] 无效的SDW项目目录")
        console.print("请确保当前目录包含 sdw.json 配置文件")
        raise click.ClickException("无效的项目目录")

    # 加载项目配置
    try:
        config = ProjectConfig.from_file(project_path / "sdw.json")
        console.print(f"[dim]项目名称:[/dim] {config.name}")
        console.print(f"[dim]项目类型:[/dim] {config.type}")
    except Exception as e:
        console.print(f"[red]✗[/red] 加载项目配置失败: {e}")
        raise click.ClickException("配置文件错误")

    # 根据项目类型启动开发服务器
    try:
        if config.type == "node":
            _run_node_dev_server(project_path, config, host, port, reload)
        elif config.type == "graph":
            _run_graph_dev_server(project_path, config, host, port, reload)
        else:
            raise ValueError(f"不支持的项目类型: {config.type}")

    except KeyboardInterrupt:
        console.print("\n[yellow]开发服务器已停止[/yellow]")
    except Exception as e:
        console.print(f"[red]✗[/red] 启动开发服务器失败: {e}")
        raise click.ClickException(str(e))


def _run_node_dev_server(project_path: Path, config: ProjectConfig, host: str, port: int, reload: bool):
    """运行Node项目开发服务器."""
    console.print("\n[green]启动Node项目开发服务器...[/green]")
    console.print(f"[dim]地址:[/dim] http://{host}:{port}")

    # 检查入口文件
    entry_file = project_path / "src" / "main.py"
    if not entry_file.exists():
        entry_file = project_path / "main.py"

    if not entry_file.exists():
        raise FileNotFoundError("找不到项目入口文件 (main.py)")

    # 构建运行命令
    cmd = [sys.executable, str(entry_file), "--host", host, "--port", str(port)]

    if reload:
        cmd.append("--reload")

    # 运行开发服务器
    with Live(Spinner("dots", text="开发服务器运行中..."), console=console):
        subprocess.run(cmd, check=False, cwd=project_path, capture_output=False)


def _run_graph_dev_server(project_path: Path, config: ProjectConfig, host: str, port: int, reload: bool):
    """运行Graph项目开发服务器."""
    console.print("\n[green]启动Graph项目开发服务器...[/green]")
    console.print(f"[dim]地址:[/dim] http://{host}:{port}")

    # 检查工作流定义文件
    workflow_file = project_path / "workflow.json"
    if not workflow_file.exists():
        workflow_file = project_path / "src" / "workflow.json"

    if not workflow_file.exists():
        raise FileNotFoundError("找不到工作流定义文件 (workflow.json)")

    # 构建运行命令
    cmd = [sys.executable, "-m", "sdwk.runtime.graph_server", "--workflow", str(workflow_file), "--host", host, "--port", str(port)]

    if reload:
        cmd.append("--reload")

    # 运行开发服务器
    with Live(Spinner("dots", text="Graph服务器运行中..."), console=console):
        subprocess.run(cmd, check=False, cwd=project_path, capture_output=False)
