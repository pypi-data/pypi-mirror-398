"""
类型转换函数

用于将字符串参数转换为正确的类型
"""
import json
from typing import Any, List, Optional


def to_int(value: Any) -> int:
    """转换为整数"""
    if value is None or value == "":
        return None
    return int(value)


def to_float(value: Any) -> float:
    """转换为浮点数"""
    if value is None or value == "":
        return None
    return float(value)


def to_bool(value: Any) -> bool:
    """转换为布尔值"""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "y")
    return bool(value)


def split_by_comma(value: Any) -> Optional[List[str]]:
    """按逗号分割字符串"""
    if value is None or value == "":
        return None
    if isinstance(value, list):
        return value
    return [x.strip() for x in str(value).split(",") if x.strip()]


def parse_json(value: Any) -> Any:
    """解析 JSON 字符串"""
    if value is None or value == "":
        return None
    if isinstance(value, str):
        return json.loads(value)
    return value

