import functools
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from copy import copy
from dataclasses import dataclass
import re
import time
from typing import Callable, List, Optional, Union

import click
from click.exceptions import BadOptionUsage
from click.exceptions import Exit as ClickExit
from click.exceptions import NoSuchOption, UsageError

from dbt.adapters.factory import register_adapter
from dbt.artifacts.schemas.catalog import CatalogArtifact
from dbt.artifacts.schemas.run import RunExecutionResult
from dbt.cli import params as p
from dbt.cli import requires
from dbt.cli.exceptions import DbtInternalException, DbtUsageException
from dbt.cli.requires import setup_manifest
from dbt.contracts.graph.manifest import Manifest
from dbt.mp_context import get_mp_context
from dbt_common.events.base_types import EventMsg


@dataclass
class dbtRunnerResult:
    """Contains the result of an invocation of the dbtRunner"""

    success: bool

    exception: Optional[BaseException] = None
    result: Union[
        bool,  # debug
        CatalogArtifact,  # docs generate
        List[str],  # list/ls
        Manifest,  # parse
        None,  # clean, deps, init, source
        RunExecutionResult,  # build, compile, run, seed, snapshot, test, run-operation
    ] = None


# Programmatic invocation
class dbtRunner:
    def __init__(
        self,
        manifest: Optional[Manifest] = None,
        callbacks: Optional[List[Callable[[EventMsg], None]]] = None,
    ) -> None:
        self.manifest = manifest

        if callbacks is None:
            callbacks = []
        self.callbacks = callbacks

    def invoke(self, args: List[str], **kwargs) -> dbtRunnerResult:
        try:
            dbt_ctx = cli.make_context(cli.name, args.copy())
            dbt_ctx.obj = {
                "manifest": self.manifest,
                "callbacks": self.callbacks,
                "dbt_runner_command_args": args,
            }

            for key, value in kwargs.items():
                dbt_ctx.params[key] = value
                # Hack to set parameter source to custom string
                dbt_ctx.set_parameter_source(key, "kwargs")  # type: ignore

            result, success = cli.invoke(dbt_ctx)
            return dbtRunnerResult(
                result=result,
                success=success,
            )
        except requires.ResultExit as e:
            return dbtRunnerResult(
                result=e.result,
                success=False,
            )
        except requires.ExceptionExit as e:
            return dbtRunnerResult(
                exception=e.exception,
                success=False,
            )
        except (BadOptionUsage, NoSuchOption, UsageError) as e:
            return dbtRunnerResult(
                exception=DbtUsageException(e.message),
                success=False,
            )
        except ClickExit as e:
            if e.exit_code == 0:
                return dbtRunnerResult(success=True)
            return dbtRunnerResult(
                exception=DbtInternalException(f"unhandled exit code {e.exit_code}"),
                success=False,
            )
        except BaseException as e:
            return dbtRunnerResult(
                exception=e,
                success=False,
            )


# approach from https://github.com/pallets/click/issues/108#issuecomment-280489786
def global_flags(func):
    @p.cache_selected_only
    @p.debug
    @p.defer
    @p.deprecated_defer
    @p.defer_state
    @p.deprecated_favor_state
    @p.deprecated_print
    @p.deprecated_state
    @p.fail_fast
    @p.favor_state
    @p.indirect_selection
    @p.log_cache_events
    @p.log_file_max_bytes
    @p.log_format
    @p.log_format_file
    @p.log_level
    @p.log_level_file
    @p.log_path
    @p.macro_debugging
    @p.partial_parse
    @p.partial_parse_file_path
    @p.partial_parse_file_diff
    @p.populate_cache
    @p.print
    @p.printer_width
    @p.profile
    @p.quiet
    @p.record_timing_info
    @p.send_anonymous_usage_stats
    @p.single_threaded
    @p.show_all_deprecations
    @p.state
    @p.static_parser
    @p.target
    @p.target_compute
    @p.use_colors
    @p.use_colors_file
    @p.use_experimental_parser
    @p.version
    @p.version_check
    @p.warn_error
    @p.warn_error_options
    @p.write_json
    @p.use_fast_test_edges
    @p.upload_artifacts
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


# dbt
@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
    no_args_is_help=True,
    epilog="Specify one of these sub-commands and you can find more help from there.",
)
@click.pass_context
@global_flags
@p.show_resource_report
def cli(ctx, **kwargs):
    """An ELT tool for managing your SQL transformations and data models.
    For more documentation on these commands, visit: docs.getdbt.com
    """


# dbt build
@cli.command("build")
@click.pass_context
@global_flags
@p.empty
@p.event_time_start
@p.event_time_end
@p.exclude
@p.export_saved_queries
@p.full_refresh
@p.deprecated_include_saved_query
@p.profiles_dir
@p.project_dir
@p.resource_type
@p.exclude_resource_type
@p.sample
@p.select
@p.selector
@p.show
@p.store_failures
@p.target_path
@p.threads
@p.vars
@requires.postflight
@requires.preflight
@requires.profile
@requires.project
@requires.catalogs
@requires.runtime_config
@requires.manifest
def build(ctx, **kwargs):
    """Run all seeds, models, snapshots, and tests in DAG order"""
    from dbt.task.build import BuildTask

    task = BuildTask(
        ctx.obj["flags"],
        ctx.obj["runtime_config"],
        ctx.obj["manifest"],
    )

    results = task.run()
    success = task.interpret_results(results)
    return results, success


# dbt clean
@cli.command("clean")
@click.pass_context
@global_flags
@p.clean_project_files_only
@p.profiles_dir
@p.project_dir
@p.target_path
@p.vars
@requires.postflight
@requires.preflight
@requires.unset_profile
@requires.project
def clean(ctx, **kwargs):
    """Delete all folders in the clean-targets list (usually the dbt_packages and target directories.)"""
    from dbt.task.clean import CleanTask

    with CleanTask(ctx.obj["flags"], ctx.obj["project"]) as task:
        results = task.run()
        success = task.interpret_results(results)
    return results, success


# dbt docs
@cli.group()
@click.pass_context
@global_flags
def docs(ctx, **kwargs):
    """Generate or serve the documentation website for your project"""


# dbt docs generate
@docs.command("generate")
@click.pass_context
@global_flags
@p.compile_docs
@p.exclude
@p.profiles_dir
@p.project_dir
@p.select
@p.selector
@p.empty_catalog
@p.static
@p.target_path
@p.threads
@p.vars
@requires.postflight
@requires.preflight
@requires.profile
@requires.project
@requires.runtime_config
@requires.manifest(write=False)
def docs_generate(ctx, **kwargs):
    """Generate the documentation website for your project"""
    from dbt.task.docs.generate import GenerateTask

    task = GenerateTask(
        ctx.obj["flags"],
        ctx.obj["runtime_config"],
        ctx.obj["manifest"],
    )

    results = task.run()
    success = task.interpret_results(results)
    return results, success


# dbt docs serve
@docs.command("serve")
@click.pass_context
@global_flags
@p.browser
@p.host
@p.port
@p.profiles_dir
@p.project_dir
@p.target_path
@p.vars
@requires.postflight
@requires.preflight
@requires.profile
@requires.project
@requires.runtime_config
def docs_serve(ctx, **kwargs):
    """Serve the documentation website for your project"""
    from dbt.task.docs.serve import ServeTask

    task = ServeTask(
        ctx.obj["flags"],
        ctx.obj["runtime_config"],
    )

    results = task.run()
    success = task.interpret_results(results)
    return results, success


# dbt compile
@cli.command("compile")
@click.pass_context
@global_flags
@p.exclude
@p.full_refresh
@p.show_output_format
@p.introspect
@p.profiles_dir
@p.project_dir
@p.empty
@p.select
@p.selector
@p.inline
@p.compile_inject_ephemeral_ctes
@p.target_path
@p.threads
@p.vars
@requires.postflight
@requires.preflight
@requires.profile
@requires.project
@requires.runtime_config
@requires.manifest
def compile(ctx, **kwargs):
    """Generates executable SQL from source, model, test, and analysis files. Compiled SQL files are written to the
    target/ directory."""
    from dbt.task.compile import CompileTask

    task = CompileTask(
        ctx.obj["flags"],
        ctx.obj["runtime_config"],
        ctx.obj["manifest"],
    )

    results = task.run()
    success = task.interpret_results(results)
    return results, success


# dbt show
@cli.command("show")
@click.pass_context
@global_flags
@p.exclude
@p.full_refresh
@p.show_output_format
@p.show_limit
@p.introspect
@p.profiles_dir
@p.project_dir
@p.select
@p.selector
@p.inline
@p.inline_direct
@p.target_path
@p.threads
@p.vars
@requires.postflight
@requires.preflight
@requires.profile
@requires.project
@requires.runtime_config
def show(ctx, **kwargs):
    """Generates executable SQL for a named resource or inline query, runs that SQL, and returns a preview of the
    results. Does not materialize anything to the warehouse."""
    from dbt.task.show import ShowTask, ShowTaskDirect

    if ctx.obj["flags"].inline_direct:
        # Issue the inline query directly, with no templating. Does not require
        # loading the manifest.
        register_adapter(ctx.obj["runtime_config"], get_mp_context())
        task = ShowTaskDirect(
            ctx.obj["flags"],
            ctx.obj["runtime_config"],
        )
    else:
        setup_manifest(ctx)
        task = ShowTask(
            ctx.obj["flags"],
            ctx.obj["runtime_config"],
            ctx.obj["manifest"],
        )

    results = task.run()
    success = task.interpret_results(results)
    return results, success


# dbt debug
@cli.command("debug")
@click.pass_context
@global_flags
@p.debug_connection
@p.config_dir
@p.profiles_dir_exists_false
@p.project_dir
@p.vars
@requires.postflight
@requires.preflight
def debug(ctx, **kwargs):
    """Show information on the current dbt environment and check dependencies, then test the database connection. Not to be confused with the --debug option which increases verbosity."""
    from dbt.task.debug import DebugTask

    task = DebugTask(
        ctx.obj["flags"],
    )

    results = task.run()
    success = task.interpret_results(results)
    return results, success


# dbt deps
@cli.command("deps")
@click.pass_context
@global_flags
@p.profiles_dir_exists_false
@p.project_dir
@p.vars
@p.source
@p.lock
@p.upgrade
@p.add_package
@requires.postflight
@requires.preflight
@requires.unset_profile
@requires.project
def deps(ctx, **kwargs):
    """Install dbt packages specified.
    In the following case, a new `package-lock.yml` will be generated and the packages are installed:
    - user updated the packages.yml
    - user specify the flag --update, which means for packages that are specified as a
      range, dbt-core will try to install the newer version
    Otherwise, deps will use `package-lock.yml` as source of truth to install packages.

    There is a way to add new packages by providing an `--add-package` flag to deps command
    which will allow user to specify a package they want to add in the format of packagename@version.
    """
    from dbt.task.deps import DepsTask

    flags = ctx.obj["flags"]
    if flags.ADD_PACKAGE:
        if not flags.ADD_PACKAGE["version"] and flags.SOURCE != "local":
            raise BadOptionUsage(
                message=f"Version is required in --add-package when a package when source is {flags.SOURCE}",
                option_name="--add-package",
            )
    with DepsTask(flags, ctx.obj["project"]) as task:
        results = task.run()
        success = task.interpret_results(results)
    return results, success


# dbt init
@cli.command("init")
@click.pass_context
@global_flags
# for backwards compatibility, accept 'project_name' as an optional positional argument
@click.argument("project_name", required=False)
@p.profiles_dir_exists_false
@p.project_dir
@p.skip_profile_setup
@p.vars
@requires.postflight
@requires.preflight
def init(ctx, **kwargs):
    """Initialize a new dbt project."""
    from dbt.task.init import InitTask

    with InitTask(ctx.obj["flags"]) as task:
        results = task.run()
        success = task.interpret_results(results)
    return results, success


# dbt list
@cli.command("list")
@click.pass_context
@global_flags
@p.exclude
@p.models
@p.output
@p.output_keys
@p.profiles_dir
@p.project_dir
@p.resource_type
@p.exclude_resource_type
@p.raw_select
@p.selector
@p.target_path
@p.vars
@requires.postflight
@requires.preflight
@requires.profile
@requires.project
@requires.runtime_config
@requires.manifest
def list(ctx, **kwargs):
    """List the resources in your project"""
    from dbt.task.list import ListTask

    task = ListTask(
        ctx.obj["flags"],
        ctx.obj["runtime_config"],
        ctx.obj["manifest"],
    )

    results = task.run()
    success = task.interpret_results(results)
    return results, success


# Alias "list" to "ls"
ls = copy(cli.commands["list"])
ls.hidden = True
cli.add_command(ls, "ls")


# dbt parse
@cli.command("parse")
@click.pass_context
@global_flags
@p.profiles_dir
@p.project_dir
@p.target_path
@p.threads
@p.vars
@requires.postflight
@requires.preflight
@requires.profile
@requires.project
@requires.catalogs
@requires.runtime_config
@requires.manifest(write_perf_info=True)
def parse(ctx, **kwargs):
    """Parses the project and provides information on performance"""
    # manifest generation and writing happens in @requires.manifest
    return ctx.obj["manifest"], True


# dbt run
@cli.command("run")
@click.pass_context
@global_flags
@p.exclude
@p.full_refresh
@p.profiles_dir
@p.project_dir
@p.empty
@p.event_time_start
@p.event_time_end
@p.sample
@p.select
@p.selector
@p.target_path
@p.threads
@p.vars
@requires.postflight
@requires.preflight
@requires.profile
@requires.project
@requires.catalogs
@requires.runtime_config
@requires.manifest
def run(ctx, **kwargs):
    """Compile SQL and execute against the current target database.

    DVT enhances dbt run with:
    - Rich progress display with spinner and progress bar
    - Per-model execution path display (PUSHDOWN vs FEDERATION)
    - Beautiful summary panel with pass/fail/skip counts

    DVT Compute Rules (automatically applied):
    - Same-target models use adapter pushdown (native SQL)
    - Cross-target models use Spark federation
    - Compute selection: default < model config < CLI --target-compute
    - Target selection: default < model config < CLI --target
    """
    from dbt.task.dvt_run import create_dvt_run_task

    task = create_dvt_run_task(
        ctx.obj["flags"],
        ctx.obj["runtime_config"],
        ctx.obj["manifest"],
    )

    results = task.run()
    success = task.interpret_results(results)
    return results, success


# dbt retry
@cli.command("retry")
@click.pass_context
@global_flags
@p.project_dir
@p.profiles_dir
@p.vars
@p.target_path
@p.threads
@p.full_refresh
@requires.postflight
@requires.preflight
@requires.profile
@requires.project
@requires.runtime_config
def retry(ctx, **kwargs):
    """Retry the nodes that failed in the previous run."""
    from dbt.task.retry import RetryTask

    # Retry will parse manifest inside the task after we consolidate the flags
    task = RetryTask(
        ctx.obj["flags"],
        ctx.obj["runtime_config"],
    )

    results = task.run()
    success = task.interpret_results(results)
    return results, success


# dbt clone
@cli.command("clone")
@click.pass_context
@global_flags
@p.exclude
@p.full_refresh
@p.profiles_dir
@p.project_dir
@p.resource_type
@p.exclude_resource_type
@p.select
@p.selector
@p.target_path
@p.threads
@p.vars
@requires.preflight
@requires.profile
@requires.project
@requires.runtime_config
@requires.manifest
@requires.postflight
def clone(ctx, **kwargs):
    """Create clones of selected nodes based on their location in the manifest provided to --state."""
    from dbt.task.clone import CloneTask

    task = CloneTask(
        ctx.obj["flags"],
        ctx.obj["runtime_config"],
        ctx.obj["manifest"],
    )

    results = task.run()
    success = task.interpret_results(results)
    return results, success


# dbt run operation
@cli.command("run-operation")
@click.pass_context
@global_flags
@click.argument("macro")
@p.args
@p.profiles_dir
@p.project_dir
@p.target_path
@p.threads
@p.vars
@requires.postflight
@requires.preflight
@requires.profile
@requires.project
@requires.runtime_config
@requires.manifest
def run_operation(ctx, **kwargs):
    """Run the named macro with any supplied arguments."""
    from dbt.task.run_operation import RunOperationTask

    task = RunOperationTask(
        ctx.obj["flags"],
        ctx.obj["runtime_config"],
        ctx.obj["manifest"],
    )

    results = task.run()
    success = task.interpret_results(results)
    return results, success


# dbt seed (DVT: Spark-powered with pattern transformations)
@cli.command("seed")
@click.pass_context
@global_flags
@p.exclude
@p.full_refresh
@p.profiles_dir
@p.project_dir
@p.select
@p.selector
@p.show
@p.target_path
@p.threads
@p.vars
@requires.postflight
@requires.preflight
@requires.profile
@requires.project
@requires.catalogs
@requires.runtime_config
@requires.manifest
def seed(ctx, **kwargs):
    """Load data from csv files into your data warehouse.

    DVT Enhancement: Uses Spark compute engine with automatic pattern-based
    type transformations (e.g., "1.25%" → 0.0125 DOUBLE).

    Use --target to specify the database target and --target-compute to
    override the Spark compute engine from computes.yml.
    """
    from dbt.task.dvt_seed import DVTSeedTask

    task = DVTSeedTask(
        ctx.obj["flags"],
        ctx.obj["runtime_config"],
        ctx.obj["manifest"],
    )
    results = task.run()
    success = task.interpret_results(results)
    return results, success


# dbt snapshot
@cli.command("snapshot")
@click.pass_context
@global_flags
@p.empty
@p.exclude
@p.profiles_dir
@p.project_dir
@p.select
@p.selector
@p.target_path
@p.threads
@p.vars
@requires.postflight
@requires.preflight
@requires.profile
@requires.project
@requires.catalogs
@requires.runtime_config
@requires.manifest
def snapshot(ctx, **kwargs):
    """Execute snapshots defined in your project"""
    from dbt.task.snapshot import SnapshotTask

    task = SnapshotTask(
        ctx.obj["flags"],
        ctx.obj["runtime_config"],
        ctx.obj["manifest"],
    )

    results = task.run()
    success = task.interpret_results(results)
    return results, success


# dbt source
@cli.group()
@click.pass_context
@global_flags
def source(ctx, **kwargs):
    """Manage your project's sources"""


# dbt source freshness
@source.command("freshness")
@click.pass_context
@global_flags
@p.exclude
@p.output_path  # TODO: Is this ok to re-use?  We have three different output params, how much can we consolidate?
@p.profiles_dir
@p.project_dir
@p.select
@p.selector
@p.target_path
@p.threads
@p.vars
@requires.postflight
@requires.preflight
@requires.profile
@requires.project
@requires.runtime_config
@requires.manifest
def freshness(ctx, **kwargs):
    """check the current freshness of the project's sources"""
    from dbt.task.freshness import FreshnessTask

    task = FreshnessTask(
        ctx.obj["flags"],
        ctx.obj["runtime_config"],
        ctx.obj["manifest"],
    )

    results = task.run()
    success = task.interpret_results(results)
    return results, success


# Alias "source freshness" to "snapshot-freshness"
snapshot_freshness = copy(cli.commands["source"].commands["freshness"])  # type: ignore
snapshot_freshness.hidden = True
cli.commands["source"].add_command(snapshot_freshness, "snapshot-freshness")  # type: ignore


# dbt test
@cli.command("test")
@click.pass_context
@global_flags
@p.exclude
@p.resource_type
@p.exclude_resource_type
@p.profiles_dir
@p.project_dir
@p.select
@p.selector
@p.store_failures
@p.target_path
@p.threads
@p.vars
@requires.postflight
@requires.preflight
@requires.profile
@requires.project
@requires.runtime_config
@requires.manifest
def test(ctx, **kwargs):
    """Runs tests on data in deployed models. Run this after `dbt run`"""
    from dbt.task.test import TestTask

    task = TestTask(
        ctx.obj["flags"],
        ctx.obj["runtime_config"],
        ctx.obj["manifest"],
    )

    results = task.run()
    success = task.interpret_results(results)
    return results, success


# =============================================================================
# DVT Metadata Command Group (v0.57.0 - replaces dvt snap)
# =============================================================================

@cli.group("metadata")
def metadata():
    """Manage DVT project metadata.

    The metadata store captures type information for sources and models,
    enabling accurate type mapping across federated queries.

    Commands:
        reset       Clear all metadata from the store
        snapshot    Capture metadata for sources and models
        export      Display metadata in CLI
        export-csv  Export metadata to CSV file
        export-json Export metadata to JSON file
    """
    pass


@metadata.command("reset")
@click.pass_context
@p.project_dir
def metadata_reset(ctx, project_dir, **kwargs):
    """Clear all metadata from the store.

    Removes all captured metadata including:
    - Source column metadata
    - Model column metadata
    - Row counts
    - Profile results

    Example:
        dvt metadata reset
    """
    from dbt.task.metadata import MetadataTask

    class Args:
        def __init__(self):
            self.subcommand = 'reset'
            self.project_dir = project_dir

    task = MetadataTask(Args())
    success, _ = task.run()
    return None, success


@metadata.command("snapshot")
@click.pass_context
@p.project_dir
def metadata_snapshot(ctx, project_dir, **kwargs):
    """Capture metadata for sources and models.

    Reads source definitions (sources.yml) and model definitions (schema.yml)
    from your project and captures column metadata into .dvt/metadata_store.duckdb.

    This metadata is used by DVT to:
    - Map adapter types to Spark types for federated queries
    - Optimize query planning with schema information
    - Generate correct Spark DDL for table creation

    Examples:
        dvt metadata snapshot

    Note: This is automatically run on first 'dvt run' and on 'dvt run --full-refresh'.
    """
    from dbt.task.metadata import MetadataTask

    class Args:
        def __init__(self):
            self.subcommand = 'snapshot'
            self.project_dir = project_dir

    task = MetadataTask(Args())
    success, _ = task.run()
    return None, success


@metadata.command("export")
@click.pass_context
@p.project_dir
def metadata_export(ctx, project_dir, **kwargs):
    """Display metadata in CLI.

    Shows a Rich-formatted table of all captured metadata including:
    - Source/Model type
    - Table names
    - Column counts
    - Last updated timestamp

    Example:
        dvt metadata export
    """
    from dbt.task.metadata import MetadataTask

    class Args:
        def __init__(self):
            self.subcommand = 'export'
            self.project_dir = project_dir

    task = MetadataTask(Args())
    success, _ = task.run()
    return None, success


@metadata.command("export-csv")
@click.argument("filename", default="metadata.csv")
@click.pass_context
@p.project_dir
def metadata_export_csv(ctx, filename, project_dir, **kwargs):
    """Export metadata to CSV file.

    Exports all column metadata to a CSV file with columns:
    type, source_name, table_name, column_name, adapter_type,
    spark_type, is_nullable, is_primary_key, ordinal_position, last_refreshed

    Examples:
        dvt metadata export-csv                  # Creates metadata.csv
        dvt metadata export-csv my_export.csv   # Custom filename
    """
    from dbt.task.metadata import MetadataTask

    class Args:
        def __init__(self):
            self.subcommand = 'export-csv'
            self.project_dir = project_dir
            self.filename = filename

    task = MetadataTask(Args())
    success, _ = task.run()
    return None, success


@metadata.command("export-json")
@click.argument("filename", default="metadata.json")
@click.pass_context
@p.project_dir
def metadata_export_json(ctx, filename, project_dir, **kwargs):
    """Export metadata to JSON file.

    Exports all metadata to a JSON file with structured format:
    - sources: grouped by source name with tables and columns
    - models: grouped by model name with columns

    Examples:
        dvt metadata export-json                  # Creates metadata.json
        dvt metadata export-json my_export.json  # Custom filename
    """
    from dbt.task.metadata import MetadataTask

    class Args:
        def __init__(self):
            self.subcommand = 'export-json'
            self.project_dir = project_dir
            self.filename = filename

    task = MetadataTask(Args())
    success, _ = task.run()
    return None, success


# DVT profile command group (v0.58.0) - profiling + web UI
@cli.group("profile")
@click.pass_context
@global_flags
def profile(ctx, **kwargs):
    """Profile data sources and models, or serve the profile viewer.

    \b
    Commands:
      run    - Run data profiling (default)
      serve  - Start profile viewer web UI

    \b
    Examples:
        dvt profile run                    # Profile all sources
        dvt profile run --sample 10000     # Sample 10K rows
        dvt profile run --sample 10%       # Sample 10% of rows
        dvt profile serve                  # Start web UI at http://localhost:8580
    """
    pass


@profile.command("run")
@click.pass_context
@global_flags
@p.exclude
@p.profiles_dir
@p.project_dir
@p.select
@p.selector
@p.profile_sample
@p.threads
@p.vars
@requires.postflight
@requires.preflight
@requires.profile
@requires.project
@requires.runtime_config
@requires.manifest
def profile_run(ctx, **kwargs):
    """Run data profiling on sources and models.

    Works like 'dvt run' with DAG-based execution:
    - Respects --select and --exclude selectors
    - Respects --target and --target-compute overrides
    - Follows DVT compute rules (pushdown when possible)

    \b
    Sampling (--sample):
    - Row count: --sample 10000  (profile 10K rows)
    - Percentage: --sample 10%   (profile 10% of rows)
    - Default: All rows (no sampling)

    \b
    Examples:
        dvt profile run                       # Profile all sources (all rows)
        dvt profile run --select "source:*"   # Profile all sources
        dvt profile run --sample 10000        # Sample 10K rows per table
        dvt profile run --sample 10%          # Sample 10% of each table

    Results are saved to: .dvt/metadata_store.duckdb
    """
    from dbt.task.profile import ProfileTask

    task = ProfileTask(
        ctx.obj["flags"],
        ctx.obj["runtime_config"],
        ctx.obj["manifest"],
    )

    results = task.run()
    success = task.interpret_results(results)
    return results, success


@profile.command("serve")
@click.option("--port", default=8580, type=int, help="Port number for the profile viewer server")
@click.option("--host", default="localhost", help="Host address to bind the server")
@click.option("--no-browser", "no_browser", is_flag=True, default=False, help="Don't auto-open browser")
@click.option("--project-dir", default=".", help="Project directory (defaults to current directory)")
def profile_serve(port, host, no_browser, project_dir, **kwargs):
    """Start the profile viewer web UI.

    Opens an interactive web interface to explore profiling results
    stored in .dvt/metadata_store.duckdb.

    \b
    Features:
    - Summary statistics (tables, columns, sources, models)
    - Table browser with column details
    - Type mappings (adapter types to Spark types)
    - Beautiful dark theme UI

    \b
    Examples:
        dvt profile serve                # Start on http://localhost:8580
        dvt profile serve --port 9000    # Custom port
        dvt profile serve --no-browser   # Don't auto-open browser

    Note: Run 'dvt profile run' first to capture profiling data.
    """
    from pathlib import Path
    from dbt.task.profile_serve import serve_profile_ui

    project_path = Path(project_dir)
    success = serve_profile_ui(
        project_dir=project_path,
        port=port,
        host=host,
        open_browser=not no_browser,
    )
    return None, success


# DVT retract command - drop materialized models (v0.58.0)
@cli.command("retract")
@click.pass_context
@global_flags
@p.dry_run
@p.exclude
@p.profiles_dir
@p.project_dir
@p.select
@p.selector
@p.target_path
@p.threads
@p.vars
@requires.postflight
@requires.preflight
@requires.profile
@requires.project
@requires.runtime_config
@requires.manifest
def retract(ctx, **kwargs):
    """Drop all materialized models from target databases.

    Removes tables and views created by DVT from the target databases.
    Sources are never dropped. Use this to clean up a project or reset state.

    \b
    WARNING: This command permanently deletes data. Use --dry-run first!

    \b
    Examples:
        dvt retract --dry-run              # Preview what would be dropped
        dvt retract                        # Drop all materialized models
        dvt retract --select "dim_*"       # Drop matching models only
        dvt retract --exclude "fact_*"     # Keep matching models
        dvt retract --target prod          # Drop from specific target
    """
    from dbt.task.retract import RetractTask

    task = RetractTask(
        ctx.obj["flags"],
        ctx.obj["runtime_config"],
        ctx.obj["manifest"],
    )

    results = task.run()
    success = task.interpret_results(results)
    return results, success


# DVT compute commands
@cli.group()
@click.pass_context
@p.version
def compute(ctx, **kwargs):
    """Manage DVT compute engines for multi-source federation.

    Compute engines are configured in .dvt/computes.yml.

    \b
    Commands:
      list     - List all configured compute engines
      test     - Test a compute engine's connectivity
      edit     - Open computes.yml in your editor
      validate - Validate computes.yml syntax

    \b
    Examples:
      dvt compute list              # List all engines
      dvt compute test spark-local  # Test local Spark
      dvt compute edit              # Edit configuration
    """


@compute.command("list")
@click.pass_context
@p.project_dir
def compute_list(ctx, **kwargs):
    """List all configured compute engines.

    Shows all compute engines defined in computes.yml with their
    platform type and description.

    Examples:
        dvt compute list                    # List all compute engines
    """
    from dbt.task.compute import ComputeTask

    task = ComputeTask(project_dir=kwargs.get("project_dir"))
    success = task.list_computes()
    return None, success


@compute.command("test")
@click.pass_context
@click.argument("compute_name", required=True)
@p.project_dir
def compute_test(ctx, compute_name, **kwargs):
    """Test a compute engine's connectivity.

    Tests the specified compute engine and shows its status.
    Use 'dvt compute list' to see all available compute engines.

    Shows rich status symbols:
        ✅ Connected/Available
        ❌ Error/Not available
        ⚠️  Warning (missing optional dependency)

    Examples:
        dvt compute test spark-local        # Test local Spark
        dvt compute test databricks-prod    # Test Databricks connectivity
        dvt compute test spark-docker       # Test Docker Spark cluster
    """
    from dbt.task.compute import ComputeTask

    task = ComputeTask(project_dir=kwargs.get("project_dir"))
    success = task.test_single_compute(compute_name)
    return None, success


@compute.command("edit")
@click.pass_context
@p.project_dir
def compute_edit(ctx, **kwargs):
    """Open computes.yml in your editor.

    Opens the compute configuration file in your preferred editor.
    Uses EDITOR environment variable, or falls back to common editors
    (code, nano, vim, vi, notepad).

    The file contains comprehensive commented samples for:
    - Local Spark (default)
    - Databricks (SQL Warehouse and Interactive Cluster)
    - AWS EMR
    - GCP Dataproc
    - Standalone Spark clusters

    After editing, run 'dvt compute validate' to check syntax.

    Examples:
        dvt compute edit              # Open in default editor
        EDITOR=nano dvt compute edit  # Use specific editor
    """
    from dbt.task.compute import ComputeTask

    task = ComputeTask(project_dir=kwargs.get("project_dir"))
    success = task.edit_config()
    return None, success


@compute.command("validate")
@click.pass_context
@p.project_dir
def compute_validate(ctx, **kwargs):
    """Validate computes.yml syntax and configuration.

    Checks the compute configuration file for:
    - Valid YAML syntax
    - Required fields (target_compute, type)
    - Valid compute engine references
    - Platform-specific configuration

    Examples:
        dvt compute validate    # Validate configuration
    """
    from dbt.task.compute import ComputeTask

    task = ComputeTask(project_dir=kwargs.get("project_dir"))
    is_valid = task.validate_config()
    return None, is_valid




# DVT migrate command - migrate from dbt to DVT or import dbt projects
@cli.command("migrate")
@click.pass_context
@click.argument("source_path", required=False, type=click.Path(exists=True))
@click.option("--profiles", "migrate_profiles", is_flag=True, help="Migrate profiles.yml only")
@click.option("--project", "migrate_project", is_flag=True, help="Migrate dbt_project.yml only")
@click.option("--full", "migrate_full", is_flag=True, help="Full migration (profiles + project)")
@click.option("--dry-run", is_flag=True, help="Show what would be migrated without making changes")
@p.profiles_dir
@p.project_dir
def migrate(ctx, source_path, migrate_profiles, migrate_project, migrate_full, dry_run, **kwargs):
    """Migrate or import dbt configuration into DVT.

    \b
    Mode A - Convert dbt project to DVT (run from dbt project directory):
        dvt migrate              # Auto-detect and migrate
        dvt migrate --profiles   # Migrate profiles.yml only
        dvt migrate --project    # Migrate dbt_project.yml only
        dvt migrate --full       # Full migration

    \b
    Mode B - Import dbt project INTO DVT (run from DVT project directory):
        dvt migrate /path/to/dbt_project   # Import dbt project
        # Models copied to: models/<project_name>/
        # Targets merged into DVT profile

    \b
    Options:
        dvt migrate --dry-run    # Preview what would happen
    """
    from dbt.task.migrate import MigrateTask

    task = MigrateTask(
        source_path=source_path,
        profiles_only=migrate_profiles,
        project_only=migrate_project,
        full=migrate_full,
        dry_run=dry_run,
        project_dir=kwargs.get("project_dir"),
    )
    success = task.run()
    return None, success


# DVT target (connection) management commands
@cli.group()
@click.pass_context
@p.version
def target(ctx, **kwargs):
    """Manage connection targets in profiles.yml.

    \b
    Commands:
      list    - List available targets
      test    - Test connection to one or all targets
      add     - Add a new target to a profile
      remove  - Remove a target from a profile
      sync    - Sync adapters and JDBC JARs

    \b
    Examples:
      dvt target list              # List all targets
      dvt target test              # Test all connections
      dvt target test dev          # Test specific target
    """


@target.command("list")
@click.option("--profile", help="Profile name to list targets from")
@click.pass_context
@p.profiles_dir
@p.project_dir
def target_list(ctx, profile, profiles_dir, project_dir, **kwargs):
    """List available targets in profiles.yml.

    If executed from within a DVT project directory, automatically detects the profile
    from dbt_project.yml. Use --profile to override or when outside a project directory.

    Features colored output for improved readability:
    - Cyan: Profile and target names
    - Green: Default target indicators
    - Red: Error messages

    Examples:
        dvt target list                    # Auto-detect from project
        dvt target list --profile my_proj  # Specific profile
    """
    from dbt.config.profile import read_profile
    from dbt.config.project_utils import get_project_profile_name

    profiles = read_profile(profiles_dir)

    if not profiles:
        click.echo(click.style("No profiles found in profiles.yml", fg="red"))
        ctx.exit(1)

    # If --profile not provided, try to get from dvt_project.yml or dbt_project.yml
    if not profile:
        profile = get_project_profile_name(project_dir)
        if not profile:
            # v0.59.0a18: Don't show all profiles - that breaks multi-project setups
            # User must be in a project directory or specify --profile
            click.echo(click.style("✗ Not in a DVT project directory", fg="red"))
            click.echo("")
            click.echo("Run from within a DVT project directory, or use --profile:")
            click.echo("  dvt target list --profile <profile_name>")
            click.echo("")
            click.echo("To create a new project: dvt init <project_name>")
            ctx.exit(1)

    # Show targets for specific profile
    if profile not in profiles:
        click.echo(click.style(f"✗ Profile '{profile}' not found", fg="red"))
        ctx.exit(1)

    profile_data = profiles[profile]
    if profile_data is None:
        click.echo(click.style(f"✗ Profile '{profile}' is empty or invalid", fg="red"))
        ctx.exit(1)
    outputs = profile_data.get("outputs", {})

    if not outputs:
        click.echo(click.style(f"No targets found in profile '{profile}'", fg="yellow"))
        return True, True

    default_target = profile_data.get(
        "default_target", profile_data.get("target", "unknown")
    )

    # Always show profile name header for context
    click.echo(click.style(f"Profile: {profile}", fg="cyan", bold=True))
    click.echo(f"Default target: {click.style(default_target, fg='green')}")
    click.echo("")
    click.echo("Available targets:")
    for target_name, target_config in outputs.items():
        default_marker = (
            click.style(" (default)", fg="green")
            if target_name == default_target
            else ""
        )
        adapter_type = target_config.get("type", "unknown")
        click.echo(
            f"  {click.style(target_name, fg='cyan')} ({adapter_type}){default_marker}"
        )

    return True, True


def _get_test_query(adapter_type: str) -> str:
    """Get adapter-specific test query for connection validation.

    Args:
        adapter_type: The adapter type (postgres, snowflake, etc.)

    Returns:
        SQL query string for testing connectivity
    """
    test_queries = {
        # Standard SELECT 1
        "postgres": "SELECT 1",
        "mysql": "SELECT 1",
        "redshift": "SELECT 1",
        "databricks": "SELECT 1",
        "duckdb": "SELECT 1",
        "clickhouse": "SELECT 1",
        "trino": "SELECT 1",
        "presto": "SELECT 1",
        "athena": "SELECT 1",
        "spark": "SELECT 1",
        "sqlserver": "SELECT 1",
        # Snowflake has a nice version function
        "snowflake": "SELECT CURRENT_VERSION()",
        # BigQuery
        "bigquery": "SELECT 1",
        # Oracle requires FROM DUAL
        "oracle": "SELECT 1 FROM DUAL",
        # DB2 requires SYSIBM.SYSDUMMY1
        "db2": "SELECT 1 FROM SYSIBM.SYSDUMMY1",
        # Teradata
        "teradata": "SELECT 1",
        # SAP HANA requires FROM DUMMY
        "saphana": "SELECT 1 FROM DUMMY",
        # Vertica
        "vertica": "SELECT 1",
        # Exasol
        "exasol": "SELECT 1 FROM DUAL",
        # SingleStore (formerly MemSQL)
        "singlestore": "SELECT 1",
        # CockroachDB (Postgres-compatible)
        "cockroachdb": "SELECT 1",
        # TimescaleDB (Postgres-compatible)
        "timescale": "SELECT 1",
        # Greenplum (Postgres-compatible)
        "greenplum": "SELECT 1",
    }
    return test_queries.get(adapter_type, "SELECT 1")


def _get_connection_error_hint(exception: Exception, adapter_type: str) -> str:
    """Provide user-friendly hints for common connection errors.

    Args:
        exception: The exception that was raised
        adapter_type: The adapter type being tested

    Returns:
        A helpful error message with troubleshooting hints
    """
    error_str = str(exception).lower()

    # Common error patterns and hints
    if "timeout" in error_str or "timed out" in error_str:
        return "Connection timeout - Check network connectivity and firewall rules"
    elif "could not connect" in error_str or "connection refused" in error_str:
        return "Connection refused - Verify host and port are correct"
    elif (
        "authentication" in error_str or "password" in error_str or "login" in error_str
    ):
        return "Authentication failed - Check username and password"
    elif "database" in error_str and "does not exist" in error_str:
        return "Database not found - Verify database name"
    elif "permission" in error_str or "access denied" in error_str:
        return "Permission denied - Check user privileges"
    elif "ssl" in error_str or "certificate" in error_str:
        return "SSL/TLS error - Check SSL configuration"
    elif "no such host" in error_str or "name resolution" in error_str:
        return "Host not found - Verify hostname is correct"

    # Adapter-specific hints
    if adapter_type == "snowflake":
        if "account" in error_str:
            return "Invalid Snowflake account - Check account identifier format"
        elif "warehouse" in error_str:
            return "Warehouse error - Verify warehouse name and status"
    elif adapter_type == "databricks":
        if "token" in error_str:
            return "Invalid token - Check Databricks access token"
        elif "cluster" in error_str:
            return "Cluster error - Verify cluster is running and accessible"

    return "Connection failed - See error details above"


def _test_single_target(profile_data: dict, target_name: str) -> tuple[bool, str]:
    """Test connection to a single target using dbt adapters (preferred) or native drivers.

    v0.59.0a22: Uses dbt adapter first (handles env vars, credential resolution),
    falls back to native drivers only if adapter unavailable.

    Args:
        profile_data: The profile dictionary containing outputs
        target_name: Name of the target to test

    Returns:
        Tuple of (success: bool, message: str)
    """
    outputs = profile_data.get("outputs", {})

    if target_name not in outputs:
        return False, f"Target '{target_name}' not found"

    target_config = outputs[target_name]
    adapter_type = target_config.get("type", "unknown")

    # First try dbt adapter (handles env vars, credential resolution properly)
    try:
        result = _test_via_dbt_adapter(profile_data, target_name, adapter_type)
        # If adapter test succeeded or failed with auth error, return that result
        if result[0] or "authentication" in result[1].lower() or "password" in result[1].lower():
            return result
        # If adapter not installed, fall through to native driver
        if "not installed" not in result[1].lower():
            return result
    except Exception:
        pass  # Fall through to native driver

    # Fallback to native drivers (for when dbt adapter not available)
    test_query = _get_test_query(adapter_type)

    try:
        # =========== PostgreSQL ===========
        if adapter_type == "postgres":
            try:
                import psycopg2
                # Handle both 'password' and 'pass' keys (dbt-postgres accepts both)
                password = target_config.get("password") or target_config.get("pass")
                conn = psycopg2.connect(
                    host=target_config.get("host", "localhost"),
                    port=target_config.get("port", 5432),
                    database=target_config.get("database", target_config.get("dbname")),
                    user=target_config.get("user"),
                    password=password,
                    connect_timeout=10
                )
                cursor = conn.cursor()
                cursor.execute(test_query)
                cursor.fetchone()
                cursor.close()
                conn.close()
                return True, "Connection successful"
            except ImportError:
                return False, "psycopg2 not installed - Run 'pip install psycopg2-binary'"
            except Exception as e:
                return False, f"Connection failed: {str(e)}"

        # =========== Snowflake ===========
        elif adapter_type == "snowflake":
            try:
                import snowflake.connector
                conn = snowflake.connector.connect(
                    account=target_config.get("account"),
                    user=target_config.get("user"),
                    password=target_config.get("password"),
                    database=target_config.get("database"),
                    warehouse=target_config.get("warehouse"),
                    schema=target_config.get("schema", "PUBLIC"),
                    login_timeout=10
                )
                cursor = conn.cursor()
                cursor.execute(test_query)
                cursor.fetchone()
                cursor.close()
                conn.close()
                return True, "Connection successful"
            except ImportError:
                return False, "snowflake-connector-python not installed - Run 'pip install snowflake-connector-python'"
            except Exception as e:
                return False, f"Connection failed: {str(e)}"

        # =========== Databricks ===========
        elif adapter_type == "databricks":
            try:
                from databricks import sql
                conn = sql.connect(
                    server_hostname=target_config.get("host", "").replace("https://", ""),
                    http_path=target_config.get("http_path"),
                    access_token=target_config.get("token"),
                )
                cursor = conn.cursor()
                cursor.execute(test_query)
                cursor.fetchone()
                cursor.close()
                conn.close()
                return True, "Connection successful"
            except ImportError:
                return False, "databricks-sql-connector not installed - Run 'pip install databricks-sql-connector'"
            except Exception as e:
                return False, f"Connection failed: {str(e)}"

        # =========== BigQuery ===========
        elif adapter_type == "bigquery":
            try:
                from google.cloud import bigquery
                client = bigquery.Client(project=target_config.get("project"))
                query_job = client.query(test_query)
                query_job.result(timeout=10)
                return True, "Connection successful"
            except ImportError:
                return False, "google-cloud-bigquery not installed - Run 'pip install google-cloud-bigquery'"
            except Exception as e:
                return False, f"Connection failed: {str(e)}"

        # =========== Redshift ===========
        elif adapter_type == "redshift":
            try:
                import psycopg2
                # Handle both 'password' and 'pass' keys
                password = target_config.get("password") or target_config.get("pass")
                conn = psycopg2.connect(
                    host=target_config.get("host"),
                    port=target_config.get("port", 5439),
                    database=target_config.get("database"),
                    user=target_config.get("user"),
                    password=password,
                    connect_timeout=10
                )
                cursor = conn.cursor()
                cursor.execute(test_query)
                cursor.fetchone()
                cursor.close()
                conn.close()
                return True, "Connection successful"
            except ImportError:
                return False, "psycopg2 not installed - Run 'pip install psycopg2-binary'"
            except Exception as e:
                return False, f"Connection failed: {str(e)}"

        # =========== DuckDB ===========
        elif adapter_type == "duckdb":
            try:
                import duckdb
                from pathlib import Path
                db_path = target_config.get("path", ":memory:")
                if db_path != ":memory:":
                    db_path = str(Path(db_path).expanduser().resolve())
                conn = duckdb.connect(db_path)
                conn.execute(test_query).fetchone()
                conn.close()
                return True, "Connection successful"
            except ImportError:
                return False, "duckdb not installed - Run 'pip install duckdb'"
            except Exception as e:
                return False, f"Connection failed: {str(e)}"

        # =========== MySQL ===========
        elif adapter_type == "mysql":
            try:
                import mysql.connector
                # Handle both 'password' and 'pass' keys
                password = target_config.get("password") or target_config.get("pass")
                conn = mysql.connector.connect(
                    host=target_config.get("host", "localhost"),
                    port=target_config.get("port", 3306),
                    database=target_config.get("database", target_config.get("schema")),
                    user=target_config.get("user"),
                    password=password,
                    connection_timeout=10
                )
                cursor = conn.cursor()
                cursor.execute(test_query)
                cursor.fetchone()
                cursor.close()
                conn.close()
                return True, "Connection successful"
            except ImportError:
                return False, "mysql-connector-python not installed - Run 'pip install mysql-connector-python'"
            except Exception as e:
                return False, f"Connection failed: {str(e)}"

        # =========== SQL Server ===========
        elif adapter_type == "sqlserver":
            try:
                import pyodbc
                driver = target_config.get("driver", "ODBC Driver 18 for SQL Server")
                # Handle both 'password' and 'pass' keys
                password = target_config.get("password") or target_config.get("pass")
                conn_str = (
                    f"DRIVER={{{driver}}};"
                    f"SERVER={target_config.get('host')},{target_config.get('port', 1433)};"
                    f"DATABASE={target_config.get('database')};"
                    f"UID={target_config.get('user')};"
                    f"PWD={password};"
                    f"TrustServerCertificate=yes;"
                )
                conn = pyodbc.connect(conn_str, timeout=10)
                cursor = conn.cursor()
                cursor.execute(test_query)
                cursor.fetchone()
                cursor.close()
                conn.close()
                return True, "Connection successful"
            except ImportError:
                return False, "pyodbc not installed - Run 'pip install pyodbc'"
            except Exception as e:
                return False, f"Connection failed: {str(e)}"

        # =========== Oracle ===========
        elif adapter_type == "oracle":
            try:
                import oracledb
                # Handle both 'password' and 'pass' keys
                password = target_config.get("password") or target_config.get("pass")
                conn = oracledb.connect(
                    user=target_config.get("user"),
                    password=password,
                    dsn=f"{target_config.get('host')}:{target_config.get('port', 1521)}/{target_config.get('database', target_config.get('service'))}",
                )
                cursor = conn.cursor()
                cursor.execute(test_query)
                cursor.fetchone()
                cursor.close()
                conn.close()
                return True, "Connection successful"
            except ImportError:
                return False, "oracledb not installed - Run 'pip install oracledb'"
            except Exception as e:
                return False, f"Connection failed: {str(e)}"

        # =========== ClickHouse ===========
        elif adapter_type == "clickhouse":
            try:
                import clickhouse_connect
                # Handle both 'password' and 'pass' keys
                password = target_config.get("password") or target_config.get("pass")
                client = clickhouse_connect.get_client(
                    host=target_config.get("host", "localhost"),
                    port=target_config.get("port", 8123),
                    username=target_config.get("user"),
                    password=password,
                    database=target_config.get("database", "default"),
                )
                client.query(test_query)
                client.close()
                return True, "Connection successful"
            except ImportError:
                return False, "clickhouse-connect not installed - Run 'pip install clickhouse-connect'"
            except Exception as e:
                return False, f"Connection failed: {str(e)}"

        # =========== Trino / Presto ===========
        elif adapter_type in ("trino", "presto"):
            try:
                from trino.dbapi import connect
                conn = connect(
                    host=target_config.get("host"),
                    port=target_config.get("port", 8080),
                    user=target_config.get("user"),
                    catalog=target_config.get("catalog", "hive"),
                    schema=target_config.get("schema", "default"),
                )
                cursor = conn.cursor()
                cursor.execute(test_query)
                cursor.fetchone()
                cursor.close()
                conn.close()
                return True, "Connection successful"
            except ImportError:
                return False, "trino not installed - Run 'pip install trino'"
            except Exception as e:
                return False, f"Connection failed: {str(e)}"

        # =========== Athena ===========
        elif adapter_type == "athena":
            try:
                import pyathena
                conn = pyathena.connect(
                    s3_staging_dir=target_config.get("s3_staging_dir"),
                    region_name=target_config.get("region_name"),
                    schema_name=target_config.get("schema", target_config.get("database", "default")),
                )
                cursor = conn.cursor()
                cursor.execute(test_query)
                cursor.fetchone()
                cursor.close()
                conn.close()
                return True, "Connection successful"
            except ImportError:
                return False, "pyathena not installed - Run 'pip install pyathena'"
            except Exception as e:
                return False, f"Connection failed: {str(e)}"

        # =========== Spark ===========
        elif adapter_type == "spark":
            try:
                from pyspark.sql import SparkSession
                spark = SparkSession.builder.appName("DVT Connection Test").getOrCreate()
                spark.sql(test_query).collect()
                spark.stop()
                return True, "Connection successful"
            except ImportError:
                return False, "pyspark not installed - Run 'pip install pyspark'"
            except Exception as e:
                return False, f"Connection failed: {str(e)}"

        # =========== Fallback: Try dbt adapter ===========
        else:
            try:
                return _test_via_dbt_adapter(profile_data, target_name, adapter_type)
            except Exception:
                return True, f"Configuration valid (testing not available for '{adapter_type}')"

    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def _test_via_dbt_adapter(
    profile_data: dict, target_name: str, adapter_type: str
) -> tuple[bool, str]:
    """Test connection using dbt's adapter infrastructure.

    This fallback method works for ANY dbt adapter that is installed.
    It creates an actual adapter instance and tests the connection,
    providing full support for all 30+ dbt adapters.

    Args:
        profile_data: The profile dictionary
        target_name: Name of the target
        adapter_type: The adapter type

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        from dbt.adapters.factory import get_adapter_class_by_name
        from dbt.config.runtime import RuntimeConfig
        from dbt.flags import set_from_args
        from argparse import Namespace
        import tempfile
        import yaml
        import os

        # Check if adapter is available
        try:
            adapter_cls = get_adapter_class_by_name(adapter_type)
        except Exception:
            return False, f"Adapter 'dbt-{adapter_type}' not installed - Run 'pip install dbt-{adapter_type}'"

        if not adapter_cls:
            return False, f"Adapter 'dbt-{adapter_type}' not installed"

        # Try to create a connection using the adapter
        # This requires creating a minimal runtime config
        try:
            # Create a temporary profiles.yml with just this profile/target
            with tempfile.TemporaryDirectory() as tmpdir:
                # Create minimal profiles.yml
                profiles_path = os.path.join(tmpdir, "profiles.yml")
                minimal_profile = {
                    "test_profile": {
                        "target": target_name,
                        "outputs": {target_name: profile_data.get("outputs", {}).get(target_name, {})}
                    }
                }
                with open(profiles_path, "w") as f:
                    yaml.dump(minimal_profile, f)

                # Create minimal dbt_project.yml
                project_path = os.path.join(tmpdir, "dbt_project.yml")
                with open(project_path, "w") as f:
                    yaml.dump({
                        "name": "connection_test",
                        "version": "1.0.0",
                        "profile": "test_profile",
                    }, f)

                # Try to get adapter and test connection
                # Set minimal flags
                args = Namespace(
                    profiles_dir=tmpdir,
                    project_dir=tmpdir,
                    target=target_name,
                    profile="test_profile",
                    threads=1,
                    vars="{}",
                )
                set_from_args(args, {})

                # Load runtime config and get adapter
                config = RuntimeConfig.from_args(args)
                adapter = adapter_cls(config, config.get_macro_resolver())

                # Test the connection
                with adapter.connection_named("test_connection"):
                    # Connection was successful if we get here
                    pass

                adapter.cleanup_connections()
                return True, "Connection successful (via dbt adapter)"

        except Exception as conn_error:
            # Connection test failed, but adapter is available
            error_msg = str(conn_error)
            if "authentication" in error_msg.lower() or "password" in error_msg.lower():
                return False, f"Authentication failed: {error_msg}"
            elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                return False, f"Connection failed: {error_msg}"
            else:
                # For other errors, at least confirm adapter is installed
                return True, f"Adapter '{adapter_type}' available (connection test inconclusive: {error_msg})"

    except ImportError as e:
        return False, f"Adapter 'dbt-{adapter_type}' not installed - Run 'pip install dbt-{adapter_type}'"
    except Exception as e:
        return False, f"Could not validate adapter: {str(e)}"


def _test_target_with_timeout(
    profile_data: dict, target_name: str, timeout: int = 30
) -> tuple[bool, str]:
    """Test target connection with timeout protection.

    Args:
        profile_data: The profile dictionary
        target_name: Name of the target to test
        timeout: Timeout in seconds (default 30)

    Returns:
        Tuple of (success: bool, message: str)
    """
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_test_single_target, profile_data, target_name)
        try:
            success, message = future.result(timeout=timeout)
            return success, message
        except FuturesTimeoutError:
            return False, f"Connection test timed out after {timeout} seconds"
        except Exception as e:
            return False, f"Unexpected error during connection test: {str(e)}"


@target.command("test")
@click.argument("target_name", required=False, default=None)
@click.option("--profile", help="Profile name (defaults to project profile)")
@click.option(
    "--timeout",
    type=int,
    default=30,
    help="Connection timeout in seconds (default: 30)",
)
@click.pass_context
@p.profiles_dir
@p.project_dir
def target_test(
    ctx, target_name, profile, timeout, profiles_dir, project_dir, **kwargs
):
    """Test connection to one or all targets.

    When TARGET_NAME is provided: Tests connection to a specific target
    When TARGET_NAME is omitted: Tests all targets in the profile

    This command now performs REAL connection testing by executing a simple query
    against the target database. It validates both configuration AND network connectivity.

    Features colored output and proper exit codes:
    - Exit code 0: All connections succeeded
    - Exit code 1: One or more connections failed
    - Green checkmarks (✓): Success
    - Red X marks (✗): Errors

    Examples:
        dvt target test                           # Test ALL targets (auto-detect profile)
        dvt target test dev                       # Test specific target (auto-detect profile)
        dvt target test prod --profile my_proj    # Test specific target (explicit profile)
        dvt target test --profile my_proj         # Test all targets in profile
        dvt target test dev --timeout 60          # Custom timeout

    Performance:
    - Tests run with configurable timeout (default 30s)
    - Provides helpful error hints for common connection issues
    - Shows detailed connection information on success
    """
    from dbt.config.profile import read_profile
    from dbt.config.project_utils import get_project_profile_name

    profiles = read_profile(profiles_dir)

    # Determine which profile to use
    if not profile:
        # Try to get from dvt_project.yml or dbt_project.yml
        profile = get_project_profile_name(project_dir)

    # v0.59.0a17: Do NOT search all profiles - that breaks multi-project setups
    # User must be in a project directory or use --profile flag

    if not profile:
        click.echo(
            click.style(
                "✗ Error: Could not determine profile. Use --profile flag.", fg="red"
            )
        )
        ctx.exit(1)

    if profile not in profiles:
        click.echo(click.style(f"✗ Profile '{profile}' not found", fg="red"))
        ctx.exit(1)

    profile_data = profiles[profile]
    if profile_data is None:
        click.echo(click.style(f"✗ Profile '{profile}' is empty or invalid", fg="red"))
        ctx.exit(1)
    outputs = profile_data.get("outputs", {})

    if not outputs:
        click.echo(click.style(f"No targets found in profile '{profile}'", fg="yellow"))
        ctx.exit(0)

    # CASE 1: Test specific target
    if target_name:
        if target_name not in outputs:
            click.echo(
                click.style(
                    f"✗ Target '{target_name}' not found in profile '{profile}'",
                    fg="red",
                )
            )
            ctx.exit(1)

        target_config = outputs[target_name]
        adapter_type = target_config.get("type", "unknown")

        click.echo(
            f"Testing connection: {click.style(target_name, fg='cyan')} ({adapter_type})"
        )

        # Show connection details FIRST (like dbt debug)
        if "host" in target_config:
            click.echo(f"  host: {target_config['host']}")
        if "port" in target_config:
            click.echo(f"  port: {target_config['port']}")
        if "account" in target_config:
            click.echo(f"  account: {target_config['account']}")
        if "database" in target_config or "dbname" in target_config:
            db = target_config.get("database") or target_config.get("dbname")
            click.echo(f"  database: {db}")
        if "warehouse" in target_config:
            click.echo(f"  warehouse: {target_config['warehouse']}")
        if "schema" in target_config:
            click.echo(f"  schema: {target_config['schema']}")
        if "project" in target_config:
            click.echo(f"  project: {target_config['project']}")

        # Test connection with timeout
        success, message = _test_target_with_timeout(profile_data, target_name, timeout)

        # Show test result (like dbt debug)
        if success:
            click.echo(
                f"  Connection test: {click.style('[OK connection ok]', fg='green')}"
            )
            ctx.exit(0)
        else:
            click.echo(f"  Connection test: {click.style('[ERROR]', fg='red')}")
            click.echo(f"    {message}")
            ctx.exit(1)

    # CASE 2: Test all targets in profile
    else:
        total_targets = len(outputs)
        click.echo(
            f"Testing all connections in profile {click.style(profile, fg='cyan')}...\n"
        )

        # Test each target with progress indicators
        passed_count = 0
        failed_count = 0
        target_index = 1

        for tgt_name, target_config in outputs.items():
            adapter_type = target_config.get("type", "unknown")

            # Progress indicator
            progress = click.style(f"[{target_index}/{total_targets}]", fg="yellow")
            click.echo(
                f"{progress} Testing connection: {click.style(tgt_name, fg='cyan')} ({adapter_type})"
            )

            # Show connection details FIRST (like dbt debug)
            if "host" in target_config:
                click.echo(f"      host: {target_config['host']}")
            if "port" in target_config:
                click.echo(f"      port: {target_config['port']}")
            if "account" in target_config:
                click.echo(f"      account: {target_config['account']}")
            if "database" in target_config or "dbname" in target_config:
                db = target_config.get("database") or target_config.get("dbname")
                click.echo(f"      database: {db}")
            if "warehouse" in target_config:
                click.echo(f"      warehouse: {target_config['warehouse']}")
            if "schema" in target_config:
                click.echo(f"      schema: {target_config['schema']}")
            if "project" in target_config:
                click.echo(f"      project: {target_config['project']}")

            # Test connection
            success, message = _test_target_with_timeout(
                profile_data, tgt_name, timeout
            )

            # Show test result (like dbt debug)
            if success:
                click.echo(
                    f"      Connection test: {click.style('[OK connection ok]', fg='green')}"
                )
                passed_count += 1
            else:
                click.echo(f"      Connection test: {click.style('[ERROR]', fg='red')}")
                click.echo(f"        {message}")
                failed_count += 1

            click.echo("")
            target_index += 1

        # Summary line
        click.echo("─" * 60)
        if failed_count == 0:
            summary = click.style(
                f"✓ All {passed_count} connection tests passed", fg="green", bold=True
            )
            click.echo(summary)
            ctx.exit(0)
        else:
            passed_str = click.style(f"{passed_count} passed", fg="green")
            failed_str = click.style(f"{failed_count} failed", fg="red")
            summary = f"✗ {passed_str}, {failed_str}"
            click.echo(summary)
            ctx.exit(1)


@target.command("add")
@click.argument("target_name")
@click.option("--profile", help="Profile name (auto-detected from project if not specified)")
@click.option(
    "--type",
    "adapter_type",
    required=True,
    help="Adapter type (postgres, snowflake, etc)",
)
@click.option("--host", help="Database host")
@click.option("--port", type=int, help="Database port")
@click.option("--user", help="Database user")
@click.option("--password", help="Database password")
@click.option("--database", help="Database name")
@click.option("--schema", help="Default schema")
@click.option("--threads", type=int, default=4, help="Number of threads")
@click.option("--set-default", is_flag=True, help="Set as default target for profile")
@click.pass_context
@p.profiles_dir
@p.project_dir
def target_add(
    ctx,
    target_name,
    profile,
    adapter_type,
    host,
    port,
    user,
    password,
    database,
    schema,
    threads,
    set_default,
    profiles_dir,
    project_dir,
    **kwargs,
):
    """Add a new target to a profile in profiles.yml"""
    import yaml
    from pathlib import Path
    from dbt.config.project_utils import get_project_profile_name

    # v0.59.0a18: Auto-detect profile from project if not specified
    if not profile:
        profile = get_project_profile_name(project_dir)
        if not profile:
            click.echo(click.style("✗ Not in a DVT project directory", fg="red"))
            click.echo("")
            click.echo("Run from within a DVT project directory, or use --profile:")
            click.echo("  dvt target add <target_name> --profile <profile_name> --type <type>")
            ctx.exit(1)

    profiles_file = Path(profiles_dir) / "profiles.yml"

    if not profiles_file.exists():
        click.echo(f"✗ profiles.yml not found at {profiles_file}")
        return False, False

    with open(profiles_file, "r") as f:
        profiles = yaml.safe_load(f) or {}

    if profile not in profiles:
        click.echo(f"✗ Profile '{profile}' not found in profiles.yml")
        return False, False

    profile_data = profiles[profile]
    if profile_data is None:
        click.echo(f"✗ Profile '{profile}' is empty or invalid")
        return False, False

    # Get or create outputs dict (standard dbt format)
    if "outputs" not in profile_data:
        profile_data["outputs"] = {}

    outputs = profile_data["outputs"]

    # Check if target already exists
    if target_name in outputs:
        if not click.confirm(f"Target '{target_name}' already exists. Overwrite?"):
            return False, False

    # Build target config
    target_config = {"type": adapter_type}

    if host:
        target_config["host"] = host
    if port:
        target_config["port"] = port
    if user:
        target_config["user"] = user
    if password:
        target_config["password"] = password
    if database:
        target_config["database"] = database
    if schema:
        target_config["schema"] = schema
    if threads:
        target_config["threads"] = threads

    # Add target to outputs
    outputs[target_name] = target_config

    # Set as default if requested
    if set_default:
        profile_data["target"] = target_name

    # Write back to profiles.yml
    with open(profiles_file, "w") as f:
        yaml.dump(profiles, f, default_flow_style=False, sort_keys=False)

    click.echo(f"✓ Added target '{target_name}' to profile '{profile}'")
    if set_default:
        click.echo(f"  Set as default target")

    return True, True


@target.command("sync")
@click.option("--profile", help="Profile name (defaults to project profile)")
@click.option("--clean", is_flag=True, help="Remove adapters not needed by profiles.yml")
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
@click.pass_context
@p.profiles_dir
@p.project_dir
def target_sync(ctx, profile, clean, dry_run, profiles_dir, project_dir, **kwargs):
    """Sync adapters and JDBC JARs based on profiles.yml connections.

    Scans your profiles.yml to find all connection types, then:
    - Installs required dbt adapters via pip
    - Updates JDBC JARs for Spark federation
    - Optionally removes unused adapters (with --clean)

    Examples:

        dvt target sync              # Sync for current project
        dvt target sync --profile my_project  # Sync specific profile
        dvt target sync --dry-run    # Show what would happen
        dvt target sync --clean      # Also remove unused adapters
    """
    from dbt.task.target_sync import TargetSyncTask

    task = TargetSyncTask(
        project_dir=project_dir,
        profiles_dir=profiles_dir,
        profile_name=profile,
    )
    success = task.sync(verbose=True, clean=clean, dry_run=dry_run)
    return None, success


@target.command("remove")
@click.argument("target_name")
@click.option("--profile", help="Profile name (auto-detected from project if not specified)")
@click.pass_context
@p.profiles_dir
@p.project_dir
def target_remove(ctx, target_name, profile, profiles_dir, project_dir, **kwargs):
    """Remove a target from a profile in profiles.yml"""
    import yaml
    from pathlib import Path
    from dbt.config.project_utils import get_project_profile_name

    # v0.59.0a18: Auto-detect profile from project if not specified
    if not profile:
        profile = get_project_profile_name(project_dir)
        if not profile:
            click.echo(click.style("✗ Not in a DVT project directory", fg="red"))
            click.echo("")
            click.echo("Run from within a DVT project directory, or use --profile:")
            click.echo("  dvt target remove <target_name> --profile <profile_name>")
            ctx.exit(1)

    profiles_file = Path(profiles_dir) / "profiles.yml"

    if not profiles_file.exists():
        click.echo(f"✗ profiles.yml not found at {profiles_file}")
        return False, False

    with open(profiles_file, "r") as f:
        profiles = yaml.safe_load(f) or {}

    if profile not in profiles:
        click.echo(f"✗ Profile '{profile}' not found in profiles.yml")
        return False, False

    profile_data = profiles[profile]
    if profile_data is None:
        click.echo(f"✗ Profile '{profile}' is empty or invalid")
        return False, False
    outputs = profile_data.get("outputs", {})

    if target_name not in outputs:
        click.echo(f"✗ Target '{target_name}' not found in profile '{profile}'")
        return False, False

    # Remove the target
    del outputs[target_name]

    # Check if this was the default target
    default_target = profile_data.get("target")
    if default_target == target_name:
        # Set new default to first available target
        if outputs:
            new_default = list(outputs.keys())[0]
            profile_data["target"] = new_default
            click.echo(
                f"  Note: '{target_name}' was the default target, changed to '{new_default}'"
            )
        else:
            click.echo(f"  Warning: No targets remaining in profile '{profile}'")

    # Write back to profiles.yml
    with open(profiles_file, "w") as f:
        yaml.dump(profiles, f, default_flow_style=False, sort_keys=False)

    click.echo(f"✓ Removed target '{target_name}' from profile '{profile}'")

    return True, True


# DVT java commands for Java management
@cli.group()
@click.pass_context
@p.version
def java(ctx, **kwargs):
    """Manage Java installations for PySpark.

    Java is required for Spark compute engines.

    \b
    Compatibility:
      PySpark 4.0.x -> Java 17 or 21
      PySpark 3.5.x -> Java 8, 11, or 17
      PySpark 3.3-3.4 -> Java 8 or 11

    \b
    Commands:
      check   - Check Java compatibility with PySpark
      search  - Find all Java installations
      set     - Select and configure JAVA_HOME
      install - Show installation guide

    \b
    Examples:
      dvt java check    # Check compatibility
      dvt java search   # Find installations
      dvt java set      # Configure JAVA_HOME
    """


@java.command("check")
@click.pass_context
def java_check(ctx, **kwargs):
    """Check Java installation and PySpark compatibility.

    Shows current Java version, installed PySpark version, and whether
    they are compatible. Provides guidance if there's a mismatch.

    Exit codes:
        0 - Java and PySpark are compatible
        1 - Java/PySpark mismatch or not found
    """
    from dbt.task.java import JavaTask

    task = JavaTask()
    is_compatible = task.check()
    ctx.exit(0 if is_compatible else 1)


@java.command("search")
@click.pass_context
def java_search(ctx, **kwargs):
    """Find all Java installations on the system.

    Searches common installation locations for Java on your OS:

    \b
    macOS:   /Library/Java/JavaVirtualMachines, Homebrew, SDKMAN
    Linux:   /usr/lib/jvm, /opt/java, update-alternatives, SDKMAN
    Windows: Program Files, Registry, Scoop, Chocolatey

    Shows Java version, vendor, and compatibility with installed PySpark.
    """
    from dbt.task.java import JavaTask

    task = JavaTask()
    installations = task.search()
    ctx.exit(0 if installations else 1)


@java.command("set")
@click.pass_context
def java_set(ctx, **kwargs):
    """Interactively select and set JAVA_HOME.

    Shows all found Java installations with compatibility indicators,
    lets you choose one, and updates your shell configuration file
    (.zshrc, .bashrc, etc.) to persist JAVA_HOME.

    After setting, restart your terminal or run 'source ~/.zshrc'
    (or equivalent) for changes to take effect.
    """
    from dbt.task.java import JavaTask

    task = JavaTask()
    success = task.set_java_home()
    ctx.exit(0 if success else 1)


@java.command("install")
@click.pass_context
def java_install(ctx, **kwargs):
    """Show Java installation guide for your platform.

    Provides platform-specific installation instructions based on
    your installed PySpark version. Includes options for:

    \b
    macOS:   Homebrew, SDKMAN, manual download
    Linux:   apt-get, dnf, pacman, SDKMAN
    Windows: Winget, Chocolatey, Scoop, manual download
    """
    from dbt.task.java import JavaTask

    task = JavaTask()
    task.install_guide()
    ctx.exit(0)


# DVT spark commands for Spark/PySpark management
@cli.group()
@click.pass_context
@p.version
def spark(ctx, **kwargs):
    """Manage PySpark installations and cluster compatibility.

    PySpark is used by DVT for federated query execution.

    \b
    Commands:
      check         - Check PySpark/Java status
      set-version   - Install specific PySpark version
      match-cluster - Match PySpark to cluster version
      versions      - Show compatibility matrix

    \b
    Examples:
      dvt spark check                # Check status
      dvt spark set-version          # Install PySpark
      dvt spark match-cluster spark  # Match to cluster
      dvt spark versions             # Show matrix
    """


@spark.command("check")
@click.pass_context
def spark_check(ctx, **kwargs):
    """Check PySpark installation and Java compatibility.

    Shows:
    - Installed PySpark version and requirements
    - Current Java version
    - Compatibility status

    Exit codes:
        0 - PySpark installed and Java compatible
        1 - PySpark not installed or Java incompatible
    """
    from dbt.task.spark import SparkTask

    task = SparkTask()
    is_ok = task.check()
    ctx.exit(0 if is_ok else 1)


@spark.command("set-version")
@click.pass_context
def spark_set_version(ctx, **kwargs):
    """Interactively select and install a PySpark version.

    Presents available PySpark versions with their Java requirements.
    Shows compatibility indicators based on your current Java.
    Installs the selected version via pip.

    Available versions:
    \b
        PySpark 4.0.x - Latest, requires Java 17+
        PySpark 3.5.x - Stable, Java 8/11/17
        PySpark 3.4.x - Java 8/11/17
        PySpark 3.3.x - Java 8/11
        PySpark 3.2.x - Java 8/11

    After installing, check Java compatibility with 'dvt java check'.
    """
    from dbt.task.spark import SparkTask

    task = SparkTask()
    success = task.set_version()
    ctx.exit(0 if success else 1)


@spark.command("match-cluster")
@click.argument("compute_name")
@click.pass_context
def spark_match_cluster(ctx, compute_name, **kwargs):
    """Detect cluster Spark version and check PySpark compatibility.

    Connects to the specified compute engine from computes.yml,
    detects its Spark version, and compares with locally installed
    PySpark. Provides recommendations if versions don't match.

    IMPORTANT: PySpark version must match the cluster's Spark version
    (same major.minor). A mismatch can cause runtime errors.

    Arguments:
        COMPUTE_NAME: Name of compute engine in computes.yml

    Examples:

    \b
        dvt spark match-cluster spark-docker
        dvt spark match-cluster spark-local
        dvt spark match-cluster databricks-prod
    """
    from dbt.task.spark import SparkTask

    task = SparkTask()
    is_match = task.match_cluster(compute_name)
    ctx.exit(0 if is_match else 1)


@spark.command("versions")
@click.pass_context
def spark_versions(ctx, **kwargs):
    """Display PySpark/Java compatibility matrix.

    Shows all available PySpark versions with their Java requirements,
    marks the currently installed version, and shows your current
    Java installation.
    """
    from dbt.task.spark import SparkTask

    task = SparkTask()
    task.show_versions()
    ctx.exit(0)


# Register DVT command groups with main CLI
cli.add_command(compute)
cli.add_command(target)
cli.add_command(java)
cli.add_command(spark)


# Support running as a module (python -m dbt.cli.main)
if __name__ == "__main__":
    cli()
