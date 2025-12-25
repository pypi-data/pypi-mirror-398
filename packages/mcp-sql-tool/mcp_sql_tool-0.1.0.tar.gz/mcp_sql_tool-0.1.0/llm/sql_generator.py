"""SQL 生成器：核心 SQL 生成逻辑"""

import re
from typing import Optional, Dict, Any
from .llm_client import LLMClient, create_llm_client
from .prompt_builder import PromptBuilder
from .schema_encoder import SchemaEncoder
from database.schema_loader import SchemaLoader
from security.sql_validator import SQLValidator


class SQLGenerator:
    """SQL 生成器"""

    def __init__(
        self,
        llm_client: LLMClient,
        schema_loader: SchemaLoader,
        sql_validator: Optional[SQLValidator] = None,
        database_type: str = "mysql",
    ):
        """
        初始化 SQL 生成器

        Args:
            llm_client: LLM 客户端实例
            schema_loader: Schema 加载器实例
            sql_validator: SQL 验证器实例（可选）
            database_type: 数据库类型
        """
        self.llm_client = llm_client
        self.schema_loader = schema_loader
        self.sql_validator = sql_validator or SQLValidator()
        self.prompt_builder = PromptBuilder(database_type=database_type)
        self.schema_encoder = SchemaEncoder()

    def generate(
        self,
        user_query: str,
        database_name: str,
        table_names: Optional[list] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        生成 SQL 查询

        Args:
            user_query: 用户自然语言查询
            database_name: 数据库连接名称
            table_names: 相关表名列表（None 表示自动推断或使用所有表）
            max_retries: 最大重试次数

        Returns:
            包含生成的 SQL 和元数据的字典
        """
        # 1. 获取 Schema 信息
        if table_names:
            schemas = {}
            for table_name in table_names:
                try:
                    schema = self.schema_loader.get_table_schema(database_name, table_name)
                    schemas[table_name] = schema
                except Exception as e:
                    # 如果表不存在，继续处理其他表
                    continue
        else:
            # 获取整个数据库的 Schema
            schemas = self.schema_loader.get_database_schema(database_name)

        # 2. 构建 Prompt
        prompt = self.prompt_builder.build(user_query, schemas=schemas)

        # 3. 调用 LLM 生成 SQL
        sql = None
        error = None

        for attempt in range(max_retries):
            try:
                response = self.llm_client.generate(prompt)
                sql = self._extract_sql(response)

                if not sql:
                    error = "Failed to extract SQL from LLM response"
                    continue

                # 4. 验证 SQL
                validation_result = self.sql_validator.validate(sql)
                if not validation_result:
                    error = validation_result.error
                    # 如果验证失败，尝试重新生成
                    if attempt < max_retries - 1:
                        # 在 Prompt 中添加错误信息，让 LLM 修正
                        prompt += f"\n\nPrevious attempt failed: {error}. Please generate a corrected SQL query."
                        continue
                    else:
                        return {
                            "sql": sql,
                            "success": False,
                            "error": error,
                            "validated": False,
                        }

                # 验证通过
                return {
                    "sql": sql,
                    "success": True,
                    "error": None,
                    "validated": True,
                }

            except Exception as e:
                error = str(e)
                if attempt < max_retries - 1:
                    continue
                else:
                    return {
                        "sql": None,
                        "success": False,
                        "error": error,
                        "validated": False,
                    }

        return {
            "sql": sql,
            "success": False,
            "error": error or "Failed to generate SQL after multiple attempts",
            "validated": False,
        }

    def _extract_sql(self, response: str) -> Optional[str]:
        """
        从 LLM 响应中提取 SQL 语句

        Args:
            response: LLM 响应文本

        Returns:
            提取的 SQL 语句
        """
        # 移除 markdown 代码块
        response = re.sub(r"```sql\s*", "", response, flags=re.IGNORECASE)
        response = re.sub(r"```\s*", "", response)

        # 查找 SELECT 语句
        match = re.search(r"(SELECT\s+.*?)(?:;|$)", response, re.IGNORECASE | re.DOTALL)
        if match:
            sql = match.group(1).strip()
            # 移除末尾的分号（如果有）
            sql = sql.rstrip(";")
            return sql

        # 如果没有找到，尝试提取整个响应（如果看起来像 SQL）
        response = response.strip()
        if response.upper().startswith("SELECT"):
            return response.rstrip(";")

        return None

    def generate_with_context(
        self,
        user_query: str,
        database_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        使用上下文信息生成 SQL（支持多轮对话）

        Args:
            user_query: 用户查询
            database_name: 数据库连接名称
            context: 上下文信息（包含之前的查询、错误等）

        Returns:
            生成结果
        """
        # 如果有上下文，可以优化 Prompt
        if context and context.get("previous_error"):
            # 在查询中添加错误信息，帮助 LLM 修正
            user_query = f"{user_query}\n\nNote: Previous query failed with error: {context['previous_error']}"

        return self.generate(user_query, database_name)

