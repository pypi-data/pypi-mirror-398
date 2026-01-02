"""
Federated Query Executor

Orchestrates multi-source query execution using Spark compute engine.
This is the core component that enables DVT's data virtualization capabilities.

v0.3.0: Unified Spark architecture - all federation uses Spark JDBC.
v0.58.5: Fixed segfaults by disabling multiprocessing resource tracker.

Execution flow:
1. Identify all source tables/models from compiled SQL
2. Load sources into Spark via JDBC (parallel reads)
3. Execute model SQL in Spark
4. Return results as PyArrow Table
5. Materialize to target via JDBC or adapter

Key principle: Adapters for I/O only, Spark for all compute.
"""

# Standard imports
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

from pathlib import Path

from datetime import datetime

from dbt.adapters.base import BaseAdapter
from dbt.compute.engines.spark_engine import SparkEngine, _clean_spark_error
from dbt.contracts.graph.manifest import Manifest
from dbt.contracts.graph.nodes import ManifestNode
from dbt.query_analyzer import QueryAnalysisResult
from dbt_common.exceptions import DbtRuntimeError


def _log(msg: str) -> None:
    """
    Log a message that appears immediately in console output.
    DVT v0.4.7: Suppressed for clean output (logs go to spark_run_history).
    """
    # Suppressed for clean output - all debug info goes to spark_run_history file
    pass


def _get_dependent_views_pg(cursor, schema: str, table: str) -> List[Dict[str, str]]:
    """
    Query PostgreSQL for views that depend on a table.
    DVT v0.5.5: Used to save views before DROP CASCADE, then restore after.

    Returns list of dicts with: schema, name, definition
    """
    try:
        # Query views that depend on this table using pg_depend
        sql = """
        SELECT DISTINCT
            n.nspname as view_schema,
            c.relname as view_name,
            pg_get_viewdef(c.oid, true) as view_definition
        FROM pg_depend d
        JOIN pg_rewrite r ON r.oid = d.objid
        JOIN pg_class c ON c.oid = r.ev_class
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_class t ON t.oid = d.refobjid
        JOIN pg_namespace tn ON tn.oid = t.relnamespace
        WHERE t.relname = %s
          AND tn.nspname = %s
          AND c.relkind = 'v'
          AND d.classid = 'pg_rewrite'::regclass
          AND d.deptype = 'n'
        """
        cursor.execute(sql, (table, schema))
        rows = cursor.fetchall()
        return [
            {'schema': row[0], 'name': row[1], 'definition': row[2]}
            for row in rows
        ]
    except Exception:
        # If query fails (different DB, permissions), return empty
        return []


def _recreate_views_pg(cursor, views: List[Dict[str, str]]) -> None:
    """
    Recreate views from their saved definitions.
    DVT v0.5.5: Restores views after DROP CASCADE.
    """
    for view in views:
        try:
            create_sql = f'CREATE OR REPLACE VIEW "{view["schema"]}"."{view["name"]}" AS {view["definition"]}'
            _log(f"[DVT] Recreating view: {view['schema']}.{view['name']}")
            cursor.execute(create_sql)
        except Exception as e:
            _log(f"[DVT] Warning: Could not recreate view {view['name']}: {e}")


@dataclass
class SourceTableMetadata:
    """Metadata about a source table needed for federated execution."""

    source_id: str  # Unique ID from manifest
    connection_name: str  # Which connection to read from
    database: str  # Database name
    schema: str  # Schema name
    identifier: str  # Table name
    qualified_name: str  # Fully qualified name for SQL


@dataclass
class FederatedExecutionResult:
    """Result of federated query execution."""

    spark_dataframe: Any  # Spark DataFrame with query results
    source_tables: List[SourceTableMetadata]  # Sources used
    compute_engine: str  # Engine used (spark)
    execution_time_ms: float  # Execution time in milliseconds
    rows_read: int  # Total rows read from sources
    rows_returned: int  # Rows in result (may be None if not counted)
    engine: Any  # SparkEngine instance (for session lifecycle management)


class FederatedExecutor:
    """
    Orchestrates federated query execution across multiple data sources.

    This executor:
    1. Extracts data from multiple sources via adapters
    2. Loads data into a compute engine
    3. Executes the query
    4. Returns results as Spark DataFrame
    """

    def __init__(
        self,
        manifest: Manifest,
        adapters: Dict[str, BaseAdapter],
        default_compute_engine: str = "spark-local",
        project_root: Optional[Path] = None,
    ):
        """
        Initialize federated executor.

        v0.3.0: All federation uses Spark (local or cluster).
        v0.54.0: Added metadata store integration for type mapping.

        :param manifest: The dbt manifest with all nodes and sources
        :param adapters: Dict of connection_name → adapter instances
        :param default_compute_engine: Default compute engine ("spark-local" or "spark-cluster")
        :param project_root: Project root directory (for metadata store access)
        """
        self.manifest = manifest
        self.adapters = adapters
        self.default_compute_engine = default_compute_engine
        self.project_root = project_root or Path(".")
        self._metadata_store = None

    @property
    def metadata_store(self):
        """
        Lazy-load the project metadata store.

        v0.54.0: Returns None if store doesn't exist (graceful degradation).
        """
        if self._metadata_store is None:
            try:
                from dbt.compute.metadata import ProjectMetadataStore
                store_path = self.project_root / ".dvt" / "metadata.duckdb"
                if store_path.exists():
                    self._metadata_store = ProjectMetadataStore(self.project_root)
                    _log("[DVT] Metadata store loaded from .dvt/metadata.duckdb")
            except ImportError:
                _log("[DVT] DuckDB not available - metadata store disabled")
            except Exception as e:
                _log(f"[DVT] Could not load metadata store: {e}")
        return self._metadata_store

    def get_source_column_metadata(
        self,
        source_name: str,
        table_name: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Look up column metadata for a source table from the metadata store.

        v0.54.0: Returns cached metadata if available, None otherwise.

        :param source_name: Name of the source
        :param table_name: Name of the table
        :returns: List of column metadata dicts, or None if not cached
        """
        if self.metadata_store is None:
            return None

        try:
            metadata = self.metadata_store.get_table_metadata(source_name, table_name)
            if metadata:
                return [
                    {
                        "column_name": col.column_name,
                        "adapter_type": col.adapter_type,
                        "spark_type": col.spark_type,
                        "is_nullable": col.is_nullable,
                        "ordinal_position": col.ordinal_position,
                    }
                    for col in metadata.columns
                ]
        except Exception as e:
            _log(f"[DVT] Warning: Could not fetch metadata for {source_name}.{table_name}: {e}")

        return None

    def get_spark_schema_for_source(
        self,
        source_name: str,
        table_name: str
    ) -> Optional[str]:
        """
        Generate Spark schema DDL for a source table from cached metadata.

        v0.54.0: Returns schema string for explicit type enforcement.

        :param source_name: Name of the source
        :param table_name: Name of the table
        :returns: Spark schema DDL string, or None if not cached
        """
        columns = self.get_source_column_metadata(source_name, table_name)
        if not columns:
            return None

        # Build Spark schema DDL
        # Format: "col1 StringType, col2 IntegerType, ..."
        schema_parts = []
        for col in sorted(columns, key=lambda c: c["ordinal_position"]):
            spark_type = col["spark_type"]
            nullable = "" if col["is_nullable"] else " NOT NULL"
            schema_parts.append(f"`{col['column_name']}` {spark_type}{nullable}")

        return ", ".join(schema_parts)

    def capture_source_metadata(
        self,
        engine: SparkEngine,
        source_name: str,
        table_name: str,
        adapter_name: str,
        connection_name: str,
        schema_name: str,
        table_alias: str
    ) -> None:
        """
        Capture metadata from a loaded source table and save to metadata store.

        v0.54.0: Metadata propagation during federated execution.

        :param engine: SparkEngine instance with loaded table
        :param source_name: Name of the source
        :param table_name: Name of the table
        :param adapter_name: Type of adapter (postgres, snowflake, etc.)
        :param connection_name: Connection profile name
        :param schema_name: Database schema name
        :param table_alias: Alias used in Spark for the temp view
        """
        if self.metadata_store is None:
            return

        try:
            # Import here to avoid circular imports
            from dbt.compute.metadata.store import TableMetadata, ColumnMetadata
            from dbt.compute.metadata.registry import TypeRegistry

            # Get schema from Spark temp view
            spark_schema = engine.get_schema(table_alias)
            if not spark_schema:
                _log(f"[DVT] Could not get schema for {table_alias}")
                return

            # Build column metadata from Spark schema
            columns = []
            for idx, field in enumerate(spark_schema):
                # field is a StructField with name, dataType, nullable
                spark_type_str = str(field.dataType)

                # Try to map Spark type back to adapter type
                # Look up in type registry (reverse mapping)
                adapter_type = self._spark_to_adapter_type(
                    adapter_name, spark_type_str
                )

                columns.append(ColumnMetadata(
                    column_name=field.name,
                    adapter_type=adapter_type,
                    spark_type=spark_type_str,
                    is_nullable=field.nullable,
                    is_primary_key=False,  # Can't infer from JDBC
                    ordinal_position=idx + 1,
                ))

            if columns:
                # Create and save table metadata
                metadata = TableMetadata(
                    source_name=source_name,
                    table_name=table_name,
                    adapter_name=adapter_name,
                    connection_name=connection_name,
                    schema_name=schema_name,
                    row_count=None,  # Don't query count to avoid performance hit
                    columns=columns,
                    last_refreshed=datetime.now(),
                )

                with self.metadata_store as store:
                    store.save_table_metadata(metadata)
                    _log(f"[DVT] Captured metadata for {source_name}.{table_name}: {len(columns)} columns")

        except Exception as e:
            # Don't fail execution if metadata capture fails
            _log(f"[DVT] Warning: Could not capture metadata for {source_name}.{table_name}: {e}")

    def _spark_to_adapter_type(
        self,
        adapter_name: str,
        spark_type: str
    ) -> str:
        """
        Map Spark type back to approximate adapter type.

        This is a best-effort reverse mapping - exact original type
        may not be recoverable due to type normalization during JDBC read.

        :param adapter_name: Target adapter name
        :param spark_type: Spark type string (e.g., "StringType()")
        :returns: Approximate adapter type string
        """
        from dbt.compute.metadata.registry import TypeRegistry

        # Normalize spark type (remove parentheses, etc.)
        spark_type_normalized = spark_type.replace("()", "").replace("Type", "").upper()

        # Common mappings (reverse of type_registry)
        spark_to_common = {
            "STRING": "VARCHAR",
            "INTEGER": "INTEGER",
            "INT": "INTEGER",
            "LONG": "BIGINT",
            "BIGINT": "BIGINT",
            "SHORT": "SMALLINT",
            "DOUBLE": "DOUBLE PRECISION",
            "FLOAT": "REAL",
            "DECIMAL": "DECIMAL",
            "BOOLEAN": "BOOLEAN",
            "DATE": "DATE",
            "TIMESTAMP": "TIMESTAMP",
            "BINARY": "BYTEA",
            "ARRAY": "ARRAY",
            "MAP": "JSON",
            "STRUCT": "JSON",
        }

        # Return common SQL type
        return spark_to_common.get(spark_type_normalized, spark_type)

    def execute(
        self,
        node: ManifestNode,
        analysis_result: QueryAnalysisResult,
        compute_engine_override: Optional[str] = None,
        spark_config: Optional[Dict[str, str]] = None,
        target_adapter_type: Optional[str] = None,
        coerce_view_to_table: bool = False,
    ) -> FederatedExecutionResult:
        """
        Execute a node using federated query processing.

        :param node: The compiled node to execute
        :param analysis_result: Query analysis result
        :param compute_engine_override: Override compute engine choice
        :param spark_config: Spark configuration (if using Spark)
        :param target_adapter_type: Target adapter type for JDBC materialization
        :param coerce_view_to_table: DVT v0.51.6 - If True, treat view as table (Rule 3.C.3)
        :returns: FederatedExecutionResult with query results
        :raises DbtRuntimeError: If execution fails
        """
        import time

        _log(f"[DVT] Starting federated execution for node: {node.unique_id}")
        start_time = time.time()

        # Determine compute engine
        compute_engine = (
            compute_engine_override
            or analysis_result.user_override
            or self.default_compute_engine
        )
        _log(f"[DVT] Compute engine selected: {compute_engine}")

        # DVT v0.5.0: Restrict Spark compute to table and incremental materializations only
        # DVT v0.51.6: Allow view if coerce_view_to_table is True (Rule 3.C.3)
        if hasattr(node, 'config') and hasattr(node.config, 'materialized'):
            materialized = node.config.materialized

            # DVT v0.51.6: Views are coerced to tables in cross-target scenarios
            effective_materialized = 'table' if (materialized == 'view' and coerce_view_to_table) else materialized

            # Only allow table and incremental
            if effective_materialized not in ('table', 'incremental'):
                raise DbtRuntimeError(
                    f"Spark compute engine only supports 'table' and 'incremental' materializations. "
                    f"Node '{node.unique_id}' uses '{materialized}'. "
                    f"Please change the materialization to 'table' or 'incremental', or use adapter-native execution."
                )

            # For incremental, validate strategy is 'append' (only supported strategy)
            if materialized == 'incremental':
                incremental_strategy = getattr(node.config, 'incremental_strategy', 'append')
                if incremental_strategy != 'append':
                    raise DbtRuntimeError(
                        f"Spark compute engine only supports 'append' incremental strategy. "
                        f"Node '{node.unique_id}' uses '{incremental_strategy}'. "
                        f"Supported strategies: append. "
                        f"For merge/delete+insert/insert_overwrite, use adapter-native execution."
                    )

            if coerce_view_to_table and materialized == 'view':
                _log(f"[DVT] Materialization: view → table (coerced for cross-target)")
            else:
                _log(f"[DVT] Materialization validated: {materialized}")

        # Extract source table metadata
        source_tables = self._extract_source_tables(analysis_result)
        _log(f"[DVT] Found {len(source_tables)} source table(s)")

        # v0.5.99: Look up named clusters from registry
        from dbt.config.compute import ComputeRegistry
        from dbt.compute.jdbc_utils import set_docker_mode
        registry = ComputeRegistry()
        cluster_config = None

        # Check if it's a registered named cluster
        if compute_engine not in ("spark-local", "spark", "spark-cluster"):
            cluster = registry.get(compute_engine)
            if cluster:
                cluster_config = cluster.config
                _log(f"[DVT] Found registered cluster '{compute_engine}' with platform: {cluster.detect_platform().value}")

                # DVT v0.51.8: Enable Docker mode for standalone clusters with localhost master
                # This rewrites localhost -> host.docker.internal in JDBC URLs
                master = cluster_config.get("master", "")
                if master.startswith("spark://") and ("localhost" in master or "127.0.0.1" in master):
                    set_docker_mode(True)
                    _log("[DVT] Docker mode enabled for JDBC URLs")
                else:
                    set_docker_mode(False)
            else:
                # Not in registry - check if it starts with "spark" for backwards compat
                if not compute_engine.startswith("spark"):
                    raise DbtRuntimeError(
                        f"Invalid compute engine '{compute_engine}'. "
                        f"Not found in compute registry. "
                        f"Available: {[c.name for c in registry.list()]}"
                    )
        else:
            set_docker_mode(False)

        # Create Spark engine (local or cluster based on config)
        _log(f"[DVT] Creating Spark engine (mode: {compute_engine})")
        if compute_engine == "spark-local" or compute_engine == "spark":
            engine = SparkEngine(mode="embedded", spark_config=spark_config or {})
        elif compute_engine == "spark-cluster" or compute_engine.startswith("spark:"):
            # External cluster
            engine = SparkEngine(mode="external", spark_config=spark_config or {})
        elif cluster_config:
            # Named cluster from registry - pass full config
            engine = SparkEngine(mode="external", spark_config=cluster_config)
        else:
            # Fallback
            engine = SparkEngine(mode="external", spark_config=spark_config or {})

        _log("[DVT] Spark engine created, initializing Spark session...")
        try:
            # v0.5.99: Collect adapter types from sources + target for JDBC driver provisioning
            all_adapter_types = set()
            for source_table in source_tables:
                adapter = self.adapters.get(source_table.connection_name)
                if adapter:
                    all_adapter_types.add(adapter.type())
            # Include target adapter type for materialization
            if target_adapter_type:
                all_adapter_types.add(target_adapter_type)
            _log(f"[DVT] Adapter types (sources + target): {all_adapter_types}")

            # Initialize Spark session with all adapter types (for JDBC drivers)
            engine.connect(adapter_types=all_adapter_types)
            _log("[DVT] Spark session initialized successfully")

            # Get compiled SQL first (needed for optimization checks)
            compiled_sql = (
                node.compiled_code
                if hasattr(node, "compiled_code")
                else node.raw_code
            )

            # Step 1: Load source data into Spark via JDBC (v0.3.0: Spark-only)
            total_rows_read = self._load_sources_spark_jdbc(
                engine, source_tables, analysis_result, compiled_sql
            )

            # Step 2: Rewrite SQL to use table aliases
            rewritten_sql = self._rewrite_sql_for_compute(
                compiled_sql, source_tables
            )

            # Step 3: Execute query in Spark
            result_df = engine.spark.sql(rewritten_sql)

            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000

            # Return Spark DataFrame AND engine (caller must close engine after materialization)
            return FederatedExecutionResult(
                spark_dataframe=result_df,
                source_tables=source_tables,
                compute_engine=compute_engine,
                execution_time_ms=execution_time_ms,
                rows_read=total_rows_read,
                rows_returned=None,  # Will be counted during JDBC write
                engine=engine,  # Return engine for lifecycle management
            )

        except Exception as e:
            # Clean up engine on error
            try:
                engine.close()
            except:
                pass
            # DVT v0.5.2: Clean error message (no Java stack trace)
            clean_error = _clean_spark_error(e)
            # DVT v0.5.99: Include original exception for debugging if cleaned message is too short
            if len(clean_error) < 20:
                clean_error = f"{clean_error} (original: {str(e)[:200]})"
            raise DbtRuntimeError(
                f"Federated execution failed for node {node.unique_id}: {clean_error}"
            )

    def _extract_source_tables(
        self, analysis_result: QueryAnalysisResult
    ) -> List[SourceTableMetadata]:
        """
        Extract metadata for all source tables referenced in the query.

        :param analysis_result: Query analysis result
        :returns: List of SourceTableMetadata
        """
        source_tables = []

        for source_id in analysis_result.source_refs:
            source = self.manifest.sources.get(source_id)
            if not source:
                raise DbtRuntimeError(
                    f"Source {source_id} not found in manifest. "
                    f"Available sources: {list(self.manifest.sources.keys())[:3]}"
                )

            # Get connection name from source definition
            connection_name = getattr(source, "connection", None)

            if not connection_name:
                raise DbtRuntimeError(
                    f"Source {source_id} does not have a connection specified. "
                    "DVT requires all sources to specify a connection in the source YAML:\n"
                    "  - name: my_source\n"
                    "    connection: my_connection"
                )

            # Build qualified name for SQL
            qualified_name = f"{source.database}.{source.schema}.{source.identifier}"

            metadata = SourceTableMetadata(
                source_id=source_id,
                connection_name=connection_name,
                database=source.database,
                schema=source.schema,
                identifier=source.identifier,
                qualified_name=qualified_name,
            )

            source_tables.append(metadata)

        return source_tables

    # NOTE: _load_sources_via_adapters method removed in v0.3.0
    # All data loading now uses Spark JDBC via _load_sources_spark_jdbc

    def _load_sources_spark_jdbc(
        self,
        engine: SparkEngine,
        source_tables: List[SourceTableMetadata],
        analysis_result: QueryAnalysisResult,
        compiled_sql: str,
    ) -> int:
        """
        Load all source tables into Spark via JDBC connectors (Phase 1: v0.2.0).

        This bypasses the DVT node's memory by reading data directly from source
        databases into Spark workers (distributed memory). Data flow:
        Source DB → Spark Workers → Target DB (no DVT node bottleneck)

        This method:
        1. Gets adapter credentials for each source
        2. Converts credentials to JDBC config
        3. Auto-detects partition column for parallel reads
        4. Reads data via Spark JDBC with partitioning
        5. Registers as temp view in Spark

        :param engine: Spark engine instance
        :param source_tables: List of source table metadata
        :param analysis_result: Query analysis result
        :returns: Total number of rows loaded (estimated, as Spark is lazy)
        :raises DbtRuntimeError: If JDBC not supported or read fails
        """
        from dbt.compute.jdbc_utils import build_jdbc_config
        from dbt.compute.filter_pushdown import optimize_jdbc_table_read

        total_rows = 0

        for source_meta in source_tables:
            # Get adapter for this source's connection
            adapter = self.adapters.get(source_meta.connection_name)
            if not adapter:
                raise DbtRuntimeError(
                    f"No adapter found for connection '{source_meta.connection_name}'"
                )

            # Check if JDBC is supported for this adapter type
            if not engine.supports_jdbc(adapter.type()):
                raise DbtRuntimeError(
                    f"JDBC not supported for adapter type '{adapter.type()}'. "
                    f"This source type requires a JDBC driver. "
                    f"Please ensure the appropriate JDBC driver is available."
                )

            # Log connection attempt
            _log(f"[DVT] Connecting to {adapter.type()} source: {source_meta.qualified_name} (connection: {source_meta.connection_name})")
            connection_start = time.time()

            # Get adapter credentials
            credentials = adapter.config.credentials

            # Build JDBC configuration
            try:
                jdbc_url, jdbc_properties = build_jdbc_config(credentials)
            except Exception as e:
                _log(f"[DVT] ERROR: Failed to build JDBC config for '{source_meta.qualified_name}': {str(e)}")
                raise DbtRuntimeError(
                    f"Failed to build JDBC config for source '{source_meta.qualified_name}': {str(e)}"
                ) from e

            # Prepare JDBC read parameters with filter pushdown optimization
            # Instead of reading full table, push down filters (LIMIT, WHERE) to source DB
            jdbc_table = optimize_jdbc_table_read(
                source_table=source_meta,
                compiled_sql=compiled_sql,
                source_tables=source_tables,
                adapter_type=adapter.type()
            )
            table_alias = self._get_table_alias(source_meta)
            numPartitions = 16  # Default parallelism

            # Automatic partition detection DISABLED
            # Reasons:
            # 1. Slow metadata queries (30-60s on cold Snowflake warehouses)
            # 2. Unnecessary overhead for small datasets
            # 3. Filter pushdown now handles optimization automatically
            partition_column = None
            lower_bound = None
            upper_bound = None

            # v0.54.0: Look up cached metadata for type mapping
            # Extract source_name and table_name from source_id
            source_parts = source_meta.source_id.split(".")
            if len(source_parts) >= 4:
                source_name = source_parts[2]
                table_name = source_parts[3]
                cached_metadata = self.get_source_column_metadata(source_name, table_name)
                if cached_metadata:
                    _log(f"[DVT] Using cached metadata for {source_name}.{table_name} ({len(cached_metadata)} columns)")
                else:
                    _log(f"[DVT] No cached metadata for {source_name}.{table_name} - using JDBC type inference")
            else:
                cached_metadata = None

            # Read via Spark JDBC and register as temp view
            _log(f"[DVT] Reading from JDBC: {jdbc_table}")
            try:
                engine.register_jdbc_table(
                    url=jdbc_url,
                    table=jdbc_table,
                    properties=jdbc_properties,
                    table_alias=table_alias,
                    numPartitions=numPartitions,
                    partitionColumn=partition_column,
                    lowerBound=lower_bound,
                    upperBound=upper_bound,
                )
                connection_time = time.time() - connection_start
                _log(f"[DVT] ✓ Connected to {source_meta.qualified_name} in {connection_time:.1f}s")
                if connection_time > 30:
                    _log(f"[DVT] WARNING: Connection took {connection_time:.1f}s (warehouse may have been suspended)")

                # v0.54.0: Capture metadata if not already cached
                if not cached_metadata and len(source_parts) >= 4:
                    self.capture_source_metadata(
                        engine=engine,
                        source_name=source_name,
                        table_name=table_name,
                        adapter_name=adapter.type(),
                        connection_name=source_meta.connection_name,
                        schema_name=source_meta.schema,
                        table_alias=table_alias
                    )
            except Exception as e:
                connection_time = time.time() - connection_start
                # DVT v0.5.2: Clean error message (no Java stack trace)
                clean_error = _clean_spark_error(e)
                _log(f"[DVT] ERROR: Failed to load '{source_meta.qualified_name}' after {connection_time:.1f}s: {clean_error}")
                raise DbtRuntimeError(
                    f"Failed to load source '{source_meta.qualified_name}' via JDBC: {clean_error}"
                )

            # Note: Can't easily count rows without triggering Spark action
            # For now, return 0 (rows_read will be inaccurate for JDBC path)
            # TODO: Consider running COUNT(*) query if row count is needed
            total_rows += 0

        return total_rows

    def _get_table_alias(self, source_meta: SourceTableMetadata) -> str:
        """
        Generate a safe table alias for the compute engine.

        Compute engines may not support dots or special characters in table names,
        so we create a normalized alias.

        :param source_meta: Source table metadata
        :returns: Safe table alias
        """
        # Extract source name and table name from source_id
        # source_id format: source.{project}.{source_name}.{table_name}
        parts = source_meta.source_id.split(".")
        if len(parts) >= 4:
            source_name = parts[2]
            table_name = parts[3]
            return f"{source_name}_{table_name}"
        else:
            # Fallback: use identifier
            return source_meta.identifier

    def _rewrite_sql_for_compute(
        self, sql: str, source_tables: List[SourceTableMetadata]
    ) -> str:
        """
        Rewrite SQL to replace fully-qualified source table names with compute engine aliases.

        Source tables are loaded into the compute engine with simple aliases (e.g., 'Exim_cbs_f_country'),
        but the compiled SQL contains fully-qualified names (e.g., '"EXIM_EDWH_DEV"."ods"."cbs_f_country"').
        This method replaces the qualified names with the aliases and removes source-specific clauses
        like SAMPLE that have been pushed down to the source.

        :param sql: Compiled SQL with fully-qualified table names
        :param source_tables: List of source table metadata
        :returns: Rewritten SQL with aliases and source-specific clauses removed
        """
        import re

        rewritten_sql = sql

        for source_meta in source_tables:
            # Get the alias used in the compute engine
            alias = self._get_table_alias(source_meta)

            # Replace the fully-qualified table name with the alias
            # Format: "database"."schema"."table" or database.schema.table
            qualified_name = source_meta.qualified_name
            parts = qualified_name.split(".")

            # DVT v0.51.7: Use case-insensitive regex replacement for all variants
            # because Snowflake returns uppercase but Spark/Databricks lowercases

            # 1. Unquoted: EXIM_EDWH_DEV.ods.cbs_f_country (any case)
            unquoted_pattern = re.compile(
                r'\b' + r'\.'.join(re.escape(p) for p in parts) + r'\b',
                re.IGNORECASE
            )
            rewritten_sql = unquoted_pattern.sub(alias, rewritten_sql)

            # 2. Double-quoted (PostgreSQL style): "EXIM_EDWH_DEV"."ods"."cbs_f_country" (any case)
            quoted_pattern = re.compile(
                r'"' + r'"\."\s*'.join(re.escape(p) for p in parts) + r'"',
                re.IGNORECASE
            )
            rewritten_sql = quoted_pattern.sub(alias, rewritten_sql)

            # 3. Single string quoted: "EXIM_EDWH_DEV.ods.cbs_f_country" (any case)
            single_quoted_pattern = re.compile(
                r'"' + r'\.'.join(re.escape(p) for p in parts) + r'"',
                re.IGNORECASE
            )
            rewritten_sql = single_quoted_pattern.sub(alias, rewritten_sql)

            # 4. Backtick-quoted (Spark/Databricks style): `EXIM_EDWH_DEV`.`ods`.`cbs_f_country` (any case)
            backtick_pattern = re.compile(
                r'`' + r'`\.`\s*'.join(re.escape(p) for p in parts) + r'`',
                re.IGNORECASE
            )
            rewritten_sql = backtick_pattern.sub(alias, rewritten_sql)

        # DVT v0.4.5: Remove Snowflake-specific SAMPLE clauses
        # These have been pushed down to the source via JDBC subqueries
        # Spark SQL doesn't support SAMPLE syntax, so remove it from the query
        # Pattern matches: SAMPLE (N), SAMPLE (N ROWS), SAMPLE SYSTEM|BERNOULLI|BLOCK (P)
        # with optional REPEATABLE(seed) or SEED(seed)
        rewritten_sql = re.sub(
            r'\s*(?:TABLE)?SAMPLE\s+(?:SYSTEM|BERNOULLI|BLOCK)\s*\(\s*\d+(?:\.\d+)?\s*\)'
            r'(?:\s+(?:REPEATABLE|SEED)\s*\(\s*\d+\s*\))?',
            '',
            rewritten_sql,
            flags=re.IGNORECASE
        )
        rewritten_sql = re.sub(
            r'\s*(?:TABLE)?SAMPLE\s*\(\s*\d+(?:\s+ROWS)?\s*\)'
            r'(?:\s+(?:REPEATABLE|SEED)\s*\(\s*\d+\s*\))?',
            '',
            rewritten_sql,
            flags=re.IGNORECASE
        )

        return rewritten_sql

    def materialize_result(
        self,
        result: FederatedExecutionResult,
        target_adapter: BaseAdapter,
        target_table: str,
        mode: str = "create",
        use_jdbc: bool = True,
        spark_result_df: Optional[Any] = None,
    ) -> Any:
        """
        Materialize federated query results to target database.

        v0.3.0: Uses Spark JDBC for all materialization (default).

        :param result: Federated execution result
        :param target_adapter: Adapter to use for getting target credentials
        :param target_table: Target table name (qualified)
        :param mode: Write mode ('create', 'append', 'replace')
        :param use_jdbc: If True, use JDBC write path (default in v0.3.0)
        :param spark_result_df: Spark DataFrame with results (required for JDBC path)
        :returns: AdapterResponse from write operation
        """
        if use_jdbc and spark_result_df is not None:
            # Use JDBC write path (default in v0.3.0)
            return self._materialize_spark_jdbc(
                result_df=spark_result_df,
                target_adapter=target_adapter,
                target_table=target_table,
                mode=mode,
            )
        else:
            # Fallback: use target adapter directly (for adapters without JDBC support)
            raise DbtRuntimeError(
                "Non-JDBC materialization path removed in v0.3.0. "
                "All materialization requires Spark JDBC. "
                "Ensure spark_result_df is provided."
            )

    def _materialize_spark_jdbc(
        self,
        result_df: Any,  # Spark DataFrame
        target_adapter: BaseAdapter,
        target_table: str,
        mode: str = "create",
    ) -> Any:
        """
        Materialize Spark query results to target database via JDBC (Phase 1: v0.2.0).

        This bypasses the DVT node's memory by writing data directly from Spark
        workers to the target database.

        :param result_df: Spark DataFrame with query results
        :param target_adapter: Adapter to use for getting target credentials
        :param target_table: Target table name (qualified)
        :param mode: Write mode ('create', 'append', 'replace')
        :returns: AdapterResponse
        :raises DbtRuntimeError: If JDBC write fails
        """
        from dbt.compute.jdbc_utils import build_jdbc_config
        from dbt.adapters.contracts.connection import AdapterResponse

        # Get target credentials
        target_credentials = target_adapter.config.credentials

        # Build JDBC configuration for target
        try:
            jdbc_url, jdbc_properties = build_jdbc_config(target_credentials)
        except Exception as e:
            raise DbtRuntimeError(
                f"Failed to build JDBC config for target '{target_table}': {str(e)}"
            ) from e

        # Map DVT mode to Spark JDBC mode
        spark_mode_mapping = {
            "create": "overwrite",  # Create/recreate table (dbt behavior)
            "append": "append",  # Add to existing table
            "replace": "overwrite",  # Drop and recreate
        }
        spark_mode = spark_mode_mapping.get(mode, "overwrite")

        _log(f"[DVT] Writing to target via Spark JDBC: {target_table} (mode={spark_mode})")

        # Get Spark session from DataFrame
        spark = result_df.sparkSession

        # Log DataFrame schema for debugging
        _log(f"[DVT] DataFrame schema:")
        for field in result_df.schema.fields:
            _log(f"  - {field.name}: {field.dataType}")

        # Log row count
        row_count = result_df.count()
        _log(f"[DVT] DataFrame has {row_count} rows")

        # Sanitize URL for logging (hide password)
        safe_url = jdbc_url.split("?")[0] if "?" in jdbc_url else jdbc_url
        _log(f"[DVT] JDBC URL: {safe_url}")
        _log(f"[DVT] JDBC table: {target_table}")

        # Write via JDBC
        saved_views: List[Dict[str, str]] = []
        target_adapter_type = target_adapter.type()
        is_postgres = target_adapter_type in ("postgres", "postgresql")

        try:
            # DVT v0.5.5: Save dependent views before DROP CASCADE, restore after
            # Spark's JDBC overwrite mode doesn't use CASCADE, causing failures
            # when dependent objects (views, etc.) exist
            # DVT v0.51.6: Only applies to PostgreSQL (other DBs handle this differently)
            if spark_mode == "overwrite" and is_postgres:
                try:
                    with target_adapter.connection_named("__dvt_drop__"):
                        conn = target_adapter.connections.get_thread_connection()
                        cursor = conn.handle.cursor()

                        # Parse schema.table from target_table
                        parts = target_table.replace('"', '').split('.')
                        if len(parts) >= 2:
                            tbl_schema = parts[-2]
                            tbl_name = parts[-1]
                        else:
                            tbl_schema = 'public'
                            tbl_name = parts[-1]

                        # DVT v0.5.5: Save dependent views before dropping
                        saved_views = _get_dependent_views_pg(cursor, tbl_schema, tbl_name)
                        if saved_views:
                            _log(f"[DVT] Saving {len(saved_views)} dependent view(s) before DROP")

                        # Use CASCADE to drop dependent objects
                        drop_sql = f"DROP TABLE IF EXISTS {target_table} CASCADE"
                        _log(f"[DVT] Pre-drop with CASCADE: {drop_sql}")
                        cursor.execute(drop_sql)
                        conn.handle.commit()
                        cursor.close()
                except Exception as drop_err:
                    _log(f"[DVT] Pre-drop warning (continuing): {drop_err}")

            result_df.write.format("jdbc").options(
                url=jdbc_url, dbtable=target_table, batchsize="10000", **jdbc_properties
            ).mode(spark_mode).save()

            # DVT v0.5.5: Restore dependent views after successful write (PostgreSQL only)
            if saved_views and is_postgres:
                try:
                    with target_adapter.connection_named("__dvt_restore__"):
                        conn = target_adapter.connections.get_thread_connection()
                        cursor = conn.handle.cursor()
                        _recreate_views_pg(cursor, saved_views)
                        conn.handle.commit()
                        cursor.close()
                        _log(f"[DVT] Restored {len(saved_views)} dependent view(s)")
                except Exception as restore_err:
                    _log(f"[DVT] Warning: Could not restore views: {restore_err}")

            # Return mock AdapterResponse
            # Note: Can't easily get rows_affected from Spark JDBC write
            return AdapterResponse(
                _message=f"SUCCESS - Table {target_table} materialized via JDBC",
                rows_affected=row_count,
            )

        except Exception as e:
            # DVT v0.5.2: Clean error message (no Java stack trace)
            clean_error = _clean_spark_error(e)
            raise DbtRuntimeError(
                f"Failed to materialize results to '{target_table}': {clean_error}"
            )

    def explain_execution(
        self, node: ManifestNode, analysis_result: QueryAnalysisResult
    ) -> str:
        """
        Generate an execution plan explanation for a federated query.

        Useful for debugging and optimization.

        :param node: The node to explain
        :param analysis_result: Query analysis result
        :returns: Human-readable execution plan
        """
        source_tables = self._extract_source_tables(analysis_result)

        plan_parts = [
            "=== DVT Federated Execution Plan ===",
            f"Node: {node.unique_id}",
            f"Compute Engine: {self.default_compute_engine}",
            "",
            "Data Sources:",
        ]

        for i, source_meta in enumerate(source_tables, 1):
            plan_parts.append(
                f"  {i}. {source_meta.qualified_name} "
                f"(connection: {source_meta.connection_name})"
            )

        plan_parts.extend(
            [
                "",
                "Execution Steps (v0.3.0 - Spark-Unified):",
                "  1. Extract data from each source via Spark JDBC (parallel reads)",
                f"  2. Load {len(source_tables)} table(s) into Spark ({self.default_compute_engine})",
                "  3. Execute query in Spark",
                "  4. Materialize to target via Spark JDBC",
                "",
                f"Strategy: {analysis_result.strategy.upper()}",
                f"Reason: {analysis_result.reason}",
            ]
        )

        return "\n".join(plan_parts)


class SourceRewriter:
    """
    Rewrites SQL queries to use compute engine table aliases.

    When sources are loaded into compute engines, they may be registered with
    different names (aliases). This class rewrites the SQL to use those aliases.
    """

    @staticmethod
    def rewrite_sources(sql: str, source_mapping: Dict[str, str]) -> str:
        """
        Rewrite SQL to use compute engine table aliases.

        :param sql: Original SQL with qualified source names
        :param source_mapping: Dict of qualified_name → alias
        :returns: Rewritten SQL
        """
        rewritten = sql

        # Replace each qualified name with its alias
        for qualified_name, alias in source_mapping.items():
            # Match qualified name (database.schema.table)
            pattern = re.compile(rf"\b{re.escape(qualified_name)}\b", re.IGNORECASE)
            rewritten = pattern.sub(alias, rewritten)

        return rewritten
