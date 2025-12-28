"""Create command for generating new SDW projects."""

from typing import Any

import click
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from sdwk.core.exceptions import safe_questionary_ask
from sdwk.core.template_manager import TemplateManager

console = Console()


@click.command()
@click.option("--name", help="项目名称")
@click.option("--type", "project_type", type=click.Choice(["node", "graph"]), help="项目类型")
@click.option("--description", help="项目描述")
@click.option("--platform-url", help="平台地址")
@click.option("--output-dir", help="输出目录", default=".")
def create(name: str, project_type: str, description: str, platform_url: str, output_dir: str):
    """创建新的SDW项目."""
    console.print(Panel.fit("[bold blue]SDW Platform SDK[/bold blue]\n创建新项目向导", border_style="blue"))

    try:
        # 交互式收集项目信息
        project_info = _collect_project_info(name, project_type, description, platform_url)

        if not project_info:
            # 用户取消了操作
            console.print("\n[yellow]操作已取消[/yellow]")
            return

    except KeyboardInterrupt:
        console.print("\n\n[yellow]操作已取消[/yellow]")
        return

    # 创建项目
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("正在创建项目...", total=None)

            template_manager = TemplateManager()
            project_path = template_manager.create_project(project_info=project_info, output_dir=output_dir)

            progress.update(task, description="项目创建完成!")

        console.print("\n[green]✓[/green] 项目创建成功!")
        console.print(f"[dim]项目路径:[/dim] {project_path}")
        console.print("\n[yellow]下一步:[/yellow]")
        console.print(f"  cd {project_info['name']}")
        console.print("  sdwk dev")

    except Exception as e:
        console.print(f"[red]✗[/red] 创建项目失败: {e}")
        raise click.ClickException(str(e))


def _collect_project_info(name: str, project_type: str, description: str, platform_url: str) -> dict[str, Any] | None:
    """交互式收集项目信息."""
    # 项目名称
    if not name:
        name = safe_questionary_ask(questionary.text("项目名称:", validate=lambda x: len(x.strip()) > 0 or "项目名称不能为空"))
        if name is None:
            return None

    # 项目类型
    if not project_type:
        project_type = safe_questionary_ask(questionary.select("选择项目类型:", choices=[questionary.Choice("Node项目 (单节点处理)", "node"), questionary.Choice("Graph项目 (工作流图)", "graph")]))
        if project_type is None:
            return None

    # 项目描述
    if not description:
        description = safe_questionary_ask(questionary.text("项目描述:", default="A new SDW project"))
        if description is None:
            return None

    # 平台地址
    if not platform_url:
        platform_url = safe_questionary_ask(questionary.text("平台地址:", default="https://platform.sdw.com"))
        if platform_url is None:
            return None

    return {
        "name": name.strip(),
        "type": project_type,
        "description": description.strip(),
        "platform_url": platform_url.strip(),
    }
