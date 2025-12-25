import logging
import os


def get_logger(input_dir, log_name="app.log", mode="w", console=True, file=True):
    # 创建 Logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # 设置日志级别

    # 创建控制台 Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # 创建文件 Handler
    file_handler = logging.FileHandler(os.path.join(input_dir, log_name), mode=mode)
    file_handler.setLevel(logging.DEBUG)

    # 创建 Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 将 Formatter 添加到 Handler
    if console:
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    if file:
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger
