from __future__ import annotations

import functools
import threading
import time
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
from typing import AbstractSet, Any, Dict, Iterable, List, Optional, Set, Tuple, Type

from dbt import tracking, utils
from dbt.adapters.base import BaseAdapter, BaseRelation
from dbt.adapters.capability import Capability
from dbt.adapters.events.types import FinishedRunningStats
from dbt.adapters.exceptions import MissingMaterializationError
from dbt.artifacts.resources import Hook
from dbt.artifacts.schemas.batch_results import BatchResults, BatchType
from dbt.artifacts.schemas.results import (
    NodeStatus,
    RunningStatus,
    RunStatus,
    TimingInfo,
    collect_timing_info,
)
from dbt.artifacts.schemas.run import RunResult
from dbt.cli.flags import Flags
from dbt.clients.jinja import MacroGenerator
from dbt.config import RuntimeConfig
from dbt.context.providers import generate_runtime_model_context
from dbt.contracts.graph.manifest import Manifest
from dbt.contracts.graph.nodes import BatchContext, HookNode, ModelNode, ResultNode
from dbt.events.types import (
    GenericExceptionOnRun,
    LogBatchResult,
    LogHookEndLine,
    LogHookStartLine,
    LogModelResult,
    LogStartBatch,
    LogStartLine,
    MicrobatchExecutionDebug,
)
from dbt.exceptions import CompilationError, DbtInternalError, DbtRuntimeError, DbtValidationError
from dbt.graph import ResourceTypeSelector
from dbt.graph.thread_pool import DbtThreadPool
from dbt.hooks import get_hook_dict
from dbt.materializations.incremental.microbatch import MicrobatchBuilder
from dbt.node_types import NodeType, RunHookType
from dbt.task import group_lookup
from dbt.task.base import BaseRunner
from dbt.task.compile import CompileRunner, CompileTask
# DVT: Import query analysis and federated execution components
from dbt.query_analyzer import QueryAnalyzer
from dbt.compute.federated_executor import FederatedExecutor
from dbt.compute.smart_selector import SmartComputeSelector
from dbt.task.printer import get_counts, print_run_end_messages
from dbt.utils.artifact_upload import add_artifact_produced
from dbt_common.clients.jinja import MacroProtocol
from dbt_common.dataclass_schema import dbtClassMixin
from dbt_common.events.base_types import EventLevel
from dbt_common.events.contextvars import log_contextvars
from dbt_common.events.functions import fire_event, get_invocation_id
from dbt_common.events.types import Formatting
from dbt_common.exceptions import DbtValidationError
from dbt_common.invocation import get_invocation_started_at


@functools.total_ordering
class BiggestName(str):
    def __lt__(self, other):
        return True

    def __eq__(self, other):
        return isinstance(other, self.__class__)


def _hook_list() -> List[HookNode]:
    return []


def get_hooks_by_tags(
    nodes: Iterable[ResultNode],
    match_tags: Set[str],
) -> List[HookNode]:
    matched_nodes = []
    for node in nodes:
        if not isinstance(node, HookNode):
            continue
        node_tags = node.tags
        if len(set(node_tags) & match_tags):
            matched_nodes.append(node)
    return matched_nodes


def get_hook(source, index):
    hook_dict = get_hook_dict(source)
    hook_dict.setdefault("index", index)
    Hook.validate(hook_dict)
    return Hook.from_dict(hook_dict)


def get_execution_status(sql: str, adapter: BaseAdapter) -> Tuple[RunStatus, str]:
    if not sql.strip():
        return RunStatus.Success, "OK"

    try:
        response, _ = adapter.execute(sql, auto_begin=False, fetch=False)
        status = RunStatus.Success
        message = response._message
    except (KeyboardInterrupt, SystemExit):
        raise
    except DbtRuntimeError as exc:
        status = RunStatus.Error
        message = exc.msg
    except Exception as exc:
        status = RunStatus.Error
        message = str(exc)

    return (status, message)


def _get_adapter_info(adapter, run_model_result) -> Dict[str, Any]:
    """Each adapter returns a dataclass with a flexible dictionary for
    adapter-specific fields. Only the non-'model_adapter_details' fields
    are guaranteed cross adapter."""
    return asdict(adapter.get_adapter_run_info(run_model_result.node.config)) if adapter else {}


def track_model_run(index, num_nodes, run_model_result, adapter=None):
    if tracking.active_user is None:
        raise DbtInternalError("cannot track model run with no active user")
    invocation_id = get_invocation_id()
    node = run_model_result.node
    has_group = True if hasattr(node, "group") and node.group else False
    if node.resource_type == NodeType.Model:
        access = node.access.value if node.access is not None else None
        contract_enforced = node.contract.enforced
        versioned = True if node.version else False
        incremental_strategy = node.config.incremental_strategy
    else:
        access = None
        contract_enforced = False
        versioned = False
        incremental_strategy = None

    tracking.track_model_run(
        {
            "invocation_id": invocation_id,
            "index": index,
            "total": num_nodes,
            "execution_time": run_model_result.execution_time,
            "run_status": str(run_model_result.status).upper(),
            "run_skipped": run_model_result.status == NodeStatus.Skipped,
            "run_error": run_model_result.status == NodeStatus.Error,
            "model_materialization": node.get_materialization(),
            "model_incremental_strategy": incremental_strategy,
            "model_id": utils.get_hash(node),
            "hashed_contents": utils.get_hashed_contents(node),
            "timing": [t.to_dict(omit_none=True) for t in run_model_result.timing],
            "language": str(node.language),
            "has_group": has_group,
            "contract_enforced": contract_enforced,
            "access": access,
            "versioned": versioned,
            "adapter_info": _get_adapter_info(adapter, run_model_result),
        }
    )


# make sure that we got an ok result back from a materialization
def _validate_materialization_relations_dict(inp: Dict[Any, Any], model) -> List[BaseRelation]:
    try:
        relations_value = inp["relations"]
    except KeyError:
        msg = (
            'Invalid return value from materialization, "relations" '
            "not found, got keys: {}".format(list(inp))
        )
        raise CompilationError(msg, node=model) from None

    if not isinstance(relations_value, list):
        msg = (
            'Invalid return value from materialization, "relations" '
            "not a list, got: {}".format(relations_value)
        )
        raise CompilationError(msg, node=model) from None

    relations: List[BaseRelation] = []
    for relation in relations_value:
        if not isinstance(relation, BaseRelation):
            msg = (
                "Invalid return value from materialization, "
                '"relations" contains non-Relation: {}'.format(relation)
            )
            raise CompilationError(msg, node=model)

        assert isinstance(relation, BaseRelation)
        relations.append(relation)
    return relations


class ModelRunner(CompileRunner):
    def get_node_representation(self):
        display_quote_policy = {"database": False, "schema": False, "identifier": False}
        relation = self.adapter.Relation.create_from(
            self.config, self.node, quote_policy=display_quote_policy
        )
        # exclude the database from output if it's the default
        if self.node.database == self.config.credentials.database:
            relation = relation.include(database=False)
        return str(relation)

    def describe_node(self) -> str:
        # TODO CL 'language' will be moved to node level when we change representation
        return f"{self.node.language} {self.node.get_materialization()} model {self.get_node_representation()}"

    def print_start_line(self):
        fire_event(
            LogStartLine(
                description=self.describe_node(),
                index=self.node_index,
                total=self.num_nodes,
                node_info=self.node.node_info,
            )
        )

    def print_result_line(self, result):
        description = self.describe_node()
        group = group_lookup.get(self.node.unique_id)
        if result.status == NodeStatus.Error:
            status = result.status
            level = EventLevel.ERROR
        else:
            status = result.message
            level = EventLevel.INFO
        fire_event(
            LogModelResult(
                description=description,
                status=status,
                index=self.node_index,
                total=self.num_nodes,
                execution_time=result.execution_time,
                node_info=self.node.node_info,
                group=group,
            ),
            level=level,
        )

    def before_execute(self) -> None:
        self.print_start_line()

    def after_execute(self, result) -> None:
        track_model_run(self.node_index, self.num_nodes, result, adapter=self.adapter)
        self.print_result_line(result)

    def _build_run_model_result(self, model, context, elapsed_time: float = 0.0):
        result = context["load_result"]("main")
        if not result:
            raise DbtRuntimeError("main is not being called during running model")
        adapter_response = {}
        if isinstance(result.response, dbtClassMixin):
            adapter_response = result.response.to_dict(omit_none=True)
        return RunResult(
            node=model,
            status=RunStatus.Success,
            timing=[],
            thread_id=threading.current_thread().name,
            execution_time=elapsed_time,
            message=str(result.response),
            adapter_response=adapter_response,
            failures=result.get("failures"),
            batch_results=None,
        )

    def _materialization_relations(self, result: Any, model) -> List[BaseRelation]:
        if isinstance(result, str):
            msg = (
                'The materialization ("{}") did not explicitly return a '
                "list of relations to add to the cache.".format(str(model.get_materialization()))
            )
            raise CompilationError(msg, node=model)

        if isinstance(result, dict):
            return _validate_materialization_relations_dict(result, model)

        msg = (
            "Invalid return value from materialization, expected a dict "
            'with key "relations", got: {}'.format(str(result))
        )
        raise CompilationError(msg, node=model)

    def _write_to_file_database(
        self,
        spark_df,
        target_adapter,
        target_table: str,
        adapter_type: str,
    ) -> None:
        """
        Write Spark DataFrame to file-based databases (DuckDB, SQLite).

        DVT v0.59.0a30: These databases don't support concurrent JDBC writes.
        DVT v0.59.0a31: Use the ADAPTER's connection to ensure tables are visible
        to subsequent pushdown queries (fixes connection isolation issue).

        :param spark_df: PySpark DataFrame to write
        :param target_adapter: dbt adapter instance (used to get its connection)
        :param target_table: Target table name (schema.table format)
        :param adapter_type: 'duckdb' or 'sqlite'
        """
        # Convert Spark DataFrame to Pandas
        pandas_df = spark_df.toPandas()

        # Parse schema and table from target_table
        # Can be: "table", "schema.table", or "database.schema.table"
        parts = target_table.split('.')
        if len(parts) == 3:
            # database.schema.table - for DuckDB, ignore database (it's the file)
            _, schema_name, table_name = parts
        elif len(parts) == 2:
            schema_name, table_name = parts
        else:
            schema_name = "main"
            table_name = target_table

        if adapter_type == 'duckdb':
            # Use the ADAPTER's connection to ensure visibility
            # dbt-duckdb's handle is a DuckDBConnectionWrapper with cursor() method
            with target_adapter.connection_named('federation_write'):
                connection = target_adapter.connections.get_thread_connection()
                handle = connection.handle

                # Get the cursor (DuckDBCursorWrapper) and its underlying raw cursor
                cursor_wrapper = handle.cursor()
                raw_cursor = cursor_wrapper._cursor  # Access the raw DuckDB cursor

                # Create schema if not exists
                raw_cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
                # Drop existing table
                raw_cursor.execute(f'DROP TABLE IF EXISTS "{schema_name}"."{table_name}"')
                # Register pandas DataFrame and create table
                raw_cursor.register('_dvt_temp_df', pandas_df)
                raw_cursor.execute(f'CREATE TABLE "{schema_name}"."{table_name}" AS SELECT * FROM _dvt_temp_df')
                raw_cursor.unregister('_dvt_temp_df')

        elif adapter_type == 'sqlite':
            # SQLite: Use adapter's connection similarly
            with target_adapter.connection_named('federation_write'):
                connection = target_adapter.connections.get_thread_connection()
                handle = connection.handle

                # Parse table name (SQLite doesn't have schemas)
                table_name_only = parts[-1]

                # Use pandas to_sql with the adapter's connection
                pandas_df.to_sql(table_name_only, handle, if_exists='replace', index=False)

    def _execute_model(
        self,
        hook_ctx: Any,
        context_config: Any,
        model: ModelNode,
        context: Dict[str, Any],
        materialization_macro: MacroProtocol,
    ) -> RunResult:
        try:
            result = MacroGenerator(
                materialization_macro, context, stack=context["context_macro_stack"]
            )()
        finally:
            self.adapter.post_model_hook(context_config, hook_ctx)

        for relation in self._materialization_relations(result, model):
            self.adapter.cache_added(relation.incorporate(dbt_created=True))

        return self._build_run_model_result(model, context)

    def execute(self, model, manifest):
        # DVT: Analyze query for execution strategy
        analyzer = QueryAnalyzer(manifest)

        # DVT v0.51.1: Fix --target-compute logic
        # CLI --target-compute should ONLY override models that:
        # 1. Already have compute= config in their model definition, OR
        # 2. Require federated execution (multi-source)
        #
        # Models without compute= config should ALWAYS favor pushdown
        # (adapter-native execution) when possible.
        cli_compute = getattr(self.config.args, 'TARGET_COMPUTE', None)
        model_compute = model.config.compute if hasattr(model.config, 'compute') else None

        # DVT v0.51.6: Target Hierarchy (Rule 2.1):
        #   Level 1 (Lowest): profiles.yml default target
        #   Level 2: Model-specific target config
        #   Level 3 (Highest): CLI --target argument (Forces Global Target Override)
        #
        # Rule 2.2: If CLI --target is used, ALL models are forced to materialize in this target.
        cli_target = getattr(self.config.args, 'TARGET', None)
        model_target = model.config.target if hasattr(model.config, 'target') else None

        # CLI --target (Level 3) overrides model config (Level 2) which overrides profile default (Level 1)
        if cli_target:
            target_connection = cli_target  # CLI always wins
        elif model_target:
            target_connection = model_target  # Model config
        else:
            target_connection = self.config.target_name  # Profile default

        # First, analyze WITHOUT any compute override to see if federation is required
        # Pass target_connection to detect cross-adapter scenarios
        natural_analysis = analyzer.analyze(
            model,
            user_compute_override=None,
            target_connection=target_connection
        )

        # DVT v0.51.6: Rule 3.C.3 - View coercion in cross-target scenarios
        # Views are SQL definitions that reference tables by name.
        # You CANNOT create a cross-database view - it's physically impossible.
        # If federation is required, views MUST be coerced to tables with a warning.
        materialization = model.get_materialization()
        convert_view_to_table = False
        if materialization == 'view' and natural_analysis.is_federated:
            convert_view_to_table = True
            # Rule 3.C.3: Log warning about view coercion
            import sys
            print(
                f"[DVT Warning] Model '{model.name}' is configured as 'view' but requires federation. "
                f"Materializing as TABLE instead. (Cross-database views are not supported)",
                file=sys.stderr
            )

        # DVT v0.51.6: Rule 1.5 - Compute engine only applies to Federation path
        # Compute Selection Hierarchy (Rule 1.3):
        #   Level 1: Default compute in computes.yml
        #   Level 2: Model-specific compute config
        #   Level 3: CLI --compute argument
        # BUT: Compute settings are IGNORED for Pushdown-eligible models (Rule 1.5)

        if natural_analysis.is_federated:
            # Federation required - apply compute hierarchy
            if cli_compute:
                user_compute = cli_compute  # Level 3 (highest)
            elif model_compute:
                user_compute = model_compute  # Level 2
            else:
                user_compute = None  # Will use Level 1 default from selector
        else:
            # Pushdown-eligible - Rule 1.5: IGNORE compute settings
            user_compute = None

        # Use the natural analysis (compute override doesn't change pushdown/federation decision)
        analysis = natural_analysis

        # Get target adapter (for materialization)
        # DVT v0.51.6: Use target_connection which follows Rule 2.1 hierarchy
        target_adapter = self.config.get_adapter(target_connection)

        if analysis.is_pushdown:
            # Pushdown execution: Use source adapter directly
            execution_adapter = self.config.get_adapter(analysis.primary_connection)

            context = generate_runtime_model_context(model, self.config, manifest)

            # Execute using existing path but with correct adapter
            materialization_macro = manifest.find_materialization_macro_by_name(
                self.config.project_name,
                model.get_materialization(),
                execution_adapter.type()
            )

            if materialization_macro is None:
                raise MissingMaterializationError(
                    materialization=model.get_materialization(), adapter_type=execution_adapter.type()
                )

            if "config" not in context:
                raise DbtInternalError(
                    "Invalid materialization context generated, missing config: {}".format(context)
                )
            context_config = context["config"]

            mat_has_supported_langs = hasattr(materialization_macro, "supported_languages")
            model_lang_supported = model.language in materialization_macro.supported_languages
            if mat_has_supported_langs and not model_lang_supported:
                str_langs = [str(lang) for lang in materialization_macro.supported_languages]
                raise DbtValidationError(
                    f'Materialization "{materialization_macro.name}" only supports languages {str_langs}; '
                    f'got "{model.language}"'
                )

            # DVT v0.59.0a29: Removed pre-drop CASCADE from pushdown path
            # dbt-adapters manages table drop/swap during materialization
            # Pre-drop CASCADE interferes with dbt's materialization process
            # (dbt checks for existing relation during swap, errors if not found)
            #
            # Note: Federation path still uses pre-drop CASCADE because Spark JDBC
            # mode="overwrite" doesn't use CASCADE when dropping.

            # Run hooks
            hook_ctx = execution_adapter.pre_model_hook(context_config)
            result = self._execute_model(hook_ctx, context_config, model, context, materialization_macro)

            return result
        else:
            # Federated execution: Use compute layer
            executor = FederatedExecutor(
                manifest=manifest,
                adapters=self.config.adapters or {},
                default_compute_engine='spark-local'
            )

            # Select compute engine
            if user_compute:
                compute_engine = user_compute
            else:
                selector = SmartComputeSelector(manifest)
                compute_engine = selector.select_engine(model, analysis)

            # Execute federally (pass target adapter type for JDBC materialization)
            # DVT v0.51.6: Pass view coercion flag so executor treats view as table
            fed_result = executor.execute(
                node=model,
                analysis_result=analysis,
                compute_engine_override=compute_engine,
                target_adapter_type=target_adapter.type() if target_adapter else None,
                coerce_view_to_table=convert_view_to_table,
            )

            try:
                # Materialize to target via Spark JDBC
                # DVT v0.51.7: Use 3-part naming (database.schema.table) for adapters like Databricks
                if hasattr(model, 'database') and model.database:
                    target_table = f"{model.database}.{model.schema}.{model.alias}"
                else:
                    target_table = f"{model.schema}.{model.alias}"

                # Get Spark DataFrame from result
                spark_df = fed_result.spark_dataframe

                # DVT v0.58.6: Inline JDBC write to avoid segfault with FederatedExecutor method call
                # This is a known issue with PySpark 4.0 + Java 21 on macOS
                from dbt.adapters.contracts.connection import AdapterResponse

                target_credentials = target_adapter.config.credentials
                adapter_type = target_adapter.type()

                # DVT v0.59.0a30: Special handling for file-based databases
                # DuckDB and SQLite don't support concurrent writes via JDBC
                # Use the ADAPTER's connection to ensure visibility to subsequent queries
                if adapter_type in ('duckdb', 'sqlite'):
                    self._write_to_file_database(
                        spark_df, target_adapter, target_table, adapter_type
                    )
                else:
                    # For other databases, use Spark JDBC
                    from dbt.compute.jdbc_utils import build_jdbc_config
                    jdbc_url, jdbc_properties = build_jdbc_config(target_credentials)

                    # DVT v0.59.0a29: Use TRUNCATE + APPEND instead of DROP CASCADE
                    # This preserves dependent views (like dbt-adapters' atomic swap).
                    #
                    # Strategy:
                    # 1. If table exists: TRUNCATE it (preserves structure and dependents)
                    # 2. Then: mode="append" to insert new data
                    # 3. If table doesn't exist: mode="overwrite" creates it (first run)
                    #
                    # This matches dbt-adapters behavior where tables with dependent
                    # views continue to work after materialization.
                    table_exists = False
                    try:
                        if adapter_type == 'postgres':
                            import psycopg2
                            conn = psycopg2.connect(
                                host=target_credentials.host,
                                port=target_credentials.port,
                                database=target_credentials.database,
                                user=target_credentials.user,
                                password=target_credentials.password,
                            )
                            conn.autocommit = True
                            cursor = conn.cursor()
                            # Check if table exists
                            cursor.execute(f"""
                                SELECT EXISTS (
                                    SELECT FROM pg_tables
                                    WHERE schemaname || '.' || tablename = '{target_table}'
                                       OR tablename = '{target_table.split('.')[-1]}'
                                )
                            """)
                            table_exists = cursor.fetchone()[0]
                            if table_exists:
                                # TRUNCATE preserves table structure and dependent views
                                cursor.execute(f"TRUNCATE TABLE {target_table}")
                            cursor.close()
                            conn.close()
                    except Exception:
                        # If check fails, fall back to overwrite mode
                        pass

                    # Write to target via Spark JDBC
                    write_mode = "append" if table_exists else "overwrite"
                    spark_df.write.jdbc(
                        jdbc_url,
                        target_table,
                        mode=write_mode,
                        properties=jdbc_properties
                    )

                adapter_response = AdapterResponse(_message="DVT: Federated JDBC write completed")

                # Return result in expected format
                rows_affected = getattr(adapter_response, 'rows_affected', 0)
                rows_msg = f"{rows_affected} rows" if rows_affected else "completed"
                # DVT v0.51.5: Note when view was materialized as table
                exec_msg = f"Federated execution: {rows_msg}"
                if convert_view_to_table:
                    exec_msg = f"Federated (view→table): {rows_msg}"
                return RunResult(
                    status=RunStatus.Success,
                    timing=[],
                    thread_id='main',
                    execution_time=fed_result.execution_time_ms / 1000.0,
                    adapter_response=adapter_response._asdict() if hasattr(adapter_response, '_asdict') else {},
                    message=exec_msg,
                    failures=None,
                    node=model,
                    agate_table=None,
                )
            finally:
                # Always close Spark session after materialization
                if fed_result.engine:
                    try:
                        fed_result.engine.close()
                    except Exception as e:
                        # Log but don't fail on cleanup errors
                        import sys
                        print(f"[DVT] Warning: Failed to close Spark session: {e}", file=sys.stderr)


class MicrobatchBatchRunner(ModelRunner):
    """Handles the running of individual batches"""

    def __init__(
        self,
        config,
        adapter,
        node,
        node_index: int,
        num_nodes: int,
        batch_idx: int,
        batches: Dict[int, BatchType],
        relation_exists: bool,
        incremental_batch: bool,
    ):
        super().__init__(config, adapter, node, node_index, num_nodes)

        self.batch_idx = batch_idx
        self.batches = batches
        self.relation_exists = relation_exists
        self.incremental_batch = incremental_batch

    def describe_batch(self) -> str:
        batch_start = self.batches[self.batch_idx][0]
        formatted_batch_start = MicrobatchBuilder.format_batch_start(
            batch_start, self.node.config.batch_size
        )
        return f"batch {formatted_batch_start} of {self.get_node_representation()}"

    def print_result_line(self, result: RunResult):
        if result.status == NodeStatus.Error:
            status = result.status
            level = EventLevel.ERROR
        elif result.status == NodeStatus.Skipped:
            status = result.status
            level = EventLevel.INFO
        else:
            status = result.message
            level = EventLevel.INFO

        fire_event(
            LogBatchResult(
                description=self.describe_batch(),
                status=status,
                batch_index=self.batch_idx + 1,
                total_batches=len(self.batches),
                execution_time=result.execution_time,
                node_info=self.node.node_info,
                group=group_lookup.get(self.node.unique_id),
            ),
            level=level,
        )

    def print_start_line(self) -> None:
        fire_event(
            LogStartBatch(
                description=self.describe_batch(),
                batch_index=self.batch_idx + 1,
                total_batches=len(self.batches),
                node_info=self.node.node_info,
            )
        )

    def should_run_in_parallel(self) -> bool:
        if not self.adapter.supports(Capability.MicrobatchConcurrency):
            run_in_parallel = False
        elif not self.relation_exists:
            # If the relation doesn't exist, we can't run in parallel
            run_in_parallel = False
        elif self.node.config.concurrent_batches is not None:
            # If the relation exists and the `concurrent_batches` config isn't None, use the config value
            run_in_parallel = self.node.config.concurrent_batches
        else:
            # If the relation exists, the `concurrent_batches` config is None, check if the model self references `this`.
            # If the model self references `this` then we assume the model batches _can't_ be run in parallel
            run_in_parallel = not self.node.has_this

        return run_in_parallel

    def on_skip(self):
        result = RunResult(
            node=self.node,
            status=RunStatus.Skipped,
            timing=[],
            thread_id=threading.current_thread().name,
            execution_time=0.0,
            message="SKIPPED",
            adapter_response={},
            failures=1,
            batch_results=BatchResults(failed=[self.batches[self.batch_idx]]),
        )
        self.print_result_line(result=result)
        return result

    def error_result(self, node, message, start_time, timing_info):
        """Necessary to return a result with a batch result

        Called by `BaseRunner.safe_run` when an error occurs
        """
        return self._build_run_result(
            node=node,
            start_time=start_time,
            status=RunStatus.Error,
            timing_info=timing_info,
            message=message,
            batch_results=BatchResults(failed=[self.batches[self.batch_idx]]),
        )

    def compile(self, manifest: Manifest):
        batch = self.batches[self.batch_idx]

        # LEGACY: Set start/end in context prior to re-compiling (Will be removed for 1.10+)
        # TODO: REMOVE before 1.10 GA
        self.node.config["__dbt_internal_microbatch_event_time_start"] = batch[0]
        self.node.config["__dbt_internal_microbatch_event_time_end"] = batch[1]
        # Create batch context on model node prior to re-compiling
        self.node.batch = BatchContext(
            id=MicrobatchBuilder.batch_id(batch[0], self.node.config.batch_size),
            event_time_start=batch[0],
            event_time_end=batch[1],
        )
        # Recompile node to re-resolve refs with event time filters rendered, update context
        self.compiler.compile_node(
            self.node,
            manifest,
            {},
            split_suffix=MicrobatchBuilder.format_batch_start(
                batch[0], self.node.config.batch_size
            ),
        )

        return self.node

    def _build_succesful_run_batch_result(
        self,
        model: ModelNode,
        context: Dict[str, Any],
        batch: BatchType,
        elapsed_time: float = 0.0,
    ) -> RunResult:
        run_result = self._build_run_model_result(model, context, elapsed_time)
        run_result.batch_results = BatchResults(successful=[batch])
        return run_result

    def _build_failed_run_batch_result(
        self,
        model: ModelNode,
        batch: BatchType,
        elapsed_time: float = 0.0,
    ) -> RunResult:
        return RunResult(
            node=model,
            status=RunStatus.Error,
            timing=[],
            thread_id=threading.current_thread().name,
            execution_time=elapsed_time,
            message="ERROR",
            adapter_response={},
            failures=1,
            batch_results=BatchResults(failed=[batch]),
        )

    def _execute_microbatch_materialization(
        self,
        model: ModelNode,
        context: Dict[str, Any],
        materialization_macro: MacroProtocol,
    ) -> RunResult:

        batch = self.batches[self.batch_idx]
        # call materialization_macro to get a batch-level run result
        start_time = time.perf_counter()
        try:
            # Update jinja context with batch context members
            jinja_context = MicrobatchBuilder.build_jinja_context_for_batch(
                model=model,
                incremental_batch=self.incremental_batch,
            )
            context.update(jinja_context)

            # Materialize batch and cache any materialized relations
            result = MacroGenerator(
                materialization_macro, context, stack=context["context_macro_stack"]
            )()
            for relation in self._materialization_relations(result, model):
                self.adapter.cache_added(relation.incorporate(dbt_created=True))

            # Build result of executed batch
            batch_run_result = self._build_succesful_run_batch_result(
                model, context, batch, time.perf_counter() - start_time
            )
            batch_result = batch_run_result

            # At least one batch has been inserted successfully!
            # Can proceed incrementally + in parallel
            self.relation_exists = True

        except (KeyboardInterrupt, SystemExit):
            # reraise it for GraphRunnableTask.execute_nodes to handle
            raise
        except Exception as e:
            fire_event(
                GenericExceptionOnRun(
                    unique_id=self.node.unique_id,
                    exc=f"Exception on worker thread. {str(e)}",
                    node_info=self.node.node_info,
                )
            )
            batch_run_result = self._build_failed_run_batch_result(
                model, batch, time.perf_counter() - start_time
            )

        batch_result = batch_run_result

        return batch_result

    def _execute_model(
        self,
        hook_ctx: Any,
        context_config: Any,
        model: ModelNode,
        context: Dict[str, Any],
        materialization_macro: MacroProtocol,
    ) -> RunResult:
        try:
            batch_result = self._execute_microbatch_materialization(
                model, context, materialization_macro
            )
        finally:
            self.adapter.post_model_hook(context_config, hook_ctx)

        return batch_result


class MicrobatchModelRunner(ModelRunner):
    """Handles the orchestration of batches to run for a given microbatch model"""

    def __init__(self, config, adapter, node, node_index: int, num_nodes: int):
        super().__init__(config, adapter, node, node_index, num_nodes)

        # The parent task is necessary because we need access to the `_submit_batch` and `submit` methods
        self._parent_task: Optional[RunTask] = None
        # The pool is necessary because we need to batches to be executed within the same thread pool
        self._pool: Optional[DbtThreadPool] = None

    def set_parent_task(self, parent_task: RunTask) -> None:
        self._parent_task = parent_task

    def set_pool(self, pool: DbtThreadPool) -> None:
        self._pool = pool

    @property
    def parent_task(self) -> RunTask:
        if self._parent_task is None:
            raise DbtInternalError(
                msg="Tried to access `parent_task` of `MicrobatchModelRunner` before it was set"
            )

        return self._parent_task

    @property
    def pool(self) -> DbtThreadPool:
        if self._pool is None:
            raise DbtInternalError(
                msg="Tried to access `pool` of `MicrobatchModelRunner` before it was set"
            )

        return self._pool

    def _has_relation(self, model: ModelNode) -> bool:
        """Check whether the relation for the model exists in the data warehouse"""
        relation_info = self.adapter.Relation.create_from(self.config, model)
        relation = self.adapter.get_relation(
            relation_info.database, relation_info.schema, relation_info.name
        )
        return relation is not None

    def _is_incremental(self, model) -> bool:
        """Check whether the model should be run `incrementally` or as `full refresh`"""
        # TODO: Remove this whole function. This should be a temporary method. We're working with adapters on
        # a strategy to ensure we can access the `is_incremental` logic without drift
        relation_info = self.adapter.Relation.create_from(self.config, model)
        relation = self.adapter.get_relation(
            relation_info.database, relation_info.schema, relation_info.name
        )
        if (
            relation is not None
            and relation.type == "table"
            and model.config.materialized == "incremental"
        ):
            if model.config.full_refresh is not None:
                return not model.config.full_refresh
            else:
                return not getattr(self.config.args, "FULL_REFRESH", False)
        else:
            return False

    def _initial_run_microbatch_model_result(self, model: ModelNode) -> RunResult:
        return RunResult(
            node=model,
            status=RunStatus.Success,
            timing=[],
            thread_id=threading.current_thread().name,
            # The execution_time here doesn't get propagated to logs because
            # `safe_run_hooks` handles the elapsed time at the node level
            execution_time=0,
            message="",
            adapter_response={},
            failures=0,
            batch_results=BatchResults(),
        )

    def describe_node(self) -> str:
        return f"{self.node.language} microbatch model {self.get_node_representation()}"

    def merge_batch_results(self, result: RunResult, batch_results: List[RunResult]):
        """merge batch_results into result"""
        if result.batch_results is None:
            result.batch_results = BatchResults()

        for batch_result in batch_results:
            if batch_result.batch_results is not None:
                result.batch_results += batch_result.batch_results
            result.execution_time += batch_result.execution_time

        num_successes = len(result.batch_results.successful)
        num_failures = len(result.batch_results.failed)
        if num_failures == 0:
            status = RunStatus.Success
            msg = "SUCCESS"
        elif num_successes == 0:
            status = RunStatus.Error
            msg = "ERROR"
        else:
            status = RunStatus.PartialSuccess
            msg = f"PARTIAL SUCCESS ({num_successes}/{num_successes + num_failures})"
        result.status = status
        result.message = msg

        result.batch_results.successful = sorted(result.batch_results.successful)
        result.batch_results.failed = sorted(result.batch_results.failed)

        # # If retrying, propagate previously successful batches into final result, even thoguh they were not run in this invocation
        if self.node.previous_batch_results is not None:
            result.batch_results.successful += self.node.previous_batch_results.successful

    def _update_result_with_unfinished_batches(
        self, result: RunResult, batches: Dict[int, BatchType]
    ) -> None:
        """This method is really only to be used when the execution of a microbatch model is halted before all batches have had a chance to run"""
        batches_finished: Set[BatchType] = set()

        if result.batch_results:
            # build list of finished batches
            batches_finished = batches_finished.union(set(result.batch_results.successful))
            batches_finished = batches_finished.union(set(result.batch_results.failed))
        else:
            # instantiate `batch_results` if it was `None`
            result.batch_results = BatchResults()

        # skipped batches are any batch that was expected but didn't finish
        batches_expected = {batch for _, batch in batches.items()}
        skipped_batches = batches_expected.difference(batches_finished)

        result.batch_results.failed.extend(list(skipped_batches))

        # We call this method, even though we are merging no new results, as it updates
        # the result witht he appropriate status (Success/Partial/Failed)
        self.merge_batch_results(result, [])

    def get_microbatch_builder(self, model: ModelNode) -> MicrobatchBuilder:
        # Intially set the start/end to values from args
        event_time_start = getattr(self.config.args, "EVENT_TIME_START", None)
        event_time_end = getattr(self.config.args, "EVENT_TIME_END", None)

        # If we're in sample mode, alter start/end to sample values
        if getattr(self.config.args, "SAMPLE", None) is not None:
            event_time_start = self.config.args.sample.start
            event_time_end = self.config.args.sample.end

        return MicrobatchBuilder(
            model=model,
            is_incremental=self._is_incremental(model),
            event_time_start=event_time_start,
            event_time_end=event_time_end,
            default_end_time=get_invocation_started_at(),
        )

    def get_batches(self, model: ModelNode) -> Dict[int, BatchType]:
        """Get the batches that should be run for the model"""

        # Note currently (02/23/2025) model.previous_batch_results is only ever _not_ `None`
        # IFF `dbt retry` is being run and the microbatch model had batches which
        # failed on the run of the model (which is being retried)
        if model.previous_batch_results is None:
            microbatch_builder = self.get_microbatch_builder(model)
            end = microbatch_builder.build_end_time()
            start = microbatch_builder.build_start_time(end)
            batches = microbatch_builder.build_batches(start, end)
        else:
            batches = model.previous_batch_results.failed

        return {batch_idx: batches[batch_idx] for batch_idx in range(len(batches))}

    def compile(self, manifest: Manifest):
        """Don't do anything here because this runner doesn't need to compile anything"""
        return self.node

    def execute(self, model: ModelNode, manifest: Manifest) -> RunResult:
        # Execution really means orchestration in this case

        batches = self.get_batches(model=model)
        relation_exists = self._has_relation(model=model)
        result = self._initial_run_microbatch_model_result(model=model)

        # No batches to run, so return initial result
        if len(batches) == 0:
            return result

        batch_results: List[RunResult] = []
        batch_idx = 0

        # Run first batch not in parallel
        relation_exists = self.parent_task._submit_batch(
            node=model,
            adapter=self.adapter,
            relation_exists=relation_exists,
            batches=batches,
            batch_idx=batch_idx,
            batch_results=batch_results,
            pool=self.pool,
            force_sequential_run=True,
            incremental_batch=self._is_incremental(model=model),
        )
        batch_idx += 1
        skip_batches = batch_results[0].status != RunStatus.Success

        # Run all batches except first and last batch, in parallel if possible
        while batch_idx < len(batches) - 1:
            relation_exists = self.parent_task._submit_batch(
                node=model,
                adapter=self.adapter,
                relation_exists=relation_exists,
                batches=batches,
                batch_idx=batch_idx,
                batch_results=batch_results,
                pool=self.pool,
                skip=skip_batches,
            )
            batch_idx += 1

        # Wait until all submitted batches have completed
        while len(batch_results) != batch_idx:
            # Check if the pool was closed, because if it was, then the main thread is trying to exit.
            # If the main thread is trying to exit, we need to shutdown. If we _don't_ shutdown, then
            # batches will continue to execute and we'll delay the run from stopping
            if self.pool.is_closed():
                # It's technically possible for more results to come in while we clean up
                # instead we're going to say the didn't finish, regardless of if they finished
                # or not. Thus, lets get a copy of the results as they exist right "now".
                frozen_batch_results = deepcopy(batch_results)
                self.merge_batch_results(result, frozen_batch_results)
                self._update_result_with_unfinished_batches(result, batches)
                return result

            # breifly sleep so that this thread doesn't go brrrrr while waiting
            time.sleep(0.1)

        # Only run "last" batch if there is more than one batch
        if len(batches) != 1:
            # Final batch runs once all others complete to ensure post_hook runs at the end
            self.parent_task._submit_batch(
                node=model,
                adapter=self.adapter,
                relation_exists=relation_exists,
                batches=batches,
                batch_idx=batch_idx,
                batch_results=batch_results,
                pool=self.pool,
                force_sequential_run=True,
                skip=skip_batches,
            )

        # Finalize run: merge results, track model run, and print final result line
        self.merge_batch_results(result, batch_results)

        return result


class RunTask(CompileTask):
    def __init__(
        self,
        args: Flags,
        config: RuntimeConfig,
        manifest: Manifest,
        batch_map: Optional[Dict[str, BatchResults]] = None,
    ) -> None:
        super().__init__(args, config, manifest)
        self.batch_map = batch_map

    def raise_on_first_error(self) -> bool:
        return False

    def get_hook_sql(self, adapter, hook, idx, num_hooks, extra_context) -> str:
        if self.manifest is None:
            raise DbtInternalError("compile_node called before manifest was loaded")

        compiled = self.compiler.compile_node(hook, self.manifest, extra_context)
        statement = compiled.compiled_code
        hook_index = hook.index or num_hooks
        hook_obj = get_hook(statement, index=hook_index)
        return hook_obj.sql or ""

    def handle_job_queue(self, pool, callback):
        node = self.job_queue.get()
        self._raise_set_error()
        runner = self.get_runner(node)
        # we finally know what we're running! Make sure we haven't decided
        # to skip it due to upstream failures
        if runner.node.unique_id in self._skipped_children:
            cause = self._skipped_children.pop(runner.node.unique_id)
            runner.do_skip(cause=cause)

        if isinstance(runner, MicrobatchModelRunner):
            runner.set_parent_task(self)
            runner.set_pool(pool)

        args = [runner]
        self._submit(pool, args, callback)

    def _submit_batch(
        self,
        node: ModelNode,
        adapter: BaseAdapter,
        relation_exists: bool,
        batches: Dict[int, BatchType],
        batch_idx: int,
        batch_results: List[RunResult],
        pool: DbtThreadPool,
        force_sequential_run: bool = False,
        skip: bool = False,
        incremental_batch: bool = True,
    ):
        node_copy = deepcopy(node)
        # Only run pre_hook(s) for first batch
        if batch_idx != 0:
            node_copy.config.pre_hook = []

        # Only run post_hook(s) for last batch
        if batch_idx != len(batches) - 1:
            node_copy.config.post_hook = []

        # TODO: We should be doing self.get_runner, however doing so
        # currently causes the tracking of how many nodes there are to
        # increment when we don't want it to
        batch_runner = MicrobatchBatchRunner(
            self.config,
            adapter,
            node_copy,
            self.run_count,
            self.num_nodes,
            batch_idx,
            batches,
            relation_exists,
            incremental_batch,
        )

        if skip:
            batch_runner.do_skip()

        if not pool.is_closed():
            if not force_sequential_run and batch_runner.should_run_in_parallel():
                fire_event(
                    MicrobatchExecutionDebug(
                        msg=f"{batch_runner.describe_batch()} is being run concurrently"
                    )
                )
                self._submit(pool, [batch_runner], batch_results.append)
            else:
                fire_event(
                    MicrobatchExecutionDebug(
                        msg=f"{batch_runner.describe_batch()} is being run sequentially"
                    )
                )
                batch_results.append(self.call_runner(batch_runner))
                relation_exists = batch_runner.relation_exists
        else:
            batch_results.append(
                batch_runner._build_failed_run_batch_result(node_copy, batches[batch_idx])
            )

        return relation_exists

    def _hook_keyfunc(self, hook: HookNode) -> Tuple[str, Optional[int]]:
        package_name = hook.package_name
        if package_name == self.config.project_name:
            package_name = BiggestName("")
        return package_name, hook.index

    def get_hooks_by_type(self, hook_type: RunHookType) -> List[HookNode]:

        if self.manifest is None:
            raise DbtInternalError("self.manifest was None in get_hooks_by_type")

        nodes = self.manifest.nodes.values()
        # find all hooks defined in the manifest (could be multiple projects)
        hooks: List[HookNode] = get_hooks_by_tags(nodes, {hook_type})
        hooks.sort(key=self._hook_keyfunc)
        return hooks

    def safe_run_hooks(
        self, adapter: BaseAdapter, hook_type: RunHookType, extra_context: Dict[str, Any]
    ) -> RunStatus:
        ordered_hooks = self.get_hooks_by_type(hook_type)

        if hook_type == RunHookType.End and ordered_hooks:
            fire_event(Formatting(""))

        # on-run-* hooks should run outside a transaction. This happens because psycopg2 automatically begins a transaction when a connection is created.
        adapter.clear_transaction()
        if not ordered_hooks:
            return RunStatus.Success

        status = RunStatus.Success
        failed = False
        num_hooks = len(ordered_hooks)

        for idx, hook in enumerate(ordered_hooks, 1):
            with log_contextvars(node_info=hook.node_info):
                hook.index = idx
                hook_name = f"{hook.package_name}.{hook_type}.{hook.index - 1}"
                execution_time = 0.0
                timing: List[TimingInfo] = []
                failures = 1

                if not failed:
                    with collect_timing_info("compile", timing.append):
                        sql = self.get_hook_sql(
                            adapter, hook, hook.index, num_hooks, extra_context
                        )

                    started_at = timing[0].started_at or datetime.now(timezone.utc).replace(
                        tzinfo=None
                    )
                    hook.update_event_status(
                        started_at=started_at.isoformat(), node_status=RunningStatus.Started
                    )

                    fire_event(
                        LogHookStartLine(
                            statement=hook_name,
                            index=hook.index,
                            total=num_hooks,
                            node_info=hook.node_info,
                        )
                    )

                    with collect_timing_info("execute", timing.append):
                        status, message = get_execution_status(sql, adapter)

                    finished_at = timing[1].completed_at or datetime.now(timezone.utc).replace(
                        tzinfo=None
                    )
                    hook.update_event_status(finished_at=finished_at.isoformat())
                    execution_time = (finished_at - started_at).total_seconds()
                    failures = 0 if status == RunStatus.Success else 1

                    if status == RunStatus.Success:
                        message = f"{hook_name} passed"
                    else:
                        message = f"{hook_name} failed, error:\n {message}"
                        failed = True
                else:
                    status = RunStatus.Skipped
                    message = f"{hook_name} skipped"

                hook.update_event_status(node_status=status)

                self.node_results.append(
                    RunResult(
                        status=status,
                        thread_id="main",
                        timing=timing,
                        message=message,
                        adapter_response={},
                        execution_time=execution_time,
                        failures=failures,
                        node=hook,
                    )
                )

                fire_event(
                    LogHookEndLine(
                        statement=hook_name,
                        status=status,
                        index=hook.index,
                        total=num_hooks,
                        execution_time=execution_time,
                        node_info=hook.node_info,
                    )
                )

        if hook_type == RunHookType.Start and ordered_hooks:
            fire_event(Formatting(""))

        return status

    def print_results_line(self, results, execution_time) -> None:
        nodes = [r.node for r in results if hasattr(r, "node")]
        stat_line = get_counts(nodes)

        execution = ""

        if execution_time is not None:
            execution = utils.humanize_execution_time(execution_time=execution_time)

        fire_event(Formatting(""))
        fire_event(
            FinishedRunningStats(
                stat_line=stat_line, execution=execution, execution_time=execution_time
            )
        )

    def populate_microbatch_batches(self, selected_uids: AbstractSet[str]):
        if self.batch_map is not None and self.manifest is not None:
            for uid in selected_uids:
                if uid in self.batch_map:
                    node = self.manifest.ref_lookup.perform_lookup(uid, self.manifest)
                    if isinstance(node, ModelNode):
                        node.previous_batch_results = self.batch_map[uid]

    def before_run(self, adapter: BaseAdapter, selected_uids: AbstractSet[str]) -> RunStatus:
        with adapter.connection_named("master"):
            self.defer_to_manifest()
            required_schemas = self.get_model_schemas(adapter, selected_uids)
            self.create_schemas(adapter, required_schemas)
            self.populate_adapter_cache(adapter, required_schemas)
            self.populate_microbatch_batches(selected_uids)
            group_lookup.init(self.manifest, selected_uids)

            # DVT v0.57.0: Auto-snapshot metadata on first run or --full-refresh
            self._ensure_source_metadata()

            run_hooks_status = self.safe_run_hooks(adapter, RunHookType.Start, {})
            return run_hooks_status

    def _ensure_source_metadata(self) -> None:
        """
        Auto-capture source metadata if not present or on --full-refresh.

        DVT v0.57.0: Ensures metadata is available for type propagation
        across federated paths. Called automatically before every run.
        """
        from pathlib import Path

        try:
            from dbt.compute.metadata import ProjectMetadataStore
        except ImportError:
            # DuckDB not available - skip metadata capture
            return

        # Get project root
        project_dir = getattr(self.config, 'project_root', None)
        if not project_dir:
            return

        project_root = Path(project_dir).resolve()

        # Check if --full-refresh is set
        full_refresh = getattr(self.config.args, 'FULL_REFRESH', False)

        try:
            with ProjectMetadataStore(project_root) as store:
                store.initialize()
                has_metadata = store.has_source_metadata()

                # Re-capture on first run OR --full-refresh
                if full_refresh or not has_metadata:
                    from dbt.task.metadata import MetadataTask

                    # Create args for metadata task
                    class MetadataArgs:
                        def __init__(self):
                            self.subcommand = 'snapshot'
                            self.project_dir = str(project_root)

                    # Run snapshot silently
                    task = MetadataTask(MetadataArgs())

                    # Capture without verbose output (run silently)
                    import io
                    import sys
                    old_stdout = sys.stdout
                    sys.stdout = io.StringIO()
                    try:
                        task.run_snapshot()
                    finally:
                        sys.stdout = old_stdout
        except Exception:
            # Silently skip metadata capture if it fails
            pass

    def after_run(self, adapter, results) -> None:
        # DVT v0.58.4: Clean up all Spark sessions BEFORE thread pool terminates
        # This prevents semaphore leaks and segfaults from JVM cleanup issues
        try:
            from dbt.compute.strategies.local import cleanup_all_spark_sessions
            cleanup_all_spark_sessions()
        except ImportError:
            pass  # PySpark not installed, nothing to clean up

        # in on-run-end hooks, provide the value 'database_schemas', which is a
        # list of unique (database, schema) pairs that successfully executed
        # models were in. For backwards compatibility, include the old
        # 'schemas', which did not include database information.

        database_schema_set: Set[Tuple[Optional[str], str]] = {
            (r.node.database, r.node.schema)
            for r in results
            if (hasattr(r, "node") and r.node.is_relational)
            and r.status not in (NodeStatus.Error, NodeStatus.Fail, NodeStatus.Skipped)
        }

        extras = {
            "schemas": list({s for _, s in database_schema_set}),
            "results": [
                r for r in results if r.thread_id != "main" or r.status == RunStatus.Error
            ],  # exclude that didn't fail to preserve backwards compatibility
            "database_schemas": list(database_schema_set),
        }

        try:
            with adapter.connection_named("master"):
                self.safe_run_hooks(adapter, RunHookType.End, extras)
        except (KeyboardInterrupt, SystemExit, DbtRuntimeError):
            run_result = self.get_result(
                results=self.node_results,
                elapsed_time=time.time() - self.started_at,
                generated_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )

            if self.args.write_json and hasattr(run_result, "write"):
                run_result.write(self.result_path())
                add_artifact_produced(self.result_path())

            print_run_end_messages(self.node_results, keyboard_interrupt=True)

            raise

    def get_node_selector(self) -> ResourceTypeSelector:
        if self.manifest is None or self.graph is None:
            raise DbtInternalError("manifest and graph must be set to get perform node selection")
        return ResourceTypeSelector(
            graph=self.graph,
            manifest=self.manifest,
            previous_state=self.previous_state,
            resource_types=[NodeType.Model],
        )

    def get_runner_type(self, node) -> Optional[Type[BaseRunner]]:
        if self.manifest is None:
            raise DbtInternalError("manifest must be set prior to calling get_runner_type")

        if (
            node.config.materialized == "incremental"
            and node.config.incremental_strategy == "microbatch"
            and self.manifest.use_microbatch_batches(project_name=self.config.project_name)
        ):
            return MicrobatchModelRunner
        else:
            return ModelRunner

    def task_end_messages(self, results) -> None:
        if results:
            print_run_end_messages(results)
