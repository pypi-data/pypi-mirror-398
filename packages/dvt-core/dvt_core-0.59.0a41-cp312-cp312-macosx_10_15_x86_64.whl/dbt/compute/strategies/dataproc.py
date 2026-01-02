"""
GCP Dataproc Spark Connection Strategy

Provides connection to Google Cloud Dataproc Spark clusters.

v0.5.98: New strategy for GCP Dataproc clusters with Maven-based JAR provisioning.

Configuration:
{
    "project": "my-gcp-project",         # Required: GCP project ID
    "region": "us-central1",             # Required: Dataproc region
    "cluster": "my-dataproc-cluster",    # Required: Cluster name
    "spark.driver.memory": "4g",         # Optional: driver memory
    "spark.executor.memory": "8g",       # Optional: executor memory
}

Requirements:
- GCP Dataproc cluster must be running
- gcloud SDK configured (gcloud auth login)
- Dataproc connector or direct YARN access

Cost Estimate:
- Typical 5-node Dataproc cluster: ~$1.00/hr (n1-standard-4 instances)
- Dataproc pricing includes Spark/Hadoop runtime at no extra cost
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


class DataprocStrategy(BaseConnectionStrategy):
    """
    GCP Dataproc Spark cluster connection strategy.

    Connects to Dataproc clusters using YARN as the resource manager.
    Uses spark.jars.packages for JDBC JAR provisioning.
    """

    def validate_config(self) -> None:
        """
        Validate Dataproc strategy configuration.

        Required:
        - project: GCP project ID
        - region: Dataproc region
        - cluster: Cluster name

        :raises DbtRuntimeError: If configuration is invalid
        """
        if not isinstance(self.config, dict):
            raise DbtRuntimeError(
                f"Dataproc config must be a dictionary, got {type(self.config)}"
            )

        # Check required fields
        required_fields = ["project", "region", "cluster"]
        missing = [f for f in required_fields if f not in self.config]
        if missing:
            raise DbtRuntimeError(
                f"Dataproc config missing required fields: {', '.join(missing)}"
            )

    def get_spark_session(self, adapter_types: Optional[Set[str]] = None) -> SparkSession:
        """
        Create Spark session connected to Dataproc cluster.

        :param adapter_types: Set of adapter types that need JDBC drivers
        :returns: Initialized SparkSession connected to Dataproc
        :raises DbtRuntimeError: If session creation fails
        """
        if not PYSPARK_AVAILABLE:
            raise DbtRuntimeError("PySpark is not available. Install it with: pip install pyspark")

        try:
            builder = SparkSession.builder.appName(self.app_name)

            # Set YARN master for Dataproc
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
                if key not in ("project", "region", "cluster"):
                    builder = builder.config(key, value)

            # Default Dataproc optimizations
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
                    f"Cannot connect to Dataproc cluster '{self.config.get('cluster')}'. "
                    f"Ensure the cluster is running. Error: {error_msg}"
                ) from e
            raise DbtRuntimeError(f"Failed to create Dataproc Spark session: {error_msg}") from e

    def close(self, spark: Optional[SparkSession]) -> None:
        """
        Clean up Spark session.

        For Dataproc, we stop the application but the cluster continues running.

        :param spark: SparkSession to clean up
        """
        if spark:
            try:
                spark.stop()
            except Exception:
                pass  # Best effort cleanup

    def estimate_cost(self, duration_minutes: float) -> float:
        """
        Estimate cost for Dataproc execution.

        Based on typical 5-node Dataproc cluster with n1-standard-4 instances.

        :param duration_minutes: Estimated query duration in minutes
        :returns: Estimated cost in USD
        """
        # Typical Dataproc cluster: 5x n1-standard-4 @ ~$0.19/hr each = ~$0.95/hr total
        # Plus Dataproc fee: $0.01/vCPU/hr = ~$0.20/hr for 20 vCPUs
        hourly_cost = 1.15
        hours = duration_minutes / 60.0
        return round(hourly_cost * hours, 2)

    def get_platform_name(self) -> str:
        """Get platform name."""
        return "dataproc"

    def get_jar_provisioning_config(self, adapter_types: Set[str]) -> Dict[str, str]:
        """
        Get Spark config for JDBC JAR provisioning using Maven coordinates.

        Dataproc clusters download JDBC drivers from Maven Central at session startup.

        :param adapter_types: Set of adapter types that need JDBC drivers
        :returns: Dictionary with spark.jars.packages config
        """
        from dbt.compute.jar_provisioning import RemoteJARProvisioning

        provisioning = RemoteJARProvisioning()
        return provisioning.get_spark_config(adapter_types)

    def test_connectivity(self) -> Tuple[bool, str]:
        """
        Test connectivity to Dataproc cluster.

        :returns: Tuple of (success, message)
        """
        if not PYSPARK_AVAILABLE:
            return (False, "PySpark not installed")

        try:
            spark = self.get_spark_session()
            spark.sql("SELECT 1 AS test").collect()
            return (True, "Dataproc session created and SQL test passed")
        except Exception as e:
            error_msg = str(e)
            if "Connection refused" in error_msg:
                return (False, "Cannot connect to Dataproc cluster (connection refused)")
            return (False, f"Dataproc connection failed: {e}")

    def get_cluster_info(self) -> Dict[str, Any]:
        """
        Get information about the Dataproc configuration.

        :returns: Dictionary with cluster metadata
        """
        return {
            "platform": "dataproc",
            "project": self.config.get("project", "unknown"),
            "region": self.config.get("region", "unknown"),
            "cluster": self.config.get("cluster", "unknown"),
        }
