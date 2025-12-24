"""Cluster operations for elasticsearch-mcp."""

from __future__ import annotations

from typing import Any, cast

from ..connection import connection_manager


async def cluster_health() -> dict[str, Any]:
    """Get the health status of the Elasticsearch cluster.

    Returns:
        Cluster health information including status, nodes, and shards.
    """
    return await connection_manager.get_cluster_health()


async def cluster_info() -> dict[str, Any]:
    """Get cluster version and information.

    Returns:
        Cluster version, build info, and compatibility info.
    """
    return await connection_manager.get_cluster_info()


async def list_nodes() -> dict[str, Any]:
    """List all nodes in the cluster.

    Returns:
        Node information including name, IP, roles, and resource usage.
    """
    client = await connection_manager.ensure_connected()

    try:
        response = await client.cat.nodes(
            format="json",
            h="name,ip,node.role,master,heap.percent,ram.percent,cpu,load_1m,disk.used_percent",
        )

        nodes = []
        for item in response:
            node = cast(dict[str, Any], item)
            nodes.append(
                {
                    "name": node.get("name"),
                    "ip": node.get("ip"),
                    "roles": node.get("node.role"),
                    "is_master": node.get("master") == "*",
                    "heap_percent": node.get("heap.percent"),
                    "ram_percent": node.get("ram.percent"),
                    "cpu_percent": node.get("cpu"),
                    "load_1m": node.get("load_1m"),
                    "disk_used_percent": node.get("disk.used_percent"),
                }
            )

        return {
            "nodes": nodes,
            "count": len(nodes),
        }
    except Exception as e:
        return {"error": str(e), "nodes": [], "count": 0}


async def node_stats(node_id: str | None = None) -> dict[str, Any]:
    """Get detailed statistics for nodes.

    Args:
        node_id: Optional node ID to filter (default: all nodes).

    Returns:
        Detailed node statistics.
    """
    client = await connection_manager.ensure_connected()

    try:
        if node_id:
            response = await client.nodes.stats(node_id=node_id)
        else:
            response = await client.nodes.stats()

        nodes_data = response.get("nodes", {})
        nodes = []

        for nid, node in nodes_data.items():
            nodes.append(
                {
                    "id": nid,
                    "name": node.get("name"),
                    "transport_address": node.get("transport_address"),
                    "host": node.get("host"),
                    "ip": node.get("ip"),
                    "roles": node.get("roles", []),
                    "os": {
                        "cpu_percent": node.get("os", {}).get("cpu", {}).get("percent"),
                        "mem_used_percent": node.get("os", {}).get("mem", {}).get("used_percent"),
                        "mem_free_bytes": node.get("os", {}).get("mem", {}).get("free_in_bytes"),
                    },
                    "jvm": {
                        "heap_used_percent": node.get("jvm", {})
                        .get("mem", {})
                        .get("heap_used_percent"),
                        "heap_max_bytes": node.get("jvm", {})
                        .get("mem", {})
                        .get("heap_max_in_bytes"),
                        "uptime_ms": node.get("jvm", {}).get("uptime_in_millis"),
                    },
                    "indices": {
                        "docs_count": node.get("indices", {}).get("docs", {}).get("count", 0),
                        "store_size_bytes": node.get("indices", {})
                        .get("store", {})
                        .get("size_in_bytes", 0),
                        "indexing_total": node.get("indices", {})
                        .get("indexing", {})
                        .get("index_total", 0),
                        "search_query_total": node.get("indices", {})
                        .get("search", {})
                        .get("query_total", 0),
                    },
                }
            )

        return {
            "cluster_name": response.get("cluster_name"),
            "nodes": nodes,
            "count": len(nodes),
        }
    except Exception as e:
        return {"error": str(e)}


async def cluster_stats() -> dict[str, Any]:
    """Get cluster-wide statistics.

    Returns:
        Aggregated statistics across the cluster.
    """
    client = await connection_manager.ensure_connected()

    try:
        response = await client.cluster.stats()

        return {
            "cluster_name": response.get("cluster_name"),
            "cluster_uuid": response.get("cluster_uuid"),
            "status": response.get("status"),
            "indices": {
                "count": response.get("indices", {}).get("count", 0),
                "shards": response.get("indices", {}).get("shards", {}),
                "docs": response.get("indices", {}).get("docs", {}),
                "store": response.get("indices", {}).get("store", {}),
            },
            "nodes": {
                "count": response.get("nodes", {}).get("count", {}),
                "versions": response.get("nodes", {}).get("versions", []),
                "os": response.get("nodes", {}).get("os", {}),
                "jvm": response.get("nodes", {}).get("jvm", {}),
            },
        }
    except Exception as e:
        return {"error": str(e)}


async def pending_tasks() -> dict[str, Any]:
    """Get pending cluster tasks.

    Returns:
        List of pending tasks in the cluster.
    """
    client = await connection_manager.ensure_connected()

    try:
        response = await client.cluster.pending_tasks()

        tasks = []
        for task in response.get("tasks", []):
            tasks.append(
                {
                    "insert_order": task.get("insert_order"),
                    "priority": task.get("priority"),
                    "source": task.get("source"),
                    "time_in_queue_millis": task.get("time_in_queue_millis"),
                    "time_in_queue": task.get("time_in_queue"),
                }
            )

        return {
            "tasks": tasks,
            "count": len(tasks),
        }
    except Exception as e:
        return {"error": str(e), "tasks": [], "count": 0}


async def allocation_explain(index: str | None = None, shard: int | None = None) -> dict[str, Any]:
    """Explain shard allocation decisions.

    Args:
        index: Optional index name.
        shard: Optional shard number.

    Returns:
        Shard allocation explanation.
    """
    client = await connection_manager.ensure_connected()

    try:
        body: dict[str, Any] = {}
        if index:
            body["index"] = index
        if shard is not None:
            body["shard"] = shard

        response = await client.cluster.allocation_explain(body=body if body else None)

        return {
            "index": response.get("index"),
            "shard": response.get("shard"),
            "primary": response.get("primary"),
            "current_state": response.get("current_state"),
            "unassigned_info": response.get("unassigned_info"),
            "can_allocate": response.get("can_allocate"),
            "allocate_explanation": response.get("allocate_explanation"),
            "node_allocation_decisions": response.get("node_allocation_decisions", [])[:5],  # Limit
        }
    except Exception as e:
        error_str = str(e)
        if "illegal_argument_exception" in error_str.lower():
            return {"message": "No unassigned shards to explain", "status": "all_assigned"}
        return {"error": str(e)}
