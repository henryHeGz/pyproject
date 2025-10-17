# Docker 快速开始

## 前置要求

- Docker 20.10+
- Docker Compose 1.29+

## 快速启动

### 方式一：使用管理脚本（推荐）

```bash
# 赋予脚本执行权限（首次运行）
chmod +x docker.sh

# 启动服务（默认使用 SQLite）
./docker.sh start

# 使用 PostgreSQL
./docker.sh start postgres

# 使用 MySQL
./docker.sh start mysql

# 查看服务状态
./docker.sh ps

# 查看日志
./docker.sh logs

# 停止服务
./docker.sh stop
```

### 方式二：使用 Docker Compose

```bash
# SQLite 版本（最简单）
docker-compose up -d

# PostgreSQL 版本
docker-compose --profile postgres up -d

# MySQL 版本
docker-compose --profile mysql up -d
```

## 访问地址

- **SQLite 版本**: http://localhost:8000
- **PostgreSQL 版本**: http://localhost:8001
- **MySQL 版本**: http://localhost:8002
- **API 文档**: http://localhost:8000/docs

## 数据持久化

所有重要数据都已挂载到宿主机：

```
项目目录/
├── data/              # SQLite 数据库文件
├── csv_exports/       # CSV 导出文件
├── flfg_downloads/    # 下载的法律法规文档
└── logs/              # 应用日志
```

即使删除容器，这些数据也会保留。

## 常用操作

### 查看日志

```bash
# 实时查看所有日志
./docker.sh logs

# 查看特定服务日志
./docker.sh logs chinatax-scraper
```

### 进入容器

```bash
# 进入默认容器
./docker.sh exec

# 进入特定容器
./docker.sh exec chinatax-scraper-postgres
```

### 备份数据

```bash
./docker.sh backup
```

备份文件将保存在 `backups/` 目录下。

### 重启服务

```bash
./docker.sh restart
```

## 环境变量配置

创建 `.env` 文件来自定义配置：

```bash
# 复制示例文件
cp .env.example .env

# 编辑配置
vim .env
```

主要配置项：

```env
# 数据库类型
DB_TYPE=sqlite

# SQLite 配置
SQLITE_DB_PATH=/app/data/chinatax.db

# MySQL 配置（如果使用 MySQL）
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=chinatax
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=chinatax
```

## 故障排查

### 容器无法启动

```bash
# 查看容器日志
docker-compose logs chinatax-scraper

# 检查容器状态
docker-compose ps
```

### 端口冲突

如果端口 8000 已被占用，修改 `docker-compose.yml`：

```yaml
ports:
  - "8080:8000"  # 改为其他端口
```

### 数据库连接失败

```bash
# 检查数据库服务
docker-compose ps postgres  # 或 mysql

# 测试数据库连接
docker-compose exec chinatax-scraper python -c "from config.db_config import test_connection; print(test_connection())"
```

### 清理重建

```bash
# 停止并删除所有容器
docker-compose down

# 重新构建并启动
docker-compose up -d --build
```

## 进阶使用

### 使用自定义数据库

如果您已有 MySQL/PostgreSQL 服务，可以修改环境变量连接：

```yaml
environment:
  - DB_TYPE=mysql
  - MYSQL_HOST=your-db-host
  - MYSQL_PORT=3306
  - MYSQL_USER=your-user
  - MYSQL_PASSWORD=your-password
  - MYSQL_DATABASE=chinatax
```

### 生产部署建议

1. **使用外部数据库**：不使用 docker-compose 中的数据库服务
2. **添加反向代理**：使用 Nginx 处理 HTTPS 和负载均衡
3. **设置资源限制**：限制容器的 CPU 和内存使用
4. **定期备份**：设置定时任务自动备份数据

### 性能优化

编辑 `docker-compose.yml` 添加资源限制：

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

## 完整清理

⚠️ **警告：这将删除所有数据！**

```bash
# 使用管理脚本
./docker.sh destroy

# 或手动执行
docker-compose down -v
rm -rf data/ csv_exports/ flfg_downloads/ logs/
```

## 获取帮助

```bash
# 查看管理脚本帮助
./docker.sh help

# 查看详细文档
cat README.Docker.md
```

## 技术支持

如遇到问题，请检查：

1. Docker 和 Docker Compose 版本是否满足要求
2. 端口 8000/8001/8002 是否被占用
3. 是否有足够的磁盘空间
4. 容器日志中的错误信息

更多信息请参阅 [完整 Docker 部署指南](README.Docker.md)。
