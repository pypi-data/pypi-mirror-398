"""Schema 缓存管理"""

import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from .db_manager import DBManager


class SchemaCache:
    """Schema 缓存管理器"""

    def __init__(self, db_manager: DBManager, default_ttl: int = 3600):
        """
        初始化 Schema 缓存管理器

        Args:
            db_manager: 数据库管理器实例
            default_ttl: 默认缓存过期时间（秒）
        """
        self.db = db_manager
        self.default_ttl = default_ttl
        self._memory_cache: Dict[str, Dict] = {}

    def get_schema(
        self, database_name: str, table_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取缓存的 Schema 信息

        Args:
            database_name: 数据库名称
            table_name: 表名（None 表示获取整个数据库的 Schema）

        Returns:
            Schema 信息字典，如果不存在或已过期则返回 None
        """
        cache_key = f"{database_name}:{table_name or 'all'}"

        # 先检查内存缓存
        if cache_key in self._memory_cache:
            cached = self._memory_cache[cache_key]
            if cached["expires_at"] > datetime.now():
                return cached["schema"]

        # 检查数据库缓存
        if table_name:
            query = """
                SELECT schema_json, expires_at 
                FROM schema_cache 
                WHERE database_name = ? AND table_name = ?
            """
            params = (database_name, table_name)
        else:
            query = """
                SELECT schema_json, expires_at 
                FROM schema_cache 
                WHERE database_name = ? AND table_name IS NULL
            """
            params = (database_name,)

        results = self.db.execute_query(query, params)
        if results:
            expires_at = datetime.fromisoformat(results[0]["expires_at"])
            if expires_at > datetime.now():
                schema = json.loads(results[0]["schema_json"])
                # 更新内存缓存
                self._memory_cache[cache_key] = {
                    "schema": schema,
                    "expires_at": expires_at,
                }
                return schema
            else:
                # 缓存已过期，删除
                self._delete_cache(database_name, table_name)

        return None

    def set_schema(
        self,
        database_name: str,
        schema: Dict[str, Any],
        table_name: Optional[str] = None,
        ttl: Optional[int] = None,
    ):
        """
        缓存 Schema 信息

        Args:
            database_name: 数据库名称
            schema: Schema 信息字典
            table_name: 表名（None 表示整个数据库的 Schema）
            ttl: 缓存过期时间（秒），None 使用默认值
        """
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        schema_json = json.dumps(schema, ensure_ascii=False)

        cache_key = f"{database_name}:{table_name or 'all'}"

        # 更新内存缓存
        self._memory_cache[cache_key] = {
            "schema": schema,
            "expires_at": expires_at,
        }

        # 更新数据库缓存
        query = """
            INSERT OR REPLACE INTO schema_cache 
            (database_name, table_name, schema_json, expires_at)
            VALUES (?, ?, ?, ?)
        """
        self.db.execute_update(
            query, (database_name, table_name, schema_json, expires_at.isoformat())
        )

    def _delete_cache(self, database_name: str, table_name: Optional[str] = None):
        """删除缓存"""
        cache_key = f"{database_name}:{table_name or 'all'}"
        self._memory_cache.pop(cache_key, None)

        if table_name:
            query = "DELETE FROM schema_cache WHERE database_name = ? AND table_name = ?"
            params = (database_name, table_name)
        else:
            query = "DELETE FROM schema_cache WHERE database_name = ? AND table_name IS NULL"
            params = (database_name,)

        self.db.execute_update(query, params)

    def clear_cache(self, database_name: Optional[str] = None):
        """
        清除缓存

        Args:
            database_name: 数据库名称，None 表示清除所有缓存
        """
        if database_name:
            # 清除特定数据库的缓存
            keys_to_delete = [
                key for key in self._memory_cache.keys() if key.startswith(f"{database_name}:")
            ]
            for key in keys_to_delete:
                del self._memory_cache[key]

            self.db.execute_update(
                "DELETE FROM schema_cache WHERE database_name = ?", (database_name,)
            )
        else:
            # 清除所有缓存
            self._memory_cache.clear()
            self.db.execute_update("DELETE FROM schema_cache")

    def refresh_cache(self, database_name: str, table_name: Optional[str] = None):
        """刷新缓存（标记为过期）"""
        self._delete_cache(database_name, table_name)

