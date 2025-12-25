"""配置加载器"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径（可选）
        """
        self.config_path = config_path or "config/config.yaml"
        self.config: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        """
        加载配置文件

        Returns:
            配置字典
        """
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}

        # 从环境变量覆盖配置
        self._load_from_env()

        return self.config

    def _load_from_env(self):
        """从环境变量加载配置"""
        # LLM 配置
        if "LLM_API_KEY" in os.environ:
            if "llm" not in self.config:
                self.config["llm"] = {}
            self.config["llm"]["api_key"] = os.environ["LLM_API_KEY"]

        if "LLM_PROVIDER" in os.environ:
            if "llm" not in self.config:
                self.config["llm"] = {}
            self.config["llm"]["provider"] = os.environ["LLM_PROVIDER"]

        if "LLM_MODEL" in os.environ:
            if "llm" not in self.config:
                self.config["llm"] = {}
            self.config["llm"]["model"] = os.environ["LLM_MODEL"]

        # 数据库配置
        if "DB_HOST" in os.environ:
            if "databases" not in self.config:
                self.config["databases"] = [{}]
            if not self.config["databases"]:
                self.config["databases"] = [{}]
            self.config["databases"][0]["host"] = os.environ["DB_HOST"]

        if "DB_USER" in os.environ:
            if "databases" not in self.config:
                self.config["databases"] = [{}]
            if not self.config["databases"]:
                self.config["databases"] = [{}]
            self.config["databases"][0]["user"] = os.environ["DB_USER"]

        if "DB_PASSWORD" in os.environ:
            if "databases" not in self.config:
                self.config["databases"] = [{}]
            if not self.config["databases"]:
                self.config["databases"] = [{}]
            self.config["databases"][0]["password"] = os.environ["DB_PASSWORD"]

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的嵌套键）

        Args:
            key: 配置键（如 'llm.provider'）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_llm_config(self) -> Dict[str, Any]:
        """获取 LLM 配置"""
        return self.config.get("llm", {})

    def get_database_configs(self) -> list:
        """获取数据库配置列表"""
        return self.config.get("databases", [])

    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return self.config.get("security", {})

    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存配置"""
        return self.config.get("cache", {})

