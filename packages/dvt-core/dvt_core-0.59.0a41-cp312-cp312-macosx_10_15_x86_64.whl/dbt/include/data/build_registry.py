#!/usr/bin/env python3
"""
Build Script for DVT Adapters Registry

This script reads CSV files from the csv/ directory and creates
adapters_registry.duckdb with pre-populated type mappings, syntax rules,
and adapter queries.

Usage:
    python build_registry.py

The resulting adapters_registry.duckdb is shipped with the DVT package.
"""

import csv
import os
from pathlib import Path

try:
    import duckdb
except ImportError:
    print("Error: duckdb is required. Install with: pip install duckdb")
    exit(1)


def get_script_dir() -> Path:
    """Get directory containing this script."""
    return Path(__file__).parent


def create_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Create the database schema."""

    # Table: datatype_mappings
    conn.execute("""
        CREATE TABLE IF NOT EXISTS datatype_mappings (
            adapter_name VARCHAR NOT NULL,
            adapter_type VARCHAR NOT NULL,
            spark_type VARCHAR NOT NULL,
            spark_version VARCHAR DEFAULT 'all',
            is_complex BOOLEAN DEFAULT FALSE,
            cast_expression VARCHAR,
            notes VARCHAR,
            UNIQUE (adapter_name, adapter_type, spark_version)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_datatype_lookup
        ON datatype_mappings(adapter_name, adapter_type)
    """)

    # Table: syntax_registry
    conn.execute("""
        CREATE TABLE IF NOT EXISTS syntax_registry (
            adapter_name VARCHAR NOT NULL PRIMARY KEY,
            quote_start VARCHAR NOT NULL,
            quote_end VARCHAR NOT NULL,
            case_sensitivity VARCHAR NOT NULL,
            reserved_keywords VARCHAR
        )
    """)

    # Table: adapter_queries
    conn.execute("""
        CREATE TABLE IF NOT EXISTS adapter_queries (
            adapter_name VARCHAR NOT NULL,
            query_type VARCHAR NOT NULL,
            query_template VARCHAR NOT NULL,
            notes VARCHAR,
            PRIMARY KEY (adapter_name, query_type)
        )
    """)

    print("Schema created successfully")


def load_type_mappings(conn: duckdb.DuckDBPyConnection, csv_dir: Path) -> int:
    """Load type mappings from CSV files."""
    total_rows = 0

    # Find all type_mappings_*.csv files
    for csv_file in sorted(csv_dir.glob("type_mappings_*.csv")):
        adapter_name = csv_file.stem.replace("type_mappings_", "")
        rows_loaded = 0

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                conn.execute("""
                    INSERT OR REPLACE INTO datatype_mappings
                    (adapter_name, adapter_type, spark_type, spark_version,
                     is_complex, cast_expression, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, [
                    adapter_name,
                    row['adapter_type'].strip(),
                    row['spark_type'].strip(),
                    row.get('spark_version', 'all').strip() or 'all',
                    row.get('is_complex', 'false').strip().lower() == 'true',
                    row.get('cast_expression', '').strip() or None,
                    row.get('notes', '').strip() or None,
                ])
                rows_loaded += 1

        print(f"  Loaded {rows_loaded} type mappings for {adapter_name}")
        total_rows += rows_loaded

    return total_rows


def load_syntax_rules(conn: duckdb.DuckDBPyConnection, csv_dir: Path) -> int:
    """Load syntax rules from CSV file."""
    csv_file = csv_dir / "syntax_rules.csv"
    if not csv_file.exists():
        print("  Warning: syntax_rules.csv not found")
        return 0

    rows_loaded = 0
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            conn.execute("""
                INSERT OR REPLACE INTO syntax_registry
                (adapter_name, quote_start, quote_end, case_sensitivity, reserved_keywords)
                VALUES (?, ?, ?, ?, ?)
            """, [
                row['adapter_name'].strip(),
                row['quote_start'].strip(),
                row['quote_end'].strip(),
                row['case_sensitivity'].strip(),
                row.get('reserved_keywords', '').strip() or None,
            ])
            rows_loaded += 1

    print(f"  Loaded {rows_loaded} syntax rules")
    return rows_loaded


def load_adapter_queries(conn: duckdb.DuckDBPyConnection, csv_dir: Path) -> int:
    """Load adapter queries from CSV file."""
    csv_file = csv_dir / "adapter_queries.csv"
    if not csv_file.exists():
        print("  Warning: adapter_queries.csv not found")
        return 0

    rows_loaded = 0
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            conn.execute("""
                INSERT OR REPLACE INTO adapter_queries
                (adapter_name, query_type, query_template, notes)
                VALUES (?, ?, ?, ?)
            """, [
                row['adapter_name'].strip(),
                row['query_type'].strip(),
                row['query_template'].strip(),
                row.get('notes', '').strip() or None,
            ])
            rows_loaded += 1

    print(f"  Loaded {rows_loaded} adapter queries")
    return rows_loaded


def print_stats(conn: duckdb.DuckDBPyConnection) -> None:
    """Print statistics about the loaded data."""
    print("\n=== Registry Statistics ===")

    # Type mappings by adapter
    result = conn.execute("""
        SELECT adapter_name, COUNT(*) as count
        FROM datatype_mappings
        GROUP BY adapter_name
        ORDER BY adapter_name
    """).fetchall()
    print("\nType mappings per adapter:")
    for row in result:
        print(f"  {row[0]}: {row[1]}")

    # Syntax rules
    result = conn.execute("SELECT COUNT(*) FROM syntax_registry").fetchone()
    print(f"\nSyntax rules: {result[0]} adapters")

    # Adapter queries
    result = conn.execute("""
        SELECT adapter_name, COUNT(*) as count
        FROM adapter_queries
        GROUP BY adapter_name
        ORDER BY adapter_name
    """).fetchall()
    print("\nAdapter queries:")
    for row in result:
        print(f"  {row[0]}: {row[1]} queries")


def main():
    script_dir = get_script_dir()
    csv_dir = script_dir / "csv"
    db_path = script_dir / "adapters_registry.duckdb"

    print(f"Building adapters_registry.duckdb")
    print(f"CSV directory: {csv_dir}")
    print(f"Output: {db_path}")
    print()

    # Remove existing database
    if db_path.exists():
        os.remove(db_path)
        print("Removed existing database")

    # Create new database
    conn = duckdb.connect(str(db_path))

    try:
        # Create schema
        print("\nCreating schema...")
        create_schema(conn)

        # Load data
        print("\nLoading type mappings...")
        type_count = load_type_mappings(conn, csv_dir)

        print("\nLoading syntax rules...")
        syntax_count = load_syntax_rules(conn, csv_dir)

        print("\nLoading adapter queries...")
        query_count = load_adapter_queries(conn, csv_dir)

        # Print stats
        print_stats(conn)

        print(f"\n=== Build Complete ===")
        print(f"Total: {type_count} type mappings, {syntax_count} syntax rules, {query_count} queries")
        print(f"Database size: {db_path.stat().st_size / 1024:.1f} KB")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
