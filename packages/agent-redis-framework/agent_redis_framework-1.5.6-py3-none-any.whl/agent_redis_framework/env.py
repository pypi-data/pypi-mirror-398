"""环境变量加载模块

提供轻量级的 .env 文件加载和环境变量读取功能，无需外部依赖。
"""

from __future__ import annotations

import os
from typing import Optional


def _load_env_file() -> None:
    """最小化 .env 加载器：解析 KEY=VALUE 行，忽略注释与空行。

    查找顺序：
    1) 当前工作目录 .env
    2) 项目根目录 .env（相对于本文件：../../.env）
    已存在于 os.environ 的键不覆盖。
    """
    candidates: list[str] = []
    try:
        cwd_env = os.path.join(os.getcwd(), ".env")
        candidates.append(cwd_env)
    except Exception:
        pass
    try:
        root_env = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, ".env")
        )
        candidates.append(root_env)
    except Exception:
        pass

    for path in candidates:
        if not path or not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    key = k.strip()
                    val = v.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = val
        except Exception:
            # 静默失败，避免影响正常导入
            continue


def env_str(key: str, default: str) -> str:
    """获取字符串类型的环境变量。"""
    return os.getenv(key, default)


def env_opt_str(*keys: str) -> Optional[str]:
    """获取可选字符串类型的环境变量，支持多个候选键。"""
    for k in keys:
        val = os.getenv(k)
        if val is not None and val != "":
            return val
    return None


def env_int(key: str, default: int) -> int:
    """获取整数类型的环境变量。"""
    val = os.getenv(key)
    if val is None or val == "":
        return default
    try:
        return int(val)
    except Exception:
        return default


def env_float_opt(key: str) -> Optional[float]:
    """获取可选浮点数类型的环境变量。"""
    val = os.getenv(key)
    if val is None or val == "":
        return None
    try:
        return float(val)
    except Exception:
        return None


def env_bool(key: str, default: bool) -> bool:
    """获取布尔类型的环境变量。"""
    val = os.getenv(key)
    if val is None or val == "":
        return default
    true_set = {"1", "true", "yes", "on", "y", "t"}
    false_set = {"0", "false", "no", "off", "n", "f"}
    v = val.strip().lower()
    if v in true_set:
        return True
    if v in false_set:
        return False
    return default


# 自动加载 .env 文件
_load_env_file()


__all__ = ["env_str", "env_opt_str", "env_int", "env_float_opt", "env_bool"]