"""
DVT Profile Task

Data profiling task with DAG-based execution for sources and models.
Works like 'dvt run' with full selector support and DVT compute rules.

v0.56.0: Initial implementation with 4 profiling modes.
v0.58.1: PipeRider-style profiling - fast SQL-based metrics instead of ydata-profiling.
v0.58.7: Simplified to single comprehensive mode, added --sample flag for row sampling.

Features:
- Profiles ALL columns with comprehensive metrics
- Supports sampling: --sample 10000 (row count) or --sample 10% (percentage)
- PipeRider-style CLI output with column details
- Stores results in .dvt/metadata_store.duckdb

PipeRider-Style Metrics:
- row_count, column_count
- null_count, null_percent
- distinct_count, distinct_percent
- min, max, mean, median, stddev
- top_values (most frequent)
- percentiles (p25, p50, p75)
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import click

# Try to import Rich for beautiful CLI output
try:
    from rich.console import Console
    from rich.progress import (
        Progress,
        TextColumn,
        BarColumn,
        MofNCompleteColumn,
        TimeElapsedColumn,
        SpinnerColumn,
        TaskProgressColumn,
    )
    from rich.table import Table
    from rich import box
    from rich.panel import Panel
    from rich.style import Style
    from rich.live import Live
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from dbt.artifacts.schemas.run import RunStatus
from dbt.config.runtime import RuntimeConfig
from dbt.contracts.graph.manifest import Manifest
from dbt.contracts.graph.nodes import SourceDefinition, ModelNode
from dbt.task.base import BaseTask

# Initialize Rich console
console = Console() if HAS_RICH else None


@dataclass
class ColumnProfile:
    """
    Profile result for a single column (PipeRider-style metrics).

    PipeRider Metric Names (exact copy from piperider_cli/profiler/profiler.py):
    - total: Total row count in table
    - samples: Number of sampled rows (same as total if no sampling)
    - samples_p: Sampling percentage (1.0 = 100%)
    - non_nulls: Count of non-null values
    - non_nulls_p: Percentage of non-null values
    - nulls: Count of null values
    - nulls_p: Percentage of null values
    - valids: Count of valid values (non-null, parseable)
    - valids_p: Percentage of valid values
    - invalids: Count of invalid values
    - invalids_p: Percentage of invalid values
    - distinct: Count of distinct values
    - distinct_p: Percentage of distinct values
    - duplicates: Count of duplicate values
    - duplicates_p: Percentage of duplicate values
    - non_duplicates: Count of non-duplicate (unique) values
    - non_duplicates_p: Percentage of non-duplicate values
    - min: Minimum value
    - max: Maximum value
    - sum: Sum (numeric only)
    - avg: Average/mean (numeric only)
    - stddev: Standard deviation (numeric only)
    - p5, p25, p50, p75, p95: Percentiles (numeric only)
    - zeros, zeros_p: Zero values (numeric only)
    - negatives, negatives_p: Negative values (numeric only)
    - positives, positives_p: Positive values (numeric only)
    - min_length, max_length, avg_length: String length stats
    - zero_length, zero_length_p: Empty strings
    - topk: Top K values with counts
    - histogram: Distribution histogram
    """
    # Column identity
    name: str  # PipeRider uses 'name' not 'column_name'
    type: str  # PipeRider uses 'type' (generic: string, integer, numeric, datetime, boolean, other)
    schema_type: str = ""  # Original database type (VARCHAR, INTEGER, etc.)

    # Core metrics (PipeRider exact names)
    total: Optional[int] = None  # Set from table row_count
    samples: int = 0  # Number of sampled rows
    samples_p: Optional[float] = None  # Sampling percentage

    # Null metrics
    non_nulls: int = 0
    non_nulls_p: Optional[float] = None
    nulls: int = 0
    nulls_p: Optional[float] = None

    # Validity metrics
    valids: int = 0
    valids_p: Optional[float] = None
    invalids: int = 0
    invalids_p: Optional[float] = None

    # Distinct/uniqueness metrics
    distinct: int = 0
    distinct_p: Optional[float] = None
    duplicates: int = 0
    duplicates_p: Optional[float] = None
    non_duplicates: int = 0
    non_duplicates_p: Optional[float] = None

    # Numeric statistics
    min: Optional[float] = None
    max: Optional[float] = None
    sum: Optional[float] = None
    avg: Optional[float] = None
    stddev: Optional[float] = None

    # Percentiles (numeric)
    p5: Optional[float] = None
    p25: Optional[float] = None
    p50: Optional[float] = None
    p75: Optional[float] = None
    p95: Optional[float] = None

    # Numeric sign distribution
    zeros: int = 0
    zeros_p: Optional[float] = None
    negatives: int = 0
    negatives_p: Optional[float] = None
    positives: int = 0
    positives_p: Optional[float] = None

    # String length metrics
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    avg_length: Optional[float] = None
    stddev_length: Optional[float] = None
    zero_length: int = 0
    zero_length_p: Optional[float] = None
    non_zero_length: int = 0
    non_zero_length_p: Optional[float] = None

    # Boolean metrics
    trues: int = 0
    trues_p: Optional[float] = None
    falses: int = 0
    falses_p: Optional[float] = None

    # Distribution data (PipeRider format)
    topk: Optional[Dict] = None  # {"values": [...], "counts": [...]}
    histogram: Optional[Dict] = None  # {"labels": [...], "counts": [...], "bin_edges": [...]}
    histogram_length: Optional[Dict] = None  # For string length distribution

    # Quality alerts (PipeRider format)
    alerts: List[Dict] = field(default_factory=list)

    # Profiling metadata
    profile_duration: Optional[str] = None  # "1.23" seconds
    elapsed_milli: int = 0  # Duration in milliseconds

    # Legacy aliases for backward compatibility
    @property
    def column_name(self) -> str:
        return self.name

    @property
    def data_type(self) -> str:
        return self.type

    @property
    def row_count(self) -> int:
        return self.samples

    @property
    def null_count(self) -> int:
        return self.nulls

    @property
    def null_percent(self) -> float:
        return (self.nulls_p or 0.0) * 100

    @property
    def distinct_count(self) -> int:
        return self.distinct

    @property
    def distinct_percent(self) -> float:
        return (self.distinct_p or 0.0) * 100

    @property
    def duration_ms(self) -> int:
        return self.elapsed_milli


@dataclass
class TableProfile:
    """Profile result for a table."""
    source_name: str
    table_name: str
    connection_name: str
    row_count: int
    column_count: int
    columns: List[ColumnProfile]
    profile_mode: str
    profiled_at: datetime
    duration_ms: int
    alerts: List[Dict] = field(default_factory=list)
    status: str = "success"
    error: Optional[str] = None


@dataclass
class ProfileExecutionResult:
    """Result of profile execution."""
    tables_profiled: int = 0
    total_rows: int = 0
    total_columns: int = 0
    total_alerts: int = 0
    duration_ms: int = 0
    profiles: List[TableProfile] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class ProfileTask(BaseTask):
    """
    DAG-based profiling task for DVT (PipeRider-style).

    v0.58.1: Uses fast SQL-based profiling queries instead of slow ydata-profiling.

    Execution flow:
    1. Parse selectors (--select, --exclude)
    2. Build execution list (sources + models)
    3. For each node:
       a. Execute efficient SQL profiling queries
       b. Collect PipeRider-style metrics
       c. Store results in metadata_store.duckdb
    4. Display summary (PipeRider-style)
    """

    def __init__(
        self,
        flags: Any,
        runtime_config: RuntimeConfig,
        manifest: Manifest,
    ):
        super().__init__(flags)  # BaseTask only takes flags, sets self.args
        self.runtime_config = runtime_config
        self.manifest = manifest
        # v0.58.7: Use lowercase parameter names (fixed from uppercase)
        self._sample_str = getattr(self.args, "sample", None)
        self._threads = getattr(self.args, "threads", 4) or 4

    def _parse_sample(self, sample_str: Optional[str], total_rows: int) -> int:
        """Parse sample string into row count.

        Args:
            sample_str: Sample specification (e.g., "10000" or "10%")
            total_rows: Total rows in the table

        Returns:
            Number of rows to sample
        """
        if not sample_str:
            return total_rows
        sample_str = sample_str.strip()
        if sample_str.endswith('%'):
            pct = float(sample_str[:-1]) / 100
            return max(1, int(total_rows * pct))
        return min(int(sample_str), total_rows)

    def run(self) -> ProfileExecutionResult:
        """Execute profiling on selected sources and models."""
        start_time = time.time()
        result = ProfileExecutionResult()

        # Build sample display string
        sample_display = self._sample_str if self._sample_str else "all rows"

        # Print header with Rich Panel
        if HAS_RICH:
            console.print()
            header_panel = Panel(
                f"[bold cyan]Sample:[/bold cyan] [yellow]{sample_display}[/yellow]  |  "
                f"[bold cyan]Threads:[/bold cyan] [yellow]{self._threads}[/yellow]",
                title="[bold magenta]DVT Profile - Data Profiling[/bold magenta]",
                subtitle="[dim]PipeRider-style fast SQL profiling[/dim]",
                border_style="magenta",
                box=box.DOUBLE,
            )
            console.print(header_panel)
            console.print()
        else:
            print("\n" + "=" * 60)
            print("  DVT Profile - Data Profiling")
            print(f"  Sample: {sample_display} | Threads: {self._threads}")
            print("=" * 60 + "\n")

        # Get selected nodes
        nodes = self._get_selected_nodes()

        if not nodes:
            if HAS_RICH:
                console.print("[yellow]No sources or models selected for profiling.[/yellow]")
                console.print("[dim]Use --select to specify targets, e.g.: dvt profile run --select 'source:*'[/dim]")
            else:
                print("No sources or models selected for profiling.")
            return result

        # Profile with progress display
        if HAS_RICH:
            result = self._profile_with_progress(nodes, result)
        else:
            result = self._profile_without_progress(nodes, result)

        # Calculate duration
        result.duration_ms = int((time.time() - start_time) * 1000)

        # Print summary
        self._print_summary(result)

        return result

    def _profile_with_progress(self, nodes: List[Any], result: ProfileExecutionResult) -> ProfileExecutionResult:
        """Profile nodes with Rich progress display."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            main_task = progress.add_task("[cyan]Profiling...", total=len(nodes))

            # Profile each node
            for i, node in enumerate(nodes, 1):
                node_name = self._get_node_display_name(node)
                progress.update(main_task, description=f"[cyan]Profiling[/cyan] [bold]{node_name}[/bold]")

                profile = self._profile_node(node, i, len(nodes))
                if profile:
                    result.profiles.append(profile)
                    result.tables_profiled += 1
                    result.total_rows += profile.row_count
                    result.total_columns += profile.column_count
                    result.total_alerts += len(profile.alerts)
                    for col in profile.columns:
                        result.total_alerts += len(col.alerts)

                    # Store in metadata_store.duckdb
                    self._store_profile(profile)

                    # Show result line
                    status_icon = "[green]OK[/green]" if profile.status == "success" else "[red]FAIL[/red]"
                    console.print(
                        f"  {status_icon} {node_name} "
                        f"[dim]({profile.row_count:,} rows, {profile.column_count} cols, {profile.duration_ms}ms)[/dim]"
                    )

                    # Show detailed column profile (PipeRider-style)
                    self._print_table_profile(profile)

                progress.advance(main_task)

        return result

    def _profile_without_progress(self, nodes: List[Any], result: ProfileExecutionResult) -> ProfileExecutionResult:
        """Profile nodes without Rich (fallback)."""
        for i, node in enumerate(nodes, 1):
            node_name = self._get_node_display_name(node)
            print(f"  [{i}/{len(nodes)}] Profiling {node_name}...")

            profile = self._profile_node(node, i, len(nodes))
            if profile:
                result.profiles.append(profile)
                result.tables_profiled += 1
                result.total_rows += profile.row_count
                result.total_columns += profile.column_count

                self._store_profile(profile)

                status = "OK" if profile.status == "success" else "FAIL"
                print(f"       {status} ({profile.row_count:,} rows, {profile.column_count} cols)")

                # Show detailed column profile (text fallback)
                self._print_table_profile(profile)

        return result

    def _get_selected_nodes(self) -> List[Any]:
        """Get list of nodes to profile based on selectors."""
        nodes = []

        # v0.58.7: Use lowercase parameter names (fixed from uppercase)
        selector = getattr(self.args, "select", None)
        exclude = getattr(self.args, "exclude", None)

        if not selector:
            # Default: profile all sources
            for source_id, source in self.manifest.sources.items():
                nodes.append(source)
        else:
            # Parse selection
            for sel in selector:
                if isinstance(sel, tuple):
                    for s in sel:
                        nodes.extend(self._parse_selector(s))
                else:
                    nodes.extend(self._parse_selector(sel))

        # Apply exclusions
        if exclude:
            excluded = set()
            for exc in exclude:
                if isinstance(exc, tuple):
                    for e in exc:
                        excluded.update(self._get_excluded_ids(e))
                else:
                    excluded.update(self._get_excluded_ids(exc))
            nodes = [n for n in nodes if self._get_node_id(n) not in excluded]

        return nodes

    def _parse_selector(self, selector: str) -> List[Any]:
        """Parse a selector string into nodes."""
        nodes = []

        if selector.startswith("source:"):
            # Source selector: source:* or source:postgres.*
            pattern = selector[7:]  # Remove "source:" prefix
            for source_id, source in self.manifest.sources.items():
                if self._matches_pattern(source, pattern):
                    nodes.append(source)

        elif selector.startswith("model:"):
            # Model selector: model:* or model:staging.*
            pattern = selector[6:]  # Remove "model:" prefix
            for node_id, node in self.manifest.nodes.items():
                if hasattr(node, "resource_type") and node.resource_type.value == "model":
                    if self._matches_pattern(node, pattern):
                        nodes.append(node)

        elif "*" in selector:
            # Wildcard - match both sources and models
            pattern = selector
            for source_id, source in self.manifest.sources.items():
                if self._matches_pattern(source, pattern):
                    nodes.append(source)
            for node_id, node in self.manifest.nodes.items():
                if hasattr(node, "resource_type") and node.resource_type.value == "model":
                    if self._matches_pattern(node, pattern):
                        nodes.append(node)

        else:
            # Exact match by name
            for source_id, source in self.manifest.sources.items():
                if source.name == selector or source.identifier == selector:
                    nodes.append(source)
            for node_id, node in self.manifest.nodes.items():
                if hasattr(node, "name") and node.name == selector:
                    nodes.append(node)

        return nodes

    def _matches_pattern(self, node: Any, pattern: str) -> bool:
        """Check if a node matches a glob pattern."""
        import fnmatch

        if pattern == "*":
            return True

        name = getattr(node, "name", "")
        identifier = getattr(node, "identifier", name)
        source_name = getattr(node, "source_name", "")
        unique_id = getattr(node, "unique_id", "")

        # Try matching against different attributes
        full_name = f"{source_name}.{identifier}" if source_name else identifier

        # Extract just the source_name.table portion from unique_id
        # unique_id format: source.project_name.source_name.table_name
        # We want to match against: project_name.source_name.table_name
        parts = unique_id.split(".")
        if len(parts) >= 4 and parts[0] == "source":
            # project_name.source_name.table_name
            project_source_table = ".".join(parts[1:])
            source_table = ".".join(parts[2:])  # source_name.table_name
        else:
            project_source_table = unique_id
            source_table = full_name

        return (
            fnmatch.fnmatch(name, pattern) or
            fnmatch.fnmatch(identifier, pattern) or
            fnmatch.fnmatch(full_name, pattern) or
            fnmatch.fnmatch(project_source_table, pattern) or
            fnmatch.fnmatch(source_table, pattern) or
            fnmatch.fnmatch(unique_id, pattern)
        )

    def _get_excluded_ids(self, exclude_str: str) -> Set[str]:
        """Get IDs of nodes matching exclusion pattern."""
        ids = set()
        nodes = self._parse_selector(exclude_str)
        for node in nodes:
            ids.add(self._get_node_id(node))
        return ids

    def _get_node_id(self, node: Any) -> str:
        """Get unique ID for a node."""
        if hasattr(node, "unique_id"):
            return node.unique_id
        return getattr(node, "name", str(node))

    def _get_node_display_name(self, node: Any) -> str:
        """Get display name for a node."""
        if isinstance(node, SourceDefinition):
            return f"{node.source_name}.{node.identifier}"
        else:
            return getattr(node, "name", str(node))

    def _profile_node(self, node: Any, index: int, total: int) -> Optional[TableProfile]:
        """Profile a single node (source or model)."""
        start_time = time.time()

        # Get node info
        if isinstance(node, SourceDefinition):
            source_name = node.source_name
            table_name = node.identifier
            connection_name = getattr(node, "config", {}).get("target", "default")
            node_type = "source"
        else:
            source_name = "models"
            table_name = node.name
            connection_name = getattr(node.config, "target", "default") if hasattr(node, "config") else "default"
            node_type = "model"

        try:
            # Execute profiling
            columns = self._execute_profile(node)

            duration_ms = int((time.time() - start_time) * 1000)

            # Calculate totals - use samples field (actual profiled rows)
            row_count = columns[0].samples if columns else 0
            total_rows = columns[0].total if columns else 0

            # Collect alerts
            alerts = []
            for col in columns:
                alerts.extend(col.alerts)

            profile = TableProfile(
                source_name=source_name,
                table_name=table_name,
                connection_name=connection_name,
                row_count=total_rows,  # Total rows in table
                column_count=len(columns),
                columns=columns,
                profile_mode="standard",  # v0.58.7: Single standard mode
                profiled_at=datetime.now(),
                duration_ms=duration_ms,
                alerts=alerts,
                status="success",
            )

            return profile

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return TableProfile(
                source_name=source_name,
                table_name=table_name,
                connection_name=connection_name,
                row_count=0,
                column_count=0,
                columns=[],
                profile_mode="standard",  # v0.58.7: Single standard mode
                profiled_at=datetime.now(),
                duration_ms=duration_ms,
                status="error",
                error=str(e),
            )

    def _execute_profile(self, node: Any) -> List[ColumnProfile]:
        """
        Execute PipeRider-style profiling queries on a node.

        Uses efficient SQL queries to compute:
        - row_count, null_count, distinct_count
        - min, max, mean, stddev (numeric)
        - min_length, max_length, avg_length (string)
        - top_values (categorical)

        v0.58.7: Added sampling support via --sample flag.
        """
        columns = []

        # Get table info
        if isinstance(node, SourceDefinition):
            schema = node.schema
            table = node.identifier
            database = getattr(node, "database", None)
            target_name = node.config.get("target") if hasattr(node, "config") else None
        else:
            schema = node.schema
            table = node.alias or node.name
            database = getattr(node, "database", None)
            target_name = getattr(node.config, "target", None) if hasattr(node, "config") else None

        # Get adapter for connection
        adapter = self._get_adapter(target_name)

        # Get column info - either from node definition or by querying database
        node_columns = getattr(node, "columns", {})

        if not node_columns:
            # Query database for column info
            column_info = self._get_columns_from_db(adapter, database, schema, table)
        else:
            column_info = [
                (col_name, getattr(col_info, "data_type", "VARCHAR") or "VARCHAR")
                for col_name, col_info in node_columns.items()
            ]

        if not column_info:
            # Fallback: profile as single row count only
            row_count = self._get_row_count(adapter, database, schema, table)
            return [ColumnProfile(
                name="_table_",
                type="TABLE",
                schema_type="TABLE",
                total=row_count,
                samples=row_count,
            )]

        # Get row count once for all columns
        total_row_count = self._get_row_count(adapter, database, schema, table)

        # v0.58.7: Calculate sample size
        sample_row_count = self._parse_sample(self._sample_str, total_row_count)
        is_sampling = sample_row_count < total_row_count

        # Profile columns in parallel using threads
        if self._threads > 1 and len(column_info) > 1:
            with ThreadPoolExecutor(max_workers=min(self._threads, len(column_info))) as executor:
                futures = {
                    executor.submit(
                        self._profile_column_sql,
                        adapter, database, schema, table,
                        col_name, col_type, total_row_count, sample_row_count
                    ): (col_name, col_type)
                    for col_name, col_type in column_info
                }
                for future in as_completed(futures):
                    try:
                        profile = future.result()
                        columns.append(profile)
                    except Exception as e:
                        col_name, col_type = futures[future]
                        columns.append(ColumnProfile(
                            name=col_name,
                            type=self._classify_type(col_type),
                            schema_type=col_type,
                            total=total_row_count,
                            samples=sample_row_count,
                            alerts=[{"type": "PROFILE_ERROR", "severity": "warning", "message": str(e)[:100]}]
                        ))
        else:
            # Sequential profiling
            for col_name, col_type in column_info:
                profile = self._profile_column_sql(
                    adapter, database, schema, table,
                    col_name, col_type, total_row_count, sample_row_count
                )
                columns.append(profile)

        return columns

    def _get_adapter(self, target_name: Optional[str] = None):
        """Get adapter for the specified target or default."""
        from dbt.adapters.factory import get_adapter

        # Get adapter from runtime config
        adapter = get_adapter(self.runtime_config)
        return adapter

    def _get_columns_from_db(
        self, adapter, database: Optional[str], schema: str, table: str
    ) -> List[tuple]:
        """Query database to get column names and types."""
        try:
            # Use adapter's get_columns_in_relation
            from dbt.adapters.base import BaseRelation

            relation = adapter.Relation.create(
                database=database,
                schema=schema,
                identifier=table,
            )

            with adapter.connection_named("profile"):
                columns = adapter.get_columns_in_relation(relation)
                return [(col.name, col.dtype) for col in columns]
        except Exception:
            return []

    def _get_row_count(
        self, adapter, database: Optional[str], schema: str, table: str
    ) -> int:
        """Get row count from table."""
        try:
            fqn = self._build_fqn(adapter, database, schema, table)
            sql = f"SELECT COUNT(*) as cnt FROM {fqn}"

            with adapter.connection_named("profile"):
                _, result = adapter.execute(sql, fetch=True)
                if result and len(result) > 0:
                    return int(result[0][0])
        except Exception:
            pass
        return 0

    def _build_fqn(
        self, adapter, database: Optional[str], schema: str, table: str
    ) -> str:
        """Build fully qualified table name."""
        parts = []
        if database:
            parts.append(adapter.quote(database))
        if schema:
            parts.append(adapter.quote(schema))
        parts.append(adapter.quote(table))
        return ".".join(parts)

    def _classify_type(self, col_type: str) -> str:
        """Classify database type into PipeRider generic type."""
        col_type_lower = col_type.lower()

        if any(t in col_type_lower for t in ["int", "bigint", "smallint", "tinyint", "serial"]):
            return "integer"
        elif any(t in col_type_lower for t in ["numeric", "decimal", "float", "double", "real", "number"]):
            return "numeric"
        elif any(t in col_type_lower for t in ["char", "varchar", "text", "string", "clob"]):
            return "string"
        elif any(t in col_type_lower for t in ["date", "time", "timestamp"]):
            return "datetime"
        elif any(t in col_type_lower for t in ["bool", "boolean"]):
            return "boolean"
        else:
            return "other"

    def _profile_column_sql(
        self, adapter, database: Optional[str], schema: str, table: str,
        col_name: str, col_type: str, total_row_count: int, sample_row_count: int
    ) -> ColumnProfile:
        """
        Profile a single column using efficient SQL queries.

        PipeRider-style: Single-pass or minimal queries for all metrics.
        Uses PipeRider metric names: nulls, non_nulls, distinct, valids, etc.

        v0.58.7: Added sampling support. When sample_row_count < total_row_count,
        SQL queries will use LIMIT clause to sample rows.

        Args:
            adapter: Database adapter
            database: Database name
            schema: Schema name
            table: Table name
            col_name: Column name to profile
            col_type: Column data type
            total_row_count: Total rows in the table
            sample_row_count: Number of rows to sample (may equal total_row_count)
        """
        start_time = time.time()

        generic_type = self._classify_type(col_type)
        is_sampling = sample_row_count < total_row_count
        profile = ColumnProfile(
            name=col_name,
            type=generic_type,
            schema_type=col_type,
            total=total_row_count,
            samples=sample_row_count,
            samples_p=sample_row_count / total_row_count if total_row_count > 0 else 1.0,
        )

        fqn = self._build_fqn(adapter, database, schema, table)
        quoted_col = adapter.quote(col_name)

        try:
            # Determine column type category
            col_type_lower = col_type.lower()
            is_numeric = any(t in col_type_lower for t in [
                "int", "numeric", "decimal", "float", "double", "real", "number", "bigint", "smallint"
            ])
            is_string = any(t in col_type_lower for t in [
                "char", "varchar", "text", "string", "clob"
            ])

            # Build comprehensive profiling query based on column type
            if is_numeric:
                profile = self._profile_numeric_column(
                    adapter, fqn, quoted_col, col_name, col_type,
                    total_row_count, sample_row_count
                )
            elif is_string:
                profile = self._profile_string_column(
                    adapter, fqn, quoted_col, col_name, col_type,
                    total_row_count, sample_row_count
                )
            else:
                # Default: basic metrics only
                profile = self._profile_basic_column(
                    adapter, fqn, quoted_col, col_name, col_type,
                    total_row_count, sample_row_count
                )

            # Get top values for categorical columns
            if profile.distinct and profile.distinct <= 100:
                self._add_top_values(adapter, fqn, quoted_col, profile, sample_row_count)

        except Exception as e:
            # If SQL fails, return what we have
            profile.alerts.append({
                "type": "PROFILE_ERROR",
                "severity": "warning",
                "message": f"Could not profile column: {str(e)[:100]}",
            })

        # Generate quality alerts
        profile.alerts.extend(self._generate_alerts(profile))

        profile.elapsed_milli = int((time.time() - start_time) * 1000)
        profile.profile_duration = f"{(time.time() - start_time):.2f}"
        return profile

    def _profile_numeric_column(
        self, adapter, fqn: str, quoted_col: str, col_name: str, col_type: str,
        total_row_count: int, sample_row_count: int
    ) -> ColumnProfile:
        """Profile a numeric column with all stats in one query (PipeRider-style).

        v0.58.7: Added sampling support via subquery when sample_row_count < total_row_count.
        """
        generic_type = self._classify_type(col_type)
        is_sampling = sample_row_count < total_row_count
        profile = ColumnProfile(
            name=col_name,
            type=generic_type,
            schema_type=col_type,
            total=total_row_count,
            samples=sample_row_count,
            samples_p=sample_row_count / total_row_count if total_row_count > 0 else 1.0,
        )

        # Build source expression - use subquery with LIMIT when sampling
        if is_sampling:
            source_expr = f"(SELECT * FROM {fqn} LIMIT {sample_row_count}) AS sampled"
        else:
            source_expr = fqn

        # Single comprehensive query for numeric columns (PipeRider-style)
        sql = f"""
            SELECT
                COUNT(*) - COUNT({quoted_col}) as nulls,
                COUNT({quoted_col}) as non_nulls,
                COUNT(DISTINCT {quoted_col}) as distinct_val,
                MIN({quoted_col}) as min_val,
                MAX({quoted_col}) as max_val,
                SUM(CAST({quoted_col} AS DOUBLE PRECISION)) as sum_val,
                AVG(CAST({quoted_col} AS DOUBLE PRECISION)) as avg_val,
                STDDEV(CAST({quoted_col} AS DOUBLE PRECISION)) as stddev_val,
                SUM(CASE WHEN {quoted_col} = 0 THEN 1 ELSE 0 END) as zeros,
                SUM(CASE WHEN {quoted_col} < 0 THEN 1 ELSE 0 END) as negatives,
                SUM(CASE WHEN {quoted_col} > 0 THEN 1 ELSE 0 END) as positives
            FROM {source_expr}
        """

        try:
            with adapter.connection_named("profile"):
                _, result = adapter.execute(sql, fetch=True)
                if result and len(result) > 0:
                    row = result[0]
                    # PipeRider-style metric names
                    profile.nulls = int(row[0] or 0)
                    profile.non_nulls = int(row[1] or 0)
                    profile.distinct = int(row[2] or 0)
                    profile.min = float(row[3]) if row[3] is not None else None
                    profile.max = float(row[4]) if row[4] is not None else None
                    profile.sum = float(row[5]) if row[5] is not None else None
                    profile.avg = float(row[6]) if row[6] is not None else None
                    profile.stddev = float(row[7]) if row[7] is not None else None
                    profile.zeros = int(row[8] or 0)
                    profile.negatives = int(row[9] or 0)
                    profile.positives = int(row[10] or 0)

            # Calculate percentages based on sampled rows (PipeRider-style with decimal 0-1)
            sampled = profile.samples
            if sampled > 0:
                profile.nulls_p = profile.nulls / sampled
                profile.non_nulls_p = profile.non_nulls / sampled
                profile.distinct_p = profile.distinct / sampled if profile.non_nulls > 0 else None
                profile.zeros_p = profile.zeros / sampled
                profile.negatives_p = profile.negatives / sampled
                profile.positives_p = profile.positives / sampled

            # Validity metrics (for numeric, valid = non-null)
            profile.valids = profile.non_nulls
            profile.valids_p = profile.non_nulls_p
            profile.invalids = profile.nulls
            profile.invalids_p = profile.nulls_p

            # Duplicate metrics
            if profile.non_nulls > 0 and profile.distinct > 0:
                profile.non_duplicates = profile.distinct
                profile.duplicates = profile.non_nulls - profile.distinct
                profile.non_duplicates_p = profile.non_duplicates / profile.non_nulls
                profile.duplicates_p = profile.duplicates / profile.non_nulls

            # Always get percentiles in standard mode (v0.58.7: single comprehensive mode)
            self._add_percentiles(adapter, fqn, quoted_col, profile, sample_row_count)

        except Exception:
            # Fall back to basic profile
            profile = self._profile_basic_column(
                adapter, fqn, quoted_col, col_name, col_type,
                total_row_count, sample_row_count
            )

        return profile

    def _profile_string_column(
        self, adapter, fqn: str, quoted_col: str, col_name: str, col_type: str,
        total_row_count: int, sample_row_count: int
    ) -> ColumnProfile:
        """Profile a string column with all stats in one query (PipeRider-style).

        v0.58.7: Added sampling support via subquery when sample_row_count < total_row_count.
        """
        generic_type = self._classify_type(col_type)
        is_sampling = sample_row_count < total_row_count
        profile = ColumnProfile(
            name=col_name,
            type=generic_type,
            schema_type=col_type,
            total=total_row_count,
            samples=sample_row_count,
            samples_p=sample_row_count / total_row_count if total_row_count > 0 else 1.0,
        )

        # Build source expression - use subquery with LIMIT when sampling
        if is_sampling:
            source_expr = f"(SELECT * FROM {fqn} LIMIT {sample_row_count}) AS sampled"
        else:
            source_expr = fqn

        # Single comprehensive query for string columns (PipeRider-style)
        sql = f"""
            SELECT
                COUNT(*) - COUNT({quoted_col}) as nulls,
                COUNT({quoted_col}) as non_nulls,
                COUNT(DISTINCT {quoted_col}) as distinct_val,
                MIN(LENGTH({quoted_col})) as min_len,
                MAX(LENGTH({quoted_col})) as max_len,
                AVG(LENGTH({quoted_col})) as avg_len,
                SUM(CASE WHEN LENGTH({quoted_col}) = 0 THEN 1 ELSE 0 END) as zero_length_count
            FROM {source_expr}
        """

        try:
            with adapter.connection_named("profile"):
                _, result = adapter.execute(sql, fetch=True)
                if result and len(result) > 0:
                    row = result[0]
                    # PipeRider-style metric names
                    profile.nulls = int(row[0] or 0)
                    profile.non_nulls = int(row[1] or 0)
                    profile.distinct = int(row[2] or 0)
                    profile.min_length = int(row[3]) if row[3] is not None else None
                    profile.max_length = int(row[4]) if row[4] is not None else None
                    profile.avg_length = float(row[5]) if row[5] is not None else None
                    profile.zero_length = int(row[6] or 0)

            # Calculate percentages based on sampled rows (PipeRider-style with decimal 0-1)
            sampled = profile.samples
            if sampled > 0:
                profile.nulls_p = profile.nulls / sampled
                profile.non_nulls_p = profile.non_nulls / sampled
                profile.distinct_p = profile.distinct / sampled if profile.non_nulls > 0 else None
                profile.zero_length_p = profile.zero_length / sampled

            # Validity metrics (for string, valid = non-null non-empty)
            profile.valids = profile.non_nulls - profile.zero_length
            profile.invalids = profile.nulls + profile.zero_length
            if sampled > 0:
                profile.valids_p = profile.valids / sampled
                profile.invalids_p = profile.invalids / sampled

            # Non-zero length
            profile.non_zero_length = profile.non_nulls - profile.zero_length
            if profile.non_nulls > 0:
                profile.non_zero_length_p = profile.non_zero_length / profile.non_nulls

            # Duplicate metrics
            if profile.non_nulls > 0 and profile.distinct > 0:
                profile.non_duplicates = profile.distinct
                profile.duplicates = profile.non_nulls - profile.distinct
                profile.non_duplicates_p = profile.non_duplicates / profile.non_nulls
                profile.duplicates_p = profile.duplicates / profile.non_nulls

        except Exception:
            # Fall back to basic profile
            profile = self._profile_basic_column(
                adapter, fqn, quoted_col, col_name, col_type,
                total_row_count, sample_row_count
            )

        return profile

    def _profile_basic_column(
        self, adapter, fqn: str, quoted_col: str, col_name: str, col_type: str,
        total_row_count: int, sample_row_count: int
    ) -> ColumnProfile:
        """Profile any column with basic metrics only (PipeRider-style).

        v0.58.7: Added sampling support via subquery when sample_row_count < total_row_count.
        """
        generic_type = self._classify_type(col_type)
        is_sampling = sample_row_count < total_row_count
        profile = ColumnProfile(
            name=col_name,
            type=generic_type,
            schema_type=col_type,
            total=total_row_count,
            samples=sample_row_count,
            samples_p=sample_row_count / total_row_count if total_row_count > 0 else 1.0,
        )

        # Build source expression - use subquery with LIMIT when sampling
        if is_sampling:
            source_expr = f"(SELECT * FROM {fqn} LIMIT {sample_row_count}) AS sampled"
        else:
            source_expr = fqn

        sql = f"""
            SELECT
                COUNT(*) - COUNT({quoted_col}) as nulls,
                COUNT({quoted_col}) as non_nulls,
                COUNT(DISTINCT {quoted_col}) as distinct_val
            FROM {source_expr}
        """

        try:
            with adapter.connection_named("profile"):
                _, result = adapter.execute(sql, fetch=True)
                if result and len(result) > 0:
                    profile.nulls = int(result[0][0] or 0)
                    profile.non_nulls = int(result[0][1] or 0)
                    profile.distinct = int(result[0][2] or 0)

            # Calculate percentages based on sampled rows (PipeRider-style with decimal 0-1)
            sampled = profile.samples
            if sampled > 0:
                profile.nulls_p = profile.nulls / sampled
                profile.non_nulls_p = profile.non_nulls / sampled
                profile.distinct_p = profile.distinct / sampled if profile.non_nulls > 0 else None

            # Validity metrics
            profile.valids = profile.non_nulls
            profile.valids_p = profile.non_nulls_p
            profile.invalids = profile.nulls
            profile.invalids_p = profile.nulls_p

            # Duplicate metrics
            if profile.non_nulls > 0 and profile.distinct > 0:
                profile.non_duplicates = profile.distinct
                profile.duplicates = profile.non_nulls - profile.distinct
                profile.non_duplicates_p = profile.non_duplicates / profile.non_nulls
                profile.duplicates_p = profile.duplicates / profile.non_nulls

        except Exception:
            pass

        return profile

    def _add_percentiles(
        self, adapter, fqn: str, quoted_col: str, profile: ColumnProfile,
        sample_row_count: int = None
    ) -> None:
        """Try to add percentiles to numeric profile.

        v0.58.7: Added sampling support via subquery when sample_row_count is provided.
        """
        try:
            # Build source expression for sampling
            if sample_row_count and sample_row_count < profile.total:
                source_expr = f"(SELECT {quoted_col} FROM {fqn} WHERE {quoted_col} IS NOT NULL LIMIT {sample_row_count}) AS sampled"
                where_clause = ""
            else:
                source_expr = fqn
                where_clause = f"WHERE {quoted_col} IS NOT NULL"

            # Try PostgreSQL/Redshift style
            percentile_sql = f"""
                SELECT
                    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {quoted_col}) as p25,
                    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY {quoted_col}) as p50,
                    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {quoted_col}) as p75
                FROM {source_expr}
                {where_clause}
            """
            with adapter.connection_named("profile"):
                _, result = adapter.execute(percentile_sql, fetch=True)
                if result and len(result) > 0:
                    row = result[0]
                    profile.p25 = float(row[0]) if row[0] is not None else None
                    profile.p50 = float(row[1]) if row[1] is not None else None
                    profile.p75 = float(row[2]) if row[2] is not None else None
        except Exception:
            # Percentiles not supported on this database
            pass

    def _add_top_values(
        self, adapter, fqn: str, quoted_col: str, profile: ColumnProfile,
        sample_row_count: int = None
    ) -> None:
        """Add top values to profile (PipeRider topk format).

        v0.58.7: Added sampling support via subquery when sample_row_count is provided.
        """
        try:
            # Build source expression for sampling
            if sample_row_count and sample_row_count < profile.total:
                source_expr = f"(SELECT * FROM {fqn} LIMIT {sample_row_count}) AS sampled"
            else:
                source_expr = fqn

            top_sql = f"""
                SELECT {quoted_col} as val, COUNT(*) as cnt
                FROM {source_expr}
                WHERE {quoted_col} IS NOT NULL
                GROUP BY {quoted_col}
                ORDER BY cnt DESC
                LIMIT 10
            """
            with adapter.connection_named("profile"):
                _, result = adapter.execute(top_sql, fetch=True)
                if result:
                    # PipeRider topk format: {"values": [...], "counts": [...]}
                    values = [str(row[0]) for row in result]
                    counts = [int(row[1]) for row in result]
                    profile.topk = {
                        "values": values,
                        "counts": counts,
                    }
        except Exception:
            pass

    def _generate_alerts(self, profile: ColumnProfile) -> List[Dict]:
        """
        Generate quality alerts for a column profile (PipeRider-style).

        PipeRider alert types (from piperider_cli/profiler/event.py):
        - missing_value: High percentage of null/missing values
        - high_distinct: Very high cardinality (possible PK)
        - low_distinct: Very low cardinality (possible boolean/flag)
        - all_null: 100% null values
        - constant: All values are the same
        - negative_value: Has negative values in numeric column
        - zero_length_string: Has empty strings
        """
        alerts = []

        # Get null percentage (as 0-100 for comparison)
        nulls_pct = (profile.nulls_p or 0) * 100 if profile.nulls_p is not None else 0
        distinct_pct = (profile.distinct_p or 0) * 100 if profile.distinct_p is not None else 0

        # High null rate alert (PipeRider: missing_value)
        if nulls_pct > 50:
            alerts.append({
                "type": "missing_value",
                "severity": "error",
                "column": profile.name,
                "message": f"Column has {nulls_pct:.1f}% null values (>50%)",
            })
        elif nulls_pct > 20:
            alerts.append({
                "type": "missing_value",
                "severity": "warning",
                "column": profile.name,
                "message": f"Column has {nulls_pct:.1f}% null values",
            })

        # High cardinality alert (PipeRider: high_distinct)
        if distinct_pct > 99 and profile.samples > 100:
            alerts.append({
                "type": "high_distinct",
                "severity": "info",
                "column": profile.name,
                "message": f"Column is {distinct_pct:.1f}% unique (possible primary key)",
            })

        # Low cardinality (PipeRider: low_distinct)
        if profile.distinct and profile.distinct < 10 and profile.samples > 1000:
            alerts.append({
                "type": "low_distinct",
                "severity": "info",
                "column": profile.name,
                "message": f"Column has only {profile.distinct} distinct values (possible category)",
            })

        # All nulls alert (PipeRider: all_null)
        if nulls_pct >= 100 or (profile.non_nulls == 0 and profile.nulls > 0):
            alerts.append({
                "type": "all_null",
                "severity": "error",
                "column": profile.name,
                "message": "Column is 100% null - consider removing",
            })

        # Zero variance / Constant alert (PipeRider: constant)
        if profile.min is not None and profile.max is not None:
            if profile.min == profile.max and profile.distinct == 1:
                alerts.append({
                    "type": "constant",
                    "severity": "warning",
                    "column": profile.name,
                    "message": f"Column has constant value: {profile.min}",
                })

        # Negative values (PipeRider: negative_value) - informational only
        if profile.negatives and profile.negatives > 0:
            negatives_pct = (profile.negatives_p or 0) * 100
            if negatives_pct > 50:
                alerts.append({
                    "type": "negative_value",
                    "severity": "info",
                    "column": profile.name,
                    "message": f"Column has {negatives_pct:.1f}% negative values",
                })

        # Zero-length strings (PipeRider: zero_length_string)
        if profile.zero_length and profile.zero_length > 0:
            zero_len_pct = (profile.zero_length_p or 0) * 100
            if zero_len_pct > 10:
                alerts.append({
                    "type": "zero_length_string",
                    "severity": "warning",
                    "column": profile.name,
                    "message": f"Column has {zero_len_pct:.1f}% empty strings",
                })

        return alerts

    def _print_table_profile(self, profile: TableProfile) -> None:
        """Print detailed column profile in PipeRider style.

        v0.58.7: Added column-level display with key metrics.
        """
        if not profile.columns:
            return

        if HAS_RICH:
            # Rich table for column details
            table = Table(
                box=box.SIMPLE,
                show_header=True,
                padding=(0, 1),
                expand=False,
            )
            table.add_column("Column", style="cyan", no_wrap=True)
            table.add_column("Type", style="dim", no_wrap=True)
            table.add_column("Non-Null", justify="right")
            table.add_column("Distinct", justify="right")
            table.add_column("Min", justify="right", max_width=12)
            table.add_column("Max", justify="right", max_width=12)
            table.add_column("Mean", justify="right")

            for col in profile.columns:
                # Format percentages
                non_null_pct = f"{(col.non_nulls_p or 0) * 100:.0f}%" if col.non_nulls_p is not None else "-"
                distinct_pct = f"{(col.distinct_p or 0) * 100:.0f}%" if col.distinct_p is not None else "-"

                # Format min/max values (truncate if too long)
                def fmt_val(val, max_len=10):
                    if val is None:
                        return "-"
                    s = str(val)
                    return s[:max_len] + "..." if len(s) > max_len else s

                min_val = fmt_val(col.min)
                max_val = fmt_val(col.max)
                mean_val = f"{col.avg:.2f}" if col.avg is not None else "-"

                table.add_row(
                    col.name,
                    col.type,
                    non_null_pct,
                    distinct_pct,
                    min_val,
                    max_val,
                    mean_val,
                )

            console.print(table)
            console.print()  # Blank line after table
        else:
            # Text fallback
            print("       Column Details:")
            print("       " + "-" * 60)
            for col in profile.columns:
                non_null_pct = f"{(col.non_nulls_p or 0) * 100:.0f}%" if col.non_nulls_p is not None else "-"
                distinct_pct = f"{(col.distinct_p or 0) * 100:.0f}%" if col.distinct_p is not None else "-"
                print(f"       {col.name:20} {col.type:10} Non-Null: {non_null_pct:5} Distinct: {distinct_pct:5}")
            print()

    def _store_profile(self, profile: TableProfile) -> None:
        """Store profile results in metadata_store.duckdb.

        v0.58.7: Fixed field mappings from ColumnProfile to ColumnProfileResult.
        """
        try:
            # Check if DuckDB is available
            try:
                import duckdb
            except ImportError:
                if HAS_RICH:
                    console.print("[yellow]Warning: DuckDB not available. Profile results will not be persisted.[/yellow]")
                return

            from dbt.compute.metadata import ProjectMetadataStore, ColumnProfileResult

            project_root = Path(self.runtime_config.project_root)
            store = ProjectMetadataStore(project_root)
            store.initialize()

            for col in profile.columns:
                # Map ColumnProfile fields to ColumnProfileResult fields
                # ColumnProfile uses PipeRider-style names (name, samples, nulls, distinct, etc.)
                # ColumnProfileResult uses legacy-style names (column_name, row_count, null_count, etc.)
                result = ColumnProfileResult(
                    source_name=profile.source_name,
                    table_name=profile.table_name,
                    column_name=col.name,  # PipeRider field: name
                    profile_mode=profile.profile_mode,
                    row_count=col.samples,  # PipeRider field: samples
                    null_count=col.nulls,  # PipeRider field: nulls
                    null_percent=(col.nulls_p or 0.0) * 100,  # Convert decimal to percentage
                    distinct_count=col.distinct,  # PipeRider field: distinct
                    distinct_percent=(col.distinct_p or 0.0) * 100,  # Convert decimal to percentage
                    min_value=col.min,  # PipeRider field: min
                    max_value=col.max,  # PipeRider field: max
                    mean_value=col.avg,  # PipeRider field: avg
                    median_value=col.p50,  # Use p50 as median
                    stddev_value=col.stddev,  # PipeRider field: stddev
                    p25=col.p25,
                    p50=col.p50,
                    p75=col.p75,
                    min_length=col.min_length,
                    max_length=col.max_length,
                    avg_length=col.avg_length,
                    histogram=json.dumps(col.histogram) if col.histogram else None,
                    top_values=json.dumps(col.topk) if col.topk else None,  # PipeRider field: topk
                    alerts=json.dumps(col.alerts) if col.alerts else None,
                    profiled_at=profile.profiled_at,
                    duration_ms=col.elapsed_milli,  # PipeRider field: elapsed_milli
                )
                store.save_profile_result(result)

            store.close()

        except Exception as e:
            # Log but don't fail if storage fails
            if HAS_RICH:
                console.print(f"[yellow]Warning: Could not store profile results: {e}[/yellow]")

    def _print_summary(self, result: ProfileExecutionResult) -> None:
        """Print PipeRider-style summary with Rich formatting."""
        if not HAS_RICH:
            print("\n" + "=" * 60)
            print("  SUMMARY")
            print(f"  Tables profiled: {result.tables_profiled}")
            print(f"  Total rows: {result.total_rows:,}")
            print(f"  Total columns: {result.total_columns}")
            print(f"  Alerts: {result.total_alerts}")
            print(f"  Duration: {result.duration_ms / 1000:.1f}s")
            print("=" * 60 + "\n")
            return

        console.print()

        # Summary panel
        summary_lines = [
            f"[bold]Tables profiled:[/bold]  {result.tables_profiled}",
            f"[bold]Total rows:[/bold]       {result.total_rows:,}",
            f"[bold]Total columns:[/bold]    {result.total_columns}",
        ]

        if result.total_alerts > 0:
            summary_lines.append(f"[bold yellow]Alerts:[/bold yellow]          {result.total_alerts}")
        else:
            summary_lines.append(f"[bold green]Alerts:[/bold green]          0")

        summary_lines.append(f"[dim]Duration:[/dim]         {result.duration_ms / 1000:.1f}s")

        console.print(Panel(
            "\n".join(summary_lines),
            title="[bold cyan]Summary[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED,
        ))

        # List alerts if any
        if result.total_alerts > 0:
            console.print()
            console.print("[bold yellow]Alerts:[/bold yellow]")
            console.print()

            alerts_table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
            alerts_table.add_column("Severity", style="bold", width=8)
            alerts_table.add_column("Type", style="cyan", width=15)
            alerts_table.add_column("Location", style="white", width=30)
            alerts_table.add_column("Message", style="dim")

            for profile in result.profiles:
                for col in profile.columns:
                    for alert in col.alerts:
                        if alert["severity"] == "error":
                            sev_display = "[red]ERROR[/red]"
                        elif alert["severity"] == "warning":
                            sev_display = "[yellow]WARN[/yellow]"
                        else:
                            sev_display = "[blue]INFO[/blue]"

                        location = f"{profile.table_name}.{col.column_name}"
                        alerts_table.add_row(
                            sev_display,
                            alert["type"],
                            location,
                            alert["message"]
                        )

            console.print(alerts_table)

        console.print()

        # Success footer
        if result.tables_profiled > 0:
            console.print("[bold green]Profiling complete![/bold green]")
            console.print()
            console.print("[cyan]Results saved to:[/cyan] [bold].dvt/metadata_store.duckdb[/bold]")
            console.print("[dim]View report: dvt profile serve[/dim]")
        else:
            console.print("[yellow]No tables were profiled.[/yellow]")

        console.print()

    def interpret_results(self, result: ProfileExecutionResult) -> bool:
        """Interpret results to determine success/failure."""
        if not result.profiles:
            return False
        # Success if at least one profile completed
        return any(p.status == "success" for p in result.profiles)
