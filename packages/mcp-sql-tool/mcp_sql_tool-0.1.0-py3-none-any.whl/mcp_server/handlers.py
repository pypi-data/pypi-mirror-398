"""MCP 工具处理器"""

from typing import Dict, Any, Optional, List
from llm import SQLGenerator
from database import Executor, SchemaLoader
from security import SQLValidator, QueryLimiter, AuditLogger
from storage import QueryHistory, ResultCache


class ToolHandlers:
    """MCP 工具处理器"""

    def __init__(
        self,
        sql_generator: SQLGenerator,
        executor: Executor,
        schema_loader: SchemaLoader,
        sql_validator: SQLValidator,
        query_limiter: QueryLimiter,
        audit_logger: AuditLogger,
        query_history: QueryHistory,
        result_cache: Optional[ResultCache] = None,
    ):
        """
        初始化工具处理器

        Args:
            sql_generator: SQL 生成器
            executor: SQL 执行器
            schema_loader: Schema 加载器
            sql_validator: SQL 验证器
            query_limiter: 查询限制器
            audit_logger: 审计日志记录器
            query_history: 查询历史管理器
            result_cache: 结果缓存管理器（可选）
        """
        self.sql_generator = sql_generator
        self.executor = executor
        self.schema_loader = schema_loader
        self.sql_validator = sql_validator
        self.query_limiter = query_limiter
        self.audit_logger = audit_logger
        self.query_history = query_history
        self.result_cache = result_cache

    def execute_sql_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 SQL 查询工具

        Args:
            arguments: 工具参数
                - sql: SQL 查询语句（可选，如果提供则直接执行）
                - query: 自然语言查询（可选，如果提供则生成 SQL）
                - database: 数据库连接名称
                - limit: 结果行数限制
                - timeout: 查询超时时间（秒）

        Returns:
            执行结果
        """
        database_name = arguments.get("database", "default")
        sql = arguments.get("sql")
        user_query = arguments.get("query")
        limit = arguments.get("limit")
        timeout = arguments.get("timeout")

        user_id = arguments.get("user_id", "default")

        try:
            # 检查查询频率限制
            rate_ok, rate_error = self.query_limiter.check_query_rate(user_id)
            if not rate_ok:
                self.audit_logger.log_operation(
                    "QUERY",
                    database_name=database_name,
                    user_id=user_id,
                    success=False,
                    error_message=rate_error,
                )
                return {"success": False, "error": rate_error}

            # 检查超时设置
            timeout_ok, timeout_error = self.query_limiter.check_timeout(timeout)
            if not timeout_ok:
                return {"success": False, "error": timeout_error}

            # 如果没有提供 SQL，从自然语言生成
            if not sql and user_query:
                generation_result = self.sql_generator.generate(
                    user_query, database_name
                )
                if not generation_result["success"]:
                    self.audit_logger.log_operation(
                        "QUERY",
                        sql_query=user_query,
                        database_name=database_name,
                        user_id=user_id,
                        success=False,
                        error_message=generation_result.get("error"),
                    )
                    return {
                        "success": False,
                        "error": f"SQL generation failed: {generation_result.get('error')}",
                    }
                sql = generation_result["sql"]
                generated_sql = sql
            else:
                generated_sql = None

            if not sql:
                return {"success": False, "error": "No SQL query provided"}

            # 验证 SQL
            validation_result = self.sql_validator.validate(sql)
            if not validation_result:
                self.audit_logger.log_operation(
                    "QUERY",
                    sql_query=sql,
                    database_name=database_name,
                    user_id=user_id,
                    success=False,
                    error_message=validation_result.error,
                )
                return {"success": False, "error": f"SQL validation failed: {validation_result.error}"}

            # 检查结果缓存
            if self.result_cache:
                cached_result = self.result_cache.get_result(sql, database_name)
                if cached_result is not None:
                    self.audit_logger.log_operation(
                        "QUERY",
                        sql_query=sql,
                        database_name=database_name,
                        user_id=user_id,
                        success=True,
                        execution_time_ms=0,
                    )
                    return {
                        "success": True,
                        "rows": cached_result,
                        "cached": True,
                    }

            # 执行查询
            try:
                result = self.executor.execute(
                    database_name, sql, limit=limit, timeout=timeout
                )

                # 检查结果行数限制
                rows_ok, rows_error = self.query_limiter.check_result_rows(result.row_count)
                if not rows_ok:
                    self.audit_logger.log_operation(
                        "QUERY",
                        sql_query=sql,
                        database_name=database_name,
                        user_id=user_id,
                        success=False,
                        error_message=rows_error,
                    )
                    return {"success": False, "error": rows_error}

                # 记录查询历史
                self.query_history.add_query(
                    user_query=user_query or sql,
                    generated_sql=generated_sql,
                    executed_sql=sql,
                    database_name=database_name,
                    execution_time_ms=result.execution_time_ms,
                    row_count=result.row_count,
                    success=True,
                )

                # 缓存结果
                if self.result_cache:
                    self.result_cache.set_result(sql, result.rows, database_name)

                # 记录审计日志
                self.audit_logger.log_operation(
                    "QUERY",
                    sql_query=sql,
                    database_name=database_name,
                    user_id=user_id,
                    success=True,
                    execution_time_ms=result.execution_time_ms,
                )

                return {
                    "success": True,
                    "rows": result.rows,
                    "columns": result.columns,
                    "row_count": result.row_count,
                    "execution_time_ms": result.execution_time_ms,
                }

            except Exception as e:
                error_msg = str(e)
                self.query_history.add_query(
                    user_query=user_query or sql,
                    generated_sql=generated_sql,
                    executed_sql=sql,
                    database_name=database_name,
                    success=False,
                    error_message=error_msg,
                )
                self.audit_logger.log_operation(
                    "QUERY",
                    sql_query=sql,
                    database_name=database_name,
                    user_id=user_id,
                    success=False,
                    error_message=error_msg,
                )
                return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = str(e)
            self.audit_logger.log_operation(
                "QUERY",
                database_name=database_name,
                user_id=user_id,
                success=False,
                error_message=error_msg,
            )
            return {"success": False, "error": error_msg}

    def get_schema_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取数据库 Schema 工具

        Args:
            arguments: 工具参数
                - database: 数据库连接名称
                - table: 表名（可选，不提供则返回整个数据库的 Schema）

        Returns:
            Schema 信息
        """
        database_name = arguments.get("database", "default")
        table_name = arguments.get("table")

        try:
            if table_name:
                schema = self.schema_loader.get_table_schema(database_name, table_name)
                return {
                    "success": True,
                    "database": database_name,
                    "table": table_name,
                    "schema": {
                        "name": schema.name,
                        "columns": schema.columns,
                        "indexes": schema.indexes,
                        "foreign_keys": schema.foreign_keys,
                        "comment": schema.comment,
                    },
                }
            else:
                schemas = self.schema_loader.get_database_schema(database_name)
                return {
                    "success": True,
                    "database": database_name,
                    "tables": list(schemas.keys()),
                    "schemas": {
                        name: {
                            "name": schema.name,
                            "columns": schema.columns,
                            "indexes": schema.indexes,
                            "foreign_keys": schema.foreign_keys,
                            "comment": schema.comment,
                        }
                        for name, schema in schemas.items()
                    },
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_tables_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        列出数据库表工具

        Args:
            arguments: 工具参数
                - database: 数据库连接名称

        Returns:
            表名列表
        """
        database_name = arguments.get("database", "default")

        try:
            tables = self.schema_loader.list_tables(database_name)
            return {
                "success": True,
                "database": database_name,
                "tables": tables,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def explain_query_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        解释查询计划工具

        Args:
            arguments: 工具参数
                - sql: SQL 查询语句
                - database: 数据库连接名称

        Returns:
            查询计划信息
        """
        database_name = arguments.get("database", "default")
        sql = arguments.get("sql")

        if not sql:
            return {"success": False, "error": "SQL query is required"}

        try:
            plan = self.executor.explain(database_name, sql)
            return {
                "success": True,
                "database": database_name,
                "sql": sql,
                "plan": plan,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

