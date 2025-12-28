"""异常处理工具模块."""

from collections.abc import Callable
import functools
from typing import Any

import click
from rich.console import Console

console = Console()


def handle_keyboard_interrupt(message: str = "操作已取消"):
    """装饰器：优雅处理KeyboardInterrupt异常.

    Args:
        message: 取消操作时显示的消息

    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except KeyboardInterrupt:
                console.print(f"\n\n[yellow]{message}[/yellow]")
                return None
            except click.Abort:
                console.print(f"\n[yellow]{message}[/yellow]")
                return None

        return wrapper

    return decorator


def safe_questionary_ask(questionary_obj, default_value=None):
    """安全的questionary询问，处理KeyboardInterrupt.

    Args:
        questionary_obj: questionary对象
        default_value: 默认值（当用户取消时返回）

    Returns:
        用户输入的值或None（如果用户取消）

    """
    try:
        return questionary_obj.ask()
    except KeyboardInterrupt:
        return None
    except click.Abort:
        return None


class UserCancelledError(Exception):
    """用户取消操作异常."""


class ProjectValidationError(Exception):
    """项目验证错误."""


class TemplateError(Exception):
    """模板相关错误."""


class PlatformError(Exception):
    """平台相关错误."""
