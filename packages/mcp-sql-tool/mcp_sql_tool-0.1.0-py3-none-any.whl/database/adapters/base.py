"""数据库适配器基类"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class QueryResult:
    """查询结果数据类"""

    rows: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time_ms: int


@dataclass
class TableSchema:
    """表结构数据类"""

    name: str
    columns: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]]
    foreign_keys: List[Dict[str, Any]]
    comment: Optional[str] = None


class DatabaseAdapter(ABC):
    """数据库适配器基类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化适配器

        Args:
            config: 数据库配置字典
        """
        self.config = config
        self.connection = None

    @abstractmethod
    def connect(self) -> Any:
        """建立数据库连接"""
        pass

    @abstractmethod
    def disconnect(self):
        """关闭数据库连接"""
        pass

    @abstractmethod
    def execute_query(self, sql: str, limit: Optional[int] = None) -> QueryResult:
        """
        执行查询

        Args:
            sql: SQL 查询语句
            limit: 结果行数限制

        Returns:
            查询结果
        """
        pass

    @abstractmethod
    def get_schema(self, table_name: str) -> TableSchema:
        """
        获取表结构

        Args:
            table_name: 表名

        Returns:
            表结构信息
        """
        pass

    @abstractmethod
    def list_tables(self) -> List[str]:
        """
        列出所有表名

        Returns:
            表名列表
        """
        pass

    @abstractmethod
    def explain_query(self, sql: str) -> Dict[str, Any]:
        """
        解释查询计划

        Args:
            sql: SQL 查询语句

        Returns:
            查询计划信息
        """
        pass

    def test_connection(self) -> bool:
        """
        测试数据库连接

        Returns:
            连接是否成功
        """
        try:
            self.connect()
            self.disconnect()
            return True
        except Exception:
            return False

