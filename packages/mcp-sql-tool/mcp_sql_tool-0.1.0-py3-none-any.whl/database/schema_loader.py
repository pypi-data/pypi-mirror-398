"""Schema 加载器"""

from typing import Dict, Any, Optional, List
from .connection_manager import ConnectionManager
from .adapters import TableSchema
from storage import SchemaCache


class SchemaLoader:
    """Schema 加载器，负责从数据库加载表结构信息"""

    def __init__(self, connection_manager: ConnectionManager, schema_cache: SchemaCache):
        """
        初始化 Schema 加载器

        Args:
            connection_manager: 连接管理器实例
            schema_cache: Schema 缓存实例
        """
        self.connection_manager = connection_manager
        self.schema_cache = schema_cache

    def get_table_schema(
        self, database_name: str, table_name: str, use_cache: bool = True
    ) -> TableSchema:
        """
        获取表结构

        Args:
            database_name: 数据库连接名称
            table_name: 表名
            use_cache: 是否使用缓存

        Returns:
            表结构信息
        """
        # 检查缓存
        if use_cache:
            cached = self.schema_cache.get_schema(database_name, table_name)
            if cached:
                # 将缓存的字典转换为 TableSchema 对象
                return TableSchema(**cached)

        # 从数据库加载
        adapter = self.connection_manager.get_adapter(database_name)
        if not adapter:
            raise ValueError(f"Database '{database_name}' not found")

        adapter.connect()
        schema = adapter.get_schema(table_name)

        # 存入缓存
        if use_cache:
            self.schema_cache.set_schema(
                database_name,
                {
                    "name": schema.name,
                    "columns": schema.columns,
                    "indexes": schema.indexes,
                    "foreign_keys": schema.foreign_keys,
                    "comment": schema.comment,
                },
                table_name=table_name,
            )

        return schema

    def get_database_schema(
        self, database_name: str, use_cache: bool = True
    ) -> Dict[str, TableSchema]:
        """
        获取整个数据库的 Schema

        Args:
            database_name: 数据库连接名称
            use_cache: 是否使用缓存

        Returns:
            表名到表结构的映射字典
        """
        # 检查缓存
        if use_cache:
            cached = self.schema_cache.get_schema(database_name, table_name=None)
            if cached:
                return {
                    name: TableSchema(**schema_data)
                    for name, schema_data in cached.items()
                }

        # 从数据库加载
        adapter = self.connection_manager.get_adapter(database_name)
        if not adapter:
            raise ValueError(f"Database '{database_name}' not found")

        adapter.connect()
        tables = adapter.list_tables()

        schemas = {}
        for table_name in tables:
            schema = adapter.get_schema(table_name)
            schemas[table_name] = schema

            # 缓存单个表
            if use_cache:
                self.schema_cache.set_schema(
                    database_name,
                    {
                        "name": schema.name,
                        "columns": schema.columns,
                        "indexes": schema.indexes,
                        "foreign_keys": schema.foreign_keys,
                        "comment": schema.comment,
                    },
                    table_name=table_name,
                )

        # 缓存整个数据库 Schema
        if use_cache:
            schemas_dict = {
                name: {
                    "name": schema.name,
                    "columns": schema.columns,
                    "indexes": schema.indexes,
                    "foreign_keys": schema.foreign_keys,
                    "comment": schema.comment,
                }
                for name, schema in schemas.items()
            }
            self.schema_cache.set_schema(database_name, schemas_dict, table_name=None)

        return schemas

    def list_tables(self, database_name: str) -> List[str]:
        """
        列出数据库中的所有表

        Args:
            database_name: 数据库连接名称

        Returns:
            表名列表
        """
        adapter = self.connection_manager.get_adapter(database_name)
        if not adapter:
            raise ValueError(f"Database '{database_name}' not found")

        adapter.connect()
        return adapter.list_tables()

    def refresh_schema(self, database_name: str, table_name: Optional[str] = None):
        """
        刷新 Schema 缓存

        Args:
            database_name: 数据库连接名称
            table_name: 表名，None 表示刷新整个数据库
        """
        self.schema_cache.refresh_cache(database_name, table_name)

