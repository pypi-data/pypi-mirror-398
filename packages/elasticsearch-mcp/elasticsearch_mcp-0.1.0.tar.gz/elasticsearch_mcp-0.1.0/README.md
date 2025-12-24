# elasticsearch-mcp

An MCP (Model Context Protocol) server for Elasticsearch clusters. Enables AI assistants like Claude to search, analyze, and interact with Elasticsearch through natural language.

[![PyPI version](https://badge.fury.io/py/elasticsearch-mcp.svg)](https://badge.fury.io/py/elasticsearch-mcp)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Features

- **Natural Language Search**: Ask Claude about your data in plain English
- **Index Discovery**: Explore indices, mappings, and field types
- **Search & Aggregations**: Full Query DSL and aggregation support
- **Document Operations**: Read, index, update, and delete documents
- **Data Export**: Export search results to JSON or CSV
- **Knowledge Persistence**: Claude remembers what it learns about your cluster
- **Safety Controls**: Read-only mode, index blocking, result limits
- **Connection Watchdog**: Automatic recovery from hung connections
- **OAuth Integration**: Deploy as a Claude.ai Custom Connector with SSO

## Quick Start

### 1. Install

```bash
pip install elasticsearch-mcp
```

### 2. Configure Claude Desktop

Edit your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "elasticsearch": {
      "command": "elasticsearch-mcp",
      "env": {
        "ES_HOST": "https://your-cluster.es.example.com:9200",
        "ES_API_KEY": "your-api-key",
        "ES_READ_ONLY": "true"
      }
    }
  }
}
```

### 3. Restart Claude Desktop

Quit and reopen Claude Desktop. You'll see a hammer icon indicating tools are available.

### 4. Start Chatting

Ask Claude about your Elasticsearch data:

> "What indices are available?"

> "Search for errors in the logs index from the last hour"

> "Show me the top 10 users by request count"

> "Describe the mappings for the customers index"

## Documentation

| Guide | Description |
|-------|-------------|
| [Installation](docs/installation.md) | Complete installation guide |
| [Configuration](docs/configuration.md) | All configuration options |
| [Tools Reference](docs/tools.md) | Detailed tool documentation |
| [Usage Examples](docs/examples.md) | Common usage patterns |
| [OAuth Setup](docs/oauth.md) | Claude.ai integration with SSO |

## Available Tools

### Connection & Cluster
| Tool | Description |
|------|-------------|
| `connect` | Connect to the cluster |
| `disconnect` | Close connections |
| `cluster_health` | Get cluster health status |
| `cluster_info` | Get cluster version and info |

### Index Operations
| Tool | Description |
|------|-------------|
| `list_indices` | List all indices |
| `describe_index` | Get index mappings and settings |
| `get_index_stats` | Get index statistics |

### Search & Query
| Tool | Description |
|------|-------------|
| `search` | Execute Query DSL search |
| `search_simple` | Simple query string search |
| `count` | Count matching documents |
| `get_document` | Get document by ID |

### Aggregations
| Tool | Description |
|------|-------------|
| `aggregate` | Run aggregation queries |
| `terms_aggregation` | Quick terms aggregation |
| `date_histogram` | Time-based aggregations |

### Document Operations
| Tool | Description |
|------|-------------|
| `index_document` | Create/update document |
| `update_document` | Partial document update |
| `delete_document` | Delete document |

### Export & Knowledge
| Tool | Description |
|------|-------------|
| `export_to_json` | Export results to JSON |
| `export_to_csv` | Export results to CSV |
| `save_knowledge` | Save learned information |
| `get_all_knowledge` | Retrieve saved knowledge |

## Configuration

### Required Variables

| Variable | Description |
|----------|-------------|
| `ES_HOST` | Elasticsearch host URL |

### Authentication (choose one)

| Variable | Description |
|----------|-------------|
| `ES_API_KEY` | API key authentication |
| `ES_USERNAME` + `ES_PASSWORD` | Basic authentication |
| `ES_CLOUD_ID` | Elastic Cloud ID |

### Safety Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ES_READ_ONLY` | `false` | Block all write operations |
| `ES_MAX_RESULTS` | `1000` | Maximum results per query |
| `ES_BLOCKED_INDICES` | `.security*,...` | Indices to hide |

## Deployment Modes

### Local (Default)

```bash
elasticsearch-mcp
```

### HTTP/SSE Server

```bash
elasticsearch-mcp --http --host 0.0.0.0 --port 8080
```

### Streamable HTTP (Claude.ai)

```bash
elasticsearch-mcp --streamable-http --host 0.0.0.0 --port 8080
```

## Development

```bash
# Clone repository
git clone https://github.com/bpamiri/elasticsearch-mcp.git
cd elasticsearch-mcp

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint and format
ruff check .
ruff format .

# Type check
mypy src/
```

## Security

- API keys and passwords are never logged
- Configurable index blocklist
- Optional read-only mode
- Result size limits
- Query validation

## License

Apache-2.0. See [LICENSE](LICENSE) for details.

## Links

- [PyPI Package](https://pypi.org/project/elasticsearch-mcp/)
- [GitHub Repository](https://github.com/bpamiri/elasticsearch-mcp)
- [Issue Tracker](https://github.com/bpamiri/elasticsearch-mcp/issues)
- [MCP Documentation](https://modelcontextprotocol.io/)
