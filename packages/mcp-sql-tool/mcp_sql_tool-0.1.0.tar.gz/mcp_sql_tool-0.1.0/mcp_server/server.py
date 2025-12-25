"""MCP Server 主入口 - 使用 FastMCP"""

import json
from typing import Optional
from fastmcp import FastMCP
from .handlers import ToolHandlers


def create_mcp_server(tool_handlers: ToolHandlers) -> FastMCP:
    """
    创建 MCP Server 实例

    Args:
        tool_handlers: 工具处理器实例

    Returns:
        FastMCP 服务器实例
    """
    mcp = FastMCP("MCP SQL Tool")

    @mcp.tool()
    def execute_sql(
        sql: Optional[str] = None,
        query: Optional[str] = None,
        database: str = "default",
        limit: Optional[int] = None,
        timeout: Optional[int] = None,
        user_id: str = "default",
    ) -> str:
        """
        执行 SQL 查询或根据自然语言生成并执行 SQL 查询

        Args:
            sql: SQL 查询语句（如果提供则直接执行）
            query: 自然语言查询（如果提供则生成 SQL）
            database: 数据库连接名称
            limit: 结果行数限制
            timeout: 查询超时时间（秒）
            user_id: 用户 ID

        Returns:
            JSON 格式的执行结果
        """
        arguments = {
            "sql": sql,
            "query": query,
            "database": database,
            "limit": limit,
            "timeout": timeout,
            "user_id": user_id,
        }
        result = tool_handlers.execute_sql_tool(arguments)
        return json.dumps(result, ensure_ascii=False)

    @mcp.tool()
    def get_schema(
        database: str = "default",
        table: Optional[str] = None,
    ) -> str:
        """
        获取数据库表结构信息

        Args:
            database: 数据库连接名称
            table: 表名（可选，不提供则返回整个数据库的 Schema）

        Returns:
            JSON 格式的 Schema 信息
        """
        arguments = {
            "database": database,
            "table": table,
        }
        result = tool_handlers.get_schema_tool(arguments)
        return json.dumps(result, ensure_ascii=False)

    @mcp.tool()
    def list_tables(database: str = "default") -> str:
        """
        列出数据库中的所有表

        Args:
            database: 数据库连接名称

        Returns:
            JSON 格式的表名列表
        """
        arguments = {"database": database}
        result = tool_handlers.list_tables_tool(arguments)
        return json.dumps(result, ensure_ascii=False)

    @mcp.tool()
    def explain_query(sql: str, database: str = "default") -> str:
        """
        解释 SQL 查询的执行计划

        Args:
            sql: SQL 查询语句
            database: 数据库连接名称

        Returns:
            JSON 格式的查询计划信息
        """
        arguments = {
            "sql": sql,
            "database": database,
        }
        result = tool_handlers.explain_query_tool(arguments)
        return json.dumps(result, ensure_ascii=False)

    return mcp
