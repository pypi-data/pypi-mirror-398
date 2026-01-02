# =============================================================================
# DVT Run Task with Rich UI Enhancement
# =============================================================================
# Wrapper around standard RunTask that adds beautiful Rich UI output.
#
# DVT v0.58.0: Enhanced CLI output with Rich library
# DVT v0.59.0a36: Header + Summary panels (works with dbt's event system)
#
# IMPORTANT: This wrapper does NOT modify core dbt execution logic.
# All DVT compute rules are enforced in run.py's ModelRunner.execute().
#
# DVT Compute Rules (implemented in run.py):
#   1. Pushdown Preference: Same-target -> Adapter pushdown (no Spark)
#   2. Federation Path: Cross-target -> Spark execution
#   3. Compute Hierarchy: default < model config < CLI --target-compute
#   4. Target Hierarchy: default < model config < CLI --target
#
# NOTE: Rich's Live context conflicts with dbt's fire_event logging system.
# We use a header+summary approach instead of live-updating progress bars.
# =============================================================================

from __future__ import annotations

import os
import time
import threading
from typing import Any, Dict, Optional, AbstractSet

from dbt.artifacts.schemas.results import NodeStatus
from dbt.cli.flags import Flags
from dbt.config import RuntimeConfig
from dbt.contracts.graph.manifest import Manifest
from dbt.task.run import RunTask, ModelRunner
from dbt.task.dvt_output import DVTMultiBarDisplay, HAS_RICH

# Lock for thread-safe Rich console updates
_console_lock = threading.Lock()


class DVTRunTask(RunTask):
    """
    DVT Run Task with Rich UI enhancement.

    This class wraps the standard RunTask to add beautiful CLI output
    while preserving all dbt-core and DVT compute logic.

    DVT v0.59.0a36 Features:
    - Header panel: Shows operation, target, and compute info
    - dbt output: Normal dbt event logging flows during execution
    - Summary panel: Errors grouped by execution path (pushdown vs federation)
    - Warning tracking: Materialization coercions (e.g., view→table)
    - Spark logging: Output captured to target/{compute}_log.txt

    Note: Does NOT use Rich's Live context (conflicts with dbt's fire_event).
    Instead, prints a header before execution and summary after.

    Usage:
        task = DVTRunTask(args, config, manifest)
        results = task.run()
    """

    def __init__(
        self,
        args: Flags,
        config: RuntimeConfig,
        manifest: Manifest,
        batch_map: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(args, config, manifest, batch_map)
        self._display: Optional[DVTMultiBarDisplay] = None
        self._use_rich_output = HAS_RICH and not getattr(args, 'QUIET', False)
        self._execution_paths: Dict[str, str] = {}  # Track pushdown vs federation
        self._spark_logger = None

    def _get_target_info(self) -> str:
        """Get the current target name for display."""
        cli_target = getattr(self.config.args, 'TARGET', None)
        return cli_target or self.config.target_name or "default"

    def _get_compute_info(self) -> str:
        """Get the current compute engine for display."""
        cli_compute = getattr(self.config.args, 'TARGET_COMPUTE', None)
        return cli_compute or "auto"

    def _start_spark_logger(self) -> None:
        """Start Spark output logging to target directory.

        Note: suppress_console=False so dbt's event output flows normally.
        Spark output is tee'd to the log file for later reference.
        """
        try:
            from dbt.compute.spark_logger import get_spark_logger

            # Get target directory
            target_dir = os.path.join(os.getcwd(), "target")
            compute_name = self._get_compute_info().replace("-", "_")
            if compute_name == "auto":
                compute_name = "spark"

            self._spark_logger = get_spark_logger(target_dir, compute_name)
            # Don't suppress console - let dbt events flow normally
            # Spark output is tee'd to file for debugging
            self._spark_logger.start_session(suppress_console=False)
        except Exception:
            # Don't fail if logging setup fails
            self._spark_logger = None

    def _stop_spark_logger(self) -> None:
        """Stop Spark output logging."""
        if self._spark_logger:
            try:
                self._spark_logger.end_session()
            except Exception:
                pass
            self._spark_logger = None

    def _determine_execution_path(self, result) -> str:
        """Determine if model was executed via pushdown or federation."""
        # Check if already tracked
        if result.node and result.node.unique_id in self._execution_paths:
            return self._execution_paths[result.node.unique_id]

        # Check error message for federation hints
        error_msg = result.message or ""
        if "Federated" in error_msg or "JDBC" in error_msg or "Spark" in error_msg:
            return "FEDERATION"

        # Default to pushdown for all other cases (success or non-federation errors)
        return "PUSHDOWN"

    def _check_materialization_warning(self, result) -> Optional[str]:
        """Check if model has materialization coercion warning."""
        if not result.node:
            return None

        # Get model's intended materialization
        config = getattr(result.node, 'config', None)
        if not config:
            return None

        materialized = getattr(config, 'materialized', 'table')

        # Check if it's a cross-target view (coerced to table)
        exec_path = self._determine_execution_path(result)
        if exec_path == "FEDERATION" and materialized == "view":
            return "view -> table (cross-target requires table)"

        return None

    def before_run(self, adapter, selected_uids: AbstractSet[str]):
        """Called before running models - initialize multi-bar display."""
        # Call parent first (handles schemas, cache, hooks, metadata)
        result = super().before_run(adapter, selected_uids)

        # Initialize multi-bar Rich display if available (BEFORE Spark logger)
        if self._use_rich_output and hasattr(self, '_flattened_nodes') and self._flattened_nodes:
            try:
                self._display = DVTMultiBarDisplay(
                    title="DVT Run",
                    operation="run",
                    target=self._get_target_info(),
                    compute=self._get_compute_info(),
                )

                # Initialize ALL model tracking upfront from _flattened_nodes
                self._display.initialize_models(self._flattened_nodes)

                # Print header before dbt output starts
                self._display.start_display()

            except Exception:
                # Fall back to standard output on any Rich error
                self._display = None
                self._use_rich_output = False

        # Start Spark output logging AFTER display header is shown
        self._start_spark_logger()

        return result

    def _handle_result(self, result) -> None:
        """Handle a single model result - update the specific model's progress bar."""
        # Call parent handler first (fires standard dbt events for logging)
        super()._handle_result(result)

        # Update the specific model's bar in multi-bar display
        if self._display and result.node:
            try:
                # Determine execution path
                exec_path = self._determine_execution_path(result)
                self._execution_paths[result.node.unique_id] = exec_path

                # Get error message
                error_msg = result.message if result.status in (
                    NodeStatus.Error, NodeStatus.Fail
                ) else None

                # Check for materialization warning
                warning = self._check_materialization_warning(result)

                # Map status
                if result.status in (NodeStatus.Error, NodeStatus.Fail):
                    status = "error"
                elif result.status == NodeStatus.Skipped:
                    status = "skip"
                elif result.status == NodeStatus.Warn:
                    status = "warn"
                else:
                    status = "pass"

                # Calculate duration in milliseconds
                duration_ms = (result.execution_time or 0) * 1000

                # Thread-safe update to the model's progress bar
                with _console_lock:
                    self._display.update_model_complete(
                        unique_id=result.node.unique_id,
                        status=status,
                        duration_ms=duration_ms,
                        execution_path=exec_path,
                        error_message=error_msg,
                        warning=warning,
                    )

            except Exception:
                # Silently ignore Rich display errors
                pass

    def after_run(self, adapter, results) -> None:
        """Called after all models complete - show summary."""
        # Stop Spark logging FIRST so we can print to console
        self._stop_spark_logger()

        # Stop multi-bar display and show summary
        if self._display:
            try:
                self._display.stop_display()
                self._display.print_summary()
            except Exception:
                pass

        # Call parent (handles end hooks)
        super().after_run(adapter, results)

    def task_end_messages(self, results) -> None:
        """Override to prevent duplicate output when using Rich."""
        if self._display:
            # Rich display handles summary, skip default messages
            return

        # Fall back to standard dbt output
        super().task_end_messages(results)


def create_dvt_run_task(
    args: Flags,
    config: RuntimeConfig,
    manifest: Manifest,
    batch_map: Optional[Dict[str, Any]] = None,
) -> RunTask:
    """
    Factory function to create appropriate run task.

    Returns DVTRunTask with Rich UI if available and not in quiet mode,
    otherwise returns standard RunTask.

    Args:
        args: CLI flags
        config: Runtime configuration
        manifest: Project manifest
        batch_map: Optional batch map for retry

    Returns:
        RunTask instance (DVTRunTask or standard RunTask)
    """
    # Check if we should use Rich output
    use_rich = HAS_RICH and not getattr(args, 'QUIET', False)

    if use_rich:
        return DVTRunTask(args, config, manifest, batch_map)
    else:
        return RunTask(args, config, manifest, batch_map)
