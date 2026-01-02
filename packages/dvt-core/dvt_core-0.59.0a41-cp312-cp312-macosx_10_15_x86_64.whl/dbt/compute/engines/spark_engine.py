"""
Spark Compute Engine

Provides Spark integration for large-scale federated query execution.
Supports multiple connection strategies via strategy pattern:
- Local: Embedded PySpark (in-process)
- Standalone: Remote Spark clusters via spark:// URL
- EMR: AWS EMR clusters via YARN
- Dataproc: GCP Dataproc clusters

Key characteristics:
- Scalable to large datasets
- Distributed processing
- Can connect to external Spark clusters
- No materialization (ephemeral only)

v0.51.2: Removed Databricks support (serverless cannot read external JDBC sources).
"""

from typing import Any, Dict, List, Optional
from dbt_common.exceptions import DbtRuntimeError

try:
    from pyspark.sql import SparkSession, DataFrame
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False
    SparkSession = None
    DataFrame = None

from dbt.compute.strategies import (
    BaseConnectionStrategy,
    LocalStrategy,
    get_emr_strategy,
    get_dataproc_strategy,
    get_standalone_strategy,
)


def _clean_spark_error(e: Exception) -> str:
    """
    Extract clean error message from Java/Spark exception.

    DVT v0.5.2: Removes verbose Java stack traces and returns readable error message.

    :param e: Exception from Spark/Java
    :returns: Clean error message string
    """
    error_str = str(e)

    # Check for common error patterns and extract meaningful message

    # Pattern 1: ServiceConfigurationError (Scala version mismatch)
    if "ServiceConfigurationError" in error_str:
        if "Unable to get public no-arg constructor" in error_str:
            # Extract the class name that failed
            if "DataSourceRegister:" in error_str:
                class_name = error_str.split("DataSourceRegister:")[-1].split()[0]
                return f"Spark connector incompatible with current Scala version: {class_name}. Try using JDBC driver directly instead of Spark connector."
        return "Spark service configuration error - possible Scala version mismatch"

    # Pattern 2: NoClassDefFoundError
    if "NoClassDefFoundError:" in error_str:
        missing_class = error_str.split("NoClassDefFoundError:")[-1].split()[0].strip()
        return f"Missing Java class: {missing_class}. This usually indicates a Scala version mismatch between Spark and the connector."

    # Pattern 3: ClassNotFoundException
    if "ClassNotFoundException:" in error_str:
        missing_class = error_str.split("ClassNotFoundException:")[-1].split()[0].strip()
        return f"Class not found: {missing_class}"

    # Pattern 4: SQLException
    if "SQLException:" in error_str:
        sql_error = error_str.split("SQLException:")[-1].split('\n')[0].strip()
        return f"SQL Error: {sql_error}"

    # Pattern 5: Snowflake errors
    if "net.snowflake" in error_str:
        if "Authentication" in error_str or "auth" in error_str.lower():
            return "Snowflake authentication failed. Check credentials in profile."
        if "does not exist" in error_str:
            return "Snowflake table/schema not found. Check the object path."

    # Pattern 6: PostgreSQL errors
    if "PSQLException:" in error_str:
        lines = error_str.split('\n')
        for line in lines:
            if "PSQLException:" in line:
                return line.split("PSQLException:")[-1].strip()

    # Default: Return first line only (remove stack trace)
    first_line = error_str.split('\n')[0]
    if len(first_line) > 200:
        first_line = first_line[:200] + "..."
    return first_line


class SparkEngine:
    """
    Ephemeral Spark compute engine for federated query execution.

    Uses strategy pattern for flexible connection management:
    1. Local: Embedded PySpark session (in-process)
    2. Databricks: Remote Databricks clusters via databricks-connect
    3. External: Generic external clusters (legacy)
    """

    def __init__(
        self,
        mode: str = "embedded",
        spark_config: Optional[Dict[str, str]] = None,
        app_name: str = "DVT-Compute",
    ):
        """
        Initialize Spark engine.

        :param mode: 'embedded' for local, 'external' for remote cluster, 'databricks' for Databricks
        :param spark_config: Spark configuration dict (platform-specific)
        :param app_name: Spark application name
        :raises DbtRuntimeError: If PySpark not available or invalid config
        """
        if not PYSPARK_AVAILABLE:
            raise DbtRuntimeError("PySpark is not available. Install it with: pip install pyspark")

        self.mode = mode
        self.spark_config = spark_config or {}
        self.app_name = app_name
        self.spark: Optional[SparkSession] = None
        self.registered_tables: Dict[str, str] = {}

        # Create connection strategy based on mode or config
        self._connection_strategy = self._create_strategy()

    def _create_strategy(self) -> BaseConnectionStrategy:
        """
        Create connection strategy based on mode or config.

        v0.51.2: Removed Databricks (serverless cannot read external JDBC sources).
        Platform detection order:
        1. Dataproc: project + region + cluster
        2. EMR: master=yarn (without Dataproc keys)
        3. Standalone: master=spark://
        4. Local: default (local[*] or no master)

        :returns: Connection strategy instance
        :raises DbtRuntimeError: If platform detection fails
        """
        config_keys = set(self.spark_config.keys())

        # 1. Dataproc: has project, region, and cluster
        if all(k in config_keys for k in ("project", "region", "cluster")):
            DataprocStrategy = get_dataproc_strategy()
            strategy = DataprocStrategy(config=self.spark_config, app_name=self.app_name)
            strategy.validate_config()
            return strategy

        # Check master config for EMR, Standalone, or Local
        master = self.spark_config.get("master", "")

        # 3. EMR: master=yarn (YARN resource manager)
        if master.lower() == "yarn":
            EMRStrategy = get_emr_strategy()
            strategy = EMRStrategy(config=self.spark_config, app_name=self.app_name)
            strategy.validate_config()
            return strategy

        # 4. Standalone: master=spark://
        if master.startswith("spark://"):
            StandaloneStrategy = get_standalone_strategy()
            strategy = StandaloneStrategy(config=self.spark_config, app_name=self.app_name)
            strategy.validate_config()
            return strategy

        # 5. Local: local[*], local[N], or no master (default)
        if master.startswith("local") or not master or self.mode in ("embedded", "local"):
            strategy = LocalStrategy(config=self.spark_config, app_name=self.app_name)
            strategy.validate_config()
            return strategy

        # Explicit mode overrides
        if self.mode == "emr":
            EMRStrategy = get_emr_strategy()
            strategy = EMRStrategy(config=self.spark_config, app_name=self.app_name)
            strategy.validate_config()
            return strategy

        if self.mode == "dataproc":
            DataprocStrategy = get_dataproc_strategy()
            strategy = DataprocStrategy(config=self.spark_config, app_name=self.app_name)
            strategy.validate_config()
            return strategy

        if self.mode in ("standalone", "external"):
            StandaloneStrategy = get_standalone_strategy()
            strategy = StandaloneStrategy(config=self.spark_config, app_name=self.app_name)
            strategy.validate_config()
            return strategy

        # Fallback to local
        strategy = LocalStrategy(config=self.spark_config, app_name=self.app_name)
        strategy.validate_config()
        return strategy

    def __enter__(self):
        """Context manager entry - initialize Spark session."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stop Spark session."""
        self.close()

    def connect(self, adapter_types: Optional[set] = None) -> None:
        """
        Create Spark session using the configured strategy.

        v0.5.99: Now accepts adapter_types for JDBC driver provisioning.

        :param adapter_types: Set of source adapter types that need JDBC drivers
        """
        try:
            self.spark = self._connection_strategy.get_spark_session(adapter_types=adapter_types)
        except Exception as e:
            raise DbtRuntimeError(f"Failed to initialize Spark engine: {str(e)}") from e

    def close(self) -> None:
        """Stop Spark session and release resources."""
        if self.spark:
            try:
                self._connection_strategy.close(self.spark)
            except Exception:
                pass  # Best effort cleanup
            finally:
                self.spark = None
                self.registered_tables.clear()

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get metadata about a registered table.

        :param table_name: Name of the table
        :returns: Dictionary with table metadata (columns, row_count, etc.)
        :raises DbtRuntimeError: If table not found
        """
        if not self.spark:
            raise DbtRuntimeError("Spark engine not connected")

        if table_name not in self.registered_tables:
            raise DbtRuntimeError(f"Table '{table_name}' not registered")

        try:
            # Get DataFrame for the table
            df = self.spark.table(table_name)

            # Get schema
            columns = []
            for field in df.schema.fields:
                columns.append(
                    {"name": field.name, "type": str(field.dataType), "nullable": field.nullable}
                )

            # Get row count
            row_count = df.count()

            return {"table_name": table_name, "columns": columns, "row_count": row_count}

        except Exception as e:
            raise DbtRuntimeError(f"Failed to get info for table '{table_name}': {str(e)}") from e

    def list_tables(self) -> List[str]:
        """
        List all registered tables.

        :returns: List of table names
        """
        return list(self.registered_tables.keys())

    def explain_query(self, sql: str) -> str:
        """
        Get query execution plan.

        Useful for debugging and optimization.

        :param sql: SQL query to explain
        :returns: Query execution plan as string
        """
        if not self.spark:
            raise DbtRuntimeError("Spark engine not connected")

        try:
            df = self.spark.sql(sql)
            # Get extended explain with cost model and optimizations
            return df._jdf.queryExecution().toString()

        except Exception as e:
            raise DbtRuntimeError(f"Failed to explain query: {str(e)}\nSQL: {sql}") from e

    def cache_table(self, table_name: str) -> None:
        """
        Cache a table in Spark memory for faster subsequent queries.

        Useful for tables that are accessed multiple times.

        :param table_name: Name of the table to cache
        :raises DbtRuntimeError: If table not found or caching fails
        """
        if not self.spark:
            raise DbtRuntimeError("Spark engine not connected")

        if table_name not in self.registered_tables:
            raise DbtRuntimeError(f"Table '{table_name}' not registered")

        try:
            self.spark.catalog.cacheTable(table_name)
        except Exception as e:
            raise DbtRuntimeError(f"Failed to cache table '{table_name}': {str(e)}") from e

    def uncache_table(self, table_name: str) -> None:
        """
        Remove a table from Spark memory cache.

        :param table_name: Name of the table to uncache
        """
        if self.spark and table_name in self.registered_tables:
            try:
                self.spark.catalog.uncacheTable(table_name)
            except Exception:
                pass  # Best effort

    def get_platform_info(self) -> Dict[str, Any]:
        """
        Get information about the Spark platform and connection.

        :returns: Dictionary with platform metadata
        """
        info = {
            "platform": self._connection_strategy.get_platform_name(),
            "mode": self.mode,
        }

        # Add strategy-specific info if available
        if hasattr(self._connection_strategy, "get_cluster_info"):
            info.update(self._connection_strategy.get_cluster_info())

        return info

    def estimate_cost(self, duration_minutes: float) -> float:
        """
        Estimate execution cost for the configured platform.

        :param duration_minutes: Estimated query duration in minutes
        :returns: Estimated cost in USD
        """
        return self._connection_strategy.estimate_cost(duration_minutes)

    # JDBC Methods (Phase 1: v0.2.0)

    def supports_jdbc(self, adapter_type: str) -> bool:
        """
        Check if the given adapter type is supported for JDBC connectivity.

        :param adapter_type: Adapter type (e.g., 'postgres', 'mysql', 'snowflake')
        :returns: True if JDBC is supported for this adapter type

        Example:
            >>> engine = SparkEngine()
            >>> engine.supports_jdbc('postgres')
            True
            >>> engine.supports_jdbc('duckdb')
            False
        """
        # Import here to avoid circular dependency
        from dbt.compute.jdbc_utils import JDBC_DRIVER_MAPPING

        return adapter_type.lower() in JDBC_DRIVER_MAPPING

    def read_jdbc(
        self,
        url: str,
        table: str,
        properties: Dict[str, str],
        numPartitions: int = 16,
        partitionColumn: Optional[str] = None,
        lowerBound: Optional[int] = None,
        upperBound: Optional[int] = None,
        predicates: Optional[List[str]] = None,
    ) -> DataFrame:
        """
        Read data from a JDBC source into Spark DataFrame with parallel reads.

        This method bypasses the DVT node's memory by reading data directly
        from the source database into Spark workers (distributed memory).

        :param url: JDBC connection URL (e.g., 'jdbc:postgresql://host:port/db')
        :param table: Table name or SQL query (wrapped in parentheses)
        :param properties: JDBC connection properties (user, password, driver)
        :param numPartitions: Number of partitions for parallel reads (default: 16)
        :param partitionColumn: Column to use for partitioning (must be numeric)
        :param lowerBound: Lower bound for partition column
        :param upperBound: Upper bound for partition column
        :param predicates: List of WHERE clause predicates for filtering partitions
        :returns: Spark DataFrame with loaded data
        :raises DbtRuntimeError: If JDBC read fails

        Example:
            >>> url = "jdbc:postgresql://localhost:5432/warehouse"
            >>> properties = {
            ...     "user": "analytics",
            ...     "password": "secret",
            ...     "driver": "org.postgresql.Driver"
            ... }
            >>> df = engine.read_jdbc(
            ...     url=url,
            ...     table="public.orders",
            ...     properties=properties,
            ...     numPartitions=16,
            ...     partitionColumn="order_id",
            ...     lowerBound=1,
            ...     upperBound=1000000
            ... )
            >>> print(f"Loaded {df.count()} rows")

        Notes:
            - For partitioned reads, all of (partitionColumn, lowerBound, upperBound)
              must be provided
            - Partitioning enables parallel reads across Spark workers
            - Without partitioning, data is read in a single thread
        """
        if not self.spark:
            raise DbtRuntimeError("Spark engine not connected")

        try:
            # Build JDBC read options
            read_options = {
                "url": url,
                "dbtable": table,
                **properties,  # Merge user, password, driver
            }

            # Add partitioning options if provided
            if partitionColumn and lowerBound is not None and upperBound is not None:
                read_options.update(
                    {
                        "partitionColumn": partitionColumn,
                        "lowerBound": str(lowerBound),
                        "upperBound": str(upperBound),
                        "numPartitions": str(numPartitions),
                    }
                )

            # Add predicates if provided
            if predicates:
                # Predicates are used for push-down filtering
                read_options["predicates"] = predicates

            # Read via JDBC
            df = self.spark.read.format("jdbc").options(**read_options).load()

            return df

        except Exception as e:
            # DVT v0.5.2: Clean error message (no Java stack trace)
            clean_error = _clean_spark_error(e)
            raise DbtRuntimeError(f"Failed to read from JDBC source '{table}': {clean_error}")

    def write_jdbc(
        self,
        df: DataFrame,
        url: str,
        table: str,
        properties: Dict[str, str],
        mode: str = "overwrite",
        batchsize: int = 10000,
        numPartitions: Optional[int] = None,
    ) -> None:
        """
        Write Spark DataFrame to JDBC target with batch writes.

        This method writes data directly from Spark workers to the target database,
        bypassing the DVT node's memory.

        :param df: Spark DataFrame to write
        :param url: JDBC connection URL
        :param table: Target table name (qualified: schema.table)
        :param properties: JDBC connection properties (user, password, driver)
        :param mode: Write mode - 'overwrite', 'append', 'error', 'ignore' (default: 'overwrite')
        :param batchsize: Number of rows to insert per batch (default: 10000)
        :param numPartitions: Repartition DataFrame before write for parallelism
        :raises DbtRuntimeError: If JDBC write fails

        Example:
            >>> url = "jdbc:postgresql://localhost:5432/warehouse"
            >>> properties = {
            ...     "user": "analytics",
            ...     "password": "secret",
            ...     "driver": "org.postgresql.Driver"
            ... }
            >>> engine.write_jdbc(
            ...     df=result_df,
            ...     url=url,
            ...     table="analytics.aggregated_metrics",
            ...     properties=properties,
            ...     mode="overwrite",
            ...     batchsize=10000
            ... )

        Notes:
            - 'overwrite' mode drops and recreates the table
            - 'append' mode adds data to existing table
            - Batch size affects memory usage and write performance
            - Larger batch sizes are faster but use more memory
        """
        if not self.spark:
            raise DbtRuntimeError("Spark engine not connected")

        try:
            # Repartition if requested for better write parallelism
            write_df = df
            if numPartitions:
                write_df = df.repartition(numPartitions)

            # DVT v0.5.0: Handle DROP CASCADE for table materialization
            if mode == "overwrite":
                # Drop existing table with CASCADE before writing
                # This is essential for declarative workflows (handles dependent views)
                try:
                    import jaydebeapi
                    conn = jaydebeapi.connect(
                        properties.get("driver"),
                        url,
                        [properties.get("user"), properties.get("password")]
                    )
                    cursor = conn.cursor()
                    cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                    conn.commit()
                    cursor.close()
                    conn.close()
                except Exception:
                    # If DROP fails (table doesn't exist), continue
                    pass

            # Build JDBC write options
            write_options = {
                "url": url,
                "dbtable": table,
                "batchsize": str(batchsize),
                **properties,  # Merge user, password, driver
            }

            # Write via JDBC (now with CASCADE handling)
            write_df.write.format("jdbc").options(**write_options).mode("append" if mode == "overwrite" else mode).save()

        except Exception as e:
            # DVT v0.5.0: Extract only the actual error message (remove Java stack trace)
            error_msg = str(e).split('\n')[0] if '\n' in str(e) else str(e)
            # Look for PostgreSQL error detail
            if "PSQLException:" in str(e):
                lines = str(e).split('\n')
                for i, line in enumerate(lines):
                    if "PSQLException:" in line:
                        error_msg = line.split("PSQLException:")[-1].strip()
                        # Include Detail and Hint if present
                        if i+1 < len(lines) and "Detail:" in lines[i+1]:
                            error_msg += "\n  " + lines[i+1].strip()
                        if i+2 < len(lines) and "Hint:" in lines[i+2]:
                            error_msg += "\n  " + lines[i+2].strip()
                        break
            raise DbtRuntimeError(f"Failed to write to JDBC target '{table}': {error_msg}")

    def register_jdbc_table(
        self,
        url: str,
        table: str,
        properties: Dict[str, str],
        table_alias: str,
        numPartitions: int = 16,
        partitionColumn: Optional[str] = None,
        lowerBound: Optional[int] = None,
        upperBound: Optional[int] = None,
    ) -> None:
        """
        Read from JDBC and register as a temporary view in Spark.

        Convenience method that combines read_jdbc() and temp view registration.

        :param url: JDBC connection URL
        :param table: Source table name
        :param properties: JDBC connection properties
        :param table_alias: Name to register the table as in Spark
        :param numPartitions: Number of partitions for parallel reads
        :param partitionColumn: Column to use for partitioning
        :param lowerBound: Lower bound for partition column
        :param upperBound: Upper bound for partition column
        :raises DbtRuntimeError: If read or registration fails

        Example:
            >>> engine.register_jdbc_table(
            ...     url="jdbc:postgresql://localhost:5432/warehouse",
            ...     table="public.customers",
            ...     properties={"user": "...", "password": "...", "driver": "..."},
            ...     table_alias="customers",
            ...     numPartitions=8,
            ...     partitionColumn="customer_id",
            ...     lowerBound=1,
            ...     upperBound=500000
            ... )
            >>> # Now can query with: engine.execute_query("SELECT * FROM customers")
        """
        # Read from JDBC
        df = self.read_jdbc(
            url=url,
            table=table,
            properties=properties,
            numPartitions=numPartitions,
            partitionColumn=partitionColumn,
            lowerBound=lowerBound,
            upperBound=upperBound,
        )

        # Register as temp view
        df.createOrReplaceTempView(table_alias)

        # Track registration
        self.registered_tables[table_alias] = table_alias

    def get_schema(self, table_alias: str) -> Optional[List]:
        """
        Get the schema of a registered temp view.

        v0.54.0: Returns schema for metadata capture.

        :param table_alias: Name of the registered temp view
        :returns: List of StructFields (name, dataType, nullable), or None if not found
        """
        if not self.spark:
            return None

        try:
            df = self.spark.table(table_alias)
            return df.schema.fields
        except Exception:
            return None
