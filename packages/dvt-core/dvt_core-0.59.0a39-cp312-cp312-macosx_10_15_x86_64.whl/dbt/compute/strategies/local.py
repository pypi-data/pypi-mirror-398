"""
Local Spark Connection Strategy

Provides embedded PySpark session for local development and testing.
This is the default strategy extracted from the original SparkEngine implementation.

Includes auto-configuration of Java with PySpark compatibility checking.

v0.51.3: Refactored to use java_compat module for centralized Java/PySpark compatibility.
v0.5.98: Added JAR provisioning using local file paths (spark.jars).
v0.58.5: Fixed Java 21 segfaults by NOT loading jdk.incubator.vector module.
"""

import os
from typing import Dict, Optional, Set, Tuple

from dbt.compute.strategies.base import BaseConnectionStrategy
from dbt_common.exceptions import DbtRuntimeError

try:
    from pyspark.sql import SparkSession

    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False
    SparkSession = None

# Global Spark session cache for reuse across calls (within same process)
_SPARK_SESSION_CACHE = {}

# Thread lock for safe session management
import threading
_SPARK_SESSION_LOCK = threading.Lock()


def cleanup_all_spark_sessions():
    """
    Clean up ALL cached Spark sessions.

    DVT v0.58.4: Call this at the end of runs to prevent semaphore leaks
    and segfaults when the thread pool terminates.

    Thread-safe - uses lock for cache access.
    """
    global _SPARK_SESSION_CACHE

    with _SPARK_SESSION_LOCK:
        for cache_key, spark in list(_SPARK_SESSION_CACHE.items()):
            try:
                spark.stop()
            except Exception:
                pass  # Best effort cleanup
        _SPARK_SESSION_CACHE.clear()


def _disable_multiprocessing_resource_tracker():
    """
    Disable Python's multiprocessing resource tracker to prevent segfaults.

    DVT v0.58.5: PySpark 4.0 + Java 21 creates semaphores that conflict with
    Python's resource tracker during shutdown, causing segfaults on macOS.
    Disabling the tracker prevents these conflicts.
    """
    import multiprocessing
    try:
        # Disable resource tracking for semaphores
        from multiprocessing import resource_tracker
        # Replace the tracker's main function with a no-op
        resource_tracker._resource_tracker = None
        resource_tracker._fd = None
    except Exception:
        pass  # Best effort - if it fails, continue anyway


def _ensure_java_available():
    """
    Ensure Java is available and compatible with installed PySpark.

    Uses the centralized java_compat module for cross-platform Java detection
    and PySpark compatibility checking.

    v0.51.3: Refactored to use java_compat module with enhanced compatibility checking.
             Always sets JAVA_HOME to a proper JDK path (not /usr or invalid paths).
    """
    from dbt.compute.java_compat import (
        get_pyspark_info,
        find_all_java_installations,
        select_best_java,
    )

    # Get PySpark requirements
    pyspark = get_pyspark_info()
    if not pyspark:
        raise DbtRuntimeError(
            "PySpark is not installed. Install it with: pip install pyspark\n"
            "Or run 'dvt spark set-version' to select a specific version."
        )

    # Always search for Java installations and select the best one
    # This ensures JAVA_HOME is set to a proper JDK path (not /usr or invalid)
    all_java = find_all_java_installations()
    best_java = select_best_java(all_java, pyspark.java_supported)

    if best_java:
        # Set JAVA_HOME to the best compatible Java found
        # This is needed even if Java is in PATH because PySpark's scripts
        # rely on JAVA_HOME being set to a proper JDK directory
        os.environ["JAVA_HOME"] = best_java.path
        bin_path = os.path.join(best_java.path, "bin")
        # Prepend to PATH to ensure this Java is used
        os.environ["PATH"] = bin_path + os.pathsep + os.environ.get("PATH", "")
        return

    # No compatible Java found - show error with guidance
    supported_str = ", ".join(str(v) for v in pyspark.java_supported)
    raise DbtRuntimeError(
        f"No compatible Java found for PySpark {pyspark.version}.\n"
        f"PySpark {pyspark.major_minor} requires Java {supported_str}.\n\n"
        f"Run 'dvt java search' to find Java installations.\n"
        f"Run 'dvt java set' to select a compatible version.\n"
        f"Run 'dvt java install' for installation guide."
    )


class LocalStrategy(BaseConnectionStrategy):
    """
    Local embedded Spark strategy.

    Creates an in-process PySpark session with local[*] master.
    Best for development, testing, and small-medium workloads.

    Configuration:
    {
        "master": "local[*]",  # optional, defaults to local[*]
        "spark.driver.memory": "4g",  # optional
        "spark.executor.memory": "4g",  # optional
        # ... any other Spark configs
    }
    """

    def validate_config(self) -> None:
        """
        Validate local strategy configuration.

        Local strategy is flexible - no required fields.
        """
        # Local strategy accepts any config - very flexible
        # Just ensure it's a dictionary
        if not isinstance(self.config, dict):
            raise DbtRuntimeError(
                f"Local Spark config must be a dictionary, got {type(self.config)}"
            )

    def get_spark_session(self, adapter_types: Optional[Set[str]] = None) -> SparkSession:
        """
        Create or reuse local Spark session (BLAZING FAST).

        Creates an embedded PySpark session with optimized configuration for speed.
        Implements session caching to reuse existing sessions.

        DVT v0.5.3: Uses direct JAR paths instead of spark.jars.packages to avoid
        verbose Ivy output. JARs are downloaded once and cached in ~/.dvt/jdbc_jars/

        :param adapter_types: Set of adapter types that need JDBC drivers (optional, for API compatibility)
        :returns: Initialized SparkSession
        :raises DbtRuntimeError: If session creation fails
        """
        import sys
        import hashlib

        if not PYSPARK_AVAILABLE:
            raise DbtRuntimeError("PySpark is not available. Install it with: pip install pyspark")

        # DVT v0.58.5: Disable resource tracker BEFORE any JVM operations
        # This prevents segfaults caused by semaphore cleanup conflicts
        _disable_multiprocessing_resource_tracker()

        # DVT v0.59.0a28: Remove _JAVA_OPTIONS to stop "Picked up" messages
        # JVM options are passed via spark.driver.extraJavaOptions instead
        # Only clear if we set it ourselves (check for our specific flags)
        _java_opts = os.environ.get("_JAVA_OPTIONS", "")
        if "-XX:-UseVectorCmov" in _java_opts:
            # We set this previously, clear it to avoid output noise
            os.environ.pop("_JAVA_OPTIONS", None)

        # Auto-configure Java first
        _ensure_java_available()

        # Create cache key from config to reuse sessions with same configuration
        config_str = str(sorted(self.config.items()))
        cache_key = hashlib.md5(config_str.encode()).hexdigest()

        # Thread-safe session management
        with _SPARK_SESSION_LOCK:
            # Check if we have a cached session with this config
            if cache_key in _SPARK_SESSION_CACHE:
                cached_spark = _SPARK_SESSION_CACHE[cache_key]
                # Verify session is still active
                try:
                    cached_spark.sparkContext.getConf()  # Will fail if session is dead
                    return cached_spark
                except Exception:
                    # Session died, remove from cache
                    del _SPARK_SESSION_CACHE[cache_key]

            # v0.51.0: Stop any existing session with DIFFERENT config
            # This ensures we get correct spark.jars.packages for this strategy
            try:
                existing = SparkSession.getActiveSession()
                if existing:
                    existing.stop()
                    # Clear the global cache too
                    _SPARK_SESSION_CACHE.clear()
            except Exception:
                pass

        # DVT v0.5.3: Suppress Java/Spark startup warnings completely
        # Create a custom log4j2 config to silence Spark startup noise
        import tempfile
        log4j_config = """
status = error
appender.console.type = Console
appender.console.name = console
appender.console.layout.type = PatternLayout
appender.console.layout.pattern = %msg%n
rootLogger.level = error
rootLogger.appenderRef.console.ref = console
logger.spark.name = org.apache.spark
logger.spark.level = error
logger.hadoop.name = org.apache.hadoop
logger.hadoop.level = error
"""
        log4j_file = os.path.join(tempfile.gettempdir(), "dvt_log4j2.properties")
        with open(log4j_file, "w") as f:
            f.write(log4j_config)

        # Use persistent JAR cache in project directory
        dvt_home = os.path.expanduser("~/.dvt")
        jar_cache_dir = os.path.join(dvt_home, "jdbc_jars")
        os.makedirs(jar_cache_dir, exist_ok=True)

        # DVT v0.5.3: Get cached JDBC jars (from project dir, not home dir)
        jar_paths = self._get_jdbc_jars(jar_cache_dir)

        builder = SparkSession.builder.appName(self.app_name)

        # Use local[2] instead of local[*] for faster startup
        master = self.config.get("master", "local[2]")
        builder = builder.master(master)

        # Optimized default configurations for SPEED
        fast_configs = {
            # Memory optimization
            "spark.driver.memory": "1g",
            "spark.executor.memory": "1g",

            # DVT v0.5.3: Use direct JAR paths (NO Ivy output!)
            "spark.jars": ",".join(jar_paths) if jar_paths else "",

            # DVT v0.58.5: Add JARs to classpath for JDBC driver loading
            "spark.driver.extraClassPath": ":".join(jar_paths) if jar_paths else "",
            "spark.executor.extraClassPath": ":".join(jar_paths) if jar_paths else "",

            # DVT v0.58.5: Java 21 compatibility flags for PySpark 4.0
            # Minimal JVM options - don't restrict modules (causes Spark failures)
            "spark.driver.extraJavaOptions": " ".join([
                f"-Dlog4j2.configurationFile=file:{log4j_file}",
                "-Djava.util.logging.level=SEVERE",
                # Java module system compatibility for Spark
                "--add-opens=java.base/java.lang=ALL-UNNAMED",
                "--add-opens=java.base/java.lang.invoke=ALL-UNNAMED",
                "--add-opens=java.base/java.lang.reflect=ALL-UNNAMED",
                "--add-opens=java.base/java.io=ALL-UNNAMED",
                "--add-opens=java.base/java.net=ALL-UNNAMED",
                "--add-opens=java.base/java.nio=ALL-UNNAMED",
                "--add-opens=java.base/java.util=ALL-UNNAMED",
                "--add-opens=java.base/java.util.concurrent=ALL-UNNAMED",
                "--add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED",
                "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED",
                "--add-opens=java.base/sun.nio.cs=ALL-UNNAMED",
                "--add-opens=java.base/sun.security.action=ALL-UNNAMED",
                "--add-opens=java.base/sun.util.calendar=ALL-UNNAMED",
                "--add-opens=java.security.jgss/sun.security.krb5=ALL-UNNAMED",
                "-XX:+IgnoreUnrecognizedVMOptions",
            ]),

            # Suppress Spark UI and progress
            "spark.ui.enabled": "false",
            "spark.ui.showConsoleProgress": "false",
            "spark.eventLog.enabled": "false",

            # Network optimizations
            "spark.driver.bindAddress": "127.0.0.1",
            "spark.driver.host": "localhost",

            # Reduce shuffle partitions for faster queries on small data
            "spark.sql.shuffle.partitions": "8",

            # DVT v0.58.4: Disable Arrow temporarily to avoid segfaults on macOS + Java 21
            # Arrow's native code can cause segfaults during Spark session creation
            "spark.sql.execution.arrow.pyspark.enabled": "false",
            "spark.sql.execution.arrow.pyspark.fallback.enabled": "true",
            "spark.sql.execution.arrow.enabled": "false",

            # Disable adaptive optimization (slow for small data)
            "spark.sql.adaptive.enabled": "false",
            "spark.sql.adaptive.coalescePartitions.enabled": "false",
        }

        # Apply fast configs (can be overridden by user config)
        for key, value in fast_configs.items():
            if key not in self.config:
                builder = builder.config(key, value)

        # Apply user-provided configs (except 'master' which is already set)
        for key, value in self.config.items():
            if key != "master":
                builder = builder.config(key, value)

        # DVT v0.59.0: Suppress Java/Spark startup noise completely
        # Java prints _JAVA_OPTIONS and module warnings to stderr before log4j2 loads
        # We capture and discard these during session creation
        import io
        import contextlib

        original_stderr = sys.stderr
        sys.stderr = io.StringIO()  # Capture stderr

        try:
            # Create Spark session
            spark = builder.getOrCreate()

            # Set log level to ERROR to suppress Spark warnings
            spark.sparkContext.setLogLevel("ERROR")
        finally:
            # Restore stderr
            captured = sys.stderr.getvalue()
            sys.stderr = original_stderr

            # Only print actual errors, not Java startup noise
            for line in captured.split('\n'):
                line = line.strip()
                if line and not any(skip in line for skip in [
                    'Picked up _JAVA_OPTIONS',
                    'Picked up JAVA_TOOL_OPTIONS',
                    'Using incubator modules',
                    'WARNING:',
                    'log4j:',
                    'SLF4J:',
                ]):
                    print(line, file=sys.stderr)

        # Cache the session for reuse (thread-safe)
        with _SPARK_SESSION_LOCK:
            _SPARK_SESSION_CACHE[cache_key] = spark

        return spark

    def _get_jdbc_jars(self, cache_dir: str) -> list:
        """
        Discover ALL JDBC JAR files from project cache at runtime.

        v0.5.96: Dynamic discovery - finds all *.jar files in .dvt/jdbc_jars/
        This enables project folder portability (move folder → JARs still work).

        JARs are downloaded via 'dvt target sync' command.

        :param cache_dir: Directory to look for JAR files (ignored, uses project dir)
        :returns: List of JAR file absolute paths
        """
        import glob

        # Look for JARs in project directory (current working directory)
        project_dir = os.getcwd()
        jar_cache_dir = os.path.join(project_dir, ".dvt", "jdbc_jars")

        # Discover ALL *.jar files dynamically (not hardcoded list)
        jar_pattern = os.path.join(jar_cache_dir, "*.jar")
        jar_paths = sorted(glob.glob(jar_pattern))

        # No warning needed - clean output
        # User should run 'dvt target sync' if JARs needed

        return jar_paths

    def close(self, spark: Optional[SparkSession]) -> None:
        """
        Close Spark session after execution.

        By default, closes the session to free resources and prevent blocking other models.
        Session caching can be enabled by setting DVT_SPARK_KEEP_ALIVE=1 for faster
        consecutive runs within the same Python process.

        Set DVT_SPARK_KEEP_ALIVE=1 environment variable to keep sessions alive (advanced).

        :param spark: SparkSession to close (or optionally keep alive)
        """
        import os

        # Check if caching is enabled (opt-in, not default)
        keep_alive = os.environ.get("DVT_SPARK_KEEP_ALIVE", "0") == "1"

        if keep_alive:
            # DVT v0.4.8: Suppressed verbose output
            # Session stays alive in cache for reuse (opt-in)
            # print("[DVT] Spark session kept alive in cache (DVT_SPARK_KEEP_ALIVE=1)", flush=True)
            pass
        elif spark:
            try:
                # Clear from cache first (thread-safe)
                with _SPARK_SESSION_LOCK:
                    for key, cached_spark in list(_SPARK_SESSION_CACHE.items()):
                        if cached_spark is spark:
                            del _SPARK_SESSION_CACHE[key]
                            break

                # Stop the session
                spark.stop()
                # DVT v0.4.8: Suppressed verbose output
                # print("[DVT] ✓ Spark session closed", flush=True)
            except Exception:
                pass  # Best effort cleanup

    def estimate_cost(self, duration_minutes: float) -> float:
        """
        Estimate cost for local execution.

        Local execution is free (runs on local machine).

        :param duration_minutes: Estimated query duration
        :returns: 0.0 (free)
        """
        return 0.0

    def get_platform_name(self) -> str:
        """Get platform name."""
        return "local"

    def get_jar_provisioning_config(self, adapter_types: Set[str]) -> Dict[str, str]:
        """
        Get Spark config for JDBC JAR provisioning using local file paths.

        Local Spark uses spark.jars with local file paths from .dvt/jdbc_jars/
        for instant startup (no download at runtime).

        :param adapter_types: Set of adapter types (ignored - uses all JARs found)
        :returns: Dictionary with spark.jars config
        """
        from dbt.compute.jar_provisioning import LocalJARProvisioning

        provisioning = LocalJARProvisioning(project_dir=os.getcwd())
        return provisioning.get_spark_config(adapter_types)

    def test_connectivity(self) -> Tuple[bool, str]:
        """
        Test connectivity by creating a local Spark session.

        :returns: Tuple of (success, message)
        """
        # Check PySpark at runtime (not module import time)
        try:
            from pyspark.sql import SparkSession as _  # noqa: F401
        except ImportError:
            return (False, "PySpark not installed")

        try:
            spark = self.get_spark_session()
            # Run simple SQL to verify
            spark.sql("SELECT 1 AS test").collect()
            return (True, "Local Spark session created and SQL test passed")
        except Exception as e:
            return (False, f"Local Spark failed: {e}")
