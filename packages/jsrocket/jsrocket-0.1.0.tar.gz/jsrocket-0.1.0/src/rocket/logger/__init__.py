"""
生产级Logger包
使用方式：
    from logger_package import get_logger
    logger = get_logger(env="prod")
    logger.error("生产环境错误日志")
"""
from .core.logger import get_logger

__version__ = "1.0.0"
__all__ = ["get_logger"]
