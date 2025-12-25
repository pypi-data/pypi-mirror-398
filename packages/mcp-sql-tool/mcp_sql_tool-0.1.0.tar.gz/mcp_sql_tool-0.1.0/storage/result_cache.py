"""查询结果缓存管理"""

import json
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from .db_manager import DBManager


class ResultCache:
    """查询结果缓存管理器"""

    def __init__(self, db_manager: DBManager, default_ttl: int = 300):
        """
        初始化结果缓存管理器

        Args:
            db_manager: 数据库管理器实例
            default_ttl: 默认缓存过期时间（秒）
        """
        self.db = db_manager
        self.default_ttl = default_ttl

    def _hash_sql(self, sql: str) -> str:
        """生成 SQL 的哈希值"""
        return hashlib.md5(sql.encode("utf-8")).hexdigest()

    def get_result(
        self, sql: str, database_name: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        获取缓存的查询结果

        Args:
            sql: SQL 查询语句
            database_name: 数据库名称

        Returns:
            查询结果列表，如果不存在或已过期则返回 None
        """
        sql_hash = self._hash_sql(sql)

        query = """
            SELECT result_json, expires_at 
            FROM result_cache 
            WHERE sql_hash = ? AND database_name = ?
        """
        results = self.db.execute_query(query, (sql_hash, database_name or ""))

        if results:
            expires_at = datetime.fromisoformat(results[0]["expires_at"])
            if expires_at > datetime.now():
                return json.loads(results[0]["result_json"])
            else:
                # 缓存已过期，删除
                self._delete_cache(sql_hash)

        return None

    def set_result(
        self,
        sql: str,
        result: List[Dict[str, Any]],
        database_name: Optional[str] = None,
        ttl: Optional[int] = None,
    ):
        """
        缓存查询结果

        Args:
            sql: SQL 查询语句
            result: 查询结果列表
            database_name: 数据库名称
            ttl: 缓存过期时间（秒），None 使用默认值
        """
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        sql_hash = self._hash_sql(sql)
        result_json = json.dumps(result, ensure_ascii=False, default=str)

        query = """
            INSERT OR REPLACE INTO result_cache 
            (sql_hash, sql_query, result_json, database_name, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """
        self.db.execute_update(
            query, (sql_hash, sql, result_json, database_name or "", expires_at.isoformat())
        )

    def _delete_cache(self, sql_hash: str):
        """删除缓存"""
        self.db.execute_update("DELETE FROM result_cache WHERE sql_hash = ?", (sql_hash,))

    def clear_cache(self, database_name: Optional[str] = None):
        """
        清除缓存

        Args:
            database_name: 数据库名称，None 表示清除所有缓存
        """
        if database_name:
            self.db.execute_update(
                "DELETE FROM result_cache WHERE database_name = ?", (database_name,)
            )
        else:
            self.db.execute_update("DELETE FROM result_cache")

    def cleanup_expired(self) -> int:
        """清理过期的缓存"""
        query = "DELETE FROM result_cache WHERE expires_at < ?"
        return self.db.execute_update(query, (datetime.now().isoformat(),))

