"""SQL 验证器：防止 SQL 注入和危险操作"""

import re
from typing import List, Tuple, Optional
from enum import Enum


class ValidationResult:
    """验证结果"""

    def __init__(self, valid: bool, error: Optional[str] = None):
        self.valid = valid
        self.error = error

    def __bool__(self):
        return self.valid


class SQLValidator:
    """SQL 验证器"""

    def __init__(
        self,
        read_only: bool = True,
        allowed_operations: Optional[List[str]] = None,
        blocked_keywords: Optional[List[str]] = None,
    ):
        """
        初始化 SQL 验证器

        Args:
            read_only: 是否只读模式（默认只允许 SELECT）
            allowed_operations: 允许的 SQL 操作列表（如 ['SELECT']）
            blocked_keywords: 被阻止的关键字列表
        """
        self.read_only = read_only
        self.allowed_operations = allowed_operations or (["SELECT"] if read_only else [])
        self.blocked_keywords = blocked_keywords or [
            "DROP",
            "TRUNCATE",
            "DELETE",
            "UPDATE",
            "INSERT",
            "ALTER",
            "CREATE",
            "GRANT",
            "REVOKE",
            "EXEC",
            "EXECUTE",
            "CALL",
        ]

        # SQL 注入检测模式
        self.injection_patterns = [
            r"(--|#)",  # SQL 注释
            r"(;|\|)",  # 命令分隔符
            r"(UNION\s+SELECT)",  # UNION 注入
            r"(OR\s+1\s*=\s*1)",  # 永真条件
            r"(/\*|\*/)",  # 多行注释
            r"(xp_|sp_)",  # 存储过程
            r"(LOAD_FILE|INTO\s+OUTFILE)",  # 文件操作
        ]

    def validate(self, sql: str) -> ValidationResult:
        """
        验证 SQL 语句

        Args:
            sql: SQL 语句

        Returns:
            验证结果
        """
        sql_upper = sql.upper().strip()

        # 1. 检查是否为空
        if not sql or not sql.strip():
            return ValidationResult(False, "SQL statement is empty")

        # 2. 检查操作类型
        operation_result = self._validate_operation(sql_upper)
        if not operation_result:
            return operation_result

        # 3. 检查危险关键字
        keyword_result = self._validate_keywords(sql_upper)
        if not keyword_result:
            return keyword_result

        # 4. 检查 SQL 注入
        injection_result = self._validate_injection(sql)
        if not injection_result:
            return injection_result

        # 5. 检查语法（基础检查）
        syntax_result = self._validate_syntax(sql_upper)
        if not syntax_result:
            return syntax_result

        return ValidationResult(True)

    def _validate_operation(self, sql_upper: str) -> ValidationResult:
        """验证操作类型"""
        # 提取第一个关键字（通常是操作类型）
        first_word = sql_upper.split()[0] if sql_upper.split() else ""

        if not self.allowed_operations:
            return ValidationResult(True)

        # 检查是否以允许的操作开头
        for op in self.allowed_operations:
            if sql_upper.startswith(op):
                return ValidationResult(True)

        return ValidationResult(
            False,
            f"Operation not allowed. Allowed operations: {', '.join(self.allowed_operations)}",
        )

    def _validate_keywords(self, sql_upper: str) -> ValidationResult:
        """验证危险关键字"""
        for keyword in self.blocked_keywords:
            # 使用单词边界匹配，避免误判
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, sql_upper, re.IGNORECASE):
                return ValidationResult(
                    False, f"Dangerous keyword detected: {keyword}"
                )

        return ValidationResult(True)

    def _validate_injection(self, sql: str) -> ValidationResult:
        """检测 SQL 注入"""
        for pattern in self.injection_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                return ValidationResult(
                    False, f"Potential SQL injection detected: {pattern}"
                )

        return ValidationResult(True)

    def _validate_syntax(self, sql_upper: str) -> ValidationResult:
        """基础语法验证"""
        # 检查括号匹配
        open_parens = sql_upper.count("(")
        close_parens = sql_upper.count(")")
        if open_parens != close_parens:
            return ValidationResult(False, "Unmatched parentheses")

        # 检查引号匹配（简单检查）
        single_quotes = sql.count("'")
        double_quotes = sql.count('"')
        if single_quotes % 2 != 0:
            return ValidationResult(False, "Unmatched single quotes")
        if double_quotes % 2 != 0:
            return ValidationResult(False, "Unmatched double quotes")

        return ValidationResult(True)

    def sanitize(self, sql: str) -> str:
        """
        清理 SQL 语句（移除注释等）

        Args:
            sql: 原始 SQL 语句

        Returns:
            清理后的 SQL 语句
        """
        # 移除单行注释
        sql = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
        sql = re.sub(r"#.*$", "", sql, flags=re.MULTILINE)

        # 移除多行注释
        sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)

        # 移除多余空白
        sql = " ".join(sql.split())

        return sql.strip()

