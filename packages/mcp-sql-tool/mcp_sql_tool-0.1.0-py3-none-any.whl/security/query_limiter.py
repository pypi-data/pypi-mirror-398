"""查询限制器：控制查询超时、行数、频率等"""

import time
from typing import Dict, Optional
from collections import defaultdict
from threading import Lock


class QueryLimiter:
    """查询限制器"""

    def __init__(
        self,
        max_timeout: int = 30,
        max_result_rows: int = 10000,
        max_queries_per_minute: int = 60,
        max_queries_per_hour: int = 1000,
    ):
        """
        初始化查询限制器

        Args:
            max_timeout: 最大查询超时时间（秒）
            max_result_rows: 最大结果行数
            max_queries_per_minute: 每分钟最大查询数
            max_queries_per_hour: 每小时最大查询数
        """
        self.max_timeout = max_timeout
        self.max_result_rows = max_result_rows
        self.max_queries_per_minute = max_queries_per_minute
        self.max_queries_per_hour = max_queries_per_hour

        # 查询频率跟踪
        self._query_times: Dict[str, list] = defaultdict(list)
        self._lock = Lock()

    def check_timeout(self, timeout: Optional[int] = None) -> tuple:
        """
        检查超时设置是否合法

        Args:
            timeout: 请求的超时时间（秒）

        Returns:
            (是否合法, 错误信息)
        """
        if timeout is None:
            return True, None

        if timeout > self.max_timeout:
            return False, f"Timeout {timeout}s exceeds maximum {self.max_timeout}s"

        return True, None

    def check_result_rows(self, row_count: int) -> tuple:
        """
        检查结果行数是否超过限制

        Args:
            row_count: 结果行数

        Returns:
            (是否合法, 错误信息)
        """
        if row_count > self.max_result_rows:
            return (
                False,
                f"Result row count {row_count} exceeds maximum {self.max_result_rows}",
            )

        return True, None

    def check_query_rate(self, user_id: str = "default") -> tuple:
        """
        检查查询频率

        Args:
            user_id: 用户 ID

        Returns:
            (是否合法, 错误信息)
        """
        with self._lock:
            now = time.time()
            user_queries = self._query_times[user_id]

            # 清理过期记录（1小时前）
            user_queries[:] = [t for t in user_queries if now - t < 3600]

            # 检查每小时限制
            hour_queries = [t for t in user_queries if now - t < 3600]
            if len(hour_queries) >= self.max_queries_per_hour:
                return (
                    False,
                    f"Query rate limit exceeded: {len(hour_queries)} queries in the last hour",
                )

            # 检查每分钟限制
            minute_queries = [t for t in user_queries if now - t < 60]
            if len(minute_queries) >= self.max_queries_per_minute:
                return (
                    False,
                    f"Query rate limit exceeded: {len(minute_queries)} queries in the last minute",
                )

            # 记录本次查询
            user_queries.append(now)

        return True, None

    def reset_rate_limit(self, user_id: Optional[str] = None):
        """
        重置频率限制

        Args:
            user_id: 用户 ID，None 表示重置所有用户
        """
        with self._lock:
            if user_id:
                self._query_times.pop(user_id, None)
            else:
                self._query_times.clear()

