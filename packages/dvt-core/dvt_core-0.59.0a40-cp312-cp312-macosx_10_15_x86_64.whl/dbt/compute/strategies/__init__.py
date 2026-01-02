"""
Spark Connection Strategies

This module provides different strategies for connecting to Spark clusters.
Uses the strategy pattern for flexible platform support.

v0.5.98: Added EMRStrategy, DataprocStrategy, and StandaloneStrategy.
v0.51.2: Removed Databricks support (serverless cannot read external JDBC sources).
"""

from dbt.compute.strategies.base import BaseConnectionStrategy
from dbt.compute.strategies.local import LocalStrategy, cleanup_all_spark_sessions

# Strategies are imported lazily to avoid import errors when
# optional dependencies are not installed


def get_emr_strategy():
    """
    Lazily import and return EMRStrategy.

    :returns: EMRStrategy class
    """
    from dbt.compute.strategies.emr import EMRStrategy
    return EMRStrategy


def get_dataproc_strategy():
    """
    Lazily import and return DataprocStrategy.

    :returns: DataprocStrategy class
    """
    from dbt.compute.strategies.dataproc import DataprocStrategy
    return DataprocStrategy


def get_standalone_strategy():
    """
    Lazily import and return StandaloneStrategy.

    :returns: StandaloneStrategy class
    """
    from dbt.compute.strategies.standalone import StandaloneStrategy
    return StandaloneStrategy


__all__ = [
    "BaseConnectionStrategy",
    "LocalStrategy",
    "cleanup_all_spark_sessions",
    "get_emr_strategy",
    "get_dataproc_strategy",
    "get_standalone_strategy",
]
