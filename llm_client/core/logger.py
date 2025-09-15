import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_logger(log_config):
    log_dir = log_config.get('dir', 'logs')
    log_file = os.path.join(log_dir, log_config.get('filename', 'app.log'))
    
    # 文件日志级别
    file_log_level_str = log_config.get('level', 'INFO').upper()
    file_log_level = getattr(logging, file_log_level_str, logging.INFO)
    
    # [核心修改] 控制台日志级别
    console_log_level_str = log_config.get('console_level', 'WARNING').upper()
    console_log_level = getattr(logging, console_log_level_str, logging.WARNING)

    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger("LLM_APP")
    # 将logger的最低级别设置为两者中更低的那个，以确保所有消息都能被处理器接收
    logger.setLevel(min(file_log_level, console_log_level))

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # --- 控制台处理器 (使用新的 console_log_level) ---
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(console_log_level) # 应用控制台级别
    logger.addHandler(stream_handler)

    # --- 文件处理器 (使用旧的 file_log_level) ---
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(file_log_level) # 应用文件级别
    logger.addHandler(file_handler)
    
    return logger