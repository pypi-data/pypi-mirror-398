"""
Query Analyzer for Execution Routing

This module analyzes compiled SQL queries to determine the optimal execution strategy:
- Pushdown: All sources from same connection → execute on source database
- Federated: Sources from multiple connections → use compute layer

The analyzer respects user configuration overrides while providing intelligent defaults.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from dbt.contracts.graph.manifest import Manifest
from dbt.contracts.graph.nodes import ManifestNode, SourceDefinition
from dbt_common.exceptions import DbtRuntimeError


@dataclass
class QueryAnalysisResult:
    """
    Result of query analysis.

    Contains information about source connections and recommended execution strategy.
    """

    # Set of connection names used by this query
    source_connections: Set[str]

    # Set of source unique_ids referenced
    source_refs: Set[str]

    # Recommended execution strategy
    strategy: str  # "pushdown" or "federated"

    # Primary connection (for pushdown) or None (for federated)
    primary_connection: Optional[str]

    # Reason for the chosen strategy
    reason: str

    # User override applied (if any)
    user_override: Optional[str] = None

    @property
    def is_pushdown(self) -> bool:
        """Check if pushdown strategy is recommended."""
        return self.strategy == "pushdown"

    @property
    def is_federated(self) -> bool:
        """Check if federated strategy is recommended."""
        return self.strategy == "federated"

    @property
    def is_homogeneous(self) -> bool:
        """Check if all sources are from the same connection."""
        return len(self.source_connections) <= 1


class QueryAnalyzer:
    """
    Analyzes compiled SQL queries to determine execution strategy.

    The analyzer:
    1. Identifies all source() and ref() references in the query
    2. Determines which connections are involved
    3. Recommends pushdown (homogeneous) or federated (heterogeneous) execution
    4. Respects user configuration overrides
    """

    def __init__(self, manifest: Manifest):
        """
        Initialize query analyzer.

        :param manifest: The parsed dbt manifest with all nodes and sources
        """
        self.manifest = manifest
        # Cache for source connection mappings
        self._source_connection_cache: Dict[str, str] = {}

    def analyze(
        self,
        node: ManifestNode,
        user_compute_override: Optional[str] = None,
        target_connection: Optional[str] = None
    ) -> QueryAnalysisResult:
        """
        Analyze a compiled node to determine execution strategy.

        :param node: The compiled ManifestNode to analyze
        :param user_compute_override: User's compute config (if specified)
        :param target_connection: Target connection for materialization (if different from source)
        :returns: QueryAnalysisResult with execution strategy
        """
        # Skip analysis for seeds - they don't have sources and accessing
        # node.sources property on SeedNode raises an error
        if node.resource_type == "seed":
            return QueryAnalysisResult(
                source_connections=set(),
                source_refs=set(),
                strategy="pushdown",
                primary_connection=None,
                reason="Seed node - no source analysis needed",
                user_override=None
            )

        # Extract source and ref dependencies
        source_refs = self._extract_source_references(node)

        # Map sources to their connections
        source_connections = self._map_sources_to_connections(source_refs)

        # DVT v0.51.6: Determine strategy based on DVT Rules
        #
        # Rule 1 (Primary Directive): Pushdown whenever model and ALL inputs are in same Target
        # Rule 1.1: Federation ONLY when model requires inputs from a Target different than its own
        # Rule 1.5: Compute engine settings are IGNORED for Pushdown-eligible models
        # Rule 2.2: CLI --target forces all models to that target; sources NOT in target trigger Federation
        #
        # Decision Logic:
        # 1. If no direct sources → Pushdown (refs resolve to target where upstream is materialized)
        # 2. If all sources are in target_connection → Pushdown
        # 3. If any source is NOT in target_connection → Federation
        # 4. user_compute_override does NOT change this decision (Rule 1.5)

        if len(source_connections) == 0:
            # No direct source() dependencies
            # Models with only refs → Pushdown to target (refs are already materialized there)
            strategy = "pushdown"
            has_refs = hasattr(node, 'depends_on') and node.depends_on and node.depends_on.nodes
            if has_refs and target_connection:
                reason = f"Model refs materialized tables - pushdown to target '{target_connection}'"
                primary_connection = target_connection
            else:
                reason = "No source dependencies - pushdown to default target"
                primary_connection = target_connection
            # Rule 1.5: Compute override is noted but doesn't change strategy
            user_override = user_compute_override if user_compute_override else None

        elif len(source_connections) == 1:
            single_source_conn = list(source_connections)[0]

            # Rule 2.2: Check if source is in the target connection
            if target_connection and single_source_conn != target_connection:
                # Source NOT in target → Federation required (Rule 1.1)
                strategy = "federated"
                reason = f"Cross-target: source '{single_source_conn}' != target '{target_connection}' - federation required"
                primary_connection = None
                user_override = user_compute_override
            else:
                # Source IS in target (or no target override) → Pushdown (Rule 1)
                strategy = "pushdown"
                primary_connection = single_source_conn
                reason = f"All sources in target '{primary_connection}' - pushdown"
                # Rule 1.5: Compute override ignored for pushdown-eligible models
                user_override = None

        else:
            # Multiple source connections → Always requires Federation
            strategy = "federated"
            reason = f"Sources span {len(source_connections)} connections: {sorted(source_connections)} - federation required"
            primary_connection = None
            user_override = user_compute_override

        return QueryAnalysisResult(
            source_connections=source_connections,
            source_refs=source_refs,
            strategy=strategy,
            primary_connection=primary_connection,
            reason=reason,
            user_override=user_override
        )

    def _extract_source_references(self, node: ManifestNode) -> Set[str]:
        """
        Extract all source unique_ids DIRECTLY referenced by this node.

        DVT v0.51.5: Only direct source() references are considered.
        ref() dependencies are NOT traced to their underlying sources because:
        - ref() resolves to the target database where upstream models are materialized
        - If model_a reads from postgres and is materialized to databricks,
          then model_b which refs model_a should use databricks (pushdown),
          NOT trace back to postgres (which would incorrectly force federation)

        :param node: The node to analyze
        :returns: Set of source unique_ids (direct references only)
        """
        source_refs = set()

        # Direct source dependencies ONLY
        # ref() dependencies resolve to target database, not original sources
        if hasattr(node, 'sources') and node.sources:
            # node.sources can be a list or set - convert to list for safety
            sources = node.sources if isinstance(node.sources, (list, tuple, set)) else []
            for source in sources:
                # source can be either:
                # 1. A string (full unique_id): "source.package.source_name.table_name"
                # 2. A list/tuple: ["source_name", "table_name"]
                if isinstance(source, str):
                    # Full unique_id - use as-is
                    source_refs.add(source)
                elif isinstance(source, (list, tuple)) and len(source) == 2:
                    # Tuple format: ["source_name", "table_name"]
                    # Need to construct full unique_id: "source.{package}.{source_name}.{table_name}"
                    source_name, table_name = source
                    # Build unique_id using node's package_name
                    package_name = node.package_name if hasattr(node, 'package_name') else self.root_project.project_name
                    unique_id = f"source.{package_name}.{source_name}.{table_name}"
                    source_refs.add(unique_id)

        # DVT v0.51.5: DO NOT trace ref() dependencies to their underlying sources
        # ref() resolves to target database, where upstream models are already materialized
        # Only direct source() references determine federation vs pushdown

        return source_refs

    def _trace_node_to_sources(self, node_id: str, visited: Optional[Set[str]] = None) -> Set[str]:
        """
        Recursively trace a node's dependencies to find all underlying sources.

        :param node_id: Unique ID of the node to trace
        :param visited: Set of already-visited nodes (for cycle detection)
        :returns: Set of source unique_ids
        """
        if visited is None:
            visited = set()

        if node_id in visited:
            return set()

        visited.add(node_id)
        sources = set()

        # Check if this is a source
        if node_id.startswith('source.'):
            sources.add(node_id)
            return sources

        # Get the node from manifest
        node = self.manifest.nodes.get(node_id)
        if not node:
            # Node not found (could be disabled or external)
            return sources

        # Skip seeds - they don't have source dependencies and accessing
        # node.sources property raises an error
        if hasattr(node, 'resource_type') and node.resource_type == 'seed':
            # Seeds have no upstream sources to trace
            return sources

        # Add direct source dependencies
        if hasattr(node, 'sources') and node.sources:
            # Handle both list and set types safely
            node_sources = node.sources if isinstance(node.sources, (list, tuple, set)) else []
            for source in node_sources:
                if isinstance(source, str):
                    sources.add(source)

        # Recursively trace node dependencies
        if hasattr(node, 'depends_on') and node.depends_on:
            nodes = node.depends_on.nodes if isinstance(node.depends_on.nodes, (list, tuple, set)) else []
            for dep_id in nodes:
                if isinstance(dep_id, str):
                    dep_sources = self._trace_node_to_sources(dep_id, visited)
                    sources.update(dep_sources)

        return sources

    def _map_sources_to_connections(self, source_refs: Set[str]) -> Set[str]:
        """
        Map source unique_ids to their connection names.

        :param source_refs: Set of source unique_ids
        :returns: Set of connection names
        """
        connections = set()

        for source_id in source_refs:
            connection = self._get_source_connection(source_id)
            if connection:
                connections.add(connection)

        return connections

    def _get_source_connection(self, source_id: str) -> Optional[str]:
        """
        Get the connection name for a source.

        Uses caching for performance. Checks multiple locations for backward
        compatibility with different source definition styles:
        1. source.connection (direct attribute)
        2. source.meta.connection (meta dict)
        3. source.source_meta.connection (source_meta dict)

        :param source_id: Source unique_id
        :returns: Connection name or None if not specified
        """
        # Check cache
        if source_id in self._source_connection_cache:
            return self._source_connection_cache[source_id]

        # Look up source in manifest
        source = self.manifest.sources.get(source_id)
        if not source:
            return None

        # Get connection - check multiple locations for backward compatibility
        connection = None

        # 1. Direct connection attribute (preferred)
        if hasattr(source, 'connection') and source.connection:
            connection = source.connection

        # 2. meta.connection (fallback)
        elif hasattr(source, 'meta') and isinstance(source.meta, dict):
            connection = source.meta.get('connection')

        # 3. source_meta.connection (legacy fallback)
        elif hasattr(source, 'source_meta') and isinstance(source.source_meta, dict):
            connection = source.source_meta.get('connection')

        # Cache and return
        self._source_connection_cache[source_id] = connection
        return connection

    def get_execution_summary(self, node: ManifestNode) -> str:
        """
        Get a human-readable summary of the execution strategy for a node.

        Useful for logging and debugging.

        :param node: The node to analyze
        :returns: Summary string
        """
        result = self.analyze(node)

        summary_parts = [
            f"Node: {node.unique_id}",
            f"Strategy: {result.strategy.upper()}",
            f"Reason: {result.reason}",
            f"Source Connections: {sorted(result.source_connections) if result.source_connections else 'None'}",
            f"Source Count: {len(result.source_refs)}",
        ]

        if result.primary_connection:
            summary_parts.append(f"Execution Connection: {result.primary_connection}")

        if result.user_override:
            summary_parts.append(f"User Override: {result.user_override}")

        return "\n".join(summary_parts)

    def analyze_batch(
        self,
        nodes: List[ManifestNode]
    ) -> Dict[str, QueryAnalysisResult]:
        """
        Analyze multiple nodes in batch.

        More efficient than analyzing one at a time due to caching.

        :param nodes: List of nodes to analyze
        :returns: Dict mapping node unique_id to QueryAnalysisResult
        """
        results = {}

        for node in nodes:
            result = self.analyze(node)
            results[node.unique_id] = result

        return results

    def get_federated_nodes(
        self,
        nodes: List[ManifestNode]
    ) -> List[ManifestNode]:
        """
        Filter nodes that require federated execution.

        :param nodes: List of nodes to filter
        :returns: List of nodes requiring federated execution
        """
        federated = []

        for node in nodes:
            result = self.analyze(node)
            if result.is_federated:
                federated.append(node)

        return federated

    def get_pushdown_nodes(
        self,
        nodes: List[ManifestNode]
    ) -> List[ManifestNode]:
        """
        Filter nodes eligible for pushdown execution.

        :param nodes: List of nodes to filter
        :returns: List of nodes eligible for pushdown
        """
        pushdown = []

        for node in nodes:
            result = self.analyze(node)
            if result.is_pushdown:
                pushdown.append(node)

        return pushdown
