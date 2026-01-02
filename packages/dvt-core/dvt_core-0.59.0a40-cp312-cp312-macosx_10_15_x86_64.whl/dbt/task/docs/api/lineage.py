"""
DVT Docs Serve - Lineage API

v0.56.0: Lineage graph, node traversal, and cross-connection edges.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from fastapi import APIRouter, HTTPException, Query
except ImportError:
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


router = APIRouter(prefix="/api/lineage", tags=["lineage"])

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


@router.get("/graph")
async def get_lineage_graph() -> Dict[str, Any]:
    """
    Get the full lineage graph.

    Returns nodes and edges suitable for visualization.
    """
    store = _get_store()

    try:
        graph = store.get_lineage_graph()
        return graph
    finally:
        store.close()


@router.get("/node/{node_id}")
async def get_node_lineage(
    node_id: str,
    depth: int = Query(1, ge=1, le=10, description="Traversal depth"),
) -> Dict[str, Any]:
    """
    Get lineage for a specific node.

    Returns upstream and downstream nodes up to specified depth using BFS traversal.
    """
    store = _get_store()

    try:
        # Get the node
        node = store.get_catalog_node(node_id)
        if not node:
            raise HTTPException(status_code=404, detail=f"Node not found: {node_id}")

        # BFS traversal for upstream nodes
        upstream_nodes = _traverse_lineage(
            store, node_id, depth, direction="upstream"
        )

        # BFS traversal for downstream nodes
        downstream_nodes = _traverse_lineage(
            store, node_id, depth, direction="downstream"
        )

        return {
            "node": {
                "unique_id": node.unique_id,
                "name": node.name,
                "resource_type": node.resource_type,
                "connection": node.connection_name,
                "icon": node.icon_type,
                "color": node.color_hex,
            },
            "upstream": upstream_nodes,
            "downstream": downstream_nodes,
            "depth": depth,
        }
    finally:
        store.close()


def _traverse_lineage(
    store, start_node_id: str, max_depth: int, direction: str
) -> List[Dict[str, Any]]:
    """
    BFS traversal of lineage graph.

    Args:
        store: ProjectMetadataStore instance
        start_node_id: Starting node ID
        max_depth: Maximum traversal depth
        direction: "upstream" or "downstream"

    Returns:
        List of nodes with depth information
    """
    from collections import deque

    visited = set()
    result = []

    # Queue: (node_id, current_depth, edge_info)
    queue = deque([(start_node_id, 0, None)])
    visited.add(start_node_id)

    while queue:
        current_id, current_depth, edge_info = queue.popleft()

        # Skip the start node itself
        if current_depth > 0:
            node = store.get_catalog_node(current_id)
            if node:
                result.append({
                    "unique_id": node.unique_id,
                    "name": node.name,
                    "resource_type": node.resource_type,
                    "connection": node.connection_name,
                    "depth": current_depth,
                    "edge_type": edge_info.edge_type if edge_info else None,
                    "is_cross_connection": edge_info.is_cross_connection if edge_info else False,
                })

        # Stop if we've reached max depth
        if current_depth >= max_depth:
            continue

        # Get edges based on direction
        if direction == "upstream":
            edges = store.get_upstream_edges(current_id)
            next_nodes = [(e.source_node_id, e) for e in edges]
        else:
            edges = store.get_downstream_edges(current_id)
            next_nodes = [(e.target_node_id, e) for e in edges]

        # Add unvisited neighbors to queue
        for next_id, edge in next_nodes:
            if next_id not in visited:
                visited.add(next_id)
                queue.append((next_id, current_depth + 1, edge))

    return result


@router.get("/cross-connection")
async def get_cross_connection_edges() -> List[Dict[str, Any]]:
    """
    Get all cross-connection edges.

    Returns edges that span different database connections.
    """
    store = _get_store()

    try:
        edges = store.get_cross_connection_edges()
        return [
            {
                "id": e.id,
                "source_node_id": e.source_node_id,
                "target_node_id": e.target_node_id,
                "edge_type": e.edge_type,
                "source_connection": e.source_connection,
                "target_connection": e.target_connection,
            }
            for e in edges
        ]
    finally:
        store.close()


@router.get("/stats")
async def get_lineage_stats() -> Dict[str, Any]:
    """
    Get lineage statistics.

    Returns edge counts, cross-connection counts, etc.
    """
    store = _get_store()

    try:
        all_edges = store.get_all_lineage_edges()
        cross_edges = store.get_cross_connection_edges()

        # Count by edge type
        type_counts: Dict[str, int] = {}
        for edge in all_edges:
            type_counts[edge.edge_type] = type_counts.get(edge.edge_type, 0) + 1

        return {
            "total_edges": len(all_edges),
            "cross_connection_edges": len(cross_edges),
            "by_type": type_counts,
        }
    finally:
        store.close()
