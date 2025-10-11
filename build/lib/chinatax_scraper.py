"""Scrape the 国家税务总局法规库法律法规列表 using Playwright."""
from __future__ import annotations

import argparse
import asyncio
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, List, Set, Tuple

if TYPE_CHECKING:  # pragma: no cover - used only for type hints
    from playwright.async_api import Browser, Page

BASE_URL = "https://fgk.chinatax.gov.cn/zcfgk/c100012/listflfg.html"
CSV_HEADERS = ["序号", "标题", "发文字号", "成文日期"]


@dataclass(frozen=True)
class Record:
    """Container for a single row in the法规 list."""

    sequence: str
    title: str
    document_no: str
    publish_date: str

    @property
    def csv_row(self) -> List[str]:
        return [self.sequence, self.title, self.document_no, self.publish_date]

    @property
    def unique_key(self) -> Tuple[str, str]:
        # Using title and document number provides a stable identifier even if
        # the sequence number changes when new rows are inserted at the top.
        return self.title.strip(), self.document_no.strip()


def load_existing_keys(csv_path: Path) -> Set[Tuple[str, str]]:
    """Load the unique keys for previously downloaded records from CSV."""
    seen_keys: Set[Tuple[str, str]] = set()
    if not csv_path.exists():
        return seen_keys

    with csv_path.open("r", encoding="utf-8", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = reader.fieldnames or []
        missing_columns = [column for column in CSV_HEADERS if column not in fieldnames]
        if missing_columns:
            raise ValueError(
                f"CSV 文件缺少必要的列: {', '.join(missing_columns)}"
            )
        for row in reader:
            key = (row["标题"].strip(), row["发文字号"].strip())
            seen_keys.add(key)
    return seen_keys


async def extract_records(page: "Page") -> List[Record]:
    """Extract the records from the current page."""
    records: List[Record] = []

    # The table layout is the most common on policy list pages. We first try to
    # locate rows in a table structure and gracefully fall back to list items if
    # the markup differs.
    table_rows = await page.locator("table tbody tr").all()
    if table_rows:
        for row in table_rows:
            cells = await row.locator("td").all_text_contents()
            if len(cells) < 4:
                continue
            if cells[0].strip() == "序号":
                continue
            record = Record(
                sequence=cells[0].strip(),
                title=cells[1].strip(),
                document_no=cells[2].strip(),
                publish_date=cells[3].strip(),
            )
            if record.sequence and record.title:
                records.append(record)
        return records

    # Fallback: list layouts where each <li> contains spans for the metadata.
    list_items = await page.locator("li").all()
    for item in list_items:
        spans = await item.locator("span").all_text_contents()
        if len(spans) < 4:
            continue
        if spans[0].strip() == "序号":
            continue
        record = Record(
            sequence=spans[0].strip(),
            title=spans[1].strip(),
            document_no=spans[2].strip(),
            publish_date=spans[3].strip(),
        )
        if record.sequence and record.title:
            records.append(record)
    return records


async def goto_next_page(page: "Page") -> bool:
    """Move to the next page if available."""
    next_link = page.locator("a:has-text(\"下一页\")")
    if await next_link.count() == 0:
        return False

    first_next = next_link.first
    class_attr = (await first_next.get_attribute("class")) or ""
    aria_disabled = (await first_next.get_attribute("aria-disabled")) or "false"

    if "disabled" in class_attr.lower() or aria_disabled.lower() == "true":
        return False

    try:
        await first_next.click()
    except Exception:
        return False

    await page.wait_for_load_state("networkidle")
    return True


async def scrape(csv_path: Path, headless: bool = True) -> int:
    try:
        from playwright.async_api import async_playwright
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised in tests via skip
        raise RuntimeError(
            "Playwright 未安装，无法运行采集脚本。请先执行 `pip install playwright` "
            "并运行 `playwright install` 安装浏览器内核。"
        ) from exc

    seen_keys = load_existing_keys(csv_path)

    async with async_playwright() as playwright:
        browser: "Browser" = await playwright.chromium.launch(headless=headless)
        page = await browser.new_page()
        await page.goto(BASE_URL, wait_until="networkidle")

        new_records: List[Record] = []

        while True:
            current_records = await extract_records(page)
            for record in current_records:
                if record.unique_key in seen_keys:
                    continue
                seen_keys.add(record.unique_key)
                new_records.append(record)

            has_next = await goto_next_page(page)
            if not has_next:
                break

        await browser.close()

    if not csv_path.exists():
        with csv_path.open("w", encoding="utf-8", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(CSV_HEADERS)

    if new_records:
        with csv_path.open("a", encoding="utf-8", newline="") as csvfile:
            writer = csv.writer(csvfile)
            for record in new_records:
                writer.writerow(record.csv_row)

    return len(new_records)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="下载国家税务总局法规库法律法规列表数据")
    parser.add_argument(
        "--csv",
        default="chinatax_flfg.csv",
        type=Path,
        help="保存数据的 CSV 文件路径 (默认: chinatax_flfg.csv)",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="以可视化模式运行浏览器，便于调试",
    )
    return parser.parse_args()


async def async_main(args: argparse.Namespace) -> None:
    headless = not args.headed
    csv_path = args.csv
    new_count = await scrape(csv_path=csv_path, headless=headless)
    print(f"新增 {new_count} 条记录，保存至 {csv_path}")


def main() -> None:
    args = parse_arguments()
    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
