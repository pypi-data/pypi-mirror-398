"""
Target Sync Task

Handles DVT target synchronization:
- Scans profiles.yml connections to detect required adapter types
- Reports connections found and their types
- Shows adapter install instructions (manual pip/uv install)
- Resolves JDBC JARs with transitive dependencies via Maven POM
- Downloads all JARs to project .dvt/jdbc_jars/ directory
- Configures spark.jars to use pre-downloaded JARs (no Spark download at runtime)
- Removes unused adapters and JARs (with --clean flag)

v0.5.91: Smart sync based on profiles.yml connections
v0.5.93: Actual JDBC JAR download to project directory
v0.5.94: Show install instructions instead of auto-installing adapters
v0.5.95: Hybrid JAR resolution - DVT downloads with transitive deps, spark.jars config
"""

import os
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from dbt.config.compute import ComputeRegistry
from dbt_common.exceptions import DbtRuntimeError


def get_dvt_dir() -> Path:
    """Get the DVT configuration directory (~/.dvt/)."""
    dvt_dir = Path.home() / ".dvt"
    dvt_dir.mkdir(parents=True, exist_ok=True)
    return dvt_dir


# Maven repository URL
MAVEN_REPO = "https://repo1.maven.org/maven2"


# Mapping of adapter type to dbt adapter package name
ADAPTER_PACKAGE_MAPPING = {
    "postgres": "dbt-postgres",
    "snowflake": "dbt-snowflake",
    "bigquery": "dbt-bigquery",
    "redshift": "dbt-redshift",
    "spark": "dbt-spark",
    "databricks": "dbt-databricks",
    "trino": "dbt-trino",
    "duckdb": "dbt-duckdb",
    "mysql": "dbt-mysql",
    "sqlserver": "dbt-sqlserver",
    "synapse": "dbt-synapse",
    "fabric": "dbt-fabric",
    "oracle": "dbt-oracle",
    "teradata": "dbt-teradata",
    "clickhouse": "dbt-clickhouse",
    "greenplum": "dbt-greenplum",
    "vertica": "dbt-vertica",
    "sqlite": "dbt-sqlite",
    "mariadb": "dbt-mysql",  # Uses MySQL adapter
    "exasol": "dbt-exasol",
    "db2": "dbt-db2",
    "athena": "dbt-athena-community",
    "presto": "dbt-presto",
    "hive": "dbt-hive",
    "impala": "dbt-impala",
    "singlestore": "dbt-singlestore",
    "firebolt": "dbt-firebolt",
    "starrocks": "dbt-starrocks",
    "doris": "dbt-doris",
    "materialize": "dbt-materialize",
    "rockset": "dbt-rockset",
    "questdb": "dbt-questdb",
    "neo4j": "dbt-neo4j",
    "timescaledb": "dbt-postgres",  # Uses PostgreSQL adapter
}

# Mapping of adapter type to JDBC Maven coordinates (ONE JAR per adapter)
# These are pure JDBC drivers that Spark uses for spark.read.jdbc()
# NOTE: All versions verified against Maven Central as of Dec 2025
ADAPTER_JDBC_MAPPING = {
    # Official dbt-labs adapters - JDBC drivers only
    "postgres": "org.postgresql:postgresql:42.7.4",
    "snowflake": "net.snowflake:snowflake-jdbc:3.16.1",
    "bigquery": "com.google.cloud.bigdataoss:gcs-connector:hadoop3-2.2.22",  # GCS connector for BQ
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
    # Adapters without Maven JDBC drivers (require manual JAR download):
    # athena, impala, firebolt, rockset - use respective vendor download pages
}


class TargetSyncTask:
    """Task for synchronizing adapters and JARs based on profiles.yml connections."""

    def __init__(
        self,
        project_dir: Optional[str] = None,
        profiles_dir: Optional[str] = None,
        profile_name: Optional[str] = None,
    ):
        """
        Initialize TargetSyncTask.

        :param project_dir: Path to project root directory
        :param profiles_dir: Path to profiles directory (defaults to ~/.dvt/)
        :param profile_name: Profile name to sync (defaults to project profile)
        """
        self.project_dir = project_dir or str(Path.cwd())
        self.profiles_dir = profiles_dir or str(get_dvt_dir())
        self.profile_name = profile_name
        self.compute_registry = ComputeRegistry(self.project_dir)

    def _get_profile_name(self) -> Optional[str]:
        """Get the profile name from project or explicit parameter."""
        if self.profile_name:
            return self.profile_name

        # Try to read from dvt_project.yml first (DVT), then dbt_project.yml (legacy)
        project_files = [
            Path(self.project_dir) / "dvt_project.yml",
            Path(self.project_dir) / "dbt_project.yml",
        ]

        for project_file in project_files:
            if project_file.exists():
                try:
                    from dbt.clients.yaml_helper import load_yaml_text

                    content = project_file.read_text()
                    data = load_yaml_text(content)
                    if data and "profile" in data:
                        return data["profile"]
                except Exception:
                    pass

        return None

    def _load_profiles(self) -> Dict:
        """Load profiles.yml and return the data."""
        profiles_path = Path(self.profiles_dir) / "profiles.yml"
        if not profiles_path.exists():
            raise DbtRuntimeError(
                f"profiles.yml not found at {profiles_path}\n"
                f"Create it with: dvt init <project_name>"
            )

        try:
            from dbt.clients.yaml_helper import load_yaml_text

            content = profiles_path.read_text()
            return load_yaml_text(content) or {}
        except Exception as e:
            raise DbtRuntimeError(f"Failed to load profiles.yml: {e}") from e

    def get_connections_info(self) -> Dict[str, Dict]:
        """
        Scan profiles.yml and return detailed info about connections.

        :returns: Dict mapping connection name to {type, profile}
        """
        profiles = self._load_profiles()
        connections = {}

        profile_name = self._get_profile_name()

        if profile_name and profile_name in profiles:
            # Scan only the specified profile
            profile_data = profiles[profile_name]
            outputs = profile_data.get("outputs", {})
            for target_name, target_config in outputs.items():
                adapter_type = target_config.get("type")
                if adapter_type:
                    connections[target_name] = {
                        "type": adapter_type,
                        "profile": profile_name,
                    }
        elif profile_name:
            # v0.59.0a18: Profile specified but not found - don't fall back to all profiles
            raise DbtRuntimeError(
                f"Profile '{profile_name}' not found in profiles.yml.\n"
                f"Available profiles: {list(profiles.keys())}\n"
                f"Create it with: dvt init"
            )
        # v0.59.0a18: No profile detected (not in a project) - return empty
        # Don't scan all profiles as that breaks multi-project setups

        return connections

    def get_required_adapter_types(self) -> Set[str]:
        """
        Scan profiles.yml and return the set of adapter types needed.

        :returns: Set of adapter type names (e.g., {'postgres', 'snowflake'})
        """
        connections = self.get_connections_info()
        return {info["type"] for info in connections.values()}

    def get_installed_adapters(self) -> Set[str]:
        """
        Detect which dbt adapters are currently installed.

        :returns: Set of installed adapter type names
        """
        import importlib.util

        installed = set()

        adapter_modules = {
            "postgres": "dbt.adapters.postgres",
            "snowflake": "dbt.adapters.snowflake",
            "bigquery": "dbt.adapters.bigquery",
            "redshift": "dbt.adapters.redshift",
            "spark": "dbt.adapters.spark",
            "databricks": "dbt.adapters.databricks",
            "trino": "dbt.adapters.trino",
            "duckdb": "dbt.adapters.duckdb",
            "mysql": "dbt.adapters.mysql",
            "sqlserver": "dbt.adapters.sqlserver",
            "synapse": "dbt.adapters.synapse",
            "fabric": "dbt.adapters.fabric",
            "oracle": "dbt.adapters.oracle",
            "teradata": "dbt.adapters.teradata",
            "clickhouse": "dbt.adapters.clickhouse",
            "greenplum": "dbt.adapters.greenplum",
            "vertica": "dbt.adapters.vertica",
            "sqlite": "dbt.adapters.sqlite",
            "mariadb": "dbt.adapters.mysql",  # Uses MySQL adapter
            "exasol": "dbt.adapters.exasol",
            "athena": "dbt.adapters.athena",
            "hive": "dbt.adapters.hive",
            "impala": "dbt.adapters.impala",
            "singlestore": "dbt.adapters.singlestore",
            "firebolt": "dbt.adapters.firebolt",
            "starrocks": "dbt.adapters.starrocks",
            "doris": "dbt.adapters.doris",
            "materialize": "dbt.adapters.materialize",
            "rockset": "dbt.adapters.rockset",
        }

        for adapter_type, module_name in adapter_modules.items():
            spec = importlib.util.find_spec(module_name)
            if spec is not None:
                installed.add(adapter_type)

        return installed

    def install_adapters(
        self, adapter_types: Set[str], verbose: bool = True
    ) -> Tuple[List[str], List[str]]:
        """
        Install dbt adapters for the given adapter types.

        :param adapter_types: Set of adapter type names to install
        :param verbose: Print progress messages
        :returns: Tuple of (installed packages, failed packages)
        """
        installed = []
        failed = []

        for adapter_type in adapter_types:
            package = ADAPTER_PACKAGE_MAPPING.get(adapter_type)
            if not package:
                if verbose:
                    print(f"    ⚠ Unknown adapter type: {adapter_type}")
                continue

            if verbose:
                print(f"    Installing {package}...")

            try:
                # Use pip to install the adapter
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package, "--quiet"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    installed.append(package)
                    if verbose:
                        print(f"      ✓ {package} installed")
                else:
                    failed.append(package)
                    if verbose:
                        print(f"      ✗ Failed to install {package}")
                        if result.stderr:
                            print(f"        {result.stderr[:200]}")
            except Exception as e:
                failed.append(package)
                if verbose:
                    print(f"      ✗ Error installing {package}: {e}")

        return installed, failed

    def uninstall_adapters(
        self, adapter_types: Set[str], verbose: bool = True
    ) -> Tuple[List[str], List[str]]:
        """
        Uninstall dbt adapters for the given adapter types.

        :param adapter_types: Set of adapter type names to uninstall
        :param verbose: Print progress messages
        :returns: Tuple of (uninstalled packages, failed packages)
        """
        uninstalled = []
        failed = []

        for adapter_type in adapter_types:
            package = ADAPTER_PACKAGE_MAPPING.get(adapter_type)
            if not package:
                continue

            if verbose:
                print(f"    Removing {package}...")

            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "uninstall", package, "-y", "--quiet"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    uninstalled.append(package)
                    if verbose:
                        print(f"      ✓ {package} removed")
                else:
                    failed.append(package)
                    if verbose:
                        print(f"      ✗ Failed to remove {package}")
            except Exception as e:
                failed.append(package)
                if verbose:
                    print(f"      ✗ Error removing {package}: {e}")

        return uninstalled, failed

    def _maven_coord_to_url(self, coord: str) -> Tuple[str, str]:
        """
        Convert Maven coordinate to download URL and JAR filename.

        :param coord: Maven coordinate (e.g., 'org.postgresql:postgresql:42.7.4')
        :returns: Tuple of (download_url, jar_filename)
        """
        parts = coord.split(":")
        if len(parts) < 3:
            raise ValueError(f"Invalid Maven coordinate: {coord}")

        group_id = parts[0]
        artifact_id = parts[1]
        version = parts[2]

        # Convert group.id to group/id path
        group_path = group_id.replace(".", "/")

        # Build URL
        jar_name = f"{artifact_id}-{version}.jar"
        url = f"{MAVEN_REPO}/{group_path}/{artifact_id}/{version}/{jar_name}"

        return url, jar_name

    def _resolve_transitive_deps(
        self, coord: str, resolved: Optional[Set[str]] = None, depth: int = 0
    ) -> Set[str]:
        """
        Resolve transitive dependencies for a Maven coordinate by parsing POM file.

        :param coord: Maven coordinate (e.g., 'org.postgresql:postgresql:42.7.4')
        :param resolved: Set of already resolved coordinates (to avoid cycles)
        :param depth: Current recursion depth (max 3 to avoid deep trees)
        :returns: Set of all coordinates (including transitive deps)
        """
        if resolved is None:
            resolved = set()

        # Parse coordinate
        parts = coord.split(":")
        if len(parts) < 3:
            return resolved

        group_id, artifact_id, version = parts[0], parts[1], parts[2]

        # Avoid cycles and limit depth
        if coord in resolved or depth > 3:
            return resolved

        resolved.add(coord)

        # Skip transitive resolution for known self-contained JDBC drivers
        # Most JDBC drivers bundle their dependencies or have minimal deps
        self_contained_drivers = {
            "postgresql", "snowflake-jdbc", "mysql-connector-j", "mssql-jdbc",
            "ojdbc11", "terajdbc", "clickhouse-jdbc", "sqlite-jdbc",
            "mariadb-java-client", "exasol-jdbc", "jcc", "trino-jdbc",
            "presto-jdbc", "duckdb_jdbc", "databricks-jdbc", "redshift-jdbc42",
            "singlestore-jdbc-client", "neo4j-jdbc-driver", "vertica-jdbc"
        }
        if artifact_id in self_contained_drivers:
            return resolved

        # Try to fetch and parse POM for transitive deps
        try:
            group_path = group_id.replace(".", "/")
            pom_url = f"{MAVEN_REPO}/{group_path}/{artifact_id}/{version}/{artifact_id}-{version}.pom"

            request = urllib.request.Request(
                pom_url,
                headers={"User-Agent": "DVT-Core/0.5.95"}
            )

            with urllib.request.urlopen(request, timeout=10) as response:
                pom_content = response.read().decode("utf-8")

            # Parse POM XML
            root = ET.fromstring(pom_content)
            ns = {"m": "http://maven.apache.org/POM/4.0.0"}

            # Find dependencies
            for dep in root.findall(".//m:dependency", ns):
                dep_group = dep.find("m:groupId", ns)
                dep_artifact = dep.find("m:artifactId", ns)
                dep_version = dep.find("m:version", ns)
                dep_scope = dep.find("m:scope", ns)
                dep_optional = dep.find("m:optional", ns)

                # Skip test, provided, and optional dependencies
                if dep_scope is not None and dep_scope.text in ("test", "provided"):
                    continue
                if dep_optional is not None and dep_optional.text == "true":
                    continue

                if dep_group is not None and dep_artifact is not None and dep_version is not None:
                    dep_coord = f"{dep_group.text}:{dep_artifact.text}:{dep_version.text}"
                    # Recursively resolve (limited depth)
                    self._resolve_transitive_deps(dep_coord, resolved, depth + 1)

        except Exception:
            # If POM parsing fails, just return current resolved set
            pass

        return resolved

    def _download_jar(self, url: str, dest_path: Path, verbose: bool = True) -> bool:
        """
        Download a JAR file from URL.

        :param url: URL to download from
        :param dest_path: Destination path
        :param verbose: Print progress messages
        :returns: True if successful
        """
        try:
            if verbose:
                print(f"      Downloading {dest_path.name}...")

            # Create request with user agent
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "DVT-Core/0.5.95"}
            )

            with urllib.request.urlopen(request, timeout=60) as response:
                with open(dest_path, "wb") as f:
                    f.write(response.read())

            if verbose:
                size_mb = dest_path.stat().st_size / (1024 * 1024)
                print(f"        ✓ Downloaded ({size_mb:.1f} MB)")
            return True

        except Exception as e:
            if verbose:
                print(f"        ✗ Failed: {e}")
            return False

    def download_jdbc_jars(
        self, adapter_types: Set[str], verbose: bool = True
    ) -> Tuple[List[str], List[str]]:
        """
        Download JDBC JARs to project .dvt/jdbc_jars/ directory.

        v0.5.95: Hybrid approach - resolves transitive dependencies via Maven POM,
        downloads all JARs to local cache, then uses spark.jars for fast startup.

        :param adapter_types: Set of adapter type names
        :param verbose: Print progress messages
        :returns: Tuple of (downloaded jars, failed jars)
        """
        # Ensure jdbc_jars directory exists
        jdbc_jars_dir = Path(self.project_dir) / ".dvt" / "jdbc_jars"
        jdbc_jars_dir.mkdir(parents=True, exist_ok=True)

        downloaded = []
        failed = []

        # Build list of required JAR coordinates (direct dependencies)
        direct_coords = set()
        for adapter_type in adapter_types:
            jars = ADAPTER_JDBC_MAPPING.get(adapter_type, "")
            if jars:
                for jar in jars.split(","):
                    jar = jar.strip()
                    if jar:
                        direct_coords.add(jar)

        if not direct_coords:
            if verbose:
                print("\n  No JDBC JARs needed for these adapters")
            return downloaded, failed

        if verbose:
            print(f"\n  Resolving JDBC dependencies...")
            print(f"    Direct dependencies: {len(direct_coords)}")

        # Resolve transitive dependencies for all direct coords
        all_coords = set()
        for coord in direct_coords:
            resolved = self._resolve_transitive_deps(coord)
            all_coords.update(resolved)

        if verbose:
            transitive_count = len(all_coords) - len(direct_coords)
            if transitive_count > 0:
                print(f"    Transitive dependencies: {transitive_count}")
            print(f"    Total JARs to download: {len(all_coords)}")
            print(f"\n  Downloading to {jdbc_jars_dir}/")

        for coord in sorted(all_coords):
            try:
                url, jar_name = self._maven_coord_to_url(coord)
                dest_path = jdbc_jars_dir / jar_name

                # Skip if already downloaded
                if dest_path.exists():
                    if verbose:
                        print(f"      {jar_name} (cached)")
                    downloaded.append(jar_name)
                    continue

                # Download the JAR
                if self._download_jar(url, dest_path, verbose):
                    downloaded.append(jar_name)
                else:
                    failed.append(jar_name)

            except ValueError as e:
                if verbose:
                    print(f"      ⚠ Skipping {coord}: {e}")
                continue
            except Exception as e:
                if verbose:
                    print(f"      ✗ Error with {coord}: {e}")
                failed.append(coord)

        return downloaded, failed

    def update_jdbc_jars(self, adapter_types: Set[str], verbose: bool = True) -> bool:
        """
        Report JDBC JAR status (JARs discovered at runtime by Spark).

        v0.5.96: No longer stores spark.jars in config - JARs are discovered at runtime.
        This enables project folder portability (move folder → JARs still work).

        The LocalStrategy._get_jdbc_jars() method discovers JARs from current project
        directory at runtime: <project>/.dvt/jdbc_jars/*.jar

        :param adapter_types: Set of adapter type names
        :param verbose: Print progress messages
        :returns: True if JARs found
        """
        # Get the jdbc_jars directory
        jdbc_jars_dir = Path(self.project_dir) / ".dvt" / "jdbc_jars"

        # Find all downloaded JAR files
        jar_paths = []
        if jdbc_jars_dir.exists():
            jar_paths = sorted(jdbc_jars_dir.glob("*.jar"))

        if verbose:
            if jar_paths:
                print(f"\n  JDBC JARs downloaded ({len(jar_paths)}):")
                for jar_path in jar_paths:
                    print(f"    - {jar_path.name}")
                print(f"\n  ✓ JARs stored in: {jdbc_jars_dir}")
                print("    (Spark discovers JARs at runtime - portable across folder moves)")
            else:
                print("\n  No JDBC JARs downloaded")

        # v0.5.96: Remove spark.jars from config if present (old absolute path config)
        # JARs are now discovered at runtime from project directory
        spark_local = self.compute_registry.get("spark-local")
        if spark_local:
            modified = False
            if "spark.jars" in spark_local.config:
                spark_local.config.pop("spark.jars", None)
                modified = True
            if "spark.jars.packages" in spark_local.config:
                spark_local.config.pop("spark.jars.packages", None)
                modified = True
            if modified:
                self.compute_registry._save()
                if verbose:
                    print("\n  ✓ Cleaned up old spark.jars config (now uses runtime discovery)")

        return bool(jar_paths)

    def sync(self, verbose: bool = True, clean: bool = False, dry_run: bool = False) -> bool:
        """
        Synchronize adapters and JARs based on profiles.yml.

        :param verbose: Print progress messages
        :param clean: If True, remove adapters not needed by profiles.yml
        :param dry_run: If True, only report what would be done without making changes
        :returns: True if sync successful
        """
        if verbose:
            print("\nDVT Target Sync")
            print("=" * 60)

        # Get connection info from profiles.yml
        try:
            connections = self.get_connections_info()
            required = self.get_required_adapter_types()
        except DbtRuntimeError as e:
            print(f"✗ Error: {e}")
            return False

        # Report connections found
        if verbose:
            profile_name = self._get_profile_name()
            if profile_name:
                print(f"Profile: {profile_name}")
            print(f"\nConnections found: {len(connections)}")
            print("-" * 40)

            # Group connections by type
            by_type: Dict[str, List[str]] = {}
            for conn_name, info in connections.items():
                adapter_type = info["type"]
                if adapter_type not in by_type:
                    by_type[adapter_type] = []
                by_type[adapter_type].append(conn_name)

            for adapter_type in sorted(by_type.keys()):
                conn_names = by_type[adapter_type]
                package = ADAPTER_PACKAGE_MAPPING.get(adapter_type, "unknown")
                print(f"\n  {adapter_type} ({len(conn_names)} connection(s)):")
                for conn_name in conn_names:
                    print(f"    - {conn_name}")
                print(f"    Package: {package}")

        if not required:
            print("\n⚠ No connections found in profiles.yml")
            print("  Add connections to ~/.dvt/profiles.yml first")
            return False

        # Get currently installed adapters
        installed = self.get_installed_adapters()

        # Determine what to install and uninstall
        to_install = required - installed
        to_uninstall = installed - required if clean else set()

        # Report what will be installed
        if verbose:
            print("\n" + "-" * 40)
            print("\nAdapter Status:")

            if to_install:
                print(f"\n  To install ({len(to_install)}):")
                for adapter_type in sorted(to_install):
                    package = ADAPTER_PACKAGE_MAPPING.get(adapter_type, "unknown")
                    print(f"    - {adapter_type}: pip install {package}")
            else:
                print("\n  ✓ All required adapters already installed")

            if to_uninstall:
                print(f"\n  To remove ({len(to_uninstall)}):")
                for adapter_type in sorted(to_uninstall):
                    package = ADAPTER_PACKAGE_MAPPING.get(adapter_type, "unknown")
                    print(f"    - {adapter_type}: pip uninstall {package}")

            # Report adapters installed but not used (if not cleaning)
            unused = installed - required
            if unused and not clean:
                print(f"\n  Installed but not used ({len(unused)}):")
                for adapter_type in sorted(unused):
                    package = ADAPTER_PACKAGE_MAPPING.get(adapter_type, "unknown")
                    print(f"    - {adapter_type} ({package})")
                print("    (use --clean to remove unused adapters)")

        # If dry run, stop here
        if dry_run:
            if verbose:
                print("\n" + "=" * 60)
                print("Dry run complete. No changes made.")
            return True

        # Show install instructions for missing adapters (don't auto-install)
        if to_install:
            if verbose:
                print(f"\n" + "-" * 40)
                print(f"\nMissing Adapters ({len(to_install)}):")
                print("  Install manually with pip or uv:\n")
                for adapter_type in sorted(to_install):
                    package = ADAPTER_PACKAGE_MAPPING.get(adapter_type, "unknown")
                    print(f"    pip install {package}")
                    print(f"    # or: uv pip install {package}\n")

        # Show uninstall instructions for unused adapters (only if clean=True)
        if to_uninstall:
            if verbose:
                print(f"\n" + "-" * 40)
                print(f"\nUnused Adapters ({len(to_uninstall)}):")
                print("  Uninstall manually with pip or uv:\n")
                for adapter_type in sorted(to_uninstall):
                    package = ADAPTER_PACKAGE_MAPPING.get(adapter_type, "unknown")
                    print(f"    pip uninstall {package}")
                    print(f"    # or: uv pip uninstall {package}\n")

        # Download JDBC JARs to project directory
        if verbose:
            print("\n" + "-" * 40)
            print("\nDownloading JDBC JARs...")
        downloaded_jars, failed_jars = self.download_jdbc_jars(required, verbose)
        if failed_jars and verbose:
            print(f"\n  ⚠ {len(failed_jars)} JAR(s) failed to download")

        # Update JDBC JARs config in spark-local
        if verbose:
            print("\n" + "-" * 40)
            print("\nUpdating JDBC configuration...")
        self.update_jdbc_jars(required, verbose)

        if verbose:
            print("\n" + "=" * 60)
            print("✓ Sync complete")
            print("\nYou can now run: dvt run")

        return True
