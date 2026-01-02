from pathlib import Path

from dbt.config.project import PartialProject
from dbt.exceptions import DbtProjectError


def default_project_dir() -> Path:
    """Return the default project directory.

    DVT: Support both dvt_project.yml (DVT projects) and dbt_project.yml (adapter packages).
    Priority: dvt_project.yml > dbt_project.yml
    """
    paths = list(Path.cwd().parents)
    paths.insert(0, Path.cwd())
    # First look for dvt_project.yml
    dvt_result = next((x for x in paths if (x / "dvt_project.yml").exists()), None)
    if dvt_result:
        return dvt_result
    # Fall back to dbt_project.yml (for adapter packages)
    return next((x for x in paths if (x / "dbt_project.yml").exists()), Path.cwd())


def default_profiles_dir() -> Path:
    """Return the default profiles directory for DVT.

    Priority:
    1. CWD with profiles.yml
    2. CWD/.dvt/profiles.yml
    3. ~/.dvt/profiles.yml (DVT standard location)

    Note: DVT does NOT fall back to ~/.dbt/ - use 'dvt migrate' to move configs.
    """
    cwd = Path.cwd()
    home = Path.home()

    if (cwd / "profiles.yml").exists():
        return cwd
    elif (cwd / ".dvt" / "profiles.yml").exists():
        return cwd / ".dvt"
    else:
        # DVT always uses ~/.dvt/ - no fallback to ~/.dbt/
        return home / ".dvt"


def default_log_path(project_dir: Path, verify_version: bool = False) -> Path:
    """If available, derive a default log path from dbt_project.yml. Otherwise, default to "logs".
    Known limitations:
    1. Using PartialProject here, so no jinja rendering of log-path.
    2. Programmatic invocations of the cli via dbtRunner may pass a Project object directly,
       which is not being taken into consideration here to extract a log-path.
    """
    default_log_path = Path("logs")
    try:
        partial = PartialProject.from_project_root(str(project_dir), verify_version=verify_version)
        partial_log_path = partial.project_dict.get("log-path") or default_log_path
        default_log_path = Path(project_dir) / partial_log_path
    except DbtProjectError:
        pass

    return default_log_path
