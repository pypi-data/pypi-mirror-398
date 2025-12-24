"""Index operations for elasticsearch-mcp."""

from __future__ import annotations

import fnmatch
from typing import Any, cast

from ..config import settings
from ..connection import connection_manager


def _is_blocked_index(index_name: str) -> bool:
    """Check if an index matches any blocked pattern."""
    for pattern in settings.blocked_indices_list:
        if fnmatch.fnmatch(index_name, pattern):
            return True
    return False


async def list_indices(
    pattern: str = "*",
    include_hidden: bool = False,
) -> dict[str, Any]:
    """List all indices in the cluster.

    Args:
        pattern: Index pattern to filter (supports wildcards).
        include_hidden: Include hidden indices (starting with .).

    Returns:
        List of indices with their stats.
    """
    client = await connection_manager.ensure_connected()

    # Get index stats
    try:
        cat_response = await client.cat.indices(
            index=pattern,
            format="json",
            h="index,health,status,pri,rep,docs.count,store.size,pri.store.size",
        )
    except Exception as e:
        return {"error": str(e), "indices": [], "count": 0}

    indices = []
    for item in cat_response:
        idx = cast(dict[str, Any], item)
        index_name = idx.get("index", "")

        # Skip blocked indices
        if _is_blocked_index(index_name):
            continue

        # Skip hidden indices unless requested
        if not include_hidden and index_name.startswith("."):
            continue

        indices.append(
            {
                "name": index_name,
                "health": idx.get("health"),
                "status": idx.get("status"),
                "primary_shards": int(idx.get("pri", 0) or 0),
                "replica_shards": int(idx.get("rep", 0) or 0),
                "doc_count": int(idx.get("docs.count", 0) or 0),
                "store_size": idx.get("store.size"),
                "primary_store_size": idx.get("pri.store.size"),
            }
        )

    # Sort by name
    indices.sort(key=lambda x: x["name"])

    return {
        "indices": indices,
        "count": len(indices),
        "pattern": pattern,
    }


async def describe_index(index: str) -> dict[str, Any]:
    """Get detailed information about an index.

    Args:
        index: Name of the index to describe.

    Returns:
        Index mappings, settings, and stats.
    """
    if _is_blocked_index(index):
        return {"error": f"Access to index '{index}' is blocked"}

    client = await connection_manager.ensure_connected()

    result: dict[str, Any] = {"index": index}

    # Get mappings
    try:
        mappings_response = await client.indices.get_mapping(index=index)
        if index in mappings_response:
            mappings = mappings_response[index].get("mappings", {})
            properties = mappings.get("properties", {})

            # Flatten field mappings
            fields = []
            for field_name, field_def in properties.items():
                field_info = {
                    "name": field_name,
                    "type": field_def.get("type", "object"),
                }
                if "analyzer" in field_def:
                    field_info["analyzer"] = field_def["analyzer"]
                if "index" in field_def:
                    field_info["indexed"] = field_def["index"]
                if "fields" in field_def:
                    field_info["multi_fields"] = list(field_def["fields"].keys())
                fields.append(field_info)

            result["fields"] = sorted(fields, key=lambda x: x["name"])
            result["field_count"] = len(fields)
    except Exception as e:
        result["mappings_error"] = str(e)

    # Get settings
    try:
        settings_response = await client.indices.get_settings(index=index)
        if index in settings_response:
            idx_settings = settings_response[index].get("settings", {}).get("index", {})
            result["settings"] = {
                "number_of_shards": idx_settings.get("number_of_shards"),
                "number_of_replicas": idx_settings.get("number_of_replicas"),
                "creation_date": idx_settings.get("creation_date"),
                "uuid": idx_settings.get("uuid"),
                "version": idx_settings.get("version", {}).get("created"),
            }
    except Exception as e:
        result["settings_error"] = str(e)

    # Get stats
    try:
        stats_response = await client.indices.stats(index=index)
        if "_all" in stats_response:
            primaries = stats_response["_all"].get("primaries", {})
            result["stats"] = {
                "doc_count": primaries.get("docs", {}).get("count", 0),
                "deleted_doc_count": primaries.get("docs", {}).get("deleted", 0),
                "store_size_bytes": primaries.get("store", {}).get("size_in_bytes", 0),
                "indexing_total": primaries.get("indexing", {}).get("index_total", 0),
                "search_query_total": primaries.get("search", {}).get("query_total", 0),
            }
    except Exception as e:
        result["stats_error"] = str(e)

    return result


async def get_index_stats(index: str) -> dict[str, Any]:
    """Get statistics for an index.

    Args:
        index: Name of the index.

    Returns:
        Index statistics.
    """
    if _is_blocked_index(index):
        return {"error": f"Access to index '{index}' is blocked"}

    client = await connection_manager.ensure_connected()

    try:
        stats_response = await client.indices.stats(index=index)

        if "_all" not in stats_response:
            return {"error": f"Index '{index}' not found", "index": index}

        primaries = stats_response["_all"].get("primaries", {})
        total = stats_response["_all"].get("total", {})

        return {
            "index": index,
            "primaries": {
                "docs": primaries.get("docs", {}),
                "store": primaries.get("store", {}),
                "indexing": {
                    "index_total": primaries.get("indexing", {}).get("index_total", 0),
                    "index_time_in_millis": primaries.get("indexing", {}).get(
                        "index_time_in_millis", 0
                    ),
                    "delete_total": primaries.get("indexing", {}).get("delete_total", 0),
                },
                "search": {
                    "query_total": primaries.get("search", {}).get("query_total", 0),
                    "query_time_in_millis": primaries.get("search", {}).get(
                        "query_time_in_millis", 0
                    ),
                    "fetch_total": primaries.get("search", {}).get("fetch_total", 0),
                },
            },
            "total": {
                "docs": total.get("docs", {}),
                "store": total.get("store", {}),
            },
        }
    except Exception as e:
        return {"error": str(e), "index": index}


async def get_mappings(index: str) -> dict[str, Any]:
    """Get field mappings for an index.

    Args:
        index: Name of the index.

    Returns:
        Field mappings.
    """
    if _is_blocked_index(index):
        return {"error": f"Access to index '{index}' is blocked"}

    client = await connection_manager.ensure_connected()

    try:
        response = await client.indices.get_mapping(index=index)

        if index not in response:
            return {"error": f"Index '{index}' not found", "index": index}

        mappings = response[index].get("mappings", {})
        properties = mappings.get("properties", {})

        return {
            "index": index,
            "mappings": properties,
            "field_count": len(properties),
        }
    except Exception as e:
        return {"error": str(e), "index": index}


async def get_aliases(index: str | None = None) -> dict[str, Any]:
    """Get index aliases.

    Args:
        index: Optional index name to filter.

    Returns:
        Alias information.
    """
    client = await connection_manager.ensure_connected()

    try:
        if index:
            if _is_blocked_index(index):
                return {"error": f"Access to index '{index}' is blocked"}
            response = await client.indices.get_alias(index=index)
        else:
            response = await client.indices.get_alias()

        aliases = []
        for idx_name, idx_data in response.items():
            if _is_blocked_index(idx_name):
                continue
            for alias_name, alias_data in idx_data.get("aliases", {}).items():
                aliases.append(
                    {
                        "alias": alias_name,
                        "index": idx_name,
                        "filter": alias_data.get("filter"),
                        "routing": alias_data.get("routing"),
                    }
                )

        return {
            "aliases": aliases,
            "count": len(aliases),
        }
    except Exception as e:
        return {"error": str(e), "aliases": [], "count": 0}
