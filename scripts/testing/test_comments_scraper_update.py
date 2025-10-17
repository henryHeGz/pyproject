#!/usr/bin/env python3
"""
测试留言公开爬虫的新逻辑
"""

import asyncio
import sys
from pathlib import Path

# 添加父目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from comments_scraper.chinatax_comments_scraper import scrape


async def test_scraper():
    """测试爬虫新功能"""

    print("=" * 60)
    print("测试留言公开爬虫新逻辑")
    print("=" * 60)

    # 测试1: 爬取前2页，不自动下载，不覆盖数据库，生成CSV
    print("\n【测试1】爬取前2页，生成CSV，不覆盖数据库")
    print("-" * 60)

    csv_path = "test_comments_output.csv"
    new_count, actual_csv_path, all_records = await scrape(
        headless=True,
        start_page=1,
        max_pages=2,
        auto_download=False,
        csv_path=csv_path,
        overwrite_db=False
    )

    print(f"\n结果:")
    print(f"  新增记录数: {new_count}")
    print(f"  本次抓取总数: {len(all_records)}")
    print(f"  CSV文件路径: {actual_csv_path}")
    print(f"  CSV文件存在: {Path(actual_csv_path).exists() if actual_csv_path else False}")

    if all_records:
        print(f"\n前3条记录示例:")
        for i, record in enumerate(all_records[:3], 1):
            print(f"  [{i}] {record.question} | {record.date}")

    # 测试2: 再次爬取相同页面，测试覆盖模式
    print("\n\n【测试2】再次爬取相同页面，测试覆盖模式=True")
    print("-" * 60)

    csv_path2 = "test_comments_overwrite.csv"
    new_count2, actual_csv_path2, all_records2 = await scrape(
        headless=True,
        start_page=1,
        max_pages=2,
        auto_download=False,
        csv_path=csv_path2,
        overwrite_db=True
    )

    print(f"\n结果:")
    print(f"  新增记录数: {new_count2}")
    print(f"  本次抓取总数: {len(all_records2)}")
    print(f"  (覆盖模式下，应该大部分是更新而非新增)")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_scraper())
