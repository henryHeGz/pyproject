#!/usr/bin/env python3
"""
模拟Web应用调用流程
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent))

from comments_scraper.chinatax_comments_scraper import scrape
from config.db_config import get_db_cursor
from config.csv_manager import get_csv_path
from pydantic import BaseModel


class CommentsScraperRequest(BaseModel):
    """留言爬虫请求参数"""
    start_page: int = 1
    max_pages: int = 1
    headless: bool = True
    auto_download: bool = False
    overwrite_db: bool = False


async def simulate_web_scrape():
    """模拟web_app.py中的run_comments_scraper函数"""

    # 创建任务
    task_id = f"comments_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    params = CommentsScraperRequest()

    print("=" * 60)
    print("模拟Web应用调用流程")
    print("=" * 60)
    print(f"\nTask ID: {task_id}")
    print(f"参数: {params.dict()}\n")

    # 保存初始任务状态到数据库
    task_data = {
        "task_id": task_id,
        "task_type": "留言爬虫",
        "task_category": "留言公开",
        "status": "running",
        "params": json.dumps(params.dict(), ensure_ascii=False),
        "start_time": datetime.now().isoformat(),
        "message": "任务启动中...",
        "result": None,
        "csv_path": None,
        "log_file": None,
        "error": None,
        "end_time": None
    }

    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO tasks (
                task_id, task_type, task_category, status, params,
                message, result, error, csv_path, log_file, start_time, end_time
            ) VALUES (
                %(task_id)s, %(task_type)s, %(task_category)s, %(status)s, %(params)s,
                %(message)s, %(result)s, %(error)s, %(csv_path)s, %(log_file)s, %(start_time)s, %(end_time)s
            )
        """, task_data)

    print("✓ 任务已保存到数据库\n")

    # 模拟run_comments_scraper函数的执行
    print("开始执行爬虫...")

    # 生成CSV文件路径
    csv_path = get_csv_path(f"comments_{task_id}")

    # 调用爬虫（这里是关键）
    new_count, actual_csv_path, all_records = await scrape(
        headless=params.headless,
        start_page=params.start_page,
        max_pages=params.max_pages,
        auto_download=params.auto_download,
        csv_path=str(csv_path),
        overwrite_db=params.overwrite_db
    )

    print(f"\n爬虫执行完成！")
    print(f"  返回值 new_count: {new_count}")
    print(f"  返回值 len(all_records): {len(all_records)}")
    print(f"  返回值 actual_csv_path: {actual_csv_path}")

    # 保存本次抓取的记录ID列表（模拟web_app.py line 774）
    record_ids = [r.id for r in all_records]

    # 生成更清晰的任务完成消息（模拟web_app.py lines 776-783）
    skipped_count = len(all_records) - new_count
    if new_count == 0 and len(all_records) > 0:
        message = f"任务完成！本次抓取 {len(all_records)} 条记录，全部为重复记录（数据库中已存在）"
    elif skipped_count > 0:
        message = f"任务完成！本次抓取 {len(all_records)} 条记录：新增 {new_count} 条，跳过 {skipped_count} 条重复记录"
    else:
        message = f"任务完成！新增 {new_count} 条记录"

    # 更新任务状态（模拟web_app.py lines 785-808）
    task_update = {
        "status": "completed",
        "message": message,
        "result": json.dumps({
            "new_records": new_count,
            "total_scraped": len(all_records),
            "skipped_records": skipped_count,
            "record_ids": record_ids
        }, ensure_ascii=False),
        "csv_path": actual_csv_path,
        "end_time": datetime.now().isoformat()
    }

    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE tasks
            SET status = %(status)s,
                message = %(message)s,
                result = %(result)s,
                csv_path = %(csv_path)s,
                end_time = %(end_time)s
            WHERE task_id = %(task_id)s
        """, {**task_update, 'task_id': task_id})

    print(f"\n✓ 任务状态已更新")
    print(f"  消息: {task_update['message']}")

    # 从数据库读回任务，看看存储的是什么
    print(f"\n从数据库读取任务信息...")
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM tasks WHERE task_id = %(task_id)s", {'task_id': task_id})
        saved_task = cursor.fetchone()

        print(f"  数据库中的消息: {saved_task['message']}")
        if saved_task.get('result'):
            result = json.loads(saved_task['result'])
            print(f"  数据库中的结果:")
            print(f"    new_records: {result['new_records']}")
            print(f"    total_scraped: {result['total_scraped']}")
            print(f"    record_ids数量: {len(result['record_ids'])}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(simulate_web_scrape())
