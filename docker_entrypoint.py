#!/usr/bin/env python3
"""
Docker 容器启动入口脚本
初始化数据库并启动 Web 应用
"""

import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    print("=" * 60)
    print("正鹏AI数据获取平台 - Docker 容器启动")
    print("=" * 60)

    # 初始化数据库
    try:
        print("\n[1/2] 初始化数据库...")
        from config.db_config import init_database, test_connection, DB_TYPE

        init_database()

        if test_connection():
            print("✅ 数据库连接测试成功！")
        else:
            print("❌ 数据库连接测试失败！")
            sys.exit(1)

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 启动 Web 应用
    try:
        print("\n[2/2] 启动 Web 应用...")
        import uvicorn
        from web_app import app

        print("\n访问地址: http://0.0.0.0:8000")
        print("API文档: http://0.0.0.0:8000/docs\n")

        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

    except Exception as e:
        print(f"❌ Web 应用启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
