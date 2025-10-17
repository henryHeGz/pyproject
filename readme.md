# 正鹏AI数据获取平台

一个基于 Playwright 的 Python 爬虫项目，用于采集国家税务总局的法律法规和留言数据。支持 SQLite 和 MySQL 双数据库，提供完整的数据采集、存储和管理功能。

## ✨ 主要特性

- 🚀 **双数据库支持**: SQLite（默认）和 MySQL
- 🌐 **Web管理界面**: 基于FastAPI的现代化管理后台（新）
  - 多页签架构：主页、法律法规、留言公开、任务管理
  - 实时任务监控和日志查看
  - CSV导出和数据预览
- 📊 **三大爬虫模块**:
  - 法律法规列表爬虫
  - 留言公开页面爬虫
  - 文档内容下载器
- 🔄 **自动去重**: 基于 MD5 的智能去重机制
- 📦 **零配置**: SQLite 开箱即用，无需额外配置
- 🔌 **灵活切换**: 通过环境变量轻松切换数据库
- 📝 **完善文档**: 详细的使用文档和示例

## 📦 快速安装

### 方式一：使用 Docker（推荐，最简单）

```bash
# 克隆项目
git clone <repository-url>
cd pyproject

# 启动服务（自动构建镜像、初始化数据库）
./docker.sh start

# 访问地址: http://localhost:8000
```

详细说明请参阅 [Docker 快速开始](DOCKER_QUICKSTART.md)

### 方式二：本地安装

```bash
# 克隆项目
git clone <repository-url>
cd pyproject

# 安装依赖
pip install .

# 安装 Playwright 浏览器
playwright install

# 初始化数据库（SQLite，默认）
python config/db_config.py
```

## 🚀 快速开始

### 方式一：使用 Web 界面（推荐）

```bash
# 启动 Web 管理后台
python web_app.py

# 访问地址: http://localhost:8000
```

**Web界面功能**：
- 📊 **主页**: 系统概览、数据统计、快捷入口
- 📚 **法律法规**: 爬取列表、下载详情、数据预览
- 💬 **留言公开**: 爬取留言、下载内容、数据预览
- 📋 **任务管理**: 查看任务状态、导出CSV、查看日志

### 方式二：使用命令行

```bash
# 1. 爬取法律法规数据
python flfg_scraper/chinatax_scraper.py

# 2. 爬取留言数据
python comments_scraper/chinatax_comments_scraper.py

# 3. 下载文档
python flfg_scraper/chinatax_scheduler.py --not-downloaded
```

就是这么简单！数据会自动保存到 `chinatax.db` SQLite 文件中。

## 📚 文档导航

| 分类 | 文档 | 说明 |
|------|------|------|
| **快速开始** | [QUICKSTART.md](QUICKSTART.md) | 5分钟快速上手指南 |
| | [🐳 Docker 快速开始](DOCKER_QUICKSTART.md) | Docker 部署快速指南（推荐） |
| **完整文档** | [📚 文档索引](docs/INDEX.md) | 所有文档的完整索引 |
| | | |
| **部署运维** | [🐋 Docker 部署指南](README.Docker.md) | 完整 Docker 部署文档 |
| | [数据库配置](docs/guides/DATABASE_GUIDE.md) | SQLite 和 MySQL 详细配置 |
| | | |
| **使用指南** | [Web界面](docs/WEB_REFACTOR.md) | Web 界面使用指南（新） |
| | [CSV管理](docs/CSV_MANAGEMENT_UPDATE.md) | CSV 导出文件管理说明 |
| | [文档下载](docs/guides/FLFG_DOWNLOAD_GUIDE.md) | 文档下载功能说明 |
| | [自动登录](docs/guides/AUTOLOGIN_GUIDE.md) | Codex2 自动登录工具 |
| | | |
| **迁移升级** | [数据库迁移](docs/migration/DATABASE_MIGRATION.md) | 从 CSV 迁移到数据库 |
| | [重构总结](docs/migration/REFACTORING_SUMMARY.md) | v2.0 重构技术细节 |
| | | |
| **开发文档** | [CLAUDE.md](CLAUDE.md) | 项目架构和开发指南 |
| | [模块文档](docs/INDEX.md#-模块文档) | 各爬虫模块详细文档 |

## 🏗️ 项目结构

```
pyproject/
├── db_config.py                 # 数据库配置模块（支持 SQLite & MySQL）
├── csv_manager.py               # CSV 文件管理模块（统一路径管理）
├── migrate_csv_to_db.py         # CSV 数据迁移工具
├── migrate_csv_files.py         # CSV 文件路径迁移工具
├── web_app.py                   # Web 管理界面（FastAPI）
├── chinatax.db                  # SQLite 数据库文件（自动生成）
├── csv_exports/                 # 📁 CSV 导出文件目录
│   ├── README.md                # CSV 目录说明
│   └── *.csv                    # 所有导出的 CSV 文件
├── templates/                   # 🌐 Web模板目录（新）
│   ├── index.html               # 主页
│   ├── flfg.html                # 法律法规页面
│   ├── comments.html            # 留言公开页面
│   └── tasks.html               # 任务管理页面
├── static/                      # 📦 静态资源目录（新）
│   └── style.css                # 公共样式文件
├── flfg_scraper/                # 法律法规爬虫模块
│   ├── chinatax_scraper.py      # 列表数据爬虫
│   ├── chinatax_scheduler.py    # 下载调度器
│   ├── chinatax_document_downloader.py  # 文档下载器
│   └── chinatax_content_to_md.py        # 内容转换工具
├── comments_scraper/            # 留言爬虫模块
│   └── chinatax_comments_scraper.py     # 留言数据爬虫
├── pyuser/                      # 用户管理模块
│   └── pyuser.py                # Codex2 自动登录工具
├── docs/                        # 📚 文档目录
│   ├── INDEX.md                 # 文档索引
│   ├── WEB_REFACTOR.md          # Web重构说明（新）
│   ├── guides/                  # 使用指南
│   ├── migration/               # 迁移与升级
│   ├── technical/               # 技术文档
│   └── changelog/               # 更新日志
└── tests/                       # 测试文件
```

## 💾 数据库选择

### SQLite（默认，推荐）

✅ 零配置，开箱即用  
✅ 单文件存储，易于备份  
✅ 适合个人使用和开发

```bash
# 默认就是 SQLite，直接使用
python db_config.py
```

### MySQL（生产环境）

✅ 高性能，支持高并发  
✅ 适合多用户、大规模数据

```bash
# 安装 MySQL 驱动
pip install pymysql

# 设置环境变量
export DB_TYPE=mysql
export MYSQL_HOST=localhost
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=chinatax

# 初始化数据库
python db_config.py
```

## 🎯 使用场景

### 场景 1: 法律法规数据采集

```bash
# 爬取所有新增数据（自动去重）
python flfg_scraper/chinatax_scraper.py

# 从第5页开始爬取
python flfg_scraper/chinatax_scraper.py --start-page 5

# 只爬取前10页
python flfg_scraper/chinatax_scraper.py --page-count 10
```

### 场景 2: 留言数据采集

```bash
# 爬取留言列表
python comments_scraper/chinatax_comments_scraper.py

# 爬取并自动下载详情内容
python comments_scraper/chinatax_comments_scraper.py --auto-download

# 只下载未下载记录的详情
python comments_scraper/chinatax_comments_scraper.py --download-content
```

### 场景 3: 文档批量下载

```bash
# 下载所有未下载的文档
python flfg_scraper/chinatax_scheduler.py --not-downloaded

# 限制下载数量（例如前10条）
python flfg_scraper/chinatax_scheduler.py --not-downloaded --limit 10

# 根据ID列表下载
python flfg_scraper/chinatax_scheduler.py --ids "abc123,def456,ghi789"
```

## 🔍 数据查询

### 使用 SQLite 命令行

```bash
sqlite3 chinatax.db

# 查看表
.tables

# 查询记录数量
SELECT COUNT(*) FROM flfg_records;

# 查询未下载的记录
SELECT * FROM flfg_records WHERE downloaded = 'N' LIMIT 10;

# 退出
.exit
```

### 使用 Python 脚本

```python
from db_config import get_db_cursor

with get_db_cursor() as cursor:
    # 查询记录数量
    cursor.execute("SELECT COUNT(*) as total FROM flfg_records")
    print(f"总记录数: {cursor.fetchone()['total']}")
    
    # 查询未下载的记录
    cursor.execute("SELECT * FROM flfg_records WHERE downloaded = 'N' LIMIT 5")
    for record in cursor.fetchall():
        print(f"标题: {record['title']}")
```

## 🔄 从 CSV 迁移

如果你有现有的 CSV 文件数据：

```bash
# 迁移所有 CSV 文件
python migrate_csv_to_db.py --init --all

# 指定具体文件
python migrate_csv_to_db.py \
  --flfg flfg_scraper/chinatax_flfg.csv \
  --comments comments_scraper/chinatax_comments.csv
```

## 🛠️ 开发技巧

### 调试模式

```bash
# 使用有头模式查看浏览器行为
python flfg_scraper/chinatax_scraper.py --headed
```

### 定时任务

```bash
# 添加到 crontab（每天凌晨2点执行）
crontab -e

# 添加以下行
0 2 * * * cd /path/to/pyproject && python flfg_scraper/chinatax_scraper.py >> cron.log 2>&1
```

### 数据备份

```bash
# SQLite - 复制文件
cp chinatax.db chinatax_backup_$(date +%Y%m%d).db

# MySQL
mysqldump -u root -p chinatax > backup.sql
```

## 📊 数据库架构

### flfg_records（法律法规记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(32) | MD5唯一标识 |
| title | TEXT | 标题 |
| document_no | VARCHAR(255) | 发文字号 |
| publish_date | VARCHAR(50) | 成文日期 |
| link | TEXT | 链接 |
| downloaded | VARCHAR(1) | 是否下载（'Y'/'N'）|
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### comment_records（留言记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(32) | MD5唯一标识 |
| question | TEXT | 留言问题 |
| date | VARCHAR(50) | 日期 |
| link | TEXT | 链接地址 |
| downloaded | VARCHAR(1) | 是否下载（'Y'/'N'）|
| question_content | TEXT | 问的内容 |
| answer_content | TEXT | 答的内容 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

## 🔧 环境变量

### SQLite 配置

```bash
export DB_TYPE=sqlite                    # 数据库类型（默认）
export SQLITE_DB_PATH=chinatax.db        # 数据库文件路径（默认）
```

### MySQL 配置

```bash
export DB_TYPE=mysql                     # 数据库类型
export MYSQL_HOST=localhost              # 服务器地址
export MYSQL_PORT=3306                   # 端口
export MYSQL_USER=root                   # 用户名
export MYSQL_PASSWORD=password           # 密码
export MYSQL_DATABASE=chinatax           # 数据库名
```

## 🐛 故障排查

### SQLite 数据库被锁定

```bash
# 检查是否有其他进程在使用
lsof chinatax.db

# 关闭所有相关进程后重试
```

### MySQL 连接失败

```bash
# 检查 MySQL 服务状态
systemctl status mysql    # Linux
brew services list        # macOS

# 测试连接
python -c "from db_config import test_connection; print('成功' if test_connection() else '失败')"
```

### 爬虫被反爬

```bash
# 使用��头模式查看问题
python flfg_scraper/chinatax_scraper.py --headed

# 在代码中增加等待时间或添加代理
```

## 📈 性能建议

- ✅ 开发环境使用 SQLite
- ✅ 生产环境使用 MySQL
- ✅ 定期备份数据
- ✅ 大量数据时考虑分页查询
- ✅ 使用索引加速查询（已自动创建）

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

[添加你的许可证信息]

## 📞 联系方式

- 项目地址: [GitHub Repository]
- 问题反馈: [Issues]

---

**最后更新**: 2025-10-17
**版本**: 2.1.0（Web界面多页签重构版本）
**文档版本**: 2.1
