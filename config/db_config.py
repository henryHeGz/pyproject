"""
数据库配置和连接管理模块

支持 MySQL 和 SQLite 两种数据库。
通过环境变量 DB_TYPE 选择数据库类型（默认: sqlite）
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Dict, Any

# 数据库类型配置
DB_TYPE = os.environ.get("DB_TYPE", "sqlite").lower()  # mysql 或 sqlite
# 将 SQLite 数据库存储在 data 目录
SQLITE_DB_PATH = os.environ.get("SQLITE_DB_PATH", str(Path(__file__).parent.parent / "data" / "chinatax.db"))

# MySQL配置（仅当DB_TYPE为mysql时使用）
MYSQL_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": os.environ.get("MYSQL_DATABASE", "chinatax"),
    "charset": "utf8mb4",
}


class DictCursorWrapper:
    """SQLite游标包装器，提供字典形式的结果（兼容PyMySQL的DictCursor）"""

    def __init__(self, cursor):
        self.cursor = cursor
        self.cursor.row_factory = sqlite3.Row

    def execute(self, sql: str, params=None):
        """执行SQL语句"""
        if params is None:
            return self.cursor.execute(sql)

        # 转换 %(name)s 格式为 :name 格式（MySQL -> SQLite）
        if isinstance(params, dict):
            # 替换 %(key)s 为 :key
            import re
            sql_sqlite = re.sub(r'%\((\w+)\)s', r':\1', sql)
            return self.cursor.execute(sql_sqlite, params)
        else:
            # 参数是元组或列表，使用 ? 占位符
            sql_sqlite = sql.replace('%s', '?')
            return self.cursor.execute(sql_sqlite, params)

    def fetchone(self):
        """获取一行结果"""
        row = self.cursor.fetchone()
        if row:
            return dict(row)
        return None

    def fetchall(self):
        """获取所有结果"""
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def fetchmany(self, size=None):
        """获取指定数量的结果"""
        rows = self.cursor.fetchmany(size)
        return [dict(row) for row in rows]

    def close(self):
        """关闭游标"""
        self.cursor.close()

    @property
    def rowcount(self):
        """返回影响的行数"""
        return self.cursor.rowcount

    @property
    def lastrowid(self):
        """返回最后插入的行ID"""
        return self.cursor.lastrowid


def get_connection():
    """获取数据库连接"""
    if DB_TYPE == "mysql":
        try:
            import pymysql
            return pymysql.connect(**MYSQL_CONFIG)
        except ImportError:
            raise ImportError(
                "pymysql 未安装。请运行：pip install pymysql"
            )
    elif DB_TYPE == "sqlite":
        # 确保数据库目录存在
        db_path = Path(SQLITE_DB_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_path))
        # 启用外键约束
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    else:
        raise ValueError(f"不支持的数据库类型: {DB_TYPE}")


@contextmanager
def get_db_cursor(dict_cursor: bool = True) -> Generator:
    """
    获取数据库游标的上下文管理器

    Args:
        dict_cursor: 是否使用字典游标（默认True，返回字典形式的结果）

    Yields:
        游标对象

    Example:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM flfg_records")
            results = cursor.fetchall()
    """
    conn = get_connection()

    if DB_TYPE == "mysql":
        try:
            from pymysql.cursors import DictCursor
            cursor_class = DictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_class)
        except ImportError:
            raise ImportError("pymysql 未安装。请运行：pip install pymysql")
    else:  # sqlite
        cursor = conn.cursor()
        if dict_cursor:
            cursor = DictCursorWrapper(cursor)

    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if hasattr(cursor, 'close'):
            cursor.close()
        conn.close()


def init_database() -> None:
    """
    初始化数据库和表结构

    创建两个表：
    1. flfg_records - 法律法规记录
    2. comment_records - 留言记录
    """
    if DB_TYPE == "mysql":
        _init_mysql_database()
    elif DB_TYPE == "sqlite":
        _init_sqlite_database()
    else:
        raise ValueError(f"不支持的数据库类型: {DB_TYPE}")


def _init_mysql_database() -> None:
    """初始化MySQL数据库"""
    try:
        import pymysql
    except ImportError:
        raise ImportError("pymysql 未安装。请运行：pip install pymysql")

    # 先连接到 MySQL 服务器（不指定数据库）
    conn_config = MYSQL_CONFIG.copy()
    database_name = conn_config.pop("database")

    conn = pymysql.connect(**conn_config)
    cursor = conn.cursor()

    try:
        # 创建数据库（如果不存在）
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✓ 数据库 '{database_name}' 已就绪")

        # 选择数据库
        cursor.execute(f"USE `{database_name}`")

        # 创建任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `tasks` (
                `task_id` VARCHAR(64) PRIMARY KEY COMMENT '任务唯一标识',
                `task_type` VARCHAR(50) NOT NULL COMMENT '任务类型',
                `task_category` VARCHAR(50) NOT NULL COMMENT '任务分类',
                `status` VARCHAR(20) NOT NULL COMMENT '任务状态',
                `params` TEXT COMMENT '任务参数JSON',
                `message` TEXT COMMENT '任务消息',
                `result` TEXT COMMENT '任务结果JSON',
                `error` TEXT COMMENT '错误信息',
                `csv_path` VARCHAR(255) COMMENT 'CSV文件路径',
                `start_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
                `end_time` TIMESTAMP NULL COMMENT '结束时间',
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                INDEX `idx_task_status` (`status`),
                INDEX `idx_task_category` (`task_category`),
                INDEX `idx_task_start_time` (`start_time`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务记录表'
        """)
        print("✓ 表 'tasks' 已就绪")

        # 创建法律法规记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `flfg_records` (
                `id` VARCHAR(32) PRIMARY KEY COMMENT 'MD5唯一标识',
                `title` TEXT NOT NULL COMMENT '标题',
                `document_no` VARCHAR(255) NOT NULL COMMENT '发文字号',
                `publish_date` VARCHAR(50) NOT NULL COMMENT '成文日期',
                `link` TEXT COMMENT '链接',
                `downloaded` ENUM('Y', 'N') DEFAULT 'N' COMMENT '是否下载',
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX `idx_downloaded` (`downloaded`),
                INDEX `idx_publish_date` (`publish_date`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='法律法规记录表'
        """)
        print("✓ 表 'flfg_records' 已就绪")

        # 创建留言记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `comment_records` (
                `id` VARCHAR(32) PRIMARY KEY COMMENT 'MD5唯一标识',
                `question` TEXT NOT NULL COMMENT '留言问题',
                `date` VARCHAR(50) NOT NULL COMMENT '日期',
                `link` TEXT COMMENT '链接地址',
                `downloaded` ENUM('Y', 'N') DEFAULT 'N' COMMENT '是否下载',
                `question_content` TEXT COMMENT '问的内容',
                `answer_content` TEXT COMMENT '答的内容',
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX `idx_downloaded` (`downloaded`),
                INDEX `idx_date` (`date`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='留言记录表'
        """)
        print("✓ 表 'comment_records' 已就绪")

        conn.commit()
        print(f"\n✅ MySQL数据库初始化完成！")

    finally:
        cursor.close()
        conn.close()


def _init_sqlite_database() -> None:
    """初始化SQLite数据库"""
    db_path = Path(SQLITE_DB_PATH)
    print(f"✓ 数据库文件: {db_path.absolute()}")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # 创建法律法规记录表
        # 创建任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id VARCHAR(64) PRIMARY KEY,
                task_type VARCHAR(50) NOT NULL,
                task_category VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL,
                params TEXT,
                message TEXT,
                result TEXT,
                error TEXT,
                csv_path VARCHAR(255),
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_task_status ON tasks(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_task_category ON tasks(task_category)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_task_start_time ON tasks(start_time)
        """)
        print("✓ 表 'tasks' 已就绪")

        # 创建法律法规记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flfg_records (
                id VARCHAR(32) PRIMARY KEY,
                title TEXT NOT NULL,
                document_no VARCHAR(255) NOT NULL,
                publish_date VARCHAR(50) NOT NULL,
                link TEXT,
                downloaded VARCHAR(1) DEFAULT 'N' CHECK(downloaded IN ('Y', 'N')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_flfg_downloaded ON flfg_records(downloaded)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_flfg_publish_date ON flfg_records(publish_date)
        """)
        print("✓ 表 'flfg_records' 已就绪")

        # 创建留言记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comment_records (
                id VARCHAR(32) PRIMARY KEY,
                question TEXT NOT NULL,
                date VARCHAR(50) NOT NULL,
                link TEXT,
                downloaded VARCHAR(1) DEFAULT 'N' CHECK(downloaded IN ('Y', 'N')),
                question_content TEXT,
                answer_content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_comment_downloaded ON comment_records(downloaded)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_comment_date ON comment_records(date)
        """)
        print("✓ 表 'comment_records' 已就绪")

        # 创建更新时间触发器（SQLite不支持ON UPDATE，需要用触发器）
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_flfg_records_timestamp
            AFTER UPDATE ON flfg_records
            FOR EACH ROW
            BEGIN
                UPDATE flfg_records SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        """)

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_comment_records_timestamp
            AFTER UPDATE ON comment_records
            FOR EACH ROW
            BEGIN
                UPDATE comment_records SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        """)

        # 为任务表创建更新触发器
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_tasks_timestamp
            AFTER UPDATE ON tasks
            FOR EACH ROW
            BEGIN
                UPDATE tasks SET end_time = CURRENT_TIMESTAMP WHERE task_id = NEW.task_id AND NEW.status IN ('completed', 'failed');
            END
        """)

        conn.commit()
        print(f"\n✅ SQLite数据库初始化完成！")

    finally:
        cursor.close()
        conn.close()


def test_connection() -> bool:
    """
    测试数据库连接

    Returns:
        bool: 连接成功返回True，失败返回False
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if DB_TYPE == "sqlite":
            return result[0] == 1
        else:  # mysql
            return result[0] == 1
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


if __name__ == "__main__":
    """直接运行此文件可初始化数据库"""
    print(f"数据库类型: {DB_TYPE.upper()}\n")

    if DB_TYPE == "mysql":
        print(f"数据库配置:")
        print(f"  Host: {MYSQL_CONFIG['host']}")
        print(f"  Port: {MYSQL_CONFIG['port']}")
        print(f"  User: {MYSQL_CONFIG['user']}")
        print(f"  Database: {MYSQL_CONFIG['database']}")
    else:  # sqlite
        print(f"数据库文件: {Path(SQLITE_DB_PATH).absolute()}")

    print("\n开始初始化数据库...")
    init_database()

    print("\n测试数据库连接...")
    if test_connection():
        print("✅ 数据库连接测试成功！")
    else:
        print("❌ 数据库连接测试失败！")
