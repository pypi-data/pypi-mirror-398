"""
Base Connection Strategy for Spark Engines

Defines the abstract interface for different Spark connection strategies.
Uses composition over inheritance for flexible platform support.

v0.5.98: Added JAR provisioning and connectivity testing methods.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Set, Tuple

try:
    from pyspark.sql import SparkSession

    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False
    SparkSession = None


class BaseConnectionStrategy(ABC):
    """
    Abstract base class for Spark connection strategies.

    Different strategies implement different ways to connect to Spark:
    - LocalStrategy: Embedded PySpark (in-process)
    - DatabricksStrategy: Databricks Connect (remote cluster)
    - EMRStrategy: AWS EMR cluster
    - DataprocStrategy: GCP Dataproc
    - StandaloneStrategy: Self-managed Spark clusters
    """

    def __init__(self, config: Dict[str, Any], app_name: str = "DVT-Compute"):
        """
        Initialize connection strategy.

        :param config: Strategy-specific configuration
        :param app_name: Spark application name
        """
        self.config = config
        self.app_name = app_name

    @abstractmethod
    def get_spark_session(self) -> SparkSession:
        """
        Create and return a SparkSession.

        :returns: Initialized SparkSession
        :raises DbtRuntimeError: If session creation fails
        """
        pass

    @abstractmethod
    def validate_config(self) -> None:
        """
        Validate strategy-specific configuration.

        :raises DbtRuntimeError: If configuration is invalid
        """
        pass

    def estimate_cost(self, duration_minutes: float) -> float:
        """
        Estimate cost for running on this platform.

        Default implementation returns 0.0 (free). Override for cloud platforms.

        :param duration_minutes: Estimated query duration in minutes
        :returns: Estimated cost in USD
        """
        return 0.0

    @abstractmethod
    def close(self, spark: Optional[SparkSession]) -> None:
        """
        Clean up Spark session.

        :param spark: SparkSession to clean up (may be None)
        """
        pass

    def get_platform_name(self) -> str:
        """
        Get human-readable platform name.

        :returns: Platform name (e.g., "local", "databricks", "emr")
        """
        return self.__class__.__name__.replace("Strategy", "").lower()

    def get_jar_provisioning_config(self, adapter_types: Set[str]) -> Dict[str, str]:
        """
        Get Spark configuration for JDBC JAR provisioning.

        Default implementation returns empty dict. Override in subclasses
        to provide platform-specific JAR configuration.

        Local platforms use spark.jars (local file paths).
        Remote platforms use spark.jars.packages (Maven coordinates).

        :param adapter_types: Set of adapter types that need JDBC drivers
        :returns: Dictionary of Spark config keys/values (e.g., {"spark.jars": "..."})
        """
        return {}

    def test_connectivity(self) -> Tuple[bool, str]:
        """
        Test basic connectivity to the Spark cluster.

        Creates a session, runs a simple query, and returns status.
        Override for platform-specific connectivity testing.

        :returns: Tuple of (success, message)
        """
        try:
            spark = self.get_spark_session()
            # Run a simple SQL query to verify connectivity
            spark.sql("SELECT 1 AS test").collect()
            return (True, "Session created and SQL test passed")
        except Exception as e:
            return (False, str(e))

    def test_jdbc_connectivity(
        self,
        jdbc_url: str,
        properties: Dict[str, str],
        table_or_query: str = "(SELECT 1 AS test) AS t",
    ) -> Tuple[bool, str]:
        """
        Test JDBC connectivity through the Spark cluster.

        Creates a session and attempts to read from a JDBC source.
        This verifies that JDBC drivers are properly configured.

        :param jdbc_url: JDBC connection URL
        :param properties: JDBC connection properties (user, password, driver)
        :param table_or_query: Table name or SQL query wrapped in parentheses
        :returns: Tuple of (success, message)
        """
        try:
            spark = self.get_spark_session()

            # Attempt JDBC read
            df = (
                spark.read.format("jdbc")
                .option("url", jdbc_url)
                .option("dbtable", table_or_query)
                .options(**properties)
                .load()
            )

            # Force evaluation
            row_count = df.count()
            return (True, f"JDBC read successful ({row_count} rows)")
        except Exception as e:
            error_msg = str(e)
            # Provide helpful error messages for common issues
            if "ClassNotFoundException" in error_msg:
                return (False, f"JDBC driver not found: {error_msg}")
            elif "No suitable driver" in error_msg:
                return (False, f"JDBC driver not loaded: {error_msg}")
            elif "Authentication" in error_msg.lower() or "password" in error_msg.lower():
                return (False, f"Authentication failed: {error_msg}")
            else:
                return (False, f"JDBC test failed: {error_msg}")
