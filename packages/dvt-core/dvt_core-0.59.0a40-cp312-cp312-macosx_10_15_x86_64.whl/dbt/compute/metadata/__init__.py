# =============================================================================
# DVT Metadata Layer
# =============================================================================
# Project-level metadata store using DuckDB for:
# - Type registry (adapter types → Spark types)
# - Syntax registry (quoting, case sensitivity per adapter)
# - Metadata snapshot (cached table/column info)
# - Profile results (v0.56.0 - dvt profile)
# - Catalog nodes (v0.56.0 - dvt docs generate)
# - Lineage edges (v0.56.0 - dvt docs generate)
#
# DVT v0.54.0: Initial implementation
# DVT v0.55.0: Added AdaptersRegistry for shipped registry database
# DVT v0.56.0: Added profile_results, catalog_nodes, lineage_edges tables
# =============================================================================

from dbt.compute.metadata.store import (
    ProjectMetadataStore,
    ColumnMetadata,
    TableMetadata,
    RowCountInfo,
    ColumnProfileResult,
    CatalogNode,
    LineageEdge,
)
from dbt.compute.metadata.registry import TypeRegistry, SyntaxRegistry
from dbt.compute.metadata.adapters_registry import AdaptersRegistry

__all__ = [
    "ProjectMetadataStore",
    "ColumnMetadata",
    "TableMetadata",
    "RowCountInfo",
    "ColumnProfileResult",
    "CatalogNode",
    "LineageEdge",
    "TypeRegistry",
    "SyntaxRegistry",
    "AdaptersRegistry",
]
