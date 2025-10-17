from playwright.sync_api import sync_playwright
import os

# 方案1：使用独立的用户数据目录（推荐，不会与正在运行的Chrome冲突）
def method1_separate_profile():
    """使用独立的Chrome配置文件，不会与现有Chrome冲突"""
    with sync_playwright() as p:
        # 创建一个新的用户数据目录
        user_data_dir = os.path.expanduser("~/Library/Application Support/PlaywrightChrome")

        print(f"使用用户数据目录: {user_data_dir}")

        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            channel="chrome"
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        print("正在打开页面...")
        page.goto("https://oa.zgzykg.com.cn", wait_until="networkidle", timeout=60000)

        print(f"页面标题: {page.title()}")
        print(f"当前URL: {page.url}")

        input("\n按回车键关闭浏览器...")
        browser.close()


# 方案2：使用常规launch（不复用登录状态，但更稳定）
def method2_regular_launch():
    """不复用登录状态，但启动更可靠"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            channel="chrome"
        )

        context = browser.new_context()
        page = context.new_page()

        print("正在打开页面...")
        page.goto("https://oa.zgzykg.com.cn", wait_until="networkidle", timeout=60000)

        print(f"页面标题: {page.title()}")
        print(f"当前URL: {page.url}")

        input("\n按回车键关闭浏览器...")
        browser.close()


if __name__ == "__main__":
    print("选择运行方案：")
    print("1 - 使用独立配置文件（首次需要登录，之后会保存）")
    print("2 - 常规启动（每次都需要登录）")

    choice = input("请输入选择 (1 或 2): ").strip()

    if choice == "1":
        method1_separate_profile()
    elif choice == "2":
        method2_regular_launch()
    else:
        print("无效选择，使用方案1")
        method1_separate_profile()
