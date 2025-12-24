"""
Pydantic 配置模型
提供类型验证和默认值支持
"""
from typing import Optional
from pydantic import BaseModel, Field


class RotationConfig(BaseModel):
    """日志轮转配置"""
    type: str = Field(default="time", description="轮转类型: time 或 size")
    when: str = Field(default="midnight", description="时间轮转的触发时机")
    interval: int = Field(default=1, description="轮转间隔")
    backup_count: int = Field(default=7, description="保留的备份文件数量")
    max_size: str = Field(default="100MB", description="按大小轮转时的文件上限")


class HandlersConfig(BaseModel):
    """日志处理器配置"""
    console: bool = Field(default=True, description="是否输出到控制台")
    file: bool = Field(default=True, description="是否输出到文件")
    file_path: str = Field(default="logs/dev/app.log", description="日志文件路径")


class FormatConfig(BaseModel):
    """日志格式配置"""
    console: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        description="控制台输出格式"
    )
    file: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        description="文件输出格式"
    )
    use_json: bool = Field(default=False, description="是否使用JSON格式", alias="json")


class LoggerConfig(BaseModel):
    """日志器配置"""
    name: str = Field(default="app-dev", description="日志器名称")
    level: str = Field(default="DEBUG", description="日志级别")
    encoding: str = Field(default="utf-8", description="文件编码")
    rotation: RotationConfig = Field(default_factory=RotationConfig, description="轮转配置")
    handlers: HandlersConfig = Field(default_factory=HandlersConfig, description="处理器配置")
    format: FormatConfig = Field(default_factory=FormatConfig, description="格式配置")


class Config(BaseModel):
    """完整配置模型"""
    logger: LoggerConfig = Field(default_factory=LoggerConfig, description="日志配置")
    
    class Config:
        """Pydantic 配置"""
        # 允许额外字段（向后兼容）
        extra = "allow"
