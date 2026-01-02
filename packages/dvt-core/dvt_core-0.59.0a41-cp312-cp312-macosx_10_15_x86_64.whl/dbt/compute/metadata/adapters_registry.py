# =============================================================================
# DVT Adapters Registry
# =============================================================================
# Read-only access to the shipped adapters_registry.duckdb database containing:
# - Type mappings (adapter -> Spark types)
# - Syntax rules (quoting, case sensitivity)
# - Adapter metadata queries (SQL templates)
#
# DVT v0.54.0: DuckDB-backed registry
# =============================================================================

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import re

try:
    import duckdb
except ImportError:
    duckdb = None  # Will raise helpful error on first use


@dataclass
class TypeMapping:
    """A single type mapping entry."""
    adapter_name: str
    adapter_type: str
    spark_type: str
    spark_version: str = "all"
    is_complex: bool = False
    cast_expression: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class SyntaxRule:
    """Syntax rules for a specific adapter."""
    adapter_name: str
    quote_start: str
    quote_end: str
    case_sensitivity: str  # 'lowercase', 'uppercase', 'case_insensitive'
    reserved_keywords: List[str]


@dataclass
class AdapterQuery:
    """SQL query template for adapter metadata extraction."""
    adapter_name: str
    query_type: str  # 'columns', 'tables', 'row_count', 'primary_key'
    query_template: str
    notes: Optional[str] = None


class AdaptersRegistry:
    """
    Read-only access to the shipped adapters registry database.

    This registry is shipped with DVT and provides:
    - Type mappings between adapter native types and Spark types
    - Syntax rules for SQL generation (quoting, case sensitivity)
    - Query templates for metadata extraction

    The registry is stored as a DuckDB database in the package's include/data directory.
    """

    _instance: Optional['AdaptersRegistry'] = None
    _registry_path: Optional[Path] = None

    def __new__(cls) -> 'AdaptersRegistry':
        """Singleton pattern for registry access."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._conn = None
        return cls._instance

    @classmethod
    def get_registry_path(cls) -> Path:
        """Return path to the shipped adapters_registry.duckdb."""
        if cls._registry_path is not None:
            return cls._registry_path

        # Find the package's include/data directory
        # This file is at: core/dbt/compute/metadata/adapters_registry.py
        # Registry is at: core/dbt/include/data/adapters_registry.duckdb
        this_file = Path(__file__)
        package_root = this_file.parent.parent.parent  # -> core/dbt
        registry_path = package_root / "include" / "data" / "adapters_registry.duckdb"

        if not registry_path.exists():
            raise FileNotFoundError(
                f"Adapters registry not found at: {registry_path}\n"
                "This file should be shipped with the DVT package. "
                "Please reinstall DVT or rebuild the registry with build_registry.py"
            )

        cls._registry_path = registry_path
        return registry_path

    def _get_connection(self) -> 'duckdb.DuckDBPyConnection':
        """Get or create a read-only connection to the registry."""
        if duckdb is None:
            raise ImportError(
                "duckdb is required for the adapters registry. "
                "Install with: pip install duckdb"
            )

        if self._conn is None:
            registry_path = self.get_registry_path()
            self._conn = duckdb.connect(str(registry_path), read_only=True)

        return self._conn

    def close(self) -> None:
        """Close the registry connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # =========================================================================
    # Type Mappings
    # =========================================================================

    def get_spark_type(
        self,
        adapter_name: str,
        adapter_type: str,
        spark_version: str = "all"
    ) -> Optional[TypeMapping]:
        """
        Look up the Spark type mapping for a given adapter type.

        :param adapter_name: Source adapter (e.g., 'postgres', 'snowflake')
        :param adapter_type: Adapter's native type (e.g., 'INTEGER', 'VARCHAR')
        :param spark_version: Target Spark version (default 'all')
        :returns: TypeMapping or None if not found
        """
        conn = self._get_connection()

        # Normalize inputs
        adapter_name = adapter_name.lower()
        adapter_type = adapter_type.upper().strip()

        # Remove size specifiers: VARCHAR(255) -> VARCHAR
        adapter_type_normalized = re.sub(r'\([^)]*\)', '', adapter_type).strip()

        result = conn.execute("""
            SELECT adapter_name, adapter_type, spark_type, spark_version,
                   is_complex, cast_expression, notes
            FROM datatype_mappings
            WHERE adapter_name = ?
              AND adapter_type = ?
              AND (spark_version = 'all' OR spark_version = ?)
            ORDER BY
                CASE WHEN spark_version = ? THEN 0 ELSE 1 END
            LIMIT 1
        """, [adapter_name, adapter_type_normalized, spark_version, spark_version]).fetchone()

        if result:
            return TypeMapping(
                adapter_name=result[0],
                adapter_type=result[1],
                spark_type=result[2],
                spark_version=result[3],
                is_complex=result[4],
                cast_expression=result[5],
                notes=result[6]
            )
        return None

    def get_all_mappings_for_adapter(self, adapter_name: str) -> List[TypeMapping]:
        """Get all type mappings for a specific adapter."""
        conn = self._get_connection()
        adapter_name = adapter_name.lower()

        results = conn.execute("""
            SELECT adapter_name, adapter_type, spark_type, spark_version,
                   is_complex, cast_expression, notes
            FROM datatype_mappings
            WHERE adapter_name = ?
            ORDER BY adapter_type
        """, [adapter_name]).fetchall()

        return [
            TypeMapping(
                adapter_name=row[0],
                adapter_type=row[1],
                spark_type=row[2],
                spark_version=row[3],
                is_complex=row[4],
                cast_expression=row[5],
                notes=row[6]
            )
            for row in results
        ]

    def get_supported_adapters(self) -> List[str]:
        """Get list of all supported adapter names."""
        conn = self._get_connection()
        results = conn.execute("""
            SELECT DISTINCT adapter_name FROM datatype_mappings ORDER BY adapter_name
        """).fetchall()
        return [row[0] for row in results]

    # =========================================================================
    # Syntax Rules
    # =========================================================================

    def get_syntax_rule(self, adapter_name: str) -> Optional[SyntaxRule]:
        """Get syntax rules for a specific adapter."""
        conn = self._get_connection()
        adapter_name = adapter_name.lower()

        result = conn.execute("""
            SELECT adapter_name, quote_start, quote_end, case_sensitivity, reserved_keywords
            FROM syntax_registry
            WHERE adapter_name = ?
        """, [adapter_name]).fetchone()

        if result:
            # Parse reserved keywords from comma-separated string
            keywords = []
            if result[4]:
                keywords = [kw.strip() for kw in result[4].split(',') if kw.strip()]

            return SyntaxRule(
                adapter_name=result[0],
                quote_start=result[1],
                quote_end=result[2],
                case_sensitivity=result[3],
                reserved_keywords=keywords
            )
        return None

    def quote_identifier(self, adapter_name: str, identifier: str) -> str:
        """Quote an identifier using the adapter's quoting rules."""
        rule = self.get_syntax_rule(adapter_name)
        if not rule:
            return f'"{identifier}"'  # Default to double quotes
        return f'{rule.quote_start}{identifier}{rule.quote_end}'

    def needs_quoting(self, adapter_name: str, identifier: str) -> bool:
        """Check if an identifier needs quoting (reserved keyword or special chars)."""
        rule = self.get_syntax_rule(adapter_name)
        if not rule:
            return False

        # Check if it's a reserved keyword
        upper_id = identifier.upper()
        if upper_id in [kw.upper() for kw in rule.reserved_keywords]:
            return True

        # Check for special characters or spaces
        if not identifier.replace('_', '').isalnum() or ' ' in identifier or '-' in identifier:
            return True

        return False

    def normalize_identifier(self, adapter_name: str, identifier: str) -> str:
        """Normalize an identifier based on the adapter's case sensitivity rules."""
        rule = self.get_syntax_rule(adapter_name)
        if not rule:
            return identifier

        case_rule = rule.case_sensitivity.lower()
        if case_rule == "uppercase":
            return identifier.upper()
        elif case_rule == "lowercase":
            return identifier.lower()
        return identifier  # case_insensitive or preserve

    # =========================================================================
    # Adapter Queries
    # =========================================================================

    def get_metadata_query(
        self,
        adapter_name: str,
        query_type: str
    ) -> Optional[AdapterQuery]:
        """
        Get SQL template for metadata extraction.

        :param adapter_name: Source adapter (e.g., 'postgres', 'snowflake')
        :param query_type: Query type: 'columns', 'tables', 'row_count', 'primary_key'
        :returns: AdapterQuery or None if not found
        """
        conn = self._get_connection()
        adapter_name = adapter_name.lower()

        result = conn.execute("""
            SELECT adapter_name, query_type, query_template, notes
            FROM adapter_queries
            WHERE adapter_name = ? AND query_type = ?
        """, [adapter_name, query_type]).fetchone()

        if result:
            return AdapterQuery(
                adapter_name=result[0],
                query_type=result[1],
                query_template=result[2],
                notes=result[3]
            )
        return None

    def get_all_queries_for_adapter(self, adapter_name: str) -> List[AdapterQuery]:
        """Get all query templates for a specific adapter."""
        conn = self._get_connection()
        adapter_name = adapter_name.lower()

        results = conn.execute("""
            SELECT adapter_name, query_type, query_template, notes
            FROM adapter_queries
            WHERE adapter_name = ?
            ORDER BY query_type
        """, [adapter_name]).fetchall()

        return [
            AdapterQuery(
                adapter_name=row[0],
                query_type=row[1],
                query_template=row[2],
                notes=row[3]
            )
            for row in results
        ]


# =============================================================================
# Module-level convenience functions
# =============================================================================

def get_registry() -> AdaptersRegistry:
    """Get the singleton AdaptersRegistry instance."""
    return AdaptersRegistry()


def get_spark_type(
    adapter_name: str,
    adapter_type: str,
    spark_version: str = "all"
) -> Optional[TypeMapping]:
    """
    Convenience function to look up Spark type mapping.

    :param adapter_name: Source adapter (e.g., 'postgres', 'snowflake')
    :param adapter_type: Adapter's native type (e.g., 'INTEGER', 'VARCHAR')
    :param spark_version: Target Spark version (default 'all')
    :returns: TypeMapping or None if not found
    """
    return get_registry().get_spark_type(adapter_name, adapter_type, spark_version)


def get_syntax_rule(adapter_name: str) -> Optional[SyntaxRule]:
    """Convenience function to get syntax rules for an adapter."""
    return get_registry().get_syntax_rule(adapter_name)


def get_metadata_query(adapter_name: str, query_type: str) -> Optional[AdapterQuery]:
    """Convenience function to get a metadata query template."""
    return get_registry().get_metadata_query(adapter_name, query_type)


def quote_identifier(adapter_name: str, identifier: str) -> str:
    """Convenience function to quote an identifier."""
    return get_registry().quote_identifier(adapter_name, identifier)


def normalize_identifier(adapter_name: str, identifier: str) -> str:
    """Convenience function to normalize an identifier."""
    return get_registry().normalize_identifier(adapter_name, identifier)
