# Docker 部署文件清单

本次为项目添加了完整的 Docker 部署支持。以下是所有新增的文件和说明：

## 核心文件

### 1. Dockerfile
多阶段构建的 Docker 镜像配置文件
- 基于 Python 3.11-slim
- 自动安装 Playwright 和 Chromium
- 支持健康检查
- 优化镜像大小

**位置**: `./Dockerfile`

### 2. docker-compose.yml
Docker Compose 编排配置文件
- 提供 3 种数据库配置：SQLite、PostgreSQL、MySQL
- 支持数据持久化
- 使用 profiles 控制服务启动

**位置**: `./docker-compose.yml`

### 3. docker_entrypoint.py
容器启动入口脚本
- 自动初始化数据库
- 启动 FastAPI Web 应用
- 完整的错误处理

**位置**: `./docker_entrypoint.py`

## 管理脚本

### 4. docker.sh
Docker 容器管理脚本（推荐使用）
- 一键启动/停止/重启服务
- 查看日志和状态
- 数据备份功能
- 资源清理

**位置**: `./docker.sh`

**使用示例**:
```bash
./docker.sh start         # 启动服务（SQLite）
./docker.sh start postgres  # 启动服务（PostgreSQL）
./docker.sh logs          # 查看日志
./docker.sh backup        # 备份数据
./docker.sh help          # 查看帮助
```

### 5. docker-verify.sh
Docker 配置验证脚本
- 检查 Docker 和 Docker Compose 安装
- 验证配置文件语法
- 检查必需的项目文件

**位置**: `./docker-verify.sh`

## 配置文件

### 6. .dockerignore
Docker 构建忽略文件清单
- 排除不必要的文件
- 减小镜像体积
- 保护敏感信息

**位置**: `./.dockerignore`

### 7. .env.example
环境变量配置示例
- 数据库配置模板
- 所有可配置项说明

**位置**: `./.env.example`

## 文档

### 8. README.Docker.md
完整的 Docker 部署指南（详细版）
- 架构说明
- 详细配置说明
- 生产环境建议
- 故障排查指南

**位置**: `./README.Docker.md`

### 9. DOCKER_QUICKSTART.md
Docker 快速开始指南（简洁版）
- 一页纸快速上手
- 常用命令速查
- 快速故障排查

**位置**: `./DOCKER_QUICKSTART.md`

### 10. DOCKER_FILES_SUMMARY.md
本文件 - Docker 文件清单

**位置**: `./DOCKER_FILES_SUMMARY.md`

## 目录结构

```
pyproject/
├── Dockerfile                 # Docker 镜像构建文件
├── docker-compose.yml         # Docker Compose 编排文件
├── docker_entrypoint.py       # 容器启动入口脚本
├── docker.sh                  # 管理脚本（推荐）
├── docker-verify.sh           # 配置验证脚本
├── .dockerignore              # Docker 忽略文件
├── .env.example               # 环境变量示例
├── README.Docker.md           # 详细部署指南
├── DOCKER_QUICKSTART.md       # 快速开始指南
├── DOCKER_FILES_SUMMARY.md    # 本文件
│
├── data/                      # SQLite 数据库（Docker 持久化）
├── csv_exports/               # CSV 导出（Docker 持久化）
├── flfg_downloads/            # 下载文档（Docker 持久化）
└── logs/                      # 日志文件（Docker 持久化）
```

## 快速开始

1. **验证环境**
   ```bash
   ./docker-verify.sh
   ```

2. **启动服务**（三选一）
   ```bash
   # SQLite（推荐，最简单）
   ./docker.sh start
   
   # PostgreSQL
   ./docker.sh start postgres
   
   # MySQL
   ./docker.sh start mysql
   ```

3. **访问应用**
   - SQLite: http://localhost:8000
   - PostgreSQL: http://localhost:8001
   - MySQL: http://localhost:8002

## 主要特性

✅ **开箱即用**: 一条命令启动完整环境  
✅ **多数据库支持**: SQLite/PostgreSQL/MySQL  
✅ **数据持久化**: 容器删除数据不丢失  
✅ **自动初始化**: 自动创建数据库和表结构  
✅ **健康检查**: 内置容器健康监控  
✅ **资源优化**: 多阶段构建，镜像体积小  
✅ **完善文档**: 详细的使用和部署文档  

## 技术栈

- **基础镜像**: python:3.11-slim
- **Web 框架**: FastAPI + Uvicorn
- **浏览器自动化**: Playwright + Chromium
- **数据库**: SQLite / PostgreSQL / MySQL
- **容器编排**: Docker Compose

## 生产部署建议

1. 使用外部数据库（PostgreSQL 或 MySQL）
2. 配置反向代理（Nginx）处理 HTTPS
3. 设置资源限制（CPU、内存）
4. 配置日志轮转
5. 定期备份数据

详见 [README.Docker.md](README.Docker.md) 的生产环境部分。

## 更新日志

### v1.0.0 (2025-10-17)
- ✨ 新增完整的 Docker 部署支持
- ✨ 新增多数据库配置（SQLite/PostgreSQL/MySQL）
- ✨ 新增容器管理脚本
- ✨ 新增自动初始化和健康检查
- 📝 新增完善的部署文档

## 问题反馈

如遇到 Docker 部署相关问题，请：

1. 检查 Docker 和 Docker Compose 版本
2. 运行 `./docker-verify.sh` 验证配置
3. 查看容器日志 `./docker.sh logs`
4. 参考故障排查文档

---

**注意**: 所有脚本文件（`.sh` 和 `.py`）都已添加执行权限，可直接运行。
