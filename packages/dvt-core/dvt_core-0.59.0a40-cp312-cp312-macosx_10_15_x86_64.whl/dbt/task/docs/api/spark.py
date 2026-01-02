"""
DVT Docs Serve - Spark Status API

v0.56.0: Basic Spark status for local Spark only.

Note: For external clusters (EMR, Dataproc, Databricks),
use the platform's native monitoring tools.
"""

from pathlib import Path
from typing import Any, Dict, Optional

try:
    from fastapi import APIRouter, HTTPException
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


router = APIRouter(prefix="/api/spark", tags=["spark"])

# Will be set by serve.py
_project_root: Optional[Path] = None
_store_initialized: bool = False


def set_project_root(project_root: Path) -> None:
    """Set project root for API access."""
    global _project_root, _store_initialized
    _project_root = project_root
    _store_initialized = True  # Assume serve.py already initialized


@router.get("/status")
async def get_spark_status() -> Dict[str, Any]:
    """
    Get current Spark status.

    Returns basic status info for local Spark.
    """
    try:
        # Try to detect if Spark is running
        from dbt.config.compute import ComputeRegistry

        registry = ComputeRegistry(_project_root) if _project_root else None
        if not registry:
            return {
                "engine": "unknown",
                "status": "not_configured",
                "message": "Compute registry not available",
            }

        # Get default compute
        default_compute = registry.target_compute
        compute_cluster = registry.get(default_compute)

        if not compute_cluster:
            return {
                "engine": "none",
                "status": "not_configured",
                "message": "No compute engine configured",
            }

        # Check if it's local Spark
        platform = compute_cluster.detect_platform()
        is_local = platform == "local"

        # Try to get Spark session status
        spark_ui_url = None
        spark_running = False

        if is_local:
            try:
                from pyspark.sql import SparkSession

                # Check for existing session (don't create new one)
                existing = SparkSession.getActiveSession()
                if existing:
                    spark_running = True
                    spark_ui_url = existing.sparkContext.uiWebUrl
            except Exception:
                pass

        return {
            "engine": compute_cluster.name,
            "platform": platform,
            "status": "running" if spark_running else "ready",
            "is_local": is_local,
            "spark_ui_url": spark_ui_url,
            "message": "Local Spark ready" if is_local else f"External platform: {platform}",
            "config": {
                "master": compute_cluster.config.get("master", "local[*]") if is_local else None,
                "driver_memory": compute_cluster.config.get("spark.driver.memory"),
                "executor_memory": compute_cluster.config.get("spark.executor.memory"),
            },
        }

    except Exception as e:
        return {
            "engine": "unknown",
            "status": "error",
            "message": f"Could not get Spark status: {str(e)}",
        }


@router.get("/ui-url")
async def get_spark_ui_url() -> Dict[str, Any]:
    """
    Get Spark UI URL if available.

    Only works for local Spark when a session is active.
    """
    try:
        from pyspark.sql import SparkSession

        existing = SparkSession.getActiveSession()
        if existing:
            return {
                "available": True,
                "url": existing.sparkContext.uiWebUrl,
            }
        else:
            return {
                "available": False,
                "url": None,
                "message": "No active Spark session",
            }
    except ImportError:
        return {
            "available": False,
            "url": None,
            "message": "PySpark not installed",
        }
    except Exception as e:
        return {
            "available": False,
            "url": None,
            "message": str(e),
        }


@router.get("/config")
async def get_spark_config() -> Dict[str, Any]:
    """
    Get Spark configuration from computes.yml.

    Returns the configured Spark settings without starting a session.
    """
    try:
        from dbt.config.compute import ComputeRegistry

        registry = ComputeRegistry(_project_root) if _project_root else None
        if not registry:
            raise HTTPException(status_code=500, detail="Compute registry not available")

        # Get all Spark computes
        all_computes = registry.list()
        spark_computes = [c for c in all_computes if c.type == "spark"]

        return {
            "default_compute": registry.target_compute,
            "spark_computes": [
                {
                    "name": c.name,
                    "platform": c.detect_platform(),
                    "config": {
                        "master": c.config.get("master"),
                        "driver_memory": c.config.get("spark.driver.memory"),
                        "executor_memory": c.config.get("spark.executor.memory"),
                        "jars_packages": c.config.get("spark.jars.packages"),
                    },
                }
                for c in spark_computes
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
