"""
ESN Tool CLI 入口模块

定义主命令组和子命令的注册。
"""

import click
from rich.console import Console

from esn_tool import __version__
from esn_tool.commands import acm, config, git

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="esn-tool")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """ESN Tool - 项目管理 CLI 工具
    
    一个用于管理生产项目的命令行工具。
    """
    ctx.ensure_object(dict)


# 注册子命令
cli.add_command(git.git)
cli.add_command(acm.acm)
cli.add_command(config.config)


if __name__ == "__main__":
    cli()
