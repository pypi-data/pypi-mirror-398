# =============================================================================
# DVT Project Metadata Store
# =============================================================================
# DuckDB-based metadata store for DVT projects.
#
# This store contains PROJECT-LEVEL data only:
# - Column metadata (from dvt snap or federated runs)
# - Row counts (from dvt snap only, NOT during every run)
#
# Static registry data (type mappings, syntax rules, adapter queries) comes
# from the shipped adapters_registry.duckdb via AdaptersRegistry class.
#
# Location: <project>/.dvt/metadata_store.duckdb
#
# DVT v0.54.0: Initial implementation
# DVT v0.55.0: Refactored to separate project metadata from shipped registry
# =============================================================================

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False

from dbt.compute.metadata.adapters_registry import (
    AdaptersRegistry,
    TypeMapping,
    SyntaxRule,
    get_registry,
    get_spark_type as registry_get_spark_type,
    get_syntax_rule as registry_get_syntax_rule,
    get_metadata_query as registry_get_metadata_query,
)


@dataclass
class ColumnMetadata:
    """Metadata for a single column."""
    column_name: str
    adapter_type: str
    spark_type: str
    is_nullable: bool
    is_primary_key: bool
    ordinal_position: int


@dataclass
class TableMetadata:
    """Metadata for a table/view (columns only, no row count)."""
    source_name: str
    table_name: str
    adapter_name: str
    connection_name: str
    schema_name: str
    columns: List[ColumnMetadata]
    last_refreshed: datetime


@dataclass
class RowCountInfo:
    """Row count information for a table."""
    source_name: str
    table_name: str
    row_count: int
    last_refreshed: datetime


# =============================================================================
# Profile Results (v0.56.0 - dvt profile command)
# =============================================================================

@dataclass
class ColumnProfileResult:
    """Profile result for a single column."""
    source_name: str
    table_name: str
    column_name: str
    profile_mode: str  # 'minimal', 'explorative', 'sensitive', 'time-series'

    # Basic metrics (all modes)
    row_count: Optional[int] = None
    null_count: Optional[int] = None
    null_percent: Optional[float] = None
    distinct_count: Optional[int] = None
    distinct_percent: Optional[float] = None

    # Numeric metrics (explorative+)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    stddev_value: Optional[float] = None
    p25: Optional[float] = None
    p50: Optional[float] = None
    p75: Optional[float] = None

    # String metrics (explorative+)
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    avg_length: Optional[float] = None

    # Distribution data (JSON strings)
    histogram: Optional[str] = None  # JSON: bucket counts
    top_values: Optional[str] = None  # JSON: top N values with counts

    # Quality alerts (JSON string)
    alerts: Optional[str] = None  # JSON: [{type, severity, message}]

    # Metadata
    profiled_at: Optional[datetime] = None
    duration_ms: Optional[int] = None


# =============================================================================
# Catalog Nodes (v0.56.0 - dvt docs generate enhancement)
# =============================================================================

@dataclass
class CatalogNode:
    """Enriched catalog node for dvt docs generate."""
    unique_id: str
    resource_type: str  # 'model', 'source', 'test', 'seed', 'snapshot'
    name: str
    schema_name: Optional[str] = None
    database: Optional[str] = None

    # Connection info
    connection_name: Optional[str] = None
    adapter_type: Optional[str] = None

    # Documentation
    description: Optional[str] = None

    # Visual enrichment
    icon_type: Optional[str] = None  # 'postgres', 'snowflake', 'spark', etc.
    color_hex: Optional[str] = None  # Connection color

    # Config
    materialized: Optional[str] = None
    tags: Optional[str] = None  # JSON array
    meta: Optional[str] = None  # JSON object

    # Columns (JSON array)
    columns: Optional[str] = None

    # Statistics
    row_count: Optional[int] = None
    bytes_stored: Optional[int] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# Lineage Edges (v0.56.0 - dvt docs generate enhancement)
# =============================================================================

@dataclass
class LineageEdge:
    """Lineage edge representing a dependency between nodes."""
    id: Optional[int] = None
    source_node_id: str = ""
    target_node_id: str = ""
    edge_type: str = ""  # 'ref', 'source', 'depends_on'

    # Cross-connection indicator
    is_cross_connection: bool = False
    source_connection: Optional[str] = None
    target_connection: Optional[str] = None


class ProjectMetadataStore:
    """
    DuckDB-based metadata store for a DVT project.

    Location: <project_root>/.dvt/metadata_store.duckdb

    Tables (project-level data only):
    - column_metadata: source_name, table_name, column_name, adapter_type, spark_type, ...
    - row_counts: source_name, table_name, row_count, last_refreshed

    NOTE: Static registry data (type mappings, syntax rules, adapter queries)
    comes from the shipped adapters_registry.duckdb via AdaptersRegistry class.
    """

    DVT_DIR = ".dvt"
    METADATA_DB = "metadata_store.duckdb"

    def __init__(self, project_root: Path):
        """
        Initialize the metadata store.

        Args:
            project_root: Path to the DVT project root directory
        """
        if not HAS_DUCKDB:
            raise ImportError(
                "DuckDB is required for metadata store. "
                "Install with: pip install duckdb"
            )

        self.project_root = Path(project_root)
        self.dvt_dir = self.project_root / self.DVT_DIR
        self.db_path = self.dvt_dir / self.METADATA_DB
        self._conn: Optional[duckdb.DuckDBPyConnection] = None
        self._registry: Optional[AdaptersRegistry] = None

    @property
    def conn(self) -> "duckdb.DuckDBPyConnection":
        """Get or create database connection."""
        if self._conn is None:
            self._conn = duckdb.connect(str(self.db_path))
        return self._conn

    @property
    def registry(self) -> AdaptersRegistry:
        """Get the shipped adapters registry (singleton)."""
        if self._registry is None:
            self._registry = get_registry()
        return self._registry

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "ProjectMetadataStore":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # =========================================================================
    # Initialization
    # =========================================================================

    def initialize(self) -> None:
        """
        Initialize the metadata store.

        Creates:
        1. .dvt/ directory if it doesn't exist
        2. metadata_store.duckdb database
        3. Schema tables (column_metadata, row_counts)

        NOTE: No registry data is loaded - that comes from shipped DuckDB.
        """
        # Create .dvt/ directory
        self.dvt_dir.mkdir(parents=True, exist_ok=True)

        # Create schema tables
        self._create_schema()

    def _create_schema(self) -> None:
        """Create the database schema tables."""

        # Column metadata table (populated by dvt snap or federated runs)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS column_metadata (
                source_name VARCHAR NOT NULL,
                table_name VARCHAR NOT NULL,
                column_name VARCHAR NOT NULL,
                adapter_name VARCHAR NOT NULL,
                connection_name VARCHAR NOT NULL,
                schema_name VARCHAR,
                adapter_type VARCHAR NOT NULL,
                spark_type VARCHAR NOT NULL,
                is_nullable BOOLEAN DEFAULT TRUE,
                is_primary_key BOOLEAN DEFAULT FALSE,
                ordinal_position INTEGER,
                last_refreshed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(source_name, table_name, column_name)
            )
        """)

        # Row counts table (ONLY populated by dvt snap, not during runs)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS row_counts (
                source_name VARCHAR NOT NULL,
                table_name VARCHAR NOT NULL,
                row_count BIGINT,
                last_refreshed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(source_name, table_name)
            )
        """)

        # =====================================================================
        # v0.56.0: Profile Results (dvt profile command)
        # =====================================================================
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS profile_results (
                source_name VARCHAR NOT NULL,
                table_name VARCHAR NOT NULL,
                column_name VARCHAR NOT NULL,
                profile_mode VARCHAR NOT NULL,

                -- Basic metrics (all modes)
                row_count BIGINT,
                null_count BIGINT,
                null_percent DOUBLE,
                distinct_count BIGINT,
                distinct_percent DOUBLE,

                -- Numeric metrics (explorative+)
                min_value DOUBLE,
                max_value DOUBLE,
                mean_value DOUBLE,
                median_value DOUBLE,
                stddev_value DOUBLE,
                p25 DOUBLE,
                p50 DOUBLE,
                p75 DOUBLE,

                -- String metrics (explorative+)
                min_length INTEGER,
                max_length INTEGER,
                avg_length DOUBLE,

                -- Distribution data (JSON)
                histogram JSON,
                top_values JSON,

                -- Quality alerts
                alerts JSON,

                -- Metadata
                profiled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                duration_ms INTEGER,

                PRIMARY KEY(source_name, table_name, column_name, profile_mode)
            )
        """)

        # =====================================================================
        # v0.56.0: Catalog Nodes (dvt docs generate enhancement)
        # =====================================================================
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS catalog_nodes (
                unique_id VARCHAR PRIMARY KEY,
                resource_type VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                schema_name VARCHAR,
                database VARCHAR,

                -- Connection info
                connection_name VARCHAR,
                adapter_type VARCHAR,

                -- Documentation
                description TEXT,

                -- Visual enrichment
                icon_type VARCHAR,
                color_hex VARCHAR,

                -- Config
                materialized VARCHAR,
                tags JSON,
                meta JSON,

                -- Columns (JSON array)
                columns JSON,

                -- Statistics
                row_count BIGINT,
                bytes_stored BIGINT,

                -- Timestamps
                created_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # =====================================================================
        # v0.56.0: Lineage Edges (dvt docs generate enhancement)
        # =====================================================================
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS lineage_edges (
                id INTEGER PRIMARY KEY,
                source_node_id VARCHAR NOT NULL,
                target_node_id VARCHAR NOT NULL,
                edge_type VARCHAR NOT NULL,

                -- Cross-connection indicator
                is_cross_connection BOOLEAN DEFAULT FALSE,
                source_connection VARCHAR,
                target_connection VARCHAR
            )
        """)

        # Create indexes for fast lookups
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_column_metadata_source
            ON column_metadata(source_name, table_name)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_column_metadata_adapter
            ON column_metadata(adapter_name)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_row_counts_source
            ON row_counts(source_name)
        """)

        # v0.56.0: New indexes for profile, catalog, and lineage
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_profile_results_table
            ON profile_results(source_name, table_name)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_catalog_nodes_type
            ON catalog_nodes(resource_type)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_lineage_edges_source
            ON lineage_edges(source_node_id)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_lineage_edges_target
            ON lineage_edges(target_node_id)
        """)

    # =========================================================================
    # Type Registry Queries (delegated to shipped AdaptersRegistry)
    # =========================================================================

    def get_spark_type(
        self,
        adapter_name: str,
        adapter_type: str,
        spark_version: str = "all"
    ) -> Optional[str]:
        """
        Look up the Spark type for an adapter type.

        Delegates to the shipped AdaptersRegistry.

        Args:
            adapter_name: Name of the adapter (e.g., 'postgres', 'snowflake')
            adapter_type: Native adapter type (e.g., 'VARCHAR', 'INTEGER')
            spark_version: Target Spark version (default: 'all')

        Returns:
            Spark type string or None if not found
        """
        mapping = self.registry.get_spark_type(adapter_name, adapter_type, spark_version)
        return mapping.spark_type if mapping else None

    def get_type_mappings(
        self,
        adapter_name: str,
        spark_version: str = "all"
    ) -> List[Tuple[str, str]]:
        """
        Get all type mappings for an adapter.

        Delegates to the shipped AdaptersRegistry.

        Returns:
            List of (adapter_type, spark_type) tuples
        """
        mappings = self.registry.get_all_mappings_for_adapter(adapter_name)
        return [(m.adapter_type, m.spark_type) for m in mappings]

    # =========================================================================
    # Syntax Registry Queries (delegated to shipped AdaptersRegistry)
    # =========================================================================

    def get_syntax_rule(self, adapter_name: str) -> Optional[SyntaxRule]:
        """
        Get syntax rules for an adapter.

        Delegates to the shipped AdaptersRegistry.

        Args:
            adapter_name: Name of the adapter

        Returns:
            SyntaxRule or None if not found
        """
        return self.registry.get_syntax_rule(adapter_name)

    def quote_identifier(self, adapter_name: str, identifier: str) -> str:
        """Quote an identifier for the given adapter."""
        return self.registry.quote_identifier(adapter_name, identifier)

    # =========================================================================
    # Adapter Metadata Queries (delegated to shipped AdaptersRegistry)
    # =========================================================================

    def get_metadata_query(
        self,
        adapter_name: str,
        query_type: str
    ) -> Optional[str]:
        """
        Get the metadata query template for an adapter.

        Delegates to the shipped AdaptersRegistry.

        Args:
            adapter_name: Name of the adapter
            query_type: Type of query ('columns', 'tables', 'row_count', 'primary_key')

        Returns:
            Query template string or None if not found
        """
        query = self.registry.get_metadata_query(adapter_name, query_type)
        return query.query_template if query else None

    # =========================================================================
    # Column Metadata Operations
    # =========================================================================

    def save_table_metadata(self, metadata: TableMetadata) -> None:
        """
        Save table column metadata to the store.

        This is called during federated execution to capture schema info.

        Args:
            metadata: TableMetadata object with column info
        """
        # Delete existing entries for this table
        self.conn.execute("""
            DELETE FROM column_metadata
            WHERE source_name = ? AND table_name = ?
        """, [metadata.source_name, metadata.table_name])

        # Insert new entries
        for col in metadata.columns:
            self.conn.execute("""
                INSERT INTO column_metadata
                (source_name, table_name, column_name, adapter_name, connection_name,
                 schema_name, adapter_type, spark_type, is_nullable, is_primary_key,
                 ordinal_position, last_refreshed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                metadata.source_name,
                metadata.table_name,
                col.column_name,
                metadata.adapter_name,
                metadata.connection_name,
                metadata.schema_name,
                col.adapter_type,
                col.spark_type,
                col.is_nullable,
                col.is_primary_key,
                col.ordinal_position,
                metadata.last_refreshed
            ])

    def get_table_metadata(
        self,
        source_name: str,
        table_name: str
    ) -> Optional[TableMetadata]:
        """
        Get cached column metadata for a table.

        Args:
            source_name: Name of the source
            table_name: Name of the table

        Returns:
            TableMetadata or None if not cached
        """
        results = self.conn.execute("""
            SELECT
                source_name, table_name, column_name, adapter_name, connection_name,
                schema_name, adapter_type, spark_type, is_nullable, is_primary_key,
                ordinal_position, last_refreshed
            FROM column_metadata
            WHERE source_name = ? AND table_name = ?
            ORDER BY ordinal_position
        """, [source_name, table_name]).fetchall()

        if not results:
            return None

        # Build column list
        columns = []
        for r in results:
            columns.append(ColumnMetadata(
                column_name=r[2],
                adapter_type=r[6],
                spark_type=r[7],
                is_nullable=r[8],
                is_primary_key=r[9],
                ordinal_position=r[10]
            ))

        # Build TableMetadata from first row
        first = results[0]
        return TableMetadata(
            source_name=first[0],
            table_name=first[1],
            adapter_name=first[3],
            connection_name=first[4],
            schema_name=first[5],
            columns=columns,
            last_refreshed=first[11]
        )

    def get_all_sources(self) -> List[Tuple[str, str]]:
        """
        Get all source/table combinations in the store.

        Returns:
            List of (source_name, table_name) tuples
        """
        results = self.conn.execute("""
            SELECT DISTINCT source_name, table_name
            FROM column_metadata
            ORDER BY source_name, table_name
        """).fetchall()

        return [(r[0], r[1]) for r in results]

    def clear_column_metadata(self) -> None:
        """Clear all column metadata."""
        self.conn.execute("DELETE FROM column_metadata")

    # =========================================================================
    # Row Count Operations (dvt snap only)
    # =========================================================================

    def save_row_count(
        self,
        source_name: str,
        table_name: str,
        row_count: int,
        last_refreshed: Optional[datetime] = None
    ) -> None:
        """
        Save row count for a table.

        This is ONLY called by dvt snap, not during regular runs.

        Args:
            source_name: Name of the source
            table_name: Name of the table
            row_count: Number of rows
            last_refreshed: Timestamp (defaults to now)
        """
        if last_refreshed is None:
            last_refreshed = datetime.now()

        self.conn.execute("""
            INSERT OR REPLACE INTO row_counts
            (source_name, table_name, row_count, last_refreshed)
            VALUES (?, ?, ?, ?)
        """, [source_name, table_name, row_count, last_refreshed])

    def get_row_count(self, source_name: str, table_name: str) -> Optional[RowCountInfo]:
        """
        Get cached row count for a table.

        Args:
            source_name: Name of the source
            table_name: Name of the table

        Returns:
            RowCountInfo or None if not cached
        """
        result = self.conn.execute("""
            SELECT source_name, table_name, row_count, last_refreshed
            FROM row_counts
            WHERE source_name = ? AND table_name = ?
        """, [source_name, table_name]).fetchone()

        if result:
            return RowCountInfo(
                source_name=result[0],
                table_name=result[1],
                row_count=result[2],
                last_refreshed=result[3]
            )
        return None

    def get_all_row_counts(self) -> List[RowCountInfo]:
        """
        Get all cached row counts.

        Returns:
            List of RowCountInfo objects
        """
        results = self.conn.execute("""
            SELECT source_name, table_name, row_count, last_refreshed
            FROM row_counts
            ORDER BY source_name, table_name
        """).fetchall()

        return [
            RowCountInfo(
                source_name=r[0],
                table_name=r[1],
                row_count=r[2],
                last_refreshed=r[3]
            )
            for r in results
        ]

    def clear_row_counts(self) -> None:
        """Clear all row count data."""
        self.conn.execute("DELETE FROM row_counts")

    def clear_snapshot(self) -> None:
        """Clear all snapshot data (both column metadata and row counts)."""
        self.clear_column_metadata()
        self.clear_row_counts()

    def clear_all_metadata(self) -> None:
        """Clear ALL metadata from the store (columns, row counts, profiles)."""
        self.clear_column_metadata()
        self.clear_row_counts()
        self.clear_profile_results()
        # Note: catalog_nodes and lineage_edges are not cleared here
        # as they're managed by dvt docs generate

    def has_source_metadata(self) -> bool:
        """
        Check if there is any source metadata in the store.

        Used to determine if this is the first run (auto-snapshot needed).

        Returns:
            True if source metadata exists, False otherwise
        """
        result = self.conn.execute("""
            SELECT COUNT(*) FROM column_metadata
            WHERE source_name NOT LIKE 'model:%'
        """).fetchone()[0]
        return result > 0

    def has_any_metadata(self) -> bool:
        """
        Check if there is any metadata (sources or models) in the store.

        Returns:
            True if any metadata exists, False otherwise
        """
        result = self.conn.execute(
            "SELECT COUNT(*) FROM column_metadata"
        ).fetchone()[0]
        return result > 0

    # =========================================================================
    # Legacy Compatibility - save_table_metadata with row_count
    # =========================================================================

    def save_table_metadata_with_row_count(
        self,
        source_name: str,
        table_name: str,
        adapter_name: str,
        connection_name: str,
        schema_name: str,
        columns: List[ColumnMetadata],
        row_count: Optional[int],
        last_refreshed: datetime
    ) -> None:
        """
        Save both column metadata and row count (used by dvt snap).

        Args:
            source_name: Name of the source
            table_name: Name of the table
            adapter_name: Name of the adapter
            connection_name: Name of the connection
            schema_name: Schema name
            columns: List of ColumnMetadata
            row_count: Number of rows (or None)
            last_refreshed: Timestamp
        """
        # Save column metadata
        metadata = TableMetadata(
            source_name=source_name,
            table_name=table_name,
            adapter_name=adapter_name,
            connection_name=connection_name,
            schema_name=schema_name,
            columns=columns,
            last_refreshed=last_refreshed
        )
        self.save_table_metadata(metadata)

        # Save row count separately (only if provided)
        if row_count is not None:
            self.save_row_count(source_name, table_name, row_count, last_refreshed)

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def exists(self) -> bool:
        """Check if the metadata store exists."""
        return self.db_path.exists()

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the metadata store."""
        # Count column metadata
        tables_count = self.conn.execute(
            "SELECT COUNT(DISTINCT source_name || '.' || table_name) FROM column_metadata"
        ).fetchone()[0]

        columns_count = self.conn.execute(
            "SELECT COUNT(*) FROM column_metadata"
        ).fetchone()[0]

        # Count row counts
        row_counts_count = self.conn.execute(
            "SELECT COUNT(*) FROM row_counts"
        ).fetchone()[0]

        # Get registry stats
        registry = self.registry
        adapters = registry.get_supported_adapters()

        return {
            "metadata_tables": tables_count,
            "metadata_columns": columns_count,
            "row_counts_cached": row_counts_count,
            "registry_adapters": len(adapters),
            "supported_adapters": adapters,
            "db_path": str(self.db_path),
        }

    def migrate_from_legacy(self) -> bool:
        """
        Migrate from legacy metadata.duckdb format to new format.

        Returns:
            True if migration was performed, False if not needed
        """
        legacy_path = self.dvt_dir / "metadata.duckdb"
        if not legacy_path.exists():
            return False

        # Check if new store already exists
        if self.db_path.exists():
            return False

        try:
            # Connect to legacy database
            legacy_conn = duckdb.connect(str(legacy_path), read_only=True)

            # Check if metadata_snapshot table exists
            result = legacy_conn.execute("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_name = 'metadata_snapshot'
            """).fetchone()[0]

            if result == 0:
                legacy_conn.close()
                return False

            # Initialize new store
            self.initialize()

            # Migrate metadata_snapshot to column_metadata
            rows = legacy_conn.execute("""
                SELECT DISTINCT
                    source_name, table_name, column_name, adapter_name, connection_name,
                    schema_name, adapter_type, spark_type, is_nullable, is_primary_key,
                    ordinal_position, last_refreshed
                FROM metadata_snapshot
            """).fetchall()

            for row in rows:
                self.conn.execute("""
                    INSERT OR REPLACE INTO column_metadata
                    (source_name, table_name, column_name, adapter_name, connection_name,
                     schema_name, adapter_type, spark_type, is_nullable, is_primary_key,
                     ordinal_position, last_refreshed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, list(row))

            # Migrate row_count data (distinct per table)
            row_count_rows = legacy_conn.execute("""
                SELECT DISTINCT source_name, table_name, row_count, MAX(last_refreshed)
                FROM metadata_snapshot
                WHERE row_count IS NOT NULL
                GROUP BY source_name, table_name, row_count
            """).fetchall()

            for row in row_count_rows:
                if row[2] is not None:  # row_count
                    self.conn.execute("""
                        INSERT OR REPLACE INTO row_counts
                        (source_name, table_name, row_count, last_refreshed)
                        VALUES (?, ?, ?, ?)
                    """, list(row))

            legacy_conn.close()
            return True

        except Exception as e:
            print(f"[DVT] Warning: Migration failed: {e}")
            return False

    # =========================================================================
    # Profile Results Operations (v0.56.0 - dvt profile command)
    # =========================================================================

    def save_profile_result(self, result: ColumnProfileResult) -> None:
        """
        Save a column profile result to the store.

        Args:
            result: ColumnProfileResult object
        """
        self.conn.execute("""
            INSERT OR REPLACE INTO profile_results
            (source_name, table_name, column_name, profile_mode,
             row_count, null_count, null_percent, distinct_count, distinct_percent,
             min_value, max_value, mean_value, median_value, stddev_value,
             p25, p50, p75, min_length, max_length, avg_length,
             histogram, top_values, alerts, profiled_at, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            result.source_name, result.table_name, result.column_name, result.profile_mode,
            result.row_count, result.null_count, result.null_percent,
            result.distinct_count, result.distinct_percent,
            result.min_value, result.max_value, result.mean_value,
            result.median_value, result.stddev_value,
            result.p25, result.p50, result.p75,
            result.min_length, result.max_length, result.avg_length,
            result.histogram, result.top_values, result.alerts,
            result.profiled_at or datetime.now(), result.duration_ms
        ])

    def save_profile_results_batch(self, results: List[ColumnProfileResult]) -> None:
        """
        Save multiple profile results in a batch.

        Args:
            results: List of ColumnProfileResult objects
        """
        for result in results:
            self.save_profile_result(result)

    def get_profile_result(
        self,
        source_name: str,
        table_name: str,
        column_name: str,
        profile_mode: str
    ) -> Optional[ColumnProfileResult]:
        """
        Get a profile result for a specific column.

        Args:
            source_name: Name of the source
            table_name: Name of the table
            column_name: Name of the column
            profile_mode: Profile mode ('minimal', 'explorative', etc.)

        Returns:
            ColumnProfileResult or None if not found
        """
        result = self.conn.execute("""
            SELECT source_name, table_name, column_name, profile_mode,
                   row_count, null_count, null_percent, distinct_count, distinct_percent,
                   min_value, max_value, mean_value, median_value, stddev_value,
                   p25, p50, p75, min_length, max_length, avg_length,
                   histogram, top_values, alerts, profiled_at, duration_ms
            FROM profile_results
            WHERE source_name = ? AND table_name = ? AND column_name = ? AND profile_mode = ?
        """, [source_name, table_name, column_name, profile_mode]).fetchone()

        if result:
            return ColumnProfileResult(
                source_name=result[0], table_name=result[1],
                column_name=result[2], profile_mode=result[3],
                row_count=result[4], null_count=result[5], null_percent=result[6],
                distinct_count=result[7], distinct_percent=result[8],
                min_value=result[9], max_value=result[10], mean_value=result[11],
                median_value=result[12], stddev_value=result[13],
                p25=result[14], p50=result[15], p75=result[16],
                min_length=result[17], max_length=result[18], avg_length=result[19],
                histogram=result[20], top_values=result[21], alerts=result[22],
                profiled_at=result[23], duration_ms=result[24]
            )
        return None

    def get_table_profile(
        self,
        source_name: str,
        table_name: str,
        profile_mode: Optional[str] = None
    ) -> List[ColumnProfileResult]:
        """
        Get all profile results for a table.

        Args:
            source_name: Name of the source
            table_name: Name of the table
            profile_mode: Optional mode filter

        Returns:
            List of ColumnProfileResult objects
        """
        if profile_mode:
            results = self.conn.execute("""
                SELECT source_name, table_name, column_name, profile_mode,
                       row_count, null_count, null_percent, distinct_count, distinct_percent,
                       min_value, max_value, mean_value, median_value, stddev_value,
                       p25, p50, p75, min_length, max_length, avg_length,
                       histogram, top_values, alerts, profiled_at, duration_ms
                FROM profile_results
                WHERE source_name = ? AND table_name = ? AND profile_mode = ?
                ORDER BY column_name
            """, [source_name, table_name, profile_mode]).fetchall()
        else:
            results = self.conn.execute("""
                SELECT source_name, table_name, column_name, profile_mode,
                       row_count, null_count, null_percent, distinct_count, distinct_percent,
                       min_value, max_value, mean_value, median_value, stddev_value,
                       p25, p50, p75, min_length, max_length, avg_length,
                       histogram, top_values, alerts, profiled_at, duration_ms
                FROM profile_results
                WHERE source_name = ? AND table_name = ?
                ORDER BY column_name
            """, [source_name, table_name]).fetchall()

        return [
            ColumnProfileResult(
                source_name=r[0], table_name=r[1], column_name=r[2], profile_mode=r[3],
                row_count=r[4], null_count=r[5], null_percent=r[6],
                distinct_count=r[7], distinct_percent=r[8],
                min_value=r[9], max_value=r[10], mean_value=r[11],
                median_value=r[12], stddev_value=r[13],
                p25=r[14], p50=r[15], p75=r[16],
                min_length=r[17], max_length=r[18], avg_length=r[19],
                histogram=r[20], top_values=r[21], alerts=r[22],
                profiled_at=r[23], duration_ms=r[24]
            )
            for r in results
        ]

    def get_all_profiled_tables(self) -> List[Tuple[str, str, str, datetime]]:
        """
        Get all profiled tables with their latest profile timestamp.

        Returns:
            List of (source_name, table_name, profile_mode, profiled_at) tuples
        """
        results = self.conn.execute("""
            SELECT source_name, table_name, profile_mode, MAX(profiled_at) as last_profiled
            FROM profile_results
            GROUP BY source_name, table_name, profile_mode
            ORDER BY source_name, table_name
        """).fetchall()

        return [(r[0], r[1], r[2], r[3]) for r in results]

    def get_profile_alerts(self, source_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all profile alerts, optionally filtered by source.

        Args:
            source_name: Optional source filter

        Returns:
            List of alert dicts with source/table/column info
        """
        import json

        if source_name:
            results = self.conn.execute("""
                SELECT source_name, table_name, column_name, alerts
                FROM profile_results
                WHERE source_name = ? AND alerts IS NOT NULL
            """, [source_name]).fetchall()
        else:
            results = self.conn.execute("""
                SELECT source_name, table_name, column_name, alerts
                FROM profile_results
                WHERE alerts IS NOT NULL
            """).fetchall()

        all_alerts = []
        for r in results:
            try:
                alerts = json.loads(r[3]) if r[3] else []
                for alert in alerts:
                    alert["source_name"] = r[0]
                    alert["table_name"] = r[1]
                    alert["column_name"] = r[2]
                    all_alerts.append(alert)
            except json.JSONDecodeError:
                pass

        return all_alerts

    def clear_profile_results(self, source_name: Optional[str] = None) -> None:
        """
        Clear profile results, optionally for a specific source.

        Args:
            source_name: Optional source filter
        """
        if source_name:
            self.conn.execute("DELETE FROM profile_results WHERE source_name = ?", [source_name])
        else:
            self.conn.execute("DELETE FROM profile_results")

    # =========================================================================
    # Catalog Node Operations (v0.56.0 - dvt docs generate enhancement)
    # =========================================================================

    def save_catalog_node(self, node: CatalogNode) -> None:
        """
        Save a catalog node to the store.

        Args:
            node: CatalogNode object
        """
        self.conn.execute("""
            INSERT OR REPLACE INTO catalog_nodes
            (unique_id, resource_type, name, schema_name, database,
             connection_name, adapter_type, description, icon_type, color_hex,
             materialized, tags, meta, columns, row_count, bytes_stored,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            node.unique_id, node.resource_type, node.name,
            node.schema_name, node.database,
            node.connection_name, node.adapter_type,
            node.description, node.icon_type, node.color_hex,
            node.materialized, node.tags, node.meta, node.columns,
            node.row_count, node.bytes_stored,
            node.created_at, node.updated_at or datetime.now()
        ])

    def save_catalog_nodes_batch(self, nodes: List[CatalogNode]) -> None:
        """
        Save multiple catalog nodes in a batch.

        Args:
            nodes: List of CatalogNode objects
        """
        for node in nodes:
            self.save_catalog_node(node)

    def get_catalog_node(self, unique_id: str) -> Optional[CatalogNode]:
        """
        Get a catalog node by unique ID.

        Args:
            unique_id: Unique node ID

        Returns:
            CatalogNode or None if not found
        """
        result = self.conn.execute("""
            SELECT unique_id, resource_type, name, schema_name, database,
                   connection_name, adapter_type, description, icon_type, color_hex,
                   materialized, tags, meta, columns, row_count, bytes_stored,
                   created_at, updated_at
            FROM catalog_nodes
            WHERE unique_id = ?
        """, [unique_id]).fetchone()

        if result:
            return CatalogNode(
                unique_id=result[0], resource_type=result[1], name=result[2],
                schema_name=result[3], database=result[4],
                connection_name=result[5], adapter_type=result[6],
                description=result[7], icon_type=result[8], color_hex=result[9],
                materialized=result[10], tags=result[11], meta=result[12],
                columns=result[13], row_count=result[14], bytes_stored=result[15],
                created_at=result[16], updated_at=result[17]
            )
        return None

    def get_catalog_nodes_by_type(self, resource_type: str) -> List[CatalogNode]:
        """
        Get all catalog nodes of a specific type.

        Args:
            resource_type: Type filter ('model', 'source', etc.)

        Returns:
            List of CatalogNode objects
        """
        results = self.conn.execute("""
            SELECT unique_id, resource_type, name, schema_name, database,
                   connection_name, adapter_type, description, icon_type, color_hex,
                   materialized, tags, meta, columns, row_count, bytes_stored,
                   created_at, updated_at
            FROM catalog_nodes
            WHERE resource_type = ?
            ORDER BY name
        """, [resource_type]).fetchall()

        return [
            CatalogNode(
                unique_id=r[0], resource_type=r[1], name=r[2],
                schema_name=r[3], database=r[4],
                connection_name=r[5], adapter_type=r[6],
                description=r[7], icon_type=r[8], color_hex=r[9],
                materialized=r[10], tags=r[11], meta=r[12],
                columns=r[13], row_count=r[14], bytes_stored=r[15],
                created_at=r[16], updated_at=r[17]
            )
            for r in results
        ]

    def get_all_catalog_nodes(self) -> List[CatalogNode]:
        """
        Get all catalog nodes.

        Returns:
            List of CatalogNode objects
        """
        results = self.conn.execute("""
            SELECT unique_id, resource_type, name, schema_name, database,
                   connection_name, adapter_type, description, icon_type, color_hex,
                   materialized, tags, meta, columns, row_count, bytes_stored,
                   created_at, updated_at
            FROM catalog_nodes
            ORDER BY resource_type, name
        """).fetchall()

        return [
            CatalogNode(
                unique_id=r[0], resource_type=r[1], name=r[2],
                schema_name=r[3], database=r[4],
                connection_name=r[5], adapter_type=r[6],
                description=r[7], icon_type=r[8], color_hex=r[9],
                materialized=r[10], tags=r[11], meta=r[12],
                columns=r[13], row_count=r[14], bytes_stored=r[15],
                created_at=r[16], updated_at=r[17]
            )
            for r in results
        ]

    def search_catalog_nodes(self, query: str) -> List[CatalogNode]:
        """
        Search catalog nodes by name or description.

        Args:
            query: Search query string

        Returns:
            List of matching CatalogNode objects
        """
        search_pattern = f"%{query}%"
        results = self.conn.execute("""
            SELECT unique_id, resource_type, name, schema_name, database,
                   connection_name, adapter_type, description, icon_type, color_hex,
                   materialized, tags, meta, columns, row_count, bytes_stored,
                   created_at, updated_at
            FROM catalog_nodes
            WHERE name ILIKE ? OR description ILIKE ? OR unique_id ILIKE ?
            ORDER BY resource_type, name
        """, [search_pattern, search_pattern, search_pattern]).fetchall()

        return [
            CatalogNode(
                unique_id=r[0], resource_type=r[1], name=r[2],
                schema_name=r[3], database=r[4],
                connection_name=r[5], adapter_type=r[6],
                description=r[7], icon_type=r[8], color_hex=r[9],
                materialized=r[10], tags=r[11], meta=r[12],
                columns=r[13], row_count=r[14], bytes_stored=r[15],
                created_at=r[16], updated_at=r[17]
            )
            for r in results
        ]

    def clear_catalog_nodes(self) -> None:
        """Clear all catalog nodes."""
        self.conn.execute("DELETE FROM catalog_nodes")

    # =========================================================================
    # Lineage Edge Operations (v0.56.0 - dvt docs generate enhancement)
    # =========================================================================

    def save_lineage_edge(self, edge: LineageEdge) -> int:
        """
        Save a lineage edge to the store.

        Args:
            edge: LineageEdge object

        Returns:
            ID of the inserted edge
        """
        if edge.id:
            self.conn.execute("""
                INSERT OR REPLACE INTO lineage_edges
                (id, source_node_id, target_node_id, edge_type,
                 is_cross_connection, source_connection, target_connection)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                edge.id, edge.source_node_id, edge.target_node_id, edge.edge_type,
                edge.is_cross_connection, edge.source_connection, edge.target_connection
            ])
            return edge.id
        else:
            result = self.conn.execute("""
                INSERT INTO lineage_edges
                (source_node_id, target_node_id, edge_type,
                 is_cross_connection, source_connection, target_connection)
                VALUES (?, ?, ?, ?, ?, ?)
                RETURNING id
            """, [
                edge.source_node_id, edge.target_node_id, edge.edge_type,
                edge.is_cross_connection, edge.source_connection, edge.target_connection
            ]).fetchone()
            return result[0]

    def save_lineage_edges_batch(self, edges: List[LineageEdge]) -> None:
        """
        Save multiple lineage edges in a batch.

        Args:
            edges: List of LineageEdge objects
        """
        for edge in edges:
            self.save_lineage_edge(edge)

    def get_lineage_edge(self, edge_id: int) -> Optional[LineageEdge]:
        """
        Get a lineage edge by ID.

        Args:
            edge_id: Edge ID

        Returns:
            LineageEdge or None if not found
        """
        result = self.conn.execute("""
            SELECT id, source_node_id, target_node_id, edge_type,
                   is_cross_connection, source_connection, target_connection
            FROM lineage_edges
            WHERE id = ?
        """, [edge_id]).fetchone()

        if result:
            return LineageEdge(
                id=result[0], source_node_id=result[1], target_node_id=result[2],
                edge_type=result[3], is_cross_connection=result[4],
                source_connection=result[5], target_connection=result[6]
            )
        return None

    def get_upstream_edges(self, node_id: str) -> List[LineageEdge]:
        """
        Get all edges where this node is the target (upstream dependencies).

        Args:
            node_id: Node unique ID

        Returns:
            List of LineageEdge objects
        """
        results = self.conn.execute("""
            SELECT id, source_node_id, target_node_id, edge_type,
                   is_cross_connection, source_connection, target_connection
            FROM lineage_edges
            WHERE target_node_id = ?
        """, [node_id]).fetchall()

        return [
            LineageEdge(
                id=r[0], source_node_id=r[1], target_node_id=r[2],
                edge_type=r[3], is_cross_connection=r[4],
                source_connection=r[5], target_connection=r[6]
            )
            for r in results
        ]

    def get_downstream_edges(self, node_id: str) -> List[LineageEdge]:
        """
        Get all edges where this node is the source (downstream dependents).

        Args:
            node_id: Node unique ID

        Returns:
            List of LineageEdge objects
        """
        results = self.conn.execute("""
            SELECT id, source_node_id, target_node_id, edge_type,
                   is_cross_connection, source_connection, target_connection
            FROM lineage_edges
            WHERE source_node_id = ?
        """, [node_id]).fetchall()

        return [
            LineageEdge(
                id=r[0], source_node_id=r[1], target_node_id=r[2],
                edge_type=r[3], is_cross_connection=r[4],
                source_connection=r[5], target_connection=r[6]
            )
            for r in results
        ]

    def get_all_lineage_edges(self) -> List[LineageEdge]:
        """
        Get all lineage edges.

        Returns:
            List of LineageEdge objects
        """
        results = self.conn.execute("""
            SELECT id, source_node_id, target_node_id, edge_type,
                   is_cross_connection, source_connection, target_connection
            FROM lineage_edges
            ORDER BY source_node_id, target_node_id
        """).fetchall()

        return [
            LineageEdge(
                id=r[0], source_node_id=r[1], target_node_id=r[2],
                edge_type=r[3], is_cross_connection=r[4],
                source_connection=r[5], target_connection=r[6]
            )
            for r in results
        ]

    def get_cross_connection_edges(self) -> List[LineageEdge]:
        """
        Get all edges that cross connection boundaries.

        Returns:
            List of cross-connection LineageEdge objects
        """
        results = self.conn.execute("""
            SELECT id, source_node_id, target_node_id, edge_type,
                   is_cross_connection, source_connection, target_connection
            FROM lineage_edges
            WHERE is_cross_connection = TRUE
            ORDER BY source_node_id, target_node_id
        """).fetchall()

        return [
            LineageEdge(
                id=r[0], source_node_id=r[1], target_node_id=r[2],
                edge_type=r[3], is_cross_connection=r[4],
                source_connection=r[5], target_connection=r[6]
            )
            for r in results
        ]

    def get_lineage_graph(self) -> Dict[str, Any]:
        """
        Get the full lineage graph as a dict suitable for visualization.

        Returns:
            Dict with 'nodes' and 'edges' keys
        """
        nodes = self.get_all_catalog_nodes()
        edges = self.get_all_lineage_edges()

        return {
            "nodes": [
                {
                    "id": n.unique_id,
                    "type": n.resource_type,
                    "name": n.name,
                    "connection": n.connection_name,
                    "adapter": n.adapter_type,
                    "icon": n.icon_type,
                    "color": n.color_hex,
                }
                for n in nodes
            ],
            "edges": [
                {
                    "source": e.source_node_id,
                    "target": e.target_node_id,
                    "type": e.edge_type,
                    "cross_connection": e.is_cross_connection,
                }
                for e in edges
            ],
        }

    def clear_lineage_edges(self) -> None:
        """Clear all lineage edges."""
        self.conn.execute("DELETE FROM lineage_edges")

    def clear_catalog_and_lineage(self) -> None:
        """Clear both catalog nodes and lineage edges."""
        self.clear_lineage_edges()
        self.clear_catalog_nodes()
