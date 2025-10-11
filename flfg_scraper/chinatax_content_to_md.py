"""Download content from Chinese Tax Administration document pages and save as Markdown."""
from __future__ import annotations

import argparse
import asyncio
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page


def html_to_markdown(content: str, title: str) -> str:
    """Convert HTML content to basic Markdown format."""
    md = f"问：{title}\n\n"

    # Remove script and style tags
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)

    # Convert common HTML tags to Markdown
    # Headers
    content = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1\n', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1\n', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1\n', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<h4[^>]*>(.*?)</h4>', r'#### \1\n', content, flags=re.IGNORECASE | re.DOTALL)

    # Paragraphs
    content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', content, flags=re.IGNORECASE | re.DOTALL)

    # Strong/Bold
    content = re.sub(r'<(strong|b)[^>]*>(.*?)</\1>', r'**\2**', content, flags=re.IGNORECASE | re.DOTALL)

    # Emphasis/Italic
    content = re.sub(r'<(em|i)[^>]*>(.*?)</\1>', r'*\2*', content, flags=re.IGNORECASE | re.DOTALL)

    # Links
    content = re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'[\2](\1)', content, flags=re.IGNORECASE | re.DOTALL)

    # Line breaks
    content = re.sub(r'<br\s*/?>', '\n', content, flags=re.IGNORECASE)

    # Lists
    content = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'</?[uo]l[^>]*>', '', content, flags=re.IGNORECASE)

    # Tables - basic conversion
    content = re.sub(r'<table[^>]*>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'</table>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'<tr[^>]*>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</tr>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'<t[hd][^>]*>(.*?)</t[hd]>', r'| \1 ', content, flags=re.IGNORECASE | re.DOTALL)

    # Divs and spans - just remove tags
    content = re.sub(r'</?div[^>]*>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'</?span[^>]*>', '', content, flags=re.IGNORECASE)

    # Remove remaining HTML tags
    content = re.sub(r'<[^>]+>', '', content)

    # Clean up HTML entities
    content = content.replace('&nbsp;', ' ')
    content = content.replace('&lt;', '<')
    content = content.replace('&gt;', '>')
    content = content.replace('&amp;', '&')
    content = content.replace('&quot;', '"')
    content = content.replace('&#39;', "'")

    # Clean up excessive whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = re.sub(r' {2,}', ' ', content)
    content = re.sub(r'[ \t]+\n', '\n', content)  # Remove trailing spaces

    md += content.strip()
    return md


async def download_page_content(page: Page, url: str) -> tuple[str, str]:
    """Download the page and extract title and main content."""
    print(f"正在访问 {url}...")
    await page.goto(url, wait_until="networkidle", timeout=60000)

    # Wait for content to load
    await page.wait_for_timeout(3000)

    # Extract title - try multiple methods
    title = ""
    try:
        # Method 1: Try meta tag ArticleTitle (common in Chinese government sites)
        meta_title_element = await page.query_selector('meta[name="ArticleTitle"]')
        if meta_title_element:
            title = await meta_title_element.get_attribute("content") or ""
            title = title.strip()
    except Exception:
        pass

    # Method 2: Try h1 tag
    if not title:
        try:
            h1_element = await page.query_selector("h1")
            if h1_element:
                title = (await h1_element.text_content() or "").strip()
        except Exception:
            pass

    # Method 3: Try common title classes
    if not title:
        title_selectors = [".title", ".article-title", ".doc-title", ".content-title"]
        for selector in title_selectors:
            try:
                title_element = await page.query_selector(selector)
                if title_element:
                    title = (await title_element.text_content() or "").strip()
                    if title:
                        break
            except Exception:
                continue

    # Method 4: Fallback to page title
    if not title:
        title = await page.title()

    if not title:
        title = "Untitled Document"

    print(f"标题: {title}")

    # Extract main content
    # Try to find the main content area
    content = ""
    selectors = [
        ".TRS_PreAppend",  # Common selector for Chinese government sites
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
                content = await content_element.inner_html()
                if content.strip():
                    print(f"使用选择器提取内容: {selector}")
                    break
        except Exception:
            continue

    # If no specific content area found, get body
    if not content.strip():
        print("未找到特定内容区域，提取整个页面...")
        body = await page.query_selector("body")
        if body:
            content = await body.inner_html()

    return title, content


async def download_and_save(url: str, output_path: Path, headless: bool = True) -> None:
    """Download page content and save as Markdown."""
    try:
        from playwright.async_api import async_playwright
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Playwright 未安装,无法运行脚本。请先执行 `pip install playwright` "
            "并运行 `playwright install` 安装浏览器内核。"
        ) from exc

    async with async_playwright() as playwright:
        print("正在启动浏览器...")
        browser = await playwright.chromium.launch(headless=headless)
        page = await browser.new_page()

        # Set realistic user agent
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

        # Download page
        title, html_content = await download_page_content(page, url)

        print("正在关闭浏览器...")
        await browser.close()

    # Convert to Markdown
    print("正在转换为 Markdown 格式...")
    markdown_content = html_to_markdown(html_content, title)

    # Save to file
    print(f"正在保存到 {output_path}...")
    output_path.write_text(markdown_content, encoding="utf-8")
    print(f"✓ 内容已保存到 {output_path}")
    print(f"✓ 文件大小: {output_path.stat().st_size} 字节")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="下载中国税务网页面内容并保存为 Markdown")
    parser.add_argument(
        "url",
        type=str,
        help="要下载的网页 URL",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="输出文件路径 (默认: content.md)",
        default=Path("content.md"),
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="以可视化模式运行浏览器，便于调试",
    )
    return parser.parse_args()


async def async_main(args: argparse.Namespace) -> None:
    await download_and_save(
        url=args.url,
        output_path=args.output,
        headless=not args.headed
    )


def main() -> None:
    args = parse_arguments()
    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
