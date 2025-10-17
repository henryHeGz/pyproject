#!/usr/bin/env python3
"""
任务日志管理模块

提供任务执行日志的文件管理功能：
- 为每个任务创建独立的日志文件
- 日志文件命名格式：{task_id}.log
- 所有日志文件存储在 task_logs/ 目录
- 提供日志写入和读取接口
"""

import logging
from pathlib import Path
from typing import Optional
from datetime import datetime


# 日志文件存储目录
TASK_LOGS_DIR = Path(__file__).parent / "task_logs"


def ensure_logs_dir() -> Path:
    """
    确保日志目录存在

    Returns:
        Path: 日志目录的路径对象
    """
    TASK_LOGS_DIR.mkdir(exist_ok=True)
    return TASK_LOGS_DIR


def get_log_file_path(task_id: str) -> Path:
    """
    获取任务日志文件路径

    Args:
        task_id: 任务ID

    Returns:
        Path: 日志文件的完整路径
    """
    ensure_logs_dir()
    return TASK_LOGS_DIR / f"{task_id}.log"


def create_task_logger(task_id: str, task_type: str = "") -> logging.Logger:
    """
    为任务创建专用的日志记录器

    Args:
        task_id: 任务ID
        task_type: 任务类型（可选，用于日志前缀）

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    log_file = get_log_file_path(task_id)

    # 创建logger
    logger = logging.getLogger(f"task_{task_id}")
    logger.setLevel(logging.INFO)

    # 清除已有的handlers（避免重复）
    logger.handlers.clear()

    # 创建文件handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='w')
    file_handler.setLevel(logging.INFO)

    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    # 添加handler到logger
    logger.addHandler(file_handler)

    # 写入任务开始信息
    logger.info("=" * 60)
    logger.info(f"任务开始: {task_type}")
    logger.info(f"任务ID: {task_id}")
    logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    return logger


def read_task_log(task_id: str, max_lines: Optional[int] = None) -> str:
    """
    读取任务日志内容

    Args:
        task_id: 任务ID
        max_lines: 最多读取的行数（None表示读取全部）

    Returns:
        str: 日志内容
    """
    log_file = get_log_file_path(task_id)

    if not log_file.exists():
        return f"日志文件不存在: {task_id}"

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            if max_lines:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line)
                return ''.join(lines)
            else:
                return f.read()
    except Exception as e:
        return f"读取日志失败: {str(e)}"


def append_to_log(task_id: str, message: str, level: str = "INFO") -> None:
    """
    向任务日志追加消息（简单方式，不使用logger对象）

    Args:
        task_id: 任务ID
        message: 日志消息
        level: 日志级别（INFO, WARNING, ERROR等）
    """
    log_file = get_log_file_path(task_id)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{timestamp} - [{level}] - {message}\n")


def finish_task_log(logger: logging.Logger, task_id: str, status: str = "completed") -> None:
    """
    完成任务日志记录

    Args:
        logger: 任务的日志记录器
        task_id: 任务ID
        status: 任务状态（completed/failed）
    """
    logger.info("=" * 60)
    logger.info(f"任务结束: {status.upper()}")
    logger.info(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # 关闭所有handlers
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)


def list_log_files() -> list[Path]:
    """
    列出所有任务日志文件

    Returns:
        list[Path]: 日志文件路径列表，按修改时间倒序排列
    """
    ensure_logs_dir()
    files = list(TASK_LOGS_DIR.glob("*.log"))
    return sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)


def get_log_file_info(task_id: str) -> dict:
    """
    获取日志文件信息

    Args:
        task_id: 任务ID

    Returns:
        dict: 日志文件信息（存在、大小、修改时间等）
    """
    log_file = get_log_file_path(task_id)

    if not log_file.exists():
        return {
            "exists": False,
            "path": str(log_file),
            "size": 0,
            "modified": None
        }

    stats = log_file.stat()
    return {
        "exists": True,
        "path": str(log_file),
        "size": stats.st_size,
        "size_kb": round(stats.st_size / 1024, 2),
        "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
        "line_count": sum(1 for _ in open(log_file, 'r', encoding='utf-8'))
    }


if __name__ == "__main__":
    # 测试代码
    print("Task Log Manager Test")
    print("=" * 50)

    # 测试目录创建
    logs_dir = ensure_logs_dir()
    print(f"日志目录: {logs_dir}")

    # 测试logger创建
    test_task_id = "test_task_20251017_001"
    logger = create_task_logger(test_task_id, "测试任务")

    # 写入一些日志
    logger.info("开始执行任务...")
    logger.info("正在处理第1页数据")
    logger.info("正在处理第2页数据")
    logger.warning("发现一条重复记录")
    logger.info("任务执行完成，共处理100条数据")

    # 完成日志
    finish_task_log(logger, test_task_id, "completed")

    # 读取日志
    print(f"\n读取日志内容:")
    print("-" * 50)
    content = read_task_log(test_task_id)
    print(content)

    # 获取日志信息
    info = get_log_file_info(test_task_id)
    print(f"\n日志文件信息:")
    print(f"  存在: {info['exists']}")
    print(f"  大小: {info['size_kb']} KB")
    print(f"  行数: {info['line_count']}")

    # 列出所有日志
    print(f"\n所有日志文件:")
    for log_file in list_log_files():
        print(f"  - {log_file.name}")
