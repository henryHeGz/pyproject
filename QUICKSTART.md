# 快速开始指南

## 📦 安装

```bash
# 克隆项目
git clone <repository-url>
cd pyproject

# 安装依赖
pip install .

# 安装 Playwright 浏览器
playwright install
```

## 🚀 快速开始（使用 SQLite，推荐）

SQLite 是默认数据库，无需任何配置即可使用：

```bash
# 1. 初始化数据库
python db_config.py

# 2. 爬取法律法规数据
python flfg_scraper/chinatax_scraper.py

# 3. 爬取留言数据
python comments_scraper/chinatax_comments_scraper.py

# 4. 下载文档
python flfg_scraper/chinatax_scheduler.py --not-downloaded
```

就是这么简单！数据会自动保存到 `chinatax.db` 文件中。

## 🔄 从 CSV 迁移（可选）

如果你有现有的 CSV 数据：

```bash
# 迁移所有 CSV 数据到数据库
python migrate_csv_to_db.py --init --all

# 或指定具体文件
python migrate_csv_to_db.py --flfg chinatax_flfg.csv --comments chinatax_comments.csv
```

## 💾 数据库选择

### 选项 1: SQLite（默认，推荐用于开发）

✅ **优点：**
- 零配置，开箱即用
- 单文件存储，易于备份
- Python 内置支持
- 非常适合个人使用和开发

```bash
# 默认就是 SQLite，无需配置
python db_config.py
```

### 选项 2: MySQL（用于生产环境）

✅ **优点：**
- 高性能、支持高并发
- 适合多用户、大规模数据
- 企业级功能

```bash
# 1. 安装 MySQL 驱动
pip install pymysql

# 2. 设置环境变量
export DB_TYPE=mysql
export MYSQL_HOST=localhost
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=chinatax

# 3. 初始化数据库
python db_config.py
```

## 📚 常用命令

### 法律法规爬虫

```bash
# 爬取数据
python flfg_scraper/chinatax_scraper.py

# 从第5页开始爬取
python flfg_scraper/chinatax_scraper.py --start-page 5

# 只爬取10页
python flfg_scraper/chinatax_scraper.py --page-count 10

# 有头模式（显示浏览器）
python flfg_scraper/chinatax_scraper.py --headed
```

### 留言爬虫

```bash
# 爬取留言列表
python comments_scraper/chinatax_comments_scraper.py

# 爬取前10页
python comments_scraper/chinatax_comments_scraper.py --max-pages 10

# 爬取并自动下载详情
python comments_scraper/chinatax_comments_scraper.py --auto-download

# 只下载未下载记录的详情
python comments_scraper/chinatax_comments_scraper.py --download-content
```

### 文档下载调度器

```bash
# 下载第一条未下载的记录
python flfg_scraper/chinatax_scheduler.py

# 下载所有未下载的记录
python flfg_scraper/chinatax_scheduler.py --not-downloaded

# 下载前5条未下载的记录
python flfg_scraper/chinatax_scheduler.py --not-downloaded --limit 5

# 根据ID下载指定记录
python flfg_scraper/chinatax_scheduler.py --ids "abc123,def456"
```

## 🔍 查看数据

### 使用 SQLite 命令行

```bash
# 进入 SQLite 命令行
sqlite3 chinatax.db

# 查看所有表
.tables

# 查看表结构
.schema flfg_records

# 查询数据
SELECT COUNT(*) FROM flfg_records;
SELECT * FROM flfg_records LIMIT 10;

# 查询未下载的记录
SELECT COUNT(*) FROM flfg_records WHERE downloaded = 'N';

# 退出
.exit
```

### 使用 Python 脚本

```python
from db_config import get_db_cursor

# 查询记录数量
with get_db_cursor() as cursor:
    cursor.execute("SELECT COUNT(*) as total FROM flfg_records")
    print("法律法规记录数:", cursor.fetchone()['total'])

    cursor.execute("SELECT COUNT(*) as total FROM comment_records")
    print("留言记录数:", cursor.fetchone()['total'])

    # 查询未下载的记录
    cursor.execute("SELECT COUNT(*) as total FROM flfg_records WHERE downloaded = 'N'")
    print("未下载的法律法规:", cursor.fetchone()['total'])
```

## 📚 更多文档

| 文档分类 | 链接 |
|---------|------|
| **完整索引** | [📚 文档索引](docs/INDEX.md) - 所有文档的完整目录 |
| **数据库** | [数据库配置](docs/guides/DATABASE_GUIDE.md) - SQLite 和 MySQL 详细配置 |
| | [数据库迁移](docs/migration/DATABASE_MIGRATION.md) - 从 CSV 迁移到数据库 |
| **Web界面** | [Web管理界面](docs/guides/WEB_GUIDE.md) - Web 后台使用指南 |
| **项目架构** | [CLAUDE.md](CLAUDE.md) - 项目架构和开发指南 |

---

**最后更新**: 2025-10-14
