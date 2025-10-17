#!/usr/bin/env python3
"""
国家税务总局留言公开页面爬虫

从 https://www.chinatax.gov.cn 的留言公开页面提取用户留言数据。
提取字段：留言问题、日期、链接地址
使用 MD5(留言问题+日期+链接地址) 作为唯一ID进行去重。
"""

import asyncio
import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Set, List, Dict
import argparse

# 添加父目录到 Python 路径以导入 db_config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.db_config import get_db_cursor

try:
    from playwright.async_api import async_playwright, Page, Browser
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError
except ImportError:
    raise ImportError(
        "playwright 未安装。请运行：pip install playwright && playwright install"
    )

# 目标网页URL
BASE_URL = "https://www.chinatax.gov.cn/chinatax/manuscriptList/n3255681?_channelName=%E7%95%99%E8%A8%80%E5%85%AC%E5%BC%80&_isAgg=0&_pageSize=20&_template=index"


@dataclass(frozen=True)
class CommentRecord:
    """留言记录数据类"""
    id: str  # MD5哈希值
    question: str  # 留言问题
    date: str  # 日期
    link: str  # 链接地址
    downloaded: str = "N"  # 是否下载，默认N
    question_content: str = ""  # 问的内容
    answer_content: str = ""  # 答的内容

    @staticmethod
    def generate_id(question: str, date: str, link: str) -> str:
        """生成唯一ID：MD5(留言问题+日期+链接地址)"""
        combined = f"{question}{date}{link}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()

    @classmethod
    def from_data(cls, question: str, date: str, link: str, downloaded: str = "N",
                  question_content: str = "", answer_content: str = ""):
        """从数据创建记录"""
        record_id = cls.generate_id(question, date, link)
        return cls(id=record_id, question=question, date=date, link=link,
                  downloaded=downloaded, question_content=question_content,
                  answer_content=answer_content)

    def to_csv_row(self) -> List[str]:
        """转换为CSV行"""
        return [self.id, self.question, self.date, self.link, self.downloaded,
                self.question_content, self.answer_content]

    def to_dict(self) -> dict:
        """转换为字典格式，用于数据库插入"""
        return {
            "id": self.id,
            "question": self.question,
            "date": self.date,
            "link": self.link,
            "downloaded": self.downloaded,
            "question_content": self.question_content,
            "answer_content": self.answer_content,
        }


def load_existing_ids() -> Set[str]:
    """从数据库加载已存在的记录ID集合，用于去重"""
    existing_ids = set()
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id FROM comment_records")
            for row in cursor.fetchall():
                existing_ids.add(row["id"])
    except Exception as e:
        print(f"⚠️  加载现有数据时出错: {e}")
    return existing_ids


def load_existing_records() -> Dict[str, CommentRecord]:
    """从数据库加载已存在的所有记录，用于下载内容更新"""
    records = {}
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT id, question, date, link, downloaded,
                       question_content, answer_content
                FROM comment_records
            """)
            for row in cursor.fetchall():
                record = CommentRecord.from_data(
                    row["question"], row["date"], row["link"], row["downloaded"],
                    row["question_content"] or "", row["answer_content"] or ""
                )
                records[row["id"]] = record
    except Exception as e:
        print(f"⚠️  加载现有记录时出错: {e}")
    return records


def save_all_records(records: List[CommentRecord]):
    """保存所有记录到数据库（批量插入或更新）"""
    if not records:
        return

    try:
        with get_db_cursor() as cursor:
            for record in records:
                # 使用 INSERT OR REPLACE (SQLite) / INSERT ... ON DUPLICATE KEY UPDATE (MySQL)
                # SQLite 兼容写法：先尝试更新，如果不存在则插入
                cursor.execute("""
                    INSERT INTO comment_records
                    (id, question, date, link, downloaded, question_content, answer_content)
                    VALUES (%(id)s, %(question)s, %(date)s, %(link)s, %(downloaded)s,
                            %(question_content)s, %(answer_content)s)
                    ON CONFLICT(id) DO UPDATE SET
                        downloaded = excluded.downloaded,
                        question_content = excluded.question_content,
                        answer_content = excluded.answer_content,
                        updated_at = CURRENT_TIMESTAMP
                """, record.to_dict())
    except Exception as e:
        print(f"❌ 保存记录时出错: {e}")



async def extract_comments(page: Page) -> List[CommentRecord]:
    """
    从当前页面提取留言记录

    页面结构：<ul class="list"><li><a>问题</a><span>日期</span></li>...</ul>
    """
    records = []

    # 等待页面加载完成 - 直接等待ul.list元素
    try:
        await page.wait_for_selector('ul.list', timeout=15000)
    except PlaywrightTimeoutError:
        print("⚠️  警告：页面加载超时，未找到ul.list")
        return records

    # 提取ul.list下的所有li元素
    list_items = await page.query_selector_all('ul.list > li')

    print(f"   找到 {len(list_items)} 个列表项")

    for item in list_items:
        try:
            # 提取链接和标题（在<a>标签中）
            link_elem = await item.query_selector('a')
            if not link_elem:
                continue

            question = (await link_elem.inner_text()).strip()
            link = await link_elem.get_attribute('href')

            # 确保链接是完整的URL
            if link:
                if not link.startswith('http'):
                    if link.startswith('/'):
                        link = f"https://www.chinatax.gov.cn{link}"
                    else:
                        link = f"https://www.chinatax.gov.cn/{link}"
            else:
                link = ""

            # 提取日期（在<span>标签中）
            date_elem = await item.query_selector('span')
            date = ""
            if date_elem:
                date_text = (await date_elem.inner_text()).strip()
                # 去除方括号 [2025-10-11] -> 2025-10-11
                date = date_text.strip('[]')

            # 跳过空记录
            if not question or not date:
                continue

            record = CommentRecord.from_data(question, date, link)
            records.append(record)

        except Exception as e:
            print(f"⚠️  提取列表项失败: {e}")
            continue

    return records


def extract_qa_from_html(html_content: str) -> tuple[str, str]:
    """
    从HTML内容中提取问和答

    参数：
        html_content: 页面HTML内容

    返回：
        tuple[str, str]: (问的内容, 答的内容)
    """
    # 移除script和style标签
    content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)

    # 清理HTML标签
    content = re.sub(r'<br\s*/?>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'<p[^>]*>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'</p>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'<[^>]+>', '', content)

    # 清理HTML实体
    content = content.replace('&nbsp;', ' ')
    content = content.replace('&lt;', '<')
    content = content.replace('&gt;', '>')
    content = content.replace('&amp;', '&')
    content = content.replace('&quot;', '"')
    content = content.replace('&#39;', "'")

    # 清理多余空白
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = re.sub(r' {2,}', ' ', content)
    content = re.sub(r'[ \t]+\n', '\n', content)

    question_content = ""
    answer_content = ""

    # 尝试匹配"问："和"答："模式
    question_match = re.search(r'问[:：]\s*(.*?)(?=答[:：]|$)', content, re.DOTALL | re.IGNORECASE)
    answer_match = re.search(r'答[:：]\s*(.*?)(?=$)', content, re.DOTALL | re.IGNORECASE)

    if question_match:
        question_content = question_match.group(1).strip()

    if answer_match:
        answer_content = answer_match.group(1).strip()

    return question_content, answer_content


async def download_comment_content(page: Page, url: str) -> tuple[str, str]:
    """
    下载留言详情页内容并提取问答

    参数：
        page: Playwright页面对象
        url: 详情页URL

    返回：
        tuple[str, str]: (问的内容, 答的内容)
    """
    try:
        print(f"      正在访问: {url}")
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(2000)

        # 提取标题（问题）
        question_content = ""
        try:
            # 方法1: 尝试从h1标签提取
            h1_element = await page.query_selector("h1")
            if h1_element:
                question_content = (await h1_element.inner_text()).strip()
        except Exception:
            pass

        # 方法2: 如果h1没有内容，尝试从title提取
        if not question_content:
            try:
                title = await page.title()
                # 去除常见的后缀
                question_content = title.replace("_国家税务总局", "").replace("国家税务总局", "").strip()
            except Exception:
                pass

        # 提取答案内容
        answer_content = ""

        # 尝试多个选择器提取答案内容
        content_html = ""
        selectors = [
            ".TRS_PreAppend",
            ".content",
            ".article-content",
            ".main-content",
            ".doc-content",
            "article",
            "#content",
            ".xxgk-detail",
        ]

        for selector in selectors:
            try:
                content_element = await page.query_selector(selector)
                if content_element:
                    content_html = await content_element.inner_html()
                    if content_html.strip():
                        break
            except Exception:
                continue

        # 如果没找到特定内容区域，获取body
        if not content_html.strip():
            body = await page.query_selector("body")
            if body:
                content_html = await body.inner_html()

        # 从HTML中提取答案（去掉"答："标记）
        _, answer_content = extract_qa_from_html(content_html)

        # 如果没有找到"答："标记，尝试直接提取文本内容
        if not answer_content:
            # 清理HTML获取纯文本
            text_content = re.sub(r'<script[^>]*>.*?</script>', '', content_html, flags=re.DOTALL | re.IGNORECASE)
            text_content = re.sub(r'<style[^>]*>.*?</style>', '', text_content, flags=re.DOTALL | re.IGNORECASE)
            text_content = re.sub(r'<[^>]+>', ' ', text_content)
            text_content = text_content.replace('&nbsp;', ' ')
            text_content = re.sub(r'\s+', ' ', text_content).strip()

            # 如果文本内容有一定长度，认为是有效答案
            if len(text_content) > 50:
                answer_content = text_content

        print(f"      ✓ 提取成功 (问: {len(question_content)} 字符, 答: {len(answer_content)} 字符)")
        return question_content, answer_content

    except PlaywrightTimeoutError:
        print(f"      ⚠️  访问超时: {url}")
        return "", ""
    except Exception as e:
        print(f"      ⚠️  提取失败: {e}")
        return "", ""


async def goto_next_page(page: Page) -> bool:
    """
    导航到下一页

    返回：
        bool: 如果成功导航到下一页返回True，否则返回False
    """
    try:
        # 查找"下一页"链接（class="next"）
        next_button = await page.query_selector('a.next')

        if not next_button:
            print("📄 未找到下一页按钮，已到达最后一页")
            return False

        # 检查href属性是否存在
        href = await next_button.get_attribute('href')
        if not href:
            print("📄 下一页按钮无链接，已到达最后一页")
            return False

        # 点击下一页
        await next_button.click()
        await page.wait_for_load_state('domcontentloaded', timeout=30000)
        # 额外等待，确保内容加载完成
        await page.wait_for_timeout(2000)

        print("✅ 成功翻页")
        return True

    except PlaywrightTimeoutError:
        print("⏱️  翻页超时")
        return False
    except Exception as e:
        print(f"⚠️  翻页失败: {e}")
        return False


async def scrape(headless: bool = True, start_page: int = 1, max_pages: int = None, auto_download: bool = False,
                 csv_path: str = None, overwrite_db: bool = False) -> tuple[int, str, List[CommentRecord]]:
    """
    主爬取函数

    参数：
        headless: 是否无头模式运行
        start_page: 起始页码（默认：1）
        max_pages: 最多爬取页数（默认：None，表示爬取所有页）
        auto_download: 爬取完成后自动下载详情内容（默认：False）
        csv_path: CSV文件保存路径（默认：None，不保存CSV）
        overwrite_db: 是否覆盖数据库已存在的记录（默认：False）

    返回：
        tuple[int, str, List[CommentRecord]]: (新增记录数, CSV文件路径, 本次抓取的所有记录)
    """
    if start_page > 1:
        print(f"📄 起始页码：第 {start_page} 页")
    if max_pages:
        print(f"📊 最多爬取：{max_pages} 页")

    all_scraped_records = []  # 本次抓取的所有记录（不去重）
    page_num = 1
    pages_scraped = 0  # 已爬取页数计数器

    async with async_playwright() as p:
        # 使用更真实的浏览器设置
        browser: Browser = await p.chromium.launch(
            headless=headless,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page: Page = await context.new_page()

        try:
            # 访问第一页
            print(f"🌐 正在访问: {BASE_URL}")
            await page.goto(BASE_URL, wait_until='domcontentloaded', timeout=60000)
            # 等待页面内容渲染
            await page.wait_for_timeout(3000)

            # 如果起始页 > 1，需要先翻页到指定页
            if start_page > 1:
                print(f"\n⏩ 正在跳转到第 {start_page} 页...")
                for i in range(1, start_page):
                    print(f"   跳过第 {i} 页...")
                    has_next = await goto_next_page(page)
                    if not has_next:
                        print(f"⚠️  无法跳转到第 {start_page} 页，总共只有 {i} 页")
                        await browser.close()
                        return 0
                    page_num += 1
                    await asyncio.sleep(1)
                print(f"✅ 已到达第 {start_page} 页\n")

            while True:
                print(f"\n📃 正在处理第 {page_num} 页...")

                # 提取当前页记录
                records = await extract_comments(page)
                print(f"   提取到 {len(records)} 条留言")

                # 直接添加所有记录到本次抓取列表（不去重）
                all_scraped_records.extend(records)
                print(f"   已添加到本次抓取列表")

                # 增加已爬取页数计数
                pages_scraped += 1

                # 检查是否达到最大页数限制
                if max_pages and pages_scraped >= max_pages:
                    print(f"\n✅ 已达到最大页数限制 ({max_pages} 页)")
                    break

                # 尝试翻页
                has_next = await goto_next_page(page)
                if not has_next:
                    break

                page_num += 1

                # 短暂延迟，避免请求过快
                await asyncio.sleep(1)

        finally:
            await browser.close()

    print(f"\n📊 本次共抓取 {len(all_scraped_records)} 条记录")

    # 如果启用自动下载，立即下载本次抓取记录的详情内容
    if auto_download and all_scraped_records:
        print(f"\n{'='*60}")
        print(f"🚀 自动下载功能已启用，开始下载本次抓取的 {len(all_scraped_records)} 条记录的详情内容...")
        print(f"{'='*60}\n")

        downloaded = await download_new_records_content(headless, all_scraped_records)
        print(f"\n✅ 自动下载完成！成功下载 {downloaded} 条记录的详情内容")

    # 保存到CSV文件
    actual_csv_path = None
    if csv_path:
        print(f"\n💾 正在保存到CSV文件: {csv_path}")
        try:
            import csv
            from pathlib import Path

            # 确保目录存在
            csv_file = Path(csv_path)
            csv_file.parent.mkdir(parents=True, exist_ok=True)

            with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
                if all_scraped_records:
                    writer = csv.writer(f)
                    # 写入表头
                    writer.writerow(['ID', '留言问题', '日期', '链接地址', '是否下载', '问的内容', '答的内容'])
                    # 写入数据
                    for record in all_scraped_records:
                        writer.writerow(record.to_csv_row())
            print(f"✅ 成功保存 {len(all_scraped_records)} 条记录到CSV文件")
            actual_csv_path = csv_path
        except Exception as e:
            print(f"❌ 保存CSV文件时出错: {e}")

    # 保存到数据库（根据overwrite_db参数决定是否覆盖）
    new_count = 0
    updated_count = 0
    skipped_count = 0

    if all_scraped_records:
        print(f"\n💾 正在保存到数据库 (覆盖模式: {'是' if overwrite_db else '否'})...")

        # 加载已存在的记录ID
        existing_ids = load_existing_ids()
        existing_count = len(existing_ids)

        try:
            with get_db_cursor() as cursor:
                for record in all_scraped_records:
                    if record.id in existing_ids:
                        if overwrite_db:
                            # 覆盖模式：更新已存在的记录
                            cursor.execute("""
                                UPDATE comment_records
                                SET question = %(question)s, date = %(date)s, link = %(link)s,
                                    downloaded = %(downloaded)s, question_content = %(question_content)s,
                                    answer_content = %(answer_content)s, updated_at = CURRENT_TIMESTAMP
                                WHERE id = %(id)s
                            """, record.to_dict())
                            updated_count += 1
                        else:
                            # 不覆盖模式：跳过已存在的记录
                            skipped_count += 1
                            # 只在详细模式下打印每条跳过的记录
                            # print(f"   跳过已存在记录: {record.question}")
                    else:
                        # 插入新记录
                        cursor.execute("""
                            INSERT INTO comment_records
                            (id, question, date, link, downloaded, question_content, answer_content)
                            VALUES (%(id)s, %(question)s, %(date)s, %(link)s, %(downloaded)s,
                                    %(question_content)s, %(answer_content)s)
                        """, record.to_dict())
                        new_count += 1

            if overwrite_db:
                print(f"✅ 数据库操作完成：新增 {new_count} 条，更新 {updated_count} 条")
            else:
                if skipped_count > 0:
                    print(f"✅ 数据库操作完成：新增 {new_count} 条，跳过 {skipped_count} 条重复记录")
                    print(f"   说明：本次抓取的 {len(all_scraped_records)} 条记录中，{skipped_count} 条已存在于数据库（共{existing_count}条记录）")
                else:
                    print(f"✅ 数据库操作完成：新增 {new_count} 条（数据库原有{existing_count}条记录）")
        except Exception as e:
            print(f"❌ 保存数据库时出错: {e}")

    return new_count, actual_csv_path, all_scraped_records


async def download_contents(headless: bool = True, max_downloads: int = None) -> int:
    """
    下载数据库中未下载记录的详情内容（问和答）

    参数：
        headless: 是否无头模式运行
        max_downloads: 最多下载数量（默认：None，表示下载所有未下载的）

    返回：
        int: 成功下载的记录数量
    """
    # 加载所有现有记录
    all_records = load_existing_records()
    if not all_records:
        print("📂 数据库为空或无记录")
        return 0

    # 筛选出未下载的记录
    undownloaded = [r for r in all_records.values() if r.downloaded == "N" and r.link]
    print(f"📊 发现 {len(undownloaded)} 条未下载的记录")

    if not undownloaded:
        print("✅ 所有记录已下载完成")
        return 0

    # 如果设置了最大下载数，限制数量
    if max_downloads:
        undownloaded = undownloaded[:max_downloads]
        print(f"📋 将下载前 {len(undownloaded)} 条记录")

    return await _download_records_content(headless, undownloaded)


async def download_new_records_content(headless: bool, records: List[CommentRecord]) -> int:
    """
    下载指定的新抓取记录的详情内容（问和答）

    参数：
        headless: 是否无头模式运行
        records: 要下载的记录列表

    返回：
        int: 成功下载的记录数量
    """
    if not records:
        print("📂 没有需要下载的记录")
        return 0

    print(f"📊 将下载 {len(records)} 条新记录的详情内容")
    return await _download_records_content(headless, records)


async def _download_records_content(headless: bool, records: List[CommentRecord]) -> int:
    """
    内部函数：下载指定记录列表的详情内容

    参数：
        headless: 是否无头模式运行
        records: 要下载的记录列表

    返回：
        int: 成功下载的记录数量
    """
    downloaded_count = 0
    updated_records = {}

    async with async_playwright() as p:
        browser: Browser = await p.chromium.launch(
            headless=headless,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page: Page = await context.new_page()

        try:
            for i, record in enumerate(records, 1):
                print(f"\n📥 [{i}/{len(records)}] 下载: {record.question}")

                # 下载内容
                question_content, answer_content = await download_comment_content(page, record.link)

                if question_content or answer_content:
                    # 创建更新后的记录（使用replace因为dataclass是frozen的）
                    updated_record = CommentRecord.from_data(
                        record.question, record.date, record.link, "Y",
                        question_content, answer_content
                    )
                    updated_records[record.id] = updated_record
                    downloaded_count += 1
                    print(f"      ✅ 成功下载并标记为已下载")
                else:
                    print(f"      ⚠️  未提取到内容，保持未下载状态")

                # 短暂延迟，避免请求过快
                await asyncio.sleep(1.5)

        finally:
            await browser.close()

    # 如果有更新的记录，需要更新数据库
    if updated_records:
        print(f"\n💾 正在更新数据库...")
        save_all_records(list(updated_records.values()))
        print(f"✅ 成功更新 {downloaded_count} 条记录")
    else:
        print(f"\n📝 没有记录被更新")

    return downloaded_count


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='国家税务总局留言公开页面爬虫',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  # 爬取所有页面
  python chinatax_comments_scraper.py

  # 从第5页开始爬取
  python chinatax_comments_scraper.py --start-page 5

  # 只爬取10页
  python chinatax_comments_scraper.py --max-pages 10

  # 从第3页开始爬取5页（第3-7页）
  python chinatax_comments_scraper.py --start-page 3 --max-pages 5

  # 使用有头模式
  python chinatax_comments_scraper.py --headed

  # 爬取列表并自动下载详情内容（一步完成）
  python chinatax_comments_scraper.py --auto-download

  # 爬取前5页并自动下载详情
  python chinatax_comments_scraper.py --max-pages 5 --auto-download

  # 仅下载未下载记录的详情内容（问和答）
  python chinatax_comments_scraper.py --download-content

  # 下载前10条未下载的记录
  python chinatax_comments_scraper.py --download-content --max-downloads 10
        """
    )
    parser.add_argument(
        '--headed',
        action='store_true',
        help='使用有头模式运行浏览器（显示浏览器窗口）'
    )
    parser.add_argument(
        '--start-page',
        type=int,
        default=1,
        metavar='N',
        help='起始页码，从第N页开始爬取 (默认: 1)'
    )
    parser.add_argument(
        '--max-pages',
        type=int,
        default=None,
        metavar='N',
        help='最多爬取N页 (默认: 无限制，爬取所有页)'
    )
    parser.add_argument(
        '--download-content',
        action='store_true',
        help='下载CSV中未下载记录的详情内容（问和答）'
    )
    parser.add_argument(
        '--auto-download',
        action='store_true',
        help='爬取列表后自动下载详情内容（一步完成）'
    )
    parser.add_argument(
        '--max-downloads',
        type=int,
        default=None,
        metavar='N',
        help='最多下载N条记录的内容 (默认: 无限制，下载所有未下载的)'
    )

    args = parser.parse_args()

    # 如果是下载内容模式
    if args.download_content:
        print("🚀 开始下载留言详情内容...\n")

        downloaded = asyncio.run(download_contents(
            headless=not args.headed,
            max_downloads=args.max_downloads
        ))

        print(f"\n🎉 下载完成！成功下载 {downloaded} 条记录的详情内容")
        return

    # 参数验证
    if args.start_page < 1:
        print("❌ 错误：起始页码必须 >= 1")
        return

    if args.max_pages is not None and args.max_pages < 1:
        print("❌ 错误：最大页数必须 >= 1")
        return

    # 检查参数冲突
    if args.download_content and args.auto_download:
        print("❌ 错误：--download-content 和 --auto-download 不能同时使用")
        return

    if args.auto_download:
        print("🚀 开始爬取国家税务总局留言数据并自动下载详情...\n")
    else:
        print("🚀 开始爬取国家税务总局留言数据...\n")

    new_count, csv_path, records = asyncio.run(scrape(
        headless=not args.headed,
        start_page=args.start_page,
        max_pages=args.max_pages,
        auto_download=args.auto_download
    ))

    print(f"\n🎉 爬取完成！新增 {new_count} 条记录，本次共抓取 {len(records)} 条记录")


if __name__ == '__main__':
    main()
