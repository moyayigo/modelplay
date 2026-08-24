"""应用配置管理模块
用于管理前端应用（游戏、课程等）的公共配置，如后端服务器地址、请求超时时间等。
"""
import json
import os
from typing import Dict, Any

# 配置文件路径
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
CONFIG_FILE = os.path.join(CONFIG_DIR, "app.json")

# 默认配置
DEFAULT_CONFIG = {
    # 后端 API 服务器地址
    "api_base_url": "http://localhost:8000",
    # 前端请求超时时间（秒），应大于后端 LLM 超时时间
    "frontend_timeout": 480,
    # 每日 token 限额（0 表示不限制）
    "daily_token_limit": 1000000,
}


def load_app_config() -> Dict[str, Any]:
    """加载应用配置，如果配置文件不存在则创建默认配置。"""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)

    if not os.path.exists(CONFIG_FILE):
        save_app_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        # 合并默认配置，确保新增字段有默认值
        merged = DEFAULT_CONFIG.copy()
        merged.update(config)
        return merged
    except (json.JSONDecodeError, IOError):
        return DEFAULT_CONFIG.copy()


def save_app_config(config: Dict[str, Any]) -> None:
    """保存应用配置。"""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def get_api_base_url() -> str:
    """获取后端 API 服务器地址。"""
    config = load_app_config()
    return config.get("api_base_url", DEFAULT_CONFIG["api_base_url"])


def get_frontend_timeout() -> int:
    """获取前端请求超时时间。"""
    config = load_app_config()
    return config.get("frontend_timeout", DEFAULT_CONFIG["frontend_timeout"])


def get_daily_token_limit() -> int:
    """获取每日 token 限额（0 表示不限制）。"""
    config = load_app_config()
    return int(config.get("daily_token_limit", DEFAULT_CONFIG["daily_token_limit"]))
