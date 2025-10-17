#!/usr/bin/env python3
"""
快速验证修复效果的脚本
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from comments_scraper.chinatax_comments_scraper import scrape
from config.db_config import get_db_cursor


async def verify_fix():
    """验证修复效果"""

    print("=" * 70)
    print(" " * 20 + "留言爬虫修复效果验证")
    print("=" * 70)

    # 检查数据库状态
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM comment_records")
        db_count = cursor.fetchone()['count']

    print(f"\n当前数据库中有 {db_count} 条留言记录")

    if db_count == 0:
        print("\n【场景1】数据库为空，首次抓取")
        print("-" * 70)
    else:
        print(f"\n【场景2】数据库已有 {db_count} 条记录，重复抓取测试")
        print("-" * 70)

    # 运行爬虫（只抓取1页用于快速测试）
    print("\n开始抓取第1页（共20条记录）...\n")

    new_count, csv_path, all_records = await scrape(
        headless=True,
        start_page=1,
        max_pages=1,
        auto_download=False,
        csv_path=None,
        overwrite_db=False
    )

    # 显示结果
    print("\n" + "=" * 70)
    print(" " * 25 + "抓取结果汇总")
    print("=" * 70)
    print(f"\n本次抓取记录数: {len(all_records)} 条")
    print(f"新增记录数:     {new_count} 条")
    print(f"重复记录数:     {len(all_records) - new_count} 条")

    # 检查最终数据库状态
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM comment_records")
        final_count = cursor.fetchone()['count']

    print(f"\n数据库总记录数: {final_count} 条")

    # 显示消息示例
    skipped_count = len(all_records) - new_count
    if new_count == 0 and len(all_records) > 0:
        message = f"任务完成！本次抓取 {len(all_records)} 条记录，全部为重复记录（数据库中已存在）"
    elif skipped_count > 0:
        message = f"任务完成！本次抓取 {len(all_records)} 条记录：新增 {new_count} 条，跳过 {skipped_count} 条重复记录"
    else:
        message = f"任务完成！新增 {new_count} 条记录"

    print("\n" + "-" * 70)
    print("Web界面将显示的消息:")
    print(f"  {message}")
    print("-" * 70)

    # 给出建议
    print("\n💡 说明:")
    if new_count == 0:
        print("  - 新增为0是因为这些记录已经存在于数据库中")
        print("  - 这是正常的去重行为，不是bug")
        print("  - 如需抓取新数据，请使用 start_page 参数跳过已抓取的页面")
    else:
        print("  - 爬虫正常工作，成功添加了新记录")
        print("  - 去重机制正常，跳过了重复记录")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(verify_fix())
