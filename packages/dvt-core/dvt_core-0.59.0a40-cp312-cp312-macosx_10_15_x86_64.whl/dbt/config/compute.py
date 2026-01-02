"""
Compute Cluster Registry

Manages external compute cluster configurations for DVT.

v0.55.0: Computes stored in <project>/.dvt/computes.yml (project-level)
         Managed exclusively via `dvt compute` CLI commands.
         Contains comprehensive commented samples for all platforms.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dbt_common.exceptions import DbtRuntimeError


def get_project_dvt_dir(project_dir) -> Path:
    """Get the DVT config directory for a project (<project>/.dvt/).

    :param project_dir: Path to project root directory (str or Path)
    """
    return Path(project_dir) / ".dvt"


class SparkPlatform(Enum):
    """Spark platform types for connection strategies.

    v0.51.2: Removed DATABRICKS (serverless cannot read external JDBC sources).
    """

    LOCAL = "local"
    EMR = "emr"
    DATAPROC = "dataproc"
    STANDALONE = "standalone"  # Self-managed Spark clusters (spark://)
    EXTERNAL = "external"  # Generic external cluster (fallback)


# Default computes.yml template with comprehensive commented samples
DEFAULT_COMPUTES_YAML = """# ============================================================================
# DVT Compute Engines Configuration (v0.5.98)
# ============================================================================
# This file defines Spark compute engines for federated query execution.
#
# Commands:
#   dvt compute test      Test connectivity to all compute engines
#   dvt compute edit      Open this file in your editor
#   dvt compute validate  Validate YAML syntax
#
# JDBC JAR Provisioning (v0.5.98):
#   - Local Spark: Uses spark.jars with local file paths (fast startup)
#   - Remote clusters: Uses spark.jars.packages with Maven coordinates
#     (workers download JARs from Maven Central at session start)
#
# Platform Detection:
#   DVT auto-detects the platform from config keys:
#   - Dataproc: project + region + cluster
#   - EMR: master=yarn (without Dataproc keys)
#   - Standalone: master=spark://...
#   - Local: master=local[*] or no master
# ============================================================================

# Default compute engine (must match a name in 'computes' section)
target_compute: spark-local

# ============================================================================
# COMPUTE ENGINES
# ============================================================================
# Each compute engine must have:
#   - type: 'spark' (currently the only supported type)
#   - config: Spark configuration options
#   - description: (optional) Human-readable description
# ============================================================================

computes:

  # --------------------------------------------------------------------------
  # LOCAL SPARK (Default - Works out of the box)
  # --------------------------------------------------------------------------
  # Embedded PySpark for development and small-medium datasets.
  # Uses spark.jars with local file paths for fast startup.
  # JDBC JARs are auto-discovered from profiles.yml connections.
  #
  # Cost: Free (runs on your local machine)
  # Best for: Development, testing, datasets < 10GB
  # --------------------------------------------------------------------------
  spark-local:
    type: spark
    description: "Local Spark for development and testing"
    config:
      master: "local[2]"                    # Use 2 CPU cores (local[*] for all)
      spark.driver.memory: "2g"             # Driver memory
      spark.executor.memory: "2g"           # Executor memory
      spark.ui.enabled: "false"             # Disable Spark UI
      spark.ui.showConsoleProgress: "false" # No progress bars
      # Spark 4.0 legacy compatibility flags
      spark.sql.legacy.postgres.datetimeMapping.enabled: "true"
      spark.sql.legacy.mysql.timestampNTZMapping.enabled: "true"
      spark.sql.legacy.oracle.timestampMapping.enabled: "true"
      spark.sql.legacy.mssqlserver.numericMapping.enabled: "true"
      # Performance optimizations
      spark.sql.shuffle.partitions: "8"
      spark.sql.execution.arrow.pyspark.enabled: "true"
      spark.sql.execution.arrow.pyspark.fallback.enabled: "true"
      spark.sql.adaptive.enabled: "true"
      spark.sql.adaptive.coalescePartitions.enabled: "true"

  # --------------------------------------------------------------------------
  # AWS EMR (Elastic MapReduce)
  # --------------------------------------------------------------------------
  # Connects to AWS EMR clusters via YARN.
  # JDBC drivers are provisioned via spark.jars.packages (Maven).
  #
  # Requirements:
  #   - AWS credentials configured (aws configure or IAM role)
  #   - EMR cluster must be running
  #   - Network access to EMR master node
  #
  # Cost: ~$1.20/hr (typical 5-node m5.xlarge cluster)
  # Best for: AWS-native workloads, S3 data integration
  # --------------------------------------------------------------------------
  # emr-cluster:
  #   type: spark
  #   description: "AWS EMR Spark Cluster"
  #   config:
  #     master: "yarn"                      # Required: YARN resource manager
  #     spark.submit.deployMode: "client"   # Client mode for interactive
  #     spark.driver.memory: "4g"
  #     spark.executor.memory: "8g"
  #     spark.executor.instances: "4"
  #     spark.dynamicAllocation.enabled: "true"

  # --------------------------------------------------------------------------
  # GCP DATAPROC (Google Cloud Spark)
  # --------------------------------------------------------------------------
  # Connects to GCP Dataproc clusters via YARN.
  # JDBC drivers are provisioned via spark.jars.packages (Maven).
  #
  # Requirements:
  #   - gcloud SDK configured (gcloud auth login)
  #   - Dataproc cluster must be running
  #   - Network access to Dataproc master
  #
  # Cost: ~$1.15/hr (typical 5-node n1-standard-4 cluster)
  # Best for: GCP-native workloads, BigQuery/GCS integration
  # --------------------------------------------------------------------------
  # dataproc-cluster:
  #   type: spark
  #   description: "GCP Dataproc Cluster"
  #   config:
  #     project: "my-gcp-project"           # Required: GCP project ID
  #     region: "us-central1"               # Required: Dataproc region
  #     cluster: "my-dataproc-cluster"      # Required: Cluster name
  #     spark.driver.memory: "4g"
  #     spark.executor.memory: "8g"
  #     spark.dynamicAllocation.enabled: "true"

  # --------------------------------------------------------------------------
  # STANDALONE SPARK CLUSTER
  # --------------------------------------------------------------------------
  # Connects to self-managed Spark clusters (on-premises or cloud VMs).
  # JDBC drivers are provisioned via spark.jars.packages (Maven).
  # Workers download JARs from Maven Central at session start.
  #
  # Requirements:
  #   - Spark master accessible at spark://host:port
  #   - Workers must have network access to Maven Central
  #
  # Cost: Infrastructure-dependent (your own hardware/VMs)
  # Best for: On-premises deployments, custom Spark configurations
  # --------------------------------------------------------------------------
  # spark-cluster:
  #   type: spark
  #   description: "Standalone Spark Cluster"
  #   config:
  #     master: "spark://master-node:7077"  # Required: Spark master URL
  #     spark.driver.memory: "4g"
  #     spark.executor.memory: "8g"
  #     spark.executor.cores: "4"
  #     spark.executor.instances: "10"

  # --------------------------------------------------------------------------
  # HIGH-MEMORY LOCAL SPARK
  # --------------------------------------------------------------------------
  # For larger local workloads (requires more system RAM).
  # Same JAR provisioning as spark-local (local file paths).
  #
  # Cost: Free (runs on your local machine)
  # Best for: Larger datasets on powerful workstations
  # --------------------------------------------------------------------------
  # spark-local-large:
  #   type: spark
  #   description: "High-memory local Spark for large datasets"
  #   config:
  #     master: "local[*]"                  # Use all available cores
  #     spark.driver.memory: "8g"
  #     spark.executor.memory: "8g"
  #     spark.sql.shuffle.partitions: "200"
  #     spark.sql.adaptive.enabled: "true"
  #     spark.sql.adaptive.coalescePartitions.enabled: "true"
  #     spark.sql.adaptive.skewJoin.enabled: "true"
  #     spark.memory.fraction: "0.8"
  #     spark.memory.storageFraction: "0.3"

# ============================================================================
# CONFIGURATION REFERENCE
# ============================================================================
# Common Spark configurations:
#
# Memory:
#   spark.driver.memory: "4g"          # Driver memory (default 1g)
#   spark.executor.memory: "4g"        # Executor memory (default 1g)
#   spark.memory.fraction: "0.6"       # Fraction for execution/storage
#
# Parallelism:
#   spark.executor.cores: "4"          # Cores per executor
#   spark.executor.instances: "4"      # Number of executors
#   spark.sql.shuffle.partitions: "200"  # Shuffle partitions
#   spark.default.parallelism: "100"   # Default parallelism
#
# Arrow (PyArrow integration):
#   spark.sql.execution.arrow.pyspark.enabled: "true"
#   spark.sql.execution.arrow.maxRecordsPerBatch: "10000"
#
# Adaptive Query Execution (Spark 3.0+):
#   spark.sql.adaptive.enabled: "true"
#   spark.sql.adaptive.coalescePartitions.enabled: "true"
#   spark.sql.adaptive.skewJoin.enabled: "true"
#
# JDBC JAR Provisioning (v0.5.98):
#   Local Spark:
#     - Uses spark.jars with local file paths
#     - Fast startup (no download needed)
#     - JARs auto-discovered from profiles.yml
#
#   Remote Clusters (EMR, Dataproc, Standalone):
#     - Uses spark.jars.packages with Maven coordinates
#     - Workers download JARs at session start
#     - Supported databases: PostgreSQL, MySQL, Oracle, SQL Server,
#       Snowflake, Redshift, BigQuery, Teradata, DB2, and 30+ more
# ============================================================================
"""


@dataclass
class ComputeCluster:
    """Configuration for an external compute cluster."""

    name: str  # Cluster identifier
    type: str  # 'spark' (currently only Spark supported for external)
    config: Dict[str, Any] = field(default_factory=dict)  # Cluster-specific config
    description: Optional[str] = None
    cost_per_hour: Optional[float] = None  # Estimated cost per hour (USD)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        result = {
            "type": self.type,
            "config": self.config,
        }
        if self.description:
            result["description"] = self.description
        if self.cost_per_hour is not None:
            result["cost_per_hour"] = self.cost_per_hour
        return result

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "ComputeCluster":
        """Deserialize from dictionary."""
        return cls(
            name=name,
            type=data.get("type", "spark"),
            config=data.get("config", {}),
            description=data.get("description"),
            cost_per_hour=data.get("cost_per_hour"),
        )

    def detect_platform(self) -> SparkPlatform:
        """
        Detect Spark platform from configuration keys.

        v0.51.2: Removed Databricks support.
        Detection order (most specific first):
        1. Dataproc: project + region + cluster
        2. EMR: master=yarn (without Dataproc keys)
        3. Standalone: master=spark://
        4. Local: master=local[*] or no master
        5. External: fallback for unknown configurations

        :returns: SparkPlatform enum value
        """
        if self.type != "spark":
            return SparkPlatform.EXTERNAL

        config_keys = set(self.config.keys())

        # 1. Dataproc: has project, region, and cluster
        if all(k in config_keys for k in ["project", "region", "cluster"]):
            return SparkPlatform.DATAPROC

        # Check master value for remaining platforms
        if "master" in config_keys:
            master = str(self.config["master"]).lower()

            # 2. EMR: master=yarn (without Dataproc keys)
            if master == "yarn":
                return SparkPlatform.EMR

            # 3. Standalone: master=spark://
            if master.startswith("spark://"):
                return SparkPlatform.STANDALONE

            # 4. Local: master=local[*]
            if master.startswith("local"):
                return SparkPlatform.LOCAL

            # 5. External: unknown master format
            return SparkPlatform.EXTERNAL

        # Default to local (no master specified)
        return SparkPlatform.LOCAL


class ComputeRegistry:
    """
    Registry for managing external compute clusters.

    v0.55.0: Clusters stored in <project>/.dvt/computes.yml (project-level)
             Managed exclusively via `dvt compute` CLI commands.
    """

    def __init__(self, project_dir=None):
        """
        Initialize compute registry.

        :param project_dir: Path to project root directory (str or Path)
        """
        self.project_dir = str(project_dir) if project_dir else os.getcwd()

        # v0.55.0: Project-level paths
        self.project_dvt_dir = get_project_dvt_dir(self.project_dir)
        self.compute_file = self.project_dvt_dir / "computes.yml"
        self.jdbc_jars_dir = self.project_dvt_dir / "jdbc_jars"

        self._clusters: Dict[str, ComputeCluster] = {}
        self._target_compute: Optional[str] = None
        self._load()

    def _load(self) -> None:
        """Load clusters from storage.

        v0.55.0: Only project-level <project>/.dvt/computes.yml is supported.
        """
        # Load from project-level YAML file if it exists
        if self.compute_file.exists():
            self._load_from_yaml()
            return

        # No file exists - load defaults (will be saved when ensure_config_exists is called)
        self._load_defaults()

    def _load_from_yaml(self) -> None:
        """Load clusters from YAML file."""
        try:
            with open(self.compute_file, "r") as f:
                data = yaml.safe_load(f)

            if not data:
                self._load_defaults()
                return

            # Parse target_compute (default compute engine)
            self._target_compute = data.get("target_compute", "spark-local")

            # Parse computes
            computes_data = data.get("computes", {})
            for name, cluster_data in computes_data.items():
                if cluster_data:  # Skip None/empty entries
                    cluster = ComputeCluster.from_dict(name, cluster_data)
                    self._clusters[cluster.name] = cluster

            # If no computes defined, use defaults
            if not self._clusters:
                self._load_defaults()

        except Exception as e:
            raise DbtRuntimeError(f"Failed to load compute registry: {str(e)}") from e

    def _load_defaults(self) -> None:
        """Load default out-of-box compute engines."""
        data = yaml.safe_load(DEFAULT_COMPUTES_YAML)

        self._target_compute = data.get("target_compute", "spark-local")

        computes_data = data.get("computes", {})
        for name, cluster_data in computes_data.items():
            if cluster_data:  # Skip None entries (commented out samples)
                cluster = ComputeCluster.from_dict(name, cluster_data)
                self._clusters[cluster.name] = cluster

    def _save(self) -> None:
        """Save clusters to YAML file at project-level."""
        # Ensure project .dvt directory exists
        self.project_dvt_dir.mkdir(parents=True, exist_ok=True)

        # Build the YAML content with active computes
        computes_dict = {}
        for cluster in self._clusters.values():
            computes_dict[cluster.name] = cluster.to_dict()

        # If file exists, try to preserve comments by updating only the active section
        # For simplicity, we'll write the full template with active computes
        yaml_content = f"""# ============================================================================
# DVT Compute Engines Configuration
# ============================================================================
# This file defines Spark compute engines for federated query execution.
# Edit with: dvt compute edit
# Validate with: dvt compute validate
# Test with: dvt compute test
# ============================================================================

# Default compute engine (must match a name in 'computes' section)
target_compute: {self._target_compute or 'spark-local'}

computes:
"""
        # Add active computes
        for name, cluster in self._clusters.items():
            yaml_content += f"\n  {name}:\n"
            yaml_content += f"    type: {cluster.type}\n"
            if cluster.description:
                yaml_content += f'    description: "{cluster.description}"\n'
            yaml_content += "    config:\n"
            for key, value in cluster.config.items():
                yaml_content += f'      {key}: "{value}"\n'

        with open(self.compute_file, "w") as f:
            f.write(yaml_content)

    def get_config_path(self) -> Path:
        """Get the path to the computes.yml file."""
        return self.compute_file

    def ensure_config_exists(self) -> Path:
        """Ensure the config file exists at project-level and return its path."""
        if not self.compute_file.exists():
            self._load_defaults()
            # Write full template with samples to project-level
            self.project_dvt_dir.mkdir(parents=True, exist_ok=True)
            with open(self.compute_file, "w") as f:
                f.write(DEFAULT_COMPUTES_YAML)
        return self.compute_file

    @property
    def target_compute(self) -> str:
        """Get the default target compute engine."""
        return self._target_compute or "spark-local"

    @target_compute.setter
    def target_compute(self, value: str) -> None:
        """Set the default target compute engine."""
        if value not in self._clusters:
            raise DbtRuntimeError(
                f"Cannot set target_compute to '{value}': compute engine not found. "
                f"Available engines: {', '.join(self._clusters.keys())}"
            )
        self._target_compute = value
        self._save()

    def get(self, name: str) -> Optional[ComputeCluster]:
        """
        Get a compute cluster by name.

        :param name: Cluster name
        :returns: ComputeCluster or None if not found
        """
        return self._clusters.get(name)

    def list(self) -> List[ComputeCluster]:
        """
        List all registered clusters.

        :returns: List of ComputeCluster objects
        """
        return list(self._clusters.values())

    def exists(self, name: str) -> bool:
        """
        Check if a cluster exists.

        :param name: Cluster name
        :returns: True if cluster exists
        """
        return name in self._clusters

    @staticmethod
    def ensure_jdbc_jars_dir(project_dir: str) -> Path:
        """
        Ensure the project-level .dvt/jdbc_jars/ directory exists.

        :param project_dir: Path to project root directory
        :returns: Path to the jdbc_jars directory
        """
        jdbc_jars_dir = get_project_dvt_dir(project_dir) / "jdbc_jars"
        jdbc_jars_dir.mkdir(parents=True, exist_ok=True)
        return jdbc_jars_dir

    def get_jdbc_jars_dir(self) -> Path:
        """Get the project-level jdbc_jars directory path."""
        return self.jdbc_jars_dir
