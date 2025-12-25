"""ClickHouse 数据库适配器"""

import time
from typing import List, Dict, Any, Optional
from clickhouse_driver import Client
from .base import DatabaseAdapter, QueryResult, TableSchema


class ClickHouseAdapter(DatabaseAdapter):
    """ClickHouse 数据库适配器"""

    def connect(self):
        """建立 ClickHouse 连接"""
        self.connection = Client(
            host=self.config.get("host", "localhost"),
            port=self.config.get("port", 9000),
            user=self.config.get("user", "default"),
            password=self.config.get("password", ""),
            database=self.config.get("database", "default"),
        )
        return self.connection

    def disconnect(self):
        """关闭连接"""
        if self.connection:
            self.connection.disconnect()
            self.connection = None

    def execute_query(self, sql: str, limit: Optional[int] = None) -> QueryResult:
        """执行查询"""
        if not self.connection:
            self.connect()

        # 如果有限制，添加 LIMIT 子句
        if limit and "LIMIT" not in sql.upper():
            sql = f"{sql.rstrip(';')} LIMIT {limit}"

        start_time = time.time()
        result = self.connection.execute(sql, with_column_types=True)
        execution_time_ms = int((time.time() - start_time) * 1000)

        rows_data, columns_info = result
        columns = [col[0] for col in columns_info]

        # 转换为字典列表
        result_rows = [dict(zip(columns, row)) for row in rows_data]

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

        # 获取列信息
        columns_query = f"DESCRIBE TABLE `{table_name}`"
        columns_data = self.connection.execute(columns_query)

        columns = []
        for col in columns_data:
            columns.append({
                "name": col[0],
                "type": col[1],
                "default_type": col[2],
                "default_expression": col[3],
                "comment": col[4],
                "codec_expression": col[5],
                "ttl_expression": col[6],
            })

        # ClickHouse 索引信息
        indexes_query = f"SHOW INDEX FROM `{table_name}`"
        try:
            indexes_data = self.connection.execute(indexes_query)
            indexes = []
            for idx in indexes_data:
                indexes.append({
                    "name": idx[0] if len(idx) > 0 else None,
                    "type": idx[1] if len(idx) > 1 else None,
                    "expr": idx[2] if len(idx) > 2 else None,
                })
        except Exception:
            indexes = []

        # ClickHouse 不支持传统外键
        foreign_keys = []

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

        result = self.connection.execute("SHOW TABLES")
        tables = [row[0] for row in result]
        return tables

    def explain_query(self, sql: str) -> Dict[str, Any]:
        """解释查询计划"""
        if not self.connection:
            self.connect()

        try:
            plan = self.connection.execute(f"EXPLAIN {sql}")
            return {"plan": [dict(row) for row in plan]}
        except Exception as e:
            return {"error": str(e)}

