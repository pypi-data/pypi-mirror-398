"""
DVT Docs Serve API

v0.56.0: FastAPI routers for enhanced docs serve with 3-tab web UI.

Endpoints:
- /api/catalog/* - Catalog nodes and search
- /api/profile/* - Profile results and alerts
- /api/lineage/* - Lineage graph and traversal
- /api/spark/* - Spark status (local only)
"""

from dbt.task.docs.api.catalog import router as catalog_router
from dbt.task.docs.api.profile import router as profile_router
from dbt.task.docs.api.lineage import router as lineage_router
from dbt.task.docs.api.spark import router as spark_router

__all__ = [
    "catalog_router",
    "profile_router",
    "lineage_router",
    "spark_router",
]
