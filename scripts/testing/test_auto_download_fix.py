#!/usr/bin/env python3
"""
测试自动下载功能修复
验证：抓取1页时，自动下载只下载本次新抓取的记录，而不是数据库中所有未下载的记录
"""
import asyncio
from comments_scraper.chinatax_comments_scraper import scrape
from config.db_config import get_db_cursor


async def test_auto_download():
    """测试自动下载功能"""

    # 先查看数据库状态
    print("=" * 60)
    print("数据库当前状态：")
    print("=" * 60)

    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM comment_records")
        total = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM comment_records WHERE downloaded = 'N'")
        not_downloaded = cursor.fetchone()['count']

        print(f"总记录数: {total}")
        print(f"未下载记录数: {not_downloaded}")
        print(f"已下载记录数: {total - not_downloaded}")

    print("\n" + "=" * 60)
    print("开始测试：抓取第1页，启用自动下载")
    print("=" * 60 + "\n")

    # 执行抓取（第1页，启用自动下载）
    new_count = await scrape(
        headless=True,
        start_page=1,
        max_pages=1,
        auto_download=True
    )

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    print(f"本次新增记录数: {new_count}")

    # 再次查看数据库状态
    print("\n数据库更新后状态：")
    print("=" * 60)

    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM comment_records")
        total_after = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM comment_records WHERE downloaded = 'N'")
        not_downloaded_after = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM comment_records WHERE downloaded = 'Y'")
        downloaded_after = cursor.fetchone()['count']

        print(f"总记录数: {total_after}")
        print(f"未下载记录数: {not_downloaded_after}")
        print(f"已下载记录数: {downloaded_after}")

        print(f"\n变化：")
        print(f"新增记录: {total_after - total}")
        print(f"新下载记录: {downloaded_after - (total - not_downloaded)}")

    print("\n" + "=" * 60)
    print("验证结果：")
    print("=" * 60)

    if new_count == 0:
        print("✅ 第1页全部为重复记录，没有新增")
        print("✅ 自动下载没有执行（因为没有新记录）")
    else:
        # 计算新下载的数量
        new_downloaded = downloaded_after - (total - not_downloaded)
        if new_downloaded == new_count:
            print(f"✅ 成功！只下载了本次新抓取的 {new_count} 条记录")
            print(f"✅ 没有下载数据库中的其他 {not_downloaded_after} 条未下载记录")
        else:
            print(f"❌ 失败！预期下载 {new_count} 条，实际下载 {new_downloaded} 条")


if __name__ == "__main__":
    asyncio.run(test_auto_download())
