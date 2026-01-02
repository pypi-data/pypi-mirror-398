# =============================================================================
# DVT Spark Output Logger
# =============================================================================
# Captures Spark/compute output to log files for debugging while keeping
# console clean with progress bars.
#
# DVT v0.59.0a36: New module for Spark output capture
# =============================================================================

from __future__ import annotations

import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO


class TeeWriter:
    """
    A writer that writes to both the original stream and a log file.

    This allows us to capture Spark output to a log file while still
    passing it through (though in practice we suppress console output
    by using Rich's Live display which takes over the terminal).
    """

    def __init__(self, original: TextIO, log_file: TextIO, suppress_console: bool = True):
        self.original = original
        self.log_file = log_file
        self.suppress_console = suppress_console
        self._lock = threading.Lock()

    def write(self, data: str) -> int:
        """Write data to log file and optionally to original stream."""
        with self._lock:
            # Always write to log file
            try:
                self.log_file.write(data)
                self.log_file.flush()
            except Exception:
                pass  # Don't break if log file write fails

            # Write to original only if not suppressing console
            if not self.suppress_console:
                return self.original.write(data)

            return len(data)

    def flush(self) -> None:
        """Flush both streams."""
        with self._lock:
            try:
                self.log_file.flush()
            except Exception:
                pass
            if not self.suppress_console:
                self.original.flush()

    def fileno(self) -> int:
        """Return the file descriptor of the original stream."""
        return self.original.fileno()

    def isatty(self) -> bool:
        """Return whether the original stream is a tty."""
        return self.original.isatty()


class SparkOutputLogger:
    """
    Captures Spark/compute stderr and stdout to a log file.

    The log file is written to target/{compute_name}_log.txt and overwrites
    each time a new session starts. Each session is separated by a clear
    header with timestamp.

    Usage:
        logger = SparkOutputLogger.get_instance(target_dir="/path/to/target", compute_name="spark")
        logger.start_session()
        # ... Spark operations ...
        logger.end_session()

    The logger is a singleton per (target_dir, compute_name) combination.
    """

    _instances: dict[tuple[str, str], "SparkOutputLogger"] = {}
    _global_lock = threading.Lock()

    def __init__(self, target_dir: str, compute_name: str = "spark"):
        """
        Initialize the Spark output logger.

        Args:
            target_dir: Path to the dbt target directory
            compute_name: Name of the compute engine (used in log filename)
        """
        self.target_dir = Path(target_dir)
        self.compute_name = compute_name
        self.log_path = self.target_dir / f"{compute_name}_log.txt"
        self._log_file: Optional[TextIO] = None
        self._original_stderr: Optional[TextIO] = None
        self._original_stdout: Optional[TextIO] = None
        self._tee_stderr: Optional[TeeWriter] = None
        self._tee_stdout: Optional[TeeWriter] = None
        self._session_active = False
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls, target_dir: str, compute_name: str = "spark") -> "SparkOutputLogger":
        """
        Get or create a singleton instance for the given target_dir and compute_name.

        Args:
            target_dir: Path to the dbt target directory
            compute_name: Name of the compute engine

        Returns:
            SparkOutputLogger instance
        """
        key = (str(target_dir), compute_name)
        with cls._global_lock:
            if key not in cls._instances:
                cls._instances[key] = cls(target_dir, compute_name)
            return cls._instances[key]

    def start_session(self, suppress_console: bool = True) -> None:
        """
        Start a new logging session.

        This overwrites the previous log file and writes a session header.
        stderr and stdout are redirected to capture Spark output.

        Args:
            suppress_console: If True, suppress output to console (default: True)
        """
        with self._lock:
            if self._session_active:
                return  # Already active

            try:
                # Ensure target directory exists
                self.target_dir.mkdir(parents=True, exist_ok=True)

                # Open log file (overwrite mode)
                self._log_file = open(self.log_path, 'w', encoding='utf-8')

                # Write session header
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self._log_file.write("=" * 80 + "\n")
                self._log_file.write(f"  DVT {self.compute_name.upper()} LOG\n")
                self._log_file.write(f"  Session started: {timestamp}\n")
                self._log_file.write("=" * 80 + "\n\n")
                self._log_file.flush()

                # Save original streams
                self._original_stderr = sys.stderr
                self._original_stdout = sys.stdout

                # Create tee writers
                self._tee_stderr = TeeWriter(
                    self._original_stderr,
                    self._log_file,
                    suppress_console=suppress_console,
                )
                self._tee_stdout = TeeWriter(
                    self._original_stdout,
                    self._log_file,
                    suppress_console=suppress_console,
                )

                # Redirect stderr and stdout
                sys.stderr = self._tee_stderr  # type: ignore
                sys.stdout = self._tee_stdout  # type: ignore

                self._session_active = True

            except Exception as e:
                # Don't break the application if logging fails
                self._cleanup()
                # Optionally log the error
                try:
                    if self._original_stderr:
                        self._original_stderr.write(f"[DVT] Warning: Could not start Spark logging: {e}\n")
                except Exception:
                    pass

    def write_separator(self, label: str = "") -> None:
        """
        Write a separator line to the log file.

        Useful for marking different phases of Spark execution.

        Args:
            label: Optional label for the separator
        """
        with self._lock:
            if self._log_file:
                try:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    if label:
                        self._log_file.write(f"\n--- [{timestamp}] {label} ---\n\n")
                    else:
                        self._log_file.write(f"\n--- [{timestamp}] ---\n\n")
                    self._log_file.flush()
                except Exception:
                    pass

    def end_session(self) -> None:
        """
        End the logging session.

        Restores original stderr and stdout, closes the log file.
        """
        with self._lock:
            if not self._session_active:
                return

            try:
                # Write session footer
                if self._log_file:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self._log_file.write("\n")
                    self._log_file.write("=" * 80 + "\n")
                    self._log_file.write(f"  Session ended: {timestamp}\n")
                    self._log_file.write("=" * 80 + "\n")

            except Exception:
                pass

            self._cleanup()

    def _cleanup(self) -> None:
        """Restore original streams and close log file."""
        # Restore original streams
        if self._original_stderr:
            sys.stderr = self._original_stderr
            self._original_stderr = None

        if self._original_stdout:
            sys.stdout = self._original_stdout
            self._original_stdout = None

        # Close log file
        if self._log_file:
            try:
                self._log_file.close()
            except Exception:
                pass
            self._log_file = None

        self._tee_stderr = None
        self._tee_stdout = None
        self._session_active = False

    def __del__(self):
        """Ensure cleanup on deletion."""
        self._cleanup()


# Convenience function for getting the logger
def get_spark_logger(target_dir: str, compute_name: str = "spark") -> SparkOutputLogger:
    """
    Get a Spark output logger for the given target directory.

    Args:
        target_dir: Path to the dbt target directory
        compute_name: Name of the compute engine (default: "spark")

    Returns:
        SparkOutputLogger instance
    """
    return SparkOutputLogger.get_instance(target_dir, compute_name)
