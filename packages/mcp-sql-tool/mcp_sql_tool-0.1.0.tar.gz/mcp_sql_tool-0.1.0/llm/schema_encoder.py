"""Schema 编码器：将数据库表结构转换为 LLM 可理解的格式"""

from typing import Dict, Any, List
from database.adapters import TableSchema


class SchemaEncoder:
    """Schema 编码器"""

    def encode_table(self, schema: TableSchema) -> str:
        """
        编码单个表结构为文本格式

        Args:
            schema: 表结构对象

        Returns:
            编码后的文本
        """
        lines = [f"Table: {schema.name}"]
        if schema.comment:
            lines.append(f"Comment: {schema.comment}")

        lines.append("Columns:")
        for col in schema.columns:
            col_info = f"  - {col.get('name', 'unknown')}: {col.get('type', 'unknown')}"
            if col.get("null"):
                col_info += " (nullable)"
            if col.get("default"):
                col_info += f" DEFAULT {col.get('default')}"
            if col.get("pk"):
                col_info += " PRIMARY KEY"
            lines.append(col_info)

        if schema.indexes:
            lines.append("Indexes:")
            for idx in schema.indexes:
                idx_info = f"  - {idx.get('name', 'unknown')}"
                if idx.get("unique"):
                    idx_info += " (unique)"
                if "column" in idx:
                    idx_info += f" on {idx.get('column')}"
                lines.append(idx_info)

        if schema.foreign_keys:
            lines.append("Foreign Keys:")
            for fk in schema.foreign_keys:
                fk_info = f"  - {fk.get('name', 'unknown')}: {fk.get('column', 'unknown')}"
                if "referenced_table" in fk:
                    fk_info += f" -> {fk.get('referenced_table')}.{fk.get('referenced_column', 'unknown')}"
                lines.append(fk_info)

        return "\n".join(lines)

    def encode_database(self, schemas: Dict[str, TableSchema]) -> str:
        """
        编码整个数据库的 Schema

        Args:
            schemas: 表名到表结构的映射字典

        Returns:
            编码后的文本
        """
        if not schemas:
            return "No tables found in database."

        lines = [f"Database Schema ({len(schemas)} tables):", ""]

        for table_name, schema in schemas.items():
            lines.append(self.encode_table(schema))
            lines.append("")  # 空行分隔

        return "\n".join(lines)

    def encode_json(self, schemas: Dict[str, TableSchema]) -> Dict[str, Any]:
        """
        编码为 JSON 格式

        Args:
            schemas: 表名到表结构的映射字典

        Returns:
            JSON 格式的字典
        """
        result = {}
        for table_name, schema in schemas.items():
            result[table_name] = {
                "name": schema.name,
                "comment": schema.comment,
                "columns": schema.columns,
                "indexes": schema.indexes,
                "foreign_keys": schema.foreign_keys,
            }
        return result

