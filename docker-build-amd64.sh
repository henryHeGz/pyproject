#!/bin/bash

# 项目的 AMD64 镜像构建脚本

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="${1:-chinatax-scraper:amd64}"
PLATFORM="linux/amd64"
DOCKERFILE="${DOCKERFILE:-Dockerfile}"

echo "======================================"
echo "Docker 构建 (仅 $PLATFORM)"
echo "--------------------------------------"
echo "镜像名称: $IMAGE_NAME"
echo "Dockerfile: $DOCKERFILE"
echo "构建目录: $SCRIPT_DIR"
echo "======================================"
echo ""

if ! command -v docker >/dev/null 2>&1; then
    echo "❌ 未找到 docker 命令，请先安装 Docker。" >&2
    exit 1
fi

if docker buildx version >/dev/null 2>&1; then
    docker buildx build \
        --platform "$PLATFORM" \
        --load \
        -t "$IMAGE_NAME" \
        -f "$SCRIPT_DIR/$DOCKERFILE" \
        "$SCRIPT_DIR"
else
    echo "⚠️ 未检测到 docker buildx，改用 docker build。"
    echo "   如需跨平台构建，请安装并启用 Docker Buildx。"
    docker build \
        --platform "$PLATFORM" \
        -t "$IMAGE_NAME" \
        -f "$SCRIPT_DIR/$DOCKERFILE" \
        "$SCRIPT_DIR"
fi

echo ""
echo "✅ 镜像构建完成: $IMAGE_NAME ($PLATFORM)"
