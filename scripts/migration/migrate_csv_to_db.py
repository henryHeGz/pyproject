#!/usr/bin/env python3
"""
CSV数据迁移脚本

将现有的CSV文件数据迁移到MySQL数据库。
支持两种CSV格式：
1. chinatax_flfg.csv - 法律法规记录
2. chinatax_comments.csv - 留言记录
"""

import argparse
import csv
from pathlib import Path
from typing import List, Dict

from config.db_config import get_db_cursor, init_database


def migrate_flfg_csv(csv_path: Path) -> int:
    """
    迁移法律法规CSV数据到数据库

    Args:
        csv_path: CSV文件路径

    Returns:
        int: 成功迁移的记录数
    """
    if not csv_path.exists():
        print(f"❌ 文件不存在: {csv_path}")
        return 0

    print(f"📂 正在读取 {csv_path}...")

    records = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # 兼容不同的列名格式
            record = {
                "id": row.get("序号", "").strip(),
                "title": row.get("标题", "").strip(),
                "document_no": row.get("发文字号", "").strip(),
                "publish_date": row.get("成文日期", "").strip(),
                "link": row.get("链接", "").strip(),
                "downloaded": row.get("是否下载", "N").strip() or "N",
            }

            # 跳过空记录
            if not record["id"] or not record["title"]:
                continue

            records.append(record)

    print(f"✓ 读取到 {len(records)} 条记录")

    if not records:
        print("⚠️  没有有效记录需要迁移")
        return 0

    # 插入数据库
    print("💾 正在插入数据库...")
    success_count = 0
    error_count = 0

    try:
        with get_db_cursor() as cursor:
            for record in records:
                try:
                    cursor.execute("""
                        INSERT INTO flfg_records
                        (id, title, document_no, publish_date, link, downloaded)
                        VALUES (%(id)s, %(title)s, %(document_no)s, %(publish_date)s, %(link)s, %(downloaded)s)
                        ON DUPLICATE KEY UPDATE
                            title = VALUES(title),
                            document_no = VALUES(document_no),
                            publish_date = VALUES(publish_date),
                            link = VALUES(link),
                            downloaded = VALUES(downloaded),
                            updated_at = CURRENT_TIMESTAMP
                    """, record)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"  ⚠️  插入记录失败 [{record['id']}]: {e}")

        print(f"✅ 成功迁移 {success_count} 条记录")
        if error_count > 0:
            print(f"⚠️  失败 {error_count} 条记录")

    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
        return 0

    return success_count


def migrate_comments_csv(csv_path: Path) -> int:
    """
    迁移留言CSV数据到数据库

    Args:
        csv_path: CSV文件路径

    Returns:
        int: 成功迁移的记录数
    """
    if not csv_path.exists():
        print(f"❌ 文件不存在: {csv_path}")
        return 0

    print(f"📂 正在读取 {csv_path}...")

    records = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # 兼容不同的列名格式
            record = {
                "id": row.get("id", "").strip(),
                "question": row.get("留言问题", "").strip(),
                "date": row.get("日期", "").strip(),
                "link": row.get("链接地址", row.get("链接", "")).strip(),
                "downloaded": row.get("是否下载", "N").strip() or "N",
                "question_content": row.get("问", "").strip(),
                "answer_content": row.get("答", "").strip(),
            }

            # 跳过空记录
            if not record["id"] or not record["question"]:
                continue

            records.append(record)

    print(f"✓ 读取到 {len(records)} 条记录")

    if not records:
        print("⚠️  没有有效记录需要迁移")
        return 0

    # 插入数据库
    print("💾 正在插入数据库...")
    success_count = 0
    error_count = 0

    try:
        with get_db_cursor() as cursor:
            for record in records:
                try:
                    cursor.execute("""
                        INSERT INTO comment_records
                        (id, question, date, link, downloaded, question_content, answer_content)
                        VALUES (%(id)s, %(question)s, %(date)s, %(link)s, %(downloaded)s,
                                %(question_content)s, %(answer_content)s)
                        ON DUPLICATE KEY UPDATE
                            question = VALUES(question),
                            date = VALUES(date),
                            link = VALUES(link),
                            downloaded = VALUES(downloaded),
                            question_content = VALUES(question_content),
                            answer_content = VALUES(answer_content),
                            updated_at = CURRENT_TIMESTAMP
                    """, record)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"  ⚠️  插入记录失败 [{record['id']}]: {e}")

        print(f"✅ 成功迁移 {success_count} 条记录")
        if error_count > 0:
            print(f"⚠️  失败 {error_count} 条记录")

    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
        return 0

    return success_count


def main():
    parser = argparse.ArgumentParser(
        description="CSV数据迁移到MySQL数据库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 初始化数据库并迁移所有CSV文件
  python migrate_csv_to_db.py --init --all

  # 只迁移法律法规CSV
  python migrate_csv_to_db.py --flfg chinatax_flfg.csv

  # 只迁移留言CSV
  python migrate_csv_to_db.py --comments chinatax_comments.csv

  # 迁移指定目录下的所有CSV文件
  python migrate_csv_to_db.py --flfg flfg_scraper/chinatax_flfg.csv --comments comments_scraper/chinatax_comments.csv
        """
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="初始化数据库（创建表结构）"
    )
    parser.add_argument(
        "--flfg",
        type=Path,
        help="法律法规CSV文件路径"
    )
    parser.add_argument(
        "--comments",
        type=Path,
        help="留言CSV文件路径"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="迁移所有默认CSV文件（chinatax_flfg.csv, chinatax_comments.csv）"
    )

    args = parser.parse_args()

    # 初始化数据库
    if args.init:
        print("🚀 正在初始化数据库...\n")
        init_database()
        print()

    # 如果指定了 --all，使用默认路径
    if args.all:
        args.flfg = Path("chinatax_flfg.csv")
        args.comments = Path("chinatax_comments.csv")

    # 检查是否有任务
    if not args.flfg and not args.comments:
        print("❌ 请指定要迁移的CSV文件（--flfg 或 --comments）或使用 --all 迁移所有文件")
        print("使用 -h 查看帮助信息")
        return

    total_migrated = 0

    # 迁移法律法规数据
    if args.flfg:
        print(f"\n{'='*60}")
        print("📋 迁移法律法规数据")
        print(f"{'='*60}\n")
        count = migrate_flfg_csv(args.flfg)
        total_migrated += count

    # 迁移留言数据
    if args.comments:
        print(f"\n{'='*60}")
        print("💬 迁移留言数据")
        print(f"{'='*60}\n")
        count = migrate_comments_csv(args.comments)
        total_migrated += count

    print(f"\n{'='*60}")
    print(f"🎉 迁移完成！共迁移 {total_migrated} 条记录")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
