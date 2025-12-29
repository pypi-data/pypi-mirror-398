"""
配置管理命令模块

提供交互式配置界面，管理 esn-tool 的各项配置。
"""

import click
from rich.console import Console

from esn_tool.utils.config import (
    CONFIG_FILE,
    get_config_value,
    set_config_value,
)

console = Console()


@click.command()
def config() -> None:
    """
    \b
    配置管理
    
    \b
    交互式配置 esn-tool 的各项设置，包括 AI 接口等。
    配置文件保存在 ~/.esntool/config.json
    
    \b
    示例:
        esntool config
    """
    _interactive_setup()


def _interactive_setup() -> None:
    """菜单式配置设置"""
    import questionary
    from questionary import Style
    
    # 自定义样式
    custom_style = Style([
        ("qmark", "fg:cyan bold"),
        ("question", "bold"),
        ("answer", "fg:green"),
        ("pointer", "fg:cyan bold"),
        ("highlighted", "fg:cyan bold"),
        ("selected", "fg:green"),
    ])
    
    console.print("\n[bold cyan]📋 ESN Tool 配置[/bold cyan]")
    console.print("[dim]使用 ↑↓ 选择配置项，回车编辑，Ctrl+C 退出[/dim]\n")
    
    while True:
        # 获取当前配置值
        current_api_key = get_config_value("ai.api_key", "")
        current_base_url = get_config_value("ai.base_url", "https://api.siliconflow.cn/v1")
        current_model = get_config_value("ai.model", "Qwen/Qwen2.5-7B-Instruct")
        
        # API Key 脱敏显示
        if current_api_key:
            masked_key = current_api_key[:8] + "..." + current_api_key[-4:] if len(current_api_key) > 12 else "***"
        else:
            masked_key = "(未设置)"
        
        # 构建选项列表
        choices = [
            f"API Key     : {masked_key}",
            f"Base URL    : {current_base_url[:40]}..." if len(current_base_url) > 40 else f"Base URL    : {current_base_url}",
            f"Model       : {current_model}",
            "─" * 40,
            "✓ 保存并退出",
        ]
        
        try:
            selected = questionary.select(
                "选择要编辑的配置项:",
                choices=choices,
                style=custom_style,
                instruction="(↑↓ 选择, Enter 编辑)",
            ).ask()
        except KeyboardInterrupt:
            console.print("\n[yellow]已取消[/yellow]")
            return
        
        if selected is None:
            console.print("\n[yellow]已取消[/yellow]")
            return
        
        if "保存并退出" in selected:
            console.print("\n[green]✓ 配置已保存[/green]")
            console.print(f"[dim]配置文件: {CONFIG_FILE}[/dim]\n")
            return
        
        if selected.startswith("─"):
            continue
        
        # 根据选择编辑对应配置
        if selected.startswith("API Key"):
            try:
                new_value = questionary.text(
                    "请输入新的 API Key:",
                    default=current_api_key,
                    style=custom_style,
                ).ask()
                if new_value is not None and new_value != current_api_key:
                    set_config_value("ai.api_key", new_value)
                    console.print("[green]✓ API Key 已更新[/green]\n")
            except KeyboardInterrupt:
                pass
                
        elif selected.startswith("Base URL"):
            try:
                new_value = questionary.text(
                    "请输入新的 Base URL:",
                    default=current_base_url,
                    style=custom_style,
                ).ask()
                if new_value is not None and new_value != current_base_url:
                    set_config_value("ai.base_url", new_value)
                    console.print("[green]✓ Base URL 已更新[/green]\n")
            except KeyboardInterrupt:
                pass
                
        elif selected.startswith("Model"):
            # 提供模型选择
            console.print("[dim]常用模型:[/dim]")
            model_choices = [
                "Qwen/Qwen2.5-7B-Instruct",
                "Qwen/Qwen2.5-32B-Instruct",
                "deepseek-ai/DeepSeek-V3",
                "deepseek-ai/DeepSeek-R1",
                "THUDM/glm-4-9b-chat",
                "─ 自定义输入 ─",
            ]
            try:
                model_selected = questionary.select(
                    "选择模型:",
                    choices=model_choices,
                    default=current_model if current_model in model_choices else model_choices[0],
                    style=custom_style,
                ).ask()
                
                if model_selected and "自定义" in model_selected:
                    model_selected = questionary.text(
                        "请输入模型名称:",
                        default=current_model,
                        style=custom_style,
                    ).ask()
                
                if model_selected and model_selected != current_model and "─" not in model_selected:
                    set_config_value("ai.model", model_selected)
                    console.print("[green]✓ Model 已更新[/green]\n")
            except KeyboardInterrupt:
                pass
