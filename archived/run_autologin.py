#!/usr/bin/env python3
"""
Codex2 自动登录 - 快速使用示例

这是一个简单的示例，展示如何使用autologin_codex2.py进行自动登录
"""

import subprocess
import sys
from pathlib import Path


def main():
    print("=" * 60)
    print("Codex2 自动登录 - 快速启动")
    print("=" * 60)
    print()

    # 检查脚本文件是否存在
    script_path = Path("autologin_codex2.py")
    if not script_path.exists():
        print("❌ 错误: 找不到 autologin_codex2.py")
        print("请确保在正确的目录中运行此脚本")
        return 1

    # 询问用户模式
    print("请选择运行模式:")
    print("  1. 显示浏览器窗口（推荐，可以观察过程）")
    print("  2. 无头模式（后台运行，不显示窗口）")
    print()

    choice = input("请输入选项 (1 或 2，默认1): ").strip() or "1"

    if choice == "1":
        print("\n启动自动登录（显示浏览器）...")
        cmd = [sys.executable, "autologin_codex2.py"]
    elif choice == "2":
        print("\n启动自动登录（无头模式）...")
        cmd = [sys.executable, "autologin_codex2.py", "--headless"]
    else:
        print("❌ 无效选项")
        return 1

    print("-" * 60)
    print()

    # 运行脚本
    try:
        result = subprocess.run(cmd)
        return result.returncode
    except KeyboardInterrupt:
        print("\n\n⚠ 用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
