"""
Filter pushdown optimization for federated queries.

Extracts filters (WHERE, LIMIT, ORDER BY) from compiled SQL and rewrites them
to be pushed down to source databases in their native SQL dialects.
"""

import re
import sys
import sqlparse
from sqlparse.sql import Statement, Token, TokenList, Identifier, Where, Comparison
from sqlparse.tokens import Keyword, Whitespace
from typing import Dict, List, Optional, Any


class FilterPushdownOptimizer:
    """
    Optimizes federated queries by pushing filters down to source databases.

    Strategy:
    1. Parse compiled SQL to extract filters per source table
    2. Rewrite filters in each source adapter's SQL dialect
    3. Return subqueries for JDBC reads instead of plain table names

    Example:
        Input SQL:
            SELECT * FROM snowflake_table WHERE date > '2024-01-01' LIMIT 10

        Output:
            JDBC subquery: (SELECT * FROM snowflake_table WHERE date > '2024-01-01' LIMIT 10)
    """

    def __init__(self, compiled_sql: str, source_tables: List[Any]):
        """
        Initialize optimizer with compiled SQL and source table metadata.

        Args:
            compiled_sql: The fully compiled SQL from the model
            source_tables: List of SourceTableMetadata objects
        """
        self.compiled_sql = compiled_sql
        self.source_tables = source_tables
        self.parsed = sqlparse.parse(compiled_sql)[0] if compiled_sql else None

    def extract_limit(self) -> Optional[int]:
        """
        Extract LIMIT clause from SQL.

        Returns:
            Limit value as integer, or None if no LIMIT clause
        """
        if not self.parsed:
            return None

        # Simple regex approach for LIMIT (works for most cases)
        limit_match = re.search(r'\bLIMIT\s+(\d+)\b', self.compiled_sql, re.IGNORECASE)
        if limit_match:
            return int(limit_match.group(1))

        return None

    def extract_sample_clause(self) -> Optional[Dict[str, Any]]:
        """
        Extract SAMPLE/TABLESAMPLE clause from SQL (Snowflake-specific sampling).

        Snowflake supports several SAMPLE methods:
        - SAMPLE (N) or SAMPLE (N ROWS) - Row-count sampling
        - SAMPLE SYSTEM (P) - System/block sampling with P% probability
        - SAMPLE BERNOULLI (P) - Bernoulli/row-level sampling with P% probability
        - SAMPLE BLOCK (P) - Alias for SYSTEM
        - TABLESAMPLE ... - Alternative syntax
        - REPEATABLE(seed) or SEED(seed) - Reproducible sampling

        Returns:
            Dict with keys:
                - 'method': 'ROWS', 'SYSTEM', 'BERNOULLI', 'BLOCK'
                - 'value': int (row count or percentage)
                - 'seed': Optional int for reproducible sampling
                - 'full_clause': The complete SAMPLE clause to push down
            or None if no SAMPLE clause
        """
        if not self.parsed:
            return None

        # Try to match complete SAMPLE/TABLESAMPLE clause
        # Pattern: (TABLE)?SAMPLE <method>? (value) (REPEATABLE|SEED)?(seed)?

        # Match: SAMPLE (N) or SAMPLE (N ROWS) with optional seed
        sample_rows = re.search(
            r'\b(?:TABLE)?SAMPLE\s*\(\s*(\d+)(?:\s+ROWS)?\s*\)'
            r'(?:\s+(?:REPEATABLE|SEED)\s*\(\s*(\d+)\s*\))?',
            self.compiled_sql,
            re.IGNORECASE
        )
        if sample_rows:
            result = {
                'method': 'ROWS',
                'value': int(sample_rows.group(1)),
                'seed': int(sample_rows.group(2)) if sample_rows.group(2) else None
            }
            # Build full clause
            clause = f"SAMPLE ({result['value']})"
            if result['seed']:
                clause += f" REPEATABLE ({result['seed']})"
            result['full_clause'] = clause
            return result

        # Match: SAMPLE SYSTEM|BERNOULLI|BLOCK (P) with optional seed
        sample_method = re.search(
            r'\b(?:TABLE)?SAMPLE\s+(SYSTEM|BERNOULLI|BLOCK)\s*\(\s*(\d+(?:\.\d+)?)\s*\)'
            r'(?:\s+(?:REPEATABLE|SEED)\s*\(\s*(\d+)\s*\))?',
            self.compiled_sql,
            re.IGNORECASE
        )
        if sample_method:
            method = sample_method.group(1).upper()
            # BLOCK is an alias for SYSTEM
            if method == 'BLOCK':
                method = 'SYSTEM'

            result = {
                'method': method,
                'value': float(sample_method.group(2)),
                'seed': int(sample_method.group(3)) if sample_method.group(3) else None
            }
            # Build full clause
            clause = f"SAMPLE {result['method']} ({result['value']})"
            if result['seed']:
                clause += f" REPEATABLE ({result['seed']})"
            result['full_clause'] = clause
            return result

        return None

    def extract_where_clauses(self) -> Dict[str, List[str]]:
        """
        Extract WHERE clauses that apply to specific source tables.

        Returns:
            Dict mapping table name/alias to list of WHERE conditions

        Example:
            {
                'snowflake_table': ['date > \'2024-01-01\'', 'status = \'active\''],
                'postgres_table': ['id > 100']
            }
        """
        # TODO: Implement WHERE clause extraction using sqlparse
        # For now, return empty dict - LIMIT pushdown is the priority
        return {}

    def build_pushdown_subquery(
        self,
        source_table: Any,
        adapter_type: str
    ) -> Optional[str]:
        """
        Build a subquery with pushed-down filters for a specific source table.

        Args:
            source_table: SourceTableMetadata object
            adapter_type: Adapter type (postgres, snowflake, etc.)

        Returns:
            SQL subquery with filters, or None if no pushdown possible

        Example:
            Input: table="schema.table", LIMIT 10
            Output: "(SELECT * FROM schema.table LIMIT 10)"
        """
        limit = self.extract_limit()
        sample_clause = self.extract_sample_clause()
        where_clauses = self.extract_where_clauses()

        # DVT v0.4.7: Suppressed debug output for clean console
        # Debug info: LIMIT={limit}, SAMPLE={sample_clause}, WHERE={where_clauses}

        # If no filters to push down, return None (read full table)
        if not limit and not sample_clause and not where_clauses:
            return None

        # Build subquery
        qualified_name = source_table.qualified_name
        subquery_parts = [f"SELECT * FROM {qualified_name}"]

        # Add SAMPLE clause (Snowflake-specific, goes right after FROM)
        if sample_clause and adapter_type.lower() == 'snowflake':
            # Use the pre-built full_clause from extract_sample_clause
            # This includes all sampling options: method, value, and seed
            subquery_parts.append(sample_clause['full_clause'])

        # Add WHERE clauses (if any)
        table_key = source_table.identifier  # or qualified_name
        if table_key in where_clauses:
            conditions = " AND ".join(where_clauses[table_key])
            subquery_parts.append(f"WHERE {conditions}")

        # Add LIMIT (if present and no SAMPLE used)
        # Note: SAMPLE takes precedence over LIMIT for Snowflake
        if limit and not (sample_clause and adapter_type.lower() == 'snowflake'):
            # Rewrite LIMIT in adapter's dialect
            limit_clause = self._rewrite_limit_for_adapter(limit, adapter_type)
            if limit_clause:
                subquery_parts.append(limit_clause)

        subquery = " ".join(subquery_parts)
        # DVT v0.4.7: Suppressed debug output
        return f"({subquery})"

    def _rewrite_limit_for_adapter(self, limit: int, adapter_type: str) -> Optional[str]:
        """
        Rewrite LIMIT clause for specific adapter's SQL dialect.

        Args:
            limit: Limit value
            adapter_type: Adapter type (postgres, snowflake, redshift, etc.)

        Returns:
            LIMIT clause in adapter's dialect
        """
        # Most adapters support standard LIMIT syntax
        standard_adapters = [
            'postgres', 'postgresql',
            'snowflake',
            'redshift',
            'mysql',
            'sqlite',
            'bigquery'
        ]

        if adapter_type.lower() in standard_adapters:
            return f"LIMIT {limit}"

        # SQL Server / TSQL uses TOP
        if adapter_type.lower() in ['sqlserver', 'mssql', 'tsql']:
            # Note: This should go in SELECT clause, not at the end
            # For now, return None - we'll handle this in a future iteration
            return None

        # Oracle uses ROWNUM or FETCH FIRST (12c+)
        if adapter_type.lower() == 'oracle':
            return f"FETCH FIRST {limit} ROWS ONLY"

        # Default: standard LIMIT
        return f"LIMIT {limit}"


def optimize_jdbc_table_read(
    source_table: Any,
    compiled_sql: str,
    source_tables: List[Any],
    adapter_type: str
) -> str:
    """
    Optimize JDBC table read by pushing down filters.

    Args:
        source_table: SourceTableMetadata for this table
        compiled_sql: Compiled SQL from the model
        source_tables: All source tables in the query
        adapter_type: Source adapter type

    Returns:
        Table identifier (plain name or subquery with filters)
    """
    optimizer = FilterPushdownOptimizer(compiled_sql, source_tables)
    subquery = optimizer.build_pushdown_subquery(source_table, adapter_type)

    if subquery:
        return subquery
    else:
        # No filters to push down - read full table
        return source_table.qualified_name
