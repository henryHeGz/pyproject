# 多阶段构建 - Stage 1: 基础镜像
FROM python:3.11-slim AS base

# 设置工作目录
WORKDIR /app

# 安装系统依赖（Playwright需要的浏览器依赖）
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: 依赖安装
FROM base AS dependencies

# 复制项目配置文件
COPY pyproject.toml ./

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# 安装Playwright浏览器
RUN playwright install chromium && \
    playwright install-deps chromium

# Stage 3: 最终镜像
FROM dependencies AS final

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p csv_exports flfg_downloads logs

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    DB_TYPE=sqlite \
    SQLITE_DB_PATH=/app/data/chinatax.db

# 创建数据目录
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/database/stats')" || exit 1

# 启动命令（使用入口脚本，自动初始化数据库）
CMD ["python", "docker_entrypoint.py"]
