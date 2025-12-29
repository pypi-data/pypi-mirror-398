"""
打印工具模块

提供带时间戳和日志等级的打印功能
"""
import sys
from datetime import datetime
from typing import Optional


# ANSI 颜色代码
class Colors:
    """ANSI 颜色代码"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # 前景色
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # 亮色
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"


# 日志等级配置
LOG_LEVELS = {
    "DEBUG": {"color": Colors.CYAN, "prefix": "🔍 DEBUG"},
    "INFO": {"color": Colors.GREEN, "prefix": "ℹ️  INFO"},
    "WARNING": {"color": Colors.YELLOW, "prefix": "⚠️  WARNING"},
    "ERROR": {"color": Colors.RED, "prefix": "❌ ERROR"},
    "CRITICAL": {"color": Colors.BRIGHT_RED, "prefix": "🔥 CRITICAL"},
    "SUCCESS": {"color": Colors.BRIGHT_GREEN, "prefix": "✅ SUCCESS"},
}


def get_timestamp() -> str:
    """获取当前时间戳字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_print(
    message: str,
    level: str = "INFO",
    show_timestamp: bool = True,
    show_level: bool = True,
    use_color: bool = True,
    file=None
) -> None:
    """
    安全打印函数，支持时间戳、日志等级和颜色
    
    Args:
        message: 要打印的消息
        level: 日志等级，可选: DEBUG, INFO, WARNING, ERROR, CRITICAL, SUCCESS
        show_timestamp: 是否显示时间戳
        show_level: 是否显示日志等级
        use_color: 是否使用颜色（在不支持 ANSI 的环境中自动禁用）
        file: 输出文件对象，默认为 sys.stdout
    
    Examples:
        >>> safe_print("训练开始")
        2025-01-11 10:30:45 ℹ️  INFO    训练开始
        
        >>> safe_print("训练完成", level="SUCCESS")
        2025-01-11 10:35:20 ✅ SUCCESS 训练完成
        
        >>> safe_print("发现错误", level="ERROR")
        2025-01-11 10:36:10 ❌ ERROR   发现错误
        
        >>> safe_print("调试信息", level="DEBUG", show_timestamp=False)
        🔍 DEBUG   调试信息
    """
    if file is None:
        file = sys.stdout
    
    # 检查是否支持颜色（简单检查）
    if use_color and not _supports_color(file):
        use_color = False
    
    # 获取日志等级配置
    level = level.upper()
    if level not in LOG_LEVELS:
        level = "INFO"
    
    level_config = LOG_LEVELS[level]
    color = level_config["color"] if use_color else ""
    prefix = level_config["prefix"]
    reset = Colors.RESET if use_color else ""
    
    # 构建输出消息
    parts = []
    
    # 添加时间戳
    if show_timestamp:
        timestamp = get_timestamp()
        parts.append(f"{Colors.CYAN if use_color else ''}{timestamp}{reset}")
    
    # 添加日志等级
    if show_level:
        parts.append(f"{color}{prefix}{reset}")
    
    # 添加消息
    parts.append(message)
    
    # 打印
    output = " ".join(parts)
    print(output, file=file, flush=True)


def _supports_color(file) -> bool:
    """
    检查文件对象是否支持 ANSI 颜色
    
    Args:
        file: 文件对象
        
    Returns:
        是否支持颜色
    """
    # 检查是否是 TTY
    if not hasattr(file, "isatty"):
        return False
    
    if not file.isatty():
        return False
    
    # 检查环境变量
    import os
    
    # 如果明确禁用颜色
    if os.environ.get("NO_COLOR"):
        return False
    
    # 如果明确启用颜色
    if os.environ.get("FORCE_COLOR"):
        return True
    
    # Windows 检查
    if sys.platform == "win32":
        # Windows 10+ 支持 ANSI
        try:
            import platform
            version = platform.version()
            # Windows 10 build 10586+ 支持 ANSI
            if "10." in version:
                return True
        except:
            pass
        return False
    
    # Unix-like 系统通常支持
    return True


# 便捷函数
def print_debug(message: str, **kwargs) -> None:
    """打印 DEBUG 级别消息"""
    safe_print(message, level="DEBUG", **kwargs)


def print_info(message: str, **kwargs) -> None:
    """打印 INFO 级别消息"""
    safe_print(message, level="INFO", **kwargs)


def print_warning(message: str, **kwargs) -> None:
    """打印 WARNING 级别消息"""
    safe_print(message, level="WARNING", **kwargs)


def print_error(message: str, **kwargs) -> None:
    """打印 ERROR 级别消息"""
    safe_print(message, level="ERROR", **kwargs)


def print_critical(message: str, **kwargs) -> None:
    """打印 CRITICAL 级别消息"""
    safe_print(message, level="CRITICAL", **kwargs)


def print_success(message: str, **kwargs) -> None:
    """打印 SUCCESS 级别消息"""
    safe_print(message, level="SUCCESS", **kwargs)


def print_separator(char: str = "=", length: int = 80, **kwargs) -> None:
    """
    打印分隔线
    
    Args:
        char: 分隔符字符
        length: 分隔线长度
        **kwargs: 传递给 safe_print 的其他参数
    """
    safe_print(char * length, show_timestamp=False, show_level=False, **kwargs)


def print_header(title: str, char: str = "=", length: int = 80, **kwargs) -> None:
    """
    打印标题头
    
    Args:
        title: 标题文本
        char: 分隔符字符
        length: 分隔线长度
        **kwargs: 传递给 safe_print 的其他参数
    """
    print_separator(char, length, **kwargs)
    safe_print(title, show_timestamp=False, show_level=False, **kwargs)
    print_separator(char, length, **kwargs)


# 向后兼容：保持原有的 safe_print 签名
def safe_print_legacy(message: str, level: str = "INFO") -> None:
    """
    向后兼容的 safe_print 函数
    
    Args:
        message: 要打印的消息
        level: 日志等级
    """
    safe_print(message, level=level)


if __name__ == "__main__":
    # 测试代码
    print_header("WeData AutoML Print Utils 测试")
    
    print()
    safe_print("这是一条普通消息")
    safe_print("这是一条调试消息", level="DEBUG")
    safe_print("这是一条信息消息", level="INFO")
    safe_print("这是一条警告消息", level="WARNING")
    safe_print("这是一条错误消息", level="ERROR")
    safe_print("这是一条严重错误消息", level="CRITICAL")
    safe_print("这是一条成功消息", level="SUCCESS")
    
    print()
    print_separator("-")
    
    print()
    safe_print("不显示时间戳", show_timestamp=False)
    safe_print("不显示日志等级", show_level=False)
    safe_print("不使用颜色", use_color=False)
    
    print()
    print_separator("-")
    
    print()
    print_debug("使用便捷函数：DEBUG")
    print_info("使用便捷函数：INFO")
    print_warning("使用便捷函数：WARNING")
    print_error("使用便捷函数：ERROR")
    print_critical("使用便捷函数：CRITICAL")
    print_success("使用便捷函数：SUCCESS")
    
    print()
    print_header("测试完成", char="-", length=60)

