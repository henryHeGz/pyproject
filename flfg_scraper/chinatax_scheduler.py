"""调度器：从数据库读取记录并调用chinatax_document_downloader下载文档。"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import List

# 添加父目录到 Python 路径以导入 db_config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.db_config import get_db_cursor
from chinatax_document_downloader import scrape_document


def load_all_records() -> List[dict]:
    """从数据库读取所有记录"""
    records = []
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT id as 序号, title as 标题, document_no as 发文字号,
                       publish_date as 成文日期, link as 链接, downloaded as 是否下载
                FROM flfg_records
                ORDER BY created_at DESC
            """)
            records = cursor.fetchall()
    except Exception as e:
        print(f"❌ 读取数据库记录时出错: {e}")
    return records


def update_record_status(record_id: str, downloaded_status: str = "Y") -> None:
    """更新数据库中指定记录的下载状态

    Args:
        record_id: 记录的序号(MD5)
        downloaded_status: 下载状态，默认为"Y"
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE flfg_records
                SET downloaded = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (downloaded_status, record_id))
            print(f"  更新记录 {record_id} 的下载状态为: {downloaded_status}")
    except Exception as e:
        print(f"❌ 更新记录状态时出错: {e}")


def filter_records_by_ids(records: List[dict], ids: List[str]) -> List[dict]:
    """根据ID列表过滤记录。"""
    return [record for record in records if record["序号"] in ids]


def filter_records_not_downloaded(records: List[dict]) -> List[dict]:
    """过滤出未下载的记录。"""
    return [
        record for record in records
        if record.get("是否下载", "N").upper() != "Y"
    ]


async def download_record(record: dict, output_dir: Path, headless: bool = True) -> bool:
    """下载单条记录。

    Args:
        record: 记录字典
        output_dir: 输出目录
        headless: 是否无头模式运行浏览器

    Returns:
        是否下载成功
    """
    url = record.get("链接", "")
    if not url:
        print(f"记录 {record['序号']} 没有链接，跳过")
        return False

    print(f"\n{'='*60}")
    print(f"开始下载:")
    print(f"  序号: {record['序号']}")
    print(f"  标题: {record['标题']}")
    print(f"  发文字号: {record['发文字号']}")
    print(f"  成文日期: {record['成文日期']}")
    print(f"  链接: {url}")
    print(f"{'='*60}\n")

    try:
        folder_path = await scrape_document(
            url=url,
            base_output_dir=output_dir,
            headless=headless
        )
        print(f"\n✓ 下载成功! 文件保存在: {folder_path}\n")
        return True
    except Exception as e:
        print(f"\n✗ 下载失败: {str(e)}\n")
        return False


async def async_main(args: argparse.Namespace) -> None:
    """主函数。"""
    output_dir = args.output_dir
    headless = not args.headed

    print(f"正在读取数据库记录...")
    records = load_all_records()
    print(f"共读取 {len(records)} 条记录")

    # 根据参数过滤记录
    if args.ids:
        id_list = [id.strip() for id in args.ids.split(",")]
        records = filter_records_by_ids(records, id_list)
        print(f"根据ID列表过滤后剩余 {len(records)} 条记录")
    elif args.not_downloaded:
        records = filter_records_not_downloaded(records)
        print(f"过滤出 {len(records)} 条未下载的记录")
    else:
        # 默认只下载第一条未下载的记录
        records = filter_records_not_downloaded(records)
        if records:
            records = [records[0]]
            print(f"默认模式：下载第一条未下载的记录")
        else:
            print("没有未下载的记录")
            return

    if not records:
        print("没有符合条件的记录需要下载")
        return

    # 限制下载数量
    if args.limit:
        records = records[:args.limit]
        print(f"限制下载数量为 {args.limit} 条")

    # 逐条下载
    success_count = 0
    fail_count = 0

    for i, record in enumerate(records, 1):
        print(f"\n进度: {i}/{len(records)}")

        success = await download_record(record, output_dir, headless)

        if success:
            success_count += 1
            # 更新数据库状态
            update_record_status(record["序号"], "Y")
        else:
            fail_count += 1
            # 如果设置了fail-on-error，则停止
            if args.fail_on_error:
                print("\n遇到错误，停止下载")
                break

    print(f"\n{'='*60}")
    print(f"下载完成!")
    print(f"  成功: {success_count} 条")
    print(f"  失败: {fail_count} 条")
    print(f"{'='*60}\n")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="调度器：从数据库读取记录并下载文档",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 下载第一条未下载的记录（默认）
  python chinatax_scheduler.py

  # 下载所有未下载的记录
  python chinatax_scheduler.py --not-downloaded

  # 下载前5条未下载的记录
  python chinatax_scheduler.py --not-downloaded --limit 5

  # 根据ID下载指定记录
  python chinatax_scheduler.py --ids "abc123,def456,ghi789"

  # 指定输出目录
  python chinatax_scheduler.py --output-dir ./downloads --not-downloaded
        """
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        type=Path,
        help="输出目录 (默认: 当前目录)",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="以可视化模式运行浏览器，便于调试",
    )
    parser.add_argument(
        "--ids",
        type=str,
        help="要下载的记录ID列表（用逗号分隔），例如: abc123,def456",
    )
    parser.add_argument(
        "--not-downloaded",
        action="store_true",
        help="下载所有未下载的记录（是否下载字段为N）",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="限制下载数量",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="遇到下载错误时停止",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
