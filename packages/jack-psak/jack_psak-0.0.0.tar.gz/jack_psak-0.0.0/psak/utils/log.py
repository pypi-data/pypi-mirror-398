import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
from typing import Optional, Dict, Any

def setup_logger(
    logger,
    log_dir: str = "./logs",
    log_file_name: Optional[str] = None,
    console_level: int = logging.INFO,
    file_level: int = logging.INFO,
    max_file_size: int = 100 * 1024 * 1024,  # 10MB
    backup_count: int = 5,  # 最多保留5个备份文件
    log_format: str = "[%(asctime)s] [%(levelname)s] [%(process)d:%(threadName)s] [%(filename)s:%(lineno)d] %(message)s",
    date_format: str = "%Y-%m-%d %H:%M:%S"
):

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logger.hasHandlers():
        print("logger has handlers")
        return

    if not log_file_name:
        today = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        log_file_name = f"{today}_app.log"
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, log_file_name)

    # 配置日志格式
    formatter = logging.Formatter(log_format, date_format)

    # 配置控制台Handler(输出到终端)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 配置文件Handler(支持轮转，避免单个文件过大)
    # RotatingFileHandler : 按文件大小轮转； TimedRotatingFileHandler : 按时间轮转(可按需替换)
    file_handler = RotatingFileHandler(
        filename=log_file_path,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding="utf-8"  # 支持中文日志
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


if __name__ == "__main__":
    # from accelerate.logging import get_logger
    # logger = get_logger(__name__).logger
    logger = logging.getLogger()
    setup_logger(logger)

    # 测试日志输出
    logger.debug("这是DEBUG级日志(文件可见，控制台默认不可见)")
    logger.info("这是INFO级日志(控制台+文件都可见)")
    logger.warning("这是WARNING级日志")
    logger.error("这是ERROR级日志")
    logger.critical("这是CRITICAL级日志")

    # 异常日志(自动记录堆栈信息)
    try:
        1 / 0
    except Exception as e:
        logger.error("发生异常：", exc_info=True)  # exc_info=True 记录堆栈
