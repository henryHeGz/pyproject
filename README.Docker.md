# Docker 部署指南

本项目支持使用 Docker 和 Docker Compose 进行容器化部署。

## 快速开始

### 1. 使用 SQLite（默认，最简单）

```bash
# 构建并启动服务
docker-compose up -d

# 访问应用
# http://localhost:8000
```

### 2. 使用 PostgreSQL

```bash
# 启动 PostgreSQL 配置
docker-compose --profile postgres up -d

# 访问应用
# http://localhost:8001
```

### 3. 使用 MySQL

```bash
# 启动 MySQL 配置
docker-compose --profile mysql up -d

# 访问应用
# http://localhost:8002
```

## 架构说明

### 服务配置

项目提供三种数据库配置：

| 服务名 | 端口 | 数据库 | 适用场景 |
|--------|------|--------|----------|
| `chinatax-scraper` | 8000 | SQLite | 开发、测试、小规模部署 |
| `chinatax-scraper-postgres` | 8001 | PostgreSQL | 生产环境、需要高并发 |
| `chinatax-scraper-mysql` | 8002 | MySQL | 生产环境、已有MySQL基础设施 |

### 数据持久化

所有配置都将以下目录挂载到宿主机：

- `./data` - SQLite 数据库文件（仅 SQLite 配置）
- `./csv_exports` - CSV 导出文件
- `./flfg_downloads` - 下载的法律法规文档
- `./logs` - 应用日志文件

## 常用命令

### 启动服务

```bash
# SQLite 版本（默认）
docker-compose up -d

# PostgreSQL 版本
docker-compose --profile postgres up -d

# MySQL 版本
docker-compose --profile mysql up -d

# 查看日志
docker-compose logs -f chinatax-scraper

# 查看特定服务日志
docker-compose logs -f chinatax-scraper-postgres
```

### 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷（谨慎使用！）
docker-compose down -v
```

### 重新构建

```bash
# 重新构建镜像
docker-compose build

# 强制重新构建并启动
docker-compose up -d --build
```

### 数据库管理

#### 初始化数据库

应用启动时会自动初始化数据库表结构，无需手动操作。

#### 备份数据

**SQLite:**
```bash
# 备份 SQLite 数据库
cp ./data/chinatax.db ./data/chinatax.db.backup
```

**PostgreSQL:**
```bash
# 导出数据
docker-compose exec postgres pg_dump -U chinatax chinatax > backup.sql

# 恢复数据
docker-compose exec -T postgres psql -U chinatax chinatax < backup.sql
```

**MySQL:**
```bash
# 导出数据
docker-compose exec mysql mysqldump -u chinatax -pchinatax_password chinatax > backup.sql

# 恢复数据
docker-compose exec -T mysql mysql -u chinatax -pchinatax_password chinatax < backup.sql
```

### 查看运行状态

```bash
# 查看服务状态
docker-compose ps

# 查看资源使用
docker stats

# 进入容器
docker-compose exec chinatax-scraper bash
```

## 环境变量配置

可以通过修改 `docker-compose.yml` 中的环境变量来自定义配置：

### SQLite 配置

```yaml
environment:
  - DB_TYPE=sqlite
  - SQLITE_DB_PATH=/app/data/chinatax.db
```

### PostgreSQL 配置

```yaml
environment:
  - DB_TYPE=mysql  # 注意：代码中使用 mysql 作为 PostgreSQL 的标识
  - MYSQL_HOST=postgres
  - MYSQL_PORT=5432
  - MYSQL_USER=chinatax
  - MYSQL_PASSWORD=chinatax_password
  - MYSQL_DATABASE=chinatax
```

### MySQL 配置

```yaml
environment:
  - DB_TYPE=mysql
  - MYSQL_HOST=mysql
  - MYSQL_PORT=3306
  - MYSQL_USER=chinatax
  - MYSQL_PASSWORD=chinatax_password
  - MYSQL_DATABASE=chinatax
```

## 生产环境建议

### 安全性

1. **修改默认密码**
   - 修改 `docker-compose.yml` 中的数据库密码
   - 使用环境变量文件 `.env` 存储敏感信息

2. **网络隔离**
   - 数据库服务不对外暴露端口
   - 仅应用服务对外提供访问

3. **使用反向代理**
   ```yaml
   # 添加 Nginx 反向代理
   nginx:
     image: nginx:alpine
     ports:
       - "80:80"
       - "443:443"
     volumes:
       - ./nginx.conf:/etc/nginx/nginx.conf
     depends_on:
       - chinatax-scraper
   ```

### 性能优化

1. **资源限制**
   ```yaml
   services:
     chinatax-scraper:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
           reservations:
             cpus: '1'
             memory: 2G
   ```

2. **数据库调优**
   - PostgreSQL: 调整 `shared_buffers`, `work_mem` 等参数
   - MySQL: 调整 `innodb_buffer_pool_size` 等参数

### 监控与日志

1. **日志管理**
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```

2. **健康检查**
   - 已内置健康检查机制
   - 可集成 Prometheus + Grafana 监控

## 故障排查

### 容器无法启动

```bash
# 查看详细日志
docker-compose logs chinatax-scraper

# 检查容器状态
docker-compose ps
```

### 数据库连接失败

```bash
# 检查数据库服务是否健康
docker-compose ps postgres

# 测试数据库连接
docker-compose exec chinatax-scraper python -c "from db_config import test_connection; print(test_connection())"
```

### Playwright 浏览器错误

```bash
# 重新安装浏览器
docker-compose exec chinatax-scraper playwright install chromium
```

## 开发模式

如果需要在本地开发并实时看到代码更改：

```yaml
# 添加代码挂载（仅开发环境）
volumes:
  - .:/app
  - /app/__pycache__  # 排除缓存
```

然后重启服务：
```bash
docker-compose up -d
```

## 更多信息

- [项目主文档](readme.md)
- [快速开始指南](QUICKSTART.md)
- [CLAUDE 开发指南](CLAUDE.md)
