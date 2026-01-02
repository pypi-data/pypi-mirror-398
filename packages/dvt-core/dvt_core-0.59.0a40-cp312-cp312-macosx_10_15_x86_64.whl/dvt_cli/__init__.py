"""
DVT CLI Entry Point Package

This standalone package provides the entry point for the DVT command-line
interface. It's separate from the 'dbt' namespace to avoid conflicts with
dbt-core during the initial import.

Why this package exists:
-----------------------
DVT extends dbt-core with additional commands (compute, target, migrate).
However, dbt adapters (like dbt-postgres) depend on dbt-core, so both
dvt-core and dbt-core end up installed together. Both packages provide
the 'dbt' namespace, which causes import conflicts.

By using a separate 'dvt_cli' package for the entry point, we can
manipulate sys.path BEFORE any 'dbt' modules are imported, ensuring
DVT's extended dbt package takes precedence.
"""

import sys
from pathlib import Path


def _ensure_dvt_precedence():
    """
    Ensure DVT's dbt package takes precedence over dbt-core's version.

    When both dvt-core and dbt-core are installed (dbt-core comes as a
    dependency of dbt adapters like dbt-postgres), Python's namespace
    package mechanism may load dbt-core's modules instead of DVT's.

    This function manipulates sys.path to ensure DVT's path comes first,
    guaranteeing that DVT's extended CLI (with compute, target, migrate
    commands) is used instead of vanilla dbt-core.
    """
    # Find where dvt-core's dbt package is located
    # This file is at: <dvt-core>/dvt_cli/__init__.py
    # So the package root (containing 'dbt/') is: <dvt-core>/
    this_file = Path(__file__).resolve()
    dvt_package_root = this_file.parent.parent

    dvt_path = str(dvt_package_root)

    # Remove dvt_path if it's already in sys.path (to move it to front)
    if dvt_path in sys.path:
        sys.path.remove(dvt_path)

    # Insert at the beginning to take precedence over site-packages
    sys.path.insert(0, dvt_path)

    # Clear any already-imported dbt modules so they get re-imported
    # from the correct location
    modules_to_clear = [k for k in list(sys.modules.keys()) if k.startswith('dbt')]
    for mod in modules_to_clear:
        del sys.modules[mod]


def dvt_cli():
    """
    DVT CLI entry point function.

    This is the main entry point for the 'dvt' command. It ensures DVT's
    version of the dbt package takes precedence, then runs the CLI.

    Users who want backward compatibility with 'dbt' command can create
    a shell alias: alias dbt=dvt
    """
    _ensure_dvt_precedence()

    # Now import the CLI - this will get DVT's version
    from dbt.cli.main import cli
    cli()
