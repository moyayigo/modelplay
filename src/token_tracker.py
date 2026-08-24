"""每日 Token 使用量追踪与限额管理

数据结构（存储于 config/token_usage.json）:
{
    "date": "2026-08-07",          # 当前计数日期（YYYY-MM-DD）
    "prompt_tokens": 12345,         # 当日输入 token 累计
    "completion_tokens": 6789,       # 当日输出 token 累计
    "total_tokens": 19134,           # 当日总 token 累计
    "call_count": 15                 # 当日 LLM 调用次数
}
"""
import json
import os
from datetime import date
from typing import Dict, Any, Optional

from src.app_config import load_app_config

# 配置文件路径
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
USAGE_FILE = os.path.join(CONFIG_DIR, "token_usage.json")


def _today_str() -> str:
    """返回今日日期字符串（YYYY-MM-DD）"""
    return date.today().isoformat()


def _empty_usage() -> Dict[str, Any]:
    return {
        "date": _today_str(),
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "call_count": 0,
    }


def load_usage() -> Dict[str, Any]:
    """加载今日的 token 使用统计，若跨天则自动重置。"""
    if not os.path.exists(USAGE_FILE):
        return _empty_usage()

    try:
        with open(USAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 跨天自动重置
        if data.get("date") != _today_str():
            return _empty_usage()
        return data
    except (json.JSONDecodeError, IOError):
        return _empty_usage()


def save_usage(usage: Dict[str, Any]) -> None:
    """保存 token 使用统计。"""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(USAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(usage, f, indent=4, ensure_ascii=False)


def add_usage(prompt_tokens: int, completion_tokens: int) -> Dict[str, Any]:
    """累加一次 LLM 调用的 token 使用量，返回更新后的统计。"""
    usage = load_usage()
    total = prompt_tokens + completion_tokens
    usage["prompt_tokens"] += prompt_tokens
    usage["completion_tokens"] += completion_tokens
    usage["total_tokens"] += total
    usage["call_count"] += 1
    save_usage(usage)
    return usage


def get_today_usage() -> Dict[str, Any]:
    """获取今日使用统计。"""
    return load_usage()


def get_daily_limit() -> int:
    """获取每日 token 限额（0 表示不限制）。"""
    config = load_app_config()
    return int(config.get("daily_token_limit", 0))


def check_limit() -> Dict[str, Any]:
    """检查当前是否超出限额。

    返回:
        {
            "allowed": bool,           # 是否允许继续调用
            "used": int,               # 今日已用 token
            "limit": int,              # 每日限额（0 表示不限）
            "remaining": int,          # 剩余 token（-1 表示不限）
            "reset_at": "明日 00:00",  # 重置时间描述
        }
    """
    limit = get_daily_limit()
    usage = load_usage()
    used = usage.get("total_tokens", 0)

    if limit <= 0:
        # 不限制
        return {
            "allowed": True,
            "used": used,
            "limit": limit,
            "remaining": -1,
            "reset_at": "每日 00:00 自动重置",
        }

    remaining = max(0, limit - used)
    allowed = used < limit
    return {
        "allowed": allowed,
        "used": used,
        "limit": limit,
        "remaining": remaining,
        "reset_at": "每日 00:00 自动重置",
    }


def reset_usage() -> Dict[str, Any]:
    """手动重置今日使用量（管理员操作）。"""
    empty = _empty_usage()
    save_usage(empty)
    return empty
