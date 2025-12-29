"""
配置管理模块

管理 esn-tool 的配置文件，支持持久化存储用户配置。
"""

import json
from pathlib import Path
from typing import Any

# 配置文件目录（用户主目录下的 .esntool）
CONFIG_DIR = Path.home() / ".esntool"
CONFIG_FILE = CONFIG_DIR / "config.json"

# 默认配置
DEFAULT_CONFIG = {
    "ai": {
        "api_key": "",
        "base_url": "https://api.siliconflow.cn/v1",
        "model": "Qwen/Qwen2.5-7B-Instruct",
    }
}


def ensure_config_dir() -> None:
    """确保配置目录存在"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    """
    加载配置文件。
    
    Returns:
        配置字典，如果文件不存在则返回默认配置
    """
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            # 合并默认配置，确保所有键都存在
            merged = DEFAULT_CONFIG.copy()
            _deep_merge(merged, config)
            return merged
    except (json.JSONDecodeError, OSError):
        return DEFAULT_CONFIG.copy()


def save_config(config: dict[str, Any]) -> None:
    """
    保存配置到文件。
    
    Args:
        config: 配置字典
    """
    ensure_config_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_config_value(key: str, default: Any = None) -> Any:
    """
    获取配置值（支持点分隔的键路径）。
    
    Args:
        key: 配置键，如 "ai.api_key"
        default: 默认值
        
    Returns:
        配置值
    """
    config = load_config()
    keys = key.split(".")
    value = config
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value if value else default


def set_config_value(key: str, value: Any) -> None:
    """
    设置配置值（支持点分隔的键路径）。
    
    Args:
        key: 配置键，如 "ai.api_key"
        value: 配置值
    """
    config = load_config()
    keys = key.split(".")
    
    # 导航到父级
    target = config
    for k in keys[:-1]:
        if k not in target:
            target[k] = {}
        target = target[k]
    
    # 设置值
    target[keys[-1]] = value
    save_config(config)


def _deep_merge(base: dict, override: dict) -> None:
    """深度合并字典，将 override 合并到 base 中"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
