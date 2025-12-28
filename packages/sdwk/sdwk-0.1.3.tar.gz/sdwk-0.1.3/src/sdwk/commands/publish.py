"""Publish command for deploying SDW projects to platform."""

from pathlib import Path
from typing import Any
import zipfile
import json
import os
import yaml

import click
import httpx
import pathspec
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
        env_token = os.getenv("SDW_PLATFORM_TOKEN")
        if env_token:
            token = env_token
        else:
            console.print("[dim]尝试登录以获取令牌...[/dim]")
            token = _login_to_platform(platform_url.rstrip("/"))
            if token is None:
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


def _login_to_platform(platform_url: str) -> str | None:
    """登录平台并获取令牌."""
    username = safe_questionary_ask(questionary.text("用户名:"))
    if username is None:
        return None
    password = safe_questionary_ask(questionary.password("密码:"))
    if password is None:
        return None

    login_endpoints = [
        f"{platform_url}/api/login",
    ]

    headers = {"User-Agent": "SDW-Platform-SDK/0.1.0"}
    with httpx.Client(timeout=30.0) as client:
        while True:
            success = False
            for endpoint in login_endpoints:
                console.print(f"[dim]请求登录API:[/dim] {endpoint}")
                try:
                    resp = client.post(endpoint, data={"username": username, "password": password}, headers=headers)
                    resp_json = None
                    try:
                        resp_json = resp.json()
                    except Exception:
                        pass
                    msg = resp_json.get("detail") or resp_json.get("message") if isinstance(resp_json, dict) else ""
                    console.print(f"[dim]登录响应:[/dim] HTTP {resp.status_code}" + (f", message: {msg}" if msg else ""))
                    if resp.status_code == 200 and isinstance(resp_json, dict):
                        token = resp_json.get("token") or resp_json.get("access_token") or resp_json.get("api_key")
                        if token:
                            console.print("[green]✓[/green] 登录成功，已获取令牌")
                            return token
                    if resp.status_code in {400, 401, 403}:
                        break
                except Exception as e:
                    console.print(f"[yellow]登录请求失败: {type(e).__name__}: {e}[/yellow]")

            action = safe_questionary_ask(
                questionary.select("登录失败，选择下一步:", choices=["重试登录", "使用令牌", "取消"])
            )
            if action is None or action == "取消":
                return None
            if action == "使用令牌":
                manual_token = safe_questionary_ask(questionary.password("认证令牌:"))
                if manual_token:
                    return manual_token
                continue
            if action == "重试登录":
                new_username = safe_questionary_ask(questionary.text("用户名:", default=username))
                if new_username is None:
                    return None
                username = new_username
                new_password = safe_questionary_ask(questionary.password("密码:"))
                if new_password is None:
                    return None
                password = new_password


def _load_gitignore_spec(project_path: Path) -> pathspec.PathSpec | None:
    """加载 .gitignore 文件并返回 PathSpec 对象."""
    gitignore_path = project_path / ".gitignore"
    if not gitignore_path.exists():
        return None

    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            patterns = f.read().splitlines()
        return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
    except Exception as e:
        console.print(f"[yellow]警告: 无法读取 .gitignore 文件: {e}[/yellow]")
        return None


def _pre_publish_check(project_path: Path, config: ProjectConfig):
    """发布前检查."""
    # 检查必需文件
    required_files = ["sdw.json", "pyproject.toml"]
    context = config.get_template_context()
    project_name_snake = context["project_name_snake"]
    if config.type == "node":
        # 兼容两种结构：旧版 src/main.py 与新版 src/{project_name_snake}/main.py
        main_legacy = project_path / "src" / "main.py"
        main_new = project_path / "src" / project_name_snake / "main.py"
        if not main_legacy.exists() and not main_new.exists():
            raise FileNotFoundError(f"缺少必需文件: src/{project_name_snake}/main.py (或 src/main.py)")
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
    context = config.get_template_context()
    project_name_snake = context["project_name_snake"]
    candidates = [
        project_path / "src" / project_name_snake / "run_flow.py",
        project_path / "src" / "run_flow.py",
        project_path / project_name_snake / "run_flow.py",
        project_path / "run_flow.py",
    ]
    found = None
    for c in candidates:
        if c.exists():
            found = c
            break
    if not found:
        any_run_flow = next(project_path.rglob("run_flow.py"), None)
        if not any_run_flow:
            raise FileNotFoundError("缺少必需文件: run_flow.py，请先执行 sdwk build 生成")

    package_name = f"{config.name}-{version}.zip"
    package_path = project_path / "dist" / package_name
    package_path.parent.mkdir(exist_ok=True)

    # 加载 .gitignore 规则
    gitignore_spec = _load_gitignore_spec(project_path)

    # 基础排除模式（即使没有 .gitignore 也要排除这些）
    base_exclude_patterns = [
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".git/",
        ".DS_Store",
        "dist/",
        "build/",
        "*.egg-info/",
        ".pytest_cache/",
        ".coverage",
        "htmlcov/",
        ".venv/",
        "venv/",
        ".env",
    ]
    base_exclude_spec = pathspec.PathSpec.from_lines("gitwildmatch", base_exclude_patterns)

    with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                # 检查是否应该排除
                relative_path = file_path.relative_to(project_path)
                relative_path_str = relative_path.as_posix()

                # 使用 pathspec 检查是否应该排除
                if base_exclude_spec.match_file(relative_path_str):
                    continue
                if gitignore_spec and gitignore_spec.match_file(relative_path_str):
                    continue

                # 添加到压缩包
                # 对 sdw.json 按照当前生成逻辑修正 entry_point 后再写入压缩包
                if relative_path.as_posix() == "sdw.json":
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            sdw_data = json.load(f)
                        context = config.get_template_context()
                        project_name_snake = context["project_name_snake"]
                        # 仅在 node/graph 项目上修正入口
                        if config.type in {"node", "graph"}:
                            sdw_data["entry_point"] = f"src.{project_name_snake}.main:app"
                        zipf.writestr(str(relative_path).replace("\\", "/"), json.dumps(sdw_data, ensure_ascii=False, indent=2))
                    except Exception:
                        # 如果修正失败则按原文件写入
                        zipf.write(file_path, relative_path)
                # 对 config/settings.yaml 注入平台地址
                elif relative_path.as_posix().endswith("config/settings.yaml"):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            settings_data = yaml.safe_load(f) or {}

                        # 注入平台地址
                        if "platform" not in settings_data:
                            settings_data["platform"] = {}
                        settings_data["platform"]["url"] = config.platform_url

                        # 写入压缩包
                        yaml_content = yaml.dump(settings_data, allow_unicode=True, default_flow_style=False, sort_keys=False)
                        zipf.writestr(str(relative_path).replace("\\", "/"), yaml_content)
                        console.print(f"[dim]✓ 已注入平台地址到配置文件: {config.platform_url}[/dim]")
                    except Exception as e:
                        console.print(f"[yellow]警告: 无法注入平台配置到 {relative_path}: {e}[/yellow]")
                        # 如果处理失败则按原文件写入
                        zipf.write(file_path, relative_path)
                else:
                    zipf.write(file_path, relative_path)

    return package_path


def _upload_to_platform(package_path: Path, platform_url: str, token: str, config: ProjectConfig) -> dict[str, Any]:
    """上传到平台."""
    upload_endpoints = [
        f"{platform_url}/api/sdk/upload",
    ]

    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "SDW-Platform-SDK/0.1.0",
        "Accept": "application/json",
    }

    # 准备上传数据
    with open(package_path, "rb") as f:
        files = {"file": (package_path.name, f, "application/zip")}

        with httpx.Client(timeout=300.0) as client:
            last_response: httpx.Response | None = None
            for endpoint in upload_endpoints:
                console.print(f"[dim]请求上传API:[/dim] {endpoint}")
                try:
                    # 同时尝试通过Cookie提高兼容性（部分后端从Cookie读取token）
                    client.cookies.set("access_token_lf", token)
                    response = client.post(endpoint, headers=headers, files=files)
                    last_response = response
                    # 打印响应详情
                    resp_json = None
                    try:
                        resp_json = response.json()
                    except Exception:
                        resp_json = None
                    message = ""
                    if isinstance(resp_json, dict):
                        message = resp_json.get("message") or resp_json.get("detail") or ""
                    console.print(f"[dim]上传响应:[/dim] HTTP {response.status_code}" + (f", message: {message}" if message else ""))
                    # 成功状态：后端定义为201 CREATED 或 200 OK
                    if response.status_code in (200, 201):
                        return resp_json if isinstance(resp_json, dict) else {"message": response.text}
                except Exception as e:
                    console.print(f"[yellow]上传请求失败: {type(e).__name__}: {e}[/yellow]")
                    continue

    # 失败时打印更多细节
    if last_response is not None:
        detail = ""
        try:
            data = last_response.json()
            detail = data.get("message") or data.get("detail") or ""
        except Exception:
            detail = (last_response.text or "")[:1000]
        raise Exception(f"上传失败 (HTTP {last_response.status_code})" + (f": {detail}" if detail else ""))
    raise Exception("上传失败：未收到服务器响应")


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
