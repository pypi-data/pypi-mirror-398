"""Elasticsearch MCP Server - Main entry point."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import settings
from .connection import connection_manager
from .tools import cluster, indices, search

# Initialize FastMCP server
mcp = FastMCP("elasticsearch-mcp")


# =============================================================================
# Connection Tools
# =============================================================================


@mcp.tool()
async def connect() -> dict[str, Any]:
    """Connect to the Elasticsearch cluster.

    Uses configuration from environment variables (ES_HOST, ES_API_KEY, etc.).

    Returns:
        Connection status and cluster information.
    """
    try:
        return await connection_manager.connect()
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def disconnect() -> dict[str, Any]:
    """Disconnect from the Elasticsearch cluster.

    Returns:
        Disconnection status.
    """
    return await connection_manager.disconnect()


@mcp.tool()
async def cluster_health() -> dict[str, Any]:
    """Get the health status of the Elasticsearch cluster.

    Returns:
        Cluster health including status (green/yellow/red), nodes, and shards.
    """
    try:
        return await cluster.cluster_health()
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def cluster_info() -> dict[str, Any]:
    """Get cluster version and information.

    Returns:
        Cluster name, version, build info, and compatibility versions.
    """
    try:
        return await cluster.cluster_info()
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def list_nodes() -> dict[str, Any]:
    """List all nodes in the cluster.

    Returns:
        Node names, IPs, roles, and resource usage (CPU, memory, disk).
    """
    try:
        return await cluster.list_nodes()
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def cluster_stats() -> dict[str, Any]:
    """Get cluster-wide statistics.

    Returns:
        Aggregated statistics for indices and nodes across the cluster.
    """
    try:
        return await cluster.cluster_stats()
    except Exception as e:
        return {"status": "error", "error": str(e)}


# =============================================================================
# Index Tools
# =============================================================================


@mcp.tool()
async def list_indices(pattern: str = "*", include_hidden: bool = False) -> dict[str, Any]:
    """List all indices in the cluster.

    Args:
        pattern: Index pattern to filter (supports wildcards like "logs-*").
        include_hidden: Include hidden indices starting with "." (default: False).

    Returns:
        List of indices with health, status, doc count, and size.
    """
    try:
        return await indices.list_indices(pattern, include_hidden)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def describe_index(index: str) -> dict[str, Any]:
    """Get detailed information about an index.

    Args:
        index: Name of the index to describe.

    Returns:
        Index mappings (fields and types), settings, and statistics.
    """
    try:
        return await indices.describe_index(index)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def get_index_stats(index: str) -> dict[str, Any]:
    """Get statistics for an index.

    Args:
        index: Name of the index.

    Returns:
        Document counts, store size, indexing and search statistics.
    """
    try:
        return await indices.get_index_stats(index)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def get_mappings(index: str) -> dict[str, Any]:
    """Get field mappings for an index.

    Args:
        index: Name of the index.

    Returns:
        Field definitions including types, analyzers, and options.
    """
    try:
        return await indices.get_mappings(index)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def get_aliases(index: str | None = None) -> dict[str, Any]:
    """Get index aliases.

    Args:
        index: Optional index name to filter aliases.

    Returns:
        List of aliases with their target indices.
    """
    try:
        return await indices.get_aliases(index)
    except Exception as e:
        return {"status": "error", "error": str(e)}


# =============================================================================
# Search Tools
# =============================================================================


@mcp.tool()
async def es_search(
    index: str,
    query: dict[str, Any] | None = None,
    size: int | None = None,
    from_: int = 0,
    sort: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Execute a search query using Elasticsearch Query DSL.

    Args:
        index: Index to search (supports wildcards like "logs-*").
        query: Elasticsearch query DSL (e.g., {"match": {"message": "error"}}).
        size: Maximum results to return (default: 10, max: from config).
        from_: Starting offset for pagination.
        sort: Sort specification (e.g., [{"@timestamp": "desc"}]).

    Returns:
        Search hits with _id, _score, and _source fields.
    """
    try:
        return await search.search(index, query, size, from_, sort)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def search_simple(
    index: str,
    q: str,
    size: int | None = None,
) -> dict[str, Any]:
    """Execute a simple query string search.

    Args:
        index: Index to search.
        q: Query string (supports Lucene syntax like "status:error AND level:critical").
        size: Maximum results to return.

    Returns:
        Search hits matching the query string.
    """
    try:
        return await search.search_simple(index, q, size)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def count_docs(
    index: str,
    query: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Count documents matching a query.

    Args:
        index: Index to count.
        query: Optional query to filter documents.

    Returns:
        Document count.
    """
    try:
        return await search.count(index, query)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def get_document(
    index: str,
    doc_id: str,
) -> dict[str, Any]:
    """Get a document by ID.

    Args:
        index: Index containing the document.
        doc_id: Document ID.

    Returns:
        Document source data or not found error.
    """
    try:
        return await search.get_document(index, doc_id)
    except Exception as e:
        return {"status": "error", "error": str(e)}


# =============================================================================
# Aggregation Tools
# =============================================================================


@mcp.tool()
async def aggregate(
    index: str,
    aggs: dict[str, Any],
    query: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute an aggregation query.

    Args:
        index: Index to aggregate.
        aggs: Aggregation definition (e.g., {"status_count": {"terms": {"field": "status"}}}).
        query: Optional query to filter documents before aggregating.

    Returns:
        Aggregation results with buckets and metrics.
    """
    try:
        return await search.aggregate(index, aggs, query)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def terms_aggregation(
    index: str,
    field: str,
    size: int = 10,
    query: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Get top values for a field (terms aggregation).

    Args:
        index: Index to aggregate.
        field: Field to get top values for (must be keyword or numeric).
        size: Number of top terms to return (default: 10).
        query: Optional query to filter documents.

    Returns:
        Top field values with document counts.
    """
    try:
        return await search.terms_aggregation(index, field, size, query)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def date_histogram(
    index: str,
    field: str,
    interval: str = "day",
    query: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Get document counts over time (date histogram).

    Args:
        index: Index to aggregate.
        field: Date field to aggregate on (e.g., "@timestamp").
        interval: Time interval (minute, hour, day, week, month, year).
        query: Optional query to filter documents.

    Returns:
        Time buckets with document counts.
    """
    try:
        return await search.date_histogram(index, field, interval, query)
    except Exception as e:
        return {"status": "error", "error": str(e)}


# =============================================================================
# CLI Entry Point
# =============================================================================


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Elasticsearch MCP Server - Connect AI assistants to Elasticsearch"
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run as HTTP/SSE server (legacy mode)",
    )
    parser.add_argument(
        "--streamable-http",
        action="store_true",
        help="Run as Streamable HTTP server for Claude.ai Integrations",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="HTTP server host (overrides ES_HTTP_HOST env var)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="HTTP server port (overrides ES_HTTP_PORT env var)",
    )

    args = parser.parse_args()

    # Determine host and port
    host = args.host or settings.http_host
    port = args.port or settings.http_port

    if args.streamable_http:
        # Streamable HTTP mode for Claude.ai
        print(f"Starting Elasticsearch MCP Server (Streamable HTTP) on {host}:{port}")
        # TODO: Implement streamable HTTP with OAuth
        print("Streamable HTTP mode not yet implemented")
        sys.exit(1)
    elif args.http:
        # Legacy HTTP/SSE mode
        print(f"Starting Elasticsearch MCP Server (HTTP/SSE) on {host}:{port}")
        # TODO: Implement HTTP/SSE mode
        print("HTTP/SSE mode not yet implemented")
        sys.exit(1)
    else:
        # Default stdio mode
        print("Starting Elasticsearch MCP Server (stdio)", file=sys.stderr)
        mcp.run()


if __name__ == "__main__":
    main()
