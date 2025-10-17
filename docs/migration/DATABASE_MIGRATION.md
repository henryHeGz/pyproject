# MySQL数据库迁移指南

## 概述

项目已从CSV文件存储重构为MySQL数据库存储。本文档说明如何配置和使用新的数据库系统。

## 数据库架构

### 表结构

**1. flfg_records（法律法规记录表）**
```sql
CREATE TABLE `flfg_records` (
    `id` VARCHAR(32) PRIMARY KEY COMMENT 'MD5唯一标识',
    `title` TEXT NOT NULL COMMENT '标题',
    `document_no` VARCHAR(255) NOT NULL COMMENT '发文字号',
    `publish_date` VARCHAR(50) NOT NULL COMMENT '成文日期',
    `link` TEXT COMMENT '链接',
    `downloaded` ENUM('Y', 'N') DEFAULT 'N' COMMENT '是否下载',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
);
```

**2. comment_records（留言记录表）**
```sql
CREATE TABLE `comment_records` (
    `id` VARCHAR(32) PRIMARY KEY COMMENT 'MD5唯一标识',
    `question` TEXT NOT NULL COMMENT '留言问题',
    `date` VARCHAR(50) NOT NULL COMMENT '日期',
    `link` TEXT COMMENT '链接地址',
    `downloaded` ENUM('Y', 'N') DEFAULT 'N' COMMENT '是否下载',
    `question_content` TEXT COMMENT '问的内容',
    `answer_content` TEXT COMMENT '答的内容',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
);
```

## 安装和配置

### 1. 安装依赖

```bash
pip install pymysql
# 或者重新安装整个项目
pip install .
```

### 2. 配置数据库连接

通过环境变量配置数据库连接信息：

```bash
# Linux/Mac
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=chinatax

# Windows
set MYSQL_HOST=localhost
set MYSQL_PORT=3306
set MYSQL_USER=root
set MYSQL_PASSWORD=your_password
set MYSQL_DATABASE=chinatax
```

或者在代码中修改 `db_config.py` 的默认值。

### 3. 初始化数据库

```bash
# 方法1: 直接运行db_config.py
python db_config.py

# 方法2: 使用迁移脚本的--init选项
python migrate_csv_to_db.py --init
```

## 数据迁移

### 从CSV迁移到MySQL

如果你有现有的CSV文件，使用迁移脚本导入数据：

```bash
# 迁移所有默认CSV文件
python migrate_csv_to_db.py --init --all

# 只迁移法律法规CSV
python migrate_csv_to_db.py --flfg chinatax_flfg.csv

# 只迁移留言CSV
python migrate_csv_to_db.py --comments chinatax_comments.csv

# 指定不同位置的CSV文件
python migrate_csv_to_db.py --flfg flfg_scraper/chinatax_flfg.csv --comments comments_scraper/chinatax_comments.csv
```

## 使用说明

### 爬取法律法规数据

```bash
# 爬取数据（不再需要--csv参数）
python flfg_scraper/chinatax_scraper.py

# 从第5页开始爬取
python flfg_scraper/chinatax_scraper.py --start-page 5

# 只爬取10页
python flfg_scraper/chinatax_scraper.py --page-count 10
```

### 爬取留言数据

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

### 调度下载文档

```bash
# 下载第一条未下载的记录（不再需要--csv参数）
python flfg_scraper/chinatax_scheduler.py

# 下载所有未下载的记录
python flfg_scraper/chinatax_scheduler.py --not-downloaded

# 下载前5条
python flfg_scraper/chinatax_scheduler.py --not-downloaded --limit 5

# 根据ID下载
python flfg_scraper/chinatax_scheduler.py --ids "abc123,def456"
```

## 主要变化

### 1. 命令行参数变化

**法律法规爬虫 (chinatax_scraper.py)**
- ❌ 移除: `--csv` 参数
- ✅ 保留: `--headed`, `--start-page`, `--page-count`

**留言爬虫 (chinatax_comments_scraper.py)**
- ❌ 移除: `--csv` 参数
- ✅ 保留: `--headed`, `--start-page`, `--max-pages`, `--download-content`, `--auto-download`, `--max-downloads`

**调度器 (chinatax_scheduler.py)**
- ❌ 移除: `--csv` 参数
- ✅ 保留: `--output-dir`, `--headed`, `--ids`, `--not-downloaded`, `--limit`, `--fail-on-error`

### 2. 数据去重机制

- 使用数据库的 `ON DUPLICATE KEY UPDATE` 实现自动去重
- 主键为MD5哈希值，确保记录唯一性
- 更新时自动更新 `updated_at` 时间戳

### 3. 性能优化

- 数据库索引：在 `downloaded`、`publish_date`、`date` 字段上建立索引
- 批量操作：支持批量插入和更新
- 事务支持：使用事务保证数据一致性

## 数据库管理

### 查询记录数量

```sql
-- 查询法律法规记录总数
SELECT COUNT(*) FROM flfg_records;

-- 查询未下载的记录
SELECT COUNT(*) FROM flfg_records WHERE downloaded = 'N';

-- 查询留言记录总数
SELECT COUNT(*) FROM comment_records;
```

### 导出数据到CSV

```sql
-- 导出法律法规记录
SELECT id as '序号', title as '标题', document_no as '发文字号',
       publish_date as '成文日期', link as '链接', downloaded as '是否下载'
FROM flfg_records
INTO OUTFILE '/tmp/flfg_export.csv'
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n';
```

### 备份数据库

```bash
# 备份整个数据库
mysqldump -u root -p chinatax > chinatax_backup.sql

# 只备份表结构
mysqldump -u root -p --no-data chinatax > chinatax_schema.sql

# 只备份数据
mysqldump -u root -p --no-create-info chinatax > chinatax_data.sql
```

### 恢复数据库

```bash
# 恢复数据库
mysql -u root -p chinatax < chinatax_backup.sql
```

## 故障排查

### 连接失败

```bash
# 测试数据库连接
python -c "from db_config import test_connection; print('成功' if test_connection() else '失败')"
```

**常见问题：**
1. 检查MySQL服务是否运行
2. 确认用户名和密码正确
3. 确认数据库已创建
4. 检查防火墙设置

### 表不存在

```bash
# 重新初始化数据库
python db_config.py
```

### 字符编码问题

数据库和表都使用 `utf8mb4` 编码，支持所有Unicode字符包括emoji。

如果遇到编码问题，检查：
1. 数据库字符集：`SHOW CREATE DATABASE chinatax;`
2. 表字符集：`SHOW CREATE TABLE flfg_records;`
3. 连接字符集：在 `db_config.py` 中设置 `charset='utf8mb4'`

## 环境变量配置示例

### Linux/Mac (.env 文件)
```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=your_secure_password
export MYSQL_DATABASE=chinatax
```

### Docker Compose 示例
```yaml
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: chinatax
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  scraper:
    build: .
    environment:
      MYSQL_HOST: mysql
      MYSQL_PORT: 3306
      MYSQL_USER: root
      MYSQL_PASSWORD: root_password
      MYSQL_DATABASE: chinatax
    depends_on:
      - mysql

volumes:
  mysql_data:
```

## 进一步开发

### 添加新字段

1. 修改数据库表结构：
```sql
ALTER TABLE flfg_records ADD COLUMN new_field VARCHAR(255);
```

2. 修改对应的 dataclass 和 `to_dict()` 方法

3. 更新插入/更新SQL语句

### 添加新表

1. 在 `db_config.py` 的 `init_database()` 中添加建表SQL
2. 创建对应的数据模型类
3. 实现CRUD操作函数

## 技术栈

- **数据库**: MySQL 5.7+
- **Python驱动**: PyMySQL
- **字符编码**: UTF-8 (utf8mb4)
- **存储引擎**: InnoDB

## 联系支持

如遇问题，请查看：
- 项目文档: CLAUDE.md
- 数据库配置: db_config.py
- 迁移脚本: migrate_csv_to_db.py
