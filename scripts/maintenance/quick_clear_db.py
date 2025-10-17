#!/usr/bin/env python3
"""
快速清空数据库脚本（无需确认）

⚠️ 警告：此脚本会直接清空所有数据，不会询问确认！
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.db_config import get_db_cursor, DB_TYPE


def quick_clear():
    """快速清空所有数据"""

    print("🗑️  正在清空数据库...")

    try:
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM flfg_records")
            flfg_count = cursor.rowcount

            cursor.execute("DELETE FROM comment_records")
            comment_count = cursor.rowcount

            cursor.execute("DELETE FROM tasks")
            task_count = cursor.rowcount

        print(f"✅ 清空完成！删除了 {flfg_count + comment_count + task_count} 条记录")
        print(f"   法律法规: {flfg_count} | 留言: {comment_count} | 任务: {task_count}")

    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    quick_clear()
