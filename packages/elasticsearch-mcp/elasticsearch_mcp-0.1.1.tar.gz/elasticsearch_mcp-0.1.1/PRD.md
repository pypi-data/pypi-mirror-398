# elasticsearch-mcp Product Requirements Document

## Overview

**elasticsearch-mcp** is an MCP (Model Context Protocol) server that enables AI assistants like Claude to interact with Elasticsearch clusters through natural language. Users can search, analyze, and manage Elasticsearch data without writing complex queries.

## Vision

Allow non-technical users to query and explore Elasticsearch data using natural language, while providing power users with full access to Elasticsearch capabilities through Claude.

## Target Users

- Data analysts exploring log data
- DevOps engineers investigating issues
- Business users accessing indexed business data
- Developers prototyping search functionality

---

## Core Features

### 1. Connection Management

| Feature | Description | Priority |
|---------|-------------|----------|
| `connect` | Connect to Elasticsearch cluster with authentication | P0 |
| `disconnect` | Close connections | P0 |
| `list_connections` | Show active connections | P1 |
| `cluster_health` | Get cluster health status | P0 |
| `cluster_info` | Get cluster version and info | P1 |

**Configuration:**
- `ES_HOST` - Elasticsearch host URL (required)
- `ES_API_KEY` - API key authentication
- `ES_USERNAME` / `ES_PASSWORD` - Basic authentication
- `ES_CLOUD_ID` - Elastic Cloud ID
- `ES_CA_CERTS` - Path to CA certificates
- `ES_VERIFY_CERTS` - SSL certificate verification
- `ES_TIMEOUT` - Connection timeout

### 2. Index Operations

| Feature | Description | Priority |
|---------|-------------|----------|
| `list_indices` | List all indices with stats | P0 |
| `describe_index` | Get index mappings and settings | P0 |
| `get_index_stats` | Get index document count, size | P1 |
| `create_index` | Create new index with mappings | P2 |
| `delete_index` | Delete an index (with safety) | P2 |

### 3. Search & Query

| Feature | Description | Priority |
|---------|-------------|----------|
| `search` | Execute search query with DSL | P0 |
| `search_simple` | Simple query string search | P0 |
| `count` | Count documents matching query | P0 |
| `get_document` | Get document by ID | P0 |
| `multi_search` | Execute multiple searches | P2 |

**Safety Controls:**
- `ES_MAX_RESULTS` - Maximum documents per query (default: 1000)
- `ES_READ_ONLY` - Disable write operations
- `ES_BLOCKED_INDICES` - Indices to hide/block access

### 4. Aggregations & Analytics

| Feature | Description | Priority |
|---------|-------------|----------|
| `aggregate` | Run aggregation queries | P0 |
| `terms_aggregation` | Quick terms aggregation | P1 |
| `date_histogram` | Time-based aggregations | P1 |
| `stats_aggregation` | Statistical aggregations | P1 |

### 5. Document Operations (CRUD)

| Feature | Description | Priority |
|---------|-------------|----------|
| `index_document` | Index/create a document | P1 |
| `update_document` | Update existing document | P1 |
| `delete_document` | Delete document by ID | P1 |
| `bulk_operations` | Bulk index/update/delete | P2 |

### 6. Data Export

| Feature | Description | Priority |
|---------|-------------|----------|
| `export_to_json` | Export search results to JSON | P1 |
| `export_to_csv` | Export search results to CSV | P1 |
| `export_to_ndjson` | Export in NDJSON format | P2 |

### 7. Index Management

| Feature | Description | Priority |
|---------|-------------|----------|
| `refresh_index` | Refresh index for search | P2 |
| `get_aliases` | List index aliases | P1 |
| `get_mappings` | Get field mappings | P0 |
| `analyze_text` | Test analyzer on text | P2 |

---

## Infrastructure Features

### 8. Knowledge Persistence

Store learned information about the Elasticsearch cluster across sessions.

| Feature | Description | Priority |
|---------|-------------|----------|
| `save_knowledge` | Save discovered information | P0 |
| `list_knowledge` | List saved topics | P0 |
| `get_all_knowledge` | Retrieve all knowledge | P0 |
| `get_knowledge_topic` | Get specific topic | P1 |
| `search_knowledge` | Search saved knowledge | P1 |
| `delete_knowledge` | Remove a topic | P2 |

**What to save:**
- Index purposes and contents
- Field meanings and types
- Common query patterns
- Data retention policies
- Index relationships

**Configuration:**
- `ES_KNOWLEDGE_PATH` - Custom knowledge file path (default: `~/.elasticsearch-mcp/knowledge.md`)

### 9. Connection Watchdog

Automatic recovery from hung or stale connections.

| Feature | Description |
|---------|-------------|
| Health monitoring | Periodic cluster pings |
| Auto-reconnection | Reconnect on failure |
| Timeout detection | Detect hung queries |

**Configuration:**
- `ES_WATCHDOG_ENABLED` - Enable watchdog (default: true)
- `ES_WATCHDOG_INTERVAL` - Check interval seconds (default: 30)
- `ES_WATCHDOG_TIMEOUT` - Query timeout seconds (default: 60)

### 10. Audit Logging

Track all operations for security and debugging.

**Configuration:**
- `ES_AUDIT_ENABLED` - Enable audit logging
- `ES_AUDIT_PATH` - Audit log file path
- `ES_AUDIT_LEVEL` - Logging level

---

## Deployment Modes

### 11. Local Mode (stdio)

Default mode for Claude Desktop integration.

```bash
elasticsearch-mcp
```

### 12. HTTP/SSE Mode

Centralized server for multiple users.

```bash
elasticsearch-mcp --http --host 0.0.0.0 --port 8080
```

**Configuration:**
- `ES_HTTP_HOST` - HTTP server host
- `ES_HTTP_PORT` - HTTP server port
- `ES_HTTP_CORS_ORIGINS` - CORS allowed origins

### 13. Streamable HTTP Mode (Claude.ai)

For Claude.ai Custom Connector integration with OAuth.

```bash
elasticsearch-mcp --streamable-http --host 0.0.0.0 --port 8080
```

---

## OAuth Integration

### 14. OAuth 2.0 Support

Full OAuth authentication for Claude.ai integration.

| Feature | Description |
|---------|-------------|
| Dynamic Client Registration | RFC 7591 compliant |
| Authorization Code Flow | With PKCE support |
| Token Refresh | Automatic token renewal |
| Token Revocation | Secure logout |

**Supported Identity Providers:**
- Cisco Duo
- Auth0
- Azure AD / Entra ID
- Okta
- Generic OIDC

**Configuration:**
- `ES_AUTH_ENABLED` - Enable OAuth
- `ES_AUTH_ISSUER_URL` - OAuth issuer URL
- `ES_IDP_PROVIDER` - IdP type (duo, auth0, oidc)
- `ES_IDP_DISCOVERY_URL` - OIDC discovery URL
- `ES_IDP_CLIENT_ID` - IdP client ID
- `ES_IDP_CLIENT_SECRET` - IdP client secret
- `ES_IDP_SCOPES` - OAuth scopes
- `ES_TOKEN_EXPIRY_SECONDS` - Access token lifetime
- `ES_REFRESH_TOKEN_EXPIRY_SECONDS` - Refresh token lifetime

---

## MCP Resources

### 15. Built-in Resources

| Resource | Description |
|----------|-------------|
| `elasticsearch://knowledge` | All saved knowledge |
| `elasticsearch://syntax_help` | Query DSL reference |
| `elasticsearch://query_examples` | Example queries |

---

## Safety & Security

### 16. Safety Controls

| Feature | Description | Default |
|---------|-------------|---------|
| Read-only mode | Block all write operations | false |
| Result limits | Cap search results | 1000 |
| Index blocklist | Hide sensitive indices | [] |
| Query validation | Validate before execution | true |

**Default blocked indices:**
- `.security*`
- `.kibana*`
- `.apm*`
- `.monitoring*`

### 17. Security Features

- API key authentication
- Basic authentication
- SSL/TLS support
- Credentials never logged
- Parameterized queries

---

## Technical Specifications

### Dependencies

- `elasticsearch` - Official Elasticsearch Python client
- `mcp` - Model Context Protocol SDK
- `pydantic-settings` - Configuration management
- `httpx` - HTTP client for OAuth
- `uvicorn` - ASGI server

### Python Version

- Python 3.10+

### Project Structure

```
src/elasticsearch_mcp/
├── __init__.py
├── server.py              # FastMCP server entry point
├── connection.py          # Connection management
├── config.py              # Pydantic settings
├── tools/
│   ├── __init__.py
│   ├── cluster.py         # Cluster operations
│   ├── indices.py         # Index operations
│   ├── search.py          # Search & query
│   ├── aggregations.py    # Aggregation queries
│   ├── documents.py       # CRUD operations
│   ├── export.py          # Data export
│   └── knowledge.py       # Knowledge persistence
├── auth/
│   ├── __init__.py
│   ├── provider.py        # OAuth provider
│   ├── storage.py         # Token storage
│   ├── callback.py        # OAuth callback handler
│   └── idp/
│       ├── __init__.py
│       ├── base.py        # Base IdP adapter
│       ├── duo.py         # Cisco Duo
│       ├── auth0.py       # Auth0
│       └── oidc.py        # Generic OIDC
├── resources/
│   ├── __init__.py
│   ├── knowledge.py       # Knowledge resource
│   ├── syntax_help.py     # Query DSL reference
│   └── examples.py        # Example queries
└── utils/
    ├── __init__.py
    ├── safety.py          # Query validation
    ├── watchdog.py        # Connection watchdog
    ├── knowledge.py       # Knowledge file manager
    └── audit.py           # Audit logging
```

---

## Milestones

### v0.1.0 - Foundation
- [ ] Connection management
- [ ] Basic search operations
- [ ] Index listing and description
- [ ] Configuration with pydantic-settings
- [ ] CLI entry point

### v0.2.0 - Core Features
- [ ] Full search capabilities
- [ ] Aggregations
- [ ] Document CRUD
- [ ] Data export
- [ ] Safety controls

### v0.3.0 - Knowledge & Resources
- [ ] Knowledge persistence
- [ ] MCP resources
- [ ] Query examples
- [ ] Syntax help

### v0.4.0 - Infrastructure
- [ ] Connection watchdog
- [ ] Audit logging
- [ ] HTTP/SSE mode
- [ ] Transaction support (if applicable)

### v0.5.0 - OAuth & Claude.ai
- [ ] Streamable HTTP mode
- [ ] OAuth provider
- [ ] IdP adapters (Duo, Auth0, OIDC)
- [ ] Claude.ai integration

### v1.0.0 - Production Ready
- [ ] Comprehensive documentation
- [ ] Full test coverage
- [ ] Performance optimization
- [ ] Security audit

---

## Success Metrics

- Query response time < 2s for typical searches
- 99% uptime for HTTP deployments
- Zero credential leaks in logs
- Full feature parity with pymssql-mcp OAuth

---

## References

- [pymssql-mcp](https://github.com/bpamiri/pymssql-mcp) - Reference implementation
- [u2-mcp](https://github.com/bpamiri/u2-mcp) - Reference implementation
- [Elasticsearch Python Client](https://elasticsearch-py.readthedocs.io/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
