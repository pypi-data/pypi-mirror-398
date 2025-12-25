"""Connection management for elasticsearch-mcp."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from elasticsearch import AsyncElasticsearch

from .config import settings


@dataclass
class ConnectionState:
    """State of an Elasticsearch connection."""

    client: AsyncElasticsearch | None = None
    connected_at: datetime | None = None
    cluster_name: str | None = None
    cluster_uuid: str | None = None
    version: str | None = None


@dataclass
class ConnectionManager:
    """Manages Elasticsearch connections."""

    _state: ConnectionState = field(default_factory=ConnectionState)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @property
    def client(self) -> AsyncElasticsearch | None:
        """Get the current client."""
        return self._state.client

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._state.client is not None

    async def connect(self) -> dict[str, Any]:
        """Connect to Elasticsearch cluster.

        Returns:
            Connection status and cluster info.
        """
        async with self._lock:
            if self._state.client is not None:
                return {
                    "status": "already_connected",
                    "cluster_name": self._state.cluster_name,
                    "cluster_uuid": self._state.cluster_uuid,
                    "version": self._state.version,
                    "connected_at": self._state.connected_at.isoformat()
                    if self._state.connected_at
                    else None,
                }

            # Build client configuration
            client_kwargs: dict[str, Any] = {
                "hosts": [settings.host],
                "request_timeout": settings.timeout,
                "verify_certs": settings.verify_certs,
            }

            # Authentication
            if settings.api_key:
                client_kwargs["api_key"] = settings.api_key
            elif settings.username and settings.password:
                client_kwargs["basic_auth"] = (settings.username, settings.password)
            elif settings.cloud_id:
                client_kwargs["cloud_id"] = settings.cloud_id
                del client_kwargs["hosts"]

            # SSL configuration
            if settings.ca_certs:
                client_kwargs["ca_certs"] = settings.ca_certs

            # Create client
            client = AsyncElasticsearch(**client_kwargs)

            # Test connection and get cluster info
            try:
                info = await client.info()
                health = await client.cluster.health()

                self._state.client = client
                self._state.connected_at = datetime.now()
                self._state.cluster_name = info.get("cluster_name")
                self._state.cluster_uuid = info.get("cluster_uuid")
                self._state.version = info.get("version", {}).get("number")

                return {
                    "status": "connected",
                    "cluster_name": self._state.cluster_name,
                    "cluster_uuid": self._state.cluster_uuid,
                    "version": self._state.version,
                    "cluster_status": health.get("status"),
                    "number_of_nodes": health.get("number_of_nodes"),
                    "connected_at": self._state.connected_at.isoformat(),
                }
            except Exception as e:
                await client.close()
                raise ConnectionError(f"Failed to connect to Elasticsearch: {e}") from e

    async def disconnect(self) -> dict[str, Any]:
        """Disconnect from Elasticsearch cluster.

        Returns:
            Disconnection status.
        """
        async with self._lock:
            if self._state.client is None:
                return {"status": "not_connected"}

            try:
                await self._state.client.close()
            except Exception:
                pass  # Ignore errors on close

            cluster_name = self._state.cluster_name
            self._state = ConnectionState()

            return {
                "status": "disconnected",
                "cluster_name": cluster_name,
            }

    async def ensure_connected(self) -> AsyncElasticsearch:
        """Ensure connection exists, connecting if needed.

        Returns:
            The Elasticsearch client.

        Raises:
            ConnectionError: If not connected and auto-connect fails.
        """
        if self._state.client is None:
            await self.connect()

        if self._state.client is None:
            raise ConnectionError("Not connected to Elasticsearch")

        return self._state.client

    async def get_cluster_health(self) -> dict[str, Any]:
        """Get cluster health status.

        Returns:
            Cluster health information.
        """
        client = await self.ensure_connected()
        health = await client.cluster.health()

        return {
            "cluster_name": health.get("cluster_name"),
            "status": health.get("status"),
            "number_of_nodes": health.get("number_of_nodes"),
            "number_of_data_nodes": health.get("number_of_data_nodes"),
            "active_primary_shards": health.get("active_primary_shards"),
            "active_shards": health.get("active_shards"),
            "relocating_shards": health.get("relocating_shards"),
            "initializing_shards": health.get("initializing_shards"),
            "unassigned_shards": health.get("unassigned_shards"),
            "delayed_unassigned_shards": health.get("delayed_unassigned_shards"),
            "number_of_pending_tasks": health.get("number_of_pending_tasks"),
            "task_max_waiting_in_queue_millis": health.get("task_max_waiting_in_queue_millis"),
            "active_shards_percent_as_number": health.get("active_shards_percent_as_number"),
        }

    async def get_cluster_info(self) -> dict[str, Any]:
        """Get cluster information.

        Returns:
            Cluster version and info.
        """
        client = await self.ensure_connected()
        info = await client.info()

        version_info = info.get("version", {})
        return {
            "cluster_name": info.get("cluster_name"),
            "cluster_uuid": info.get("cluster_uuid"),
            "version": version_info.get("number"),
            "build_flavor": version_info.get("build_flavor"),
            "build_type": version_info.get("build_type"),
            "build_hash": version_info.get("build_hash"),
            "build_date": version_info.get("build_date"),
            "lucene_version": version_info.get("lucene_version"),
            "minimum_wire_compatibility_version": version_info.get(
                "minimum_wire_compatibility_version"
            ),
            "minimum_index_compatibility_version": version_info.get(
                "minimum_index_compatibility_version"
            ),
        }

    def get_connection_info(self) -> dict[str, Any]:
        """Get current connection information.

        Returns:
            Connection state information.
        """
        if not self.is_connected:
            return {"status": "not_connected"}

        return {
            "status": "connected",
            "cluster_name": self._state.cluster_name,
            "cluster_uuid": self._state.cluster_uuid,
            "version": self._state.version,
            "connected_at": self._state.connected_at.isoformat()
            if self._state.connected_at
            else None,
        }


# Global connection manager instance
connection_manager = ConnectionManager()
