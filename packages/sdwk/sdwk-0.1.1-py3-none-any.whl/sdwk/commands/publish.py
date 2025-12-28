"""Publish command for deploying SDW projects to platform."""

from pathlib import Path
from typing import Any
import zipfile

import click
import httpx
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from sdwk.core.exceptions import safe_questionary_ask
from sdwk.core.project_config import ProjectConfig
from sdwk.core.template_manager import TemplateManager

console = Console()


@click.command()
@click.option("--project-dir", default=".", help="项目目录路径")
@click.option("--platform-url", help="平台地址 (覆盖配置文件中的设置)")
@click.option("--token", help="认证令牌")
@click.option("--version", help="发布版本号")
@click.option("--dry-run", is_flag=True, help="模拟发布，不实际上传")
def publish(project_dir: str, platform_url: str | None, token: str | None, version: str | None, dry_run: bool):
    """发布SDW项目到平台."""
    project_path = Path(project_dir).resolve()

    console.print(Panel.fit(f"[bold magenta]SDW Project Publisher[/bold magenta]\n项目路径: {project_path}", border_style="magenta"))

    # 验证项目
    template_manager = TemplateManager()
    if not template_manager.validate_project(project_path):
        console.print("[red]✗[/red] 无效的SDW项目目录")
        raise click.ClickException("无效的项目目录")

    # 加载项目配置
    try:
        config = ProjectConfig.from_file(project_path / "sdw.json")
        console.print(f"[dim]项目名称:[/dim] {config.name}")
        console.print(f"[dim]项目类型:[/dim] {config.type}")
    except Exception as e:
        console.print(f"[red]✗[/red] 加载项目配置失败: {e}")
        raise click.ClickException("配置文件错误")

    # 获取发布参数
    try:
        publish_info = _collect_publish_info(config, platform_url, token, version)

        if not publish_info:
            # 用户取消了操作
            console.print("\n[yellow]发布操作已取消[/yellow]")
            return

    except KeyboardInterrupt:
        console.print("\n\n[yellow]发布操作已取消[/yellow]")
        return

    if dry_run:
        console.print("\n[yellow]模拟发布模式 - 不会实际上传[/yellow]")

    try:
        # 执行发布流程
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            # 1. 预检查
            task = progress.add_task("执行发布前检查...", total=4)
            _pre_publish_check(project_path, config)
            progress.advance(task)

            # 2. 打包项目
            progress.update(task, description="打包项目文件...")
            package_path = _package_project(project_path, config, publish_info["version"])
            progress.advance(task)

            # 3. 上传到平台
            if not dry_run:
                progress.update(task, description="上传到平台...")
                upload_result = _upload_to_platform(package_path, publish_info["platform_url"], publish_info["token"], config)
                progress.advance(task)

                # 4. 验证发布
                progress.update(task, description="验证发布结果...")
                _verify_deployment(upload_result, publish_info["platform_url"], publish_info["token"])
                progress.advance(task)
            else:
                progress.advance(task, advance=2)

        if dry_run:
            console.print("\n[green]✓[/green] 模拟发布完成!")
            console.print(f"[dim]打包文件:[/dim] {package_path}")
        else:
            console.print("\n[green]✓[/green] 项目发布成功!")
            console.print(f"[dim]版本:[/dim] {publish_info['version']}")

    except Exception as e:
        console.print(f"[red]✗[/red] 发布失败: {e}")
        raise click.ClickException(str(e))


def _collect_publish_info(config: ProjectConfig, platform_url: str | None, token: str | None, version: str | None) -> dict[str, Any] | None:
    """收集发布信息."""
    # 平台地址
    if not platform_url:
        platform_url = config.platform_url
        if not platform_url:
            platform_url = safe_questionary_ask(questionary.text("平台地址:", default="https://platform.sdw.com"))
            if platform_url is None:
                return None

    # 认证令牌
    if not token:
        token = safe_questionary_ask(questionary.password("认证令牌:"))
        if token is None:
            return None

    # 版本号
    if not version:
        current_version = config.version
        version = safe_questionary_ask(questionary.text("发布版本:", default=current_version))
        if version is None:
            return None

    return {"platform_url": platform_url.rstrip("/"), "token": token, "version": version}


def _pre_publish_check(project_path: Path, config: ProjectConfig):
    """发布前检查."""
    # 检查必需文件
    required_files = ["sdw.json", "pyproject.toml"]
    if config.type == "node":
        required_files.append("src/main.py")
    elif config.type == "graph":
        required_files.append("workflow.json")

    for file_path in required_files:
        if not (project_path / file_path).exists():
            raise FileNotFoundError(f"缺少必需文件: {file_path}")

    # 检查项目配置
    if not config.name or not config.type:
        raise ValueError("项目配置不完整")


def _package_project(project_path: Path, config: ProjectConfig, version: str) -> Path:
    """打包项目."""
    package_name = f"{config.name}-{version}.zip"
    package_path = project_path / "dist" / package_name
    package_path.parent.mkdir(exist_ok=True)

    # 要排除的文件和目录
    exclude_patterns = {"__pycache__", "*.pyc", "*.pyo", "*.pyd", ".git", ".gitignore", ".DS_Store", "dist", "build", "*.egg-info", ".pytest_cache", ".coverage", "htmlcov", ".venv", "venv", ".env"}

    with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                # 检查是否应该排除
                relative_path = file_path.relative_to(project_path)
                if _should_exclude_file(relative_path, exclude_patterns):
                    continue

                # 添加到压缩包
                zipf.write(file_path, relative_path)

    return package_path


def _should_exclude_file(file_path: Path, exclude_patterns: set) -> bool:
    """判断文件是否应该被排除."""
    # 检查文件名和路径部分
    for part in file_path.parts:
        if part in exclude_patterns:
            return True

        # 检查通配符模式
        for pattern in exclude_patterns:
            if "*" in pattern:
                import fnmatch

                if fnmatch.fnmatch(part, pattern):
                    return True

    return False


def _upload_to_platform(package_path: Path, platform_url: str, token: str, config: ProjectConfig) -> dict[str, Any]:
    """上传到平台."""
    upload_url = f"{platform_url}/api/v1/projects/upload"

    headers = {"Authorization": f"Bearer {token}", "User-Agent": "SDW-Platform-SDK/0.1.0"}

    # 准备上传数据
    with open(package_path, "rb") as f:
        files = {"package": (package_path.name, f, "application/zip")}

        data = {"name": config.name, "type": config.type, "description": config.description, "version": config.version}

        # 发送请求
        with httpx.Client(timeout=300.0) as client:
            response = client.post(upload_url, headers=headers, data=data, files=files)

    if response.status_code != 200:
        error_msg = f"上传失败 (HTTP {response.status_code})"
        try:
            error_detail = response.json().get("message", "")
            if error_detail:
                error_msg += f": {error_detail}"
        except:
            pass
        raise Exception(error_msg)

    return response.json()


def _verify_deployment(upload_result: dict[str, Any], platform_url: str, token: str):
    """验证发布结果."""
    deployment_id = upload_result.get("deployment_id")
    if not deployment_id:
        return

    # 检查部署状态
    status_url = f"{platform_url}/api/v1/deployments/{deployment_id}/status"
    headers = {"Authorization": f"Bearer {token}", "User-Agent": "SDW-Platform-SDK/0.1.0"}

    with httpx.Client(timeout=30.0) as client:
        response = client.get(status_url, headers=headers)

    if response.status_code == 200:
        status_data = response.json()
        if status_data.get("status") != "success":
            raise Exception(f"部署验证失败: {status_data.get('message', '未知错误')}")
    else:
        console.print("[yellow]警告: 无法验证部署状态[/yellow]")
