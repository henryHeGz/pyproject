import json
import sys
from pathlib import Path
from typing import Optional

from playwright.sync_api import Error, sync_playwright

TARGET_URL = "https://oa.zgzykg.com.cn"
STATE_FILE = Path(__file__).with_name("auth_state.json")
LAUNCH_ARGS = ["--no-first-run", "--no-default-browser-check"]


def load_storage_state() -> Optional[dict]:
    """读取已保存的登录状态，如果不存在则返回 None。"""
    if not STATE_FILE.exists():
        return None

    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"⚠️ 无法读取历史登录状态 ({exc})，将重新创建新的会话。")
        return None


def save_storage_state(context) -> None:
    """将当前上下文中的登录状态写入文件。"""
    context.storage_state(path=STATE_FILE)
    print(f"✅ 登录状态已保存到: {STATE_FILE}")


def reset_state() -> None:
    """删除已保存的登录状态文件。"""
    if STATE_FILE.exists():
        STATE_FILE.unlink()
        print(f"已删除保存的登录状态: {STATE_FILE}")
    else:
        print("当前没有保存的登录状态，无需删除。")


def main() -> None:
    print("=" * 60)
    print("Playwright 模式 - 复用登录状态")
    print("=" * 60)
    print("• 首次运行会打开浏览器，请手动登录一次并按提示保存状态。")
    print("• 之后再次运行脚本会自动带入已保存的登录信息。")
    print("• 如需重新登录，可带参数 --reset 重新生成登录状态。\n")

    if "--reset" in sys.argv:
        reset_state()
        if "--reset-only" in sys.argv:
            return
        print("继续运行，将创建新的登录状态。\n")

    stored_state = load_storage_state()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            channel="chrome",
            args=LAUNCH_ARGS,
        )
        context = None

        try:
            context = browser.new_context(storage_state=stored_state)
            page = context.new_page()

            print("正在打开目标页面，请稍候...")
            page.goto(TARGET_URL, wait_until="networkidle", timeout=120_000)
            print(f"页面标题: {page.title()}")
            print(f"当前 URL: {page.url}")
            print("=" * 60)

            if stored_state is None:
                print("首次运行需要手动登录。")
                input("完成登录后按回车保存登录状态...")
                save_storage_state(context)
            else:
                # 每次运行都更新一次登录状态，防止长期使用导致过期。
                save_storage_state(context)

            input("操作完成后按回车退出脚本...")
        finally:
            if context is not None:
                context.close()
            browser.close()


if __name__ == "__main__":
    try:
        main()
    except Error as exc:
        print(f"❌ Playwright 运行失败: {exc}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n已取消运行。")
