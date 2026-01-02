"""
JAR Provisioning Module

Centralized JDBC JAR provisioning for Spark compute engines.

v0.5.98: Supports two provisioning strategies:
- LocalJARProvisioning: Uses spark.jars with local file paths (fast startup)
- RemoteJARProvisioning: Uses spark.jars.packages with Maven coordinates (remote clusters)

Local Spark uses local JARs from .dvt/jdbc_jars/ for instant startup.
Remote clusters (Databricks, EMR, Dataproc, Standalone) use Maven coordinates
so Spark workers can download JARs directly from Maven Central.
"""

import glob
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Set


# Maven coordinates for JDBC drivers - used by remote clusters
# Format: groupId:artifactId:version
# These are the same JARs as downloaded by `dvt target sync`, but expressed as Maven coordinates
JDBC_MAVEN_COORDINATES = {
    # Official dbt-labs adapters - JDBC drivers only
    "postgres": "org.postgresql:postgresql:42.7.4",
    "snowflake": "net.snowflake:snowflake-jdbc:3.16.1",
    "bigquery": "com.google.cloud.bigdataoss:gcs-connector:hadoop3-2.2.22",
    "redshift": "com.amazon.redshift:redshift-jdbc42:2.1.0.32",
    "spark": "",  # Native, no JDBC needed
    "databricks": "com.databricks:databricks-jdbc:2.6.36",
    "trino": "io.trino:trino-jdbc:443",
    "duckdb": "org.duckdb:duckdb_jdbc:1.1.3",
    # Community adapters - JDBC drivers only (verified on Maven)
    "mysql": "com.mysql:mysql-connector-j:9.1.0",
    "sqlserver": "com.microsoft.sqlserver:mssql-jdbc:12.8.1.jre11",
    "synapse": "com.microsoft.sqlserver:mssql-jdbc:12.8.1.jre11",
    "fabric": "com.microsoft.sqlserver:mssql-jdbc:12.8.1.jre11",
    "oracle": "com.oracle.database.jdbc:ojdbc11:23.6.0.24.10",
    "teradata": "com.teradata.jdbc:terajdbc:20.00.00.20",
    "clickhouse": "com.clickhouse:clickhouse-jdbc:0.6.5",
    "greenplum": "org.postgresql:postgresql:42.7.4",  # PostgreSQL compatible
    "vertica": "com.vertica.jdbc:vertica-jdbc:24.3.0-0",
    "sqlite": "org.xerial:sqlite-jdbc:3.47.1.0",
    "mariadb": "org.mariadb.jdbc:mariadb-java-client:3.4.1",
    "exasol": "com.exasol:exasol-jdbc:24.2.0",
    "db2": "com.ibm.db2:jcc:11.5.9.0",
    "presto": "io.prestosql:presto-jdbc:350",
    "hive": "org.apache.hive:hive-jdbc:3.1.3",
    "singlestore": "com.singlestore:singlestore-jdbc-client:1.2.9",
    "starrocks": "com.mysql:mysql-connector-j:9.1.0",  # MySQL wire protocol
    "doris": "com.mysql:mysql-connector-j:9.1.0",  # MySQL wire protocol
    "materialize": "org.postgresql:postgresql:42.7.4",  # PostgreSQL wire protocol
    "neo4j": "org.neo4j:neo4j-jdbc-driver:4.0.10",
    "timescaledb": "org.postgresql:postgresql:42.7.4",  # PostgreSQL extension
    "questdb": "org.postgresql:postgresql:42.7.4",  # PostgreSQL wire protocol
}


class JARProvisioning(ABC):
    """Abstract base class for JAR provisioning strategies."""

    @abstractmethod
    def get_spark_config(self, adapter_types: Set[str]) -> Dict[str, str]:
        """
        Get Spark configuration for JDBC JARs.

        :param adapter_types: Set of adapter types that need JDBC drivers
        :returns: Dictionary of Spark config keys/values
        """
        pass

    @abstractmethod
    def get_provisioning_type(self) -> str:
        """
        Get the type of JAR provisioning.

        :returns: 'local' or 'maven'
        """
        pass


class LocalJARProvisioning(JARProvisioning):
    """
    Local JAR provisioning using spark.jars with local file paths.

    Best for local Spark (spark-local) where JARs are pre-downloaded
    to .dvt/jdbc_jars/ directory via `dvt target sync`.

    Advantages:
    - Instant startup (no JAR download at runtime)
    - Works offline
    - Consistent JAR versions

    Disadvantages:
    - Only works for local Spark (JARs must be on local filesystem)
    - Requires running `dvt target sync` first
    """

    def __init__(self, project_dir: Optional[str] = None):
        """
        Initialize local JAR provisioning.

        :param project_dir: Path to project root directory (defaults to cwd)
        """
        self.project_dir = project_dir or os.getcwd()
        self.jdbc_jars_dir = os.path.join(self.project_dir, ".dvt", "jdbc_jars")

    def get_jar_paths(self) -> List[str]:
        """
        Discover all JDBC JAR files from project cache.

        :returns: List of absolute JAR file paths
        """
        if not os.path.exists(self.jdbc_jars_dir):
            return []

        jar_pattern = os.path.join(self.jdbc_jars_dir, "*.jar")
        return sorted(glob.glob(jar_pattern))

    def get_spark_config(self, adapter_types: Set[str]) -> Dict[str, str]:
        """
        Get Spark config using local JAR paths.

        :param adapter_types: Set of adapter types (ignored - uses all JARs found)
        :returns: Dictionary with spark.jars config
        """
        jar_paths = self.get_jar_paths()

        if jar_paths:
            return {"spark.jars": ",".join(jar_paths)}
        return {}

    def get_provisioning_type(self) -> str:
        """Get provisioning type."""
        return "local"


class RemoteJARProvisioning(JARProvisioning):
    """
    Remote JAR provisioning using spark.jars.packages with Maven coordinates.

    Best for remote Spark clusters (Databricks, EMR, Dataproc, Standalone)
    where Spark workers need to download JARs from Maven Central.

    Advantages:
    - Works with any remote Spark cluster
    - No need to pre-install JARs on cluster
    - Spark handles dependency resolution

    Disadvantages:
    - Requires network access to Maven Central
    - First query may be slower (JAR download)
    - May need to configure Maven repositories for private JARs
    """

    def __init__(self, profiles_dir: Optional[str] = None):
        """
        Initialize remote JAR provisioning.

        :param profiles_dir: Path to DVT profiles directory (for scanning profiles.yml)
        """
        self.profiles_dir = profiles_dir or str(Path.home() / ".dvt")

    def get_maven_coordinates(self, adapter_types: Set[str]) -> List[str]:
        """
        Get Maven coordinates for the specified adapter types.

        :param adapter_types: Set of adapter types
        :returns: List of Maven coordinates (group:artifact:version)
        """
        coordinates = []
        seen = set()  # Avoid duplicates (e.g., postgres and timescaledb both use postgresql)

        for adapter_type in adapter_types:
            coord = JDBC_MAVEN_COORDINATES.get(adapter_type.lower(), "")
            if coord and coord not in seen:
                coordinates.append(coord)
                seen.add(coord)

        return sorted(coordinates)

    def get_spark_config(self, adapter_types: Set[str]) -> Dict[str, str]:
        """
        Get Spark config using Maven coordinates.

        :param adapter_types: Set of adapter types that need JDBC drivers
        :returns: Dictionary with spark.jars.packages config
        """
        coordinates = self.get_maven_coordinates(adapter_types)

        if coordinates:
            return {"spark.jars.packages": ",".join(coordinates)}
        return {}

    def get_provisioning_type(self) -> str:
        """Get provisioning type."""
        return "maven"


def get_required_adapter_types(
    profiles_dir: Optional[str] = None,
    project_dir: Optional[str] = None,
) -> Set[str]:
    """
    Scan profiles.yml and return the set of adapter types needed.

    v0.59.0a18: Project-aware - only scans current project's profile,
    not all profiles in profiles.yml.

    :param profiles_dir: Path to DVT profiles directory
    :param project_dir: Path to project directory (for profile detection)
    :returns: Set of adapter type names (e.g., {'postgres', 'snowflake'})
    """
    from dbt.clients.yaml_helper import load_yaml_text
    from dbt.config.project_utils import get_project_profile_name

    if profiles_dir is None:
        profiles_dir = str(Path.home() / ".dvt")

    if project_dir is None:
        project_dir = os.getcwd()

    profiles_path = Path(profiles_dir) / "profiles.yml"
    if not profiles_path.exists():
        return set()

    try:
        content = profiles_path.read_text()
        profiles = load_yaml_text(content) or {}

        # v0.59.0a18: Get current project's profile (project-aware)
        current_profile = get_project_profile_name(Path(project_dir))

        adapter_types = set()

        if current_profile and current_profile in profiles:
            # Only scan the current project's profile
            profile_data = profiles[current_profile]
            if isinstance(profile_data, dict):
                outputs = profile_data.get("outputs", {})
                for target_name, target_config in outputs.items():
                    if isinstance(target_config, dict):
                        adapter_type = target_config.get("type")
                        if adapter_type:
                            adapter_types.add(adapter_type.lower())
        # Note: If no project found, return empty set (don't scan all profiles)

        return adapter_types

    except Exception:
        return set()


def get_provisioning_for_platform(
    platform: str,
    project_dir: Optional[str] = None,
    profiles_dir: Optional[str] = None,
) -> JARProvisioning:
    """
    Factory function to get the appropriate JAR provisioning strategy.

    :param platform: Spark platform ('local', 'databricks', 'emr', 'dataproc', 'standalone')
    :param project_dir: Project directory (for local provisioning)
    :param profiles_dir: Profiles directory (for remote provisioning)
    :returns: JARProvisioning instance
    """
    if platform.lower() == "local":
        return LocalJARProvisioning(project_dir=project_dir)
    else:
        # All remote platforms use Maven coordinates
        return RemoteJARProvisioning(profiles_dir=profiles_dir)
