import logging
import json
from datetime import datetime
from typing import Dict, Any


class ColoredFormatter(logging.Formatter):
    """开发环境彩色文本格式化器"""
    COLORS = {
        "DEBUG": "\033[0;36m",    # 青色
        "INFO": "\033[0;32m",     # 绿色
        "WARNING": "\033[0;33m",  # 黄色
        "ERROR": "\033[0;31m",    # 红色
        "CRITICAL": "\033[0;35m",  # 紫色
        "RESET": "\033[0m"        # 重置
    }

    def format(self, record: logging.LogRecord) -> str:
        log_msg = super().format(record)
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        return f"{color}{log_msg}{self.COLORS['RESET']}"


class JSONFormatter(logging.Formatter):
    """生产环境JSON结构化格式化器（核心）"""

    def format(self, record: logging.LogRecord) -> str:
        # 构建结构化日志字段（生产环境必备）
        log_data: Dict[str, Any] = {
            # 标准化时间
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "logger_name": record.name,
            "level": record.levelname,
            "file": record.filename,
            "line": record.lineno,
            "message": record.getMessage(),
            "process_id": record.process,
            "thread_id": record.thread
        }

        # 只在有意义时添加函数名（非模块级别调用）
        if record.funcName and record.funcName != "<module>":
            log_data["function"] = record.funcName

        # 异常信息（生产环境排障关键）
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)
