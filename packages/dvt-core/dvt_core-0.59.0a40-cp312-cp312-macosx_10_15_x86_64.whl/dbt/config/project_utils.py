"""Utility functions for working with dbt project files."""

from pathlib import Path
from typing import Optional
import yaml


def get_project_profile_name(project_dir) -> Optional[str]:
    """
    Read profile name from dvt_project.yml or dbt_project.yml in the given directory.

    v0.59.0a17+: Check dvt_project.yml first (DVT projects), then fall back to
    dbt_project.yml (legacy dbt projects). Used by ALL DVT commands for
    project-aware profile detection.

    Args:
        project_dir: Path to the project directory (Path or str)

    Returns:
        Profile name if found, None otherwise
    """
    # v0.59.0a18: Handle both Path and string input
    if project_dir is None:
        project_dir = Path.cwd()
    elif not isinstance(project_dir, Path):
        project_dir = Path(project_dir)

    # Check dvt_project.yml first, then dbt_project.yml
    project_files = ["dvt_project.yml", "dbt_project.yml"]

    for project_file in project_files:
        try:
            project_yml_path = project_dir / project_file
            if not project_yml_path.exists():
                continue

            with open(project_yml_path) as f:
                project = yaml.safe_load(f)
                if project and "profile" in project:
                    return project.get("profile")
                # If no explicit profile, use project name as profile name
                if project and "name" in project:
                    return project.get("name")
        except Exception:
            # Silently handle any YAML parsing or file read errors
            continue

    return None
