"""
日志配置模块

提供统一的日志配置，支持：
- 文件日志（带轮转）
- 控制台日志
- 日志级别控制
- 异常堆栈追踪
- 线程 ID 显示
- 自动清理旧日志（P1 修复）
"""
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from logging.handlers import RotatingFileHandler


# 日志格式 - 添加线程 ID
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | Thread-%(thread)d | %(message)s"
LOG_FORMAT_DEBUG = "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s:%(lineno)d | Thread-%(thread)d | %(funcName)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 日志轮转配置
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5  # 保留 5 个旧日志文件


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    console_output: bool = True,
    debug_mode: bool = False,
    use_rotating: bool = True,  # 是否使用日志轮转
    max_bytes: int = LOG_MAX_BYTES,
    backup_count: int = LOG_BACKUP_COUNT
) -> logging.Logger:
    """
    设置日志配置

    Args:
        log_level: 日志级别
        log_file: 日志文件路径（None 表示不写入文件）
        console_output: 是否输出到控制台
        debug_mode: 调试模式（显示更详细信息）
        use_rotating: 是否使用日志轮转（默认 True）
        max_bytes: 单个日志文件最大字节数（默认 10MB）
        backup_count: 保留的旧日志文件数量（默认 5 个）

    Returns:
        根日志记录器
    """
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除已有的处理器
    root_logger.handlers.clear()

    # 设置格式
    if debug_mode:
        formatter = logging.Formatter(
            LOG_FORMAT_DEBUG,
            datefmt=DATE_FORMAT
        )
    else:
        formatter = logging.Formatter(
            LOG_FORMAT,
            datefmt=DATE_FORMAT
        )

    # 控制台处理器
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        if use_rotating:
            # 使用轮转文件处理器
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        else:
            # 使用普通文件处理器
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

    # 捕获异常堆栈
    logging.basicConfig(
        level=log_level,
        handlers=root_logger.handlers
    )

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    获取命名日志记录器
    
    Args:
        name: 日志记录器名称（通常是模块名）
    
    Returns:
        日志记录器
    """
    return logging.getLogger(name)


def get_log_path() -> Path:
    """
    获取默认日志文件路径
    
    Returns:
        日志目录路径
    """
    # 在应用目录下创建 logs 文件夹
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        base_path = Path(sys.executable).parent
    else:
        # 开发环境
        base_path = Path(__file__).parent.parent
    
    log_dir = base_path / "logs"
    log_dir.mkdir(exist_ok=True)
    
    return log_dir


def create_log_filename(prefix: str = "edge-client") -> str:
    """
    创建带时间戳的日志文件名

    Args:
        prefix: 文件名前缀

    Returns:
        日志文件路径
    """
    log_dir = get_log_path()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.log"
    return str(log_dir / filename)


def cleanup_old_logs(log_dir: Optional[str] = None, max_total_size: int = 100 * 1024 * 1024):
    """
    P1 修复：清理旧日志文件，确保日志目录总大小不超过限制
    
    Args:
        log_dir: 日志目录路径（None 则使用默认目录）
        max_total_size: 日志目录最大总字节数（默认 100MB）
    """
    if log_dir is None:
        log_dir = get_log_path()
    
    log_path = Path(log_dir)
    if not log_path.exists():
        return
    
    # 获取所有日志文件
    log_files = list(log_path.glob("*.log"))
    if not log_files:
        return
    
    # 计算总大小
    total_size = sum(f.stat().st_size for f in log_files)
    
    if total_size <= max_total_size:
        return  # 不需要清理
    
    # 按修改时间排序（最旧的在前）
    log_files.sort(key=lambda f: f.stat().st_mtime)
    
    # 删除最旧的日志文件，直到总大小 < max_total_size
    for log_file in log_files:
        if total_size <= max_total_size:
            break
        
        file_size = log_file.stat().st_size
        try:
            log_file.unlink()
            total_size -= file_size
            print(f"[日志清理] 已删除旧日志：{log_file.name}")
        except Exception as e:
            print(f"[日志清理] 删除失败：{log_file.name} - {e}")


def get_log_directory_size(log_dir: Optional[str] = None) -> int:
    """
    获取日志目录总大小
    
    Args:
        log_dir: 日志目录路径（None 则使用默认目录）
    
    Returns:
        总大小（字节）
    """
    if log_dir is None:
        log_dir = get_log_path()
    
    log_path = Path(log_dir)
    if not log_path.exists():
        return 0
    
    return sum(f.stat().st_size for f in log_path.glob("*.log"))


# 快捷函数
def log_debug(logger: logging.Logger, message: str):
    """记录 DEBUG 日志"""
    logger.debug(message)


def log_info(logger: logging.Logger, message: str):
    """记录 INFO 日志"""
    logger.info(message)


def log_warning(logger: logging.Logger, message: str):
    """记录 WARNING 日志"""
    logger.warning(message)


def log_error(logger: logging.Logger, message: str, exc_info: bool = True):
    """
    记录 ERROR 日志
    
    Args:
        logger: 日志记录器
        message: 日志消息
        exc_info: 是否记录异常堆栈
    """
    logger.error(message, exc_info=exc_info)


def log_critical(logger: logging.Logger, message: str, exc_info: bool = True):
    """
    记录 CRITICAL 日志
    
    Args:
        logger: 日志记录器
        message: 日志消息
        exc_info: 是否记录异常堆栈
    """
    logger.critical(message, exc_info=exc_info)
