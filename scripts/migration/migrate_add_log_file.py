#!/usr/bin/env python3
"""
数据库迁移脚本：为tasks表添加log_file字段

这个脚本会：
1. 检查tasks表是否存在log_file字段
2. 如果不存在，添加该字段
3. 支持MySQL和SQLite两种数据库
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config.db_config import get_db_cursor, DB_TYPE


def add_log_file_column():
    """为tasks表添加log_file字段"""
    print(f"开始迁移数据库 ({DB_TYPE})...")

    try:
        with get_db_cursor() as cursor:
            # 检查字段是否已存在
            if DB_TYPE == "mysql":
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'tasks'
                    AND COLUMN_NAME = 'log_file'
                """)
                result = cursor.fetchone()
                exists = result['count'] > 0

                if not exists:
                    print("添加 log_file 字段到 tasks 表...")
                    cursor.execute("""
                        ALTER TABLE tasks
                        ADD COLUMN log_file VARCHAR(255) COMMENT '日志文件路径'
                        AFTER csv_path
                    """)
                    print("✅ MySQL: log_file 字段添加成功")
                else:
                    print("✓ log_file 字段已存在，跳过")

            elif DB_TYPE == "sqlite":
                # SQLite检查字段
                cursor.execute("PRAGMA table_info(tasks)")
                columns = cursor.fetchall()
                column_names = [col['name'] for col in columns]

                if 'log_file' not in column_names:
                    print("添加 log_file 字段到 tasks 表...")
                    cursor.execute("""
                        ALTER TABLE tasks
                        ADD COLUMN log_file VARCHAR(255)
                    """)
                    print("✅ SQLite: log_file 字段添加成功")
                else:
                    print("✓ log_file 字段已存在，跳过")

        print("\n✅ 数据库迁移完成！")
        return True

    except Exception as e:
        print(f"\n❌ 数据库迁移失败: {e}")
        return False


if __name__ == "__main__":
    success = add_log_file_column()
    sys.exit(0 if success else 1)
