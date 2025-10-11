"""Download content from a single Chinese tax document page using Playwright."""
from __future__ import annotations

import argparse
import asyncio
import re
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urljoin, urlparse

if TYPE_CHECKING:  # pragma: no cover - used only for type hints
    from playwright.async_api import Browser, Download, Page


def sanitize_filename(filename: str) -> str:
    """Remove or replace invalid characters from filename."""
    # Replace invalid characters with underscore
    invalid_chars = r'[<>:"/\\|?*]'
    return re.sub(invalid_chars, '_', filename)


def extract_folder_name(url: str, page_title: str = "") -> str:
    """Extract folder name from URL or page title.

    Example: For 国家税务总局公告2021年第26号, create folder named:
    国家税务总局公告2021年第26号_5194992 (where 5194992 is from content.html)
    """
    # Extract the content ID from URL like /c5194992/content.html
    match = re.search(r'/c(\d+)/content\.html', url)
    content_id = match.group(1) if match else "unknown"

    # Try to extract a meaningful title from the page
    # Common patterns: "国家税务总局公告2021年第26号", "国家税务总局令第XX号"
    if page_title:
        # Remove common suffix like "- 国家税务总局政策法规库"
        base_name = re.sub(r'\s*[-_]\s*国家税务总局.*', '', page_title)
        base_name = re.sub(r'\s*国家税务总局政策法规库\s*', '', base_name)
        base_name = base_name.strip()

        if base_name:
            base_name = sanitize_filename(base_name)
        else:
            base_name = "chinatax_document"
    else:
        base_name = "chinatax_document"

    return f"{base_name}_{content_id}"


async def download_attachments(page: "Page", attachments_dir: Path, browser: "Browser") -> int:
    """Download all attachments from the page.

    Returns:
        Number of attachments downloaded
    """
    attachments_dir.mkdir(parents=True, exist_ok=True)

    # Look for attachment links - common patterns in Chinese tax pages
    # Usually marked with 附件 (attachment) or downloadable file extensions
    attachment_selectors = [
        'a[href$=".pdf"]',
        'a[href$=".doc"]',
        'a[href$=".docx"]',
        'a[href$=".xls"]',
        'a[href$=".xlsx"]',
    ]

    downloaded_count = 0
    seen_urls = set()

    for selector in attachment_selectors:
        links = await page.locator(selector).all()

        for link in links:
            try:
                href = await link.get_attribute("href")
                if not href or href == "" or href == "javascript:void(0)":
                    continue

                # Convert to absolute URL
                absolute_url = urljoin(page.url, href)

                # Skip if already downloaded
                if absolute_url in seen_urls:
                    continue
                seen_urls.add(absolute_url)

                # Extract filename from URL
                url_path = urlparse(absolute_url).path
                filename = url_path.split('/')[-1] if '/' in url_path else f"attachment_{downloaded_count + 1}.pdf"

                # Sanitize filename
                filename = sanitize_filename(filename)

                download_path = attachments_dir / filename

                print(f"  下载附件: {filename}")
                print(f"    URL: {absolute_url}")

                # Create new context with cookies from original context to maintain session
                cookies = await page.context.cookies()
                context = await browser.new_context()
                await context.add_cookies(cookies)
                new_page = await context.new_page()

                # Set user agent and referer to avoid 403
                await new_page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Referer": page.url,
                })

                try:
                    # First try: expect download event (for files that trigger browser download)
                    async with new_page.expect_download(timeout=15000) as download_info:
                        try:
                            await new_page.goto(absolute_url, wait_until="commit")
                        except Exception:
                            # ERR_ABORTED is normal for downloads - the download event will still fire
                            pass

                    download: Download = await download_info.value
                    await download.save_as(download_path)
                    downloaded_count += 1
                    print(f"    ✓ 已保存到: {download_path}")
                except Exception as dl_err:
                    # If download event didn't fire, try fetching as regular content
                    print(f"    下载事件未触发，尝试直接获取内容...")
                    try:
                        response = await new_page.goto(absolute_url, wait_until="domcontentloaded", timeout=15000)
                        if response and response.ok:
                            content = await response.body()
                            download_path.write_bytes(content)
                            downloaded_count += 1
                            print(f"    ✓ 已保存到: {download_path}")
                        else:
                            print(f"    ✗ 下载失败: HTTP {response.status if response else 'No response'}")
                    except Exception as e2:
                        print(f"    ✗ 下载失败: {str(e2)}")
                finally:
                    await context.close()

            except Exception as e:
                print(f"    ✗ 下载失败: {str(e)}")
                continue

    return downloaded_count


async def download_main_document(page: "Page", output_dir: Path, browser: "Browser") -> bool:
    """Click the main download button and save the document.

    Returns:
        True if document was downloaded successfully
    """
    # Look for download buttons - common patterns
    download_button_selectors = [
        '#zwxz',  # Specific to chinatax pages
        '.xxgk-download-btn',
        'a:has-text("【下载】")',
        'button:has-text("下载")',
        'a:has-text("下载正文")',
        'a:has-text("下载文件")',
        '.download-btn',
        '#downloadBtn',
    ]

    for selector in download_button_selectors:
        buttons = await page.locator(selector).all()

        for button in buttons:
            try:
                # Check if button has an href attribute
                href = await button.get_attribute("href")

                # If href is empty or javascript:void, it might be set dynamically
                # Wait a bit for JavaScript to execute
                if not href or href == "" or href == "javascript:void(0)":
                    await page.wait_for_timeout(1000)
                    href = await button.get_attribute("href")

                # Still no valid href, try clicking anyway
                if not href or href == "" or href == "javascript:void(0)":
                    print(f"  按钮 {selector} 的 href 为空，尝试点击...")

                    try:
                        # Try to intercept download
                        async with page.expect_download(timeout=10000) as download_info:
                            await button.click()

                        download: Download = await download_info.value
                        suggested_filename = download.suggested_filename
                        filename = sanitize_filename(suggested_filename)
                        download_path = output_dir / filename
                        await download.save_as(download_path)
                        print(f"  ✓ 主文档已下载: {download_path}")
                        return True
                    except Exception as e:
                        print(f"    点击后无下载: {str(e)}")
                        continue
                else:
                    # Valid href, navigate to it
                    absolute_url = urljoin(page.url, href)
                    print(f"  下载主文档: {absolute_url}")

                    # Create new context with cookies from original context to maintain session
                    cookies = await page.context.cookies()
                    context = await browser.new_context()
                    await context.add_cookies(cookies)
                    new_page = await context.new_page()

                    try:
                        # Try to download via navigation
                        async with new_page.expect_download(timeout=10000) as download_info:
                            await new_page.goto(absolute_url)
                        download: Download = await download_info.value

                        suggested_filename = download.suggested_filename
                        filename = sanitize_filename(suggested_filename)
                        download_path = output_dir / filename
                        await download.save_as(download_path)
                        print(f"  ✓ 主文档已下载: {download_path}")
                        return True
                    except Exception:
                        # If not a download, try to fetch as regular file
                        response = await new_page.goto(absolute_url, wait_until="domcontentloaded")
                        if response and response.ok:
                            # Determine filename from URL or content-disposition header
                            content_disposition = response.headers.get('content-disposition', '')
                            if 'filename=' in content_disposition:
                                filename = content_disposition.split('filename=')[1].strip('"\'')
                            else:
                                filename = urlparse(absolute_url).path.split('/')[-1]
                                if not filename:
                                    filename = "document.doc"

                            filename = sanitize_filename(filename)
                            download_path = output_dir / filename

                            content = await response.body()
                            download_path.write_bytes(content)
                            print(f"  ✓ 主文档已下载: {download_path}")
                            return True
                        else:
                            print(f"    下载失败: HTTP {response.status if response else 'No response'}")
                    finally:
                        await context.close()

            except Exception as e:
                print(f"    此按钮无法下载: {str(e)}")
                continue

    print("  未找到可用的下载按钮")
    return False


async def scrape_document(url: str, base_output_dir: Path = Path("."), headless: bool = True) -> Path:
    """Scrape a single document page and download all content.

    Args:
        url: The document URL to scrape
        base_output_dir: Base directory for output (default: current directory)
        headless: Whether to run browser in headless mode

    Returns:
        Path to the created folder
    """
    try:
        from playwright.async_api import async_playwright
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Playwright 未安装,无法运行采集脚本。请先执行 `pip install playwright` "
            "并运行 `playwright install` 安装浏览器内核。"
        ) from exc

    async with async_playwright() as playwright:
        print("正在启动浏览器...")
        browser: Browser = await playwright.chromium.launch(headless=headless)
        page = await browser.new_page()

        # Set a realistic user agent
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

        print(f"正在访问 {url}...")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)

        # Extract page title - try multiple methods
        # Method 1: Try meta tag ArticleTitle
        article_title = ""
        try:
            meta_title = await page.locator('meta[name="ArticleTitle"]').first.get_attribute("content")
            if meta_title:
                article_title = meta_title.strip()
        except Exception:
            pass

        # Method 2: Fallback to page title
        if not article_title:
            page_title = await page.title()
            article_title = page_title

        print(f"页面标题: {article_title}")

        # Create folder name
        folder_name = extract_folder_name(url, article_title)
        output_dir = base_output_dir / folder_name
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"创建文件夹: {output_dir}")

        # Create attachments subfolder
        attachments_dir = output_dir / "附件"

        # Download attachments
        print("\n正在查找并下载附件...")
        attachment_count = await download_attachments(page, attachments_dir, browser)
        print(f"共下载 {attachment_count} 个附���")

        # Download main document
        print("\n正在下载主文档...")
        main_downloaded = await download_main_document(page, output_dir, browser)

        if not main_downloaded:
            print("提示: 如果页面没有下载按钮，您可能需要手动保存页面内容")

        print("\n正在关闭浏览器...")
        await browser.close()

    return output_dir


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="下载国家税务总局单个文档及其附件")
    parser.add_argument(
        "url",
        type=str,
        help="要下载的文档 URL",
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
    return parser.parse_args()


async def async_main(args: argparse.Namespace) -> None:
    headless = not args.headed
    output_dir = await scrape_document(
        url=args.url,
        base_output_dir=args.output_dir,
        headless=headless
    )
    print(f"\n✓ 完成! 所有文件已保存到: {output_dir}")


def main() -> None:
    args = parse_arguments()
    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
