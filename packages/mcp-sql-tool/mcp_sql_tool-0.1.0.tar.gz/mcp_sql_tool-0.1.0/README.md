# MCP SQL Tool

基于 MCP (Model Context Protocol) 协议的智能 SQL BI 工具，通过大模型自动生成 SQL 语句并执行数据库查询，实现自然语言到 SQL 的转换。

[![PyPI version](https://badge.fury.io/py/mcp-sql-tool.svg)](https://badge.fury.io/py/mcp-sql-tool)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 快速开始

### 安装

```bash
pip install mcp-sql-tool
```

### 配置

```bash
# 初始化配置文件
mcp-sql-tool --init-config

# 编辑配置文件
# ~/.mcp_sql_tool/config/config.yaml
```

### 使用

```bash
# 启动服务器
mcp-sql-tool

# 测试数据库连接
mcp-sql-test-db
```

详细安装和使用说明请参考 [INSTALLATION.md](INSTALLATION.md)

## 功能特性

- 🚀 **自然语言转SQL**：通过 LLM 将用户自然语言查询转换为 SQL 语句
- 🗄️ **多数据库支持**：支持 MySQL、PostgreSQL、SQLite、ClickHouse 等主流数据库
- 📊 **Schema 感知**：自动获取数据库表结构，帮助 LLM 生成准确的 SQL
- 🔒 **SQL 安全控制**：防止 SQL 注入，支持只读模式、查询超时等安全机制
- 📈 **结果可视化**：支持表格、JSON、CSV、Markdown 等多种数据展示方式
- 📝 **查询历史**：记录查询历史，支持查询缓存和复用

## 项目结构

```
mcp_sql_tool/
├── mcp_server/          # MCP 协议服务端
├── llm/                 # LLM 集成模块
├── database/            # 数据库连接与执行模块
├── security/            # 安全控制模块
├── storage/             # 数据存储模块
├── utils/               # 工具模块
├── config/              # 配置文件
├── main.py              # 主入口
└── requirements.txt     # 依赖包
```

## 安装

### 方式一：从 PyPI 安装（推荐）

```bash
pip install mcp-sql-tool
```

### 方式二：从源码安装

```bash
git clone <repository-url>
cd mcp_sql_tool
pip install -e .
```

详细安装说明请参考 [INSTALLATION.md](INSTALLATION.md)

### 3. 数据库设置

项目支持多种数据库类型，根据您的需求选择并启动相应的数据库：

#### MySQL

**使用 Docker 启动 MySQL（推荐）：**

```bash
docker run -d \
  --name mysql-server \
  -e MYSQL_ROOT_PASSWORD=your_password \
  -e MYSQL_DATABASE=your_database \
  -e MYSQL_USER=your_user \
  -e MYSQL_PASSWORD=your_password \
  -p 3306:3306 \
  mysql:8.0
```

**或使用本地 MySQL：**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install mysql-server
sudo systemctl start mysql

# macOS (使用 Homebrew)
brew install mysql
brew services start mysql

# 创建数据库和用户
mysql -u root -p
CREATE DATABASE your_database;
CREATE USER 'your_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON your_database.* TO 'your_user'@'localhost';
FLUSH PRIVILEGES;
```

#### PostgreSQL

**使用 Docker 启动 PostgreSQL：**

```bash
docker run -d \
  --name postgres-server \
  -e POSTGRES_DB=your_database \
  -e POSTGRES_USER=your_user \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  postgres:15
```

**或使用本地 PostgreSQL：**

```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql

# macOS (使用 Homebrew)
brew install postgresql
brew services start postgresql

# 创建数据库和用户
sudo -u postgres psql
CREATE DATABASE your_database;
CREATE USER your_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE your_database TO your_user;
```

#### SQLite

SQLite 不需要单独启动，直接使用数据库文件即可：

```bash
# SQLite 数据库文件会自动创建
# 只需在配置中指定文件路径
```

在 `config/config.yaml` 中配置：
```yaml
databases:
  - name: "default"
    type: "sqlite"
    database: "data/mcp_sql_tool.db"  # 数据库文件路径
```

#### ClickHouse

**使用 Docker 启动 ClickHouse：**

```bash
docker run -d \
  --name clickhouse-server \
  -p 8123:8123 \
  -p 9000:9000 \
  clickhouse/clickhouse-server
```

**或使用本地 ClickHouse：**

```bash
# Ubuntu/Debian
sudo apt-get install clickhouse-server clickhouse-client
sudo systemctl start clickhouse-server

# macOS (使用 Homebrew)
brew install clickhouse
brew services start clickhouse
```

### 4. 配置环境变量

创建 `.env` 文件或设置环境变量：

```bash
# LLM 配置
export LLM_API_KEY="your-api-key"
export LLM_PROVIDER="openai"  # openai, claude, qwen
export LLM_MODEL="gpt-4"

# 数据库配置（根据您选择的数据库类型）
export DB_HOST="localhost"
export DB_PORT="3306"  # MySQL: 3306, PostgreSQL: 5432, ClickHouse: 9000
export DB_NAME="your_database"
export DB_USER="your_user"
export DB_PASSWORD="your_password"
```

### 5. 配置文件

编辑 `config/config.yaml` 文件，配置数据库连接和 LLM 设置。

**示例配置（MySQL）：**
```yaml
databases:
  - name: "default"
    type: "mysql"
    host: "${DB_HOST}"
    port: 3306
    database: "${DB_NAME}"
    user: "${DB_USER}"
    password: "${DB_PASSWORD}"
    read_only: true
    max_connections: 10
```

**示例配置（SQLite）：**
```yaml
databases:
  - name: "default"
    type: "sqlite"
    database: "data/example.db"  # 文件路径
    read_only: true
```

### 6. 测试数据库连接

在启动 MCP Server 之前，建议先测试数据库连接是否正常：

**MySQL：**
```bash
mysql -h localhost -u your_user -p your_database
```

**PostgreSQL：**
```bash
psql -h localhost -U your_user -d your_database
```

**SQLite：**
```bash
sqlite3 data/example.db
```

**ClickHouse：**
```bash
clickhouse-client --host localhost --port 9000
```

如果能够成功连接，说明数据库配置正确。

**或使用项目提供的测试脚本：**
```bash
python scripts/test_db_connection.py
```

这个脚本会自动读取配置文件并测试所有配置的数据库连接。

## 使用方法

### 运行 MCP Server

项目支持三种通信协议：**stdio**、**http** 和 **sse**。

#### 1. STDIO 模式（默认）

通过标准输入输出进行通信，适用于本地工具和命令行应用：

```bash
python main.py
```

或在 `config/config.yaml` 中设置：
```yaml
mcp:
  transport: "stdio"
```

#### 2. HTTP 模式

将 MCP Server 转换为可通过 URL 访问的 Web 服务：

在 `config/config.yaml` 中设置：
```yaml
mcp:
  transport: "http"
  host: "0.0.0.0"
  port: 8000
```

运行后，服务器将在 `http://0.0.0.0:8000/mcp/` 提供 MCP 服务。

#### 3. SSE 模式

使用 Server-Sent Events 进行通信（主要用于向后兼容）：

在 `config/config.yaml` 中设置：
```yaml
mcp:
  transport: "sse"
  host: "0.0.0.0"
  port: 8000
```

运行后，服务器将在 `http://0.0.0.0:8000/sse/` 提供 MCP 服务。

#### 4. 多协议模式

同时启用所有三种协议（使用多线程）：

在 `config/config.yaml` 中设置：
```yaml
mcp:
  transport: "all"
  host: "0.0.0.0"
  http_port: 8000
  sse_port: 8001
```

这将同时启动：
- HTTP 服务器（`http://0.0.0.0:8000/mcp/`）
- SSE 服务器（`http://0.0.0.0:8001/sse/`）

**注意**：STDIO 模式不能与其他协议同时运行，因为它需要阻塞主线程来读取标准输入。如果需要 STDIO 模式，请单独使用 `transport: "stdio"`。

### 通过 MCP 协议调用

MCP Server 提供以下工具：

1. **execute_sql**: 执行 SQL 查询或根据自然语言生成并执行 SQL
2. **get_schema**: 获取数据库表结构信息
3. **list_tables**: 列出数据库中的所有表
4. **explain_query**: 解释 SQL 查询的执行计划

#### STDIO 模式调用示例

通过标准输入发送 JSON-RPC 请求：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "execute_sql",
    "arguments": {
      "query": "查询最近7天的订单总数",
      "database": "default",
      "limit": 100
    }
  }
}
```

#### HTTP 模式调用示例

使用 HTTP POST 请求调用：

```bash
curl -X POST http://localhost:8000/mcp/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "execute_sql",
      "arguments": {
        "query": "查询最近7天的订单总数",
        "database": "default"
      }
    }
  }'
```

#### 获取表结构示例

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "get_schema",
    "arguments": {
      "database": "default",
      "table": "orders"
    }
  }
}
```

## 配置说明

### LLM 配置

支持以下 LLM 提供商：

- **OpenAI**: `provider: "openai"`, 需要设置 `OPENAI_API_KEY`
- **Anthropic Claude**: `provider: "claude"`, 需要设置 `ANTHROPIC_API_KEY`
- **通义千问**: `provider: "qwen"`, 需要设置 `DASHSCOPE_API_KEY`

### 数据库配置

支持以下数据库类型：

- **MySQL**: `type: "mysql"`
- **PostgreSQL**: `type: "postgresql"`
- **SQLite**: `type: "sqlite"`
- **ClickHouse**: `type: "clickhouse"`

### 安全配置

- `read_only_mode`: 是否只读模式（默认 true）
- `max_query_timeout`: 最大查询超时时间（秒）
- `max_result_rows`: 最大结果行数
- `allowed_operations`: 允许的 SQL 操作列表

## 架构设计

项目采用分层架构设计：

1. **MCP Server 层**: 处理 MCP 协议通信
2. **LLM 集成层**: SQL 生成核心
3. **安全控制层**: SQL 验证、权限管理、查询限制
4. **数据库层**: 统一接口，支持多数据库
5. **存储层**: 元数据管理，独立于业务数据库

详细架构说明请参考 [ARCHITECTURE.md](ARCHITECTURE.md) 和 [FRAMEWORK.md](FRAMEWORK.md)。

## 开发

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black .
flake8 .
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

