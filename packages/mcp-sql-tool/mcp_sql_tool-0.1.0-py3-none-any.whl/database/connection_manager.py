"""数据库连接管理器"""

from typing import Dict, Optional, Any
from .adapters import (
    DatabaseAdapter,
    MySQLAdapter,
    PostgreSQLAdapter,
    SQLiteAdapter,
    ClickHouseAdapter,
)


class ConnectionManager:
    """数据库连接池管理器"""

    def __init__(self):
        """初始化连接管理器"""
        self._adapters: Dict[str, DatabaseAdapter] = {}
        self._configs: Dict[str, Dict[str, Any]] = {}

    def register_database(self, name: str, config: Dict[str, Any]):
        """
        注册数据库连接

        Args:
            name: 数据库连接名称
            config: 数据库配置字典，包含 type, host, port, user, password, database 等
        """
        self._configs[name] = config
        # 延迟创建适配器，在首次使用时创建

    def get_adapter(self, name: str) -> Optional[DatabaseAdapter]:
        """
        获取数据库适配器

        Args:
            name: 数据库连接名称

        Returns:
            数据库适配器实例，如果不存在则返回 None
        """
        if name not in self._adapters:
            if name not in self._configs:
                return None

            config = self._configs[name]
            db_type = config.get("type", "").lower()

            if db_type == "mysql":
                adapter = MySQLAdapter(config)
            elif db_type == "postgresql" or db_type == "postgres":
                adapter = PostgreSQLAdapter(config)
            elif db_type == "sqlite":
                adapter = SQLiteAdapter(config)
            elif db_type == "clickhouse":
                adapter = ClickHouseAdapter(config)
            else:
                raise ValueError(f"Unsupported database type: {db_type}")

            self._adapters[name] = adapter

        return self._adapters[name]

    def test_connection(self, name: str) -> bool:
        """
        测试数据库连接

        Args:
            name: 数据库连接名称

        Returns:
            连接是否成功
        """
        adapter = self.get_adapter(name)
        if not adapter:
            return False

        try:
            return adapter.test_connection()
        except Exception:
            return False

    def disconnect(self, name: Optional[str] = None):
        """
        断开数据库连接

        Args:
            name: 数据库连接名称，None 表示断开所有连接
        """
        if name:
            if name in self._adapters:
                self._adapters[name].disconnect()
                del self._adapters[name]
        else:
            for adapter in self._adapters.values():
                adapter.disconnect()
            self._adapters.clear()

    def list_databases(self) -> list:
        """列出所有已注册的数据库"""
        return list(self._configs.keys())

