"""SDW Platform SDK CLI."""

import click
from rich.console import Console

from .commands.build import build
from .commands.check import check
from .commands.create import create
from .commands.dev import dev
from .commands.publish import publish

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="sdwk")
def main():
    """SDW Platform SDK - 用于创建、开发和发布SDW平台应用的工具."""


# 注册子命令
main.add_command(create)
main.add_command(dev)
main.add_command(check)
main.add_command(build)
main.add_command(publish)

if __name__ == "__main__":
    main()
