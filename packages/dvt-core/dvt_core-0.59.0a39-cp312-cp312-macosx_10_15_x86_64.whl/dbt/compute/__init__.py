"""
DVT Compute Layer

This module provides compute engine integration for federated query execution.

v0.3.0: Spark-unified architecture - arrow_bridge removed.
"""

# Note: arrow_bridge, adapter_to_arrow, and arrow_to_adapter removed in v0.3.0
# All data loading now uses Spark JDBC

from typing import List

__all__: List[str] = []
