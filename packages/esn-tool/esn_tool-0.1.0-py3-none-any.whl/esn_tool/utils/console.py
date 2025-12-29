"""
控制台输出工具

提供统一的控制台输出样式和方法。
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def print_success(message: str) -> None:
    """打印成功消息"""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """打印错误消息"""
    console.print(f"[red]✗[/red] {message}")


def print_warning(message: str) -> None:
    """打印警告消息"""
    console.print(f"[yellow]⚠[/yellow] {message}")


def print_info(message: str) -> None:
    """打印信息消息"""
    console.print(f"[blue]ℹ[/blue] {message}")


def print_header(title: str) -> None:
    """打印标题"""
    console.print(Panel(Text(title, style="bold cyan"), expand=False))
