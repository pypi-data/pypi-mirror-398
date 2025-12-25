"""结果格式化器"""

import json
import csv
from io import StringIO
from typing import List, Dict, Any


class ResultFormatter:
    """结果格式化器"""

    @staticmethod
    def to_json(rows: List[Dict[str, Any]], indent: int = 2) -> str:
        """
        格式化为 JSON

        Args:
            rows: 结果行列表
            indent: JSON 缩进

        Returns:
            JSON 字符串
        """
        return json.dumps(rows, ensure_ascii=False, indent=indent, default=str)

    @staticmethod
    def to_csv(rows: List[Dict[str, Any]], delimiter: str = ",") -> str:
        """
        格式化为 CSV

        Args:
            rows: 结果行列表
            delimiter: 分隔符

        Returns:
            CSV 字符串
        """
        if not rows:
            return ""

        output = StringIO()
        fieldnames = rows[0].keys()
        writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()

    @staticmethod
    def to_table(rows: List[Dict[str, Any]], max_width: int = 80) -> str:
        """
        格式化为表格

        Args:
            rows: 结果行列表
            max_width: 最大列宽

        Returns:
            表格字符串
        """
        if not rows:
            return "No results"

        # 获取所有列名
        columns = list(rows[0].keys())

        # 计算每列的最大宽度
        col_widths = {}
        for col in columns:
            col_widths[col] = max(
                len(str(col)),
                max((len(str(row.get(col, ""))) for row in rows), default=0),
                max_width,
            )

        # 构建表格
        lines = []

        # 表头
        header = " | ".join(str(col).ljust(col_widths[col]) for col in columns)
        lines.append(header)
        lines.append("-" * len(header))

        # 数据行
        for row in rows:
            line = " | ".join(
                str(row.get(col, "")).ljust(col_widths[col])[:col_widths[col]]
                for col in columns
            )
            lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def to_markdown_table(rows: List[Dict[str, Any]]) -> str:
        """
        格式化为 Markdown 表格

        Args:
            rows: 结果行列表

        Returns:
            Markdown 表格字符串
        """
        if not rows:
            return "No results"

        columns = list(rows[0].keys())

        lines = []

        # 表头
        header = "| " + " | ".join(columns) + " |"
        lines.append(header)

        # 分隔符
        separator = "| " + " | ".join(["---"] * len(columns)) + " |"
        lines.append(separator)

        # 数据行
        for row in rows:
            line = "| " + " | ".join(str(row.get(col, "")) for col in columns) + " |"
            lines.append(line)

        return "\n".join(lines)

