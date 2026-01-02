"""
DVT Docs Serve - Catalog API

v0.56.0: Catalog nodes, search, and node details.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from fastapi import APIRouter, HTTPException, Query
except ImportError:
    # Provide stub for when FastAPI is not installed
    class APIRouter:
        def __init__(self, *args, **kwargs):
            pass
        def get(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    class HTTPException(Exception):
        def __init__(self, status_code, detail):
            self.status_code = status_code
            self.detail = detail
    def Query(*args, **kwargs):
        return None


router = APIRouter(prefix="/api/catalog", tags=["catalog"])

# Will be set by serve.py
_project_root: Optional[Path] = None
_store_initialized: bool = False


def set_project_root(project_root: Path) -> None:
    """Set project root for API access."""
    global _project_root, _store_initialized
    _project_root = project_root
    _store_initialized = True  # Assume serve.py already initialized


def _get_store():
    """Get metadata store instance (lazy initialization)."""
    global _store_initialized

    if _project_root is None:
        raise HTTPException(status_code=500, detail="Project root not configured")

    try:
        from dbt.compute.metadata import ProjectMetadataStore
        store = ProjectMetadataStore(_project_root)
        # Only initialize if not already done by serve.py
        if not _store_initialized:
            store.initialize()
            _store_initialized = True
        return store
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not open metadata store: {e}")


@router.get("/nodes")
async def list_catalog_nodes(
    resource_type: Optional[str] = Query(None, description="Filter by type: model, source, test, seed, snapshot"),
) -> List[Dict[str, Any]]:
    """
    List all catalog nodes.

    Returns all nodes from the catalog, optionally filtered by resource type.
    """
    store = _get_store()

    try:
        if resource_type:
            nodes = store.get_catalog_nodes_by_type(resource_type)
        else:
            nodes = store.get_all_catalog_nodes()

        return [
            {
                "unique_id": n.unique_id,
                "resource_type": n.resource_type,
                "name": n.name,
                "schema": n.schema_name,
                "database": n.database,
                "connection": n.connection_name,
                "adapter": n.adapter_type,
                "description": n.description,
                "icon": n.icon_type,
                "color": n.color_hex,
                "materialized": n.materialized,
                "row_count": n.row_count,
            }
            for n in nodes
        ]
    finally:
        store.close()


@router.get("/nodes/{unique_id}")
async def get_catalog_node(unique_id: str) -> Dict[str, Any]:
    """
    Get a specific catalog node by unique ID.

    Returns full node details including columns.
    """
    import json

    store = _get_store()

    try:
        node = store.get_catalog_node(unique_id)
        if not node:
            raise HTTPException(status_code=404, detail=f"Node not found: {unique_id}")

        return {
            "unique_id": node.unique_id,
            "resource_type": node.resource_type,
            "name": node.name,
            "schema": node.schema_name,
            "database": node.database,
            "connection": node.connection_name,
            "adapter": node.adapter_type,
            "description": node.description,
            "icon": node.icon_type,
            "color": node.color_hex,
            "materialized": node.materialized,
            "tags": json.loads(node.tags) if node.tags else [],
            "meta": json.loads(node.meta) if node.meta else {},
            "columns": json.loads(node.columns) if node.columns else [],
            "row_count": node.row_count,
            "bytes_stored": node.bytes_stored,
            "created_at": node.created_at.isoformat() if node.created_at else None,
            "updated_at": node.updated_at.isoformat() if node.updated_at else None,
        }
    finally:
        store.close()


@router.get("/search")
async def search_catalog(
    q: str = Query(..., description="Search query"),
) -> List[Dict[str, Any]]:
    """
    Search catalog nodes by name or description.

    Returns matching nodes sorted by relevance.
    """
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

    store = _get_store()

    try:
        nodes = store.search_catalog_nodes(q)
        return [
            {
                "unique_id": n.unique_id,
                "resource_type": n.resource_type,
                "name": n.name,
                "schema": n.schema_name,
                "connection": n.connection_name,
                "description": n.description,
                "icon": n.icon_type,
                "color": n.color_hex,
            }
            for n in nodes
        ]
    finally:
        store.close()


@router.get("/stats")
async def get_catalog_stats() -> Dict[str, Any]:
    """
    Get catalog statistics.

    Returns counts of nodes by type, connections, etc.
    """
    store = _get_store()

    try:
        all_nodes = store.get_all_catalog_nodes()

        # Count by type
        type_counts: Dict[str, int] = {}
        connection_counts: Dict[str, int] = {}
        adapter_counts: Dict[str, int] = {}

        for node in all_nodes:
            type_counts[node.resource_type] = type_counts.get(node.resource_type, 0) + 1
            if node.connection_name:
                connection_counts[node.connection_name] = connection_counts.get(node.connection_name, 0) + 1
            if node.adapter_type:
                adapter_counts[node.adapter_type] = adapter_counts.get(node.adapter_type, 0) + 1

        return {
            "total_nodes": len(all_nodes),
            "by_type": type_counts,
            "by_connection": connection_counts,
            "by_adapter": adapter_counts,
        }
    finally:
        store.close()
