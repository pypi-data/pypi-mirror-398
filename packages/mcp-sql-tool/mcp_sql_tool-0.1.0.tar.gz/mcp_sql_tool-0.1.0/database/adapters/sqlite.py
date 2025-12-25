"""SQLite 数据库适配器"""

import time
import sqlite3
from typing import List, Dict, Any, Optional
from .base import DatabaseAdapter, QueryResult, TableSchema


class SQLiteAdapter(DatabaseAdapter):
    """SQLite 数据库适配器"""

    def connect(self):
        """建立 SQLite 连接"""
        db_path = self.config.get("database") or self.config.get("path")
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        return self.connection

    def disconnect(self):
        """关闭连接"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_query(self, sql: str, limit: Optional[int] = None) -> QueryResult:
        """执行查询"""
        if not self.connection:
            self.connect()

        # 如果有限制，添加 LIMIT 子句
        if limit and "LIMIT" not in sql.upper():
            sql = f"{sql.rstrip(';')} LIMIT {limit}"

        start_time = time.time()
        cursor = self.connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        execution_time_ms = int((time.time() - start_time) * 1000)

        # 转换为字典列表
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        result_rows = [dict(zip(columns, row)) for row in rows]
        cursor.close()

        return QueryResult(
            rows=result_rows,
            columns=columns,
            row_count=len(result_rows),
            execution_time_ms=execution_time_ms,
        )

    def get_schema(self, table_name: str) -> TableSchema:
        """获取表结构"""
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()

        # 获取列信息
        cursor.execute(f"PRAGMA table_info(`{table_name}`)")
        columns_data = cursor.fetchall()
        columns = []
        for col in columns_data:
            columns.append({
                "name": col[1],
                "type": col[2],
                "null": not col[3],
                "default": col[4],
                "pk": bool(col[5]),
            })

        # 获取索引信息
        cursor.execute(f"PRAGMA index_list(`{table_name}`)")
        indexes_data = cursor.fetchall()
        indexes = []
        for idx in indexes_data:
            index_name = idx[1]
            cursor.execute(f"PRAGMA index_info(`{index_name}`)")
            index_columns = cursor.fetchall()
            indexes.append({
                "name": index_name,
                "unique": bool(idx[2]),
                "columns": [col[2] for col in index_columns],
            })

        # SQLite 外键信息
        cursor.execute(f"PRAGMA foreign_key_list(`{table_name}`)")
        foreign_keys_data = cursor.fetchall()
        foreign_keys = []
        for fk in foreign_keys_data:
            foreign_keys.append({
                "id": fk[0],
                "seq": fk[1],
                "table": fk[2],
                "from": fk[3],
                "to": fk[4],
                "on_update": fk[5],
                "on_delete": fk[6],
                "match": fk[7],
            })

        cursor.close()

        return TableSchema(
            name=table_name,
            columns=columns,
            indexes=indexes,
            foreign_keys=foreign_keys,
            comment=None,
        )

    def list_tables(self) -> List[str]:
        """列出所有表"""
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables

    def explain_query(self, sql: str) -> Dict[str, Any]:
        """解释查询计划"""
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        cursor.execute(f"EXPLAIN QUERY PLAN {sql}")
        plan = cursor.fetchall()
        cursor.close()
        return {"plan": [dict(row) for row in plan]}

