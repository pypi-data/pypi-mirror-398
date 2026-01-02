# =============================================================================
# DVT Metadata Task
# =============================================================================
# Manages metadata for DVT projects - sources and materialized models.
#
# Commands:
#   dvt metadata reset              # Clear all metadata from store
#   dvt metadata snapshot           # Capture metadata for sources + models
#   dvt metadata export             # Display metadata in CLI (Rich table)
#   dvt metadata export-csv <file>  # Export to CSV file
#   dvt metadata export-json <file> # Export to JSON file
#
# DVT v0.57.0: Replaces dvt snap with enhanced metadata management
# =============================================================================

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from dbt.task.base import BaseTask
from dbt.flags import get_flags


class MetadataTask(BaseTask):
    """
    Task to manage DVT project metadata.

    This task handles:
    1. Capturing metadata from source definitions (sources.yml)
    2. Capturing metadata from materialized models
    3. Exporting metadata to various formats
    4. Clearing/resetting the metadata store
    """

    def __init__(self, args):
        super().__init__(args)
        self._metadata_store = None

    @property
    def metadata_store(self):
        """Lazy load the metadata store."""
        if self._metadata_store is None:
            from dbt.compute.metadata import ProjectMetadataStore
            project_root = Path(get_flags().PROJECT_DIR or ".")
            self._metadata_store = ProjectMetadataStore(project_root)
        return self._metadata_store

    def run(self):
        """Execute the metadata task based on subcommand."""
        subcommand = getattr(self.args, 'subcommand', 'snapshot')

        if subcommand == 'reset':
            return self.run_reset()
        elif subcommand == 'snapshot':
            return self.run_snapshot()
        elif subcommand == 'export':
            return self.run_export()
        elif subcommand == 'export-csv':
            return self.run_export_csv()
        elif subcommand == 'export-json':
            return self.run_export_json()
        else:
            # Default to snapshot
            return self.run_snapshot()

    # =========================================================================
    # Reset Subcommand
    # =========================================================================

    def run_reset(self):
        """Clear all metadata from the store."""
        from dbt.compute.metadata import ProjectMetadataStore

        project_dir = getattr(self.args, 'project_dir', None)
        project_root = Path(project_dir) if project_dir else Path(".")

        try:
            from rich.console import Console
            console = Console()
            use_rich = True
        except ImportError:
            use_rich = False

        dvt_dir = project_root / ".dvt"
        if not dvt_dir.exists():
            msg = "No .dvt directory found. Nothing to reset."
            if use_rich:
                console.print(f"[yellow]{msg}[/yellow]")
            else:
                print(msg)
            return True, True

        with ProjectMetadataStore(project_root) as store:
            store.initialize()
            store.clear_all_metadata()

        msg = "Metadata store cleared successfully."
        if use_rich:
            console.print(f"[green]✓[/green] {msg}")
        else:
            print(f"✓ {msg}")

        return True, True

    # =========================================================================
    # Snapshot Subcommand
    # =========================================================================

    def run_snapshot(self):
        """Capture metadata for all sources and materialized models."""
        from dbt.compute.metadata import ProjectMetadataStore
        from dbt.compute.metadata.store import TableMetadata, ColumnMetadata
        from dbt.compute.metadata.registry import TypeRegistry

        project_dir = getattr(self.args, 'project_dir', None)
        project_root = Path(project_dir) if project_dir else Path(".")

        # Try to use Rich for beautiful output
        try:
            from rich.console import Console
            from rich.progress import Progress, SpinnerColumn, TextColumn
            from rich.table import Table
            from rich.panel import Panel
            console = Console()
            use_rich = True
        except ImportError:
            use_rich = False

        # Ensure .dvt directory exists
        dvt_dir = project_root / ".dvt"
        if not dvt_dir.exists():
            dvt_dir.mkdir(parents=True, exist_ok=True)
            if use_rich:
                console.print(f"[cyan]Created {dvt_dir}[/cyan]")
            else:
                print(f"Created {dvt_dir}")

        # Header
        if use_rich:
            console.print(Panel.fit(
                "[bold cyan]DVT Metadata Snapshot[/bold cyan]\n"
                "Capturing metadata for sources and models",
                border_style="cyan"
            ))
            console.print()
        else:
            print("DVT Metadata Snapshot")
            print("=" * 40)
            print()

        # Load sources and models
        sources = self._load_sources(project_root)
        models = self._load_models(project_root)

        if not sources and not models:
            msg = "No sources or models found in project."
            if use_rich:
                console.print(f"[yellow]{msg}[/yellow]")
            else:
                print(msg)
            return True, True

        total_sources = len(sources)
        total_models = len(models)
        if use_rich:
            console.print(f"Found [cyan]{total_sources}[/cyan] source(s) and [cyan]{total_models}[/cyan] model(s)")
            console.print()
        else:
            print(f"Found {total_sources} source(s) and {total_models} model(s)")
            print()

        # Process sources and models
        with ProjectMetadataStore(project_root) as store:
            store.initialize()

            source_tables = 0
            source_columns = 0
            model_tables = 0
            model_columns = 0
            errors = []

            # Snapshot sources
            if sources:
                if use_rich:
                    console.print("[bold]Snapping sources...[/bold]")
                else:
                    print("Snapping sources...")

                for source_name, source_config in sources.items():
                    try:
                        t_count, c_count = self._snap_source(store, source_name, source_config)
                        source_tables += t_count
                        source_columns += c_count
                        if use_rich:
                            console.print(f"  [green]✓[/green] {source_name}: {t_count} tables, {c_count} columns")
                        else:
                            print(f"  ✓ {source_name}: {t_count} tables, {c_count} columns")
                    except Exception as e:
                        errors.append((source_name, str(e)))
                        if use_rich:
                            console.print(f"  [red]✗[/red] {source_name}: {e}")
                        else:
                            print(f"  ✗ {source_name}: {e}")

            # Snapshot models
            if models:
                if use_rich:
                    console.print()
                    console.print("[bold]Snapping models...[/bold]")
                else:
                    print()
                    print("Snapping models...")

                for model_name, model_config in models.items():
                    try:
                        t_count, c_count = self._snap_model(store, model_name, model_config)
                        model_tables += t_count
                        model_columns += c_count
                        if t_count > 0:
                            if use_rich:
                                console.print(f"  [green]✓[/green] {model_name}: {c_count} columns")
                            else:
                                print(f"  ✓ {model_name}: {c_count} columns")
                    except Exception as e:
                        errors.append((f"model:{model_name}", str(e)))
                        if use_rich:
                            console.print(f"  [red]✗[/red] {model_name}: {e}")
                        else:
                            print(f"  ✗ {model_name}: {e}")

        # Summary
        total_tables = source_tables + model_tables
        total_columns = source_columns + model_columns

        if use_rich:
            console.print()
            if errors:
                console.print(Panel(
                    f"[yellow]Completed with {len(errors)} error(s)[/yellow]\n"
                    f"Tables: {total_tables} | Columns: {total_columns}",
                    title="Summary",
                    border_style="yellow"
                ))
            else:
                console.print(Panel(
                    f"[green]Success![/green]\n"
                    f"Sources: {source_tables} tables, {source_columns} columns\n"
                    f"Models: {model_tables} tables, {model_columns} columns\n"
                    f"[dim]Saved to .dvt/metadata_store.duckdb[/dim]",
                    title="Summary",
                    border_style="green"
                ))
        else:
            print()
            print("=" * 40)
            if errors:
                print(f"Completed with {len(errors)} error(s)")
            else:
                print(f"Success: {total_tables} tables, {total_columns} columns")
            print(f"Saved to .dvt/metadata_store.duckdb")

        return len(errors) == 0, True

    # =========================================================================
    # Export Subcommand (CLI display)
    # =========================================================================

    def run_export(self):
        """Display metadata in Rich-formatted CLI output."""
        from dbt.compute.metadata import ProjectMetadataStore

        project_dir = getattr(self.args, 'project_dir', None)
        project_root = Path(project_dir) if project_dir else Path(".")

        # Try to use Rich
        try:
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel
            console = Console()
            use_rich = True
        except ImportError:
            use_rich = False

        dvt_dir = project_root / ".dvt"
        if not dvt_dir.exists():
            msg = "No .dvt directory found. Run 'dvt metadata snapshot' first."
            if use_rich:
                console.print(f"[yellow]{msg}[/yellow]")
            else:
                print(msg)
            return False, False

        with ProjectMetadataStore(project_root) as store:
            store.initialize()

            # Get all sources/tables
            all_tables = store.get_all_sources()

            if not all_tables:
                msg = "No metadata found. Run 'dvt metadata snapshot' first."
                if use_rich:
                    console.print(f"[yellow]{msg}[/yellow]")
                else:
                    print(msg)
                return True, True

            if use_rich:
                console.print(Panel.fit(
                    "[bold cyan]DVT Metadata Store[/bold cyan]",
                    border_style="cyan"
                ))
                console.print()

                # Create summary table
                table = Table(title="Captured Metadata")
                table.add_column("Type", style="cyan")
                table.add_column("Source/Model", style="green")
                table.add_column("Table", style="white")
                table.add_column("Columns", justify="right")
                table.add_column("Last Updated", style="dim")

                for source_name, table_name in all_tables:
                    metadata = store.get_table_metadata(source_name, table_name)
                    if metadata:
                        # Determine type (source or model)
                        item_type = "Model" if source_name.startswith("model:") else "Source"
                        display_name = source_name.replace("model:", "") if item_type == "Model" else source_name

                        table.add_row(
                            item_type,
                            display_name,
                            table_name,
                            str(len(metadata.columns)),
                            metadata.last_refreshed.strftime("%Y-%m-%d %H:%M") if metadata.last_refreshed else "-"
                        )

                console.print(table)

                # Stats
                stats = store.get_stats()
                console.print()
                console.print(f"[dim]Total: {stats['metadata_tables']} tables, {stats['metadata_columns']} columns[/dim]")

            else:
                print("DVT Metadata Store")
                print("=" * 60)
                print(f"{'Type':<10} {'Source/Model':<20} {'Table':<20} {'Columns':>8}")
                print("-" * 60)

                for source_name, table_name in all_tables:
                    metadata = store.get_table_metadata(source_name, table_name)
                    if metadata:
                        item_type = "Model" if source_name.startswith("model:") else "Source"
                        display_name = source_name.replace("model:", "") if item_type == "Model" else source_name
                        print(f"{item_type:<10} {display_name:<20} {table_name:<20} {len(metadata.columns):>8}")

                print("-" * 60)

        return True, True

    # =========================================================================
    # Export CSV Subcommand
    # =========================================================================

    def run_export_csv(self):
        """Export metadata to CSV file."""
        from dbt.compute.metadata import ProjectMetadataStore

        project_dir = getattr(self.args, 'project_dir', None)
        project_root = Path(project_dir) if project_dir else Path(".")
        filename = getattr(self.args, 'filename', 'metadata.csv')

        try:
            from rich.console import Console
            console = Console()
            use_rich = True
        except ImportError:
            use_rich = False

        dvt_dir = project_root / ".dvt"
        if not dvt_dir.exists():
            msg = "No .dvt directory found. Run 'dvt metadata snapshot' first."
            if use_rich:
                console.print(f"[yellow]{msg}[/yellow]")
            else:
                print(msg)
            return False, False

        with ProjectMetadataStore(project_root) as store:
            store.initialize()

            # Get all metadata as CSV
            all_tables = store.get_all_sources()

            if not all_tables:
                msg = "No metadata found. Run 'dvt metadata snapshot' first."
                if use_rich:
                    console.print(f"[yellow]{msg}[/yellow]")
                else:
                    print(msg)
                return True, True

            # Build CSV content
            import csv
            output_path = Path(filename)

            with open(output_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                # Header
                writer.writerow([
                    'type', 'source_name', 'table_name', 'column_name',
                    'adapter_type', 'spark_type', 'is_nullable', 'is_primary_key',
                    'ordinal_position', 'last_refreshed'
                ])

                # Data
                for source_name, table_name in all_tables:
                    metadata = store.get_table_metadata(source_name, table_name)
                    if metadata:
                        item_type = "model" if source_name.startswith("model:") else "source"
                        for col in metadata.columns:
                            writer.writerow([
                                item_type,
                                source_name,
                                table_name,
                                col.column_name,
                                col.adapter_type,
                                col.spark_type,
                                col.is_nullable,
                                col.is_primary_key,
                                col.ordinal_position,
                                metadata.last_refreshed.isoformat() if metadata.last_refreshed else ''
                            ])

            if use_rich:
                console.print(f"[green]✓[/green] Exported to [cyan]{output_path}[/cyan]")
            else:
                print(f"✓ Exported to {output_path}")

        return True, True

    # =========================================================================
    # Export JSON Subcommand
    # =========================================================================

    def run_export_json(self):
        """Export metadata to JSON file."""
        from dbt.compute.metadata import ProjectMetadataStore

        project_dir = getattr(self.args, 'project_dir', None)
        project_root = Path(project_dir) if project_dir else Path(".")
        filename = getattr(self.args, 'filename', 'metadata.json')

        try:
            from rich.console import Console
            console = Console()
            use_rich = True
        except ImportError:
            use_rich = False

        dvt_dir = project_root / ".dvt"
        if not dvt_dir.exists():
            msg = "No .dvt directory found. Run 'dvt metadata snapshot' first."
            if use_rich:
                console.print(f"[yellow]{msg}[/yellow]")
            else:
                print(msg)
            return False, False

        with ProjectMetadataStore(project_root) as store:
            store.initialize()

            all_tables = store.get_all_sources()

            if not all_tables:
                msg = "No metadata found. Run 'dvt metadata snapshot' first."
                if use_rich:
                    console.print(f"[yellow]{msg}[/yellow]")
                else:
                    print(msg)
                return True, True

            # Build JSON structure
            metadata_json = {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "sources": {},
                "models": {}
            }

            for source_name, table_name in all_tables:
                metadata = store.get_table_metadata(source_name, table_name)
                if metadata:
                    is_model = source_name.startswith("model:")
                    target_dict = metadata_json["models"] if is_model else metadata_json["sources"]
                    clean_name = source_name.replace("model:", "") if is_model else source_name

                    if clean_name not in target_dict:
                        target_dict[clean_name] = {
                            "adapter": metadata.adapter_name,
                            "connection": metadata.connection_name,
                            "tables": {}
                        }

                    target_dict[clean_name]["tables"][table_name] = {
                        "schema": metadata.schema_name,
                        "last_refreshed": metadata.last_refreshed.isoformat() if metadata.last_refreshed else None,
                        "columns": [
                            {
                                "name": col.column_name,
                                "adapter_type": col.adapter_type,
                                "spark_type": col.spark_type,
                                "nullable": col.is_nullable,
                                "primary_key": col.is_primary_key,
                                "position": col.ordinal_position
                            }
                            for col in metadata.columns
                        ]
                    }

            # Write JSON
            output_path = Path(filename)
            with open(output_path, 'w') as f:
                json.dump(metadata_json, f, indent=2)

            if use_rich:
                console.print(f"[green]✓[/green] Exported to [cyan]{output_path}[/cyan]")
            else:
                print(f"✓ Exported to {output_path}")

        return True, True

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _load_sources(self, project_root: Path) -> Dict[str, Dict[str, Any]]:
        """Load source definitions from the project."""
        import yaml

        sources = {}
        models_dir = project_root / "models"
        if not models_dir.exists():
            return sources

        for yml_file in models_dir.rglob("*.yml"):
            try:
                with open(yml_file) as f:
                    content = yaml.safe_load(f)

                if content and "sources" in content:
                    for source in content["sources"]:
                        source_name = source.get("name")
                        if source_name:
                            sources[source_name] = source
            except Exception:
                pass

        return sources

    def _load_models(self, project_root: Path) -> Dict[str, Dict[str, Any]]:
        """Load model metadata from catalog.json (actual database schema).

        The catalog.json is generated by `dvt docs generate` and contains
        actual column information from the database, not just what's documented
        in YAML files.
        """
        models = {}

        # Primary source: catalog.json (actual database schema)
        catalog_path = project_root / "target" / "catalog.json"
        if catalog_path.exists():
            try:
                with open(catalog_path) as f:
                    catalog = json.load(f)

                nodes = catalog.get("nodes", {})
                for node_id, node_info in nodes.items():
                    # Only process models (not seeds, tests, etc.)
                    if node_id.startswith("model."):
                        metadata = node_info.get("metadata", {})
                        columns = node_info.get("columns", {})

                        if columns:
                            model_name = metadata.get("name")
                            if model_name:
                                models[model_name] = {
                                    "name": model_name,
                                    "unique_id": node_id,
                                    "database": metadata.get("database"),
                                    "schema": metadata.get("schema"),
                                    "type": metadata.get("type"),  # TABLE, VIEW
                                    "columns": [
                                        {
                                            "name": col_info.get("name"),
                                            "data_type": col_info.get("type"),
                                            "index": col_info.get("index", 0),
                                        }
                                        for col_name, col_info in columns.items()
                                    ],
                                    "_from_catalog": True,
                                }
            except Exception as e:
                # Fall back to YAML if catalog fails
                pass

        # Fallback: YAML definitions (for models not in catalog)
        if not models:
            import yaml
            models_dir = project_root / "models"
            if models_dir.exists():
                for yml_file in models_dir.rglob("*.yml"):
                    try:
                        with open(yml_file) as f:
                            content = yaml.safe_load(f)

                        if content and "models" in content:
                            for model in content["models"]:
                                model_name = model.get("name")
                                if model_name and model.get("columns"):
                                    model["_file_path"] = str(yml_file)
                                    model["_from_catalog"] = False
                                    models[model_name] = model
                    except Exception:
                        pass

        return models

    def _snap_source(
        self,
        store,
        source_name: str,
        source_config: Dict[str, Any]
    ) -> Tuple[int, int]:
        """Snapshot metadata from a single source."""
        from dbt.compute.metadata.store import TableMetadata, ColumnMetadata
        from dbt.compute.metadata.registry import TypeRegistry

        tables_count = 0
        columns_count = 0

        schema = source_config.get("schema", "public")
        tables = source_config.get("tables", [])
        adapter_name = source_config.get("adapter", "postgres")

        for table_config in tables:
            table_name = table_config.get("name")
            if not table_name:
                continue

            columns_config = table_config.get("columns", [])
            if not columns_config:
                continue

            columns = []
            for idx, col_config in enumerate(columns_config):
                col_name = col_config.get("name")
                if not col_name:
                    continue

                adapter_type = col_config.get("data_type", "VARCHAR")
                type_info = TypeRegistry.get_spark_type(adapter_name, adapter_type)
                spark_type = type_info["spark_native_type"] if type_info else "StringType"

                columns.append(ColumnMetadata(
                    column_name=col_name,
                    adapter_type=adapter_type,
                    spark_type=spark_type,
                    is_nullable=col_config.get("nullable", True),
                    is_primary_key=col_config.get("primary_key", False),
                    ordinal_position=idx + 1,
                ))

            if columns:
                metadata = TableMetadata(
                    source_name=source_name,
                    table_name=table_name,
                    adapter_name=adapter_name,
                    connection_name=source_name,
                    schema_name=schema,
                    columns=columns,
                    last_refreshed=datetime.now(),
                )
                store.save_table_metadata(metadata)
                tables_count += 1
                columns_count += len(columns)

        return tables_count, columns_count

    def _snap_model(
        self,
        store,
        model_name: str,
        model_config: Dict[str, Any]
    ) -> Tuple[int, int]:
        """Snapshot metadata from a model definition.

        Handles both catalog-based (actual database schema) and YAML-based
        (documented columns) sources.
        """
        from dbt.compute.metadata.store import TableMetadata, ColumnMetadata
        from dbt.compute.metadata.registry import TypeRegistry

        columns_config = model_config.get("columns", [])
        if not columns_config:
            return 0, 0

        # Determine adapter type based on database in catalog
        from_catalog = model_config.get("_from_catalog", False)
        database = model_config.get("database", "")
        schema_name = model_config.get("schema", "default")

        # Infer adapter from database name in catalog
        if from_catalog:
            # Use database name to guess adapter (postgres, snowflake, etc.)
            adapter_name = self._infer_adapter_from_database(database)
        else:
            config = model_config.get("config", {})
            adapter_name = config.get("adapter_type", "postgres")

        columns = []
        for idx, col_config in enumerate(columns_config):
            col_name = col_config.get("name")
            if not col_name:
                continue

            # Get adapter type from catalog (actual DB type) or YAML
            adapter_type = col_config.get("data_type") or col_config.get("type", "STRING")

            # Convert adapter type to Spark type
            type_info = TypeRegistry.get_spark_type(adapter_name, adapter_type)
            spark_type = type_info["spark_native_type"] if type_info else "StringType"

            # For catalog-based, use index for position
            if from_catalog:
                ordinal_position = col_config.get("index", idx + 1)
            else:
                ordinal_position = idx + 1

            # Nullable defaults to True; catalog doesn't provide this info
            is_nullable = True
            is_primary_key = False

            # Check YAML tests for not_null and unique (only for YAML-based)
            if not from_catalog:
                tests = col_config.get("tests", []) or col_config.get("data_tests", [])
                if tests:
                    for test in tests:
                        if test == "not_null" or (isinstance(test, dict) and "not_null" in test):
                            is_nullable = False
                        if test == "unique" or (isinstance(test, dict) and "unique" in test):
                            is_primary_key = True

            columns.append(ColumnMetadata(
                column_name=col_name,
                adapter_type=adapter_type,
                spark_type=spark_type,
                is_nullable=is_nullable,
                is_primary_key=is_primary_key,
                ordinal_position=ordinal_position,
            ))

        if columns:
            # Sort by ordinal position for consistent output
            columns.sort(key=lambda c: c.ordinal_position)

            metadata = TableMetadata(
                source_name=f"model:{model_name}",
                table_name=model_name,
                adapter_name=adapter_name,
                connection_name="default",
                schema_name=schema_name,
                columns=columns,
                last_refreshed=datetime.now(),
            )
            store.save_table_metadata(metadata)
            return 1, len(columns)

        return 0, 0

    def _infer_adapter_from_database(self, database: str) -> str:
        """Infer adapter type from database name."""
        db_lower = database.lower() if database else ""

        # Common database name patterns
        if "postgres" in db_lower or "pg" in db_lower:
            return "postgres"
        elif "snowflake" in db_lower or "sf" in db_lower:
            return "snowflake"
        elif "databricks" in db_lower or "spark" in db_lower:
            return "databricks"
        elif "redshift" in db_lower:
            return "redshift"
        elif "bigquery" in db_lower or "bq" in db_lower:
            return "bigquery"
        elif "mysql" in db_lower:
            return "mysql"
        elif "sqlserver" in db_lower or "mssql" in db_lower:
            return "sqlserver"
        else:
            # Default to postgres as it's most common
            return "postgres"
