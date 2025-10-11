"""调度器：从CSV读取记录并调用chinatax_document_downloader下载文档。"""
from __future__ import annotations

import argparse
import asyncio
import csv
import sys
from pathlib import Path
from typing import List

from chinatax_document_downloader import scrape_document


def load_csv_records(csv_path: Path) -> List[dict]:
    """读取CSV文件并返回所有记录。"""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV文件不存在: {csv_path}")

    records = []
    with csv_path.open("r", encoding="utf-8", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = reader.fieldnames or []

        # 检查必要的列
        required_columns = ["序号", "标题", "发文字号", "成文日期", "链接"]
        missing_columns = [column for column in required_columns if column not in fieldnames]
        if missing_columns:
            raise ValueError(f"CSV 文件缺少必要的列: {', '.join(missing_columns)}")

        # 如果没有"是否下载"列，添加提示
        if "是否下载" not in fieldnames:
            print("警告: CSV文件缺少'是否下载'列，将视所有记录为未下载")

        for row in reader:
            records.append(row)

    return records


def update_csv_record(csv_path: Path, sequence_id: str, downloaded_status: str = "Y") -> None:
    """更新CSV中指定记录的下载状态。

    Args:
        csv_path: CSV文件路径
        sequence_id: 记录的序号(MD5)
        downloaded_status: 下载状态，默认为"Y"
    """
    if not csv_path.exists():
        return

    # 读取所有记录
    all_rows = []
    fieldnames = []
    with csv_path.open("r", encoding="utf-8", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = reader.fieldnames or []

        # 确保有"是否下载"列
        if "是否下载" not in fieldnames:
            fieldnames.append("是否下载")

        for row in reader:
            # 如果没有"是否下载"字段，添加默认值
            if "是否下载" not in row:
                row["是否下载"] = "N"

            # 更新匹配的记录
            if row["序号"] == sequence_id:
                row["是否下载"] = downloaded_status
                print(f"  更新记录 {sequence_id} 的下载状态为: {downloaded_status}")

            all_rows.append(row)

    # 写回CSV
    with csv_path.open("w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)


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
    csv_path = args.csv
    output_dir = args.output_dir
    headless = not args.headed

    print(f"正在读取CSV文件: {csv_path}")
    records = load_csv_records(csv_path)
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
            # 更新CSV状态
            update_csv_record(csv_path, record["序号"], "Y")
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
        description="调度器：从CSV读取记录并下载文档",
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
        "--csv",
        default="chinatax_flfg.csv",
        type=Path,
        help="CSV文件路径 (默认: chinatax_flfg.csv)",
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
