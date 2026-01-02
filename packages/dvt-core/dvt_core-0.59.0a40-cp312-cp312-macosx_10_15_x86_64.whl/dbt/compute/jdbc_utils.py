"""
JDBC Utilities for Spark Engine

Provides utilities for converting dbt adapter credentials to JDBC configurations
and helpers for optimizing parallel reads via partitioning.

This module enables DVT to bypass memory bottlenecks by using Spark JDBC connectors
to read data directly from source databases into Spark workers (distributed).

Architecture:
- Maps adapter credentials → JDBC URL + properties
- Auto-detects optimal partition columns for parallel reads
- Estimates partition bounds for efficient data distribution
"""

from typing import Dict, Optional, Tuple

from dbt.adapters.base import BaseAdapter
from dbt.adapters.contracts.connection import Credentials
from dbt_common.exceptions import DbtRuntimeError


# JDBC driver class mapping for database types
# DVT v0.5.9: Complete support for all dbt adapters with JDBC connectivity
JDBC_DRIVER_MAPPING = {
    # ============================================================
    # Cloud Data Warehouses
    # ============================================================
    "postgres": "org.postgresql.Driver",
    "postgresql": "org.postgresql.Driver",
    "snowflake": "net.snowflake.client.jdbc.SnowflakeDriver",
    "bigquery": "com.simba.googlebigquery.jdbc.Driver",
    "redshift": "com.amazon.redshift.jdbc.Driver",
    "databricks": "com.databricks.client.jdbc.Driver",
    "firebolt": "com.firebolt.FireboltDriver",

    # ============================================================
    # Microsoft Ecosystem (all use same JDBC driver)
    # ============================================================
    "sqlserver": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
    "mssql": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
    "fabric": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
    "synapse": "com.microsoft.sqlserver.jdbc.SQLServerDriver",

    # ============================================================
    # Enterprise Data Warehouses
    # ============================================================
    "oracle": "oracle.jdbc.OracleDriver",
    "db2": "com.ibm.db2.jcc.DB2Driver",
    "teradata": "com.teradata.jdbc.TeraDriver",
    "exasol": "com.exasol.jdbc.EXADriver",
    "vertica": "com.vertica.jdbc.Driver",

    # ============================================================
    # SQL Engines & Query Platforms
    # ============================================================
    "spark": "org.apache.hive.jdbc.HiveDriver",
    "trino": "io.trino.jdbc.TrinoDriver",
    "presto": "io.prestosql.jdbc.PrestoDriver",
    "athena": "com.simba.athena.jdbc.Driver",
    "hive": "org.apache.hive.jdbc.HiveDriver",
    "impala": "com.cloudera.impala.jdbc.Driver",
    "dremio": "com.dremio.jdbc.Driver",
    "glue": "com.amazonaws.glue.sql.jdbc.Driver",

    # ============================================================
    # Open Source Databases
    # ============================================================
    "mysql": "com.mysql.cj.jdbc.Driver",
    "mariadb": "org.mariadb.jdbc.Driver",
    "sqlite": "org.sqlite.JDBC",
    "duckdb": "org.duckdb.DuckDBDriver",
    "cratedb": "io.crate.client.jdbc.CrateDriver",

    # ============================================================
    # OLAP & Analytics Databases
    # ============================================================
    "clickhouse": "com.clickhouse.jdbc.ClickHouseDriver",
    "singlestore": "com.singlestore.jdbc.Driver",
    "starrocks": "com.mysql.cj.jdbc.Driver",  # StarRocks uses MySQL protocol
    "doris": "com.mysql.cj.jdbc.Driver",  # Apache Doris uses MySQL protocol
    "greenplum": "org.postgresql.Driver",  # Greenplum uses PostgreSQL protocol
    "monetdb": "org.monetdb.jdbc.MonetDriver",

    # ============================================================
    # Time-Series & Streaming
    # ============================================================
    "timescaledb": "org.postgresql.Driver",  # TimescaleDB uses PostgreSQL
    "questdb": "org.postgresql.Driver",  # QuestDB supports PostgreSQL wire protocol
    "materialize": "org.postgresql.Driver",  # Materialize uses PostgreSQL wire protocol
    "rockset": "com.rockset.jdbc.RocksetDriver",

    # ============================================================
    # Graph & Multi-Model
    # ============================================================
    "neo4j": "org.neo4j.Driver",

    # ============================================================
    # Data Lake Formats (via Spark connectors)
    # ============================================================
    "delta": "org.apache.hive.jdbc.HiveDriver",  # Delta Lake via Spark
    "iceberg": "org.apache.hive.jdbc.HiveDriver",  # Apache Iceberg via Spark
    "hudi": "org.apache.hive.jdbc.HiveDriver",  # Apache Hudi via Spark

    # ============================================================
    # AlloyDB (Google - PostgreSQL compatible)
    # ============================================================
    "alloydb": "org.postgresql.Driver",  # AlloyDB is PostgreSQL-compatible
}


def _rewrite_localhost_for_docker(jdbc_url: str) -> str:
    """
    Rewrite localhost/127.0.0.1 to host.docker.internal for Docker Spark clusters.

    DVT v0.51.8: When using Docker-based Spark clusters, workers inside containers
    need host.docker.internal to reach the host machine. With host.docker.internal
    also added to the host's /etc/hosts (pointing to 127.0.0.1), the same JDBC URL
    works for both driver (on host) and workers (in containers).

    :param jdbc_url: Original JDBC URL
    :returns: JDBC URL with localhost replaced by host.docker.internal
    """
    import re
    # Replace localhost or 127.0.0.1 with host.docker.internal
    url = re.sub(r'//localhost([:/?])', r'//host.docker.internal\1', jdbc_url)
    url = re.sub(r'//127\.0\.0\.1([:/?])', r'//host.docker.internal\1', url)
    return url


# Global flag to enable Docker JDBC URL rewriting
_docker_mode_enabled = False


def set_docker_mode(enabled: bool) -> None:
    """Enable or disable Docker mode for JDBC URL rewriting."""
    global _docker_mode_enabled
    _docker_mode_enabled = enabled


def build_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """
    Build JDBC configuration from dbt adapter credentials.

    Converts adapter-specific credentials to JDBC URL and connection properties
    that can be used by Spark JDBC connectors.

    :param credentials: dbt adapter credentials object
    :returns: Tuple of (jdbc_url, jdbc_properties)
    :raises DbtRuntimeError: If adapter type is not supported or credentials are invalid

    Example:
        >>> from dbt.adapters.postgres import PostgresCredentials
        >>> creds = PostgresCredentials(
        ...     host="localhost",
        ...     port=5432,
        ...     user="analytics",
        ...     password="secret",
        ...     database="warehouse",
        ...     schema="public"
        ... )
        >>> url, props = build_jdbc_config(creds)
        >>> print(url)
        jdbc:postgresql://localhost:5432/warehouse
        >>> print(props)
        {'user': 'analytics', 'password': 'secret', 'driver': 'org.postgresql.Driver'}
    """
    adapter_type = credentials.type.lower()

    # Check if adapter type is supported
    if adapter_type not in JDBC_DRIVER_MAPPING:
        raise DbtRuntimeError(
            f"JDBC connectivity not supported for adapter type '{adapter_type}'. "
            f"Supported types: {', '.join(JDBC_DRIVER_MAPPING.keys())}"
        )

    # Build JDBC URL and properties based on adapter type
    # DVT v0.59.0a30: Comprehensive JDBC support for ALL dbt adapters
    if adapter_type in ("postgres", "postgresql"):
        jdbc_url, jdbc_props = _build_postgres_jdbc_config(credentials)
    elif adapter_type == "mysql":
        jdbc_url, jdbc_props = _build_mysql_jdbc_config(credentials)
    elif adapter_type == "snowflake":
        jdbc_url, jdbc_props = _build_snowflake_jdbc_config(credentials)
    elif adapter_type == "redshift":
        jdbc_url, jdbc_props = _build_redshift_jdbc_config(credentials)
    elif adapter_type == "bigquery":
        jdbc_url, jdbc_props = _build_bigquery_jdbc_config(credentials)
    elif adapter_type in ("sqlserver", "mssql", "fabric", "synapse"):
        jdbc_url, jdbc_props = _build_sqlserver_jdbc_config(credentials)
    elif adapter_type == "oracle":
        jdbc_url, jdbc_props = _build_oracle_jdbc_config(credentials)
    elif adapter_type == "databricks":
        jdbc_url, jdbc_props = _build_databricks_jdbc_config(credentials)
    elif adapter_type == "duckdb":
        jdbc_url, jdbc_props = _build_duckdb_jdbc_config(credentials)
    elif adapter_type == "mariadb":
        jdbc_url, jdbc_props = _build_mariadb_jdbc_config(credentials)
    elif adapter_type == "sqlite":
        jdbc_url, jdbc_props = _build_sqlite_jdbc_config(credentials)
    elif adapter_type == "clickhouse":
        jdbc_url, jdbc_props = _build_clickhouse_jdbc_config(credentials)
    elif adapter_type == "trino":
        jdbc_url, jdbc_props = _build_trino_jdbc_config(credentials)
    elif adapter_type == "presto":
        jdbc_url, jdbc_props = _build_presto_jdbc_config(credentials)
    elif adapter_type == "athena":
        jdbc_url, jdbc_props = _build_athena_jdbc_config(credentials)
    elif adapter_type in ("hive", "spark"):
        jdbc_url, jdbc_props = _build_hive_jdbc_config(credentials)
    elif adapter_type == "impala":
        jdbc_url, jdbc_props = _build_impala_jdbc_config(credentials)
    elif adapter_type == "teradata":
        jdbc_url, jdbc_props = _build_teradata_jdbc_config(credentials)
    elif adapter_type == "exasol":
        jdbc_url, jdbc_props = _build_exasol_jdbc_config(credentials)
    elif adapter_type == "vertica":
        jdbc_url, jdbc_props = _build_vertica_jdbc_config(credentials)
    elif adapter_type == "db2":
        jdbc_url, jdbc_props = _build_db2_jdbc_config(credentials)
    elif adapter_type == "singlestore":
        jdbc_url, jdbc_props = _build_singlestore_jdbc_config(credentials)
    elif adapter_type in ("starrocks", "doris"):
        # StarRocks and Doris use MySQL protocol
        jdbc_url, jdbc_props = _build_mysql_jdbc_config(credentials)
    elif adapter_type in ("greenplum", "timescaledb", "questdb", "materialize", "alloydb"):
        # These use PostgreSQL protocol
        jdbc_url, jdbc_props = _build_postgres_jdbc_config(credentials)
    elif adapter_type == "dremio":
        jdbc_url, jdbc_props = _build_dremio_jdbc_config(credentials)
    elif adapter_type == "firebolt":
        jdbc_url, jdbc_props = _build_firebolt_jdbc_config(credentials)
    elif adapter_type == "rockset":
        jdbc_url, jdbc_props = _build_rockset_jdbc_config(credentials)
    elif adapter_type == "monetdb":
        jdbc_url, jdbc_props = _build_monetdb_jdbc_config(credentials)
    elif adapter_type == "cratedb":
        jdbc_url, jdbc_props = _build_cratedb_jdbc_config(credentials)
    else:
        # Fallback: Try generic builder based on credentials structure
        jdbc_url, jdbc_props = _build_generic_jdbc_config(credentials, adapter_type)

    # DVT v0.51.8: Rewrite localhost URLs for Docker Spark clusters
    if _docker_mode_enabled:
        jdbc_url = _rewrite_localhost_for_docker(jdbc_url)

    return jdbc_url, jdbc_props


def _build_postgres_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for PostgreSQL."""
    creds_dict = credentials.to_dict()

    host = creds_dict.get("host", "localhost")
    port = creds_dict.get("port", 5432)
    database = creds_dict.get("database")
    user = creds_dict.get("user")
    password = creds_dict.get("password", "")

    if not database:
        raise DbtRuntimeError("PostgreSQL credentials missing required field: database")
    if not user:
        raise DbtRuntimeError("PostgreSQL credentials missing required field: user")

    jdbc_url = f"jdbc:postgresql://{host}:{port}/{database}"

    jdbc_properties = {
        "user": user,
        "password": password,
        "driver": JDBC_DRIVER_MAPPING["postgres"],
    }

    # Optional: Add SSL configuration if present
    if creds_dict.get("sslmode"):
        jdbc_properties["ssl"] = "true" if creds_dict["sslmode"] != "disable" else "false"

    return jdbc_url, jdbc_properties


def _build_mysql_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for MySQL."""
    creds_dict = credentials.to_dict()

    host = creds_dict.get("host", "localhost")
    port = creds_dict.get("port", 3306)
    database = creds_dict.get("database")
    user = creds_dict.get("user")
    password = creds_dict.get("password", "")

    if not database:
        raise DbtRuntimeError("MySQL credentials missing required field: database")
    if not user:
        raise DbtRuntimeError("MySQL credentials missing required field: user")

    jdbc_url = f"jdbc:mysql://{host}:{port}/{database}"

    jdbc_properties = {
        "user": user,
        "password": password,
        "driver": JDBC_DRIVER_MAPPING["mysql"],
    }

    return jdbc_url, jdbc_properties


def _build_snowflake_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for Snowflake."""
    creds_dict = credentials.to_dict()

    account = creds_dict.get("account")
    user = creds_dict.get("user")
    password = creds_dict.get("password", "")
    database = creds_dict.get("database")
    warehouse = creds_dict.get("warehouse")
    schema = creds_dict.get("schema", "public")

    if not account:
        raise DbtRuntimeError("Snowflake credentials missing required field: account")
    if not user:
        raise DbtRuntimeError("Snowflake credentials missing required field: user")

    # Snowflake JDBC URL format with Arrow disabled via URL parameter
    # This is more reliable than JDBC properties for Snowflake driver
    jdbc_url = f"jdbc:snowflake://{account}.snowflakecomputing.com/?JDBC_QUERY_RESULT_FORMAT=JSON"

    jdbc_properties = {
        "user": user,
        "password": password,
        "driver": JDBC_DRIVER_MAPPING["snowflake"],
        # CRITICAL FIX v0.4.4: Disable Arrow format to avoid Java 21 module access errors
        # Property must be uppercase and set in BOTH URL and properties for reliability
        "JDBC_QUERY_RESULT_FORMAT": "JSON",
        "jdbc_query_result_format": "json",  # Lowercase variant for compatibility
        # Additional Snowflake-specific optimizations
        "JDBC_USE_SESSION_TIMEZONE": "false",  # Use UTC for consistency
    }

    # Add optional properties
    if database:
        jdbc_properties["db"] = database
    if warehouse:
        jdbc_properties["warehouse"] = warehouse
    if schema:
        jdbc_properties["schema"] = schema

    return jdbc_url, jdbc_properties


def _build_redshift_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for Amazon Redshift."""
    creds_dict = credentials.to_dict()

    host = creds_dict.get("host")
    port = creds_dict.get("port", 5439)
    database = creds_dict.get("database")
    user = creds_dict.get("user")
    password = creds_dict.get("password", "")

    if not host:
        raise DbtRuntimeError("Redshift credentials missing required field: host")
    if not database:
        raise DbtRuntimeError("Redshift credentials missing required field: database")
    if not user:
        raise DbtRuntimeError("Redshift credentials missing required field: user")

    jdbc_url = f"jdbc:redshift://{host}:{port}/{database}"

    jdbc_properties = {
        "user": user,
        "password": password,
        "driver": JDBC_DRIVER_MAPPING["redshift"],
    }

    return jdbc_url, jdbc_properties


def _build_bigquery_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for Google BigQuery."""
    creds_dict = credentials.to_dict()

    project = creds_dict.get("project")
    dataset = creds_dict.get("dataset") or creds_dict.get("schema")

    if not project:
        raise DbtRuntimeError("BigQuery credentials missing required field: project")

    # BigQuery JDBC URL format
    jdbc_url = "jdbc:bigquery://https://www.googleapis.com/bigquery/v2:443"

    jdbc_properties = {
        "ProjectId": project,
        "driver": JDBC_DRIVER_MAPPING["bigquery"],
    }

    if dataset:
        jdbc_properties["DefaultDataset"] = dataset

    # Handle authentication
    # BigQuery typically uses service account JSON or OAuth
    if creds_dict.get("keyfile"):
        jdbc_properties["OAuthType"] = "0"  # Service account
        jdbc_properties["OAuthServiceAcctEmail"] = creds_dict.get("client_email", "")
        jdbc_properties["OAuthPvtKeyPath"] = creds_dict["keyfile"]

    return jdbc_url, jdbc_properties


def _build_sqlserver_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for Microsoft SQL Server."""
    creds_dict = credentials.to_dict()

    host = creds_dict.get("host", "localhost")
    port = creds_dict.get("port", 1433)
    database = creds_dict.get("database")
    user = creds_dict.get("user")
    password = creds_dict.get("password", "")

    if not database:
        raise DbtRuntimeError("SQL Server credentials missing required field: database")
    if not user:
        raise DbtRuntimeError("SQL Server credentials missing required field: user")

    jdbc_url = f"jdbc:sqlserver://{host}:{port};databaseName={database}"

    jdbc_properties = {
        "user": user,
        "password": password,
        "driver": JDBC_DRIVER_MAPPING["sqlserver"],
    }

    return jdbc_url, jdbc_properties


def _build_oracle_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for Oracle Database."""
    creds_dict = credentials.to_dict()

    host = creds_dict.get("host", "localhost")
    port = creds_dict.get("port", 1521)
    database = creds_dict.get("database") or creds_dict.get("service_name")
    user = creds_dict.get("user")
    password = creds_dict.get("password", "")

    if not database:
        raise DbtRuntimeError("Oracle credentials missing required field: database/service_name")
    if not user:
        raise DbtRuntimeError("Oracle credentials missing required field: user")

    # Oracle thin driver format
    jdbc_url = f"jdbc:oracle:thin:@{host}:{port}:{database}"

    jdbc_properties = {
        "user": user,
        "password": password,
        "driver": JDBC_DRIVER_MAPPING["oracle"],
    }

    return jdbc_url, jdbc_properties


def _build_databricks_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """
    Build JDBC config for Databricks SQL Warehouse or Cluster.

    DVT v0.51.5: Added support for Databricks JDBC connectivity.

    Databricks JDBC URL format:
    jdbc:databricks://<host>:443/default;transportMode=http;ssl=1;httpPath=<http_path>;AuthMech=3;

    The dbt-databricks adapter credentials include:
    - host: Databricks workspace URL (e.g., dbc-xxxxx.cloud.databricks.com)
    - http_path: SQL warehouse or cluster HTTP path
    - token: Personal access token for authentication
    - catalog: Unity Catalog name (optional)
    - schema: Default schema (optional)
    """
    creds_dict = credentials.to_dict()

    host = creds_dict.get("host")
    http_path = creds_dict.get("http_path")
    token = creds_dict.get("token")
    catalog = creds_dict.get("catalog", "hive_metastore")
    schema = creds_dict.get("schema", "default")

    if not host:
        raise DbtRuntimeError("Databricks credentials missing required field: host")
    if not http_path:
        raise DbtRuntimeError("Databricks credentials missing required field: http_path")
    if not token:
        raise DbtRuntimeError("Databricks credentials missing required field: token")

    # Build Databricks JDBC URL
    # Format: jdbc:databricks://<host>:443/<catalog>;transportMode=http;ssl=1;httpPath=<http_path>;AuthMech=3;
    jdbc_url = (
        f"jdbc:databricks://{host}:443/{catalog};"
        f"transportMode=http;ssl=1;httpPath={http_path};AuthMech=3"
    )

    jdbc_properties = {
        "UID": "token",  # Databricks uses "token" as username for PAT auth
        "PWD": token,
        "driver": JDBC_DRIVER_MAPPING["databricks"],
    }

    return jdbc_url, jdbc_properties


# ============================================================
# DVT v0.59.0a30: Additional JDBC Config Builders
# ============================================================


def _build_duckdb_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """
    Build JDBC config for DuckDB.

    DuckDB JDBC URL format:
    - In-memory: jdbc:duckdb:
    - File-based: jdbc:duckdb:/path/to/database.duckdb

    Note: For federation, DuckDB is typically a target (write destination).
    The Spark JDBC write will create/update the file.
    """
    creds_dict = credentials.to_dict()

    # Get the database path (DuckDB uses 'path' for file location)
    path = creds_dict.get("path") or creds_dict.get("database", ":memory:")

    # Expand ~ and resolve path
    if path and path != ":memory:":
        import os
        path = os.path.expanduser(path)
        path = os.path.abspath(path)

    # Build JDBC URL
    if path == ":memory:":
        jdbc_url = "jdbc:duckdb:"
    else:
        jdbc_url = f"jdbc:duckdb:{path}"

    jdbc_properties = {
        "driver": JDBC_DRIVER_MAPPING["duckdb"],
    }

    return jdbc_url, jdbc_properties


def _build_mariadb_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for MariaDB."""
    creds_dict = credentials.to_dict()

    host = creds_dict.get("host", "localhost")
    port = creds_dict.get("port", 3306)
    database = creds_dict.get("database")
    user = creds_dict.get("user")
    password = creds_dict.get("password", "")

    if not database:
        raise DbtRuntimeError("MariaDB credentials missing required field: database")
    if not user:
        raise DbtRuntimeError("MariaDB credentials missing required field: user")

    jdbc_url = f"jdbc:mariadb://{host}:{port}/{database}"

    jdbc_properties = {
        "user": user,
        "password": password,
        "driver": JDBC_DRIVER_MAPPING["mariadb"],
    }

    return jdbc_url, jdbc_properties


def _build_sqlite_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for SQLite."""
    creds_dict = credentials.to_dict()

    path = creds_dict.get("path") or creds_dict.get("database", ":memory:")

    # Expand ~ and resolve path
    if path and path != ":memory:":
        import os
        path = os.path.expanduser(path)
        path = os.path.abspath(path)

    jdbc_url = f"jdbc:sqlite:{path}"

    jdbc_properties = {
        "driver": JDBC_DRIVER_MAPPING["sqlite"],
    }

    return jdbc_url, jdbc_properties


def _build_clickhouse_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for ClickHouse."""
    creds_dict = credentials.to_dict()

    host = creds_dict.get("host", "localhost")
    port = creds_dict.get("port", 8123)  # HTTP port, JDBC uses 8443 for secure
    database = creds_dict.get("database", "default")
    user = creds_dict.get("user", "default")
    password = creds_dict.get("password", "")

    # ClickHouse JDBC URL format
    jdbc_url = f"jdbc:clickhouse://{host}:{port}/{database}"

    jdbc_properties = {
        "user": user,
        "password": password,
        "driver": JDBC_DRIVER_MAPPING["clickhouse"],
    }

    return jdbc_url, jdbc_properties


def _build_trino_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for Trino."""
    creds_dict = credentials.to_dict()

    host = creds_dict.get("host", "localhost")
    port = creds_dict.get("port", 8080)
    catalog = creds_dict.get("catalog") or creds_dict.get("database", "hive")
    schema = creds_dict.get("schema", "default")
    user = creds_dict.get("user", "trino")
    password = creds_dict.get("password", "")

    # Trino JDBC URL format
    jdbc_url = f"jdbc:trino://{host}:{port}/{catalog}/{schema}"

    jdbc_properties = {
        "user": user,
        "driver": JDBC_DRIVER_MAPPING["trino"],
    }
    if password:
        jdbc_properties["password"] = password

    return jdbc_url, jdbc_properties


def _build_presto_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for Presto."""
    creds_dict = credentials.to_dict()

    host = creds_dict.get("host", "localhost")
    port = creds_dict.get("port", 8080)
    catalog = creds_dict.get("catalog") or creds_dict.get("database", "hive")
    schema = creds_dict.get("schema", "default")
    user = creds_dict.get("user", "presto")
    password = creds_dict.get("password", "")

    # Presto JDBC URL format
    jdbc_url = f"jdbc:presto://{host}:{port}/{catalog}/{schema}"

    jdbc_properties = {
        "user": user,
        "driver": JDBC_DRIVER_MAPPING["presto"],
    }
    if password:
        jdbc_properties["password"] = password

    return jdbc_url, jdbc_properties


def _build_athena_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for AWS Athena."""
    creds_dict = credentials.to_dict()

    region = creds_dict.get("region", "us-east-1")
    s3_staging_dir = creds_dict.get("s3_staging_dir")
    database = creds_dict.get("database", "default")

    if not s3_staging_dir:
        raise DbtRuntimeError("Athena credentials missing required field: s3_staging_dir")

    # Athena JDBC URL format
    jdbc_url = (
        f"jdbc:awsathena://athena.{region}.amazonaws.com:443;"
        f"S3OutputLocation={s3_staging_dir}"
    )

    jdbc_properties = {
        "Schema": database,
        "driver": JDBC_DRIVER_MAPPING["athena"],
    }

    # Handle AWS authentication
    if creds_dict.get("aws_access_key_id"):
        jdbc_properties["AwsCredentialsProviderClass"] = "com.simba.athena.amazonaws.auth.AWSStaticCredentialsProvider"
        jdbc_properties["AwsCredentialsProviderArguments"] = (
            f"{creds_dict['aws_access_key_id']},{creds_dict.get('aws_secret_access_key', '')}"
        )

    return jdbc_url, jdbc_properties


def _build_hive_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for Apache Hive."""
    creds_dict = credentials.to_dict()

    host = creds_dict.get("host", "localhost")
    port = creds_dict.get("port", 10000)
    database = creds_dict.get("database", "default")
    user = creds_dict.get("user", "")
    password = creds_dict.get("password", "")

    # Hive JDBC URL format
    jdbc_url = f"jdbc:hive2://{host}:{port}/{database}"

    jdbc_properties = {
        "driver": JDBC_DRIVER_MAPPING["hive"],
    }
    if user:
        jdbc_properties["user"] = user
    if password:
        jdbc_properties["password"] = password

    return jdbc_url, jdbc_properties


def _build_impala_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for Cloudera Impala."""
    creds_dict = credentials.to_dict()

    host = creds_dict.get("host", "localhost")
    port = creds_dict.get("port", 21050)
    database = creds_dict.get("database", "default")
    user = creds_dict.get("user", "")
    password = creds_dict.get("password", "")

    # Impala JDBC URL format
    jdbc_url = f"jdbc:impala://{host}:{port}/{database}"

    jdbc_properties = {
        "driver": JDBC_DRIVER_MAPPING["impala"],
    }
    if user:
        jdbc_properties["user"] = user
    if password:
        jdbc_properties["password"] = password

    return jdbc_url, jdbc_properties


def _build_teradata_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for Teradata."""
    creds_dict = credentials.to_dict()

    host = creds_dict.get("host", "localhost")
    database = creds_dict.get("database")
    user = creds_dict.get("user")
    password = creds_dict.get("password", "")

    if not user:
        raise DbtRuntimeError("Teradata credentials missing required field: user")

    # Teradata JDBC URL format
    jdbc_url = f"jdbc:teradata://{host}"
    if database:
        jdbc_url += f"/DATABASE={database}"

    jdbc_properties = {
        "user": user,
        "password": password,
        "driver": JDBC_DRIVER_MAPPING["teradata"],
    }

    return jdbc_url, jdbc_properties


def _build_exasol_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for Exasol."""
    creds_dict = credentials.to_dict()

    host = creds_dict.get("host", "localhost")
    port = creds_dict.get("port", 8563)
    user = creds_dict.get("user")
    password = creds_dict.get("password", "")

    if not user:
        raise DbtRuntimeError("Exasol credentials missing required field: user")

    # Exasol JDBC URL format
    jdbc_url = f"jdbc:exa:{host}:{port}"

    jdbc_properties = {
        "user": user,
        "password": password,
        "driver": JDBC_DRIVER_MAPPING["exasol"],
    }

    return jdbc_url, jdbc_properties


def _build_vertica_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for Vertica."""
    creds_dict = credentials.to_dict()

    host = creds_dict.get("host", "localhost")
    port = creds_dict.get("port", 5433)
    database = creds_dict.get("database")
    user = creds_dict.get("user")
    password = creds_dict.get("password", "")

    if not database:
        raise DbtRuntimeError("Vertica credentials missing required field: database")
    if not user:
        raise DbtRuntimeError("Vertica credentials missing required field: user")

    # Vertica JDBC URL format
    jdbc_url = f"jdbc:vertica://{host}:{port}/{database}"

    jdbc_properties = {
        "user": user,
        "password": password,
        "driver": JDBC_DRIVER_MAPPING["vertica"],
    }

    return jdbc_url, jdbc_properties


def _build_db2_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for IBM DB2."""
    creds_dict = credentials.to_dict()

    host = creds_dict.get("host", "localhost")
    port = creds_dict.get("port", 50000)
    database = creds_dict.get("database")
    user = creds_dict.get("user")
    password = creds_dict.get("password", "")

    if not database:
        raise DbtRuntimeError("DB2 credentials missing required field: database")
    if not user:
        raise DbtRuntimeError("DB2 credentials missing required field: user")

    # DB2 JDBC URL format
    jdbc_url = f"jdbc:db2://{host}:{port}/{database}"

    jdbc_properties = {
        "user": user,
        "password": password,
        "driver": JDBC_DRIVER_MAPPING["db2"],
    }

    return jdbc_url, jdbc_properties


def _build_singlestore_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for SingleStore (formerly MemSQL)."""
    creds_dict = credentials.to_dict()

    host = creds_dict.get("host", "localhost")
    port = creds_dict.get("port", 3306)  # SingleStore uses MySQL port
    database = creds_dict.get("database")
    user = creds_dict.get("user")
    password = creds_dict.get("password", "")

    if not database:
        raise DbtRuntimeError("SingleStore credentials missing required field: database")
    if not user:
        raise DbtRuntimeError("SingleStore credentials missing required field: user")

    # SingleStore JDBC URL format
    jdbc_url = f"jdbc:singlestore://{host}:{port}/{database}"

    jdbc_properties = {
        "user": user,
        "password": password,
        "driver": JDBC_DRIVER_MAPPING["singlestore"],
    }

    return jdbc_url, jdbc_properties


def _build_dremio_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for Dremio."""
    creds_dict = credentials.to_dict()

    host = creds_dict.get("host", "localhost")
    port = creds_dict.get("port", 31010)
    user = creds_dict.get("user")
    password = creds_dict.get("password", "")

    if not user:
        raise DbtRuntimeError("Dremio credentials missing required field: user")

    # Dremio JDBC URL format
    jdbc_url = f"jdbc:dremio:direct={host}:{port}"

    jdbc_properties = {
        "user": user,
        "password": password,
        "driver": JDBC_DRIVER_MAPPING["dremio"],
    }

    return jdbc_url, jdbc_properties


def _build_firebolt_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for Firebolt."""
    creds_dict = credentials.to_dict()

    database = creds_dict.get("database")
    engine = creds_dict.get("engine")
    user = creds_dict.get("user")
    password = creds_dict.get("password", "")

    if not database:
        raise DbtRuntimeError("Firebolt credentials missing required field: database")
    if not user:
        raise DbtRuntimeError("Firebolt credentials missing required field: user")

    # Firebolt JDBC URL format
    jdbc_url = f"jdbc:firebolt:{database}"
    if engine:
        jdbc_url += f"?engine={engine}"

    jdbc_properties = {
        "user": user,
        "password": password,
        "driver": JDBC_DRIVER_MAPPING["firebolt"],
    }

    return jdbc_url, jdbc_properties


def _build_rockset_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for Rockset."""
    creds_dict = credentials.to_dict()

    api_key = creds_dict.get("api_key") or creds_dict.get("password")
    api_server = creds_dict.get("api_server", "api.usw2a1.rockset.com")

    if not api_key:
        raise DbtRuntimeError("Rockset credentials missing required field: api_key")

    # Rockset JDBC URL format
    jdbc_url = f"jdbc:rockset://{api_server}"

    jdbc_properties = {
        "apiKey": api_key,
        "driver": JDBC_DRIVER_MAPPING["rockset"],
    }

    return jdbc_url, jdbc_properties


def _build_monetdb_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for MonetDB."""
    creds_dict = credentials.to_dict()

    host = creds_dict.get("host", "localhost")
    port = creds_dict.get("port", 50000)
    database = creds_dict.get("database")
    user = creds_dict.get("user")
    password = creds_dict.get("password", "")

    if not database:
        raise DbtRuntimeError("MonetDB credentials missing required field: database")
    if not user:
        raise DbtRuntimeError("MonetDB credentials missing required field: user")

    # MonetDB JDBC URL format
    jdbc_url = f"jdbc:monetdb://{host}:{port}/{database}"

    jdbc_properties = {
        "user": user,
        "password": password,
        "driver": JDBC_DRIVER_MAPPING["monetdb"],
    }

    return jdbc_url, jdbc_properties


def _build_cratedb_jdbc_config(credentials: Credentials) -> Tuple[str, Dict[str, str]]:
    """Build JDBC config for CrateDB."""
    creds_dict = credentials.to_dict()

    host = creds_dict.get("host", "localhost")
    port = creds_dict.get("port", 5432)  # CrateDB uses PostgreSQL port
    schema = creds_dict.get("schema", "doc")
    user = creds_dict.get("user", "crate")
    password = creds_dict.get("password", "")

    # CrateDB JDBC URL format
    jdbc_url = f"jdbc:crate://{host}:{port}/?schema={schema}"

    jdbc_properties = {
        "user": user,
        "password": password,
        "driver": JDBC_DRIVER_MAPPING["cratedb"],
    }

    return jdbc_url, jdbc_properties


def _build_generic_jdbc_config(credentials: Credentials, adapter_type: str) -> Tuple[str, Dict[str, str]]:
    """
    Generic JDBC config builder for adapters not explicitly supported.

    This tries to build a reasonable JDBC URL based on common credential patterns.
    Works for many databases that follow standard connection conventions.
    """
    creds_dict = credentials.to_dict()

    host = creds_dict.get("host", "localhost")
    port = creds_dict.get("port", 5432)
    database = creds_dict.get("database") or creds_dict.get("schema", "")
    user = creds_dict.get("user", "")
    password = creds_dict.get("password", "")

    # Get driver from mapping if available
    driver = JDBC_DRIVER_MAPPING.get(adapter_type)
    if not driver:
        raise DbtRuntimeError(
            f"No JDBC driver mapping found for adapter type '{adapter_type}'. "
            f"Please add support for this adapter in jdbc_utils.py"
        )

    # Build generic JDBC URL
    if database:
        jdbc_url = f"jdbc:{adapter_type}://{host}:{port}/{database}"
    else:
        jdbc_url = f"jdbc:{adapter_type}://{host}:{port}"

    jdbc_properties = {
        "driver": driver,
    }
    if user:
        jdbc_properties["user"] = user
    if password:
        jdbc_properties["password"] = password

    return jdbc_url, jdbc_properties


def auto_detect_partition_column(adapter: BaseAdapter, schema: str, table: str) -> Optional[str]:
    """
    Auto-detect the best column for partitioning parallel JDBC reads.

    Queries table metadata to find a suitable partition column. Prioritizes:
    1. Primary key columns (single column PKs only)
    2. Columns named 'id' or ending with '_id'
    3. Timestamp/date columns
    4. Integer columns

    :param adapter: dbt adapter to use for querying metadata
    :param schema: Schema/dataset name
    :param table: Table name
    :returns: Column name suitable for partitioning, or None if not found

    Example:
        >>> column = auto_detect_partition_column(adapter, "public", "users")
        >>> if column:
        ...     print(f"Using {column} for partitioning")
        ... else:
        ...     print("No suitable partition column found")
    """
    try:
        # Strategy 1: Check for primary key
        pk_column = _get_primary_key_column(adapter, schema, table)
        if pk_column:
            return pk_column

        # Strategy 2: Get all columns and look for ID-like columns
        columns = _get_table_columns(adapter, schema, table)

        # Look for ID columns (exact match or suffix)
        for col_name, col_type in columns:
            col_name_lower = col_name.lower()
            if col_name_lower == "id" or col_name_lower.endswith("_id"):
                # Check if it's an integer type
                if _is_integer_type(col_type):
                    return col_name

        # Strategy 3: Look for timestamp/date columns
        for col_name, col_type in columns:
            if _is_timestamp_type(col_type):
                return col_name

        # Strategy 4: Look for any integer column
        for col_name, col_type in columns:
            if _is_integer_type(col_type):
                return col_name

        # No suitable column found
        return None

    except Exception:
        # If metadata query fails, return None (caller can decide to read without partitioning)
        return None


def estimate_partition_bounds(
    adapter: BaseAdapter, schema: str, table: str, column: str
) -> Tuple[int, int]:
    """
    Estimate partition bounds (min/max) for a numeric partition column.

    Queries the table to get MIN and MAX values of the partition column,
    which are used by Spark JDBC to distribute reads across workers.

    :param adapter: dbt adapter to use for querying
    :param schema: Schema/dataset name
    :param table: Table name
    :param column: Partition column name
    :returns: Tuple of (lower_bound, upper_bound)
    :raises DbtRuntimeError: If query fails or column is not numeric

    Example:
        >>> lower, upper = estimate_partition_bounds(adapter, "public", "orders", "order_id")
        >>> print(f"Partition range: {lower} to {upper}")
        Partition range: 1 to 1000000
    """
    try:
        # Build qualified table name
        qualified_table = f"{schema}.{table}"

        # Query for min/max
        sql = f"SELECT MIN({column}) as min_val, MAX({column}) as max_val FROM {qualified_table}"

        # Execute via adapter
        response, result_table = adapter.execute(sql, auto_begin=False, fetch=True)

        if not result_table or len(result_table.rows) == 0:
            raise DbtRuntimeError(
                f"Failed to estimate partition bounds for {qualified_table}.{column}: "
                "Query returned no results"
            )

        row = result_table.rows[0]
        min_val = row[0]
        max_val = row[1]

        if min_val is None or max_val is None:
            raise DbtRuntimeError(
                f"Failed to estimate partition bounds for {qualified_table}.{column}: "
                "Column contains only NULL values"
            )

        # Convert to integers
        lower_bound = int(min_val)
        upper_bound = int(max_val)

        return lower_bound, upper_bound

    except Exception as e:
        raise DbtRuntimeError(
            f"Failed to estimate partition bounds for {schema}.{table}.{column}: {str(e)}"
        ) from e


# Helper functions for metadata queries


def _get_primary_key_column(adapter: BaseAdapter, schema: str, table: str) -> Optional[str]:
    """
    Get primary key column name (if single-column PK exists).

    Implementation is adapter-specific. Returns None if not implemented
    or if PK is composite.
    """
    adapter_type = adapter.type().lower()

    try:
        if adapter_type in ("postgres", "postgresql", "redshift"):
            # PostgreSQL/Redshift: Query information_schema
            sql = f"""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = '{schema}.{table}'::regclass
            AND i.indisprimary
            """
            response, result = adapter.execute(sql, auto_begin=False, fetch=True)
            if result and len(result.rows) == 1:
                return result.rows[0][0]

        elif adapter_type == "mysql":
            # MySQL: Query information_schema
            sql = f"""
            SELECT COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = '{schema}'
            AND TABLE_NAME = '{table}'
            AND CONSTRAINT_NAME = 'PRIMARY'
            """
            response, result = adapter.execute(sql, auto_begin=False, fetch=True)
            if result and len(result.rows) == 1:
                return result.rows[0][0]

        # For other adapters or if query fails, return None
        return None

    except Exception:
        return None


def _get_table_columns(adapter: BaseAdapter, schema: str, table: str) -> list[Tuple[str, str]]:
    """
    Get list of (column_name, column_type) for a table.
    """
    adapter_type = adapter.type().lower()

    try:
        if adapter_type in ("postgres", "postgresql", "redshift"):
            sql = f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = '{schema}'
            AND table_name = '{table}'
            ORDER BY ordinal_position
            """
            response, result = adapter.execute(sql, auto_begin=False, fetch=True)
            return [(row[0], row[1]) for row in result.rows]

        elif adapter_type == "mysql":
            sql = f"""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = '{schema}'
            AND TABLE_NAME = '{table}'
            ORDER BY ORDINAL_POSITION
            """
            response, result = adapter.execute(sql, auto_begin=False, fetch=True)
            return [(row[0], row[1]) for row in result.rows]

        else:
            # Fallback: Use LIMIT 0 query to get columns
            sql = f"SELECT * FROM {schema}.{table} LIMIT 0"
            response, result = adapter.execute(sql, auto_begin=False, fetch=True)
            # Return column names with unknown types
            return [(col, "unknown") for col in result.column_names]

    except Exception:
        return []


def _is_integer_type(sql_type: str) -> bool:
    """Check if SQL type is an integer type."""
    sql_type_upper = sql_type.upper()
    return any(
        int_type in sql_type_upper
        for int_type in ["INT", "INTEGER", "BIGINT", "SMALLINT", "SERIAL"]
    )


def _is_timestamp_type(sql_type: str) -> bool:
    """Check if SQL type is a timestamp/date type."""
    sql_type_upper = sql_type.upper()
    return any(time_type in sql_type_upper for time_type in ["TIMESTAMP", "DATETIME", "DATE"])
