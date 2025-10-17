#!/usr/bin/env python3
"""
Codex2 自动登录 - 智能拼图缺口检测版本
核心逻辑：
1. 检测canvas中拼图缺口的X坐标
2. 计算需要拖动的距离
3. 精确拖动滑块到缺口位置
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, Tuple

try:
    from playwright.async_api import async_playwright, Page
    from PIL import Image
    import io
except ImportError as e:
    print(f"缺少依赖: {e}")
    print("请安装: pip install playwright pillow")
    sys.exit(1)

LOGIN_URL = "http://10.57.11.68:31000/#/user/login?redirect=%2F"
USERNAME = "pszxAdmin"
PASSWORD = "TcmpszxAdmin199@."


async def detect_puzzle_gap(page: Page) -> Optional[Tuple[int, int]]:
    """
    智能检测拼图缺口位置

    Returns:
        (gap_x, canvas_width) 或 None
        gap_x: 缺口在canvas中的X坐标
        canvas_width: canvas总宽度
    """
    try:
        # 获取canvas元素
        canvas = await page.query_selector("canvas")
        if not canvas:
            print("  ⚠ 未找到canvas元素")
            return None

        # 截取canvas图像
        canvas_bytes = await canvas.screenshot()
        img = Image.open(io.BytesIO(canvas_bytes))
        width, height = img.size
        pixels = img.load()

        print(f"  Canvas尺寸: {width}x{height}")

        # 方法1: 检测垂直边缘（拼图缺口有明显的垂直边界）
        edge_scores = []

        for x in range(15, width - 15):  # 跳过边缘区域
            vertical_edge_score = 0

            # 沿垂直方向采样多个点，计算亮度差异
            sample_points = range(height // 4, 3 * height // 4, 3)

            for y in sample_points:
                if x < width - 2:
                    # 计算相邻像素的亮度差异
                    r1, g1, b1 = pixels[x, y][:3]
                    r2, g2, b2 = pixels[x + 1, y][:3]
                    r3, g3, b3 = pixels[x + 2, y][:3]

                    brightness1 = (r1 + g1 + b1) / 3
                    brightness2 = (r2 + g2 + b2) / 3
                    brightness3 = (r3 + g3 + b3) / 3

                    # 边缘检测：相邻像素亮度差异大
                    diff1 = abs(brightness1 - brightness2)
                    diff2 = abs(brightness2 - brightness3)

                    vertical_edge_score += diff1 + diff2

            edge_scores.append((x, vertical_edge_score))

        # 按得分排序，找到最可能的缺口位置
        edge_scores.sort(key=lambda item: item[1], reverse=True)

        # 获取前5个候选位置
        top_candidates = edge_scores[:5]

        print(f"  前5个缺口候选位置:")
        for rank, (x, score) in enumerate(top_candidates, 1):
            percentage = (x / width) * 100
            print(f"    {rank}. X={x:3d}px ({percentage:5.1f}%)  得分={int(score)}")

        # 选择得分最高的位置作为缺口
        gap_x = top_candidates[0][0]

        # 验证合理性：缺口通常不会在最边缘
        if gap_x < width * 0.05 or gap_x > width * 0.95:
            print(f"  ⚠ 检测位置{gap_x}px似乎在边缘，选择第二候选")
            gap_x = top_candidates[1][0]

        print(f"  ✓ 确定缺口位置: X={gap_x}px (占canvas的{gap_x/width*100:.1f}%)")

        return (gap_x, width)

    except Exception as e:
        print(f"  ✗ 缺口检测失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def calculate_drag_distance(page: Page, gap_x: int) -> Optional[float]:
    """
    计算滑块需要拖动的距离

    Args:
        gap_x: 缺口在canvas中的X坐标

    Returns:
        需要拖动的像素距离
    """
    try:
        # 获取滑块元素
        slider = await page.query_selector(".slide-verify-slider-mask-item")
        if not slider:
            return None

        slider_box = await slider.bounding_box()
        if not slider_box:
            return None

        # 滑块初始位置（左边缘）
        slider_start_x = slider_box['x']

        # 获取canvas位置
        canvas = await page.query_selector("canvas")
        canvas_box = await canvas.bounding_box() if canvas else None

        if not canvas_box:
            print("  ⚠ 无法获取canvas位置，使用估算")
            # 假设canvas和滑块轨道在同一水平位置
            drag_distance = gap_x
        else:
            canvas_start_x = canvas_box['x']

            # 计算拖动距离 = (canvas起始位置 + 缺口相对位置) - 滑块起始位置
            drag_distance = (canvas_start_x + gap_x) - slider_start_x

            print(f"  计算详情:")
            print(f"    Canvas起始X: {canvas_start_x:.0f}px")
            print(f"    缺口相对位置: {gap_x}px")
            print(f"    滑块起始X: {slider_start_x:.0f}px")
            print(f"    需要拖动: {drag_distance:.0f}px")

        return drag_distance

    except Exception as e:
        print(f"  ✗ 距离计算失败: {e}")
        return None


async def drag_slider_precisely(page: Page, distance: float, start_x: float, start_y: float):
    """精确拖动滑块"""
    import random

    # 移动到滑块中心
    await page.mouse.move(start_x, start_y)
    await asyncio.sleep(0.1)

    # 按下鼠标
    await page.mouse.down()
    await asyncio.sleep(0.15)

    # 执行拖动 - 使用人类般的加速度曲线
    steps = 30
    for i in range(steps):
        progress = (i + 1) / steps

        # Ease-in-out曲线：开始慢，中间快，结束慢
        if progress < 0.5:
            eased = 2 * progress * progress
        else:
            eased = 1 - 2 * (1 - progress) * (1 - progress)

        current_x = start_x + (distance * eased)

        # 添加轻微的Y轴抖动，模拟人手不稳
        y_jitter = random.uniform(-0.8, 0.8) if i % 4 == 0 else 0
        current_y = start_y + y_jitter

        await page.mouse.move(current_x, current_y)

        # 变速：开始和结束时较慢
        if i < 4:
            await asyncio.sleep(0.045)  # 慢启动
        elif i > steps - 5:
            await asyncio.sleep(0.05)   # 慢结束
        else:
            await asyncio.sleep(0.028)  # 快速中段

    # 到达目标后的微调（人类会做细微调整）
    for _ in range(3):
        micro_adjust = random.uniform(-1.5, 1.5)
        await page.mouse.move(current_x + micro_adjust, current_y)
        await asyncio.sleep(0.035)

    # 短暂停留后释放
    await asyncio.sleep(0.12)
    await page.mouse.up()

    print(f"  ✓ 拖动完成: {distance:.1f}px")


async def solve_captcha_smart(page: Page) -> bool:
    """智能解决滑块验证码"""
    print("\n【开始解决滑块验证码】")

    await asyncio.sleep(1.5)

    try:
        # 1. 检测拼图缺口位置
        print("\n步骤1: 检测拼图缺口位置")
        gap_result = await detect_puzzle_gap(page)

        if not gap_result:
            print("  ✗ 无法检测缺口，使用备用方案")
            # 备用方案：尝试常见的几个位置
            distances_to_try = [105, 95, 115, 85, 125, 75]
        else:
            gap_x, canvas_width = gap_result

            # 2. 计算拖动距离
            print("\n步骤2: 计算拖动距离")
            drag_distance = await calculate_drag_distance(page, gap_x)

            if drag_distance is None:
                print("  ✗ 无法计算距离，使用检测到的缺口位置")
                drag_distance = gap_x

            # 准备尝试列表：精确位置 ± 几个像素的微调
            distances_to_try = [
                drag_distance,
                drag_distance + 2,
                drag_distance - 2,
                drag_distance + 4,
                drag_distance - 4,
                drag_distance + 1,
                drag_distance - 1,
            ]

        # 3. 获取滑块信息
        print("\n步骤3: 获取滑块位置信息")
        slider = await page.wait_for_selector(".slide-verify-slider-mask-item", timeout=5000)
        if not slider:
            print("  ✗ 未找到滑块元素")
            return False

        slider_box = await slider.bounding_box()
        if not slider_box:
            print("  ✗ 无法获取滑块位置")
            return False

        # 滑块中心点
        start_x = slider_box['x'] + slider_box['width'] / 2
        start_y = slider_box['y'] + slider_box['height'] / 2
        print(f"  滑块中心: ({start_x:.0f}, {start_y:.0f})")

        # 4. 尝试拖动
        print("\n步骤4: 尝试拖动滑块")
        for attempt, distance in enumerate(distances_to_try, 1):
            # 跳过不合理的距离
            if distance < 20 or distance > 300:
                print(f"  跳过不合理距离: {distance:.0f}px")
                continue

            print(f"\n  【尝试 {attempt}/{len(distances_to_try)}】拖动距离: {distance:.0f}px")

            # 检查是否已经跳转
            if "login" not in page.url.lower():
                print("  ✓✓✓ 页面已跳转，验证成功!")
                return True

            # 重新获取滑块(可能被刷新)
            slider = await page.query_selector(".slide-verify-slider-mask-item")
            if not slider:
                await asyncio.sleep(1)
                if "login" not in page.url.lower():
                    print("  ✓✓✓ 滑块消失且已跳转，验证成功!")
                    return True
                print("  ✗ 滑块元素消失")
                return False

            # 执行拖动
            try:
                await drag_slider_precisely(page, distance, start_x, start_y)

                # 等待服务器响应
                print("  等待服务器验证...")
                try:
                    await page.wait_for_url(lambda url: "login" not in url.lower(), timeout=4000)
                    print(f"  ✓✓✓ 成功! 正确距离是 {distance:.0f}px")
                    return True
                except:
                    # 额外等待
                    await asyncio.sleep(1.5)

                    # 再次检查
                    if "login" not in page.url.lower():
                        print(f"  ✓✓✓ 成功(延迟响应)! 正确距离是 {distance:.0f}px")
                        return True

                    # 检查是否显示错误
                    error = await page.query_selector(".slide-verify-slider-mask-item-fail")
                    if error:
                        print("  ✗ 验证失败，显示错误标识")
                    else:
                        print("  ? 结果不明确")

                    # 如果还有尝试次数，刷新验证码
                    if attempt < len(distances_to_try) - 1:
                        await asyncio.sleep(0.8)

                        refresh_btn = await page.query_selector(".slide-verify-slider-mask-refresh-icon")
                        if refresh_btn:
                            print("  ↻ 刷新验证码，重新检测缺口...")
                            await refresh_btn.click()
                            await asyncio.sleep(1.8)

                            # 重新检测新验证码的缺口位置
                            gap_result = await detect_puzzle_gap(page)
                            if gap_result:
                                new_gap_x, _ = gap_result
                                new_distance = await calculate_drag_distance(page, new_gap_x)
                                if new_distance:
                                    # 用新检测的距离替换后续尝试
                                    distances_to_try = distances_to_try[:attempt] + [
                                        new_distance,
                                        new_distance + 2,
                                        new_distance - 2,
                                    ]

                            # 重新获取滑块位置
                            slider = await page.query_selector(".slide-verify-slider-mask-item")
                            if slider:
                                slider_box = await slider.bounding_box()
                                start_x = slider_box['x'] + slider_box['width'] / 2
                                start_y = slider_box['y'] + slider_box['height'] / 2

            except Exception as e:
                print(f"  ⚠ 拖动出错: {e}")
                continue

        print("\n  ✗ 所有尝试均失败")
        return False

    except Exception as e:
        print(f"\n✗ 验证码处理出错: {e}")
        import traceback
        traceback.print_exc()
        return False


async def login(headless: bool = False) -> bool:
    """执行自动登录"""

    async with async_playwright() as p:
        print("启动浏览器...")
        browser = await p.chromium.launch(
            headless=headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        try:
            # 访问登录页
            print(f"访问登录页: {LOGIN_URL}")
            await page.goto(LOGIN_URL, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(1)
            print("✓ 页面加载完成\n")

            # 填写表单
            print("填写登录信息...")
            await page.fill('input[type="text"]', USERNAME)
            print(f"✓ 用户名: {USERNAME}")

            await asyncio.sleep(0.3)

            await page.fill('input[type="password"]', PASSWORD)
            print("✓ 密码: ********")

            await asyncio.sleep(0.3)

            # 点击登录按钮
            print("✓ 点击登录按钮\n")
            await page.click('button[type="submit"]')
            await asyncio.sleep(1.5)

            # 保存验证码截图
            await page.screenshot(path="captcha_puzzle.png")
            print("📸 验证码截图: captcha_puzzle.png\n")

            # 解决验证码 - 最多2次完整尝试
            success = False
            for main_attempt in range(1, 3):
                print(f"\n{'='*60}")
                print(f"第 {main_attempt}/2 次登录尝试")
                print('='*60)

                success = await solve_captcha_smart(page)

                if success:
                    print(f"\n✓✓✓ 第{main_attempt}次尝试成功!")
                    break

                if main_attempt < 2:
                    print("\n⚠ 本次尝试失败，重新加载页面...")
                    await page.reload(wait_until="networkidle")
                    await asyncio.sleep(1)

                    # 重新填写表单
                    await page.fill('input[type="text"]', USERNAME)
                    await page.fill('input[type="password"]', PASSWORD)
                    await page.click('button[type="submit"]')
                    await asyncio.sleep(1.5)

            if not success:
                print("\n✗✗✗ 所有登录尝试都失败了")
                await page.screenshot(path="login_all_failed.png")
                return False

            # 验证登录状态
            await asyncio.sleep(2)
            final_url = page.url
            print(f"\n最终URL: {final_url}")

            if "login" in final_url.lower():
                print("✗ 仍在登录页面")
                await page.screenshot(path="still_login.png")
                return False

            print("✓✓✓ 登录成功!")
            await page.screenshot(path="login_success.png")
            print("📸 成功截图: login_success.png")

            # 保存session
            session_file = Path("codex2_session.json")
            with open(session_file, 'w') as f:
                json.dump({
                    "cookies": await context.cookies(),
                    "storage_state": await context.storage_state(),
                    "url": final_url,
                }, f, indent=2)
            print(f"✓ Session已保存: {session_file}")

            # 保持浏览器打开以便观察
            if not headless:
                print("\n浏览器将保持打开10秒...")
                await asyncio.sleep(10)

            return True

        except Exception as e:
            print(f"\n✗ 登录过程出错: {e}")
            import traceback
            traceback.print_exc()
            try:
                await page.screenshot(path="error_exception.png")
            except:
                pass
            return False
        finally:
            await browser.close()
            print("\n浏览器已关闭")


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Codex2自动登录脚本")
    parser.add_argument("--headless", action="store_true", help="无头模式运行")
    args = parser.parse_args()

    print("=" * 60)
    print("Codex2 自动登录脚本")
    print("智能拼图缺口检测 + 精确拖动")
    print("=" * 60)
    print()

    success = await login(headless=args.headless)

    print("\n" + "=" * 60)
    if success:
        print("✓✓✓ 登录成功")
    else:
        print("✗✗✗ 登录失败")
        print("\n调试提示:")
        print("1. 查看生成的截图文件")
        print("2. 检查用户名和密码是否正确")
        print("3. 确认网络连接正常")
    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
