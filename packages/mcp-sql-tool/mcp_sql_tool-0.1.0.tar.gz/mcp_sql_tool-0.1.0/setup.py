"""Setup script for mcp-sql-tool"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取 README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="mcp-sql-tool",
    version="0.1.0",
    description="基于 MCP 协议的智能 SQL BI 工具，通过大模型自动生成 SQL 语句并执行数据库查询",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="MCP SQL Tool Team",
    author_email="",
    url="https://github.com/yourusername/mcp-sql-tool",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "mcp_sql_tool": [
            "config/*.yaml",
            "config/*.yml",
        ],
    },
    install_requires=[
        "fastmcp>=0.9.0",
        "pymysql>=1.1.0",
        "psycopg2-binary>=2.9.9",
        "clickhouse-driver>=0.2.6",
        "openai>=1.0.0",
        "anthropic>=0.18.0",
        "dashscope>=1.17.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
        "uvicorn>=0.24.0",
        "sqlparse>=0.4.4",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mcp-sql-tool=main:main",
            "mcp-sql-test-db=scripts.test_db_connection:test_connection",
        ],
    },
    license="MIT",
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="mcp sql llm database bi nlp natural-language",
)

