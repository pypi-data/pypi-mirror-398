"""
Smart Compute Engine Selector

Selects compute engine based on DVT compute rules (NOT size-based).

v0.56.0: Refactored to follow DVT compute rules:
1. CLI --target-compute override (highest priority)
2. Model-level config {{ config(compute='...') }}
3. Default from computes.yml target_compute
4. Pushdown when model and all inputs are in same target (no Spark needed)

Selection is deterministic based on configuration, not data characteristics.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Set

from dbt.contracts.graph.manifest import Manifest
from dbt.contracts.graph.nodes import ManifestNode
from dbt.query_analyzer import QueryAnalysisResult
from dbt_common.exceptions import DbtRuntimeError


class ExecutionStrategy(Enum):
    """Execution strategy for a node."""

    PUSHDOWN = "pushdown"  # Execute directly on target adapter (same connection)
    FEDERATED = "federated"  # Execute via Spark for cross-target queries


@dataclass
class WorkloadEstimate:
    """Estimated workload characteristics for a query."""

    estimated_rows: int  # Estimated total rows to process
    source_count: int  # Number of source tables
    connection_count: int  # Number of different connections
    has_aggregations: bool  # Query contains GROUP BY or aggregations
    has_joins: bool  # Query contains JOIN operations
    complexity_score: float  # 0.0 to 1.0, higher = more complex

    @property
    def estimated_data_mb(self) -> float:
        """Rough estimate of data size in MB (assuming ~100 bytes/row)."""
        return (self.estimated_rows * 100) / (1024 * 1024)


class SmartComputeSelector:
    """
    Selects compute engine based on DVT compute rules.

    v0.56.0: Rule-based selection (NO size-based logic).

    Selection hierarchy (highest to lowest priority):
    1. CLI --target-compute override
    2. Model config: {{ config(compute='spark-cluster') }}
    3. Default from computes.yml target_compute

    Execution strategy:
    - PUSHDOWN: When model and all inputs are in same target
    - FEDERATED: When sources span multiple targets (requires Spark)
    """

    def __init__(
        self,
        manifest: Manifest,
        compute_registry: Optional[Any] = None,
        cli_target_compute: Optional[str] = None,
    ):
        """
        Initialize smart selector.

        :param manifest: The dbt manifest
        :param compute_registry: ComputeRegistry instance for compute configuration
        :param cli_target_compute: CLI --target-compute override (highest priority)
        """
        self.manifest = manifest
        self.compute_registry = compute_registry
        self.cli_target_compute = cli_target_compute

    def select_engine(
        self,
        node: ManifestNode,
        analysis_result: QueryAnalysisResult,
        cli_override: Optional[str] = None,
    ) -> str:
        """
        Select compute engine based on DVT rules.

        v0.56.0: Rule-based selection (no size-based logic).

        Priority:
        1. cli_override parameter (passed at call time)
        2. self.cli_target_compute (passed at init time)
        3. Model config: {{ config(compute='...') }}
        4. Default from computes.yml target_compute

        :param node: The node to execute
        :param analysis_result: Query analysis result
        :param cli_override: CLI --target-compute override
        :returns: Compute engine name (e.g., "spark-local", "spark-cluster")
        :raises DbtRuntimeError: If specified compute doesn't exist
        """
        # Determine execution strategy first
        strategy = self._determine_execution_strategy(node, analysis_result)

        # For pushdown, no Spark compute needed
        if strategy == ExecutionStrategy.PUSHDOWN:
            return "pushdown"

        # For federated execution, select compute engine
        return self._select_compute_for_federation(node, cli_override)

    def _determine_execution_strategy(
        self, node: ManifestNode, analysis_result: QueryAnalysisResult
    ) -> ExecutionStrategy:
        """
        Determine whether to use pushdown or federation.

        DVT Rule: Pushdown when model and ALL inputs are in same target.

        :param node: The node to analyze
        :param analysis_result: Query analysis result
        :returns: ExecutionStrategy (PUSHDOWN or FEDERATED)
        """
        # Get target connection for this node
        node_target = self._get_node_target(node)

        # Get all source connections
        source_connections = analysis_result.source_connections

        # If no sources, can use pushdown (pure computation)
        if not source_connections:
            return ExecutionStrategy.PUSHDOWN

        # Check if all sources are in the same connection as the target
        if len(source_connections) == 1:
            source_connection = next(iter(source_connections))
            if source_connection == node_target:
                # Same connection - use pushdown
                return ExecutionStrategy.PUSHDOWN

        # Multiple connections or different target - must federate
        return ExecutionStrategy.FEDERATED

    def _get_node_target(self, node: ManifestNode) -> str:
        """
        Get the target connection for a node.

        :param node: The manifest node
        :returns: Target connection name
        """
        # Check if node has explicit target config
        if hasattr(node, "config") and hasattr(node.config, "target"):
            if node.config.target:
                return node.config.target

        # Otherwise, use default target from manifest
        # Note: In DVT, this comes from profiles.yml default target
        return "default"

    def _select_compute_for_federation(
        self, node: ManifestNode, cli_override: Optional[str] = None
    ) -> str:
        """
        Select compute engine for federated execution.

        Priority:
        1. cli_override parameter (passed at call time)
        2. self.cli_target_compute (passed at init time)
        3. Model config: {{ config(compute='...') }}
        4. Default from computes.yml target_compute

        :param node: The node to execute
        :param cli_override: CLI --target-compute override
        :returns: Compute engine name
        :raises DbtRuntimeError: If specified compute doesn't exist
        """
        compute_name = None

        # Priority 1: CLI override (call-time)
        if cli_override:
            compute_name = cli_override

        # Priority 2: CLI override (init-time)
        elif self.cli_target_compute:
            compute_name = self.cli_target_compute

        # Priority 3: Model-level config
        elif hasattr(node, "config") and hasattr(node.config, "compute"):
            if node.config.compute:
                compute_name = node.config.compute

        # Priority 4: Default from computes.yml
        elif self.compute_registry:
            compute_name = self.compute_registry.target_compute

        # Fallback if no registry
        if not compute_name:
            compute_name = "spark-local"

        # Validate the compute engine exists
        if self.compute_registry and not self.compute_registry.exists(compute_name):
            available = [c.name for c in self.compute_registry.list()]
            raise DbtRuntimeError(
                f"Compute engine '{compute_name}' not found. "
                f"Available engines: {', '.join(available)}"
            )

        return compute_name

    def _estimate_workload(
        self, node: ManifestNode, analysis_result: QueryAnalysisResult
    ) -> WorkloadEstimate:
        """
        Estimate workload characteristics for a node.

        Note: Used for informational purposes only, NOT for compute selection.

        :param node: The node to analyze
        :param analysis_result: Query analysis result
        :returns: WorkloadEstimate
        """
        # Count sources
        source_count = len(analysis_result.source_refs)
        connection_count = len(analysis_result.source_connections)

        # Estimate row count (informational only)
        estimated_rows = self._estimate_row_count(analysis_result.source_refs)

        # Analyze SQL for complexity (informational only)
        sql = node.compiled_code if hasattr(node, "compiled_code") else node.raw_code
        has_aggregations = self._has_aggregations(sql)
        has_joins = self._has_joins(sql)

        # Calculate complexity score (informational only)
        complexity_score = self._calculate_complexity(
            source_count=source_count,
            connection_count=connection_count,
            has_aggregations=has_aggregations,
            has_joins=has_joins,
        )

        return WorkloadEstimate(
            estimated_rows=estimated_rows,
            source_count=source_count,
            connection_count=connection_count,
            has_aggregations=has_aggregations,
            has_joins=has_joins,
            complexity_score=complexity_score,
        )

    def _estimate_row_count(self, source_refs: set) -> int:
        """
        Estimate total row count from source tables.

        Note: Used for informational purposes only.

        :param source_refs: Set of source unique_ids
        :returns: Estimated row count
        """
        total_rows = 0

        for source_id in source_refs:
            source = self.manifest.sources.get(source_id)
            if not source:
                total_rows += 100000
                continue

            # Heuristic based on naming (informational only)
            if (
                "fact" in source.identifier.lower()
                or "events" in source.identifier.lower()
            ):
                total_rows += 1000000
            elif (
                "dim" in source.identifier.lower()
                or "lookup" in source.identifier.lower()
            ):
                total_rows += 10000
            else:
                total_rows += 100000

        return total_rows

    def _has_aggregations(self, sql: str) -> bool:
        """Check if SQL contains aggregations."""
        sql_upper = sql.upper()
        return any(
            keyword in sql_upper
            for keyword in [
                " GROUP BY ",
                " SUM(",
                " COUNT(",
                " AVG(",
                " MIN(",
                " MAX(",
                " HAVING ",
            ]
        )

    def _has_joins(self, sql: str) -> bool:
        """Check if SQL contains joins."""
        sql_upper = sql.upper()
        return any(
            keyword in sql_upper
            for keyword in [
                " JOIN ",
                " INNER JOIN ",
                " LEFT JOIN ",
                " RIGHT JOIN ",
                " FULL JOIN ",
                " CROSS JOIN ",
            ]
        )

    def _calculate_complexity(
        self,
        source_count: int,
        connection_count: int,
        has_aggregations: bool,
        has_joins: bool,
    ) -> float:
        """Calculate query complexity score (0.0 to 1.0)."""
        score = 0.0
        score += min(source_count / 10.0, 0.3)
        score += min(connection_count / 5.0, 0.2)
        if has_aggregations:
            score += 0.2
        if has_joins:
            score += 0.3
        return min(score, 1.0)

    def get_execution_strategy(
        self, node: ManifestNode, analysis_result: QueryAnalysisResult
    ) -> ExecutionStrategy:
        """
        Get the execution strategy for a node (public API).

        :param node: The node
        :param analysis_result: Query analysis result
        :returns: ExecutionStrategy enum
        """
        return self._determine_execution_strategy(node, analysis_result)

    def get_recommendation_reason(
        self, node: ManifestNode, analysis_result: QueryAnalysisResult
    ) -> str:
        """
        Get human-readable explanation for engine selection.

        :param node: The node
        :param analysis_result: Query analysis result
        :returns: Explanation string
        """
        strategy = self._determine_execution_strategy(node, analysis_result)

        if strategy == ExecutionStrategy.PUSHDOWN:
            return "Pushdown: All sources in same target connection - executing directly"

        # Federated execution
        engine = self._select_compute_for_federation(node)
        estimate = self._estimate_workload(node, analysis_result)

        reasons = []
        reasons.append(f"Cross-target query ({estimate.connection_count} connections)")

        if self.cli_target_compute:
            reasons.append(f"CLI override: --target-compute {self.cli_target_compute}")
        elif hasattr(node, "config") and hasattr(node.config, "compute") and node.config.compute:
            reasons.append(f"Model config: compute='{node.config.compute}'")
        else:
            reasons.append("Using default from computes.yml")

        reason_str = "; ".join(reasons)
        return f"Federated ({engine}): {reason_str}"
