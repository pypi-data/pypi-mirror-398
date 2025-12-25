"""MySQL 数据库适配器"""

import time
from typing import List, Dict, Any, Optional
import pymysql
from .base import DatabaseAdapter, QueryResult, TableSchema


class MySQLAdapter(DatabaseAdapter):
    """MySQL 数据库适配器"""

    def connect(self):
        """建立 MySQL 连接"""
        self.connection = pymysql.connect(
            host=self.config.get("host", "localhost"),
            port=self.config.get("port", 3306),
            user=self.config.get("user"),
            password=self.config.get("password"),
            database=self.config.get("database"),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
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
        if rows and isinstance(rows[0], dict):
            result_rows = rows
        else:
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            result_rows = [dict(zip(columns, row)) for row in rows]

        columns = list(result_rows[0].keys()) if result_rows else []
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
        cursor.execute(f"DESCRIBE `{table_name}`")
        columns_data = cursor.fetchall()

        columns = []
        for col in columns_data:
            columns.append({
                "name": col["Field"],
                "type": col["Type"],
                "null": col["Null"] == "YES",
                "key": col["Key"],
                "default": col["Default"],
                "extra": col["Extra"],
            })

        # 获取索引信息
        cursor.execute(f"SHOW INDEX FROM `{table_name}`")
        indexes_data = cursor.fetchall()
        indexes = []
        for idx in indexes_data:
            indexes.append({
                "name": idx["Key_name"],
                "column": idx["Column_name"],
                "unique": idx["Non_unique"] == 0,
                "type": idx["Index_type"],
            })

        # 获取外键信息
        cursor.execute(
            """
            SELECT 
                CONSTRAINT_NAME,
                COLUMN_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = %s
            AND REFERENCED_TABLE_NAME IS NOT NULL
            """,
            (table_name,),
        )
        foreign_keys_data = cursor.fetchall()
        foreign_keys = []
        for fk in foreign_keys_data:
            foreign_keys.append({
                "name": fk["CONSTRAINT_NAME"],
                "column": fk["COLUMN_NAME"],
                "referenced_table": fk["REFERENCED_TABLE_NAME"],
                "referenced_column": fk["REFERENCED_COLUMN_NAME"],
            })

        # 获取表注释
        cursor.execute(
            """
            SELECT TABLE_COMMENT
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = %s
            """,
            (table_name,),
        )
        comment_data = cursor.fetchone()
        comment = comment_data["TABLE_COMMENT"] if comment_data else None

        cursor.close()

        return TableSchema(
            name=table_name,
            columns=columns,
            indexes=indexes,
            foreign_keys=foreign_keys,
            comment=comment,
        )

    def list_tables(self) -> List[str]:
        """列出所有表"""
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = [list(row.values())[0] for row in cursor.fetchall()]
        cursor.close()
        return tables

    def explain_query(self, sql: str) -> Dict[str, Any]:
        """解释查询计划"""
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        cursor.execute(f"EXPLAIN {sql}")
        plan = cursor.fetchall()
        cursor.close()
        return {"plan": plan}

