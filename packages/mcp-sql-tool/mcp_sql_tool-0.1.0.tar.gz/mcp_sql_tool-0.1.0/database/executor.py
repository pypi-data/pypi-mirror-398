"""SQL 执行引擎"""

import time
from typing import Optional, Dict, Any
from .connection_manager import ConnectionManager
from .adapters import QueryResult


class Executor:
    """SQL 执行引擎"""

    def __init__(self, connection_manager: ConnectionManager):
        """
        初始化执行器

        Args:
            connection_manager: 连接管理器实例
        """
        self.connection_manager = connection_manager

    def execute(
        self,
        database_name: str,
        sql: str,
        limit: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> QueryResult:
        """
        执行 SQL 查询

        Args:
            database_name: 数据库连接名称
            sql: SQL 查询语句
            limit: 结果行数限制
            timeout: 查询超时时间（秒）

        Returns:
            查询结果

        Raises:
            Exception: 执行失败时抛出异常
        """
        adapter = self.connection_manager.get_adapter(database_name)
        if not adapter:
            raise ValueError(f"Database '{database_name}' not found")

        # 连接数据库
        adapter.connect()

        try:
            # 执行查询
            start_time = time.time()
            result = adapter.execute_query(sql, limit=limit)

            # 检查超时
            if timeout:
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    raise TimeoutError(f"Query timeout after {timeout} seconds")

            return result
        finally:
            # 注意：这里不关闭连接，由连接池管理
            pass

    def explain(
        self, database_name: str, sql: str
    ) -> Dict[str, Any]:
        """
        解释查询计划

        Args:
            database_name: 数据库连接名称
            sql: SQL 查询语句

        Returns:
            查询计划信息
        """
        adapter = self.connection_manager.get_adapter(database_name)
        if not adapter:
            raise ValueError(f"Database '{database_name}' not found")

        adapter.connect()
        return adapter.explain_query(sql)

