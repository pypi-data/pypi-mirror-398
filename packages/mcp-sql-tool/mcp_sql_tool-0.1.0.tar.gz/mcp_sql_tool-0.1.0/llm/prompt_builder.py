"""Prompt 构建器：构建包含 Schema 信息的 SQL 生成 Prompt"""

from typing import Optional, Dict, Any
from .schema_encoder import SchemaEncoder
from database.adapters import TableSchema


class PromptBuilder:
    """Prompt 构建器"""

    def __init__(self, database_type: str = "mysql"):
        """
        初始化 Prompt 构建器

        Args:
            database_type: 数据库类型（mysql, postgresql, sqlite, clickhouse）
        """
        self.database_type = database_type.lower()
        self.schema_encoder = SchemaEncoder()
        self._few_shot_examples = self._get_few_shot_examples()

    def build(
        self,
        user_query: str,
        schemas: Optional[Dict[str, TableSchema]] = None,
        include_examples: bool = True,
    ) -> str:
        """
        构建 Prompt

        Args:
            user_query: 用户自然语言查询
            schemas: 表结构字典
            include_examples: 是否包含 Few-shot 示例

        Returns:
            完整的 Prompt 文本
        """
        parts = []

        # 1. 系统提示
        parts.append(self._build_system_prompt())

        # 2. Schema 信息
        if schemas:
            parts.append(self._build_schema_section(schemas))

        # 3. Few-shot 示例
        if include_examples:
            parts.append(self._build_examples_section())

        # 4. 用户查询
        parts.append(self._build_user_query_section(user_query))

        return "\n\n".join(parts)

    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        db_dialect = {
            "mysql": "MySQL",
            "postgresql": "PostgreSQL",
            "postgres": "PostgreSQL",
            "sqlite": "SQLite",
            "clickhouse": "ClickHouse",
        }.get(self.database_type, "SQL")

        return f"""You are a SQL expert. Generate accurate {db_dialect} SQL queries based on natural language questions.

Rules:
1. Only generate SELECT queries (read-only)
2. Use proper table and column names from the schema
3. Use appropriate JOINs when needed
4. Add WHERE clauses for filtering
5. Use aggregate functions (COUNT, SUM, AVG, etc.) when appropriate
6. Return only the SQL query, no explanations
7. Do not include any markdown formatting or code blocks"""

    def _build_schema_section(self, schemas: Dict[str, TableSchema]) -> str:
        """构建 Schema 部分"""
        schema_text = self.schema_encoder.encode_database(schemas)
        return f"Database Schema:\n{schema_text}"

    def _build_examples_section(self) -> str:
        """构建 Few-shot 示例部分"""
        examples = self._few_shot_examples.get(self.database_type, self._few_shot_examples["mysql"])
        return f"Examples:\n{examples}"

    def _build_user_query_section(self, user_query: str) -> str:
        """构建用户查询部分"""
        return f"Question: {user_query}\n\nSQL Query:"

    def _get_few_shot_examples(self) -> Dict[str, str]:
        """获取 Few-shot 示例"""
        return {
            "mysql": """Example 1:
Question: How many users are there?
SQL Query: SELECT COUNT(*) as user_count FROM users;

Example 2:
Question: Show me all orders from the last 7 days
SQL Query: SELECT * FROM orders WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY);

Example 3:
Question: What is the total revenue by product category?
SQL Query: SELECT category, SUM(price) as total_revenue FROM products GROUP BY category;""",
            "postgresql": """Example 1:
Question: How many users are there?
SQL Query: SELECT COUNT(*) as user_count FROM users;

Example 2:
Question: Show me all orders from the last 7 days
SQL Query: SELECT * FROM orders WHERE created_at >= NOW() - INTERVAL '7 days';

Example 3:
Question: What is the total revenue by product category?
SQL Query: SELECT category, SUM(price) as total_revenue FROM products GROUP BY category;""",
            "sqlite": """Example 1:
Question: How many users are there?
SQL Query: SELECT COUNT(*) as user_count FROM users;

Example 2:
Question: Show me all orders from the last 7 days
SQL Query: SELECT * FROM orders WHERE created_at >= datetime('now', '-7 days');

Example 3:
Question: What is the total revenue by product category?
SQL Query: SELECT category, SUM(price) as total_revenue FROM products GROUP BY category;""",
            "clickhouse": """Example 1:
Question: How many users are there?
SQL Query: SELECT COUNT(*) as user_count FROM users;

Example 2:
Question: Show me all orders from the last 7 days
SQL Query: SELECT * FROM orders WHERE created_at >= now() - INTERVAL 7 DAY;

Example 3:
Question: What is the total revenue by product category?
SQL Query: SELECT category, SUM(price) as total_revenue FROM products GROUP BY category;""",
        }

    def set_custom_examples(self, examples: str):
        """设置自定义示例"""
        self._few_shot_examples[self.database_type] = examples

