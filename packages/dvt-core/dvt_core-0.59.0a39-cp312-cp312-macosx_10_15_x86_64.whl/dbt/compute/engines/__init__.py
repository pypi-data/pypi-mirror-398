"""
DVT Compute Engines

This module provides ephemeral compute engines for federated query execution.
Compute engines are used ONLY for processing, never for materialization.

v0.3.0: Spark-unified architecture - DuckDBEngine removed.
"""

from dbt.compute.engines.spark_engine import SparkEngine

__all__ = ["SparkEngine"]
