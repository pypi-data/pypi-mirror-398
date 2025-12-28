"""Check command for validating SDW projects."""

from pathlib import Path
import subprocess
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from sdwk.core.project_config import ProjectConfig
from sdwk.core.template_manager import TemplateManager

console = Console()


@click.command()
@click.option("--project-dir", default=".", help="项目目录路径")
@click.option("--fix", is_flag=True, help="自动修复可修复的问题")
@click.option("--strict", is_flag=True, help="严格模式检查")
def check(project_dir: str, fix: bool, strict: bool):
    """检查SDW项目的代码质量和配置."""
    project_path = Path(project_dir).resolve()

    console.print(Panel.fit(f"[bold yellow]SDW Project Checker[/bold yellow]\n项目路径: {project_path}", border_style="yellow"))

    # 验证项目
    template_manager = TemplateManager()
    if not template_manager.validate_project(project_path):
        console.print("[red]✗[/red] 无效的SDW项目目录")
        raise click.ClickException("无效的项目目录")

    # 加载项目配置
    try:
        config = ProjectConfig.from_file(project_path / "sdw.json")
    except Exception as e:
        console.print(f"[red]✗[/red] 加载项目配置失败: {e}")
        raise click.ClickException("配置文件错误")

    # 执行检查
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("正在检查项目...", total=None)

        issues = []

        # 1. 项目结构检查
        progress.update(task, description="检查项目结构...")
        structure_issues = _check_project_structure(project_path, config)
        issues.extend(structure_issues)

        # 2. 代码质量检查
        progress.update(task, description="检查代码质量...")
        code_issues = _check_code_quality(project_path, config, strict)
        issues.extend(code_issues)

        # 3. 依赖检查
        progress.update(task, description="检查依赖...")
        dependency_issues = _check_dependencies(project_path, config)
        issues.extend(dependency_issues)

        # 4. 配置检查
        progress.update(task, description="检查配置...")
        config_issues = _check_configuration(project_path, config)
        issues.extend(config_issues)

        progress.update(task, description="检查完成!")

    # 显示检查结果
    _display_check_results(issues, fix)

    # 如果有错误，退出码为1
    error_count = len([issue for issue in issues if issue[1] == "error"])
    if error_count > 0:
        raise click.ClickException(f"发现 {error_count} 个错误")


def _check_project_structure(project_path: Path, config: ProjectConfig) -> list[tuple[str, str, str]]:
    """检查项目结构."""
    issues = []

    # 检查必需文件
    required_files = ["sdw.json", "pyproject.toml"]
    if config.type == "node":
        required_files.extend(["src/main.py"])
    elif config.type == "graph":
        required_files.extend(["workflow.json"])

    for file_path in required_files:
        if not (project_path / file_path).exists():
            issues.append((f"缺少必需文件: {file_path}", "error", "structure"))

    # 检查推荐文件
    recommended_files = ["README.md", ".gitignore"]
    for file_path in recommended_files:
        if not (project_path / file_path).exists():
            issues.append((f"缺少推荐文件: {file_path}", "warning", "structure"))

    return issues


def _check_code_quality(project_path: Path, config: ProjectConfig, strict: bool) -> list[tuple[str, str, str]]:
    """检查代码质量."""
    issues = []

    # 查找Python文件
    python_files = list(project_path.rglob("*.py"))
    if not python_files:
        return issues

    try:
        # 运行flake8检查
        result = subprocess.run([sys.executable, "-m", "flake8", "--max-line-length=88"] + [str(f) for f in python_files], check=False, cwd=project_path, capture_output=True, text=True)

        if result.returncode != 0:
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    severity = "error" if strict else "warning"
                    issues.append((f"代码风格问题: {line}", severity, "code_quality"))

    except FileNotFoundError:
        issues.append(("未安装flake8，跳过代码风格检查", "info", "code_quality"))

    return issues


def _check_dependencies(project_path: Path, config: ProjectConfig) -> list[tuple[str, str, str]]:
    """检查依赖."""
    issues = []

    pyproject_file = project_path / "pyproject.toml"
    if not pyproject_file.exists():
        issues.append(("缺少pyproject.toml文件", "error", "dependencies"))
        return issues

    # 这里可以添加更多依赖检查逻辑
    # 比如检查版本冲突、安全漏洞等

    return issues


def _check_configuration(project_path: Path, config: ProjectConfig) -> list[tuple[str, str, str]]:
    """检查配置."""
    issues = []

    # 检查配置完整性
    if not config.name:
        issues.append(("项目名称不能为空", "error", "config"))

    if not config.description:
        issues.append(("建议添加项目描述", "warning", "config"))

    if config.type not in {"node", "graph"}:
        issues.append((f"不支持的项目类型: {config.type}", "error", "config"))

    return issues


def _display_check_results(issues: list[tuple[str, str, str]], fix_enabled: bool):
    """显示检查结果."""
    if not issues:
        console.print("\n[green]✓ 项目检查通过，未发现问题！[/green]")
        return

    # 按严重程度分组
    errors = [issue for issue in issues if issue[1] == "error"]
    warnings = [issue for issue in issues if issue[1] == "warning"]
    infos = [issue for issue in issues if issue[1] == "info"]

    # 创建结果表格
    table = Table(title="检查结果")
    table.add_column("类型", style="bold")
    table.add_column("问题", style="")
    table.add_column("严重程度", justify="center")

    for message, severity, category in issues:
        severity_style = {"error": "[red]错误[/red]", "warning": "[yellow]警告[/yellow]", "info": "[blue]信息[/blue]"}
        table.add_row(category, message, severity_style[severity])

    console.print("\n")
    console.print(table)

    # 显示统计
    console.print(f"\n[red]错误: {len(errors)}[/red] | [yellow]警告: {len(warnings)}[/yellow] | [blue]信息: {len(infos)}[/blue]")

    if fix_enabled:
        console.print("\n[dim]注意: 自动修复功能尚未实现[/dim]")
