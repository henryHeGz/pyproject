# 数据库配置指南

## 概述

项目支持两种数据库：**SQLite**（默认）和 **MySQL**。

- **SQLite**: 轻量级、零配置、单文件数据库，适合开发和小规模使用
- **MySQL**: 功能强大的关系型数据库，适合生产环境和大规模数据

## 快速开始（SQLite）

SQLite 是默认选项，无需额外配置：

```bash
# 1. 初始化数据库（自动创建 chinatax.db 文件）
python db_config.py

# 2. 开始使用
python flfg_scraper/chinatax_scraper.py
python comments_scraper/chinatax_comments_scraper.py
```

数据库文件默认位置：`./chinatax.db`

## 切换到 MySQL

### 1. 安装 MySQL 驱动

```bash
pip install pymysql
```

### 2. 设置环境变量

```bash
# 指定数据库类型为 mysql
export DB_TYPE=mysql

# 配置 MySQL 连接信息
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=chinatax
```

### 3. 初始化数据库

```bash
python db_config.py
```

## 环境变量配置

### SQLite 配置

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `DB_TYPE` | `sqlite` | 数据库类型 |
| `SQLITE_DB_PATH` | `chinatax.db` | 数据库文件路径 |

### MySQL 配置

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `DB_TYPE` | `sqlite` | 设置为 `mysql` |
| `MYSQL_HOST` | `localhost` | MySQL 服务器地址 |
| `MYSQL_PORT` | `3306` | MySQL 端口 |
| `MYSQL_USER` | `root` | MySQL 用户名 |
| `MYSQL_PASSWORD` | (空) | MySQL 密码 |
| `MYSQL_DATABASE` | `chinatax` | 数据库名称 |

## 数据迁移

### 从 CSV 迁移到数据库

```bash
# 使用 SQLite（默认）
python migrate_csv_to_db.py --init --all

# 使用 MySQL
export DB_TYPE=mysql
python migrate_csv_to_db.py --init --all

# 指定 CSV 文件
python migrate_csv_to_db.py --flfg chinatax_flfg.csv --comments chinatax_comments.csv
```

### 在 SQLite 和 MySQL 之间迁移

**从 SQLite 导出到 MySQL：**

```bash
# 1. 使用 SQLite 导出数据到 CSV
export DB_TYPE=sqlite
python -c "
from db_config import get_db_cursor
import csv

with get_db_cursor() as cursor:
    cursor.execute('SELECT * FROM flfg_records')
    rows = cursor.fetchall()

with open('export_flfg.csv', 'w', encoding='utf-8-sig', newline='') as f:
    if rows:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
"

# 2. 切换到 MySQL 并导入
export DB_TYPE=mysql
python migrate_csv_to_db.py --init --flfg export_flfg.csv
```

## 使用示例

### 基本操作（适用于两种数据库）

```python
from db_config import get_db_cursor

# 查询记录
with get_db_cursor() as cursor:
    cursor.execute("SELECT * FROM flfg_records WHERE downloaded = 'N' LIMIT 10")
    records = cursor.fetchall()
    for record in records:
        print(record['title'])

# 插入记录
with get_db_cursor() as cursor:
    cursor.execute("""
        INSERT INTO flfg_records (id, title, document_no, publish_date, link, downloaded)
        VALUES (%(id)s, %(title)s, %(document_no)s, %(publish_date)s, %(link)s, %(downloaded)s)
    """, {
        'id': 'abc123...',
        'title': '测试标题',
        'document_no': '国税发[2024]001号',
        'publish_date': '2024-01-01',
        'link': 'https://example.com',
        'downloaded': 'N'
    })

# 更新记录
with get_db_cursor() as cursor:
    cursor.execute("""
        UPDATE flfg_records SET downloaded = 'Y' WHERE id = %(id)s
    """, {'id': 'abc123...'})
```

### 切换数据库类型

```bash
# 使用 SQLite
export DB_TYPE=sqlite
python flfg_scraper/chinatax_scraper.py

# 使用 MySQL
export DB_TYPE=mysql
python flfg_scraper/chinatax_scraper.py
```

## 数据库架构

两种数据库使用相同的表结构：

### flfg_records（法律法规记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(32) | MD5唯一标识（主键）|
| title | TEXT | 标题 |
| document_no | VARCHAR(255) | 发文字号 |
| publish_date | VARCHAR(50) | 成文日期 |
| link | TEXT | 链接 |
| downloaded | VARCHAR(1)/ENUM | 是否下载（'Y'/'N'）|
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### comment_records（留言记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(32) | MD5唯一标识（主键）|
| question | TEXT | 留言问题 |
| date | VARCHAR(50) | 日期 |
| link | TEXT | 链接地址 |
| downloaded | VARCHAR(1)/ENUM | 是否下载（'Y'/'N'）|
| question_content | TEXT | 问的内容 |
| answer_content | TEXT | 答的内容 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

## SQLite vs MySQL 对比

| 特性 | SQLite | MySQL |
|------|--------|-------|
| 安装配置 | ✅ 无需配置 | ⚠️ 需要安装服务器 |
| 依赖 | ✅ Python内置 | ⚠️ 需要安装pymysql |
| 性能（小数据） | ✅ 快速 | ⚠️ 稍慢（网络开销）|
| 性能（大数据） | ⚠️ 受限 | ✅ 优秀 |
| 并发写入 | ⚠️ 单写入锁 | ✅ 支持高并发 |
| 数据备份 | ✅ 复制文件即可 | ⚠️ 需要mysqldump |
| 适用场景 | 开发、个人使用 | 生产、多用户 |

## 常见操作

### 查看数据库统计

```bash
# SQLite
python -c "
from db_config import get_db_cursor
with get_db_cursor() as cursor:
    cursor.execute('SELECT COUNT(*) as total FROM flfg_records')
    print('法律法规记录:', cursor.fetchone()['total'])
    cursor.execute('SELECT COUNT(*) as total FROM comment_records')
    print('留言记录:', cursor.fetchone()['total'])
"

# 或直接使用 sqlite3 命令
sqlite3 chinatax.db "SELECT COUNT(*) FROM flfg_records;"
```

### 备份数据库

```bash
# SQLite - 直接复制文件
cp chinatax.db chinatax_backup_$(date +%Y%m%d).db

# MySQL
mysqldump -u root -p chinatax > chinatax_backup_$(date +%Y%m%d).sql
```

### 恢复数据库

```bash
# SQLite - 直接替换文件
cp chinatax_backup_20240101.db chinatax.db

# MySQL
mysql -u root -p chinatax < chinatax_backup_20240101.sql
```

### 查看数据库内容

```bash
# SQLite - 使用命令行工具
sqlite3 chinatax.db
> .tables                    # 查看所有表
> .schema flfg_records       # 查看表结构
> SELECT * FROM flfg_records LIMIT 10;  # 查询数据
> .exit

# MySQL
mysql -u root -p chinatax
> SHOW TABLES;
> DESCRIBE flfg_records;
> SELECT * FROM flfg_records LIMIT 10;
> EXIT;
```

## 故障排查

### SQLite 常见问题

**问题：数据库文件被锁定**
```bash
# 检查是否有其他进程在使用数据库
lsof chinatax.db

# 等待所有连接关闭，或重启相关进程
```

**问题：数据库损坏**
```bash
# 尝试恢复
sqlite3 chinatax.db ".recover" | sqlite3 chinatax_recovered.db
```

### MySQL 常见问题

**问题：连接被拒绝**
```bash
# 检查 MySQL 服务是否运行
systemctl status mysql    # Linux
brew services list        # macOS

# 检查端口是否被占用
netstat -an | grep 3306
```

**问题：权限错误**
```sql
-- 授予用户权限
GRANT ALL PRIVILEGES ON chinatax.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
```

### 测试数据库连接

```bash
# 测试当前配置的数据库
python db_config.py

# 或使用测试脚本
python -c "from db_config import test_connection, DB_TYPE; print(f'数据库类型: {DB_TYPE}'); print('连接成功' if test_connection() else '连接失败')"
```

## 性能优化建议

### SQLite 优化

```python
from db_config import get_connection

conn = get_connection()
conn.execute("PRAGMA journal_mode=WAL")      # 提高并发性能
conn.execute("PRAGMA synchronous=NORMAL")    # 平衡性能和安全性
conn.execute("PRAGMA cache_size=10000")      # 增加缓存
conn.execute("PRAGMA temp_store=MEMORY")     # 临时表存于内存
```

### MySQL 优化

- 使用索引加速查询（已自动创建）
- 调整 `innodb_buffer_pool_size`
- 定期执行 `OPTIMIZE TABLE` 整理表

## 开发建议

1. **开发环境使用 SQLite**：快速、方便、零配置
2. **生产环境使用 MySQL**：稳定、高性能、支持并发
3. **定期备份数据**：无论使用哪种数据库
4. **使用 `get_db_cursor()` 上下文管理器**：自动处理事务和连接

## 更多信息

- SQLite文档：https://www.sqlite.org/docs.html
- MySQL文档：https://dev.mysql.com/doc/
- PyMySQL文档：https://pymysql.readthedocs.io/
- 项目文档：[DATABASE_MIGRATION.md](DATABASE_MIGRATION.md)
