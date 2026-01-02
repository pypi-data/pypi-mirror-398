"""
AWS EMR (Elastic MapReduce) Spark Connection Strategy

Provides connection to AWS EMR Spark clusters via YARN.

v0.5.98: New strategy for AWS EMR clusters with Maven-based JAR provisioning.

Configuration:
{
    "master": "yarn",                    # Required: YARN resource manager
    "spark.submit.deployMode": "client", # Optional: client or cluster
    "spark.driver.memory": "4g",         # Optional: driver memory
    "spark.executor.memory": "8g",       # Optional: executor memory
    "spark.executor.instances": "4",     # Optional: number of executors
}

Requirements:
- AWS EMR cluster must be running
- AWS credentials configured (aws configure or IAM role)
- Spark must be accessible from client machine (e.g., via SSH tunnel or VPN)

Cost Estimate:
- Typical 5-node EMR cluster: ~$1.20/hr (m5.xlarge instances)
- On-demand pricing varies by instance type and region
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


class EMRStrategy(BaseConnectionStrategy):
    """
    AWS EMR Spark cluster connection strategy.

    Connects to EMR clusters using YARN as the resource manager.
    Uses spark.jars.packages for JDBC JAR provisioning.
    """

    def validate_config(self) -> None:
        """
        Validate EMR strategy configuration.

        Required:
        - master: Must be "yarn" for EMR

        :raises DbtRuntimeError: If configuration is invalid
        """
        if not isinstance(self.config, dict):
            raise DbtRuntimeError(
                f"EMR config must be a dictionary, got {type(self.config)}"
            )

        # Check master is yarn
        master = self.config.get("master", "")
        if master.lower() != "yarn":
            raise DbtRuntimeError(
                f"EMR config requires master='yarn', got: {master}"
            )

    def get_spark_session(self, adapter_types: Optional[Set[str]] = None) -> SparkSession:
        """
        Create Spark session connected to EMR cluster via YARN.

        :param adapter_types: Set of adapter types that need JDBC drivers
        :returns: Initialized SparkSession connected to EMR
        :raises DbtRuntimeError: If session creation fails
        """
        if not PYSPARK_AVAILABLE:
            raise DbtRuntimeError("PySpark is not available. Install it with: pip install pyspark")

        try:
            builder = SparkSession.builder.appName(self.app_name)

            # Set YARN master
            builder = builder.master("yarn")

            # Get JDBC JAR config
            if adapter_types is None:
                from dbt.compute.jar_provisioning import get_required_adapter_types
                adapter_types = get_required_adapter_types()

            if adapter_types:
                jar_config = self.get_jar_provisioning_config(adapter_types)
                for key, value in jar_config.items():
                    builder = builder.config(key, value)

            # Apply user-provided configs
            for key, value in self.config.items():
                if key != "master":  # master already set
                    builder = builder.config(key, value)

            # Default EMR optimizations
            default_configs = {
                "spark.submit.deployMode": "client",
                "spark.dynamicAllocation.enabled": "true",
                "spark.sql.execution.arrow.pyspark.enabled": "true",
            }
            for key, value in default_configs.items():
                if key not in self.config:
                    builder = builder.config(key, value)

            # Create session
            spark = builder.getOrCreate()
            spark.sparkContext.setLogLevel("WARN")

            return spark

        except Exception as e:
            error_msg = str(e)
            if "Connection refused" in error_msg:
                raise DbtRuntimeError(
                    f"Cannot connect to EMR cluster. Ensure the cluster is running "
                    f"and accessible from this machine. Error: {error_msg}"
                ) from e
            raise DbtRuntimeError(f"Failed to create EMR Spark session: {error_msg}") from e

    def close(self, spark: Optional[SparkSession]) -> None:
        """
        Clean up Spark session.

        For EMR, we stop the application but the cluster continues running.

        :param spark: SparkSession to clean up
        """
        if spark:
            try:
                spark.stop()
            except Exception:
                pass  # Best effort cleanup

    def estimate_cost(self, duration_minutes: float) -> float:
        """
        Estimate cost for EMR execution.

        Based on typical 5-node EMR cluster with m5.xlarge instances.

        :param duration_minutes: Estimated query duration in minutes
        :returns: Estimated cost in USD
        """
        # Typical EMR cluster: 5x m5.xlarge @ ~$0.24/hr each = ~$1.20/hr total
        hourly_cost = 1.20
        hours = duration_minutes / 60.0
        return round(hourly_cost * hours, 2)

    def get_platform_name(self) -> str:
        """Get platform name."""
        return "emr"

    def get_jar_provisioning_config(self, adapter_types: Set[str]) -> Dict[str, str]:
        """
        Get Spark config for JDBC JAR provisioning using Maven coordinates.

        EMR clusters download JDBC drivers from Maven Central at session startup.

        :param adapter_types: Set of adapter types that need JDBC drivers
        :returns: Dictionary with spark.jars.packages config
        """
        from dbt.compute.jar_provisioning import RemoteJARProvisioning

        provisioning = RemoteJARProvisioning()
        return provisioning.get_spark_config(adapter_types)

    def test_connectivity(self) -> Tuple[bool, str]:
        """
        Test connectivity to EMR cluster.

        :returns: Tuple of (success, message)
        """
        if not PYSPARK_AVAILABLE:
            return (False, "PySpark not installed")

        try:
            spark = self.get_spark_session()
            spark.sql("SELECT 1 AS test").collect()
            return (True, "EMR session created and SQL test passed")
        except Exception as e:
            error_msg = str(e)
            if "Connection refused" in error_msg:
                return (False, "Cannot connect to EMR cluster (connection refused)")
            return (False, f"EMR connection failed: {e}")

    def get_cluster_info(self) -> Dict[str, Any]:
        """
        Get information about the EMR configuration.

        :returns: Dictionary with cluster metadata
        """
        return {
            "platform": "emr",
            "master": self.config.get("master", "yarn"),
            "deploy_mode": self.config.get("spark.submit.deployMode", "client"),
            "executor_instances": self.config.get("spark.executor.instances", "dynamic"),
        }
