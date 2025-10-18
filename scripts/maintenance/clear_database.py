#!/usr/bin/env python3
"""
清空数据库所有数据

警告：此操作将删除所有表中的数据，但保留表结构！
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.db_config import get_db_cursor, DB_TYPE, SQLITE_DB_PATH


def clear_all_data():
    """清空所有表的数据"""

    print("=" * 60)
    print("⚠️  警告：即将清空数据库所有数据")
    print("=" * 60)
    print(f"\n数据库类型: {DB_TYPE.upper()}")

    if DB_TYPE == "sqlite":
        print(f"数据库文件: {Path(SQLITE_DB_PATH).absolute()}")

    print("\n将要清空以下表的数据：")
    print("  1. flfg_records (法律法规记录)")
    print("  2. comment_records (留言记录)")
    print("  3. tasks (任务记录)")

    # 询问确认
    confirm = input("\n确认要清空所有数据吗？输入 'YES' 继续: ")

    if confirm != "YES":
        print("\n❌ 操作已取消")
        return

    try:
        with get_db_cursor() as cursor:
            # 清空法律法规记录表
            print("\n🗑️  清空 flfg_records 表...")
            cursor.execute("DELETE FROM flfg_records")
            flfg_count = cursor.rowcount
            print(f"   ✓ 删除了 {flfg_count} 条记录")

            # 清空留言记录表
            print("\n🗑️  清空 comment_records 表...")
            cursor.execute("DELETE FROM comment_records")
            comment_count = cursor.rowcount
            print(f"   ✓ 删除了 {comment_count} 条记录")

            # 清空任务表
            print("\n🗑️  清空 tasks 表...")
            cursor.execute("DELETE FROM tasks")
            task_count = cursor.rowcount
            print(f"   ✓ 删除了 {task_count} 条记录")

            # 如果是 SQLite，尝试重置自增ID（如果存在）
            if DB_TYPE == "sqlite":
                try:
                    print("\n🔄 重置SQLite序列...")
                    cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('flfg_records', 'comment_records', 'tasks')")
                    print("   ✓ 序列已重置")
                except Exception:
                    # sqlite_sequence 表只在有自增字段时才存在，忽略错误
                    print("   ✓ 无需重置序列（表未使用自增ID）")

        print("\n" + "=" * 60)
        print("✅ 数据库清空完成！")
        print("=" * 60)
        print(f"\n统计：")
        print(f"  法律法规记录: {flfg_count} 条")
        print(f"  留言记录: {comment_count} 条")
        print(f"  任务记录: {task_count} 条")
        print(f"  总计: {flfg_count + comment_count + task_count} 条")

    except Exception as e:
        print(f"\n❌ 清空数据库时出错: {e}")
        import traceback
        traceback.print_exc()


def clear_table(table_name: str):
    """清空指定表的数据"""

    valid_tables = ["flfg_records", "comment_records", "tasks"]

    if table_name not in valid_tables:
        print(f"❌ 无效的表名: {table_name}")
        print(f"有效的表名: {', '.join(valid_tables)}")
        return

    print(f"\n⚠️  警告：即将清空表 '{table_name}' 的所有数据")
    confirm = input(f"确认要清空 '{table_name}' 吗？输入 'YES' 继续: ")

    if confirm != "YES":
        print("\n❌ 操作已取消")
        return

    try:
        with get_db_cursor() as cursor:
            cursor.execute(f"DELETE FROM {table_name}")
            count = cursor.rowcount
            print(f"\n✅ 成功清空表 '{table_name}'，删除了 {count} 条记录")
    except Exception as e:
        print(f"\n❌ 清空表时出错: {e}")


def show_stats():
    """显示数据库统计信息"""

    print("\n" + "=" * 60)
    print("📊 数据库统计信息")
    print("=" * 60)

    try:
        with get_db_cursor() as cursor:
            # 法律法规记录统计
            cursor.execute("SELECT COUNT(*) as total FROM flfg_records")
            flfg_total = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as total FROM flfg_records WHERE downloaded = 'Y'")
            flfg_downloaded = cursor.fetchone()['total']

            print(f"\n📚 法律法规记录 (flfg_records):")
            print(f"   总记录数: {flfg_total}")
            print(f"   已下载: {flfg_downloaded}")
            print(f"   未下载: {flfg_total - flfg_downloaded}")

            # 留言记录统计
            cursor.execute("SELECT COUNT(*) as total FROM comment_records")
            comment_total = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as total FROM comment_records WHERE downloaded = 'Y'")
            comment_downloaded = cursor.fetchone()['total']

            print(f"\n💬 留言记录 (comment_records):")
            print(f"   总记录数: {comment_total}")
            print(f"   已下载: {comment_downloaded}")
            print(f"   未下载: {comment_total - comment_downloaded}")

            # 任务记录统计
            cursor.execute("SELECT COUNT(*) as total FROM tasks")
            task_total = cursor.fetchone()['total']

            cursor.execute("SELECT status, COUNT(*) as count FROM tasks GROUP BY status")
            task_status = cursor.fetchall()

            print(f"\n📋 任务记录 (tasks):")
            print(f"   总任务数: {task_total}")
            for row in task_status:
                print(f"   {row['status']}: {row['count']}")

        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n❌ 获取统计信息时出错: {e}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='清空数据库数据工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  # 查看数据库统计
  python clear_database.py --stats

  # 清空所有表
  python clear_database.py --all

  # 清空指定表
  python clear_database.py --table flfg_records
  python clear_database.py --table comment_records
  python clear_database.py --table tasks
        """
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='显示数据库统计信息'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='清空所有表的数据'
    )

    parser.add_argument(
        '--table',
        type=str,
        choices=['flfg_records', 'comment_records', 'tasks'],
        help='清空指定表的数据'
    )

    args = parser.parse_args()

    # 如果没有提供任何参数，显示帮助
    if not (args.stats or args.all or args.table):
        parser.print_help()
        print("\n" + "=" * 60)
        show_stats()
        return

    # 显示统计信息
    if args.stats:
        show_stats()

    # 清空所有表
    elif args.all:
        clear_all_data()

    # 清空指定表
    elif args.table:
        clear_table(args.table)


if __name__ == "__main__":
    main()
