# Data Recon MCP Server

An MCP (Model Context Protocol) server for data reconciliation between MySQL and Snowflake databases. Enables LLM agents like Claude, Antigravity, and Perplexity to validate data integrity during migrations, ETL processes, and ongoing monitoring.

## 🚀 Quick Start

### Installation

```bash
pip install data-recon-mcp
```

### Configuration

Add to your MCP client configuration:

**For Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "data-recon": {
      "command": "python3",
      "args": ["-m", "mcp_server"]
    }
  }
}
```

**For Antigravity** (`~/.gemini/antigravity/mcp_config.json`):
```json
{
  "data-recon": {
    "command": "python3",
    "args": ["-m", "mcp_server"]
  }
}
```

**For Perplexity** (MCP Settings):
```json
{
  "data-recon": {
    "command": "python3",
    "args": ["-m", "mcp_server"]
  }
}
```

That's it! Restart your LLM client and start using the tools.

## ✨ Features

- **All-in-One** - Single command starts everything (MCP server + FastAPI backend)
- **23 MCP Tools** for comprehensive data reconciliation
- **MySQL and Snowflake** support
- **Async job execution** with progress tracking
- **SQLite metadata storage** - datasource configs persist locally

## 🔧 Advanced Configuration

### Using a Centralized Backend

For team environments where you want everyone to share the same datasources:

**1. Start the centralized backend:**
```bash
git clone https://github.com/hindocharaj1997/data-recon-mcp.git
cd data-recon-mcp
pip install -e .
uvicorn data_recon.main:app --host 0.0.0.0 --port 8000
```

**2. Configure clients to use it:**
```json
{
  "data-recon": {
    "command": "python3",
    "args": ["-m", "mcp_server"],
    "env": {
      "FASTAPI_URL": "http://your-server.company.com:8000"
    }
  }
}
```

### Pre-configured Data Sources

Register data sources via environment variables:

```json
{
  "data-recon": {
    "command": "python3",
    "args": ["-m", "mcp_server"],
    "env": {
      "DATASOURCE_MYSQL_PROD": "{\"type\":\"mysql\",\"host\":\"localhost\",\"port\":3306,\"username\":\"user\",\"password\":\"pass\",\"database\":\"mydb\"}"
    }
  }
}
```

## 📊 MCP Tools

| Category | Tools | Description |
|----------|-------|-------------|
| **Data Source Management** | 7 | Add, list, test, remove datasources |
| **Discovery & Validation** | 7 | Search tables, validate existence, preview data |
| **Individual Checks** | 4 | Row count, aggregates, schema, sample rows |
| **Job Management** | 5 | Create/monitor reconciliation jobs |

### Key Tools

- `add_datasource` - Register a MySQL or Snowflake connection
- `search_tables` - Find tables by pattern
- `run_row_count_check` - Compare row counts between source and target
- `run_aggregate_check` - Compare SUM, AVG, MIN, MAX values
- `create_recon_job` - Run comprehensive reconciliation with all checks

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    LLM Client                           │
│              (Claude, Antigravity, etc.)                │
└─────────────────────┬───────────────────────────────────┘
                      │ MCP Protocol (stdio)
                      ▼
┌─────────────────────────────────────────────────────────┐
│                 MCP Server                              │
│            (python3 -m mcp_server)                      │
├─────────────────────────────────────────────────────────┤
│  Embedded FastAPI Backend (or external via FASTAPI_URL) │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │   SQLite    │  │   MySQL     │  │   Snowflake     │ │
│  │  (metadata) │  │  Connector  │  │   Connector     │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 🧪 Development

```bash
# Clone and setup
git clone https://github.com/hindocharaj1997/data-recon-mcp.git
cd data-recon-mcp
pip install -e ".[dev]"

# Run tests
pytest

# Start local MySQL for testing
docker compose -f tests/docker-compose.yml up -d
```

## 📝 License

MIT

## 🤝 Contributing

Contributions welcome! Please open an issue first to discuss proposed changes.
