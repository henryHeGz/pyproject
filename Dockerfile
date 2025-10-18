# 使用 Playwright 官方镜像作为基座（已包含浏览器和所有依赖）
FROM mcr.microsoft.com/playwright/python:v1.55.0-noble AS base
# 设置工作目录
WORKDIR /app

# Stage 2: 依赖安装
FROM base AS dependencies

# 复制应用代码（需要在安装前复制，因为 pyproject.toml 依赖这些目录）
COPY . .

# 配置 pip 使用国内镜像源（可选，加速安装）
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set install.trusted-host mirrors.aliyun.com

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Stage 3: 最终镜像
FROM dependencies AS final

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
