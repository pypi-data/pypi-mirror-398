"""Search operations for elasticsearch-mcp."""

from __future__ import annotations

import fnmatch
from typing import Any

from ..config import settings
from ..connection import connection_manager


def _is_blocked_index(index_name: str) -> bool:
    """Check if an index matches any blocked pattern."""
    for pattern in settings.blocked_indices_list:
        if fnmatch.fnmatch(index_name, pattern):
            return True
    return False


async def search(
    index: str,
    query: dict[str, Any] | None = None,
    size: int | None = None,
    from_: int = 0,
    sort: list[dict[str, Any]] | None = None,
    source: list[str] | bool | None = None,
    highlight: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a search query using Elasticsearch Query DSL.

    Args:
        index: Index to search (supports wildcards).
        query: Elasticsearch query DSL (e.g., {"match": {"field": "value"}}).
        size: Maximum number of results (default: from config).
        from_: Starting offset for pagination.
        sort: Sort specification.
        source: Fields to include in _source (True/False or list of fields).
        highlight: Highlight specification.

    Returns:
        Search results with hits and metadata.
    """
    if _is_blocked_index(index):
        return {"error": f"Access to index '{index}' is blocked"}

    client = await connection_manager.ensure_connected()

    # Apply size limits
    max_size = settings.max_results
    if size is None:
        size = min(10, max_size)
    else:
        size = min(size, max_size)

    # Build search body
    body: dict[str, Any] = {}
    if query:
        body["query"] = query
    if sort:
        body["sort"] = sort
    if highlight:
        body["highlight"] = highlight

    # Convert source list to proper format
    source_param: bool | dict[str, Any] | None = None
    if isinstance(source, bool):
        source_param = source
    elif isinstance(source, list):
        source_param = {"includes": source}

    try:
        response = await client.search(
            index=index,
            body=body if body else None,
            size=size,
            from_=from_,
            source=source_param,
        )

        hits = response.get("hits", {})
        results = []
        for hit in hits.get("hits", []):
            result = {
                "_index": hit.get("_index"),
                "_id": hit.get("_id"),
                "_score": hit.get("_score"),
                "_source": hit.get("_source", {}),
            }
            if "highlight" in hit:
                result["highlight"] = hit["highlight"]
            results.append(result)

        return {
            "index": index,
            "total": hits.get("total", {}).get("value", 0),
            "total_relation": hits.get("total", {}).get("relation", "eq"),
            "max_score": hits.get("max_score"),
            "hits": results,
            "count": len(results),
            "from": from_,
            "size": size,
            "took_ms": response.get("took", 0),
            "timed_out": response.get("timed_out", False),
        }
    except Exception as e:
        return {"error": str(e), "index": index}


async def search_simple(
    index: str,
    q: str,
    size: int | None = None,
    default_field: str | None = None,
) -> dict[str, Any]:
    """Execute a simple query string search.

    Args:
        index: Index to search.
        q: Query string (supports Lucene query syntax).
        size: Maximum number of results.
        default_field: Default field for query string.

    Returns:
        Search results.
    """
    if _is_blocked_index(index):
        return {"error": f"Access to index '{index}' is blocked"}

    client = await connection_manager.ensure_connected()

    # Apply size limits
    max_size = settings.max_results
    if size is None:
        size = min(10, max_size)
    else:
        size = min(size, max_size)

    # Build query
    query: dict[str, Any] = {
        "query_string": {
            "query": q,
        }
    }
    if default_field:
        query["query_string"]["default_field"] = default_field

    try:
        response = await client.search(
            index=index,
            query=query,
            size=size,
        )

        hits = response.get("hits", {})
        results = []
        for hit in hits.get("hits", []):
            results.append(
                {
                    "_index": hit.get("_index"),
                    "_id": hit.get("_id"),
                    "_score": hit.get("_score"),
                    "_source": hit.get("_source", {}),
                }
            )

        return {
            "index": index,
            "query": q,
            "total": hits.get("total", {}).get("value", 0),
            "hits": results,
            "count": len(results),
            "took_ms": response.get("took", 0),
        }
    except Exception as e:
        return {"error": str(e), "index": index, "query": q}


async def count(
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
    if _is_blocked_index(index):
        return {"error": f"Access to index '{index}' is blocked"}

    client = await connection_manager.ensure_connected()

    try:
        if query:
            response = await client.count(index=index, query=query)
        else:
            response = await client.count(index=index)

        return {
            "index": index,
            "count": response.get("count", 0),
        }
    except Exception as e:
        return {"error": str(e), "index": index}


async def get_document(
    index: str,
    doc_id: str,
    source: list[str] | bool | None = None,
) -> dict[str, Any]:
    """Get a document by ID.

    Args:
        index: Index containing the document.
        doc_id: Document ID.
        source: Fields to include in _source.

    Returns:
        Document data.
    """
    if _is_blocked_index(index):
        return {"error": f"Access to index '{index}' is blocked"}

    client = await connection_manager.ensure_connected()

    try:
        response = await client.get(
            index=index,
            id=doc_id,
            source=source,
        )

        return {
            "index": response.get("_index"),
            "id": response.get("_id"),
            "version": response.get("_version"),
            "found": response.get("found", False),
            "source": response.get("_source", {}),
        }
    except Exception as e:
        error_str = str(e)
        if "404" in error_str or "NotFoundError" in error_str:
            return {
                "index": index,
                "id": doc_id,
                "found": False,
                "error": "Document not found",
            }
        return {"error": str(e), "index": index, "id": doc_id}


async def aggregate(
    index: str,
    aggs: dict[str, Any],
    query: dict[str, Any] | None = None,
    size: int = 0,
) -> dict[str, Any]:
    """Execute an aggregation query.

    Args:
        index: Index to aggregate.
        aggs: Aggregation definition.
        query: Optional query to filter documents.
        size: Number of hits to return (default: 0 for aggregations only).

    Returns:
        Aggregation results.
    """
    if _is_blocked_index(index):
        return {"error": f"Access to index '{index}' is blocked"}

    client = await connection_manager.ensure_connected()

    body: dict[str, Any] = {"aggs": aggs}
    if query:
        body["query"] = query

    try:
        response = await client.search(
            index=index,
            body=body,
            size=size,
        )

        return {
            "index": index,
            "aggregations": response.get("aggregations", {}),
            "total": response.get("hits", {}).get("total", {}).get("value", 0),
            "took_ms": response.get("took", 0),
        }
    except Exception as e:
        return {"error": str(e), "index": index}


async def terms_aggregation(
    index: str,
    field: str,
    size: int = 10,
    query: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a terms aggregation (top values for a field).

    Args:
        index: Index to aggregate.
        field: Field to aggregate on.
        size: Number of top terms to return.
        query: Optional query to filter documents.

    Returns:
        Terms aggregation results.
    """
    aggs = {
        "terms_agg": {
            "terms": {
                "field": field,
                "size": size,
            }
        }
    }

    result = await aggregate(index, aggs, query, size=0)

    if "error" in result:
        return result

    buckets = result.get("aggregations", {}).get("terms_agg", {}).get("buckets", [])

    return {
        "index": index,
        "field": field,
        "buckets": [{"key": b.get("key"), "doc_count": b.get("doc_count")} for b in buckets],
        "total": result.get("total", 0),
        "took_ms": result.get("took_ms", 0),
    }


async def date_histogram(
    index: str,
    field: str,
    interval: str = "day",
    query: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a date histogram aggregation.

    Args:
        index: Index to aggregate.
        field: Date field to aggregate on.
        interval: Calendar interval (minute, hour, day, week, month, year).
        query: Optional query to filter documents.

    Returns:
        Date histogram results.
    """
    aggs = {
        "date_hist": {
            "date_histogram": {
                "field": field,
                "calendar_interval": interval,
            }
        }
    }

    result = await aggregate(index, aggs, query, size=0)

    if "error" in result:
        return result

    buckets = result.get("aggregations", {}).get("date_hist", {}).get("buckets", [])

    return {
        "index": index,
        "field": field,
        "interval": interval,
        "buckets": [
            {
                "key": b.get("key"),
                "key_as_string": b.get("key_as_string"),
                "doc_count": b.get("doc_count"),
            }
            for b in buckets
        ],
        "total": result.get("total", 0),
        "took_ms": result.get("took_ms", 0),
    }
