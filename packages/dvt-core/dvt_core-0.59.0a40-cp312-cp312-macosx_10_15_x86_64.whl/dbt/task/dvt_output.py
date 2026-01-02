# =============================================================================
# DVT Rich Output Helpers
# =============================================================================
# Beautiful CLI output using Rich library for DVT commands.
#
# DVT v0.58.0: Unified output styling for all DVT commands
# DVT v0.58.1: Enhanced for dvt run integration
# DVT v0.59.0a36: Multi-bar progress display for all operations
# =============================================================================

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

# Try to import Rich - graceful fallback if not available
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    Console = None  # type: ignore


class ModelStatus(Enum):
    """Status for a model in the progress display."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WARNED = "warned"


# Status icons for display
STATUS_ICONS = {
    ModelStatus.PENDING: "○",
    ModelStatus.RUNNING: "⏳",
    ModelStatus.PASSED: "✓",
    ModelStatus.FAILED: "✗",
    ModelStatus.SKIPPED: "⊘",
    ModelStatus.WARNED: "⚠",
}

# Operation icons for header
OPERATION_ICONS = {
    "run": "▶",
    "build": "🔧",
    "seed": "🌱",
    "profile": "📊",
    "test": "✓",
    "compile": "📝",
    "snapshot": "📸",
    "retract": "🗑",
}


@dataclass
class ModelInfo:
    """Information about a model for multi-bar display."""
    name: str
    unique_id: str
    materialization: str = "table"
    status: ModelStatus = ModelStatus.PENDING
    execution_path: str = ""
    duration_ms: float = 0.0
    warning: str = ""  # e.g., "view→table" for coercion
    error_message: str = ""


@dataclass
class ErrorInfo:
    """Error information for summary display."""
    model_name: str
    message: str
    duration_ms: float
    execution_path: str


@dataclass
class DVTRunStats:
    """Statistics for a DVT run execution."""
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    warned: int = 0
    errored: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    pushdown_count: int = 0
    federation_count: int = 0

    @property
    def duration_seconds(self) -> float:
        return self.end_time - self.start_time if self.end_time else 0.0

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 100.0
        return (self.passed / self.total) * 100


# =============================================================================
# DVTMultiBarDisplay - Summary-focused display (v0.59.0a36)
# =============================================================================
#
# NOTE: Rich's Live context conflicts with dbt's event logging system.
# dbt fires events via fire_event() which write directly to stdout, bypassing
# Rich's Live display context. This causes display corruption.
#
# SOLUTION: Instead of live multi-bar updates, we:
# 1. Print a header panel at the start (one-time)
# 2. Let dbt's normal event output flow during execution
# 3. Track model results internally (no live display updates)
# 4. Print a beautiful summary panel at the end with DVT-specific info
#
# This approach works WITH dbt's event system rather than fighting it.
# =============================================================================

class DVTMultiBarDisplay:
    """
    Enhanced progress display for DVT commands with summary focus.

    Features:
    - Header panel with operation, target, and compute (printed at start)
    - Track model results as they complete
    - Warning collection for materialization coercions
    - Summary screen with errors grouped by execution path

    DVT v0.59.0a36: Works with dbt's event system - header + summary approach.

    Note: Does NOT use Rich's Live context due to conflicts with dbt's
    fire_event logging. Instead, lets dbt output flow normally and provides
    enhanced header and summary panels.
    """

    def __init__(
        self,
        title: str = "DVT Run",
        operation: str = "run",
        target: str = "",
        compute: str = "",
    ):
        self.title = title
        self.operation = operation
        self.target = target
        self.compute = compute
        self._use_rich = HAS_RICH
        self._console: Optional[Console] = None
        self._models: Dict[str, ModelInfo] = {}  # unique_id -> ModelInfo
        self._errors_pushdown: List[ErrorInfo] = []
        self._errors_federation: List[ErrorInfo] = []
        self._warnings: List[Tuple[str, str]] = []  # (model_name, warning)
        self._lock = threading.Lock()
        self.stats = DVTRunStats()
        self._header_printed = False

        if self._use_rich:
            self._console = Console()

    def _build_header(self) -> Panel:
        """Build the header panel with operation, target, and compute."""
        op_icon = OPERATION_ICONS.get(self.operation.lower(), "▶")

        info_parts = [
            f"[bold cyan]Operation:[/bold cyan] [bold yellow]{op_icon} {self.operation.upper()}[/bold yellow]",
        ]
        if self.target:
            info_parts.append(f"[bold cyan]Target:[/bold cyan] [yellow]{self.target}[/yellow]")
        if self.compute:
            info_parts.append(f"[bold cyan]Compute:[/bold cyan] [yellow]{self.compute}[/yellow]")

        info_line = "  │  ".join(info_parts)

        return Panel(
            info_line,
            title=f"[bold magenta]{self.title}[/bold magenta]",
            border_style="magenta",
            box=box.DOUBLE,
        )

    def initialize_models(self, nodes: List[Any]) -> None:
        """
        Initialize model tracking (no visual progress bars).

        Args:
            nodes: List of ResultNode objects from _flattened_nodes
        """
        for node in nodes:
            # Get model info from node
            unique_id = getattr(node, 'unique_id', str(node))
            name = getattr(node, 'name', unique_id.split('.')[-1])

            # Get materialization from config
            config = getattr(node, 'config', None)
            materialization = "table"
            if config:
                materialization = getattr(config, 'materialized', 'table') or 'table'

            # Skip ephemeral models
            if materialization == "ephemeral":
                continue

            # Create ModelInfo for tracking
            model_info = ModelInfo(
                name=name,
                unique_id=unique_id,
                materialization=materialization,
            )
            self._models[unique_id] = model_info

        self.stats.total = len(self._models)

    def start_display(self) -> None:
        """Print the header panel (one-time, before execution starts)."""
        if not self._use_rich or self._header_printed:
            return

        self.stats.start_time = time.time()

        # Print header panel immediately
        header = self._build_header()
        self._console.print(header)
        self._console.print()  # Add blank line before dbt output
        self._header_printed = True

    def update_model_start(self, unique_id: str) -> None:
        """Mark a model as running (no visual update - dbt handles this)."""
        with self._lock:
            if unique_id in self._models:
                self._models[unique_id].status = ModelStatus.RUNNING

    def update_model_complete(
        self,
        unique_id: str,
        status: str,
        duration_ms: float,
        execution_path: str,
        error_message: Optional[str] = None,
        warning: Optional[str] = None,
    ) -> None:
        """
        Track a model's completion (no live visual update).

        dbt's event system shows progress during execution.
        We track results for the summary panel.

        Args:
            unique_id: Model unique ID
            status: Result status (pass, fail, skip, warn, error)
            duration_ms: Execution time in milliseconds
            execution_path: PUSHDOWN or FEDERATION
            error_message: Error message if failed
            warning: Warning message (e.g., materialization coercion)
        """
        with self._lock:
            # Map status string to ModelStatus
            status_map = {
                "pass": ModelStatus.PASSED,
                "success": ModelStatus.PASSED,
                "fail": ModelStatus.FAILED,
                "error": ModelStatus.FAILED,
                "skip": ModelStatus.SKIPPED,
                "warn": ModelStatus.WARNED,
            }
            model_status = status_map.get(status.lower(), ModelStatus.PASSED)

            # Update model info
            if unique_id in self._models:
                model_info = self._models[unique_id]
                model_info.status = model_status
                model_info.duration_ms = duration_ms
                model_info.execution_path = execution_path
                model_info.warning = warning or ""
                model_info.error_message = error_message or ""
                model_name = model_info.name
            else:
                model_name = unique_id.split('.')[-1]

            # Update stats
            self._update_stats(status, execution_path)

            # Collect errors
            if error_message and model_status == ModelStatus.FAILED:
                error_info = ErrorInfo(model_name, error_message, duration_ms, execution_path)
                if execution_path == "PUSHDOWN":
                    self._errors_pushdown.append(error_info)
                else:
                    self._errors_federation.append(error_info)

            # Collect warnings
            if warning:
                self._warnings.append((model_name, warning))

    def _update_stats(self, status: str, execution_path: str) -> None:
        """Update stats counters."""
        status_lower = status.lower()
        if status_lower in ("pass", "success"):
            self.stats.passed += 1
        elif status_lower in ("fail", "error"):
            self.stats.errored += 1
        elif status_lower == "skip":
            self.stats.skipped += 1
        elif status_lower == "warn":
            self.stats.warned += 1

        if execution_path == "PUSHDOWN":
            self.stats.pushdown_count += 1
        elif execution_path == "FEDERATION":
            self.stats.federation_count += 1

    def stop_display(self) -> None:
        """Record end time (no Live context to stop)."""
        self.stats.end_time = time.time()

    def print_summary(self) -> None:
        """Print the summary panel with errors grouped by execution path."""
        if not self._use_rich:
            self._print_summary_fallback()
            return

        duration = self.stats.duration_seconds

        # Build summary content
        if self.stats.errored > 0:
            status_text = f"[bold red]✗ Completed with {self.stats.errored} error(s)[/bold red]"
            border_color = "red"
        elif self.stats.warned > 0 or self._warnings:
            status_text = f"[bold yellow]⚠ Completed with warnings[/bold yellow]"
            border_color = "yellow"
        else:
            status_text = f"[bold green]✓ Completed successfully[/bold green]"
            border_color = "green"

        # Stats line
        stats_parts = [f"[bold]Passed:[/bold] {self.stats.passed}"]
        if self.stats.errored:
            stats_parts.append(f"[bold red]Failed:[/bold red] {self.stats.errored}")
        if self.stats.skipped:
            stats_parts.append(f"[bold yellow]Skipped:[/bold yellow] {self.stats.skipped}")
        if self._warnings:
            stats_parts.append(f"[bold yellow]Warnings:[/bold yellow] {len(self._warnings)}")
        stats_line = "  │  ".join(stats_parts)

        # Execution path counts
        path_parts = []
        if self.stats.pushdown_count:
            path_parts.append(f"[blue]Pushdown:[/blue] {self.stats.pushdown_count}")
        if self.stats.federation_count:
            path_parts.append(f"[magenta]Federation:[/magenta] {self.stats.federation_count}")
        path_parts.append(f"[dim]Duration:[/dim] {duration:.1f}s")
        path_line = "  │  ".join(path_parts)

        summary_content = f"{status_text}\n\n{stats_line}\n{path_line}"

        # Print main summary panel
        self._console.print()
        summary_panel = Panel(
            summary_content,
            title=f"[bold]{self.title} Complete[/bold]",
            border_style=border_color,
            box=box.ROUNDED,
        )
        self._console.print(summary_panel)

        # Print warnings panel if any
        if self._warnings:
            self._print_warnings_panel()

        # Print error panels grouped by path
        if self._errors_pushdown:
            self._print_error_panel("Pushdown Errors", self._errors_pushdown, "blue")
        if self._errors_federation:
            self._print_error_panel("Federation Errors", self._errors_federation, "magenta")

        self._console.print()

    def _print_warnings_panel(self) -> None:
        """Print materialization warnings panel."""
        lines = []
        for model_name, warning in self._warnings[:10]:
            lines.append(f"  • [bold]{model_name}:[/bold] {warning}")
        if len(self._warnings) > 10:
            lines.append(f"  [dim]... and {len(self._warnings) - 10} more[/dim]")

        content = "\n".join(lines)
        panel = Panel(
            content,
            title=f"[bold yellow]⚠ Materialization Warnings ({len(self._warnings)})[/bold yellow]",
            border_style="yellow",
            box=box.ROUNDED,
        )
        self._console.print(panel)

    def _print_error_panel(self, title: str, errors: List[ErrorInfo], color: str) -> None:
        """Print an error panel for a specific execution path."""
        lines = []
        for err in errors[:10]:
            time_str = f"{err.duration_ms / 1000:.1f}s" if err.duration_ms >= 1000 else f"{err.duration_ms:.0f}ms"
            # Extract error core
            error_core = self._extract_error_core(err.message)
            lines.append(f"  • [bold]{err.model_name}[/bold] ({time_str}): {error_core}")
        if len(errors) > 10:
            lines.append(f"  [dim]... and {len(errors) - 10} more[/dim]")

        content = "\n".join(lines)
        panel = Panel(
            content,
            title=f"[bold red]{title} ({len(errors)})[/bold red]",
            border_style="red",
            box=box.ROUNDED,
        )
        self._console.print(panel)

    def _extract_error_core(self, error_message: str, max_len: int = 100) -> str:
        """Extract the most useful part of an error message."""
        if not error_message:
            return "Unknown error"

        msg = error_message.strip()
        lines = msg.split('\n')

        # Filter Java stack traces
        filtered = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('at ') or line.startswith('... '):
                continue
            if 'org.apache.' in line or 'java.lang.' in line or 'scala.' in line:
                if ': ' in line:
                    filtered.append(line.split(': ', 1)[-1])
                continue
            filtered.append(line)

        result = ' | '.join(filtered[:2]) if filtered else msg[:max_len]
        if len(result) > max_len:
            result = result[:max_len] + "..."
        return result

    def _print_summary_fallback(self) -> None:
        """Print summary without Rich."""
        duration = self.stats.duration_seconds
        print(f"\n{'=' * 60}")
        print(f"  {self.title} Complete")
        print(f"  Passed: {self.stats.passed}  |  Failed: {self.stats.errored}  |  Skipped: {self.stats.skipped}")
        print(f"  Pushdown: {self.stats.pushdown_count}  |  Federation: {self.stats.federation_count}")
        print(f"  Duration: {duration:.1f}s")
        print(f"{'=' * 60}\n")


# =============================================================================
# Factory function
# =============================================================================

def create_dvt_display(
    operation: str = "run",
    target: str = "",
    compute: str = "",
) -> DVTMultiBarDisplay:
    """
    Factory function to create a DVT multi-bar display.

    Args:
        operation: Operation type (run, build, seed, profile, test, etc.)
        target: Target name
        compute: Compute engine name

    Returns:
        DVTMultiBarDisplay instance

    Usage:
        display = create_dvt_display(operation="run", target="postgres", compute="spark-local")
        display.initialize_models(nodes)
        display.start_display()
        for result in results:
            display.update_model_complete(...)
        display.stop_display()
        display.print_summary()
    """
    title_map = {
        "run": "DVT Run",
        "build": "DVT Build",
        "seed": "DVT Seed",
        "profile": "DVT Profile",
        "test": "DVT Test",
        "compile": "DVT Compile",
        "snapshot": "DVT Snapshot",
        "retract": "DVT Retract",
    }

    return DVTMultiBarDisplay(
        title=title_map.get(operation.lower(), f"DVT {operation.title()}"),
        operation=operation,
        target=target,
        compute=compute,
    )


# Alias for backwards compatibility in imports (but different class)
DVTProgressDisplay = DVTMultiBarDisplay
