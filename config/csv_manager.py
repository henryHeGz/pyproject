#!/usr/bin/env python3
"""
CSV文件管理工具
提供统一的CSV文件路径生成和管理功能
"""

import random
import string
from datetime import datetime
from pathlib import Path
from typing import Optional


# CSV文件存储目录（相对于项目根目录）
CSV_EXPORTS_DIR = Path(__file__).parent.parent / "csv_exports"


def ensure_csv_dir() -> Path:
    """
    确保CSV导出目录存在

    Returns:
        Path: CSV导出目录的路径对象
    """
    CSV_EXPORTS_DIR.mkdir(exist_ok=True)
    return CSV_EXPORTS_DIR


def generate_random_suffix(length: int = 4) -> str:
    """
    生成随机后缀（数字+字母）

    Args:
        length: 随机字符串长度，默认4位

    Returns:
        str: 随机字符串
    """
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_csv_filename(task_name: str, extension: str = ".csv") -> str:
    """
    生成CSV文件名
    格式：任务名_YYMMDDHHmmss_4位随机数.csv

    Args:
        task_name: 任务名称（如 flfg, comments, export等）
        extension: 文件扩展名，默认.csv

    Returns:
        str: 生成的文件名

    Examples:
        >>> generate_csv_filename("flfg")
        'flfg_20251017083045_a3f2.csv'
        >>> generate_csv_filename("comments")
        'comments_20251017083045_x9k1.csv'
    """
    timestamp = datetime.now().strftime("%y%m%d%H%M%S")
    random_suffix = generate_random_suffix(4)
    return f"{task_name}_{timestamp}_{random_suffix}{extension}"


def get_csv_path(task_name: str, extension: str = ".csv") -> Path:
    """
    获取完整的CSV文件路径
    自动创建目录并生成唯一文件名

    Args:
        task_name: 任务名称
        extension: 文件扩展名

    Returns:
        Path: 完整的CSV文件路径对象

    Examples:
        >>> path = get_csv_path("flfg")
        >>> print(path)
        /path/to/project/csv_exports/flfg_20251017083045_a3f2.csv
    """
    ensure_csv_dir()
    filename = generate_csv_filename(task_name, extension)
    return CSV_EXPORTS_DIR / filename


def list_csv_files(pattern: str = "*.csv") -> list[Path]:
    """
    列出所有CSV文件

    Args:
        pattern: 文件匹配模式，默认所有CSV文件

    Returns:
        list[Path]: CSV文件路径列表，按修改时间倒序排列
    """
    ensure_csv_dir()
    files = list(CSV_EXPORTS_DIR.glob(pattern))
    return sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)


def get_latest_csv(task_name: Optional[str] = None) -> Optional[Path]:
    """
    获取最新的CSV文件

    Args:
        task_name: 可选的任务名称，用于过滤特定任务的CSV文件

    Returns:
        Optional[Path]: 最新的CSV文件路径，如果不存在返回None
    """
    pattern = f"{task_name}_*.csv" if task_name else "*.csv"
    files = list_csv_files(pattern)
    return files[0] if files else None


if __name__ == "__main__":
    # 测试代码
    print("CSV Manager Test")
    print("=" * 50)

    # 测试目录创建
    csv_dir = ensure_csv_dir()
    print(f"CSV目录: {csv_dir}")

    # 测试文件名生成
    for task in ["flfg", "comments", "export"]:
        filename = generate_csv_filename(task)
        print(f"{task} 文件名: {filename}")

    # 测试路径生成
    path = get_csv_path("test")
    print(f"\n测试路径: {path}")

    # 创建测试文件
    path.write_text("test,data\n1,2\n", encoding="utf-8")
    print(f"创建测试文件: {path.name}")

    # 列出所有文件
    print(f"\nCSV文件列表:")
    for f in list_csv_files():
        print(f"  - {f.name}")

    # 获取最新文件
    latest = get_latest_csv("test")
    if latest:
        print(f"\n最新的test文件: {latest.name}")
