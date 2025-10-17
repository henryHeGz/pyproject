"""Scrape the 国家税务总局法规库法律法规列表 using Playwright."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, List, Set

# 添加父目录到 Python 路径以导入 db_config
sys.path.insert(0, str(Path(__file__).parent.parent))

if TYPE_CHECKING:  # pragma: no cover - used only for type hints
    from playwright.async_api import Browser, Page

from config.db_config import get_db_cursor

BASE_URL = "https://fgk.chinatax.gov.cn/zcfgk/c100012/listflfg.html"


@dataclass(frozen=True)
class Record:
    """Container for a single row in the法规 list."""

    sequence: str
    title: str
    document_no: str
    publish_date: str
    link: str
    downloaded: str = "N"

    @staticmethod
    def generate_sequence(title: str, document_no: str, publish_date: str, link: str) -> str:
        """Generate MD5 hash from title + document_no + publish_date + link."""
        combined = f"{title.strip()}{document_no.strip()}{publish_date.strip()}{link.strip()}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()

    @property
    def unique_key(self) -> str:
        # Using MD5 hash as the unique identifier
        return self.sequence

    def to_dict(self) -> dict:
        """转换为字典格式，用于数据库插入"""
        return {
            "id": self.sequence,
            "title": self.title,
            "document_no": self.document_no,
            "publish_date": self.publish_date,
            "link": self.link,
            "downloaded": self.downloaded,
        }


def load_existing_keys() -> Set[str]:
    """从数据库加载已存在记录的MD5 ID集合"""
    seen_keys: Set[str] = set()

    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id FROM flfg_records")
            for row in cursor.fetchall():
                seen_keys.add(row["id"])
    except Exception as e:
        print(f"⚠️  加载现有数据时出错: {e}")

    return seen_keys


async def extract_records(page: "Page") -> List[Record]:
    """Extract the records from the current page."""
    records: List[Record] = []

    # The list items are in .list ul li
    list_items = await page.locator(".list ul li").all()

    for item in list_items:
        # Each li contains p tags with specific classes
        ps = await item.locator("p").all()

        if len(ps) < 4:
            continue

        # Extract text from each p tag
        p_texts = []
        for p in ps:
            text = await p.text_content()
            p_texts.append((text or "").strip())

        if len(p_texts) < 4:
            continue

        # Skip header row if present
        if p_texts[0] == "序号":
            continue

        # Extract link from the title (p.bt)
        link = ""
        try:
            # The title is in the second p tag (index 1), look for an <a> tag
            title_p = ps[1]
            link_element = await title_p.locator("a").first.get_attribute("href")
            if link_element:
                # Convert relative URLs to absolute URLs
                if link_element.startswith("/"):
                    link = f"https://fgk.chinatax.gov.cn{link_element}"
                elif link_element.startswith("http"):
                    link = link_element
                else:
                    link = f"https://fgk.chinatax.gov.cn/zcfgk/c100012/{link_element}"
        except Exception:
            # If link extraction fails, leave it empty
            pass

        record = Record(
            sequence=Record.generate_sequence(p_texts[1], p_texts[2], p_texts[3], link),
            title=p_texts[1],
            document_no=p_texts[2],
            publish_date=p_texts[3],
            link=link,
        )
        if record.sequence and record.title:
            records.append(record)

    return records


async def goto_next_page(page: "Page") -> bool:
    """Move to the next page if available."""
    # Get the first record's title before clicking to verify page change
    try:
        first_item_before = await page.locator(".list ul li").first.locator("p").nth(1).text_content()
        first_item_before = (first_item_before or "").strip()
    except Exception:
        first_item_before = ""

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

    # Wait additional time for JavaScript to render new content
    await page.wait_for_timeout(3000)

    # Verify that the page content has actually changed
    try:
        first_item_after = await page.locator(".list ul li").first.locator("p").nth(1).text_content()
        first_item_after = (first_item_after or "").strip()

        # If the first item is the same, wait a bit more
        if first_item_before and first_item_after and first_item_before == first_item_after:
            print("  等待页面内容更新...")
            await page.wait_for_timeout(2000)
    except Exception:
        pass

    return True


async def scrape(headless: bool = True, start_page: int = 1, page_count: int | None = None) -> int:
    try:
        from playwright.async_api import async_playwright
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised in tests via skip
        raise RuntimeError(
            "Playwright 未安装,无法运行采集脚本。请先执行 `pip install playwright` "
            "并运行 `playwright install` 安装浏览器内核。"
        ) from exc

    print("正在加载现有数据...")
    seen_keys = load_existing_keys()
    print(f"已加载 {len(seen_keys)} 条历史记录")

    async with async_playwright() as playwright:
        print("正在启动浏览器...")
        browser: "Browser" = await playwright.chromium.launch(headless=headless)
        page = await browser.new_page()

        # Set a realistic user agent to avoid being blocked
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

        print(f"正在访问 {BASE_URL}...")
        await page.goto(BASE_URL, wait_until="networkidle")

        # Wait for JavaScript to execute and load content
        await page.wait_for_timeout(5000)

        try:
            # Wait for list items to be loaded
            await page.wait_for_selector(".list ul li", timeout=15000)
            print("页面加载成功")
        except Exception:
            # If timeout, continue anyway - the page might have loaded differently
            print("警告: 页面加载超时，尝试继续...")

        new_records: List[Record] = []
        page_num = 1
        found_duplicate = False

        # 跳过到起始页
        if start_page > 1:
            print(f"正在跳过到第 {start_page} 页...")
            for _ in range(start_page - 1):
                has_next = await goto_next_page(page)
                if not has_next:
                    print(f"无法跳转到第 {start_page} 页，已到达最后一页")
                    break
                page_num += 1
            print(f"已到达第 {page_num} 页")

        pages_scraped = 0
        max_pages = page_count if page_count is not None else float('inf')

        while pages_scraped < max_pages:
            print(f"正在提取第 {page_num} 页数据...")
            current_records = await extract_records(page)
            new_count_this_page = 0
            for record in current_records:
                if record.unique_key in seen_keys:
                    found_duplicate = True
                    print(f"\n[DEBUG] 发现重复记录:")
                    print(f"  序号(MD5): {record.sequence}")
                    print(f"  标题: {record.title}")
                    print(f"  发文字号: {record.document_no}")
                    print(f"  成文日期: {record.publish_date}")
                    print(f"  链接: {record.link}\n")
                    continue
                seen_keys.add(record.unique_key)
                new_records.append(record)
                new_count_this_page += 1

            print(f"第 {page_num} 页提取到 {len(current_records)} 条记录，其中 {new_count_this_page} 条为新记录")

            pages_scraped += 1

            if found_duplicate:
                print("发现重复记录，停止翻页")
                break

            if pages_scraped >= max_pages:
                print(f"已完成 {max_pages} 页的抓取")
                break

            print("正在尝试翻页...")
            has_next = await goto_next_page(page)
            if not has_next:
                print("已到达最后一页")
                break

            page_num += 1
            print(f"成功翻到第 {page_num} 页")

        print("正在关闭浏览器...")
        await browser.close()

    # 保存新记录到数据库
    if new_records:
        print(f"正在保存 {len(new_records)} 条新记录到数据库...")
        try:
            with get_db_cursor() as cursor:
                for record in new_records:
                    cursor.execute("""
                        INSERT INTO flfg_records (id, title, document_no, publish_date, link, downloaded)
                        VALUES (%(id)s, %(title)s, %(document_no)s, %(publish_date)s, %(link)s, %(downloaded)s)
                    """, record.to_dict())
            print("数据保存完成")
        except Exception as e:
            print(f"❌ 保存数据时出错: {e}")
    else:
        print("没有新记录需要保存")

    return len(new_records)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="下载国家税务总局法规库法律法规列表数据")
    parser.add_argument(
        "--headed",
        action="store_true",
        help="以可视化模式运行浏览器，便于调试",
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=1,
        help="从哪一页开始抓取 (默认: 1)",
    )
    parser.add_argument(
        "--page-count",
        type=int,
        default=None,
        help="抓取多少页 (默认: 抓取到最后一页或发现重复记录)",
    )
    return parser.parse_args()


async def async_main(args: argparse.Namespace) -> None:
    headless = not args.headed
    new_count = await scrape(
        headless=headless,
        start_page=args.start_page,
        page_count=args.page_count
    )
    print(f"新增 {new_count} 条记录到数据库")


def main() -> None:
    args = parse_arguments()
    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
