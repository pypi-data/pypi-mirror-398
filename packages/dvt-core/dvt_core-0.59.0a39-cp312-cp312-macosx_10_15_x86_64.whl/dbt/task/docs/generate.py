import os
import shutil
from dataclasses import replace
from datetime import datetime, timezone
from itertools import chain
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import agate

import dbt.compilation
import dbt.exceptions
import dbt.utils
import dbt_common.utils.formatting
from dbt.adapters.events.types import (
    BuildingCatalog,
    CannotGenerateDocs,
    CatalogWritten,
    WriteCatalogFailure,
)
from dbt.adapters.factory import get_adapter
from dbt.artifacts.schemas.catalog import (
    CatalogArtifact,
    CatalogKey,
    CatalogResults,
    CatalogTable,
    ColumnMetadata,
    PrimitiveDict,
    StatsDict,
    StatsItem,
    TableMetadata,
)
from dbt.artifacts.schemas.results import NodeStatus
from dbt.constants import CATALOG_FILENAME, MANIFEST_FILE_NAME
from dbt.context.providers import generate_runtime_macro_context
from dbt.contracts.graph.manifest import Manifest
from dbt.contracts.graph.nodes import ResultNode
from dbt.events.types import ArtifactWritten
from dbt.exceptions import AmbiguousCatalogMatchError
from dbt.graph import ResourceTypeSelector
from dbt.graph.graph import UniqueId
from dbt.node_types import EXECUTABLE_NODE_TYPES, NodeType
from dbt.parser.manifest import write_manifest
from dbt.task.compile import CompileTask
from dbt.task.docs import DOCS_INDEX_FILE_PATH
from dbt.utils.artifact_upload import add_artifact_produced
from dbt_common.clients.system import load_file_contents
from dbt_common.dataclass_schema import ValidationError
from dbt_common.events.functions import fire_event
from dbt_common.exceptions import DbtInternalError


def get_stripped_prefix(source: Dict[str, Any], prefix: str) -> Dict[str, Any]:
    """Go through the source, extracting every key/value pair where the key starts
    with the given prefix.
    """
    cut = len(prefix)
    return {k[cut:]: v for k, v in source.items() if k.startswith(prefix)}


def build_catalog_table(data, adapter_type: Optional[str] = None) -> CatalogTable:
    # build the new table's metadata + stats
    metadata = TableMetadata.from_dict(get_stripped_prefix(data, "table_"))
    stats = format_stats(get_stripped_prefix(data, "stats:"))

    # DVT v0.4.3: Add adapter type metadata for visualization
    # This enables adapter logos and connection badges in dbt docs
    if adapter_type:
        # Add adapter type to metadata comment for catalog display
        comment_text = metadata.comment or ""
        if comment_text and not comment_text.endswith(' '):
            comment_text += " "
        metadata = replace(
            metadata,
            comment=f"{comment_text}[adapter:{adapter_type}]"
        )

    return CatalogTable(
        metadata=metadata,
        stats=stats,
        columns={},
    )


# keys are database name, schema name, table name
class Catalog(Dict[CatalogKey, CatalogTable]):
    def __init__(self, columns: List[PrimitiveDict]) -> None:
        super().__init__()
        for col in columns:
            self.add_column(col)

    def get_table(self, data: PrimitiveDict, adapter_type: Optional[str] = None) -> CatalogTable:
        database = data.get("table_database")
        if database is None:
            dkey: Optional[str] = None
        else:
            dkey = str(database)

        try:
            key = CatalogKey(
                dkey,
                str(data["table_schema"]),
                str(data["table_name"]),
            )
        except KeyError as exc:
            raise dbt_common.exceptions.CompilationError(
                "Catalog information missing required key {} (got {})".format(exc, data)
            )
        table: CatalogTable
        if key in self:
            table = self[key]
        else:
            table = build_catalog_table(data, adapter_type)
            self[key] = table
        return table

    def add_column(self, data: PrimitiveDict):
        table = self.get_table(data)
        column_data = get_stripped_prefix(data, "column_")
        # the index should really never be that big so it's ok to end up
        # serializing this to JSON (2^53 is the max safe value there)
        column_data["index"] = int(column_data["index"])

        column = ColumnMetadata.from_dict(column_data)
        table.columns[column.name] = column

    def make_unique_id_map(
        self, manifest: Manifest, selected_node_ids: Optional[Set[UniqueId]] = None
    ) -> Tuple[Dict[str, CatalogTable], Dict[str, CatalogTable]]:
        """
        Create mappings between CatalogKeys and CatalogTables for nodes and sources, filtered by selected_node_ids.

        By default, selected_node_ids is None and all nodes and sources defined in the manifest are included in the mappings.
        """
        nodes: Dict[str, CatalogTable] = {}
        sources: Dict[str, CatalogTable] = {}

        node_map, source_map = get_unique_id_mapping(manifest)
        table: CatalogTable
        for table in self.values():
            key = table.key()
            if key in node_map:
                unique_id = node_map[key]
                if selected_node_ids is None or unique_id in selected_node_ids:
                    # DVT v0.4.3: Add comprehensive adapter and connection metadata for nodes
                    node = manifest.nodes.get(unique_id)
                    connection_name = None
                    adapter_type = None
                    compute_engine = None

                    if node:
                        # Get target connection name
                        if hasattr(node.config, 'target') and node.config.target:
                            connection_name = node.config.target

                        # Get compute engine if specified
                        if hasattr(node.config, 'compute') and node.config.compute:
                            compute_engine = node.config.compute

                    # Build metadata tags for catalog display
                    comment_text = table.metadata.comment or ""
                    tags = []

                    if connection_name:
                        tags.append(f"target:{connection_name}")
                    if compute_engine:
                        tags.append(f"compute:{compute_engine}")

                    if tags:
                        if comment_text and not comment_text.endswith(' '):
                            comment_text += " "
                        comment_text += f"[{' | '.join(tags)}]"

                    # Create updated metadata with enriched info
                    updated_metadata = replace(
                        table.metadata,
                        comment=comment_text if tags else table.metadata.comment
                    )
                    nodes[unique_id] = replace(table, unique_id=unique_id, metadata=updated_metadata)

            unique_ids = source_map.get(table.key(), set())
            for unique_id in unique_ids:
                if unique_id in sources:
                    raise AmbiguousCatalogMatchError(
                        unique_id,
                        sources[unique_id].to_dict(omit_none=True),
                        table.to_dict(omit_none=True),
                    )
                elif selected_node_ids is None or unique_id in selected_node_ids:
                    # DVT v0.4.3: Add comprehensive adapter and connection metadata for sources
                    source = manifest.sources.get(unique_id)
                    connection_name = None
                    adapter_type = None

                    if source:
                        # Get connection name for source
                        if hasattr(source, 'connection') and source.connection:
                            connection_name = source.connection

                        # Try to determine adapter type from connection
                        # Check if we can get adapter info from manifest's profile
                        if connection_name:
                            # Sources store connection name, we need to map it to adapter type
                            # This requires access to the RuntimeConfig which has the profile info
                            # For now, we'll add just the connection tag and let dbt docs UI handle it
                            pass

                    # Build metadata tags for catalog display
                    comment_text = table.metadata.comment or ""
                    tags = []

                    if connection_name:
                        tags.append(f"source:{connection_name}")

                    if tags:
                        if comment_text and not comment_text.endswith(' '):
                            comment_text += " "
                        comment_text += f"[{' | '.join(tags)}]"

                    # Create updated metadata with enriched info
                    updated_metadata = replace(
                        table.metadata,
                        comment=comment_text if tags else table.metadata.comment
                    )
                    sources[unique_id] = replace(table, unique_id=unique_id, metadata=updated_metadata)
        return nodes, sources


def format_stats(stats: PrimitiveDict) -> StatsDict:
    """Given a dictionary following this layout:

        {
            'encoded:label': 'Encoded',
            'encoded:value': 'Yes',
            'encoded:description': 'Indicates if the column is encoded',
            'encoded:include': True,

            'size:label': 'Size',
            'size:value': 128,
            'size:description': 'Size of the table in MB',
            'size:include': True,
        }

    format_stats will convert the dict into a StatsDict with keys of 'encoded'
    and 'size'.
    """
    stats_collector: StatsDict = {}

    base_keys = {k.split(":")[0] for k in stats}
    for key in base_keys:
        dct: PrimitiveDict = {"id": key}
        for subkey in ("label", "value", "description", "include"):
            dct[subkey] = stats["{}:{}".format(key, subkey)]

        try:
            stats_item = StatsItem.from_dict(dct)
        except ValidationError:
            continue
        if stats_item.include:
            stats_collector[key] = stats_item

    # we always have a 'has_stats' field, it's never included
    has_stats = StatsItem(
        id="has_stats",
        label="Has Stats?",
        value=len(stats_collector) > 0,
        description="Indicates whether there are statistics for this table",
        include=False,
    )
    stats_collector["has_stats"] = has_stats
    return stats_collector


def mapping_key(node: ResultNode) -> CatalogKey:
    dkey = dbt_common.utils.formatting.lowercase(node.database)
    return CatalogKey(dkey, node.schema.lower(), node.identifier.lower())


def get_unique_id_mapping(
    manifest: Manifest,
) -> Tuple[Dict[CatalogKey, str], Dict[CatalogKey, Set[str]]]:
    # A single relation could have multiple unique IDs pointing to it if a
    # source were also a node.
    node_map: Dict[CatalogKey, str] = {}
    source_map: Dict[CatalogKey, Set[str]] = {}
    for unique_id, node in manifest.nodes.items():
        key = mapping_key(node)
        node_map[key] = unique_id

    for unique_id, source in manifest.sources.items():
        key = mapping_key(source)
        if key not in source_map:
            source_map[key] = set()
        source_map[key].add(unique_id)
    return node_map, source_map


class GenerateTask(CompileTask):
    def run(self) -> CatalogArtifact:
        compile_results = None
        if self.args.compile:
            compile_results = CompileTask.run(self)
            if any(r.status == NodeStatus.Error for r in compile_results):
                fire_event(CannotGenerateDocs())
                return CatalogArtifact.from_results(
                    nodes={},
                    sources={},
                    generated_at=datetime.now(timezone.utc).replace(tzinfo=None),
                    errors=None,
                    compile_results=compile_results,
                )

        shutil.copyfile(
            DOCS_INDEX_FILE_PATH, os.path.join(self.config.project_target_path, "index.html")
        )

        for asset_path in self.config.asset_paths:
            to_asset_path = os.path.join(self.config.project_target_path, asset_path)

            if os.path.exists(to_asset_path):
                shutil.rmtree(to_asset_path)

            from_asset_path = os.path.join(self.config.project_root, asset_path)

            if os.path.exists(from_asset_path):
                shutil.copytree(from_asset_path, to_asset_path)

        if self.manifest is None:
            raise DbtInternalError("self.manifest was None in run!")

        selected_node_ids: Optional[Set[UniqueId]] = None
        if self.args.empty_catalog:
            catalog_table: agate.Table = agate.Table([])
            exceptions: List[Exception] = []
            selected_node_ids = set()
        else:
            # DVT v0.4.4: Multi-adapter catalog generation
            # Group catalogable nodes by their connection/adapter to avoid cross-db errors
            fire_event(BuildingCatalog())

            # Get selected nodes if applicable
            relations = None
            if self.job_queue is not None:
                selected_node_ids = self.job_queue.get_selected_nodes()
                selected_nodes = self._get_nodes_from_ids(self.manifest, selected_node_ids)

                # Source selection is handled separately
                selected_source_ids = self._get_selected_source_ids()
                selected_source_nodes = self._get_nodes_from_ids(
                    self.manifest, selected_source_ids
                )
                selected_node_ids.update(selected_source_ids)
                selected_nodes.extend(selected_source_nodes)

            # Group all catalogable nodes by their connection/adapter
            catalogable_nodes = chain(
                [
                    node
                    for node in self.manifest.nodes.values()
                    if (node.is_relational and not node.is_ephemeral_model)
                ],
                self.manifest.sources.values(),
            )

            # Group nodes by connection name
            from collections import defaultdict
            from dbt.contracts.graph.nodes import SourceDefinition

            nodes_by_connection: Dict[str, List] = defaultdict(list)
            for node in catalogable_nodes:
                # Determine which connection/adapter this node uses
                if isinstance(node, SourceDefinition):
                    # Sources use their 'connection' field or meta.connection
                    connection_name = (
                        node.connection or
                        (node.meta.get('connection') if node.meta else None) or
                        self.config.target_name
                    )
                elif hasattr(node, 'config') and hasattr(node.config, 'target') and node.config.target:
                    # Models use config.target override
                    connection_name = node.config.target
                else:
                    # Default to target connection
                    connection_name = self.config.target_name

                nodes_by_connection[connection_name].append(node)

            # Query catalog for each connection with its appropriate adapter
            all_catalog_tables: List[agate.Table] = []
            exceptions: List[Exception] = []

            for connection_name, nodes in nodes_by_connection.items():
                try:
                    # Get adapter for this connection
                    adapter = self.config.get_adapter(connection_name)

                    # DVT v0.4.7: Set macro resolver and context generator for adapter
                    adapter.set_macro_resolver(self.manifest)
                    adapter.set_macro_context_generator(generate_runtime_macro_context)

                    with adapter.connection_named(f"generate_catalog_{connection_name}"):
                        # Build relations set for this connection if we have selected nodes
                        connection_relations = None
                        if self.job_queue is not None and selected_node_ids:
                            connection_relations = {
                                adapter.Relation.create_from(adapter.config, node)
                                for node in nodes
                                if node.unique_id in selected_node_ids
                            }

                        # Get schemas used by this connection's nodes
                        connection_schemas = set()
                        for node in nodes:
                            if hasattr(node, 'schema') and node.schema:
                                if hasattr(node, 'database') and node.database:
                                    connection_schemas.add((node.database, node.schema))

                        # Query catalog for this connection's nodes
                        catalog_table_part, connection_exceptions = adapter.get_filtered_catalog(
                            nodes, connection_schemas, connection_relations
                        )

                        all_catalog_tables.append(catalog_table_part)

                        # DVT v0.4.7: Filter out "not implemented" errors from Snowflake/other adapters
                        # that don't support catalog generation
                        filtered_exceptions = [
                            e for e in connection_exceptions
                            if not ("not implemented" in str(e).lower() and
                                   isinstance(e, dbt.exceptions.CompilationError))
                        ]
                        exceptions.extend(filtered_exceptions)

                except dbt.exceptions.CompilationError as e:
                    # DVT v0.4.9: Universal fallback for adapters without get_catalog_relations
                    if "not implemented" in str(e).lower():
                        try:
                            # Try INFORMATION_SCHEMA fallback (works for most SQL databases)
                            catalog_table_part = self._get_catalog_via_information_schema(
                                adapter, connection_name, connection_schemas
                            )
                            if catalog_table_part and len(catalog_table_part) > 0:
                                all_catalog_tables.append(catalog_table_part)
                                fire_event(
                                    BuildingCatalog()  # Log success
                                )
                        except Exception as fallback_ex:
                            # DVT v0.4.9: Log fallback errors for debugging
                            import traceback
                            fire_event(
                                CannotGenerateDocs(
                                    msg=f"INFORMATION_SCHEMA fallback failed for '{connection_name}': {str(fallback_ex)}\n{traceback.format_exc()}"
                                )
                            )
                    else:
                        # Other compilation errors should be reported
                        exceptions.append(e)
                except Exception as e:
                    # Log error but continue with other connections
                    exceptions.append(e)

            # Merge all catalog tables into one
            if all_catalog_tables:
                # Merge by concatenating rows from all tables
                if len(all_catalog_tables) == 1:
                    catalog_table = all_catalog_tables[0]
                else:
                    # Combine all tables - they should have the same columns
                    catalog_table = agate.Table.merge(all_catalog_tables)
            else:
                catalog_table = agate.Table([])

        catalog_data: List[PrimitiveDict] = [
            dict(zip(catalog_table.column_names, map(dbt.utils._coerce_decimal, row)))
            for row in catalog_table
        ]

        catalog = Catalog(catalog_data)

        errors: Optional[List[str]] = None
        if exceptions:
            errors = [str(e) for e in exceptions]

        nodes, sources = catalog.make_unique_id_map(self.manifest, selected_node_ids)
        results = self.get_catalog_results(
            nodes=nodes,
            sources=sources,
            generated_at=datetime.now(timezone.utc).replace(tzinfo=None),
            compile_results=compile_results,
            errors=errors,
        )

        catalog_path = os.path.join(self.config.project_target_path, CATALOG_FILENAME)
        results.write(catalog_path)
        add_artifact_produced(catalog_path)
        fire_event(
            ArtifactWritten(artifact_type=results.__class__.__name__, artifact_path=catalog_path)
        )

        if self.args.compile:
            write_manifest(self.manifest, self.config.project_target_path)

        if self.args.static:

            # Read manifest.json and catalog.json
            read_manifest_data = load_file_contents(
                os.path.join(self.config.project_target_path, MANIFEST_FILE_NAME)
            )
            read_catalog_data = load_file_contents(catalog_path)

            # Create new static index file contents
            index_data = load_file_contents(DOCS_INDEX_FILE_PATH)
            index_data = index_data.replace('"MANIFEST.JSON INLINE DATA"', read_manifest_data)
            index_data = index_data.replace('"CATALOG.JSON INLINE DATA"', read_catalog_data)

            # Write out the new index file
            static_index_path = os.path.join(self.config.project_target_path, "static_index.html")
            with open(static_index_path, "wb") as static_index_file:
                static_index_file.write(bytes(index_data, "utf8"))

        if exceptions:
            fire_event(WriteCatalogFailure(num_exceptions=len(exceptions)))
        fire_event(CatalogWritten(path=os.path.abspath(catalog_path)))

        # DVT v0.56.0: Write enriched catalog to metadata_store.duckdb
        self._write_catalog_to_duckdb(nodes, sources)
        self._write_lineage_to_duckdb()

        return results

    def get_node_selector(self) -> ResourceTypeSelector:
        if self.manifest is None or self.graph is None:
            raise DbtInternalError("manifest and graph must be set to perform node selection")
        return ResourceTypeSelector(
            graph=self.graph,
            manifest=self.manifest,
            previous_state=self.previous_state,
            resource_types=EXECUTABLE_NODE_TYPES,
            include_empty_nodes=True,
        )

    def get_catalog_results(
        self,
        nodes: Dict[str, CatalogTable],
        sources: Dict[str, CatalogTable],
        generated_at: datetime,
        compile_results: Optional[Any],
        errors: Optional[List[str]],
    ) -> CatalogArtifact:
        return CatalogArtifact.from_results(
            generated_at=generated_at,
            nodes=nodes,
            sources=sources,
            compile_results=compile_results,
            errors=errors,
        )

    @classmethod
    def interpret_results(self, results: Optional[CatalogResults]) -> bool:
        if results is None:
            return False
        if results.errors:
            return False
        compile_results = results._compile_results
        if compile_results is None:
            return True

        return super().interpret_results(compile_results)

    @staticmethod
    def _get_nodes_from_ids(manifest: Manifest, node_ids: Iterable[str]) -> List[ResultNode]:
        selected: List[ResultNode] = []
        for unique_id in node_ids:
            if unique_id in manifest.nodes:
                node = manifest.nodes[unique_id]
                if node.is_relational and not node.is_ephemeral_model:
                    selected.append(node)
            elif unique_id in manifest.sources:
                source = manifest.sources[unique_id]
                selected.append(source)
        return selected

    def _get_selected_source_ids(self) -> Set[UniqueId]:
        if self.manifest is None or self.graph is None:
            raise DbtInternalError("manifest and graph must be set to perform node selection")

        source_selector = ResourceTypeSelector(
            graph=self.graph,
            manifest=self.manifest,
            previous_state=self.previous_state,
            resource_types=[NodeType.Source],
        )

        return source_selector.get_graph_queue(self.get_selection_spec()).get_selected_nodes()

    def _get_catalog_via_information_schema(
        self, adapter, connection_name: str, schemas: Set[Tuple[str, str]]
    ) -> agate.Table:
        """
        DVT v0.4.8: Universal fallback for catalog generation using INFORMATION_SCHEMA.

        Works for most SQL databases (Postgres, MySQL, Snowflake, Redshift, BigQuery, SQL Server).
        Falls back gracefully for databases without INFORMATION_SCHEMA (Oracle, DB2).

        :param adapter: Database adapter
        :param connection_name: Connection name for logging
        :param schemas: Set of (database, schema) tuples to query
        :return: agate.Table with catalog data
        """
        if not schemas:
            return agate.Table([])

        # Build WHERE clause for schemas
        schema_conditions = []
        for database, schema in schemas:
            # Most databases only need schema filter, some need database too
            schema_conditions.append(f"table_schema = '{schema}'")

        where_clause = " OR ".join(schema_conditions)

        # Universal INFORMATION_SCHEMA query (works for most SQL databases)
        query = f"""
        SELECT
            table_catalog as table_database,
            table_schema,
            table_name,
            column_name,
            data_type,
            ordinal_position as column_index
        FROM information_schema.columns
        WHERE {where_clause}
        ORDER BY table_schema, table_name, ordinal_position
        """

        try:
            # Execute query using adapter's connection
            _, result = adapter.execute(query, auto_begin=False, fetch=True)

            # Convert to agate.Table format expected by catalog
            if result and len(result) > 0:
                # Transform result into catalog format
                catalog_data = []
                for row in result:
                    catalog_data.append({
                        'table_database': row[0],
                        'table_schema': row[1],
                        'table_name': row[2],
                        'column_name': row[3],
                        'column_type': row[4],
                        'column_index': row[5]
                    })

                # Create agate.Table with proper column types
                return agate.Table(catalog_data)
            else:
                return agate.Table([])

        except Exception as e:
            # Fallback failed - database might not support INFORMATION_SCHEMA
            # (e.g., Oracle, DB2, or permission issues)
            fire_event(
                CannotGenerateDocs(
                    msg=f"INFORMATION_SCHEMA fallback failed for '{connection_name}': {str(e)}"
                )
            )
            return agate.Table([])

    # =========================================================================
    # DVT v0.56.0: DuckDB Catalog and Lineage Storage
    # =========================================================================

    def _write_catalog_to_duckdb(
        self,
        nodes: Dict[str, CatalogTable],
        sources: Dict[str, CatalogTable],
    ) -> None:
        """
        Write enriched catalog to metadata_store.duckdb.

        DVT v0.56.0: Stores catalog nodes with connection info, adapter type,
        and visual enrichment (icons, colors) for enhanced docs serve.
        """
        try:
            import json
            from pathlib import Path
            from dbt.compute.metadata import ProjectMetadataStore, CatalogNode

            project_root = Path(self.config.project_root)
            store = ProjectMetadataStore(project_root)
            store.initialize()

            # Clear existing catalog data
            store.clear_catalog_nodes()

            # Adapter icon mapping
            adapter_icons = {
                'postgres': 'postgresql',
                'snowflake': 'snowflake',
                'bigquery': 'bigquery',
                'redshift': 'redshift',
                'databricks': 'databricks',
                'spark': 'spark',
                'duckdb': 'duckdb',
                'mysql': 'mysql',
                'sqlserver': 'sqlserver',
                'oracle': 'oracle',
            }

            # Connection color mapping (for visual distinction)
            connection_colors = [
                '#3498db',  # Blue
                '#2ecc71',  # Green
                '#e74c3c',  # Red
                '#9b59b6',  # Purple
                '#f39c12',  # Orange
                '#1abc9c',  # Teal
                '#e91e63',  # Pink
                '#607d8b',  # Blue Grey
            ]
            color_index = 0
            connection_color_map: Dict[str, str] = {}

            # Process nodes (models)
            for unique_id, table in nodes.items():
                node = self.manifest.nodes.get(unique_id) if self.manifest else None

                # Get connection and adapter info
                connection_name = "default"
                adapter_type = None
                materialized = None
                tags = []
                meta = {}

                if node:
                    if hasattr(node.config, 'target') and node.config.target:
                        connection_name = node.config.target
                    if hasattr(node.config, 'materialized'):
                        materialized = node.config.materialized
                    if hasattr(node, 'tags'):
                        tags = list(node.tags)
                    if hasattr(node, 'meta'):
                        meta = dict(node.meta) if node.meta else {}

                # Assign connection color
                if connection_name not in connection_color_map:
                    connection_color_map[connection_name] = connection_colors[color_index % len(connection_colors)]
                    color_index += 1

                # Get adapter type from connection
                try:
                    adapter = self.config.get_adapter(connection_name)
                    adapter_type = adapter.type() if hasattr(adapter, 'type') else None
                except Exception:
                    adapter_type = None

                icon_type = adapter_icons.get(adapter_type, 'database') if adapter_type else 'database'

                # Serialize columns
                columns_data = []
                for col_name, col_meta in table.columns.items():
                    columns_data.append({
                        'name': col_name,
                        'type': col_meta.type if hasattr(col_meta, 'type') else None,
                        'comment': col_meta.comment if hasattr(col_meta, 'comment') else None,
                    })

                # Get row count from stats
                row_count = None
                if hasattr(table, 'stats') and table.stats:
                    for stat_id, stat in table.stats.items():
                        if stat_id == 'row_count' and hasattr(stat, 'value'):
                            try:
                                row_count = int(stat.value)
                            except (ValueError, TypeError):
                                pass

                catalog_node = CatalogNode(
                    unique_id=unique_id,
                    resource_type='model',
                    name=node.name if node else table.metadata.name,
                    schema_name=table.metadata.schema,
                    database=table.metadata.database,
                    connection_name=connection_name,
                    adapter_type=adapter_type,
                    description=node.description if node and hasattr(node, 'description') else None,
                    icon_type=icon_type,
                    color_hex=connection_color_map.get(connection_name),
                    materialized=materialized,
                    tags=json.dumps(tags) if tags else None,
                    meta=json.dumps(meta) if meta else None,
                    columns=json.dumps(columns_data) if columns_data else None,
                    row_count=row_count,
                )
                store.save_catalog_node(catalog_node)

            # Process sources
            for unique_id, table in sources.items():
                source = self.manifest.sources.get(unique_id) if self.manifest else None

                # Get connection and adapter info
                connection_name = "default"
                adapter_type = None
                tags = []
                meta = {}

                if source:
                    if hasattr(source, 'connection') and source.connection:
                        connection_name = source.connection
                    elif hasattr(source, 'meta') and source.meta and source.meta.get('connection'):
                        connection_name = source.meta.get('connection')
                    if hasattr(source, 'tags'):
                        tags = list(source.tags)
                    if hasattr(source, 'meta'):
                        meta = dict(source.meta) if source.meta else {}

                # Assign connection color
                if connection_name not in connection_color_map:
                    connection_color_map[connection_name] = connection_colors[color_index % len(connection_colors)]
                    color_index += 1

                # Get adapter type from connection
                try:
                    adapter = self.config.get_adapter(connection_name)
                    adapter_type = adapter.type() if hasattr(adapter, 'type') else None
                except Exception:
                    adapter_type = None

                icon_type = adapter_icons.get(adapter_type, 'database') if adapter_type else 'database'

                # Serialize columns
                columns_data = []
                for col_name, col_meta in table.columns.items():
                    columns_data.append({
                        'name': col_name,
                        'type': col_meta.type if hasattr(col_meta, 'type') else None,
                        'comment': col_meta.comment if hasattr(col_meta, 'comment') else None,
                    })

                catalog_node = CatalogNode(
                    unique_id=unique_id,
                    resource_type='source',
                    name=source.name if source else table.metadata.name,
                    schema_name=table.metadata.schema,
                    database=table.metadata.database,
                    connection_name=connection_name,
                    adapter_type=adapter_type,
                    description=source.description if source and hasattr(source, 'description') else None,
                    icon_type=icon_type,
                    color_hex=connection_color_map.get(connection_name),
                    tags=json.dumps(tags) if tags else None,
                    meta=json.dumps(meta) if meta else None,
                    columns=json.dumps(columns_data) if columns_data else None,
                )
                store.save_catalog_node(catalog_node)

            store.close()
            fire_event(CatalogWritten(path=str(store.db_path)))

        except ImportError:
            # DuckDB not installed - skip
            pass
        except Exception as e:
            # Log but don't fail catalog generation
            fire_event(
                CannotGenerateDocs(msg=f"Could not write catalog to DuckDB: {str(e)}")
            )

    def _write_lineage_to_duckdb(self) -> None:
        """
        Write lineage edges to metadata_store.duckdb.

        DVT v0.56.0: Stores full DAG with cross-connection indicators
        for enhanced visualization in docs serve.
        """
        if self.manifest is None:
            return

        try:
            from pathlib import Path
            from dbt.compute.metadata import ProjectMetadataStore, LineageEdge

            project_root = Path(self.config.project_root)
            store = ProjectMetadataStore(project_root)
            store.initialize()

            # Clear existing lineage data
            store.clear_lineage_edges()

            # Build connection map for cross-connection detection
            node_connections: Dict[str, str] = {}

            # Map nodes to connections
            for unique_id, node in self.manifest.nodes.items():
                if hasattr(node.config, 'target') and node.config.target:
                    node_connections[unique_id] = node.config.target
                else:
                    node_connections[unique_id] = self.config.target_name

            # Map sources to connections
            for unique_id, source in self.manifest.sources.items():
                if hasattr(source, 'connection') and source.connection:
                    node_connections[unique_id] = source.connection
                elif hasattr(source, 'meta') and source.meta and source.meta.get('connection'):
                    node_connections[unique_id] = source.meta.get('connection')
                else:
                    node_connections[unique_id] = self.config.target_name

            # Process dependencies
            for unique_id, node in self.manifest.nodes.items():
                if not hasattr(node, 'depends_on') or not node.depends_on:
                    continue

                target_connection = node_connections.get(unique_id, self.config.target_name)

                # Process node dependencies
                for dep_id in node.depends_on.nodes:
                    source_connection = node_connections.get(dep_id, self.config.target_name)

                    # Determine edge type
                    if dep_id.startswith('source.'):
                        edge_type = 'source'
                    elif dep_id.startswith('model.'):
                        edge_type = 'ref'
                    else:
                        edge_type = 'depends_on'

                    is_cross = source_connection != target_connection

                    edge = LineageEdge(
                        source_node_id=dep_id,
                        target_node_id=unique_id,
                        edge_type=edge_type,
                        is_cross_connection=is_cross,
                        source_connection=source_connection,
                        target_connection=target_connection,
                    )
                    store.save_lineage_edge(edge)

            store.close()

        except ImportError:
            # DuckDB not installed - skip
            pass
        except Exception as e:
            # Log but don't fail
            fire_event(
                CannotGenerateDocs(msg=f"Could not write lineage to DuckDB: {str(e)}")
            )
