#!/usr/bin/env python3
"""
迁移旧的CSV文件到csv_exports目录

这个脚本会：
1. 查找项目根目录的所有CSV文件
2. 将它们移动到 csv_exports/ 目录
3. 为每个文件添加时间戳和随机后缀
"""

import sys
from pathlib import Path
from datetime import datetime
import shutil

# 确保可以导入 csv_manager
sys.path.insert(0, str(Path(__file__).parent))

from config.csv_manager import CSV_EXPORTS_DIR, ensure_csv_dir, generate_random_suffix

def migrate_csv_files():
    """迁移根目录的CSV文件到csv_exports目录"""
    ensure_csv_dir()

    root_dir = Path(__file__).parent
    csv_files = list(root_dir.glob("*.csv"))

    if not csv_files:
        print("✅ 没有发现需要迁移的CSV文件")
        return

    print(f"发现 {len(csv_files)} 个CSV文件需要迁移:\n")

    for csv_file in csv_files:
        # 跳过已经在csv_exports目录的文件
        if csv_file.parent == CSV_EXPORTS_DIR:
            continue

        # 生成新的文件名
        original_name = csv_file.stem  # 不含扩展名的文件名
        timestamp = datetime.now().strftime("%y%m%d%H%M%S")
        random_suffix = generate_random_suffix(4)
        new_name = f"{original_name}_{timestamp}_{random_suffix}.csv"
        new_path = CSV_EXPORTS_DIR / new_name

        # 移动文件
        print(f"  移动: {csv_file.name}")
        print(f"    -> {new_path.name}")
        shutil.move(str(csv_file), str(new_path))

    print(f"\n✅ 成功迁移 {len(csv_files)} 个CSV文件到 csv_exports/")

if __name__ == "__main__":
    try:
        migrate_csv_files()
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        sys.exit(1)
