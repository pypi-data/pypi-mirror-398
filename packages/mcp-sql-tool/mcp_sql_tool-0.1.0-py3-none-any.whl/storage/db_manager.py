"""存储数据库管理器：使用 SQLite 管理元数据"""

import sqlite3
import os
from typing import Optional
from pathlib import Path
from datetime import datetime


class DBManager:
    """SQLite 数据库管理器，用于存储查询历史、Schema 缓存等元数据"""

    def __init__(self, db_path: str = "data/mcp_sql_tool.db"):
        """
        初始化数据库管理器

        Args:
            db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_database()

    def _ensure_db_dir(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            Path(db_dir).mkdir(parents=True, exist_ok=True)

    def _init_database(self):
        """初始化数据库表结构"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 查询历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_query TEXT NOT NULL,
                generated_sql TEXT,
                executed_sql TEXT,
                database_name TEXT,
                execution_time_ms INTEGER,
                row_count INTEGER,
                success BOOLEAN,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Schema 缓存表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                database_name TEXT NOT NULL,
                table_name TEXT,
                schema_json TEXT NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                UNIQUE(database_name, table_name)
            )
        """)

        # 结果缓存表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS result_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sql_hash TEXT NOT NULL UNIQUE,
                sql_query TEXT NOT NULL,
                result_json TEXT,
                database_name TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)

        # 审计日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                sql_query TEXT,
                database_name TEXT,
                user_id TEXT,
                success BOOLEAN,
                error_message TEXT,
                execution_time_ms INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def execute_query(self, query: str, params: tuple = ()) -> list:
        """执行查询并返回结果"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """执行更新操作并返回影响的行数"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected

    def close(self):
        """关闭数据库连接（SQLite 不需要显式关闭，但提供接口）"""
        pass

