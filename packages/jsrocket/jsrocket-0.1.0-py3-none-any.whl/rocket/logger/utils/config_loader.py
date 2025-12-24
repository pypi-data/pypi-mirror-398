import os
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path
from .config_models import Config


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    深度合并两个字典
    Args:
        base: 基础配置字典
        override: 覆盖配置字典
    Returns:
        合并后的字典
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(
    env: str = "dev",
    config_file: Optional[Union[str, Path]] = None
) -> Config:
    """
    加载配置文件，支持环境默认配置 + 增量覆盖

    Args:
        env: 环境名称，可选值：dev/test/production，默认为 dev
             每个环境都有对应的默认配置文件
        config_file: 可选的自定义配置文件路径，用于增量覆盖环境默认配置
                    可以是绝对路径或相对路径

    Returns:
        验证后的配置对象

    使用示例：
        # 使用 dev 环境默认配置
        config = load_config("dev")

        # 使用 test 环境默认配置
        config = load_config("test")

        # 使用 prod 环境默认配置 + 自定义增量配置
        config = load_config("prod", "/path/to/custom.yaml")

        # dev 环境 + 自定义增量配置
        config = load_config("dev", "my_config.yaml")
    """
    # 获取配置目录
    config_dir = Path(__file__).parent.parent / "config"

    # 1. 加载环境默认配置
    env_config_path = config_dir / f"{env}.yaml"
    if not env_config_path.exists():
        raise FileNotFoundError(
            f"环境配置文件 {env_config_path} 不存在。"
            f"支持的环境: dev, test, prod"
        )

    with open(env_config_path, "r", encoding="utf-8") as f:
        config_dict = yaml.safe_load(f)

    # 2. 如果提供了自定义配置文件，增量覆盖
    if config_file is not None:
        custom_path = Path(config_file)

        # 如果不是绝对路径，尝试相对于当前工作目录
        if not custom_path.is_absolute():
            custom_path = Path.cwd() / custom_path

        if not custom_path.exists():
            raise FileNotFoundError(f"自定义配置文件 {custom_path} 不存在")

        with open(custom_path, "r", encoding="utf-8") as f:
            custom_config = yaml.safe_load(f)

        # 深度合并：环境默认配置 + 自定义增量配置
        if custom_config:
            config_dict = _deep_merge(config_dict, custom_config)

    # 3. 使用 Pydantic 验证并填充默认值
    config = Config(**config_dict)

    # 4. 自动创建日志目录
    log_file_path = config.logger.handlers.file_path
    log_dir = Path(log_file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    return config
