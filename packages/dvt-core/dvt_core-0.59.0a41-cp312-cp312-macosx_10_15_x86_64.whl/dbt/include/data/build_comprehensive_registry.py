#!/usr/bin/env python3
"""
Build comprehensive datatype_mappings for DVT.

This script builds version-aware type mappings for all major dbt adapters.
Spark versions: 3.x (3.0-3.5), 4.x (4.0+)

Key changes in Spark 4.0:
- MySQL: SMALLINT -> ShortType (was IntegerType), FLOAT -> FloatType (was DoubleType)
- PostgreSQL: TIMESTAMP WITH TIME ZONE handling changed
- New VARIANT type for semi-structured data
- Spark 3.4+: TIMESTAMP_NTZ support
"""

import duckdb
from pathlib import Path

# All mappings: (adapter, adapter_type, spark_type, spark_version, is_complex, cast_expr, notes)
MAPPINGS = []

def add(adapter: str, adapter_type: str, spark_type: str,
        spark_version: str = "all", is_complex: bool = False,
        cast_expr: str = None, notes: str = ""):
    """Add a type mapping."""
    MAPPINGS.append((adapter, adapter_type, spark_type, spark_version, is_complex, cast_expr, notes))

# =============================================================================
# POSTGRES (and PostgreSQL-compatible: AlloyDB, Materialize, TimescaleDB, CrateDB)
# =============================================================================
def add_postgres_types():
    # Numeric types
    add("postgres", "SMALLINT", "ShortType", "all", notes="16-bit signed integer")
    add("postgres", "INT2", "ShortType", "all", notes="Alias for SMALLINT")
    add("postgres", "INTEGER", "IntegerType", "all", notes="32-bit signed integer")
    add("postgres", "INT", "IntegerType", "all", notes="Alias for INTEGER")
    add("postgres", "INT4", "IntegerType", "all", notes="Alias for INTEGER")
    add("postgres", "BIGINT", "LongType", "all", notes="64-bit signed integer")
    add("postgres", "INT8", "LongType", "all", notes="Alias for BIGINT")
    add("postgres", "SERIAL", "IntegerType", "all", notes="Auto-incrementing integer")
    add("postgres", "BIGSERIAL", "LongType", "all", notes="Auto-incrementing bigint")
    add("postgres", "SMALLSERIAL", "ShortType", "all", notes="Auto-incrementing smallint")

    # Decimal/Numeric
    add("postgres", "DECIMAL", "DecimalType", "all", notes="Exact numeric with precision")
    add("postgres", "NUMERIC", "DecimalType", "all", notes="Alias for DECIMAL")
    add("postgres", "MONEY", "DecimalType", "all", notes="Currency amount")

    # Floating point
    add("postgres", "REAL", "FloatType", "all", notes="32-bit floating point")
    add("postgres", "FLOAT4", "FloatType", "all", notes="Alias for REAL")
    add("postgres", "DOUBLE PRECISION", "DoubleType", "all", notes="64-bit floating point")
    add("postgres", "FLOAT8", "DoubleType", "all", notes="Alias for DOUBLE PRECISION")
    add("postgres", "FLOAT", "DoubleType", "all", notes="Floating point (precision-dependent)")

    # Character types
    add("postgres", "VARCHAR", "StringType", "all", notes="Variable-length string")
    add("postgres", "CHARACTER VARYING", "StringType", "all", notes="Alias for VARCHAR")
    add("postgres", "CHAR", "StringType", "all", notes="Fixed-length string")
    add("postgres", "CHARACTER", "StringType", "all", notes="Alias for CHAR")
    add("postgres", "TEXT", "StringType", "all", notes="Unlimited length string")
    add("postgres", "BPCHAR", "StringType", "all", notes="Blank-padded character")
    add("postgres", "NAME", "StringType", "all", notes="Internal name type")

    # Binary
    add("postgres", "BYTEA", "BinaryType", "all", notes="Binary data")

    # Boolean
    add("postgres", "BOOLEAN", "BooleanType", "all", notes="Boolean true/false")
    add("postgres", "BOOL", "BooleanType", "all", notes="Alias for BOOLEAN")

    # Date/Time - Version specific for Spark 4.0
    add("postgres", "DATE", "DateType", "all", notes="Calendar date")
    add("postgres", "TIME", "StringType", "all", notes="Time of day (no timezone)")
    add("postgres", "TIME WITHOUT TIME ZONE", "StringType", "all", notes="Time without timezone")
    add("postgres", "TIME WITH TIME ZONE", "StringType", "all", notes="Time with timezone")
    add("postgres", "TIMETZ", "StringType", "all", notes="Alias for TIME WITH TIME ZONE")

    # Timestamp handling changed in Spark 4.0
    add("postgres", "TIMESTAMP", "TimestampType", "3.x", notes="Timestamp without timezone (Spark 3.x)")
    add("postgres", "TIMESTAMP", "TimestampNTZType", "4.x", notes="Timestamp without timezone (Spark 4.x)")
    add("postgres", "TIMESTAMP WITHOUT TIME ZONE", "TimestampType", "3.x", notes="Explicit no timezone (Spark 3.x)")
    add("postgres", "TIMESTAMP WITHOUT TIME ZONE", "TimestampNTZType", "4.x", notes="Explicit no timezone (Spark 4.x)")
    add("postgres", "TIMESTAMP WITH TIME ZONE", "TimestampType", "all", notes="Timestamp with timezone")
    add("postgres", "TIMESTAMPTZ", "TimestampType", "all", notes="Alias for TIMESTAMP WITH TIME ZONE")

    # Interval
    add("postgres", "INTERVAL", "StringType", "all", notes="Time interval")

    # UUID
    add("postgres", "UUID", "StringType", "all", notes="Universally unique identifier")

    # JSON types
    add("postgres", "JSON", "StringType", "3.x", notes="JSON data (Spark 3.x)")
    add("postgres", "JSON", "VariantType", "4.x", notes="JSON data (Spark 4.x with VARIANT)")
    add("postgres", "JSONB", "StringType", "3.x", notes="Binary JSON (Spark 3.x)")
    add("postgres", "JSONB", "VariantType", "4.x", notes="Binary JSON (Spark 4.x with VARIANT)")

    # Array types
    add("postgres", "ARRAY", "ArrayType", "all", True, notes="Array of any type")
    add("postgres", "_INT4", "ArrayType", "all", True, notes="Integer array")
    add("postgres", "_TEXT", "ArrayType", "all", True, notes="Text array")
    add("postgres", "_VARCHAR", "ArrayType", "all", True, notes="Varchar array")

    # Geometric types (store as string)
    add("postgres", "POINT", "StringType", "all", notes="Geometric point")
    add("postgres", "LINE", "StringType", "all", notes="Infinite line")
    add("postgres", "LSEG", "StringType", "all", notes="Line segment")
    add("postgres", "BOX", "StringType", "all", notes="Rectangular box")
    add("postgres", "PATH", "StringType", "all", notes="Geometric path")
    add("postgres", "POLYGON", "StringType", "all", notes="Polygon")
    add("postgres", "CIRCLE", "StringType", "all", notes="Circle")

    # Network types
    add("postgres", "INET", "StringType", "all", notes="IPv4 or IPv6 address")
    add("postgres", "CIDR", "StringType", "all", notes="IPv4 or IPv6 network")
    add("postgres", "MACADDR", "StringType", "all", notes="MAC address")
    add("postgres", "MACADDR8", "StringType", "all", notes="MAC address (EUI-64)")

    # Bit string
    add("postgres", "BIT", "BinaryType", "all", notes="Fixed-length bit string")
    add("postgres", "BIT VARYING", "BinaryType", "all", notes="Variable-length bit string")
    add("postgres", "VARBIT", "BinaryType", "all", notes="Alias for BIT VARYING")

    # Text search
    add("postgres", "TSVECTOR", "StringType", "all", notes="Text search vector")
    add("postgres", "TSQUERY", "StringType", "all", notes="Text search query")

    # Range types
    add("postgres", "INT4RANGE", "StringType", "all", notes="Integer range")
    add("postgres", "INT8RANGE", "StringType", "all", notes="Bigint range")
    add("postgres", "NUMRANGE", "StringType", "all", notes="Numeric range")
    add("postgres", "TSRANGE", "StringType", "all", notes="Timestamp range")
    add("postgres", "TSTZRANGE", "StringType", "all", notes="Timestamp with timezone range")
    add("postgres", "DATERANGE", "StringType", "all", notes="Date range")

    # Other
    add("postgres", "OID", "LongType", "all", notes="Object identifier")
    add("postgres", "REGCLASS", "StringType", "all", notes="Registered class")
    add("postgres", "XML", "StringType", "all", notes="XML data")

# =============================================================================
# MYSQL (with Spark 4.0 version-specific changes)
# =============================================================================
def add_mysql_types():
    # Integer types - Spark 4.0 changed SMALLINT mapping
    add("mysql", "TINYINT", "ByteType", "all", notes="8-bit signed integer")
    add("mysql", "TINYINT UNSIGNED", "ShortType", "all", notes="8-bit unsigned integer")
    add("mysql", "SMALLINT", "IntegerType", "3.x", notes="16-bit integer (Spark 3.x reads as INT)")
    add("mysql", "SMALLINT", "ShortType", "4.x", notes="16-bit integer (Spark 4.x reads as SHORT)")
    add("mysql", "SMALLINT UNSIGNED", "IntegerType", "all", notes="16-bit unsigned integer")
    add("mysql", "MEDIUMINT", "IntegerType", "all", notes="24-bit signed integer")
    add("mysql", "MEDIUMINT UNSIGNED", "LongType", "3.x", notes="24-bit unsigned (Spark 3.x)")
    add("mysql", "MEDIUMINT UNSIGNED", "IntegerType", "4.x", notes="24-bit unsigned (Spark 4.x)")
    add("mysql", "INT", "IntegerType", "all", notes="32-bit signed integer")
    add("mysql", "INTEGER", "IntegerType", "all", notes="Alias for INT")
    add("mysql", "INT UNSIGNED", "LongType", "all", notes="32-bit unsigned integer")
    add("mysql", "BIGINT", "LongType", "all", notes="64-bit signed integer")
    add("mysql", "BIGINT UNSIGNED", "DecimalType", "all", notes="64-bit unsigned (needs Decimal)")

    # Floating point - Spark 4.0 changed FLOAT mapping
    add("mysql", "FLOAT", "DoubleType", "3.x", notes="32-bit float (Spark 3.x reads as DOUBLE)")
    add("mysql", "FLOAT", "FloatType", "4.x", notes="32-bit float (Spark 4.x reads as FLOAT)")
    add("mysql", "DOUBLE", "DoubleType", "all", notes="64-bit floating point")
    add("mysql", "DOUBLE PRECISION", "DoubleType", "all", notes="Alias for DOUBLE")
    add("mysql", "REAL", "DoubleType", "all", notes="Alias for DOUBLE")

    # Decimal
    add("mysql", "DECIMAL", "DecimalType", "all", notes="Exact numeric")
    add("mysql", "DEC", "DecimalType", "all", notes="Alias for DECIMAL")
    add("mysql", "NUMERIC", "DecimalType", "all", notes="Alias for DECIMAL")
    add("mysql", "FIXED", "DecimalType", "all", notes="Alias for DECIMAL")

    # Bit - Spark 4.0 changed BIT(n>1) mapping
    add("mysql", "BIT", "BooleanType", "all", notes="BIT(1) as boolean")
    add("mysql", "BIT(1)", "BooleanType", "all", notes="Single bit as boolean")
    add("mysql", "BIT(n)", "LongType", "3.x", notes="Multi-bit as Long (Spark 3.x)")
    add("mysql", "BIT(n)", "BinaryType", "4.x", notes="Multi-bit as Binary (Spark 4.x)")

    # String types
    add("mysql", "CHAR", "StringType", "all", notes="Fixed-length string")
    add("mysql", "VARCHAR", "StringType", "all", notes="Variable-length string")
    add("mysql", "TINYTEXT", "StringType", "all", notes="255 byte text")
    add("mysql", "TEXT", "StringType", "all", notes="64KB text")
    add("mysql", "MEDIUMTEXT", "StringType", "all", notes="16MB text")
    add("mysql", "LONGTEXT", "StringType", "all", notes="4GB text")

    # Binary types
    add("mysql", "BINARY", "BinaryType", "all", notes="Fixed-length binary")
    add("mysql", "VARBINARY", "BinaryType", "all", notes="Variable-length binary")
    add("mysql", "TINYBLOB", "BinaryType", "all", notes="255 byte blob")
    add("mysql", "BLOB", "BinaryType", "all", notes="64KB blob")
    add("mysql", "MEDIUMBLOB", "BinaryType", "all", notes="16MB blob")
    add("mysql", "LONGBLOB", "BinaryType", "all", notes="4GB blob")

    # Date/Time
    add("mysql", "DATE", "DateType", "all", notes="Calendar date")
    add("mysql", "TIME", "StringType", "all", notes="Time of day")
    add("mysql", "DATETIME", "TimestampType", "all", notes="Date and time")
    add("mysql", "TIMESTAMP", "TimestampType", "all", notes="Timestamp")
    add("mysql", "YEAR", "IntegerType", "all", notes="Year value")

    # JSON
    add("mysql", "JSON", "StringType", "3.x", notes="JSON document (Spark 3.x)")
    add("mysql", "JSON", "VariantType", "4.x", notes="JSON document (Spark 4.x)")

    # Enum and Set
    add("mysql", "ENUM", "StringType", "all", notes="Enumeration")
    add("mysql", "SET", "StringType", "all", notes="Set of values")

    # Spatial types
    add("mysql", "GEOMETRY", "BinaryType", "all", notes="Geometry type")
    add("mysql", "POINT", "BinaryType", "all", notes="Point geometry")
    add("mysql", "LINESTRING", "BinaryType", "all", notes="Line geometry")
    add("mysql", "POLYGON", "BinaryType", "all", notes="Polygon geometry")
    add("mysql", "GEOMETRYCOLLECTION", "BinaryType", "all", notes="Geometry collection")
    add("mysql", "MULTIPOINT", "BinaryType", "all", notes="Multiple points")
    add("mysql", "MULTILINESTRING", "BinaryType", "all", notes="Multiple lines")
    add("mysql", "MULTIPOLYGON", "BinaryType", "all", notes="Multiple polygons")

# =============================================================================
# BIGQUERY
# =============================================================================
def add_bigquery_types():
    # Numeric types
    add("bigquery", "INT64", "LongType", "all", notes="64-bit signed integer")
    add("bigquery", "INTEGER", "LongType", "all", notes="Alias for INT64")
    add("bigquery", "INT", "LongType", "all", notes="Alias for INT64")
    add("bigquery", "SMALLINT", "LongType", "all", notes="Alias for INT64")
    add("bigquery", "BIGINT", "LongType", "all", notes="Alias for INT64")
    add("bigquery", "TINYINT", "LongType", "all", notes="Alias for INT64")
    add("bigquery", "BYTEINT", "LongType", "all", notes="Alias for INT64")

    # Floating point
    add("bigquery", "FLOAT64", "DoubleType", "all", notes="64-bit floating point")
    add("bigquery", "FLOAT", "DoubleType", "all", notes="Alias for FLOAT64")

    # Numeric/Decimal
    add("bigquery", "NUMERIC", "DecimalType", "all", notes="38 digits precision, 9 scale")
    add("bigquery", "DECIMAL", "DecimalType", "all", notes="Alias for NUMERIC")
    add("bigquery", "BIGNUMERIC", "DecimalType", "all", notes="76 digits precision, 38 scale")
    add("bigquery", "BIGDECIMAL", "DecimalType", "all", notes="Alias for BIGNUMERIC")

    # Boolean
    add("bigquery", "BOOL", "BooleanType", "all", notes="Boolean value")
    add("bigquery", "BOOLEAN", "BooleanType", "all", notes="Alias for BOOL")

    # String
    add("bigquery", "STRING", "StringType", "all", notes="Variable-length Unicode string")

    # Binary
    add("bigquery", "BYTES", "BinaryType", "all", notes="Variable-length binary")

    # Date/Time
    add("bigquery", "DATE", "DateType", "all", notes="Calendar date")
    add("bigquery", "TIME", "StringType", "all", notes="Time of day")
    add("bigquery", "DATETIME", "TimestampType", "3.x", notes="Date and time (Spark 3.x)")
    add("bigquery", "DATETIME", "TimestampNTZType", "4.x", notes="Date and time without TZ (Spark 4.x)")
    add("bigquery", "TIMESTAMP", "TimestampType", "all", notes="Timestamp with microseconds")

    # Interval
    add("bigquery", "INTERVAL", "StringType", "all", notes="Duration of time")

    # Complex types
    add("bigquery", "ARRAY", "ArrayType", "all", True, notes="Ordered list")
    add("bigquery", "STRUCT", "StructType", "all", True, notes="Ordered fields")
    add("bigquery", "RECORD", "StructType", "all", True, notes="Alias for STRUCT")

    # JSON
    add("bigquery", "JSON", "StringType", "3.x", notes="JSON value (Spark 3.x)")
    add("bigquery", "JSON", "VariantType", "4.x", notes="JSON value (Spark 4.x)")

    # Geography
    add("bigquery", "GEOGRAPHY", "StringType", "all", notes="Geographic data (WKT)")

    # Range
    add("bigquery", "RANGE", "StringType", "all", notes="Range of values")

# =============================================================================
# SNOWFLAKE
# =============================================================================
def add_snowflake_types():
    # Numeric
    add("snowflake", "NUMBER", "DecimalType", "all", notes="Numeric with precision/scale")
    add("snowflake", "DECIMAL", "DecimalType", "all", notes="Alias for NUMBER")
    add("snowflake", "NUMERIC", "DecimalType", "all", notes="Alias for NUMBER")
    add("snowflake", "INT", "LongType", "all", notes="38-digit integer")
    add("snowflake", "INTEGER", "LongType", "all", notes="Alias for INT")
    add("snowflake", "BIGINT", "LongType", "all", notes="Alias for INT")
    add("snowflake", "SMALLINT", "LongType", "all", notes="Alias for INT")
    add("snowflake", "TINYINT", "LongType", "all", notes="Alias for INT")
    add("snowflake", "BYTEINT", "LongType", "all", notes="Alias for INT")

    # Floating point
    add("snowflake", "FLOAT", "DoubleType", "all", notes="64-bit floating point")
    add("snowflake", "FLOAT4", "DoubleType", "all", notes="Alias for FLOAT")
    add("snowflake", "FLOAT8", "DoubleType", "all", notes="Alias for FLOAT")
    add("snowflake", "DOUBLE", "DoubleType", "all", notes="Alias for FLOAT")
    add("snowflake", "DOUBLE PRECISION", "DoubleType", "all", notes="Alias for FLOAT")
    add("snowflake", "REAL", "DoubleType", "all", notes="Alias for FLOAT")

    # String
    add("snowflake", "VARCHAR", "StringType", "all", notes="Variable-length string (16MB)")
    add("snowflake", "CHAR", "StringType", "all", notes="Alias for VARCHAR")
    add("snowflake", "CHARACTER", "StringType", "all", notes="Alias for VARCHAR")
    add("snowflake", "STRING", "StringType", "all", notes="Alias for VARCHAR")
    add("snowflake", "TEXT", "StringType", "all", notes="Alias for VARCHAR")
    add("snowflake", "NCHAR", "StringType", "all", notes="Unicode character")
    add("snowflake", "NVARCHAR", "StringType", "all", notes="Unicode varchar")
    add("snowflake", "NVARCHAR2", "StringType", "all", notes="Unicode varchar (Oracle compat)")

    # Binary
    add("snowflake", "BINARY", "BinaryType", "all", notes="Variable-length binary (8MB)")
    add("snowflake", "VARBINARY", "BinaryType", "all", notes="Alias for BINARY")

    # Boolean
    add("snowflake", "BOOLEAN", "BooleanType", "all", notes="Boolean value")

    # Date/Time
    add("snowflake", "DATE", "DateType", "all", notes="Calendar date")
    add("snowflake", "TIME", "StringType", "all", notes="Time of day")
    add("snowflake", "DATETIME", "TimestampType", "all", notes="Alias for TIMESTAMP")
    add("snowflake", "TIMESTAMP", "TimestampType", "all", notes="Timestamp without timezone")
    add("snowflake", "TIMESTAMP_LTZ", "TimestampType", "all", notes="Timestamp with local timezone")
    add("snowflake", "TIMESTAMP_NTZ", "TimestampType", "3.x", notes="Timestamp no timezone (Spark 3.x)")
    add("snowflake", "TIMESTAMP_NTZ", "TimestampNTZType", "4.x", notes="Timestamp no timezone (Spark 4.x)")
    add("snowflake", "TIMESTAMP_TZ", "TimestampType", "all", notes="Timestamp with timezone")

    # Semi-structured
    add("snowflake", "VARIANT", "StringType", "3.x", notes="Semi-structured data (Spark 3.x)")
    add("snowflake", "VARIANT", "VariantType", "4.x", notes="Semi-structured data (Spark 4.x)")
    add("snowflake", "OBJECT", "MapType", "all", True, notes="Key-value pairs")
    add("snowflake", "ARRAY", "ArrayType", "all", True, notes="Array of values")

    # Geospatial
    add("snowflake", "GEOGRAPHY", "StringType", "all", notes="Geographic data")
    add("snowflake", "GEOMETRY", "StringType", "all", notes="Planar geometry")

# =============================================================================
# REDSHIFT
# =============================================================================
def add_redshift_types():
    # Integer types
    add("redshift", "SMALLINT", "ShortType", "all", notes="16-bit signed integer")
    add("redshift", "INT2", "ShortType", "all", notes="Alias for SMALLINT")
    add("redshift", "INTEGER", "IntegerType", "all", notes="32-bit signed integer")
    add("redshift", "INT", "IntegerType", "all", notes="Alias for INTEGER")
    add("redshift", "INT4", "IntegerType", "all", notes="Alias for INTEGER")
    add("redshift", "BIGINT", "LongType", "all", notes="64-bit signed integer")
    add("redshift", "INT8", "LongType", "all", notes="Alias for BIGINT")

    # Decimal
    add("redshift", "DECIMAL", "DecimalType", "all", notes="Exact numeric (38,37)")
    add("redshift", "NUMERIC", "DecimalType", "all", notes="Alias for DECIMAL")

    # Floating point
    add("redshift", "REAL", "FloatType", "all", notes="32-bit floating point")
    add("redshift", "FLOAT4", "FloatType", "all", notes="Alias for REAL")
    add("redshift", "DOUBLE PRECISION", "DoubleType", "all", notes="64-bit floating point")
    add("redshift", "FLOAT8", "DoubleType", "all", notes="Alias for DOUBLE PRECISION")
    add("redshift", "FLOAT", "DoubleType", "all", notes="Alias for DOUBLE PRECISION")

    # Boolean
    add("redshift", "BOOLEAN", "BooleanType", "all", notes="Boolean value")
    add("redshift", "BOOL", "BooleanType", "all", notes="Alias for BOOLEAN")

    # Character types
    add("redshift", "CHAR", "StringType", "all", notes="Fixed-length string (4096)")
    add("redshift", "CHARACTER", "StringType", "all", notes="Alias for CHAR")
    add("redshift", "NCHAR", "StringType", "all", notes="National character")
    add("redshift", "BPCHAR", "StringType", "all", notes="Blank-padded char")
    add("redshift", "VARCHAR", "StringType", "all", notes="Variable-length string (65535)")
    add("redshift", "CHARACTER VARYING", "StringType", "all", notes="Alias for VARCHAR")
    add("redshift", "NVARCHAR", "StringType", "all", notes="National varchar")
    add("redshift", "TEXT", "StringType", "all", notes="Alias for VARCHAR(256)")

    # Binary
    add("redshift", "VARBYTE", "BinaryType", "all", notes="Variable-length binary")
    add("redshift", "VARBINARY", "BinaryType", "all", notes="Alias for VARBYTE")
    add("redshift", "BINARY VARYING", "BinaryType", "all", notes="Alias for VARBYTE")

    # Date/Time
    add("redshift", "DATE", "DateType", "all", notes="Calendar date")
    add("redshift", "TIME", "StringType", "all", notes="Time without timezone")
    add("redshift", "TIMETZ", "StringType", "all", notes="Time with timezone")
    add("redshift", "TIME WITHOUT TIME ZONE", "StringType", "all", notes="Time no TZ")
    add("redshift", "TIME WITH TIME ZONE", "StringType", "all", notes="Time with TZ")
    add("redshift", "TIMESTAMP", "TimestampType", "all", notes="Timestamp without timezone")
    add("redshift", "TIMESTAMPTZ", "TimestampType", "all", notes="Timestamp with timezone")
    add("redshift", "TIMESTAMP WITHOUT TIME ZONE", "TimestampType", "3.x", notes="No TZ (Spark 3.x)")
    add("redshift", "TIMESTAMP WITHOUT TIME ZONE", "TimestampNTZType", "4.x", notes="No TZ (Spark 4.x)")
    add("redshift", "TIMESTAMP WITH TIME ZONE", "TimestampType", "all", notes="With timezone")

    # Interval
    add("redshift", "INTERVAL YEAR TO MONTH", "StringType", "all", notes="Year-month interval")
    add("redshift", "INTERVAL DAY TO SECOND", "StringType", "all", notes="Day-time interval")

    # Semi-structured (SUPER type)
    add("redshift", "SUPER", "StringType", "3.x", notes="Semi-structured (Spark 3.x)")
    add("redshift", "SUPER", "VariantType", "4.x", notes="Semi-structured (Spark 4.x)")

    # Geometry
    add("redshift", "GEOMETRY", "BinaryType", "all", notes="Geometry data")
    add("redshift", "GEOGRAPHY", "BinaryType", "all", notes="Geography data")

    # HyperLogLog
    add("redshift", "HLLSKETCH", "BinaryType", "all", notes="HyperLogLog sketch")

# =============================================================================
# DATABRICKS (Delta Lake)
# =============================================================================
def add_databricks_types():
    # All native Spark types
    add("databricks", "TINYINT", "ByteType", "all", notes="8-bit signed integer")
    add("databricks", "BYTE", "ByteType", "all", notes="Alias for TINYINT")
    add("databricks", "SMALLINT", "ShortType", "all", notes="16-bit signed integer")
    add("databricks", "SHORT", "ShortType", "all", notes="Alias for SMALLINT")
    add("databricks", "INT", "IntegerType", "all", notes="32-bit signed integer")
    add("databricks", "INTEGER", "IntegerType", "all", notes="Alias for INT")
    add("databricks", "BIGINT", "LongType", "all", notes="64-bit signed integer")
    add("databricks", "LONG", "LongType", "all", notes="Alias for BIGINT")

    # Floating point
    add("databricks", "FLOAT", "FloatType", "all", notes="32-bit floating point")
    add("databricks", "REAL", "FloatType", "all", notes="Alias for FLOAT")
    add("databricks", "DOUBLE", "DoubleType", "all", notes="64-bit floating point")
    add("databricks", "DOUBLE PRECISION", "DoubleType", "all", notes="Alias for DOUBLE")

    # Decimal
    add("databricks", "DECIMAL", "DecimalType", "all", notes="Arbitrary precision decimal")
    add("databricks", "DEC", "DecimalType", "all", notes="Alias for DECIMAL")
    add("databricks", "NUMERIC", "DecimalType", "all", notes="Alias for DECIMAL")

    # String
    add("databricks", "STRING", "StringType", "all", notes="UTF-8 string")
    add("databricks", "VARCHAR", "StringType", "all", notes="Alias for STRING")
    add("databricks", "CHAR", "StringType", "all", notes="Alias for STRING")

    # Binary
    add("databricks", "BINARY", "BinaryType", "all", notes="Byte array")

    # Boolean
    add("databricks", "BOOLEAN", "BooleanType", "all", notes="Boolean value")

    # Date/Time
    add("databricks", "DATE", "DateType", "all", notes="Calendar date")
    add("databricks", "TIMESTAMP", "TimestampType", "all", notes="Timestamp with local TZ")
    add("databricks", "TIMESTAMP_LTZ", "TimestampType", "all", notes="Timestamp local TZ")
    add("databricks", "TIMESTAMP_NTZ", "TimestampType", "3.x", notes="No timezone (Spark 3.x)")
    add("databricks", "TIMESTAMP_NTZ", "TimestampNTZType", "4.x", notes="No timezone (Spark 4.x)")

    # Interval
    add("databricks", "INTERVAL", "StringType", "all", notes="Time interval")
    add("databricks", "INTERVAL YEAR", "YearMonthIntervalType", "all", notes="Year interval")
    add("databricks", "INTERVAL MONTH", "YearMonthIntervalType", "all", notes="Month interval")
    add("databricks", "INTERVAL DAY", "DayTimeIntervalType", "all", notes="Day interval")
    add("databricks", "INTERVAL HOUR", "DayTimeIntervalType", "all", notes="Hour interval")
    add("databricks", "INTERVAL MINUTE", "DayTimeIntervalType", "all", notes="Minute interval")
    add("databricks", "INTERVAL SECOND", "DayTimeIntervalType", "all", notes="Second interval")

    # Complex types
    add("databricks", "ARRAY", "ArrayType", "all", True, notes="Array of elements")
    add("databricks", "MAP", "MapType", "all", True, notes="Key-value map")
    add("databricks", "STRUCT", "StructType", "all", True, notes="Structured record")

    # Variant (Spark 4.0)
    add("databricks", "VARIANT", "StringType", "3.x", notes="Semi-structured (Spark 3.x)")
    add("databricks", "VARIANT", "VariantType", "4.x", notes="Semi-structured (Spark 4.x)")

# =============================================================================
# ORACLE
# =============================================================================
def add_oracle_types():
    # Numeric
    add("oracle", "NUMBER", "DecimalType", "all", notes="Numeric with precision/scale")
    add("oracle", "FLOAT", "DoubleType", "all", notes="Floating point (126 binary)")
    add("oracle", "BINARY_FLOAT", "FloatType", "all", notes="32-bit IEEE float")
    add("oracle", "BINARY_DOUBLE", "DoubleType", "all", notes="64-bit IEEE double")

    # Integer (Oracle doesn't have true integers, uses NUMBER)
    add("oracle", "INTEGER", "DecimalType", "all", notes="NUMBER(38)")
    add("oracle", "INT", "DecimalType", "all", notes="Alias for INTEGER")
    add("oracle", "SMALLINT", "DecimalType", "all", notes="NUMBER(38)")

    # Character
    add("oracle", "CHAR", "StringType", "all", notes="Fixed-length character (2000)")
    add("oracle", "NCHAR", "StringType", "all", notes="Fixed-length national char")
    add("oracle", "VARCHAR2", "StringType", "all", notes="Variable-length string (4000)")
    add("oracle", "NVARCHAR2", "StringType", "all", notes="Variable-length national")
    add("oracle", "VARCHAR", "StringType", "all", notes="Alias for VARCHAR2")
    add("oracle", "LONG", "StringType", "all", notes="Variable-length (deprecated)")
    add("oracle", "CLOB", "StringType", "all", notes="Character large object")
    add("oracle", "NCLOB", "StringType", "all", notes="National CLOB")

    # Binary
    add("oracle", "RAW", "BinaryType", "all", notes="Raw binary (2000)")
    add("oracle", "LONG RAW", "BinaryType", "all", notes="Long raw (deprecated)")
    add("oracle", "BLOB", "BinaryType", "all", notes="Binary large object")
    add("oracle", "BFILE", "StringType", "all", notes="External file reference")

    # Date/Time
    add("oracle", "DATE", "TimestampType", "all", notes="Date with time component")
    add("oracle", "TIMESTAMP", "TimestampType", "all", notes="Timestamp no timezone")
    add("oracle", "TIMESTAMP WITH TIME ZONE", "TimestampType", "all", notes="With timezone")
    add("oracle", "TIMESTAMP WITH LOCAL TIME ZONE", "TimestampType", "all", notes="Local TZ")

    # Interval
    add("oracle", "INTERVAL YEAR TO MONTH", "StringType", "all", notes="Year-month interval")
    add("oracle", "INTERVAL DAY TO SECOND", "StringType", "all", notes="Day-time interval")

    # ROWID
    add("oracle", "ROWID", "StringType", "all", notes="Row address")
    add("oracle", "UROWID", "StringType", "all", notes="Universal ROWID")

    # JSON (Oracle 21c+)
    add("oracle", "JSON", "StringType", "3.x", notes="JSON data (Spark 3.x)")
    add("oracle", "JSON", "VariantType", "4.x", notes="JSON data (Spark 4.x)")

    # XMLType
    add("oracle", "XMLTYPE", "StringType", "all", notes="XML data")
    add("oracle", "SYS.XMLTYPE", "StringType", "all", notes="XML data (fully qualified)")

    # SDO_GEOMETRY (spatial)
    add("oracle", "SDO_GEOMETRY", "StringType", "all", notes="Spatial geometry")
    add("oracle", "MDSYS.SDO_GEOMETRY", "StringType", "all", notes="Spatial (qualified)")

# =============================================================================
# SQL SERVER (and Azure Synapse, Azure SQL)
# =============================================================================
def add_sqlserver_types():
    # Exact numerics
    add("sqlserver", "BIT", "BooleanType", "all", notes="Boolean (0 or 1)")
    add("sqlserver", "TINYINT", "ShortType", "all", notes="0 to 255")
    add("sqlserver", "SMALLINT", "ShortType", "all", notes="16-bit signed")
    add("sqlserver", "INT", "IntegerType", "all", notes="32-bit signed")
    add("sqlserver", "INTEGER", "IntegerType", "all", notes="Alias for INT")
    add("sqlserver", "BIGINT", "LongType", "all", notes="64-bit signed")
    add("sqlserver", "DECIMAL", "DecimalType", "all", notes="Exact numeric (38,38)")
    add("sqlserver", "DEC", "DecimalType", "all", notes="Alias for DECIMAL")
    add("sqlserver", "NUMERIC", "DecimalType", "all", notes="Alias for DECIMAL")
    add("sqlserver", "MONEY", "DecimalType", "all", notes="Currency (-2^63 to 2^63)")
    add("sqlserver", "SMALLMONEY", "DecimalType", "all", notes="Small currency")

    # Approximate numerics
    add("sqlserver", "FLOAT", "DoubleType", "all", notes="64-bit floating point")
    add("sqlserver", "REAL", "FloatType", "all", notes="32-bit floating point")

    # Character strings
    add("sqlserver", "CHAR", "StringType", "all", notes="Fixed-length (8000)")
    add("sqlserver", "VARCHAR", "StringType", "all", notes="Variable-length (8000)")
    add("sqlserver", "VARCHAR(MAX)", "StringType", "all", notes="Variable-length (2GB)")
    add("sqlserver", "TEXT", "StringType", "all", notes="Variable-length (deprecated)")

    # Unicode character strings
    add("sqlserver", "NCHAR", "StringType", "all", notes="Fixed-length Unicode (4000)")
    add("sqlserver", "NVARCHAR", "StringType", "all", notes="Variable Unicode (4000)")
    add("sqlserver", "NVARCHAR(MAX)", "StringType", "all", notes="Variable Unicode (2GB)")
    add("sqlserver", "NTEXT", "StringType", "all", notes="Unicode text (deprecated)")

    # Binary strings
    add("sqlserver", "BINARY", "BinaryType", "all", notes="Fixed-length binary (8000)")
    add("sqlserver", "VARBINARY", "BinaryType", "all", notes="Variable binary (8000)")
    add("sqlserver", "VARBINARY(MAX)", "BinaryType", "all", notes="Variable binary (2GB)")
    add("sqlserver", "IMAGE", "BinaryType", "all", notes="Binary (deprecated)")

    # Date and time
    add("sqlserver", "DATE", "DateType", "all", notes="Date only")
    add("sqlserver", "TIME", "StringType", "all", notes="Time only")
    add("sqlserver", "DATETIME", "TimestampType", "all", notes="Date and time")
    add("sqlserver", "DATETIME2", "TimestampType", "all", notes="High precision datetime")
    add("sqlserver", "SMALLDATETIME", "TimestampType", "all", notes="Low precision datetime")
    add("sqlserver", "DATETIMEOFFSET", "TimestampType", "all", notes="Datetime with timezone")

    # Other
    add("sqlserver", "UNIQUEIDENTIFIER", "StringType", "all", notes="GUID/UUID")
    add("sqlserver", "SQL_VARIANT", "StringType", "all", notes="Variant type")
    add("sqlserver", "XML", "StringType", "all", notes="XML data")
    add("sqlserver", "GEOGRAPHY", "BinaryType", "all", notes="Geographic data")
    add("sqlserver", "GEOMETRY", "BinaryType", "all", notes="Geometric data")
    add("sqlserver", "HIERARCHYID", "BinaryType", "all", notes="Hierarchy position")

    # JSON (SQL Server 2016+, stored as NVARCHAR)
    # Note: JSON is not a native type in SQL Server, but queries return it
    add("sqlserver", "JSON", "StringType", "3.x", notes="JSON output (Spark 3.x)")
    add("sqlserver", "JSON", "VariantType", "4.x", notes="JSON output (Spark 4.x)")

# =============================================================================
# CLICKHOUSE
# =============================================================================
def add_clickhouse_types():
    # Integer types
    add("clickhouse", "Int8", "ByteType", "all", notes="8-bit signed")
    add("clickhouse", "Int16", "ShortType", "all", notes="16-bit signed")
    add("clickhouse", "Int32", "IntegerType", "all", notes="32-bit signed")
    add("clickhouse", "Int64", "LongType", "all", notes="64-bit signed")
    add("clickhouse", "Int128", "DecimalType", "all", notes="128-bit signed")
    add("clickhouse", "Int256", "DecimalType", "all", notes="256-bit signed")
    add("clickhouse", "UInt8", "ShortType", "all", notes="8-bit unsigned")
    add("clickhouse", "UInt16", "IntegerType", "all", notes="16-bit unsigned")
    add("clickhouse", "UInt32", "LongType", "all", notes="32-bit unsigned")
    add("clickhouse", "UInt64", "DecimalType", "all", notes="64-bit unsigned")
    add("clickhouse", "UInt128", "DecimalType", "all", notes="128-bit unsigned")
    add("clickhouse", "UInt256", "DecimalType", "all", notes="256-bit unsigned")

    # Floating point
    add("clickhouse", "Float32", "FloatType", "all", notes="32-bit IEEE float")
    add("clickhouse", "Float64", "DoubleType", "all", notes="64-bit IEEE double")

    # Decimal
    add("clickhouse", "Decimal", "DecimalType", "all", notes="Fixed-point decimal")
    add("clickhouse", "Decimal32", "DecimalType", "all", notes="Decimal(9, S)")
    add("clickhouse", "Decimal64", "DecimalType", "all", notes="Decimal(18, S)")
    add("clickhouse", "Decimal128", "DecimalType", "all", notes="Decimal(38, S)")
    add("clickhouse", "Decimal256", "DecimalType", "all", notes="Decimal(76, S)")

    # Boolean
    add("clickhouse", "Bool", "BooleanType", "all", notes="Boolean")

    # String
    add("clickhouse", "String", "StringType", "all", notes="Arbitrary length")
    add("clickhouse", "FixedString", "StringType", "all", notes="Fixed length")

    # Date/Time
    add("clickhouse", "Date", "DateType", "all", notes="Days since 1970")
    add("clickhouse", "Date32", "DateType", "all", notes="Extended date range")
    add("clickhouse", "DateTime", "TimestampType", "all", notes="Unix timestamp")
    add("clickhouse", "DateTime64", "TimestampType", "all", notes="High precision")

    # UUID
    add("clickhouse", "UUID", "StringType", "all", notes="UUID value")

    # Enum
    add("clickhouse", "Enum8", "StringType", "all", notes="Enum with 8-bit index")
    add("clickhouse", "Enum16", "StringType", "all", notes="Enum with 16-bit index")

    # Array
    add("clickhouse", "Array", "ArrayType", "all", True, notes="Array type")

    # Tuple
    add("clickhouse", "Tuple", "StructType", "all", True, notes="Named tuple")

    # Map
    add("clickhouse", "Map", "MapType", "all", True, notes="Key-value map")

    # Nested
    add("clickhouse", "Nested", "ArrayType", "all", True, notes="Nested structure")

    # JSON
    add("clickhouse", "JSON", "StringType", "3.x", notes="JSON object (Spark 3.x)")
    add("clickhouse", "JSON", "VariantType", "4.x", notes="JSON object (Spark 4.x)")

    # IP addresses
    add("clickhouse", "IPv4", "StringType", "all", notes="IPv4 address")
    add("clickhouse", "IPv6", "StringType", "all", notes="IPv6 address")

    # Geo
    add("clickhouse", "Point", "ArrayType", "all", True, notes="X,Y coordinates")
    add("clickhouse", "Ring", "ArrayType", "all", True, notes="Polygon ring")
    add("clickhouse", "Polygon", "ArrayType", "all", True, notes="Polygon")
    add("clickhouse", "MultiPolygon", "ArrayType", "all", True, notes="Multi-polygon")

    # Nullable wrapper (handled separately)
    add("clickhouse", "Nullable", "NullType", "all", notes="Nullable wrapper")

    # LowCardinality (handled separately)
    add("clickhouse", "LowCardinality", "StringType", "all", notes="Dictionary encoded")

# =============================================================================
# TRINO / PRESTO (Athena, Starburst)
# =============================================================================
def add_trino_types():
    # Boolean
    add("trino", "BOOLEAN", "BooleanType", "all", notes="Boolean value")

    # Integer types
    add("trino", "TINYINT", "ByteType", "all", notes="8-bit signed")
    add("trino", "SMALLINT", "ShortType", "all", notes="16-bit signed")
    add("trino", "INTEGER", "IntegerType", "all", notes="32-bit signed")
    add("trino", "INT", "IntegerType", "all", notes="Alias for INTEGER")
    add("trino", "BIGINT", "LongType", "all", notes="64-bit signed")

    # Floating point
    add("trino", "REAL", "FloatType", "all", notes="32-bit IEEE float")
    add("trino", "DOUBLE", "DoubleType", "all", notes="64-bit IEEE double")

    # Decimal
    add("trino", "DECIMAL", "DecimalType", "all", notes="Fixed-point decimal")

    # String
    add("trino", "VARCHAR", "StringType", "all", notes="Variable-length string")
    add("trino", "CHAR", "StringType", "all", notes="Fixed-length string")

    # Binary
    add("trino", "VARBINARY", "BinaryType", "all", notes="Variable-length binary")

    # Date/Time
    add("trino", "DATE", "DateType", "all", notes="Calendar date")
    add("trino", "TIME", "StringType", "all", notes="Time without timezone")
    add("trino", "TIME WITH TIME ZONE", "StringType", "all", notes="Time with TZ")
    add("trino", "TIMESTAMP", "TimestampType", "3.x", notes="Timestamp no TZ (Spark 3.x)")
    add("trino", "TIMESTAMP", "TimestampNTZType", "4.x", notes="Timestamp no TZ (Spark 4.x)")
    add("trino", "TIMESTAMP WITH TIME ZONE", "TimestampType", "all", notes="With timezone")

    # Interval
    add("trino", "INTERVAL YEAR TO MONTH", "StringType", "all", notes="Year-month interval")
    add("trino", "INTERVAL DAY TO SECOND", "StringType", "all", notes="Day-time interval")

    # Complex types
    add("trino", "ARRAY", "ArrayType", "all", True, notes="Array of elements")
    add("trino", "MAP", "MapType", "all", True, notes="Key-value map")
    add("trino", "ROW", "StructType", "all", True, notes="Structured row")

    # JSON
    add("trino", "JSON", "StringType", "3.x", notes="JSON value (Spark 3.x)")
    add("trino", "JSON", "VariantType", "4.x", notes="JSON value (Spark 4.x)")

    # IP address
    add("trino", "IPADDRESS", "StringType", "all", notes="IP address")

    # UUID
    add("trino", "UUID", "StringType", "all", notes="UUID value")

    # HyperLogLog
    add("trino", "HYPERLOGLOG", "BinaryType", "all", notes="HLL sketch")
    add("trino", "P4HYPERLOGLOG", "BinaryType", "all", notes="P4 HLL sketch")

    # Set Digest
    add("trino", "SETDIGEST", "BinaryType", "all", notes="Set digest")

    # QDigest
    add("trino", "QDIGEST", "BinaryType", "all", notes="Quantile digest")
    add("trino", "TDIGEST", "BinaryType", "all", notes="T-Digest")

    # Geometry
    add("trino", "GEOMETRY", "BinaryType", "all", notes="Geometry")
    add("trino", "SPHERICALGEOGRAPHY", "BinaryType", "all", notes="Spherical geography")

# Add aliases for Athena (Presto-based)
def add_athena_types():
    """Athena uses Presto/Trino types - copy from trino with athena adapter name."""
    # Get all trino mappings and duplicate for athena
    trino_mappings = [(m[0], m[1], m[2], m[3], m[4], m[5], m[6])
                      for m in MAPPINGS if m[0] == "trino"]
    for m in trino_mappings:
        add("athena", m[1], m[2], m[3], m[4], m[5], m[6])

# =============================================================================
# DUCKDB
# =============================================================================
def add_duckdb_types():
    # Boolean
    add("duckdb", "BOOLEAN", "BooleanType", "all", notes="Boolean value")
    add("duckdb", "BOOL", "BooleanType", "all", notes="Alias for BOOLEAN")

    # Integer types
    add("duckdb", "TINYINT", "ByteType", "all", notes="8-bit signed")
    add("duckdb", "INT1", "ByteType", "all", notes="Alias for TINYINT")
    add("duckdb", "SMALLINT", "ShortType", "all", notes="16-bit signed")
    add("duckdb", "INT2", "ShortType", "all", notes="Alias for SMALLINT")
    add("duckdb", "INTEGER", "IntegerType", "all", notes="32-bit signed")
    add("duckdb", "INT", "IntegerType", "all", notes="Alias for INTEGER")
    add("duckdb", "INT4", "IntegerType", "all", notes="Alias for INTEGER")
    add("duckdb", "BIGINT", "LongType", "all", notes="64-bit signed")
    add("duckdb", "INT8", "LongType", "all", notes="Alias for BIGINT")
    add("duckdb", "HUGEINT", "DecimalType", "all", notes="128-bit signed")
    add("duckdb", "UHUGEINT", "DecimalType", "all", notes="128-bit unsigned")
    add("duckdb", "UTINYINT", "ShortType", "all", notes="8-bit unsigned")
    add("duckdb", "USMALLINT", "IntegerType", "all", notes="16-bit unsigned")
    add("duckdb", "UINTEGER", "LongType", "all", notes="32-bit unsigned")
    add("duckdb", "UBIGINT", "DecimalType", "all", notes="64-bit unsigned")

    # Floating point
    add("duckdb", "REAL", "FloatType", "all", notes="32-bit IEEE float")
    add("duckdb", "FLOAT4", "FloatType", "all", notes="Alias for REAL")
    add("duckdb", "FLOAT", "FloatType", "all", notes="Alias for REAL")
    add("duckdb", "DOUBLE", "DoubleType", "all", notes="64-bit IEEE double")
    add("duckdb", "FLOAT8", "DoubleType", "all", notes="Alias for DOUBLE")

    # Decimal
    add("duckdb", "DECIMAL", "DecimalType", "all", notes="Fixed-point decimal")
    add("duckdb", "NUMERIC", "DecimalType", "all", notes="Alias for DECIMAL")

    # String
    add("duckdb", "VARCHAR", "StringType", "all", notes="Variable-length string")
    add("duckdb", "CHAR", "StringType", "all", notes="Fixed-length string")
    add("duckdb", "BPCHAR", "StringType", "all", notes="Blank-padded char")
    add("duckdb", "TEXT", "StringType", "all", notes="Alias for VARCHAR")
    add("duckdb", "STRING", "StringType", "all", notes="Alias for VARCHAR")

    # Binary
    add("duckdb", "BLOB", "BinaryType", "all", notes="Binary data")
    add("duckdb", "BYTEA", "BinaryType", "all", notes="Alias for BLOB")
    add("duckdb", "BINARY", "BinaryType", "all", notes="Alias for BLOB")
    add("duckdb", "VARBINARY", "BinaryType", "all", notes="Alias for BLOB")

    # Date/Time
    add("duckdb", "DATE", "DateType", "all", notes="Calendar date")
    add("duckdb", "TIME", "StringType", "all", notes="Time of day")
    add("duckdb", "TIMESTAMP", "TimestampType", "all", notes="Timestamp")
    add("duckdb", "TIMESTAMPTZ", "TimestampType", "all", notes="With timezone")
    add("duckdb", "TIMESTAMP WITH TIME ZONE", "TimestampType", "all", notes="With TZ")

    # Interval
    add("duckdb", "INTERVAL", "StringType", "all", notes="Time interval")

    # UUID
    add("duckdb", "UUID", "StringType", "all", notes="UUID value")

    # Complex types
    add("duckdb", "LIST", "ArrayType", "all", True, notes="List/array type")
    add("duckdb", "STRUCT", "StructType", "all", True, notes="Struct type")
    add("duckdb", "MAP", "MapType", "all", True, notes="Map type")
    add("duckdb", "UNION", "StructType", "all", True, notes="Union type")

    # JSON (stored as structured)
    add("duckdb", "JSON", "StringType", "3.x", notes="JSON (Spark 3.x)")
    add("duckdb", "JSON", "VariantType", "4.x", notes="JSON (Spark 4.x)")

    # Enum
    add("duckdb", "ENUM", "StringType", "all", notes="Enumeration")

    # Bit
    add("duckdb", "BIT", "StringType", "all", notes="Bit string")
    add("duckdb", "BITSTRING", "StringType", "all", notes="Alias for BIT")

# =============================================================================
# TERADATA
# =============================================================================
def add_teradata_types():
    # Integer types
    add("teradata", "BYTEINT", "ByteType", "all", notes="8-bit signed")
    add("teradata", "SMALLINT", "ShortType", "all", notes="16-bit signed")
    add("teradata", "INTEGER", "IntegerType", "all", notes="32-bit signed")
    add("teradata", "INT", "IntegerType", "all", notes="Alias for INTEGER")
    add("teradata", "BIGINT", "LongType", "all", notes="64-bit signed")

    # Decimal
    add("teradata", "DECIMAL", "DecimalType", "all", notes="Fixed-point (18,0)")
    add("teradata", "NUMERIC", "DecimalType", "all", notes="Alias for DECIMAL")
    add("teradata", "NUMBER", "DecimalType", "all", notes="Variable precision")

    # Floating point
    add("teradata", "REAL", "FloatType", "all", notes="32-bit IEEE")
    add("teradata", "FLOAT", "DoubleType", "all", notes="64-bit IEEE")
    add("teradata", "DOUBLE PRECISION", "DoubleType", "all", notes="Alias for FLOAT")

    # Character
    add("teradata", "CHAR", "StringType", "all", notes="Fixed-length (64000)")
    add("teradata", "CHARACTER", "StringType", "all", notes="Alias for CHAR")
    add("teradata", "VARCHAR", "StringType", "all", notes="Variable-length (64000)")
    add("teradata", "CHARACTER VARYING", "StringType", "all", notes="Alias for VARCHAR")
    add("teradata", "LONG VARCHAR", "StringType", "all", notes="Extended varchar")
    add("teradata", "CLOB", "StringType", "all", notes="Character LOB (2GB)")

    # Binary
    add("teradata", "BYTE", "BinaryType", "all", notes="Fixed-length binary")
    add("teradata", "VARBYTE", "BinaryType", "all", notes="Variable binary")
    add("teradata", "BLOB", "BinaryType", "all", notes="Binary LOB (2GB)")

    # Date/Time
    add("teradata", "DATE", "DateType", "all", notes="Calendar date")
    add("teradata", "TIME", "StringType", "all", notes="Time of day")
    add("teradata", "TIME WITH TIME ZONE", "StringType", "all", notes="Time with TZ")
    add("teradata", "TIMESTAMP", "TimestampType", "all", notes="Timestamp")
    add("teradata", "TIMESTAMP WITH TIME ZONE", "TimestampType", "all", notes="With TZ")

    # Interval
    add("teradata", "INTERVAL YEAR", "StringType", "all", notes="Year interval")
    add("teradata", "INTERVAL MONTH", "StringType", "all", notes="Month interval")
    add("teradata", "INTERVAL DAY", "StringType", "all", notes="Day interval")
    add("teradata", "INTERVAL HOUR", "StringType", "all", notes="Hour interval")
    add("teradata", "INTERVAL MINUTE", "StringType", "all", notes="Minute interval")
    add("teradata", "INTERVAL SECOND", "StringType", "all", notes="Second interval")
    add("teradata", "INTERVAL YEAR TO MONTH", "StringType", "all", notes="Year-month")
    add("teradata", "INTERVAL DAY TO HOUR", "StringType", "all", notes="Day-hour")
    add("teradata", "INTERVAL DAY TO MINUTE", "StringType", "all", notes="Day-minute")
    add("teradata", "INTERVAL DAY TO SECOND", "StringType", "all", notes="Day-second")
    add("teradata", "INTERVAL HOUR TO MINUTE", "StringType", "all", notes="Hour-minute")
    add("teradata", "INTERVAL HOUR TO SECOND", "StringType", "all", notes="Hour-second")
    add("teradata", "INTERVAL MINUTE TO SECOND", "StringType", "all", notes="Minute-second")

    # Period
    add("teradata", "PERIOD(DATE)", "StringType", "all", notes="Date period")
    add("teradata", "PERIOD(TIME)", "StringType", "all", notes="Time period")
    add("teradata", "PERIOD(TIMESTAMP)", "StringType", "all", notes="Timestamp period")

    # JSON
    add("teradata", "JSON", "StringType", "3.x", notes="JSON (Spark 3.x)")
    add("teradata", "JSON", "VariantType", "4.x", notes="JSON (Spark 4.x)")

    # XML
    add("teradata", "XML", "StringType", "all", notes="XML document")

    # Geospatial
    add("teradata", "ST_GEOMETRY", "BinaryType", "all", notes="Geometry")
    add("teradata", "MBR", "BinaryType", "all", notes="Minimum bounding rectangle")

# =============================================================================
# VERTICA
# =============================================================================
def add_vertica_types():
    # Integer types
    add("vertica", "INTEGER", "IntegerType", "all", notes="32-bit or 64-bit (precision)")
    add("vertica", "INT", "IntegerType", "all", notes="Alias for INTEGER")
    add("vertica", "BIGINT", "LongType", "all", notes="64-bit signed")
    add("vertica", "INT8", "LongType", "all", notes="Alias for BIGINT")
    add("vertica", "SMALLINT", "ShortType", "all", notes="16-bit signed")
    add("vertica", "TINYINT", "ByteType", "all", notes="8-bit signed")

    # Decimal
    add("vertica", "NUMERIC", "DecimalType", "all", notes="Exact numeric")
    add("vertica", "DECIMAL", "DecimalType", "all", notes="Alias for NUMERIC")
    add("vertica", "NUMBER", "DecimalType", "all", notes="Alias for NUMERIC")
    add("vertica", "MONEY", "DecimalType", "all", notes="Currency type")

    # Floating point
    add("vertica", "DOUBLE PRECISION", "DoubleType", "all", notes="64-bit float")
    add("vertica", "FLOAT", "DoubleType", "all", notes="Alias for DOUBLE")
    add("vertica", "FLOAT8", "DoubleType", "all", notes="Alias for DOUBLE")
    add("vertica", "REAL", "DoubleType", "all", notes="Alias for DOUBLE")

    # Boolean
    add("vertica", "BOOLEAN", "BooleanType", "all", notes="Boolean value")

    # Character
    add("vertica", "CHAR", "StringType", "all", notes="Fixed-length (65000)")
    add("vertica", "VARCHAR", "StringType", "all", notes="Variable-length (65000)")
    add("vertica", "LONG VARCHAR", "StringType", "all", notes="Extended varchar")

    # Binary
    add("vertica", "BINARY", "BinaryType", "all", notes="Fixed-length binary")
    add("vertica", "VARBINARY", "BinaryType", "all", notes="Variable binary")
    add("vertica", "LONG VARBINARY", "BinaryType", "all", notes="Extended binary")
    add("vertica", "BYTEA", "BinaryType", "all", notes="Alias for VARBINARY")
    add("vertica", "RAW", "BinaryType", "all", notes="Alias for VARBINARY")

    # Date/Time
    add("vertica", "DATE", "DateType", "all", notes="Calendar date")
    add("vertica", "TIME", "StringType", "all", notes="Time of day")
    add("vertica", "TIME WITH TIMEZONE", "StringType", "all", notes="Time with TZ")
    add("vertica", "TIMETZ", "StringType", "all", notes="Alias for TIME WITH TZ")
    add("vertica", "TIMESTAMP", "TimestampType", "all", notes="Timestamp")
    add("vertica", "TIMESTAMP WITH TIMEZONE", "TimestampType", "all", notes="With TZ")
    add("vertica", "TIMESTAMPTZ", "TimestampType", "all", notes="Alias for WITH TZ")
    add("vertica", "DATETIME", "TimestampType", "all", notes="Alias for TIMESTAMP")
    add("vertica", "SMALLDATETIME", "TimestampType", "all", notes="Minute precision")

    # Interval
    add("vertica", "INTERVAL", "StringType", "all", notes="Time interval")
    add("vertica", "INTERVAL DAY TO SECOND", "StringType", "all", notes="Day-time")
    add("vertica", "INTERVAL YEAR TO MONTH", "StringType", "all", notes="Year-month")

    # UUID
    add("vertica", "UUID", "StringType", "all", notes="UUID value")

    # Complex types
    add("vertica", "ARRAY", "ArrayType", "all", True, notes="Array type")
    add("vertica", "SET", "ArrayType", "all", True, notes="Set type")
    add("vertica", "ROW", "StructType", "all", True, notes="Row type")
    add("vertica", "MAP", "MapType", "all", True, notes="Map type")

    # Geospatial
    add("vertica", "GEOMETRY", "BinaryType", "all", notes="Geometry")
    add("vertica", "GEOGRAPHY", "BinaryType", "all", notes="Geography")

# =============================================================================
# HIVE
# =============================================================================
def add_hive_types():
    # Numeric types
    add("hive", "TINYINT", "ByteType", "all", notes="8-bit signed")
    add("hive", "SMALLINT", "ShortType", "all", notes="16-bit signed")
    add("hive", "INT", "IntegerType", "all", notes="32-bit signed")
    add("hive", "INTEGER", "IntegerType", "all", notes="Alias for INT")
    add("hive", "BIGINT", "LongType", "all", notes="64-bit signed")

    # Floating point
    add("hive", "FLOAT", "FloatType", "all", notes="32-bit IEEE")
    add("hive", "DOUBLE", "DoubleType", "all", notes="64-bit IEEE")
    add("hive", "DOUBLE PRECISION", "DoubleType", "all", notes="Alias for DOUBLE")

    # Decimal
    add("hive", "DECIMAL", "DecimalType", "all", notes="Fixed-point decimal")
    add("hive", "NUMERIC", "DecimalType", "all", notes="Alias for DECIMAL")

    # String
    add("hive", "STRING", "StringType", "all", notes="Unbounded string")
    add("hive", "VARCHAR", "StringType", "all", notes="Variable-length (65535)")
    add("hive", "CHAR", "StringType", "all", notes="Fixed-length (255)")

    # Binary
    add("hive", "BINARY", "BinaryType", "all", notes="Binary data")

    # Boolean
    add("hive", "BOOLEAN", "BooleanType", "all", notes="Boolean value")

    # Date/Time
    add("hive", "DATE", "DateType", "all", notes="Calendar date")
    add("hive", "TIMESTAMP", "TimestampType", "all", notes="Timestamp")
    add("hive", "INTERVAL", "StringType", "all", notes="Time interval")

    # Complex types
    add("hive", "ARRAY", "ArrayType", "all", True, notes="Array type")
    add("hive", "MAP", "MapType", "all", True, notes="Key-value map")
    add("hive", "STRUCT", "StructType", "all", True, notes="Struct type")
    add("hive", "UNIONTYPE", "StructType", "all", True, notes="Union type")

# =============================================================================
# DB2
# =============================================================================
def add_db2_types():
    # Integer types
    add("db2", "SMALLINT", "ShortType", "all", notes="16-bit signed")
    add("db2", "INTEGER", "IntegerType", "all", notes="32-bit signed")
    add("db2", "INT", "IntegerType", "all", notes="Alias for INTEGER")
    add("db2", "BIGINT", "LongType", "all", notes="64-bit signed")

    # Decimal
    add("db2", "DECIMAL", "DecimalType", "all", notes="Exact numeric (31,31)")
    add("db2", "DEC", "DecimalType", "all", notes="Alias for DECIMAL")
    add("db2", "NUMERIC", "DecimalType", "all", notes="Alias for DECIMAL")
    add("db2", "NUM", "DecimalType", "all", notes="Alias for DECIMAL")

    # Floating point
    add("db2", "REAL", "FloatType", "all", notes="32-bit IEEE")
    add("db2", "DOUBLE", "DoubleType", "all", notes="64-bit IEEE")
    add("db2", "DOUBLE PRECISION", "DoubleType", "all", notes="Alias for DOUBLE")
    add("db2", "FLOAT", "DoubleType", "all", notes="Alias for DOUBLE")
    add("db2", "DECFLOAT", "DecimalType", "all", notes="Decimal floating point")

    # Character
    add("db2", "CHAR", "StringType", "all", notes="Fixed-length (254)")
    add("db2", "CHARACTER", "StringType", "all", notes="Alias for CHAR")
    add("db2", "VARCHAR", "StringType", "all", notes="Variable-length (32672)")
    add("db2", "CHARACTER VARYING", "StringType", "all", notes="Alias for VARCHAR")
    add("db2", "LONG VARCHAR", "StringType", "all", notes="Long varchar (32700)")
    add("db2", "CLOB", "StringType", "all", notes="Character LOB (2GB)")
    add("db2", "DBCLOB", "StringType", "all", notes="Double-byte CLOB")

    # Graphic (DBCS)
    add("db2", "GRAPHIC", "StringType", "all", notes="Fixed DBCS (127)")
    add("db2", "VARGRAPHIC", "StringType", "all", notes="Variable DBCS (16336)")
    add("db2", "LONG VARGRAPHIC", "StringType", "all", notes="Long DBCS (16350)")

    # Binary
    add("db2", "BINARY", "BinaryType", "all", notes="Fixed-length (254)")
    add("db2", "VARBINARY", "BinaryType", "all", notes="Variable binary (32672)")
    add("db2", "BLOB", "BinaryType", "all", notes="Binary LOB (2GB)")

    # Boolean - Spark 4.0 changed DB2 BOOLEAN mapping
    add("db2", "BOOLEAN", "StringType", "3.x", notes="Boolean as CHAR(1) (Spark 3.x)")
    add("db2", "BOOLEAN", "BooleanType", "4.x", notes="Boolean (Spark 4.x)")

    # Date/Time
    add("db2", "DATE", "DateType", "all", notes="Calendar date")
    add("db2", "TIME", "StringType", "all", notes="Time of day")
    add("db2", "TIMESTAMP", "TimestampType", "all", notes="Timestamp")

    # XML
    add("db2", "XML", "StringType", "all", notes="XML document")

    # Row ID
    add("db2", "ROWID", "BinaryType", "all", notes="Row identifier")

# =============================================================================
# SQLITE
# =============================================================================
def add_sqlite_types():
    # SQLite has dynamic typing with 5 storage classes
    # INTEGER
    add("sqlite", "INTEGER", "LongType", "all", notes="64-bit signed integer")
    add("sqlite", "INT", "LongType", "all", notes="Alias for INTEGER")
    add("sqlite", "TINYINT", "LongType", "all", notes="Stored as INTEGER")
    add("sqlite", "SMALLINT", "LongType", "all", notes="Stored as INTEGER")
    add("sqlite", "MEDIUMINT", "LongType", "all", notes="Stored as INTEGER")
    add("sqlite", "BIGINT", "LongType", "all", notes="Stored as INTEGER")
    add("sqlite", "UNSIGNED BIG INT", "LongType", "all", notes="Stored as INTEGER")
    add("sqlite", "INT2", "LongType", "all", notes="Stored as INTEGER")
    add("sqlite", "INT8", "LongType", "all", notes="Stored as INTEGER")

    # REAL
    add("sqlite", "REAL", "DoubleType", "all", notes="64-bit IEEE float")
    add("sqlite", "DOUBLE", "DoubleType", "all", notes="Stored as REAL")
    add("sqlite", "DOUBLE PRECISION", "DoubleType", "all", notes="Stored as REAL")
    add("sqlite", "FLOAT", "DoubleType", "all", notes="Stored as REAL")

    # TEXT
    add("sqlite", "TEXT", "StringType", "all", notes="Variable-length string")
    add("sqlite", "CHARACTER", "StringType", "all", notes="Stored as TEXT")
    add("sqlite", "VARCHAR", "StringType", "all", notes="Stored as TEXT")
    add("sqlite", "VARYING CHARACTER", "StringType", "all", notes="Stored as TEXT")
    add("sqlite", "NCHAR", "StringType", "all", notes="Stored as TEXT")
    add("sqlite", "NATIVE CHARACTER", "StringType", "all", notes="Stored as TEXT")
    add("sqlite", "NVARCHAR", "StringType", "all", notes="Stored as TEXT")
    add("sqlite", "CLOB", "StringType", "all", notes="Stored as TEXT")

    # BLOB
    add("sqlite", "BLOB", "BinaryType", "all", notes="Binary data")

    # NUMERIC (affinity)
    add("sqlite", "NUMERIC", "DecimalType", "all", notes="Numeric affinity")
    add("sqlite", "DECIMAL", "DecimalType", "all", notes="Stored as NUMERIC")
    add("sqlite", "BOOLEAN", "BooleanType", "all", notes="Stored as NUMERIC (0/1)")
    add("sqlite", "DATE", "DateType", "all", notes="Stored as TEXT/REAL/INT")
    add("sqlite", "DATETIME", "TimestampType", "all", notes="Stored as TEXT/REAL/INT")

    # JSON (stored as TEXT in SQLite, but parsed)
    add("sqlite", "JSON", "StringType", "3.x", notes="JSON as TEXT (Spark 3.x)")
    add("sqlite", "JSON", "VariantType", "4.x", notes="JSON (Spark 4.x)")

# =============================================================================
# SPARK (native types for completeness)
# =============================================================================
def add_spark_types():
    """Native Spark types for Spark-to-Spark operations."""
    add("spark", "ByteType", "ByteType", "all", notes="8-bit signed")
    add("spark", "ShortType", "ShortType", "all", notes="16-bit signed")
    add("spark", "IntegerType", "IntegerType", "all", notes="32-bit signed")
    add("spark", "LongType", "LongType", "all", notes="64-bit signed")
    add("spark", "FloatType", "FloatType", "all", notes="32-bit float")
    add("spark", "DoubleType", "DoubleType", "all", notes="64-bit float")
    add("spark", "DecimalType", "DecimalType", "all", notes="Arbitrary precision")
    add("spark", "StringType", "StringType", "all", notes="UTF-8 string")
    add("spark", "BinaryType", "BinaryType", "all", notes="Byte array")
    add("spark", "BooleanType", "BooleanType", "all", notes="Boolean")
    add("spark", "DateType", "DateType", "all", notes="Date")
    add("spark", "TimestampType", "TimestampType", "all", notes="Timestamp")
    add("spark", "TimestampNTZType", "TimestampNTZType", "4.x", notes="No TZ (Spark 3.4+)")
    add("spark", "ArrayType", "ArrayType", "all", True, notes="Array")
    add("spark", "MapType", "MapType", "all", True, notes="Map")
    add("spark", "StructType", "StructType", "all", True, notes="Struct")
    add("spark", "VariantType", "VariantType", "4.x", notes="Variant (Spark 4.0+)")
    add("spark", "YearMonthIntervalType", "YearMonthIntervalType", "all", notes="Year-month interval")
    add("spark", "DayTimeIntervalType", "DayTimeIntervalType", "all", notes="Day-time interval")
    add("spark", "NullType", "NullType", "all", notes="Null type")
    add("spark", "CalendarIntervalType", "CalendarIntervalType", "all", notes="Calendar interval")

# =============================================================================
# MAIN BUILD FUNCTION
# =============================================================================
def build_registry():
    """Build all type mappings."""
    print("Building comprehensive datatype mappings...")

    # Add all adapters
    add_postgres_types()
    print(f"  + postgres: {len([m for m in MAPPINGS if m[0] == 'postgres'])} types")

    add_mysql_types()
    print(f"  + mysql: {len([m for m in MAPPINGS if m[0] == 'mysql'])} types")

    add_bigquery_types()
    print(f"  + bigquery: {len([m for m in MAPPINGS if m[0] == 'bigquery'])} types")

    add_snowflake_types()
    print(f"  + snowflake: {len([m for m in MAPPINGS if m[0] == 'snowflake'])} types")

    add_redshift_types()
    print(f"  + redshift: {len([m for m in MAPPINGS if m[0] == 'redshift'])} types")

    add_databricks_types()
    print(f"  + databricks: {len([m for m in MAPPINGS if m[0] == 'databricks'])} types")

    add_oracle_types()
    print(f"  + oracle: {len([m for m in MAPPINGS if m[0] == 'oracle'])} types")

    add_sqlserver_types()
    print(f"  + sqlserver: {len([m for m in MAPPINGS if m[0] == 'sqlserver'])} types")

    add_clickhouse_types()
    print(f"  + clickhouse: {len([m for m in MAPPINGS if m[0] == 'clickhouse'])} types")

    add_trino_types()
    print(f"  + trino: {len([m for m in MAPPINGS if m[0] == 'trino'])} types")

    add_athena_types()
    print(f"  + athena: {len([m for m in MAPPINGS if m[0] == 'athena'])} types")

    add_duckdb_types()
    print(f"  + duckdb: {len([m for m in MAPPINGS if m[0] == 'duckdb'])} types")

    add_teradata_types()
    print(f"  + teradata: {len([m for m in MAPPINGS if m[0] == 'teradata'])} types")

    add_vertica_types()
    print(f"  + vertica: {len([m for m in MAPPINGS if m[0] == 'vertica'])} types")

    add_hive_types()
    print(f"  + hive: {len([m for m in MAPPINGS if m[0] == 'hive'])} types")

    add_db2_types()
    print(f"  + db2: {len([m for m in MAPPINGS if m[0] == 'db2'])} types")

    add_sqlite_types()
    print(f"  + sqlite: {len([m for m in MAPPINGS if m[0] == 'sqlite'])} types")

    add_spark_types()
    print(f"  + spark: {len([m for m in MAPPINGS if m[0] == 'spark'])} types")

    print(f"\nTotal: {len(MAPPINGS)} type mappings across {len(set(m[0] for m in MAPPINGS))} adapters")

    return MAPPINGS


def save_to_duckdb(db_path: str):
    """Save mappings to DuckDB."""
    mappings = build_registry()

    conn = duckdb.connect(db_path)

    # Drop and recreate table
    conn.execute("DROP TABLE IF EXISTS datatype_mappings")
    conn.execute("""
        CREATE TABLE datatype_mappings (
            adapter_name VARCHAR,
            adapter_type VARCHAR,
            spark_type VARCHAR,
            spark_version VARCHAR,
            is_complex BOOLEAN,
            cast_expression VARCHAR,
            notes VARCHAR
        )
    """)

    # Insert all mappings
    conn.executemany(
        "INSERT INTO datatype_mappings VALUES (?, ?, ?, ?, ?, ?, ?)",
        mappings
    )

    # Verify
    count = conn.execute("SELECT COUNT(*) FROM datatype_mappings").fetchone()[0]
    adapters = conn.execute("SELECT DISTINCT adapter_name FROM datatype_mappings ORDER BY adapter_name").fetchall()

    print(f"\nSaved to {db_path}")
    print(f"  - {count} total mappings")
    print(f"  - {len(adapters)} adapters: {', '.join(a[0] for a in adapters)}")

    # Version-specific stats
    v3_count = conn.execute("SELECT COUNT(*) FROM datatype_mappings WHERE spark_version = '3.x'").fetchone()[0]
    v4_count = conn.execute("SELECT COUNT(*) FROM datatype_mappings WHERE spark_version = '4.x'").fetchone()[0]
    all_count = conn.execute("SELECT COUNT(*) FROM datatype_mappings WHERE spark_version = 'all'").fetchone()[0]
    print(f"  - Version-specific: {v3_count} for Spark 3.x, {v4_count} for Spark 4.x, {all_count} for all versions")

    conn.close()


if __name__ == "__main__":
    import sys

    db_path = "adapters_registry.duckdb"
    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    save_to_duckdb(db_path)
