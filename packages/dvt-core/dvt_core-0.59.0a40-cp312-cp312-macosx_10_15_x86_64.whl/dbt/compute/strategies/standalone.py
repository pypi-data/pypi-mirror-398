"""
Standalone Spark Cluster Connection Strategy

Provides connection to self-managed Spark clusters (on-premises or cloud VMs).

v0.5.98: New strategy for standalone Spark clusters with Maven-based JAR provisioning.
         Fixes the bug where external clusters incorrectly fell back to LocalStrategy
         with local JAR paths that don't exist on remote workers.

Configuration:
{
    "master": "spark://master-node:7077",  # Required: Spark master URL
    "spark.driver.memory": "4g",           # Optional: driver memory
    "spark.executor.memory": "8g",         # Optional: executor memory
    "spark.executor.cores": "4",           # Optional: cores per executor
    "spark.executor.instances": "10",      # Optional: number of executors
}

Requirements:
- Standalone Spark cluster must be running
- Spark master must be accessible from client machine
- Workers must have network access to Maven Central (for JAR downloads)
"""

from typing import Any, Dict, Optional, Set, Tuple

from dbt.compute.strategies.base import BaseConnectionStrategy
from dbt_common.exceptions import DbtRuntimeError

try:
    from pyspark.sql import SparkSession

    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False
    SparkSession = None


class StandaloneStrategy(BaseConnectionStrategy):
    """
    Standalone Spark cluster connection strategy.

    Connects to self-managed Spark clusters using spark:// master URL.
    Uses spark.jars.packages for JDBC JAR provisioning so workers can
    download drivers from Maven Central.
    """

    def validate_config(self) -> None:
        """
        Validate Standalone strategy configuration.

        Required:
        - master: Must start with "spark://" for standalone clusters

        :raises DbtRuntimeError: If configuration is invalid
        """
        if not isinstance(self.config, dict):
            raise DbtRuntimeError(
                f"Standalone config must be a dictionary, got {type(self.config)}"
            )

        # Check master format
        master = self.config.get("master", "")
        if not master.startswith("spark://"):
            raise DbtRuntimeError(
                f"Standalone config requires master to start with 'spark://', got: {master}"
            )

    def get_spark_session(self, adapter_types: Optional[Set[str]] = None) -> SparkSession:
        """
        Create Spark session connected to standalone cluster.

        :param adapter_types: Set of adapter types that need JDBC drivers
        :returns: Initialized SparkSession connected to standalone cluster
        :raises DbtRuntimeError: If session creation fails
        """
        if not PYSPARK_AVAILABLE:
            raise DbtRuntimeError("PySpark is not available. Install it with: pip install pyspark")

        try:
            # v0.51.0: Ensure Java is available
            from dbt.compute.strategies.local import _ensure_java_available
            _ensure_java_available()

            # v0.51.0: Stop any existing session to ensure fresh config
            existing = SparkSession.getActiveSession()
            if existing:
                existing.stop()

            builder = SparkSession.builder.appName(self.app_name)

            # Set master URL
            master = self.config.get("master")
            builder = builder.master(master)

            # v0.5.99: Get JDBC JAR config (Maven coordinates for remote workers)
            # Merge with user-provided spark.jars.packages instead of overwriting
            if adapter_types is None:
                from dbt.compute.jar_provisioning import get_required_adapter_types
                adapter_types = get_required_adapter_types()

            auto_packages = []
            if adapter_types:
                jar_config = self.get_jar_provisioning_config(adapter_types)
                auto_packages_str = jar_config.get("spark.jars.packages", "")
                if auto_packages_str:
                    auto_packages = [p.strip() for p in auto_packages_str.split(",") if p.strip()]

            # Get user-provided packages from config
            user_packages_str = self.config.get("spark.jars.packages", "")
            user_packages = [p.strip() for p in user_packages_str.split(",") if p.strip()]

            # Merge packages (user + auto-detected)
            all_packages = list(set(user_packages + auto_packages))
            if all_packages:
                builder = builder.config("spark.jars.packages", ",".join(all_packages))

            # Apply user-provided configs (except spark.jars.packages which we merged)
            for key, value in self.config.items():
                if key != "master" and key != "spark.jars.packages":
                    builder = builder.config(key, value)

            # Default optimizations
            default_configs = {
                "spark.sql.execution.arrow.pyspark.enabled": "true",
                "spark.sql.execution.arrow.pyspark.fallback.enabled": "true",
            }
            for key, value in default_configs.items():
                if key not in self.config:
                    builder = builder.config(key, value)

            # DVT v0.51.5: Auto-configure driver host for Docker Spark clusters
            # When master is on localhost, workers (in Docker containers) need to reach
            # the driver running on the host machine via host.docker.internal
            if "spark.driver.host" not in self.config:
                if "localhost" in master or "127.0.0.1" in master:
                    builder = builder.config("spark.driver.host", "host.docker.internal")

            # Create session
            spark = builder.getOrCreate()
            spark.sparkContext.setLogLevel("WARN")

            return spark

        except Exception as e:
            error_msg = str(e)
            master = self.config.get("master", "unknown")
            if "Connection refused" in error_msg:
                raise DbtRuntimeError(
                    f"Cannot connect to Spark master at '{master}'. "
                    f"Ensure the cluster is running and accessible. Error: {error_msg}"
                ) from e
            raise DbtRuntimeError(f"Failed to create Standalone Spark session: {error_msg}") from e

    def close(self, spark: Optional[SparkSession]) -> None:
        """
        Clean up Spark session.

        For standalone clusters, we stop the application but the cluster continues running.

        :param spark: SparkSession to clean up
        """
        if spark:
            try:
                spark.stop()
            except Exception:
                pass  # Best effort cleanup

    def estimate_cost(self, duration_minutes: float) -> float:
        """
        Estimate cost for standalone cluster execution.

        For self-managed clusters, returns 0.0 as cost depends on infrastructure.

        :param duration_minutes: Estimated query duration in minutes
        :returns: 0.0 (infrastructure cost varies)
        """
        # Self-managed clusters have variable cost based on infrastructure
        return 0.0

    def get_platform_name(self) -> str:
        """Get platform name."""
        return "standalone"

    def get_jar_provisioning_config(self, adapter_types: Set[str]) -> Dict[str, str]:
        """
        Get Spark config for JDBC JAR provisioning using Maven coordinates.

        Standalone clusters need spark.jars.packages so workers can download
        JDBC drivers from Maven Central. Local file paths don't work because
        they're not available on remote worker nodes.

        :param adapter_types: Set of adapter types that need JDBC drivers
        :returns: Dictionary with spark.jars.packages config
        """
        from dbt.compute.jar_provisioning import RemoteJARProvisioning

        provisioning = RemoteJARProvisioning()
        return provisioning.get_spark_config(adapter_types)

    def test_connectivity(self) -> Tuple[bool, str]:
        """
        Test connectivity to standalone Spark cluster.

        v0.51.1: Added timeout to prevent hanging when workers unavailable.
        v0.51.8: Increased timeout to 90s for Docker clusters (JDBC JAR download time).

        :returns: Tuple of (success, message)
        """
        if not PYSPARK_AVAILABLE:
            return (False, "PySpark not installed")

        import concurrent.futures

        master = self.config.get("master", "unknown")

        def _run_test():
            spark = self.get_spark_session()
            spark.sql("SELECT 1 AS test").collect()
            return True

        try:
            # Use ThreadPoolExecutor with timeout to prevent hanging
            # when workers aren't available
            # v0.51.8: Increased from 30s to 90s - Docker Spark clusters need time
            # for JDBC JAR downloads from Maven on first run
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_run_test)
                try:
                    result = future.result(timeout=90)  # 90 second timeout for JAR downloads
                    return (True, "Standalone cluster session created and SQL test passed")
                except concurrent.futures.TimeoutError:
                    return (False,
                        f"Timeout (90s): Workers not responding at '{master}'.\n"
                        f"Check: cluster workers are running, network access from driver to workers.\n"
                        f"Note: First run may take longer due to JDBC JAR downloads."
                    )

        except Exception as e:
            error_msg = str(e)
            if "Connection refused" in error_msg:
                return (False, f"Cannot connect to Spark master at '{master}'")
            if "Initial job has not accepted any resources" in error_msg:
                return (False,
                    f"Workers not accepting tasks at '{master}'.\n"
                    f"Check: spark.driver.host is set correctly for your network topology"
                )
            return (False, f"Standalone connection failed: {e}")

    def get_cluster_info(self) -> Dict[str, Any]:
        """
        Get information about the standalone cluster configuration.

        :returns: Dictionary with cluster metadata
        """
        return {
            "platform": "standalone",
            "master": self.config.get("master", "unknown"),
            "executor_instances": self.config.get("spark.executor.instances", "dynamic"),
            "executor_memory": self.config.get("spark.executor.memory", "default"),
            "executor_cores": self.config.get("spark.executor.cores", "default"),
        }
