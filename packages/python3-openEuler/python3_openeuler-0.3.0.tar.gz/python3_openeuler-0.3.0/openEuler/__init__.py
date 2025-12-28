from openEuler.openEuler import OpenEuler
import logging
from typing import Optional, Union

# 初始化包专属日志器（名称与包绑定，避免冲突）
logger = logging.getLogger(__name__)

# 核心：设置默认日志级别为 INFO（全局生效）
DEFAULT_LOG_LEVEL = logging.INFO
logger.setLevel(DEFAULT_LOG_LEVEL)

# 禁止日志向上传播（避免干扰用户根日志器）
logger.propagate = False

# 定义默认日志格式（包含关键上下文信息）
DEFAULT_FORMATTER = logging.Formatter(
    fmt="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def _add_default_handler(level: int = DEFAULT_LOG_LEVEL):
    """
    为日志器添加默认控制台Handler（仅在无Handler时添加，避免重复输出）

    Args:
        level: Handler的日志级别（默认与logger级别一致）
    """
    if not logger.handlers:
        # 输出到stdout（而非stderr，避免与错误信息混淆）
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)  # Handler级别可独立控制
        console_handler.setFormatter(DEFAULT_FORMATTER)
        logger.addHandler(console_handler)


def get_logger(
        custom_formatter: Optional[logging.Formatter] = None,
        level: Optional[Union[int, str]] = None
) -> logging.Logger:
    """
    获取包的日志器，支持自定义格式和级别

    Args:
        custom_formatter: 自定义日志格式（如不指定则使用默认格式）
        level: 日志级别（可选，如 logging.DEBUG 或 "DEBUG"，优先级高于默认）

    Returns:
        配置好的日志器实例
    """
    # 确保默认Handler存在（首次调用时初始化）
    _add_default_handler()

    # 动态调整日志级别（支持字符串级别，如 "DEBUG"，更友好）
    if level is not None:
        # 若传入字符串级别（如 "DEBUG"），转换为logging常量
        if isinstance(level, str):
            level = logging.getLevelName(level.upper())
        logger.setLevel(level)
        # 同步调整所有Handler的级别（避免Handler级别低于logger导致的日志丢失）
        for handler in logger.handlers:
            handler.setLevel(level)

    # 应用用户自定义格式
    if custom_formatter:
        for handler in logger.handlers:
            handler.setFormatter(custom_formatter)

    return logger


# 初始化时触发一次默认Handler添加（确保用户首次使用日志即有输出）
_add_default_handler()

__all__ = ["OpenEuler", "get_logger"]