"""PostgreSQL 数据库适配器"""

import time
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from .base import DatabaseAdapter, QueryResult, TableSchema


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL 数据库适配器"""

    def connect(self):
        """建立 PostgreSQL 连接"""
        self.connection = psycopg2.connect(
            host=self.config.get("host", "localhost"),
            port=self.config.get("port", 5432),
            user=self.config.get("user"),
            password=self.config.get("password"),
            database=self.config.get("database"),
            cursor_factory=RealDictCursor,
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
        result_rows = [dict(row) for row in rows]
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
        cursor.execute(
            """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
            """,
            (table_name,),
        )
        columns_data = cursor.fetchall()
        columns = []
        for col in columns_data:
            columns.append({
                "name": col["column_name"],
                "type": col["data_type"],
                "null": col["is_nullable"] == "YES",
                "default": col["column_default"],
                "max_length": col["character_maximum_length"],
            })

        # 获取索引信息
        cursor.execute(
            """
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = %s
            """,
            (table_name,),
        )
        indexes_data = cursor.fetchall()
        indexes = []
        for idx in indexes_data:
            indexes.append({
                "name": idx["indexname"],
                "definition": idx["indexdef"],
            })

        # 获取外键信息
        cursor.execute(
            """
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = %s
            """,
            (table_name,),
        )
        foreign_keys_data = cursor.fetchall()
        foreign_keys = []
        for fk in foreign_keys_data:
            foreign_keys.append({
                "name": fk["constraint_name"],
                "column": fk["column_name"],
                "referenced_table": fk["foreign_table_name"],
                "referenced_column": fk["foreign_column_name"],
            })

        # 获取表注释
        cursor.execute(
            """
            SELECT obj_description(oid) as comment
            FROM pg_class
            WHERE relname = %s
            """,
            (table_name,),
        )
        comment_data = cursor.fetchone()
        comment = comment_data["comment"] if comment_data and comment_data["comment"] else None

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
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            """
        )
        tables = [row["table_name"] for row in cursor.fetchall()]
        cursor.close()
        return tables

    def explain_query(self, sql: str) -> Dict[str, Any]:
        """解释查询计划"""
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        cursor.execute(f"EXPLAIN ANALYZE {sql}")
        plan = cursor.fetchall()
        cursor.close()
        return {"plan": [dict(row) for row in plan]}

