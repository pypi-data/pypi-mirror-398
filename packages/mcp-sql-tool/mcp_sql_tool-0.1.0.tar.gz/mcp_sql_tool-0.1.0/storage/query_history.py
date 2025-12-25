"""查询历史管理"""

from typing import Optional, List, Dict
from datetime import datetime
from .db_manager import DBManager


class QueryHistory:
    """查询历史管理器"""

    def __init__(self, db_manager: DBManager):
        """
        初始化查询历史管理器

        Args:
            db_manager: 数据库管理器实例
        """
        self.db = db_manager

    def add_query(
        self,
        user_query: str,
        generated_sql: Optional[str] = None,
        executed_sql: Optional[str] = None,
        database_name: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        row_count: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> int:
        """
        添加查询历史记录

        Returns:
            插入的记录 ID
        """
        query = """
            INSERT INTO query_history 
            (user_query, generated_sql, executed_sql, database_name, 
             execution_time_ms, row_count, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            user_query,
            generated_sql,
            executed_sql,
            database_name,
            execution_time_ms,
            row_count,
            success,
            error_message,
        )
        self.db.execute_update(query, params)
        # 获取最后插入的 ID
        result = self.db.execute_query("SELECT last_insert_rowid() as id")
        return result[0]["id"] if result else None

    def get_history(
        self,
        limit: int = 100,
        database_name: Optional[str] = None,
        success_only: bool = False,
    ) -> List[Dict]:
        """
        获取查询历史

        Args:
            limit: 返回记录数限制
            database_name: 过滤特定数据库
            success_only: 是否只返回成功的查询

        Returns:
            查询历史记录列表
        """
        query = "SELECT * FROM query_history WHERE 1=1"
        params = []

        if database_name:
            query += " AND database_name = ?"
            params.append(database_name)

        if success_only:
            query += " AND success = 1"

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        return self.db.execute_query(query, tuple(params))

    def get_query_by_id(self, query_id: int) -> Optional[Dict]:
        """根据 ID 获取查询记录"""
        results = self.db.execute_query(
            "SELECT * FROM query_history WHERE id = ?", (query_id,)
        )
        return results[0] if results else None

    def search_history(self, keyword: str, limit: int = 50) -> List[Dict]:
        """搜索查询历史"""
        query = """
            SELECT * FROM query_history 
            WHERE user_query LIKE ? OR generated_sql LIKE ?
            ORDER BY created_at DESC 
            LIMIT ?
        """
        keyword_pattern = f"%{keyword}%"
        return self.db.execute_query(query, (keyword_pattern, keyword_pattern, limit))

    def delete_old_history(self, days: int = 30) -> int:
        """删除指定天数之前的查询历史"""
        query = """
            DELETE FROM query_history 
            WHERE created_at < datetime('now', '-' || ? || ' days')
        """
        return self.db.execute_update(query, (days,))

