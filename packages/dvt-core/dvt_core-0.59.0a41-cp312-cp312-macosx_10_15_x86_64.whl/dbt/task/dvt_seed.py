"""
DVT Seed Task - Spark-powered seed loading with pattern-based transformations.

DVT v0.59.0a34: Hybrid approach - file databases use native, network use JDBC.
Uses DVT's virtualization infrastructure for consistent behavior across all targets.

Features:
1. Read CSV files with Spark
2. Match column values against patterns in value_transformations table
3. Apply Spark SQL transformations automatically
4. Write to target using best method:
   - File-based databases (DuckDB): Native connection via Pandas/Arrow (avoids locking issues)
   - Network databases (Postgres, etc.): Spark JDBC with DROP CASCADE support
5. Rich UI output with progress tracking

This ensures consistent behavior whether writing to DuckDB, Postgres, Databricks,
or any other supported adapter.
"""

import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import duckdb

from dbt.adapters.factory import get_adapter
from dbt.artifacts.schemas.results import NodeStatus, RunStatus
from dbt.artifacts.schemas.run import RunResult
from dbt.config.runtime import RuntimeConfig
from dbt.contracts.graph.nodes import SeedNode
from dbt.events.types import LogSeedResult, LogStartLine
from dbt.graph import ResourceTypeSelector
from dbt.node_types import NodeType
from dbt.task import group_lookup
from dbt.task.base import BaseRunner
from dbt.task.dvt_output import DVTMultiBarDisplay, HAS_RICH
from dbt.task.printer import print_run_end_messages
from dbt.task.run import RunTask
from dbt_common.events.base_types import EventLevel
from dbt_common.events.functions import fire_event
from dbt_common.exceptions import DbtInternalError


class ValueTransformationRegistry:
    """Registry for value transformation patterns from MDM."""

    _patterns: Optional[List[Tuple[str, str, str, int]]] = None

    @classmethod
    def get_patterns(cls) -> List[Tuple[str, str, str, int]]:
        """Load transformation patterns from MDM database."""
        if cls._patterns is not None:
            return cls._patterns

        # Try packaged registry first, then user MDM
        registry_paths = [
            Path(__file__).parent.parent / "include" / "data" / "adapters_registry.duckdb",
            Path.home() / ".dvt" / ".data" / "mdm.duckdb",
        ]

        cls._patterns = []
        for path in registry_paths:
            if path.exists():
                try:
                    conn = duckdb.connect(str(path), read_only=True)
                    # Check if table exists
                    tables = conn.execute(
                        "SELECT table_name FROM information_schema.tables WHERE table_name = 'value_transformations'"
                    ).fetchall()
                    if tables:
                        result = conn.execute("""
                            SELECT pattern, target_type, transform_expr, priority
                            FROM value_transformations
                            ORDER BY priority DESC
                        """).fetchall()
                        cls._patterns = [(r[0], r[1], r[2], r[3]) for r in result]
                    conn.close()
                    if cls._patterns:
                        break
                except Exception:
                    pass

        return cls._patterns

    @classmethod
    def match_pattern(cls, sample_values: List[str]) -> Optional[Tuple[str, str]]:
        """
        Match sample values against transformation patterns.

        Returns (target_type, transform_expr) if a pattern matches majority of values.
        """
        patterns = cls.get_patterns()
        if not patterns or not sample_values:
            return None

        # Filter out None/empty values
        valid_values = [v for v in sample_values if v is not None and str(v).strip()]
        if not valid_values:
            return None

        for pattern, target_type, transform_expr, _ in patterns:
            try:
                regex = re.compile(pattern, re.IGNORECASE)
                matches = sum(1 for v in valid_values if regex.match(str(v).strip()))
                # If 80%+ of values match, use this pattern
                if matches / len(valid_values) >= 0.8:
                    return (target_type, transform_expr)
            except re.error:
                continue

        return None


class DVTSeedRunner(BaseRunner):
    """DVT Seed Runner using Spark for ETL-grade seed loading.

    Uses unified Spark JDBC for ALL adapters (32+) - same infrastructure
    as dvt run federation path. No adapter-specific code paths.
    """

    def __init__(self, config: RuntimeConfig, adapter, node: SeedNode, node_index: int, num_nodes: int):
        super().__init__(config, adapter, node, node_index, num_nodes)
        self._spark = None
        self._spark_engine = None

    def describe_node(self) -> str:
        return f"seed file {self.get_node_representation()}"

    def before_execute(self) -> None:
        fire_event(
            LogStartLine(
                description=self.describe_node(),
                index=self.node_index,
                total=self.num_nodes,
                node_info=self.node.node_info,
            )
        )

    def after_execute(self, result) -> None:
        """Print result line after seed execution completes."""
        self.print_result_line(result)

    def get_node_representation(self) -> str:
        return f"{self.node.schema}.{self.node.alias}"

    def _get_spark_session(self):
        """Get or create Spark session using configured compute from computes.yml.

        Compute selection hierarchy (highest to lowest priority):
        1. CLI --target-compute flag (MUST exist if specified)
        2. computes.yml target_compute default (MUST exist if specified)
        3. Fallback to local Spark ONLY if no compute is configured

        DVT Rule: Invalid compute → Compilation Error (NO fallback)
        """
        if self._spark is not None:
            return self._spark

        from dbt.compute.engines.spark_engine import SparkEngine
        from dbt.compute.jdbc_utils import set_docker_mode
        from dbt.config.compute import ComputeRegistry

        # Load compute configuration from project's computes.yml
        project_dir = self.config.project_root
        registry = ComputeRegistry(project_dir=project_dir)

        # Check for CLI --target-compute override (highest priority)
        cli_target_compute = getattr(self.config.args, 'TARGET_COMPUTE', None)

        # Determine which compute to use
        target_compute = cli_target_compute or registry.target_compute

        if target_compute:
            # A compute is specified - it MUST exist (no fallback)
            compute_cluster = registry.get(target_compute)
            if not compute_cluster or not compute_cluster.config:
                available = [c.name for c in registry.list()]
                raise DbtInternalError(
                    f"Compute '{target_compute}' not found in computes.yml. "
                    f"Available computes: {available}"
                )

            # DVT v0.59.0a40: Enable Docker mode for standalone clusters with localhost master
            # This rewrites localhost -> host.docker.internal in JDBC URLs
            cluster_config = compute_cluster.config
            master = cluster_config.get("master", "")
            if master.startswith("spark://") and ("localhost" in master or "127.0.0.1" in master):
                set_docker_mode(True)
            else:
                set_docker_mode(False)

            # Use configured Spark settings (SparkEngine auto-detects platform from config)
            self._spark_engine = SparkEngine(
                spark_config=cluster_config,
                app_name="DVT-Seed",
            )
        else:
            # No compute specified anywhere - fallback to local Spark
            set_docker_mode(False)
            self._spark_engine = SparkEngine(
                mode="embedded",
                app_name="DVT-Seed",
            )

        # Connect to Spark (creates the session)
        self._spark_engine.connect()
        self._spark = self._spark_engine.spark
        return self._spark

    def _get_seed_path(self) -> Path:
        """Get the path to the seed CSV file."""
        # Seeds are in the project's seed-paths directory
        seed_paths = self.config.seed_paths
        for seed_path in seed_paths:
            full_path = Path(self.config.project_root) / seed_path / f"{self.node.name}.csv"
            if full_path.exists():
                return full_path

        # Try original_file_path
        if hasattr(self.node, 'original_file_path') and self.node.original_file_path:
            original = Path(self.config.project_root) / self.node.original_file_path
            if original.exists():
                return original

        raise FileNotFoundError(f"Seed file not found for {self.node.name}")

    def _detect_transformations(self, spark_df) -> Dict[str, Tuple[str, str]]:
        """
        Analyze DataFrame columns and detect needed transformations.

        Returns dict of column_name -> (target_type, transform_expr)
        """
        transformations = {}

        # Sample first 100 rows for pattern matching
        try:
            sample_rows = spark_df.limit(100).collect()
        except Exception:
            return transformations

        if not sample_rows:
            return transformations

        # Check each string column
        for col_name in spark_df.columns:
            # Get sample values for this column
            sample_values = []
            for row in sample_rows:
                try:
                    val = row[col_name]
                    if val is not None:
                        sample_values.append(str(val))
                except Exception:
                    pass

            # Try to match a transformation pattern
            match = ValueTransformationRegistry.match_pattern(sample_values)
            if match:
                transformations[col_name] = match

        return transformations

    def _apply_transformations(self, spark_df, transformations: Dict[str, Tuple[str, str]]):
        """Apply Spark SQL transformations to columns."""
        from pyspark.sql import functions as F

        if not transformations:
            return spark_df

        # Build select expressions
        select_exprs = []
        for col_name in spark_df.columns:
            if col_name in transformations:
                target_type, transform_expr = transformations[col_name]
                # Replace {col} placeholder with actual column reference
                expr = transform_expr.replace("{col}", f"`{col_name}`")
                select_exprs.append(F.expr(expr).alias(col_name))
            else:
                select_exprs.append(F.col(f"`{col_name}`"))

        return spark_df.select(*select_exprs)

    # File-based database types that need native connection (not JDBC)
    FILE_BASED_ADAPTERS = {'duckdb', 'sqlite'}

    def _write_to_file_database(self, spark_df, adapter) -> int:
        """Write DataFrame to file-based database using native connection.

        File-based databases (DuckDB, SQLite) don't handle JDBC writes well
        due to file locking issues. We use native connections via Pandas/Arrow.

        Args:
            spark_df: Spark DataFrame to write
            adapter: The dbt adapter (used for credentials and relation naming)

        Returns:
            Row count written
        """
        adapter_type = adapter.type()
        credentials = adapter.config.credentials

        # Convert Spark DataFrame to Pandas
        pdf = spark_df.toPandas()
        row_count = len(pdf)

        if adapter_type == 'duckdb':
            # Get DuckDB path from credentials
            db_path = getattr(credentials, 'path', None) or getattr(credentials, 'database', None)
            if not db_path:
                raise ValueError("DuckDB path not found in credentials")

            # Expand user path
            db_path = str(Path(db_path).expanduser())

            # Get schema and table name
            schema = self.node.schema or 'main'
            table_name = self.node.alias or self.node.name

            # Connect and write using DuckDB's native connection
            conn = duckdb.connect(db_path)
            try:
                # Create schema if needed
                conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
                # Write DataFrame (replace if exists)
                full_table = f"{schema}.{table_name}"
                conn.execute(f"DROP TABLE IF EXISTS {full_table}")
                # Register the Pandas DataFrame as a virtual table, then create from it
                conn.register('_dvt_seed_data', pdf)
                conn.execute(f"CREATE TABLE {full_table} AS SELECT * FROM _dvt_seed_data")
                conn.unregister('_dvt_seed_data')
                conn.commit()
            finally:
                conn.close()

        elif adapter_type == 'sqlite':
            import sqlite3

            db_path = getattr(credentials, 'database', None)
            if not db_path:
                raise ValueError("SQLite database path not found in credentials")

            db_path = str(Path(db_path).expanduser())
            table_name = self.node.alias or self.node.name

            conn = sqlite3.connect(db_path)
            try:
                pdf.to_sql(table_name, conn, if_exists='replace', index=False)
            finally:
                conn.close()

        return row_count

    def _drop_table_cascade(self, adapter, relation) -> None:
        """Drop a table/view with CASCADE to handle dependent objects.

        Network databases like PostgreSQL may have views depending on tables.
        We need to drop with CASCADE before overwriting.

        Args:
            adapter: The dbt adapter
            relation: The relation to drop
        """
        adapter_type = adapter.type()
        target_table = relation.render()

        # Get a raw connection from the adapter
        with adapter.connection_named('drop_cascade'):
            conn = adapter.connections.get_thread_connection()
            if conn and conn.handle:
                try:
                    # Use raw connection to execute DROP CASCADE
                    cursor = conn.handle.cursor()
                    # Try both TABLE and VIEW
                    for obj_type in ['TABLE', 'VIEW']:
                        try:
                            drop_sql = f"DROP {obj_type} IF EXISTS {target_table} CASCADE"
                            cursor.execute(drop_sql)
                        except Exception:
                            pass
                    conn.handle.commit()
                except Exception:
                    # Ignore errors - table may not exist
                    pass

    def _write_to_target(self, spark_df, adapter) -> int:
        """Write DataFrame to target database using the appropriate method.

        DVT v0.59.0a34: Hybrid approach:
        - File-based databases (DuckDB): Native connection via Pandas/Arrow
        - Network databases (Postgres, etc.): Spark JDBC with DROP CASCADE

        Args:
            spark_df: Spark DataFrame to write
            adapter: The dbt adapter (used for credentials and relation naming)

        Returns:
            Row count written
        """
        adapter_type = adapter.type()

        # Check if this is a file-based database
        if adapter_type in self.FILE_BASED_ADAPTERS:
            return self._write_to_file_database(spark_df, adapter)

        # Network database - use Spark JDBC
        from dbt.compute.jdbc_utils import build_jdbc_config

        credentials = adapter.config.credentials

        # Use adapter's Relation class for proper naming and quoting
        relation = adapter.Relation.create_from(self.config, self.node)

        # Get target table name using adapter's rendering
        target_table = relation.render()

        # Drop with CASCADE before write (handles dependent views)
        self._drop_table_cascade(adapter, relation)

        # Build JDBC config using DVT's unified infrastructure
        jdbc_url, jdbc_properties = build_jdbc_config(credentials)

        # Count rows before write
        row_count = spark_df.count()

        # Write to target via Spark JDBC
        spark_df.write \
            .mode("overwrite") \
            .jdbc(jdbc_url, target_table, properties=jdbc_properties)

        return row_count

    def execute(self, model, manifest):
        """Execute seed loading with Spark and pattern transformations."""
        start_time = time.time()

        try:
            # Get seed file path
            seed_path = self._get_seed_path()

            # Read CSV with Spark
            spark = self._get_spark_session()
            spark_df = spark.read \
                .option("header", "true") \
                .option("inferSchema", "false") \
                .csv(str(seed_path))

            # Detect and apply transformations
            transformations = self._detect_transformations(spark_df)
            spark_df = self._apply_transformations(spark_df, transformations)

            # Write to target using unified JDBC
            adapter = get_adapter(self.config)
            row_count = self._write_to_target(spark_df, adapter)

            execution_time = time.time() - start_time

            # Build result
            return RunResult(
                status=RunStatus.Success,
                timing=[],
                thread_id="",
                execution_time=execution_time,
                adapter_response={},
                message=f"INSERT {row_count}",
                failures=None,
                node=model,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return RunResult(
                status=RunStatus.Error,
                timing=[],
                thread_id="",
                execution_time=execution_time,
                adapter_response={},
                message=str(e),
                failures=1,
                node=model,
            )

    def compile(self, manifest):
        return self.node

    def print_result_line(self, result):
        group = group_lookup.get(self.node.unique_id)
        level = EventLevel.ERROR if result.status == NodeStatus.Error else EventLevel.INFO
        fire_event(
            LogSeedResult(
                status=result.status,
                result_message=result.message,
                index=self.node_index,
                total=self.num_nodes,
                execution_time=result.execution_time,
                schema=self.node.schema,
                relation=self.node.alias,
                node_info=self.node.node_info,
                group=group,
            ),
            level=level,
        )


class DVTSeedTask(RunTask):
    """DVT Seed Task - Enhanced seed loading with Spark and multi-bar Rich UI.

    DVT v0.59.0a37: Header displays BEFORE execution via before_run() hook.
    - File-based databases: NATIVE (DuckDB, SQLite)
    - Network databases: SPARK-JDBC (Postgres, Snowflake, etc.)
    """

    # File-based databases use native connections (not JDBC)
    FILE_BASED_ADAPTERS = {'duckdb', 'sqlite'}

    def __init__(self, args, config, manifest):
        super().__init__(args, config, manifest)
        self._display: Optional[DVTMultiBarDisplay] = None
        self._adapter_type = None
        self._use_rich_output = HAS_RICH and not getattr(args, 'QUIET', False)
        self._spark_logger = None
        self._header_displayed = False

    def raise_on_first_error(self) -> bool:
        return False

    def get_node_selector(self):
        if self.manifest is None or self.graph is None:
            raise DbtInternalError("manifest and graph must be set to perform node selection")
        return ResourceTypeSelector(
            graph=self.graph,
            manifest=self.manifest,
            previous_state=self.previous_state,
            resource_types=[NodeType.Seed],
        )

    def get_runner_type(self, _):
        return DVTSeedRunner

    def _get_execution_path(self) -> str:
        """Determine execution path based on adapter type."""
        if self._adapter_type is None:
            try:
                if self.config is None:
                    raise ValueError("config is None")
                credentials = self.config.credentials
                if credentials is None:
                    raise ValueError("credentials is None")
                self._adapter_type = getattr(credentials, 'type', None)
                if not self._adapter_type:
                    adapter = get_adapter(self.config)
                    self._adapter_type = adapter.type()
            except Exception:
                self._adapter_type = 'unknown'

        if self._adapter_type in self.FILE_BASED_ADAPTERS:
            return "NATIVE"
        return "SPARK-JDBC"

    def _get_target_info(self) -> str:
        """Get the current target name for display."""
        cli_target = getattr(self.config.args, 'TARGET', None)
        return cli_target or self.config.target_name or "default"

    def _get_compute_info(self) -> str:
        """Get the current compute engine for display."""
        exec_path = self._get_execution_path()
        if exec_path == "NATIVE":
            return "native"
        cli_compute = getattr(self.config.args, 'TARGET_COMPUTE', None)
        return cli_compute or "spark-local"

    def _start_spark_logger(self) -> None:
        """Start Spark output logging to target directory.

        Note: suppress_console=False so dbt's event output flows normally.
        Spark output is tee'd to the log file for later reference.
        """
        import os
        try:
            from dbt.compute.spark_logger import get_spark_logger
            target_dir = os.path.join(os.getcwd(), "target")
            compute_name = self._get_compute_info().replace("-", "_")
            self._spark_logger = get_spark_logger(target_dir, compute_name)
            # Don't suppress console - let dbt events flow normally
            self._spark_logger.start_session(suppress_console=False)
        except Exception:
            self._spark_logger = None

    def _stop_spark_logger(self) -> None:
        """Stop Spark output logging."""
        if self._spark_logger:
            try:
                self._spark_logger.end_session()
            except Exception:
                pass
            self._spark_logger = None

    def before_run(self, adapter, selected_uids):
        """
        Called BEFORE model execution starts - this is where we show the header.

        DVT v0.59.0a38: Fixed header timing to display BEFORE execution.
        The before_run() hook is called after 'Concurrency: X threads' message
        but before any models start executing.
        """
        result = super().before_run(adapter, selected_uids)

        # Show header BEFORE execution (only once)
        if self._use_rich_output and not self._header_displayed:
            try:
                exec_path = self._get_execution_path()
                self._display = DVTMultiBarDisplay(
                    title="DVT Seed",
                    operation="seed",
                    target=self._get_target_info(),
                    compute=self._get_compute_info(),
                )
                self._display.start_display()
                self._header_displayed = True

                # Start Spark logging AFTER header is shown
                if exec_path != "NATIVE":
                    self._start_spark_logger()
            except Exception:
                self._display = None

        return result

    def run(self):
        """Override run to add Rich UI summary AFTER execution.

        DVT v0.59.0a38: Header is now displayed in before_run() hook.
        This method only handles summary display after execution completes.
        """
        # Run the parent implementation
        # Header is shown in before_run(), Spark logger started there too
        results = super().run()

        # Stop Spark logging FIRST so we can print to console
        self._stop_spark_logger()

        # Show summary AFTER execution
        exec_path = self._get_execution_path()
        if results and self._display:
            try:
                # Update stats from results
                for result in results:
                    if result.node:
                        duration_ms = (result.execution_time or 0) * 1000

                        if result.status == RunStatus.Success:
                            status = "pass"
                            error_msg = None
                        elif result.status == RunStatus.Error:
                            status = "error"
                            error_msg = result.message
                        else:
                            status = "skip"
                            error_msg = None

                        self._display.update_model_complete(
                            unique_id=result.node.unique_id,
                            status=status,
                            duration_ms=duration_ms,
                            execution_path=exec_path,
                            error_message=error_msg,
                        )

                self._display.stop_display()
                self._display.print_summary()

            except Exception:
                pass

        return results

    def task_end_messages(self, results) -> None:
        # Rich UI handles the summary, so we skip the default messages
        if self._display:
            return
        super().task_end_messages(results)
