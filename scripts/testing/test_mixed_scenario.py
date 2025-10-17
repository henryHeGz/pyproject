#!/usr/bin/env python3
"""
测试混合场景：部分新记录，部分重复记录
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from comments_scraper.chinatax_comments_scraper import scrape
from config.db_config import get_db_cursor


async def test_mixed_scenario():
    """测试混合场景"""

    print("=" * 60)
    print("测试混合场景：部分新记录，部分重复记录")
    print("=" * 60)

    # 先清空数据库
    with get_db_cursor() as cursor:
        cursor.execute("DELETE FROM comment_records")
        print(f"\n清空数据库，删除了 {cursor.rowcount} 条记录")

    # 第一次：抓取第1页（20条）
    print("\n【第一次抓取】抓取第1页...")
    new_count1, _, records1 = await scrape(
        headless=True,
        start_page=1,
        max_pages=1,
        auto_download=False,
        csv_path=None,
        overwrite_db=False
    )
    print(f"结果：新增 {new_count1} 条")

    # 第二次：抓取第1-2页（40条，其中第1页的20条是重复的）
    print("\n【第二次抓取】抓取第1-2页...")
    new_count2, _, records2 = await scrape(
        headless=True,
        start_page=1,
        max_pages=2,
        auto_download=False,
        csv_path=None,
        overwrite_db=False
    )
    print(f"\n结果：新增 {new_count2} 条，本次抓取 {len(records2)} 条")
    print(f"预期：应该新增约20条（第2页的新记录），跳过约20条（第1页的重复记录）")

    # 检查数据库
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM comment_records")
        total = cursor.fetchone()['count']
        print(f"\n数据库最终记录数: {total}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_mixed_scenario())
