"""审计日志记录器"""

from typing import Optional, Dict, Any
from datetime import datetime
from storage import DBManager


class AuditLogger:
    """审计日志记录器"""

    def __init__(self, db_manager: DBManager):
        """
        初始化审计日志记录器

        Args:
            db_manager: 数据库管理器实例
        """
        self.db = db_manager

    def log_operation(
        self,
        operation_type: str,
        sql_query: Optional[str] = None,
        database_name: Optional[str] = None,
        user_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
    ):
        """
        记录操作日志

        Args:
            operation_type: 操作类型（如 'QUERY', 'SCHEMA_GET', 'TABLE_LIST'）
            sql_query: SQL 查询语句
            database_name: 数据库名称
            user_id: 用户 ID
            success: 是否成功
            error_message: 错误信息
            execution_time_ms: 执行时间（毫秒）
        """
        query = """
            INSERT INTO audit_log 
            (operation_type, sql_query, database_name, user_id, 
             success, error_message, execution_time_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            operation_type,
            sql_query,
            database_name,
            user_id,
            success,
            error_message,
            execution_time_ms,
        )
        self.db.execute_update(query, params)

    def get_audit_logs(
        self,
        limit: int = 100,
        operation_type: Optional[str] = None,
        database_name: Optional[str] = None,
        user_id: Optional[str] = None,
        success_only: bool = False,
    ) -> list:
        """
        获取审计日志

        Args:
            limit: 返回记录数限制
            operation_type: 过滤特定操作类型
            database_name: 过滤特定数据库
            user_id: 过滤特定用户
            success_only: 是否只返回成功的操作

        Returns:
            审计日志记录列表
        """
        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []

        if operation_type:
            query += " AND operation_type = ?"
            params.append(operation_type)

        if database_name:
            query += " AND database_name = ?"
            params.append(database_name)

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if success_only:
            query += " AND success = 1"

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        return self.db.execute_query(query, tuple(params))

    def delete_old_logs(self, days: int = 90) -> int:
        """删除指定天数之前的审计日志"""
        query = """
            DELETE FROM audit_log 
            WHERE created_at < datetime('now', '-' || ? || ' days')
        """
        return self.db.execute_update(query, (days,))

