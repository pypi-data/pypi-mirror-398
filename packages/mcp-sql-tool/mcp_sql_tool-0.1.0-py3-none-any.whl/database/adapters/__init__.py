"""数据库适配器模块"""

from .base import DatabaseAdapter, QueryResult, TableSchema
from .mysql import MySQLAdapter
from .postgresql import PostgreSQLAdapter
from .sqlite import SQLiteAdapter
from .clickhouse import ClickHouseAdapter

__all__ = [
    "DatabaseAdapter",
    "QueryResult",
    "TableSchema",
    "MySQLAdapter",
    "PostgreSQLAdapter",
    "SQLiteAdapter",
    "ClickHouseAdapter",
]

