# =============================================================================
# DVT Global Registries
# =============================================================================
# Centralized lookup tables for type mappings and syntax rules.
# These are shipped with DVT and loaded into the project metadata store.
#
# DVT v0.54.0: Initial implementation
# =============================================================================

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class TypeMapping:
    """A single type mapping entry."""
    adapter_name: str
    adapter_native_type: str
    spark_version: str
    spark_native_type: str
    is_complex: bool = False
    cast_expression: Optional[str] = None


@dataclass
class SyntaxRule:
    """Syntax rules for a specific adapter."""
    adapter_name: str
    quote_start: str
    quote_end: str
    case_sensitivity: str  # 'LOWER', 'UPPER', 'PRESERVE'
    reserved_keywords: List[str]


class TypeRegistry:
    """
    Global type registry for mapping adapter types to Spark types.

    This registry is shipped with DVT and provides the definitive mapping
    between every supported adapter's native types and Spark's Catalyst types.
    """

    # ==========================================================================
    # Type Mappings: adapter_name -> adapter_type -> spark_version -> spark_type
    # ==========================================================================

    TYPE_MAPPINGS: List[Dict[str, Any]] = [
        # ======================================================================
        # PostgreSQL
        # ======================================================================
        # String types
        {"adapter_name": "postgres", "adapter_native_type": "TEXT", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "VARCHAR", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "CHARACTER VARYING", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "CHAR", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "CHARACTER", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "BPCHAR", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "NAME", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},

        # Integer types
        {"adapter_name": "postgres", "adapter_native_type": "INTEGER", "spark_version": "all", "spark_native_type": "IntegerType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "INT", "spark_version": "all", "spark_native_type": "IntegerType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "INT4", "spark_version": "all", "spark_native_type": "IntegerType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "SMALLINT", "spark_version": "all", "spark_native_type": "ShortType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "INT2", "spark_version": "all", "spark_native_type": "ShortType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "BIGINT", "spark_version": "all", "spark_native_type": "LongType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "INT8", "spark_version": "all", "spark_native_type": "LongType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "SERIAL", "spark_version": "all", "spark_native_type": "IntegerType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "BIGSERIAL", "spark_version": "all", "spark_native_type": "LongType", "is_complex": False},

        # Floating point types
        {"adapter_name": "postgres", "adapter_native_type": "REAL", "spark_version": "all", "spark_native_type": "FloatType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "FLOAT4", "spark_version": "all", "spark_native_type": "FloatType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "DOUBLE PRECISION", "spark_version": "all", "spark_native_type": "DoubleType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "FLOAT8", "spark_version": "all", "spark_native_type": "DoubleType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "FLOAT", "spark_version": "all", "spark_native_type": "DoubleType", "is_complex": False},

        # Numeric/Decimal types
        {"adapter_name": "postgres", "adapter_native_type": "NUMERIC", "spark_version": "all", "spark_native_type": "DecimalType(38,18)", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "DECIMAL", "spark_version": "all", "spark_native_type": "DecimalType(38,18)", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "MONEY", "spark_version": "all", "spark_native_type": "DecimalType(19,2)", "is_complex": False},

        # Boolean
        {"adapter_name": "postgres", "adapter_native_type": "BOOLEAN", "spark_version": "all", "spark_native_type": "BooleanType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "BOOL", "spark_version": "all", "spark_native_type": "BooleanType", "is_complex": False},

        # Date/Time types
        {"adapter_name": "postgres", "adapter_native_type": "DATE", "spark_version": "all", "spark_native_type": "DateType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "TIME", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},  # Spark has no TimeType
        {"adapter_name": "postgres", "adapter_native_type": "TIMETZ", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "TIMESTAMP", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "TIMESTAMPTZ", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "TIMESTAMP WITHOUT TIME ZONE", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "TIMESTAMP WITH TIME ZONE", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "postgres", "adapter_native_type": "INTERVAL", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},

        # Binary types
        {"adapter_name": "postgres", "adapter_native_type": "BYTEA", "spark_version": "all", "spark_native_type": "BinaryType", "is_complex": False},

        # JSON types
        {"adapter_name": "postgres", "adapter_native_type": "JSON", "spark_version": "all", "spark_native_type": "StringType", "is_complex": True, "cast_expression": "CAST({} AS STRING)"},
        {"adapter_name": "postgres", "adapter_native_type": "JSONB", "spark_version": "all", "spark_native_type": "StringType", "is_complex": True, "cast_expression": "CAST({} AS STRING)"},

        # UUID
        {"adapter_name": "postgres", "adapter_native_type": "UUID", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},

        # Array types (complex)
        {"adapter_name": "postgres", "adapter_native_type": "ARRAY", "spark_version": "all", "spark_native_type": "StringType", "is_complex": True, "cast_expression": "CAST({} AS STRING)"},

        # ======================================================================
        # Snowflake
        # ======================================================================
        # String types
        {"adapter_name": "snowflake", "adapter_native_type": "TEXT", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "VARCHAR", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "STRING", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "CHAR", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "CHARACTER", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},

        # Numeric types
        {"adapter_name": "snowflake", "adapter_native_type": "NUMBER", "spark_version": "all", "spark_native_type": "DecimalType(38,0)", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "DECIMAL", "spark_version": "all", "spark_native_type": "DecimalType(38,18)", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "NUMERIC", "spark_version": "all", "spark_native_type": "DecimalType(38,18)", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "INT", "spark_version": "all", "spark_native_type": "LongType", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "INTEGER", "spark_version": "all", "spark_native_type": "LongType", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "BIGINT", "spark_version": "all", "spark_native_type": "LongType", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "SMALLINT", "spark_version": "all", "spark_native_type": "IntegerType", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "TINYINT", "spark_version": "all", "spark_native_type": "ShortType", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "BYTEINT", "spark_version": "all", "spark_native_type": "ShortType", "is_complex": False},

        # Floating point
        {"adapter_name": "snowflake", "adapter_native_type": "FLOAT", "spark_version": "all", "spark_native_type": "DoubleType", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "FLOAT4", "spark_version": "all", "spark_native_type": "FloatType", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "FLOAT8", "spark_version": "all", "spark_native_type": "DoubleType", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "DOUBLE", "spark_version": "all", "spark_native_type": "DoubleType", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "DOUBLE PRECISION", "spark_version": "all", "spark_native_type": "DoubleType", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "REAL", "spark_version": "all", "spark_native_type": "FloatType", "is_complex": False},

        # Boolean
        {"adapter_name": "snowflake", "adapter_native_type": "BOOLEAN", "spark_version": "all", "spark_native_type": "BooleanType", "is_complex": False},

        # Date/Time
        {"adapter_name": "snowflake", "adapter_native_type": "DATE", "spark_version": "all", "spark_native_type": "DateType", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "TIME", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "TIMESTAMP", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "TIMESTAMP_LTZ", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "TIMESTAMP_NTZ", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "TIMESTAMP_TZ", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "DATETIME", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},

        # Binary
        {"adapter_name": "snowflake", "adapter_native_type": "BINARY", "spark_version": "all", "spark_native_type": "BinaryType", "is_complex": False},
        {"adapter_name": "snowflake", "adapter_native_type": "VARBINARY", "spark_version": "all", "spark_native_type": "BinaryType", "is_complex": False},

        # Semi-structured (complex)
        {"adapter_name": "snowflake", "adapter_native_type": "VARIANT", "spark_version": "all", "spark_native_type": "StringType", "is_complex": True, "cast_expression": "TO_VARCHAR({})"},
        {"adapter_name": "snowflake", "adapter_native_type": "OBJECT", "spark_version": "all", "spark_native_type": "StringType", "is_complex": True, "cast_expression": "TO_VARCHAR({})"},
        {"adapter_name": "snowflake", "adapter_native_type": "ARRAY", "spark_version": "all", "spark_native_type": "StringType", "is_complex": True, "cast_expression": "TO_VARCHAR({})"},

        # ======================================================================
        # Databricks / Delta Lake
        # ======================================================================
        {"adapter_name": "databricks", "adapter_native_type": "STRING", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "databricks", "adapter_native_type": "INT", "spark_version": "all", "spark_native_type": "IntegerType", "is_complex": False},
        {"adapter_name": "databricks", "adapter_native_type": "INTEGER", "spark_version": "all", "spark_native_type": "IntegerType", "is_complex": False},
        {"adapter_name": "databricks", "adapter_native_type": "BIGINT", "spark_version": "all", "spark_native_type": "LongType", "is_complex": False},
        {"adapter_name": "databricks", "adapter_native_type": "LONG", "spark_version": "all", "spark_native_type": "LongType", "is_complex": False},
        {"adapter_name": "databricks", "adapter_native_type": "SMALLINT", "spark_version": "all", "spark_native_type": "ShortType", "is_complex": False},
        {"adapter_name": "databricks", "adapter_native_type": "SHORT", "spark_version": "all", "spark_native_type": "ShortType", "is_complex": False},
        {"adapter_name": "databricks", "adapter_native_type": "TINYINT", "spark_version": "all", "spark_native_type": "ByteType", "is_complex": False},
        {"adapter_name": "databricks", "adapter_native_type": "BYTE", "spark_version": "all", "spark_native_type": "ByteType", "is_complex": False},
        {"adapter_name": "databricks", "adapter_native_type": "FLOAT", "spark_version": "all", "spark_native_type": "FloatType", "is_complex": False},
        {"adapter_name": "databricks", "adapter_native_type": "DOUBLE", "spark_version": "all", "spark_native_type": "DoubleType", "is_complex": False},
        {"adapter_name": "databricks", "adapter_native_type": "DECIMAL", "spark_version": "all", "spark_native_type": "DecimalType(38,18)", "is_complex": False},
        {"adapter_name": "databricks", "adapter_native_type": "BOOLEAN", "spark_version": "all", "spark_native_type": "BooleanType", "is_complex": False},
        {"adapter_name": "databricks", "adapter_native_type": "DATE", "spark_version": "all", "spark_native_type": "DateType", "is_complex": False},
        {"adapter_name": "databricks", "adapter_native_type": "TIMESTAMP", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "databricks", "adapter_native_type": "TIMESTAMP_NTZ", "spark_version": "all", "spark_native_type": "TimestampNTZType", "is_complex": False},
        {"adapter_name": "databricks", "adapter_native_type": "BINARY", "spark_version": "all", "spark_native_type": "BinaryType", "is_complex": False},
        {"adapter_name": "databricks", "adapter_native_type": "ARRAY", "spark_version": "all", "spark_native_type": "ArrayType", "is_complex": True},
        {"adapter_name": "databricks", "adapter_native_type": "MAP", "spark_version": "all", "spark_native_type": "MapType", "is_complex": True},
        {"adapter_name": "databricks", "adapter_native_type": "STRUCT", "spark_version": "all", "spark_native_type": "StructType", "is_complex": True},

        # ======================================================================
        # MySQL
        # ======================================================================
        {"adapter_name": "mysql", "adapter_native_type": "VARCHAR", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "CHAR", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "TEXT", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "TINYTEXT", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "MEDIUMTEXT", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "LONGTEXT", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "INT", "spark_version": "all", "spark_native_type": "IntegerType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "INTEGER", "spark_version": "all", "spark_native_type": "IntegerType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "BIGINT", "spark_version": "all", "spark_native_type": "LongType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "SMALLINT", "spark_version": "all", "spark_native_type": "ShortType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "TINYINT", "spark_version": "all", "spark_native_type": "ByteType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "MEDIUMINT", "spark_version": "all", "spark_native_type": "IntegerType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "FLOAT", "spark_version": "all", "spark_native_type": "FloatType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "DOUBLE", "spark_version": "all", "spark_native_type": "DoubleType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "DECIMAL", "spark_version": "all", "spark_native_type": "DecimalType(38,18)", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "NUMERIC", "spark_version": "all", "spark_native_type": "DecimalType(38,18)", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "BOOLEAN", "spark_version": "all", "spark_native_type": "BooleanType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "BOOL", "spark_version": "all", "spark_native_type": "BooleanType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "DATE", "spark_version": "all", "spark_native_type": "DateType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "DATETIME", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "TIMESTAMP", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "TIME", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "YEAR", "spark_version": "all", "spark_native_type": "IntegerType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "BLOB", "spark_version": "all", "spark_native_type": "BinaryType", "is_complex": False},
        {"adapter_name": "mysql", "adapter_native_type": "JSON", "spark_version": "all", "spark_native_type": "StringType", "is_complex": True},

        # ======================================================================
        # BigQuery
        # ======================================================================
        {"adapter_name": "bigquery", "adapter_native_type": "STRING", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "bigquery", "adapter_native_type": "INT64", "spark_version": "all", "spark_native_type": "LongType", "is_complex": False},
        {"adapter_name": "bigquery", "adapter_native_type": "INTEGER", "spark_version": "all", "spark_native_type": "LongType", "is_complex": False},
        {"adapter_name": "bigquery", "adapter_native_type": "FLOAT64", "spark_version": "all", "spark_native_type": "DoubleType", "is_complex": False},
        {"adapter_name": "bigquery", "adapter_native_type": "FLOAT", "spark_version": "all", "spark_native_type": "DoubleType", "is_complex": False},
        {"adapter_name": "bigquery", "adapter_native_type": "NUMERIC", "spark_version": "all", "spark_native_type": "DecimalType(38,9)", "is_complex": False},
        {"adapter_name": "bigquery", "adapter_native_type": "BIGNUMERIC", "spark_version": "all", "spark_native_type": "DecimalType(76,38)", "is_complex": False},
        {"adapter_name": "bigquery", "adapter_native_type": "BOOL", "spark_version": "all", "spark_native_type": "BooleanType", "is_complex": False},
        {"adapter_name": "bigquery", "adapter_native_type": "BOOLEAN", "spark_version": "all", "spark_native_type": "BooleanType", "is_complex": False},
        {"adapter_name": "bigquery", "adapter_native_type": "DATE", "spark_version": "all", "spark_native_type": "DateType", "is_complex": False},
        {"adapter_name": "bigquery", "adapter_native_type": "DATETIME", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "bigquery", "adapter_native_type": "TIMESTAMP", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "bigquery", "adapter_native_type": "TIME", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "bigquery", "adapter_native_type": "BYTES", "spark_version": "all", "spark_native_type": "BinaryType", "is_complex": False},
        {"adapter_name": "bigquery", "adapter_native_type": "GEOGRAPHY", "spark_version": "all", "spark_native_type": "StringType", "is_complex": True},
        {"adapter_name": "bigquery", "adapter_native_type": "JSON", "spark_version": "all", "spark_native_type": "StringType", "is_complex": True},
        {"adapter_name": "bigquery", "adapter_native_type": "ARRAY", "spark_version": "all", "spark_native_type": "ArrayType", "is_complex": True},
        {"adapter_name": "bigquery", "adapter_native_type": "STRUCT", "spark_version": "all", "spark_native_type": "StructType", "is_complex": True},
        {"adapter_name": "bigquery", "adapter_native_type": "RECORD", "spark_version": "all", "spark_native_type": "StructType", "is_complex": True},

        # ======================================================================
        # Redshift
        # ======================================================================
        {"adapter_name": "redshift", "adapter_native_type": "VARCHAR", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "CHAR", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "BPCHAR", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "TEXT", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "INTEGER", "spark_version": "all", "spark_native_type": "IntegerType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "INT", "spark_version": "all", "spark_native_type": "IntegerType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "INT4", "spark_version": "all", "spark_native_type": "IntegerType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "BIGINT", "spark_version": "all", "spark_native_type": "LongType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "INT8", "spark_version": "all", "spark_native_type": "LongType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "SMALLINT", "spark_version": "all", "spark_native_type": "ShortType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "INT2", "spark_version": "all", "spark_native_type": "ShortType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "REAL", "spark_version": "all", "spark_native_type": "FloatType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "FLOAT4", "spark_version": "all", "spark_native_type": "FloatType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "DOUBLE PRECISION", "spark_version": "all", "spark_native_type": "DoubleType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "FLOAT8", "spark_version": "all", "spark_native_type": "DoubleType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "FLOAT", "spark_version": "all", "spark_native_type": "DoubleType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "DECIMAL", "spark_version": "all", "spark_native_type": "DecimalType(38,18)", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "NUMERIC", "spark_version": "all", "spark_native_type": "DecimalType(38,18)", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "BOOLEAN", "spark_version": "all", "spark_native_type": "BooleanType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "BOOL", "spark_version": "all", "spark_native_type": "BooleanType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "DATE", "spark_version": "all", "spark_native_type": "DateType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "TIMESTAMP", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "TIMESTAMPTZ", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "TIME", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "TIMETZ", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "redshift", "adapter_native_type": "SUPER", "spark_version": "all", "spark_native_type": "StringType", "is_complex": True},
        {"adapter_name": "redshift", "adapter_native_type": "GEOMETRY", "spark_version": "all", "spark_native_type": "StringType", "is_complex": True},
        {"adapter_name": "redshift", "adapter_native_type": "GEOGRAPHY", "spark_version": "all", "spark_native_type": "StringType", "is_complex": True},
        {"adapter_name": "redshift", "adapter_native_type": "HLLSKETCH", "spark_version": "all", "spark_native_type": "BinaryType", "is_complex": True},

        # ======================================================================
        # Oracle
        # ======================================================================
        {"adapter_name": "oracle", "adapter_native_type": "VARCHAR2", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "oracle", "adapter_native_type": "NVARCHAR2", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "oracle", "adapter_native_type": "CHAR", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "oracle", "adapter_native_type": "NCHAR", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "oracle", "adapter_native_type": "CLOB", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "oracle", "adapter_native_type": "NCLOB", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "oracle", "adapter_native_type": "NUMBER", "spark_version": "all", "spark_native_type": "DecimalType(38,10)", "is_complex": False},
        {"adapter_name": "oracle", "adapter_native_type": "FLOAT", "spark_version": "all", "spark_native_type": "DoubleType", "is_complex": False},
        {"adapter_name": "oracle", "adapter_native_type": "BINARY_FLOAT", "spark_version": "all", "spark_native_type": "FloatType", "is_complex": False},
        {"adapter_name": "oracle", "adapter_native_type": "BINARY_DOUBLE", "spark_version": "all", "spark_native_type": "DoubleType", "is_complex": False},
        {"adapter_name": "oracle", "adapter_native_type": "DATE", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},  # Oracle DATE has time component
        {"adapter_name": "oracle", "adapter_native_type": "TIMESTAMP", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "oracle", "adapter_native_type": "TIMESTAMP WITH TIME ZONE", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "oracle", "adapter_native_type": "TIMESTAMP WITH LOCAL TIME ZONE", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "oracle", "adapter_native_type": "INTERVAL YEAR TO MONTH", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "oracle", "adapter_native_type": "INTERVAL DAY TO SECOND", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "oracle", "adapter_native_type": "RAW", "spark_version": "all", "spark_native_type": "BinaryType", "is_complex": False},
        {"adapter_name": "oracle", "adapter_native_type": "BLOB", "spark_version": "all", "spark_native_type": "BinaryType", "is_complex": False},
        {"adapter_name": "oracle", "adapter_native_type": "BFILE", "spark_version": "all", "spark_native_type": "BinaryType", "is_complex": True},
        {"adapter_name": "oracle", "adapter_native_type": "ROWID", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "oracle", "adapter_native_type": "UROWID", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "oracle", "adapter_native_type": "JSON", "spark_version": "all", "spark_native_type": "StringType", "is_complex": True},
        {"adapter_name": "oracle", "adapter_native_type": "XMLTYPE", "spark_version": "all", "spark_native_type": "StringType", "is_complex": True},

        # ======================================================================
        # SQL Server
        # ======================================================================
        {"adapter_name": "sqlserver", "adapter_native_type": "VARCHAR", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "NVARCHAR", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "CHAR", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "NCHAR", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "TEXT", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "NTEXT", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "INT", "spark_version": "all", "spark_native_type": "IntegerType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "BIGINT", "spark_version": "all", "spark_native_type": "LongType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "SMALLINT", "spark_version": "all", "spark_native_type": "ShortType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "TINYINT", "spark_version": "all", "spark_native_type": "ByteType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "FLOAT", "spark_version": "all", "spark_native_type": "DoubleType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "REAL", "spark_version": "all", "spark_native_type": "FloatType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "DECIMAL", "spark_version": "all", "spark_native_type": "DecimalType(38,18)", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "NUMERIC", "spark_version": "all", "spark_native_type": "DecimalType(38,18)", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "MONEY", "spark_version": "all", "spark_native_type": "DecimalType(19,4)", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "SMALLMONEY", "spark_version": "all", "spark_native_type": "DecimalType(10,4)", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "BIT", "spark_version": "all", "spark_native_type": "BooleanType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "DATE", "spark_version": "all", "spark_native_type": "DateType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "DATETIME", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "DATETIME2", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "SMALLDATETIME", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "DATETIMEOFFSET", "spark_version": "all", "spark_native_type": "TimestampType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "TIME", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "BINARY", "spark_version": "all", "spark_native_type": "BinaryType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "VARBINARY", "spark_version": "all", "spark_native_type": "BinaryType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "IMAGE", "spark_version": "all", "spark_native_type": "BinaryType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "UNIQUEIDENTIFIER", "spark_version": "all", "spark_native_type": "StringType", "is_complex": False},
        {"adapter_name": "sqlserver", "adapter_native_type": "XML", "spark_version": "all", "spark_native_type": "StringType", "is_complex": True},
        {"adapter_name": "sqlserver", "adapter_native_type": "GEOGRAPHY", "spark_version": "all", "spark_native_type": "StringType", "is_complex": True},
        {"adapter_name": "sqlserver", "adapter_native_type": "GEOMETRY", "spark_version": "all", "spark_native_type": "StringType", "is_complex": True},
        {"adapter_name": "sqlserver", "adapter_native_type": "HIERARCHYID", "spark_version": "all", "spark_native_type": "StringType", "is_complex": True},
    ]

    @classmethod
    def get_spark_type(
        cls,
        adapter_name: str,
        adapter_type: str,
        spark_version: str = "4.0"
    ) -> Optional[Dict[str, Any]]:
        """
        Look up the Spark type for a given adapter type.

        :param adapter_name: Source adapter (e.g., 'postgres', 'snowflake')
        :param adapter_type: Adapter's native type (e.g., 'INTEGER', 'VARCHAR')
        :param spark_version: Target Spark version (default '4.0')
        :returns: Dict with spark_native_type, is_complex, cast_expression or None
        """
        # Normalize inputs
        adapter_name = adapter_name.lower()
        adapter_type = adapter_type.upper().strip()

        # Remove size specifiers: VARCHAR(255) -> VARCHAR
        import re
        adapter_type_normalized = re.sub(r'\([^)]*\)', '', adapter_type).strip()

        for mapping in cls.TYPE_MAPPINGS:
            if (mapping["adapter_name"] == adapter_name and
                mapping["adapter_native_type"] == adapter_type_normalized):
                # Check spark version match
                if mapping["spark_version"] == "all" or mapping["spark_version"] == spark_version:
                    return {
                        "spark_native_type": mapping["spark_native_type"],
                        "is_complex": mapping.get("is_complex", False),
                        "cast_expression": mapping.get("cast_expression"),
                    }

        return None

    @classmethod
    def get_all_mappings_for_adapter(cls, adapter_name: str) -> List[Dict[str, Any]]:
        """Get all type mappings for a specific adapter."""
        adapter_name = adapter_name.lower()
        return [m for m in cls.TYPE_MAPPINGS if m["adapter_name"] == adapter_name]


class SyntaxRegistry:
    """
    Syntax rules for each adapter.

    Defines quoting characters, case sensitivity, and reserved keywords
    to ensure correct SQL generation across different dialects.
    """

    SYNTAX_RULES: Dict[str, Dict[str, Any]] = {
        "postgres": {
            "quote_start": '"',
            "quote_end": '"',
            "case_sensitivity": "LOWER",  # Postgres folds to lowercase
            "reserved_keywords": [
                "ALL", "ANALYSE", "ANALYZE", "AND", "ANY", "ARRAY", "AS", "ASC",
                "ASYMMETRIC", "BOTH", "CASE", "CAST", "CHECK", "COLLATE", "COLUMN",
                "CONSTRAINT", "CREATE", "CURRENT_CATALOG", "CURRENT_DATE",
                "CURRENT_ROLE", "CURRENT_TIME", "CURRENT_TIMESTAMP", "CURRENT_USER",
                "DEFAULT", "DEFERRABLE", "DESC", "DISTINCT", "DO", "ELSE", "END",
                "EXCEPT", "FALSE", "FETCH", "FOR", "FOREIGN", "FROM", "GRANT",
                "GROUP", "HAVING", "IN", "INITIALLY", "INTERSECT", "INTO", "LATERAL",
                "LEADING", "LIMIT", "LOCALTIME", "LOCALTIMESTAMP", "NOT", "NULL",
                "OFFSET", "ON", "ONLY", "OR", "ORDER", "PLACING", "PRIMARY",
                "REFERENCES", "RETURNING", "SELECT", "SESSION_USER", "SOME",
                "SYMMETRIC", "TABLE", "THEN", "TO", "TRAILING", "TRUE", "UNION",
                "UNIQUE", "USER", "USING", "VARIADIC", "WHEN", "WHERE", "WINDOW",
                "WITH"
            ],
        },
        "snowflake": {
            "quote_start": '"',
            "quote_end": '"',
            "case_sensitivity": "UPPER",  # Snowflake folds to uppercase
            "reserved_keywords": [
                "ACCOUNT", "ALL", "ALTER", "AND", "ANY", "AS", "BETWEEN", "BY",
                "CASE", "CAST", "CHECK", "CLUSTER", "COLUMN", "CONNECT", "CONNECTION",
                "CONSTRAINT", "CREATE", "CROSS", "CURRENT", "CURRENT_DATE",
                "CURRENT_TIME", "CURRENT_TIMESTAMP", "CURRENT_USER", "DATABASE",
                "DELETE", "DISTINCT", "DROP", "ELSE", "EXISTS", "FALSE", "FOLLOWING",
                "FOR", "FROM", "FULL", "GRANT", "GROUP", "GSCLUSTER", "HAVING",
                "ILIKE", "IN", "INCREMENT", "INNER", "INSERT", "INTERSECT", "INTO",
                "IS", "ISSUE", "JOIN", "LATERAL", "LEFT", "LIKE", "LOCALTIME",
                "LOCALTIMESTAMP", "MINUS", "NATURAL", "NOT", "NULL", "OF", "ON",
                "OR", "ORDER", "ORGANIZATION", "QUALIFY", "REGEXP", "REVOKE",
                "RIGHT", "RLIKE", "ROW", "ROWS", "SAMPLE", "SCHEMA", "SELECT",
                "SET", "SOME", "START", "TABLE", "TABLESAMPLE", "THEN", "TO",
                "TRIGGER", "TRUE", "TRY_CAST", "UNION", "UNIQUE", "UPDATE",
                "USING", "VALUES", "VIEW", "WHEN", "WHENEVER", "WHERE", "WITH"
            ],
        },
        "databricks": {
            "quote_start": '`',
            "quote_end": '`',
            "case_sensitivity": "PRESERVE",  # Databricks preserves case
            "reserved_keywords": [
                "ALL", "ALTER", "AND", "ANTI", "ANY", "ARCHIVE", "ARRAY", "AS",
                "ASC", "AT", "AUTHORIZATION", "BETWEEN", "BOTH", "BUCKET", "BUCKETS",
                "BY", "CACHE", "CASCADE", "CASE", "CAST", "CHANGE", "CHECK", "CLEAR",
                "CLUSTER", "CLUSTERED", "CODEGEN", "COLLATE", "COLLECTION", "COLUMN",
                "COLUMNS", "COMMENT", "COMMIT", "COMPACT", "COMPACTIONS", "COMPUTE",
                "CONCATENATE", "CONSTRAINT", "COST", "CREATE", "CROSS", "CUBE",
                "CURRENT", "CURRENT_DATE", "CURRENT_TIME", "CURRENT_TIMESTAMP",
                "CURRENT_USER", "DATA", "DATABASE", "DATABASES", "DAY", "DBPROPERTIES",
                "DEFINED", "DELETE", "DELIMITED", "DESC", "DESCRIBE", "DFS", "DIRECTORIES",
                "DIRECTORY", "DISTINCT", "DISTRIBUTE", "DROP", "ELSE", "END", "ESCAPE",
                "ESCAPED", "EXCEPT", "EXCHANGE", "EXISTS", "EXPLAIN", "EXPORT", "EXTENDED",
                "EXTERNAL", "EXTRACT", "FALSE", "FETCH", "FIELDS", "FILTER", "FILEFORMAT",
                "FIRST", "FOLLOWING", "FOR", "FOREIGN", "FORMAT", "FORMATTED", "FROM",
                "FULL", "FUNCTION", "FUNCTIONS", "GLOBAL", "GRANT", "GROUP", "GROUPING",
                "HAVING", "HOUR", "IF", "IGNORE", "IMPORT", "IN", "INDEX", "INDEXES",
                "INNER", "INPATH", "INPUTFORMAT", "INSERT", "INTERSECT", "INTERVAL",
                "INTO", "IS", "ITEMS", "JOIN", "KEYS", "LAST", "LATERAL", "LAZY", "LEADING",
                "LEFT", "LIKE", "LIMIT", "LINES", "LIST", "LOAD", "LOCAL", "LOCATION",
                "LOCK", "LOCKS", "LOGICAL", "MACRO", "MAP", "MATCHED", "MERGE", "MINUTE",
                "MONTH", "MSCK", "NAMESPACE", "NAMESPACES", "NATURAL", "NO", "NOT", "NULL",
                "NULLS", "OF", "ON", "ONLY", "OPTION", "OPTIONS", "OR", "ORDER", "OUT",
                "OUTER", "OUTPUTFORMAT", "OVER", "OVERLAPS", "OVERLAY", "OVERWRITE",
                "PARTITION", "PARTITIONED", "PARTITIONS", "PERCENT", "PLACING", "POSITION",
                "PRECEDING", "PRIMARY", "PRINCIPALS", "PROPERTIES", "PURGE", "QUERY",
                "RANGE", "RECORDREADER", "RECORDWRITER", "RECOVER", "REDUCE", "REFERENCES",
                "REFRESH", "RENAME", "REPAIR", "REPLACE", "RESET", "RESTRICT", "REVOKE",
                "RIGHT", "RLIKE", "ROLE", "ROLES", "ROLLBACK", "ROLLUP", "ROW", "ROWS",
                "SCHEMA", "SCHEMAS", "SECOND", "SELECT", "SEMI", "SEPARATED", "SERDE",
                "SERDEPROPERTIES", "SESSION_USER", "SET", "SETS", "SHOW", "SKEWED", "SOME",
                "SORT", "SORTED", "START", "STATISTICS", "STORED", "STRATIFY", "STRUCT",
                "SUBSTR", "SUBSTRING", "TABLE", "TABLES", "TABLESAMPLE", "TBLPROPERTIES",
                "TEMP", "TEMPORARY", "TERMINATED", "THEN", "TO", "TOUCH", "TRAILING",
                "TRANSACTION", "TRANSACTIONS", "TRANSFORM", "TRIM", "TRUE", "TRUNCATE",
                "TYPE", "UNARCHIVE", "UNBOUNDED", "UNCACHE", "UNION", "UNIQUE", "UNKNOWN",
                "UNLOCK", "UNSET", "UPDATE", "USE", "USER", "USING", "VALUES", "VIEW",
                "VIEWS", "WHEN", "WHERE", "WINDOW", "WITH", "YEAR"
            ],
        },
        "bigquery": {
            "quote_start": '`',
            "quote_end": '`',
            "case_sensitivity": "PRESERVE",  # BigQuery preserves case
            "reserved_keywords": [
                "ALL", "AND", "ANY", "ARRAY", "AS", "ASC", "ASSERT_ROWS_MODIFIED",
                "AT", "BETWEEN", "BY", "CASE", "CAST", "COLLATE", "CONTAINS", "CREATE",
                "CROSS", "CUBE", "CURRENT", "DEFAULT", "DEFINE", "DESC", "DISTINCT",
                "ELSE", "END", "ENUM", "ESCAPE", "EXCEPT", "EXCLUDE", "EXISTS",
                "EXTRACT", "FALSE", "FETCH", "FOLLOWING", "FOR", "FROM", "FULL",
                "GROUP", "GROUPING", "GROUPS", "HASH", "HAVING", "IF", "IGNORE",
                "IN", "INNER", "INTERSECT", "INTERVAL", "INTO", "IS", "JOIN",
                "LATERAL", "LEFT", "LIKE", "LIMIT", "LOOKUP", "MERGE", "NATURAL",
                "NEW", "NO", "NOT", "NULL", "NULLS", "OF", "ON", "OR", "ORDER",
                "OUTER", "OVER", "PARTITION", "PRECEDING", "PROTO", "RANGE",
                "RECURSIVE", "RESPECT", "RIGHT", "ROLLUP", "ROWS", "SELECT", "SET",
                "SOME", "STRUCT", "TABLESAMPLE", "THEN", "TO", "TREAT", "TRUE",
                "UNBOUNDED", "UNION", "UNNEST", "USING", "WHEN", "WHERE", "WINDOW",
                "WITH", "WITHIN"
            ],
        },
        "mysql": {
            "quote_start": '`',
            "quote_end": '`',
            "case_sensitivity": "PRESERVE",  # Depends on collation, default preserve
            "reserved_keywords": [
                "ACCESSIBLE", "ADD", "ALL", "ALTER", "ANALYZE", "AND", "AS", "ASC",
                "ASENSITIVE", "BEFORE", "BETWEEN", "BIGINT", "BINARY", "BLOB", "BOTH",
                "BY", "CALL", "CASCADE", "CASE", "CHANGE", "CHAR", "CHARACTER", "CHECK",
                "COLLATE", "COLUMN", "CONDITION", "CONSTRAINT", "CONTINUE", "CONVERT",
                "CREATE", "CROSS", "CUBE", "CUME_DIST", "CURRENT_DATE", "CURRENT_TIME",
                "CURRENT_TIMESTAMP", "CURRENT_USER", "CURSOR", "DATABASE", "DATABASES",
                "DAY_HOUR", "DAY_MICROSECOND", "DAY_MINUTE", "DAY_SECOND", "DEC",
                "DECIMAL", "DECLARE", "DEFAULT", "DELAYED", "DELETE", "DENSE_RANK",
                "DESC", "DESCRIBE", "DETERMINISTIC", "DISTINCT", "DISTINCTROW", "DIV",
                "DOUBLE", "DROP", "DUAL", "EACH", "ELSE", "ELSEIF", "EMPTY", "ENCLOSED",
                "ESCAPED", "EXCEPT", "EXISTS", "EXIT", "EXPLAIN", "FALSE", "FETCH",
                "FIRST_VALUE", "FLOAT", "FLOAT4", "FLOAT8", "FOR", "FORCE", "FOREIGN",
                "FROM", "FULLTEXT", "FUNCTION", "GENERATED", "GET", "GRANT", "GROUP",
                "GROUPING", "GROUPS", "HAVING", "HIGH_PRIORITY", "HOUR_MICROSECOND",
                "HOUR_MINUTE", "HOUR_SECOND", "IF", "IGNORE", "IN", "INDEX", "INFILE",
                "INNER", "INOUT", "INSENSITIVE", "INSERT", "INT", "INT1", "INT2", "INT3",
                "INT4", "INT8", "INTEGER", "INTERVAL", "INTO", "IO_AFTER_GTIDS",
                "IO_BEFORE_GTIDS", "IS", "ITERATE", "JOIN", "JSON_TABLE", "KEY", "KEYS",
                "KILL", "LAG", "LAST_VALUE", "LATERAL", "LEAD", "LEADING", "LEAVE",
                "LEFT", "LIKE", "LIMIT", "LINEAR", "LINES", "LOAD", "LOCALTIME",
                "LOCALTIMESTAMP", "LOCK", "LONG", "LONGBLOB", "LONGTEXT", "LOOP",
                "LOW_PRIORITY", "MASTER_BIND", "MASTER_SSL_VERIFY_SERVER_CERT", "MATCH",
                "MAXVALUE", "MEDIUMBLOB", "MEDIUMINT", "MEDIUMTEXT", "MIDDLEINT",
                "MINUTE_MICROSECOND", "MINUTE_SECOND", "MOD", "MODIFIES", "NATURAL",
                "NOT", "NO_WRITE_TO_BINLOG", "NTH_VALUE", "NTILE", "NULL", "NUMERIC",
                "OF", "ON", "OPTIMIZE", "OPTIMIZER_COSTS", "OPTION", "OPTIONALLY",
                "OR", "ORDER", "OUT", "OUTER", "OUTFILE", "OVER", "PARTITION",
                "PERCENT_RANK", "PRECISION", "PRIMARY", "PROCEDURE", "PURGE", "RANGE",
                "RANK", "READ", "READS", "READ_WRITE", "REAL", "RECURSIVE", "REFERENCES",
                "REGEXP", "RELEASE", "RENAME", "REPEAT", "REPLACE", "REQUIRE", "RESIGNAL",
                "RESTRICT", "RETURN", "REVOKE", "RIGHT", "RLIKE", "ROW", "ROWS",
                "ROW_NUMBER", "SCHEMA", "SCHEMAS", "SECOND_MICROSECOND", "SELECT",
                "SENSITIVE", "SEPARATOR", "SET", "SHOW", "SIGNAL", "SMALLINT", "SPATIAL",
                "SPECIFIC", "SQL", "SQLEXCEPTION", "SQLSTATE", "SQLWARNING",
                "SQL_BIG_RESULT", "SQL_CALC_FOUND_ROWS", "SQL_SMALL_RESULT", "SSL",
                "STARTING", "STORED", "STRAIGHT_JOIN", "SYSTEM", "TABLE", "TERMINATED",
                "THEN", "TINYBLOB", "TINYINT", "TINYTEXT", "TO", "TRAILING", "TRIGGER",
                "TRUE", "UNDO", "UNION", "UNIQUE", "UNLOCK", "UNSIGNED", "UPDATE",
                "USAGE", "USE", "USING", "UTC_DATE", "UTC_TIME", "UTC_TIMESTAMP",
                "VALUES", "VARBINARY", "VARCHAR", "VARCHARACTER", "VARYING", "VIRTUAL",
                "WHEN", "WHERE", "WHILE", "WINDOW", "WITH", "WRITE", "XOR", "YEAR_MONTH",
                "ZEROFILL"
            ],
        },
        "redshift": {
            "quote_start": '"',
            "quote_end": '"',
            "case_sensitivity": "LOWER",  # Redshift folds to lowercase
            "reserved_keywords": [
                "AES128", "AES256", "ALL", "ALLOWOVERWRITE", "ANALYSE", "ANALYZE",
                "AND", "ANY", "ARRAY", "AS", "ASC", "AUTHORIZATION", "BACKUP",
                "BETWEEN", "BINARY", "BLANKSASNULL", "BOTH", "BYTEDICT", "BZIP2",
                "CASE", "CAST", "CHECK", "COLLATE", "COLUMN", "CONSTRAINT", "CREATE",
                "CREDENTIALS", "CROSS", "CURRENT_DATE", "CURRENT_TIME",
                "CURRENT_TIMESTAMP", "CURRENT_USER", "CURRENT_USER_ID", "DEFAULT",
                "DEFERRABLE", "DEFLATE", "DEFRAG", "DELTA", "DELTA32K", "DESC",
                "DISABLE", "DISTINCT", "DO", "ELSE", "EMPTYASNULL", "ENABLE", "ENCODE",
                "ENCRYPT", "ENCRYPTION", "END", "EXCEPT", "EXPLICIT", "FALSE", "FOR",
                "FOREIGN", "FREEZE", "FROM", "FULL", "GLOBALDICT256", "GLOBALDICT64K",
                "GRANT", "GROUP", "GZIP", "HAVING", "IDENTITY", "IGNORE", "ILIKE",
                "IN", "INITIALLY", "INNER", "INTERSECT", "INTO", "IS", "ISNULL",
                "JOIN", "LANGUAGE", "LEADING", "LEFT", "LIKE", "LIMIT", "LOCALTIME",
                "LOCALTIMESTAMP", "LUN", "LUNS", "LZO", "LZOP", "MINUS", "MOSTLY13",
                "MOSTLY32", "MOSTLY8", "NATURAL", "NEW", "NOT", "NOTNULL", "NULL",
                "NULLS", "OFF", "OFFLINE", "OFFSET", "OID", "OLD", "ON", "ONLY",
                "OPEN", "OR", "ORDER", "OUTER", "OVERLAPS", "PARALLEL", "PARTITION",
                "PERCENT", "PERMISSIONS", "PLACING", "PRIMARY", "RAW", "READRATIO",
                "RECOVER", "REFERENCES", "RESPECT", "REJECTLOG", "RESORT", "RESTORE",
                "RIGHT", "SELECT", "SESSION_USER", "SIMILAR", "SNAPSHOT", "SOME",
                "SYSDATE", "SYSTEM", "TABLE", "TAG", "TDES", "TEXT255", "TEXT32K",
                "THEN", "TIMESTAMP", "TO", "TOP", "TRAILING", "TRUE", "TRUNCATECOLUMNS",
                "UNION", "UNIQUE", "USER", "USING", "VERBOSE", "WALLET", "WHEN",
                "WHERE", "WITH", "WITHOUT"
            ],
        },
        "oracle": {
            "quote_start": '"',
            "quote_end": '"',
            "case_sensitivity": "UPPER",  # Oracle folds to uppercase
            "reserved_keywords": [
                "ACCESS", "ADD", "ALL", "ALTER", "AND", "ANY", "AS", "ASC", "AUDIT",
                "BETWEEN", "BY", "CHAR", "CHECK", "CLUSTER", "COLUMN", "COLUMN_VALUE",
                "COMMENT", "COMPRESS", "CONNECT", "CREATE", "CURRENT", "DATE",
                "DECIMAL", "DEFAULT", "DELETE", "DESC", "DISTINCT", "DROP", "ELSE",
                "EXCLUSIVE", "EXISTS", "FILE", "FLOAT", "FOR", "FROM", "GRANT",
                "GROUP", "HAVING", "IDENTIFIED", "IMMEDIATE", "IN", "INCREMENT",
                "INDEX", "INITIAL", "INSERT", "INTEGER", "INTERSECT", "INTO", "IS",
                "LEVEL", "LIKE", "LOCK", "LONG", "MAXEXTENTS", "MINUS", "MLSLABEL",
                "MODE", "MODIFY", "NESTED_TABLE_ID", "NOAUDIT", "NOCOMPRESS", "NOT",
                "NOWAIT", "NULL", "NUMBER", "OF", "OFFLINE", "ON", "ONLINE", "OPTION",
                "OR", "ORDER", "PCTFREE", "PRIOR", "PUBLIC", "RAW", "RENAME",
                "RESOURCE", "REVOKE", "ROW", "ROWID", "ROWNUM", "ROWS", "SELECT",
                "SESSION", "SET", "SHARE", "SIZE", "SMALLINT", "START", "SUCCESSFUL",
                "SYNONYM", "SYSDATE", "TABLE", "THEN", "TO", "TRIGGER", "UID", "UNION",
                "UNIQUE", "UPDATE", "USER", "VALIDATE", "VALUES", "VARCHAR", "VARCHAR2",
                "VIEW", "WHENEVER", "WHERE", "WITH"
            ],
        },
        "sqlserver": {
            "quote_start": '[',
            "quote_end": ']',
            "case_sensitivity": "PRESERVE",  # Depends on collation
            "reserved_keywords": [
                "ADD", "ALL", "ALTER", "AND", "ANY", "AS", "ASC", "AUTHORIZATION",
                "BACKUP", "BEGIN", "BETWEEN", "BREAK", "BROWSE", "BULK", "BY",
                "CASCADE", "CASE", "CHECK", "CHECKPOINT", "CLOSE", "CLUSTERED",
                "COALESCE", "COLLATE", "COLUMN", "COMMIT", "COMPUTE", "CONSTRAINT",
                "CONTAINS", "CONTAINSTABLE", "CONTINUE", "CONVERT", "CREATE", "CROSS",
                "CURRENT", "CURRENT_DATE", "CURRENT_TIME", "CURRENT_TIMESTAMP",
                "CURRENT_USER", "CURSOR", "DATABASE", "DBCC", "DEALLOCATE", "DECLARE",
                "DEFAULT", "DELETE", "DENY", "DESC", "DISK", "DISTINCT", "DISTRIBUTED",
                "DOUBLE", "DROP", "DUMP", "ELSE", "END", "ERRLVL", "ESCAPE", "EXCEPT",
                "EXEC", "EXECUTE", "EXISTS", "EXIT", "EXTERNAL", "FETCH", "FILE",
                "FILLFACTOR", "FOR", "FOREIGN", "FREETEXT", "FREETEXTTABLE", "FROM",
                "FULL", "FUNCTION", "GOTO", "GRANT", "GROUP", "HAVING", "HOLDLOCK",
                "IDENTITY", "IDENTITY_INSERT", "IDENTITYCOL", "IF", "IN", "INDEX",
                "INNER", "INSERT", "INTERSECT", "INTO", "IS", "JOIN", "KEY", "KILL",
                "LEFT", "LIKE", "LINENO", "LOAD", "MERGE", "NATIONAL", "NOCHECK",
                "NONCLUSTERED", "NOT", "NULL", "NULLIF", "OF", "OFF", "OFFSETS", "ON",
                "OPEN", "OPENDATASOURCE", "OPENQUERY", "OPENROWSET", "OPENXML",
                "OPTION", "OR", "ORDER", "OUTER", "OVER", "PERCENT", "PIVOT", "PLAN",
                "PRECISION", "PRIMARY", "PRINT", "PROC", "PROCEDURE", "PUBLIC",
                "RAISERROR", "READ", "READTEXT", "RECONFIGURE", "REFERENCES",
                "REPLICATION", "RESTORE", "RESTRICT", "RETURN", "REVERT", "REVOKE",
                "RIGHT", "ROLLBACK", "ROWCOUNT", "ROWGUIDCOL", "RULE", "SAVE",
                "SCHEMA", "SECURITYAUDIT", "SELECT", "SEMANTICKEYPHRASETABLE",
                "SEMANTICSIMILARITYDETAILSTABLE", "SEMANTICSIMILARITYTABLE",
                "SESSION_USER", "SET", "SETUSER", "SHUTDOWN", "SOME", "STATISTICS",
                "SYSTEM_USER", "TABLE", "TABLESAMPLE", "TEXTSIZE", "THEN", "TO",
                "TOP", "TRAN", "TRANSACTION", "TRIGGER", "TRUNCATE", "TRY_CONVERT",
                "TSEQUAL", "UNION", "UNIQUE", "UNPIVOT", "UPDATE", "UPDATETEXT",
                "USE", "USER", "VALUES", "VARYING", "VIEW", "WAITFOR", "WHEN",
                "WHERE", "WHILE", "WITH", "WITHIN GROUP", "WRITETEXT"
            ],
        },
    }

    @classmethod
    def get_syntax_rule(cls, adapter_name: str) -> Optional[Dict[str, Any]]:
        """Get syntax rules for a specific adapter."""
        return cls.SYNTAX_RULES.get(adapter_name.lower())

    @classmethod
    def quote_identifier(cls, adapter_name: str, identifier: str) -> str:
        """Quote an identifier using the adapter's quoting rules."""
        rule = cls.get_syntax_rule(adapter_name)
        if not rule:
            return f'"{identifier}"'  # Default to double quotes
        return f'{rule["quote_start"]}{identifier}{rule["quote_end"]}'

    @classmethod
    def needs_quoting(cls, adapter_name: str, identifier: str) -> bool:
        """Check if an identifier needs quoting (reserved keyword or special chars)."""
        rule = cls.get_syntax_rule(adapter_name)
        if not rule:
            return False

        # Check if it's a reserved keyword
        upper_id = identifier.upper()
        if upper_id in rule.get("reserved_keywords", []):
            return True

        # Check for special characters or spaces
        if not identifier.isidentifier() or ' ' in identifier or '-' in identifier:
            return True

        return False

    @classmethod
    def normalize_identifier(cls, adapter_name: str, identifier: str) -> str:
        """Normalize an identifier based on the adapter's case sensitivity rules."""
        rule = cls.get_syntax_rule(adapter_name)
        if not rule:
            return identifier

        case_rule = rule.get("case_sensitivity", "PRESERVE")
        if case_rule == "UPPER":
            return identifier.upper()
        elif case_rule == "LOWER":
            return identifier.lower()
        return identifier  # PRESERVE
