# =============================================================================
# DVT Retract Task
# =============================================================================
# Drops all materialized models from target databases.
#
# Usage:
#   dvt retract                    # Drop all materialized models
#   dvt retract --dry-run          # Preview what would be dropped
#   dvt retract --select "model*"  # Drop matching models only
#   dvt retract --exclude "dim_*"  # Exclude matching models
#
# DVT v0.58.1: Added reverse DAG order support
# DVT v0.59.0a29: Removed CASCADE - reverse DAG order handles dependencies
# =============================================================================

from __future__ import annotations

import json
import fnmatch
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from dbt.cli.flags import Flags
from dbt.config import RuntimeConfig
from dbt.contracts.graph.manifest import Manifest
from dbt.task.base import BaseTask

# Try to import Rich for beautiful output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn, TimeElapsedColumn
    from rich.panel import Panel
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class RetractTask(BaseTask):
    """
    Task to drop materialized models from target databases.

    This task:
    1. Reads the manifest to find all materialized models
    2. Builds dependency graph and orders models in REVERSE DAG order
    3. Groups models by their target adapter
    4. Drops each model's relation (table/view)
    5. Supports --dry-run, --select, and --exclude flags

    DVT v0.58.1 Changes:
    - Follows reverse DAG order (drop dependents first, then dependencies)

    DVT v0.59.0a29 Changes:
    - Removed CASCADE - reverse DAG order already ensures dependents are dropped first
    """

    def __init__(self, args: Flags, config: RuntimeConfig, manifest: Manifest):
        super().__init__(args)
        self.config = config
        self.manifest = manifest
        self.dry_run = getattr(args, 'DRY_RUN', False)
        self._console = None
        self._use_rich = HAS_RICH
        if self._use_rich:
            self._console = Console()

    def _print(self, message: str, style: str = None):
        """Print with optional Rich styling."""
        if self._use_rich and style:
            self._console.print(f"[{style}]{message}[/{style}]")
        elif self._use_rich:
            self._console.print(message)
        else:
            print(message)

    def run(self) -> Tuple[bool, Dict[str, Any]]:
        """Execute the retract task."""
        start_time = time.time()

        # Header
        self._print("")
        if self.dry_run:
            if self._use_rich:
                self._console.print(Panel(
                    "[bold cyan]Preview of models that would be dropped[/bold cyan]\n"
                    "[dim]Using reverse DAG order (dependents first)[/dim]",
                    title="[bold cyan]DVT RETRACT (DRY RUN)[/bold cyan]",
                    border_style="cyan",
                    box=box.DOUBLE,
                ))
            else:
                self._print("=" * 60)
                self._print("  DVT RETRACT (DRY RUN)")
                self._print("  Preview of models that would be dropped")
                self._print("=" * 60)
        else:
            if self._use_rich:
                self._console.print(Panel(
                    "[bold red]Dropping materialized models from databases[/bold red]\n"
                    "[dim]Using reverse DAG order (dependents dropped first)[/dim]",
                    title="[bold red]DVT RETRACT[/bold red]",
                    border_style="red",
                    box=box.DOUBLE,
                ))
            else:
                self._print("=" * 60)
                self._print("  DVT RETRACT")
                self._print("  Dropping materialized models from databases")
                self._print("=" * 60)
        self._print("")

        # Get models to retract
        models = self._get_models_to_retract()

        if not models:
            self._print("No materialized models found to retract.", "yellow")
            return True, {"dropped": [], "failed": [], "skipped": []}

        # Filter by --select and --exclude
        models = self._filter_models(models)

        if not models:
            self._print("No models match the selection criteria.", "yellow")
            return True, {"dropped": [], "failed": [], "skipped": []}

        # Sort in REVERSE DAG order (dependents first, then dependencies)
        models = self._sort_reverse_dag_order(models)

        # Group by target
        models_by_target = self._group_models_by_target(models)

        dropped = []
        failed = []
        skipped = []

        # Calculate total for progress bar
        total_models = sum(len(m) for m in models_by_target.values())

        if self._use_rich and not self.dry_run:
            # Use progress bar for actual drops
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=40),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                console=self._console,
            ) as progress:
                task = progress.add_task("[cyan]Dropping models...", total=total_models)

                for target_name, target_models in models_by_target.items():
                    for model in target_models:
                        model_name = model.get("name")
                        relation_type = model.get("relation_type", "table")
                        schema = model.get("schema")
                        database = model.get("database")

                        # Build relation identifier
                        if database:
                            relation_id = f"{database}.{schema}.{model_name}"
                        else:
                            relation_id = f"{schema}.{model_name}"

                        progress.update(task, description=f"[cyan]Dropping[/cyan] [bold]{relation_id}[/bold]")

                        success = self._drop_relation(target_name, model, use_cascade=True)
                        if success:
                            dropped.append({"name": model_name, "target": target_name, "type": relation_type})
                        else:
                            failed.append({"name": model_name, "target": target_name, "error": "Drop failed"})

                        progress.advance(task)
        else:
            # Process each target (dry run or non-Rich)
            for target_name, target_models in models_by_target.items():
                self._print(f"\n  Target: {target_name}", "bold")
                self._print("  " + "-" * 40)

                for model in target_models:
                    model_name = model.get("name")
                    relation_type = model.get("relation_type", "table")
                    schema = model.get("schema")
                    database = model.get("database")

                    # Build relation identifier
                    if database:
                        relation_id = f"{database}.{schema}.{model_name}"
                    else:
                        relation_id = f"{schema}.{model_name}"

                    if self.dry_run:
                        self._print(f"    [would drop] {relation_id} ({relation_type})", "dim cyan")
                        dropped.append({"name": model_name, "target": target_name, "type": relation_type})
                    else:
                        success = self._drop_relation(target_name, model, use_cascade=False)
                        if success:
                            self._print(f"    [green]OK[/green] Dropped {relation_id} ({relation_type})", "green")
                            dropped.append({"name": model_name, "target": target_name, "type": relation_type})
                        else:
                            self._print(f"    [red]FAIL[/red] Failed to drop {relation_id}", "red")
                            failed.append({"name": model_name, "target": target_name, "error": "Drop failed"})

        # Summary
        elapsed = time.time() - start_time
        self._print("")

        if self._use_rich:
            # Rich summary panel
            if self.dry_run:
                summary_text = f"[bold cyan]{len(dropped)} models would be dropped[/bold cyan]"
                border_color = "cyan"
            elif failed:
                summary_text = f"[bold green]Dropped: {len(dropped)}[/bold green] | [bold red]Failed: {len(failed)}[/bold red]"
                border_color = "yellow"
            else:
                summary_text = f"[bold green]Successfully dropped {len(dropped)} models[/bold green]"
                border_color = "green"

            self._console.print(Panel(
                f"{summary_text}\n[dim]Time: {elapsed:.2f}s[/dim]",
                title="[bold]Summary[/bold]",
                border_style=border_color,
                box=box.ROUNDED,
            ))
        else:
            self._print("=" * 60)
            if self.dry_run:
                self._print(f"  DRY RUN: {len(dropped)} models would be dropped")
            else:
                if failed:
                    self._print(f"  Dropped: {len(dropped)} | Failed: {len(failed)}")
                else:
                    self._print(f"  Successfully dropped {len(dropped)} models")
            self._print(f"  Time: {elapsed:.2f}s")
            self._print("=" * 60)

        self._print("")

        success = len(failed) == 0
        return success, {"dropped": dropped, "failed": failed, "skipped": skipped}

    def _get_models_to_retract(self) -> List[Dict[str, Any]]:
        """Get list of materialized models from manifest."""
        models = []

        for node_id, node in self.manifest.nodes.items():
            # Only process model nodes
            if not node_id.startswith("model."):
                continue

            # Skip ephemeral models (not materialized)
            materialization = getattr(node.config, 'materialized', 'view')
            if materialization == 'ephemeral':
                continue

            # Determine relation type
            if materialization == 'table':
                relation_type = 'table'
            elif materialization == 'incremental':
                relation_type = 'table'
            elif materialization == 'view':
                relation_type = 'view'
            else:
                relation_type = 'table'  # Default to table for custom materializations

            # Get target - use model config target override or default
            target = getattr(node.config, 'target', None) or self.config.target_name

            # Get dependencies (models this model depends on)
            depends_on = []
            if hasattr(node, 'depends_on') and hasattr(node.depends_on, 'nodes'):
                depends_on = [
                    dep for dep in node.depends_on.nodes
                    if dep.startswith('model.')
                ]

            # Get model info
            model_info = {
                "name": node.name,
                "unique_id": node_id,
                "schema": node.schema,
                "database": getattr(node, 'database', None),
                "relation_type": relation_type,
                "target": target,
                "materialization": materialization,
                "depends_on": depends_on,
            }
            models.append(model_info)

        return models

    def _sort_reverse_dag_order(self, models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort models in REVERSE DAG order.

        Models that depend on others should be dropped FIRST,
        then their dependencies. This ensures we can drop without
        foreign key or view dependency errors.

        Uses topological sort reversed (Kahn's algorithm).
        """
        # Build lookup and dependency graph
        model_lookup = {m["unique_id"]: m for m in models}
        model_ids = set(model_lookup.keys())

        # Build reverse dependency graph (who depends on me?)
        # For reverse DAG order, we want to drop dependents before dependencies
        dependents: Dict[str, Set[str]] = {uid: set() for uid in model_ids}
        in_degree: Dict[str, int] = {uid: 0 for uid in model_ids}

        for model in models:
            uid = model["unique_id"]
            for dep in model.get("depends_on", []):
                if dep in model_ids:
                    # dep is a dependency of uid
                    # In reverse order, uid should come BEFORE dep
                    dependents[dep].add(uid)
                    in_degree[uid] += 1

        # Kahn's algorithm for topological sort (reversed)
        # Start with models that have no dependencies (in_degree = 0)
        # These are the "leaf" nodes in the normal DAG, which should be dropped first
        queue = [uid for uid, deg in in_degree.items() if deg == 0]
        result = []

        while queue:
            # Get next model with no remaining dependencies
            current = queue.pop(0)
            result.append(model_lookup[current])

            # For each model that depends on current
            for dependent in dependents[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Handle cycles (shouldn't happen in well-formed DAGs)
        remaining = [m for m in models if m["unique_id"] not in {r["unique_id"] for r in result}]
        result.extend(remaining)

        # Reverse the result so dependents come first
        # (models at the "top" of the DAG - those with many dependents - should be dropped last)
        result.reverse()

        return result

    def _filter_models(self, models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter models by --select and --exclude patterns."""
        select_patterns = getattr(self.args, 'SELECT', None) or []
        exclude_patterns = getattr(self.args, 'EXCLUDE', None) or []

        # Flatten if nested
        if select_patterns:
            select_patterns = [p for ps in select_patterns for p in (ps if isinstance(ps, (list, tuple)) else [ps])]
        if exclude_patterns:
            exclude_patterns = [p for ps in exclude_patterns for p in (ps if isinstance(ps, (list, tuple)) else [ps])]

        filtered = []
        for model in models:
            model_name = model.get("name", "")

            # Check if matches any exclude pattern
            if exclude_patterns:
                excluded = any(fnmatch.fnmatch(model_name, p) for p in exclude_patterns)
                if excluded:
                    continue

            # Check if matches any select pattern (if provided)
            if select_patterns:
                selected = any(fnmatch.fnmatch(model_name, p) for p in select_patterns)
                if not selected:
                    continue

            filtered.append(model)

        return filtered

    def _group_models_by_target(self, models: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group models by their target adapter, preserving order."""
        grouped = {}
        for model in models:
            target = model.get("target", self.config.target_name)
            if target not in grouped:
                grouped[target] = []
            grouped[target].append(model)
        return grouped

    def _drop_relation(self, target_name: str, model: Dict[str, Any], use_cascade: bool = False) -> bool:
        """
        Drop a relation from the database.

        Args:
            target_name: Name of the target adapter
            model: Model info dictionary
            use_cascade: Whether to use DROP ... CASCADE (default: False since v0.59.0a29)

        Returns:
            True if successful, False otherwise
        """
        try:
            from dbt.adapters.factory import get_adapter

            # Get adapter for target
            adapter = get_adapter(self.config)

            # Build DROP statement
            model_name = model.get("name")
            schema = model.get("schema")
            database = model.get("database")
            relation_type = model.get("relation_type", "table").upper()

            # Build qualified name with proper quoting
            if database:
                qualified_name = f'"{database}"."{schema}"."{model_name}"'
            else:
                qualified_name = f'"{schema}"."{model_name}"'

            # Execute DROP with CASCADE
            cascade_clause = " CASCADE" if use_cascade else ""
            drop_sql = f"DROP {relation_type} IF EXISTS {qualified_name}{cascade_clause}"

            with adapter.connection_named("retract"):
                adapter.execute(drop_sql, auto_begin=True, fetch=False)
                adapter.commit_if_has_connection()

            return True

        except Exception as e:
            # Log error but don't fail the entire task
            if self._use_rich:
                self._console.print(f"      [dim red]Error: {str(e)[:80]}[/dim red]")
            return False

    def interpret_results(self, results: Tuple[bool, Dict[str, Any]]) -> bool:
        """Interpret task results."""
        if isinstance(results, tuple):
            success, data = results
            return success
        return bool(results)
