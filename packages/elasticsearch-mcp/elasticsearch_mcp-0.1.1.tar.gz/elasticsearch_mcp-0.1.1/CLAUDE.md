# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

elasticsearch-mcp is a Python MCP (Model Context Protocol) server that enables AI assistants to interact with Elasticsearch clusters. It uses the official `elasticsearch` Python client and provides tools for searching, aggregations, and document management.

## Development Commands

```bash
# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest                                      # All tests
pytest tests/test_connection.py             # Single file
pytest --cov=elasticsearch_mcp --cov-report=html    # With coverage

# Linting and type checking
ruff check .
ruff format .
mypy src/
```

## Tech Stack

- **Language**: Python 3.10+
- **MCP Framework**: `mcp` (FastMCP)
- **Elasticsearch Client**: `elasticsearch` (official Python client)
- **Build System**: hatchling with pyproject.toml
- **Testing**: pytest, pytest-cov, pytest-mock, pytest-asyncio
- **Linting/Formatting**: ruff
- **Type Checking**: mypy
- **Settings**: pydantic-settings (environment variable binding)

## Architecture

```
src/elasticsearch_mcp/
├── server.py           # FastMCP server entry point
├── connection.py       # Connection management
├── config.py           # Pydantic settings, environment config
├── tools/              # MCP tool implementations
│   ├── cluster.py      # Cluster health, info
│   ├── indices.py      # Index operations
│   ├── search.py       # Search & query
│   ├── aggregations.py # Aggregation queries
│   ├── documents.py    # CRUD operations
│   ├── export.py       # JSON/CSV export
│   └── knowledge.py    # Knowledge persistence
├── auth/               # OAuth authentication
│   ├── provider.py     # OAuth provider
│   ├── storage.py      # Token storage
│   └── idp/            # Identity provider adapters
├── resources/          # MCP resources
│   ├── knowledge.py    # Knowledge resource
│   ├── syntax_help.py  # Query DSL reference
│   └── examples.py     # Example queries
└── utils/
    ├── safety.py       # Query validation
    ├── watchdog.py     # Connection watchdog
    ├── knowledge.py    # Knowledge file manager
    └── audit.py        # Audit logging
```

## Environment Variables

Required: `ES_HOST`
Authentication: `ES_API_KEY` or `ES_USERNAME`/`ES_PASSWORD` or `ES_CLOUD_ID`
Optional: `ES_TIMEOUT`, `ES_READ_ONLY`, `ES_MAX_RESULTS`, `ES_BLOCKED_INDICES`

## Coding Standards

- Follow PEP 8; use ruff for linting/formatting
- Maximum line length: 100 characters
- Type hints required for all function signatures
- Google-style docstrings for public APIs

## Key Patterns

**Connection Pattern**: Use `elasticsearch.AsyncElasticsearch` for async operations.

**Safety Controls**: Index pattern validation, blocked indices list, read-only mode.

**Schema Discovery**: Use `_cat/indices`, `_mapping`, and `_settings` APIs for metadata.

## Reference Implementations

- [pymssql-mcp](https://github.com/bpamiri/pymssql-mcp) - SQL Server MCP
- [u2-mcp](https://github.com/bpamiri/u2-mcp) - Universe/UniData MCP
