"""权限管理器"""

from typing import Dict, List, Optional, Set
from enum import Enum


class Permission(Enum):
    """权限类型"""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class PermissionManager:
    """权限管理器"""

    def __init__(self, default_permission: Permission = Permission.READ):
        """
        初始化权限管理器

        Args:
            default_permission: 默认权限
        """
        self.default_permission = default_permission
        self._user_permissions: Dict[str, Set[Permission]] = {}
        self._table_permissions: Dict[str, Dict[str, Set[Permission]]] = {}
        self._database_permissions: Dict[str, Dict[str, Set[Permission]]] = {}

    def set_user_permission(self, user_id: str, permissions: List[Permission]):
        """
        设置用户权限

        Args:
            user_id: 用户 ID
            permissions: 权限列表
        """
        self._user_permissions[user_id] = set(permissions)

    def set_table_permission(
        self,
        database_name: str,
        table_name: str,
        user_id: str,
        permissions: List[Permission],
    ):
        """
        设置表级权限

        Args:
            database_name: 数据库名称
            table_name: 表名
            user_id: 用户 ID
            permissions: 权限列表
        """
        if database_name not in self._table_permissions:
            self._table_permissions[database_name] = {}

        key = f"{user_id}:{table_name}"
        self._table_permissions[database_name][key] = set(permissions)

    def set_database_permission(
        self, database_name: str, user_id: str, permissions: List[Permission]
    ):
        """
        设置数据库级权限

        Args:
            database_name: 数据库名称
            user_id: 用户 ID
            permissions: 权限列表
        """
        if database_name not in self._database_permissions:
            self._database_permissions[database_name] = {}

        self._database_permissions[database_name][user_id] = set(permissions)

    def check_permission(
        self,
        user_id: str,
        database_name: str,
        table_name: Optional[str] = None,
        required_permission: Permission = Permission.READ,
    ) -> bool:
        """
        检查权限

        Args:
            user_id: 用户 ID
            database_name: 数据库名称
            table_name: 表名（可选）
            required_permission: 需要的权限

        Returns:
            是否有权限
        """
        # 检查表级权限
        if table_name:
            if database_name in self._table_permissions:
                key = f"{user_id}:{table_name}"
                if key in self._table_permissions[database_name]:
                    permissions = self._table_permissions[database_name][key]
                    if self._has_permission(permissions, required_permission):
                        return True

        # 检查数据库级权限
        if database_name in self._database_permissions:
            if user_id in self._database_permissions[database_name]:
                permissions = self._database_permissions[database_name][user_id]
                if self._has_permission(permissions, required_permission):
                    return True

        # 检查用户级权限
        if user_id in self._user_permissions:
            permissions = self._user_permissions[user_id]
            if self._has_permission(permissions, required_permission):
                return True

        # 使用默认权限
        return self._has_permission({self.default_permission}, required_permission)

    def _has_permission(self, user_permissions: Set[Permission], required: Permission) -> bool:
        """检查权限是否满足要求"""
        if Permission.ADMIN in user_permissions:
            return True

        if required == Permission.READ:
            return Permission.READ in user_permissions or Permission.WRITE in user_permissions

        if required == Permission.WRITE:
            return Permission.WRITE in user_permissions

        return False

    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """获取用户权限"""
        return self._user_permissions.get(user_id, {self.default_permission})

