import io
import os
import logging
import sys
from io import TextIOWrapper
from pathlib import Path

from loguru import logger

from .config import BaseConfigLoader

init = False


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            # 正确处理格式化消息
            if record.args:
                # 如果有格式化参数，使用 getMessage() 来格式化
                try:
                    message = record.getMessage()
                except Exception:
                    message = record.msg % record.args if record.msg and record.args else str(record.msg)
            else:
                # 处理 Path 对象和其他非字符串消息
                if isinstance(record.msg, Path):
                    message = str(record.msg)
                else:
                    message = str(record.msg) if not isinstance(record.msg, str) else record.msg

            # 获取日志级别
            level = logger.level(record.levelname).name

            # 转发到 loguru
            logger_opt = logger.opt(depth=6, exception=record.exc_info)
            logger_opt.log(level, message)

        except Exception as e:
            # 如果处理失败，记录原始消息
            logger_opt = logger.opt(depth=6, exception=record.exc_info)
            logger_opt.log("ERROR", f"日志处理失败: {e}, 原始消息: {repr(record.msg)}, 参数: {repr(record.args)}")


def configure_logging(log_dir="logs", log_file="app.log", logger_level: str = "INFO"):
    global init
    if init:
        return
    init = True
    # 创建日志目录（如果不存在）
    log_path = os.path.join(os.getcwd(), log_dir)
    os.makedirs(log_path, exist_ok=True)

    # 构建完整日志文件路径
    full_log_path = os.path.join(log_path, log_file)

    # 清除所有默认处理器
    logger.remove()
    # 添加文件处理器，实现日志持久化
    encoding = "utf-8"
    logger.add(
        full_log_path,
        rotation="00:00",  # 每天零点自动创建新日志文件
        retention="7 days",  # 自动清理7天前的日志
        level="INFO",
        encoding=encoding,
        enqueue=True,  # 异步写入，提升性能
        backtrace=True,  # 显示完整异常堆栈
        diagnose=True  # 调试模式显示变量值.
    )

    # 添加错误日志专用文件
    error_log_path = os.path.join(log_path, log_file.rsplit(".")[0] + "_error.log")
    logger.add(
        error_log_path,
        rotation="1 week",
        retention="30 days",
        level="ERROR",
        encoding=encoding,
        enqueue=True
    )
    # 添加控制台输出处理器
    logger.add(
        sink=sys.stdout,
        level=logger_level,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    # 配置标准库logging模块，将日志重定向到loguru
    logging.basicConfig(handlers=[InterceptHandler()], level=logger_level)
    # 配置常见第三方库的日志级别
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    # 配置httpx日志级别为WARNING
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("f2").setLevel(logging.WARNING)
