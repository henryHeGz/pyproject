#!/bin/bash

# Docker 配置验证脚本

set -e

echo "======================================"
echo "Docker 配置验证"
echo "======================================"
echo ""

# 检查 Docker
echo "[1/5] 检查 Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo "✅ $DOCKER_VERSION"
else
    echo "❌ Docker 未安装"
    exit 1
fi

# 检查 Docker Compose
echo ""
echo "[2/5] 检查 Docker Compose..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo "✅ $COMPOSE_VERSION"
else
    echo "❌ Docker Compose 未安装"
    exit 1
fi

# 检查 Dockerfile
echo ""
echo "[3/5] 检查 Dockerfile..."
if [ -f "Dockerfile" ]; then
    echo "✅ Dockerfile 存在"
else
    echo "❌ Dockerfile 不存在"
    exit 1
fi

# 检查 docker-compose.yml
echo ""
echo "[4/5] 检查 docker-compose.yml..."
if [ -f "docker-compose.yml" ]; then
    echo "✅ docker-compose.yml 存在"

    # 验证配置文件语法
    if docker-compose config > /dev/null 2>&1; then
        echo "✅ docker-compose.yml 语法正确"
    else
        echo "❌ docker-compose.yml 语法错误"
        docker-compose config
        exit 1
    fi
else
    echo "❌ docker-compose.yml 不存在"
    exit 1
fi

# 检查项目文件
echo ""
echo "[5/5] 检查项目文件..."
REQUIRED_FILES=(
    "web_app.py"
    "docker_entrypoint.py"
    "pyproject.toml"
    "config/db_config.py"
)

ALL_EXISTS=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file 不存在"
        ALL_EXISTS=false
    fi
done

if [ "$ALL_EXISTS" = false ]; then
    exit 1
fi

# 所有检查通过
echo ""
echo "======================================"
echo "✅ 所有检查通过！"
echo "======================================"
echo ""
echo "您可以使用以下命令启动服务："
echo ""
echo "  ./docker.sh start           # SQLite 版本（推荐）"
echo "  ./docker.sh start postgres  # PostgreSQL 版本"
echo "  ./docker.sh start mysql     # MySQL 版本"
echo ""
echo "或者："
echo ""
echo "  docker-compose up -d        # SQLite 版本"
echo ""
