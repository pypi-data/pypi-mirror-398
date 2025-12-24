import logging
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
from typing import Optional, Union
from pathlib import Path
from .formatter import ColoredFormatter, JSONFormatter
from ..utils.config_loader import load_config
from ..utils.config_models import Config


class ProductionLogger:
    """生产级Logger封装类（支持环境配置 + 自定义配置）"""
    _instances: dict = {}  # 每个配置组合一个实例

    def __new__(
        cls,
        env: str = "dev",
        config_file: Optional[Union[str, Path]] = None
    ) -> logging.Logger:
        """
        创建logger实例（每个环境+配置组合使用独立实例）
        Args:
            env: 环境名称（dev/test/production）
            config_file: 可选的自定义配置文件路径
        """
        # 使用 env + config_file 作为缓存键
        cache_key = f"{env}:{config_file}"

        if cache_key not in cls._instances:
            config = load_config(env, config_file)
            logger = cls._setup_logger(config)
            cls._instances[cache_key] = logger

        return cls._instances[cache_key]

    @staticmethod
    def _setup_logger(config: Config) -> logging.Logger:
        """核心：根据配置初始化logger"""
        logger_config = config.logger
        logger = logging.getLogger(logger_config.name)
        logger.setLevel(logger_config.level.upper())
        logger.handlers.clear()  # 避免重复输出（生产环境关键）

        # 1. 配置文件处理器（生产环境核心）
        if logger_config.handlers.file:
            file_path = logger_config.handlers.file_path
            rotation_config = logger_config.rotation

            # 选择轮转方式：按时间/按大小
            if rotation_config.type == "time":
                file_handler = TimedRotatingFileHandler(
                    filename=file_path,
                    when=rotation_config.when,
                    interval=rotation_config.interval,
                    backupCount=rotation_config.backup_count,
                    encoding=logger_config.encoding
                )
            else:
                file_handler = RotatingFileHandler(
                    filename=file_path,
                    maxBytes=ProductionLogger._get_size_in_bytes(
                        rotation_config.max_size),
                    backupCount=rotation_config.backup_count,
                    encoding=logger_config.encoding
                )

            # 设置文件格式化器（JSON/文本）
            if logger_config.format.use_json:
                file_handler.setFormatter(JSONFormatter())
            else:
                file_handler.setFormatter(logging.Formatter(
                    logger_config.format.file))

            file_handler.setLevel(logger_config.level.upper())
            logger.addHandler(file_handler)

        # 2. 配置控制台处理器（仅开发环境）
        if logger_config.handlers.console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(ColoredFormatter(
                logger_config.format.console))
            console_handler.setLevel(logger_config.level.upper())
            logger.addHandler(console_handler)

        return logger

    @staticmethod
    def _get_size_in_bytes(size_str: str) -> int:
        """将大小字符串（如100MB）转换为字节（生产环境轮转关键）"""
        size_str = size_str.strip().upper()
        if size_str.endswith("MB"):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith("KB"):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith("GB"):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            raise ValueError(f"不支持的大小单位：{size_str}")

# 快捷函数：创建logger实例


def get_logger(
    env: str = "dev",
    config_file: Optional[Union[str, Path]] = None
) -> logging.Logger:
    """
    对外暴露的快捷函数（核心API）

    Args:
        env: 环境名称，可选值：dev/test/production，默认为 dev
        config_file: 可选的自定义配置文件路径（用于增量覆盖）

    Returns:
        配置完成的logger实例

    使用示例：
        # 使用 prod 环境默认配置
        logger = get_logger(env="prod")

        # 使用 dev 环境默认配置
        logger = get_logger(env="dev")

        # 使用 prod 环境 + 自定义配置
        logger = get_logger(env="prod", config_file="/etc/myapp/logging.yaml")
    """
    return ProductionLogger(env, config_file)
