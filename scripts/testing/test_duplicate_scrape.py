#!/usr/bin/env python3
"""
测试：在数据库已有记录的情况下运行爬虫
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from comments_scraper.chinatax_comments_scraper import scrape, load_existing_ids
from config.db_config import get_db_cursor


async def test_duplicate_scrape():
    """测试重复抓取的情况"""

    print("=" * 60)
    print("测试重复抓取（数据库已有数据）")
    print("=" * 60)

    # 检查数据库初始状态
    print("\n【第一次运行前】数据库状态:")
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM comment_records")
        initial_count = cursor.fetchone()['count']
        print(f"  数据库记录数: {initial_count}")

    if initial_count == 0:
        print("\n  数据库为空，先运行一次爬虫...")
        new_count1, _, records1 = await scrape(
            headless=True,
            start_page=1,
            max_pages=1,
            auto_download=False,
            csv_path=None,
            overwrite_db=False
        )
        print(f"  第一次结果: 新增 {new_count1} 条，抓取 {len(records1)} 条")

    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM comment_records")
        count_after_first = cursor.fetchone()['count']
        print(f"\n【第一次运行后】数据库记录数: {count_after_first}")

    # 再次运行爬虫（抓取相同的数据）
    print("\n" + "=" * 60)
    print("第二次运行爬虫（抓取相同页面）")
    print("=" * 60 + "\n")

    new_count2, _, records2 = await scrape(
        headless=True,
        start_page=1,
        max_pages=1,
        auto_download=False,
        csv_path=None,
        overwrite_db=False
    )

    print(f"\n【第二次结果】")
    print(f"  new_count (新增): {new_count2}")
    print(f"  len(all_records) (本次抓取): {len(records2)}")

    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM comment_records")
        final_count = cursor.fetchone()['count']
        print(f"  数据库记录数: {final_count}")

    print(f"\n【分析】")
    if new_count2 == 0:
        print(f"  ✓ 符合预期: 重复抓取时new_count为0（因为都是已存在的记录）")
        print(f"  本次抓取了 {len(records2)} 条记录，但都已存在于数据库")
        print(f"  ⚠️  这就是你看到的'新增数据是0'的原因！")
    else:
        print(f"  异常: new_count应该为0，但实际是{new_count2}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_duplicate_scrape())
