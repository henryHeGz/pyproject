#!/bin/bash
# 国家税务总局爬虫Web管理后台启动脚本

echo "======================================"
echo "国家税务总局爬虫Web管理后台"
echo "======================================"
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3"
    exit 1
fi

# 检查是否安装了依赖
echo "🔍 检查依赖..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 安装依赖..."
    pip install -e .
fi

echo ""
echo "🚀 启动Web服务器..."
echo ""
echo "访问地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动服务
python3 web_app.py
