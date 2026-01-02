"""
DVT Docs Serve - Profile API

v0.56.0: Profile results, alerts, and table profiles.
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


router = APIRouter(prefix="/api/profile", tags=["profile"])

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


@router.get("/tables")
async def list_profiled_tables() -> List[Dict[str, Any]]:
    """
    List all profiled tables.

    Returns table names with last profile timestamp and mode.
    """
    store = _get_store()

    try:
        tables = store.get_all_profiled_tables()
        return [
            {
                "source_name": t[0],
                "table_name": t[1],
                "profile_mode": t[2],
                "last_profiled": t[3].isoformat() if t[3] else None,
            }
            for t in tables
        ]
    finally:
        store.close()


@router.get("/tables/{source_name}/{table_name}")
async def get_table_profile(
    source_name: str,
    table_name: str,
    mode: Optional[str] = Query(None, description="Profile mode filter"),
) -> Dict[str, Any]:
    """
    Get profile results for a specific table.

    Returns all column profiles with metrics.
    """
    import json

    store = _get_store()

    try:
        profiles = store.get_table_profile(source_name, table_name, mode)
        if not profiles:
            raise HTTPException(
                status_code=404,
                detail=f"No profile found for {source_name}.{table_name}"
            )

        # Get first profile for table-level stats
        first = profiles[0]

        return {
            "source_name": source_name,
            "table_name": table_name,
            "profile_mode": first.profile_mode,
            "row_count": first.row_count,
            "column_count": len(profiles),
            "profiled_at": first.profiled_at.isoformat() if first.profiled_at else None,
            "columns": [
                {
                    "column_name": p.column_name,
                    "null_count": p.null_count,
                    "null_percent": p.null_percent,
                    "distinct_count": p.distinct_count,
                    "distinct_percent": p.distinct_percent,
                    "min_value": p.min_value,
                    "max_value": p.max_value,
                    "mean_value": p.mean_value,
                    "median_value": p.median_value,
                    "stddev_value": p.stddev_value,
                    "p25": p.p25,
                    "p50": p.p50,
                    "p75": p.p75,
                    "min_length": p.min_length,
                    "max_length": p.max_length,
                    "avg_length": p.avg_length,
                    "histogram": json.loads(p.histogram) if p.histogram else None,
                    "top_values": json.loads(p.top_values) if p.top_values else None,
                    "alerts": json.loads(p.alerts) if p.alerts else [],
                    "duration_ms": p.duration_ms,
                }
                for p in profiles
            ],
        }
    finally:
        store.close()


@router.get("/alerts")
async def get_profile_alerts(
    source_name: Optional[str] = Query(None, description="Filter by source"),
    severity: Optional[str] = Query(None, description="Filter by severity: info, warning, error"),
) -> List[Dict[str, Any]]:
    """
    Get all profile alerts.

    Returns alerts from profile results, optionally filtered.
    """
    store = _get_store()

    try:
        alerts = store.get_profile_alerts(source_name)

        # Filter by severity if provided
        if severity:
            alerts = [a for a in alerts if a.get("severity") == severity]

        return alerts
    finally:
        store.close()


@router.get("/stats")
async def get_profile_stats() -> Dict[str, Any]:
    """
    Get profiling statistics.

    Returns counts of profiled tables, columns, alerts.
    """
    store = _get_store()

    try:
        tables = store.get_all_profiled_tables()
        alerts = store.get_profile_alerts()

        # Count alerts by type
        alert_types: Dict[str, int] = {}
        for alert in alerts:
            alert_type = alert.get("type", "unknown")
            alert_types[alert_type] = alert_types.get(alert_type, 0) + 1

        # Count alerts by severity
        alert_severities: Dict[str, int] = {}
        for alert in alerts:
            severity = alert.get("severity", "info")
            alert_severities[severity] = alert_severities.get(severity, 0) + 1

        return {
            "total_tables": len(tables),
            "total_alerts": len(alerts),
            "alerts_by_type": alert_types,
            "alerts_by_severity": alert_severities,
        }
    finally:
        store.close()
