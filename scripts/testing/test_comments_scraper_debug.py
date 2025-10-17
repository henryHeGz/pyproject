#!/usr/bin/env python3
"""
调试留言爬虫 - 找出新增计数为0的问题
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from comments_scraper.chinatax_comments_scraper import scrape, load_existing_ids
from config.db_config import get_db_cursor


async def debug_scrape():
    """运行爬虫并详细输出调试信息"""

    print("=" * 60)
    print("调试留言爬虫")
    print("=" * 60)

    # 检查数据库初始状态
    print("\n1. 检查数据库初始状态")
    existing_ids = load_existing_ids()
    print(f"   现有记录数: {len(existing_ids)}")

    # 运行爬虫
    print("\n2. 运行爬虫（抓取1页）")
    new_count, csv_path, all_records = await scrape(
        headless=True,
        start_page=1,
        max_pages=1,
        auto_download=False,
        csv_path=None,
        overwrite_db=False
    )

    print(f"\n3. 爬虫返回结果")
    print(f"   new_count (新增记录数): {new_count}")
    print(f"   len(all_records) (本次抓取总数): {len(all_records)}")
    print(f"   csv_path: {csv_path}")

    # 检查数据库最终状态
    print("\n4. 检查数据库最终状态")
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM comment_records")
        total = cursor.fetchone()['count']
        print(f"   数据库中总记录数: {total}")

        cursor.execute("SELECT COUNT(*) as count FROM comment_records WHERE downloaded = 'N'")
        not_downloaded = cursor.fetchone()['count']
        print(f"   未下载记录数: {not_downloaded}")

        cursor.execute("SELECT COUNT(*) as count FROM comment_records WHERE downloaded = 'Y'")
        downloaded = cursor.fetchone()['count']
        print(f"   已下载记录数: {downloaded}")

    # 分析结果
    print("\n5. 结果分析")
    if new_count == 0 and len(all_records) > 0:
        print("   ❌ BUG确认: 抓取了记录但new_count为0")
        print(f"   应该显示: 新增 {total} 条")
        print(f"   实际显示: 新增 {new_count} 条")
    elif new_count == total:
        print(f"   ✅ 正确: 新增记录数 {new_count} 与数据库记录数 {total} 一致")
    else:
        print(f"   ⚠️  异常: new_count={new_count}, total={total}, 不一致")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(debug_scrape())
