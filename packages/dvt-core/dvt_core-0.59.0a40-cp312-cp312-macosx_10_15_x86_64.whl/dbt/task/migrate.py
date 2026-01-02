"""
DVT Migration Task - Migrate from dbt to DVT configuration.

Two modes:
- Mode A: Convert dbt project to DVT (not in DVT project)
- Mode B: Import dbt project INTO DVT project (in DVT project)
"""
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import shutil
import click


@dataclass
class MigrationResult:
    """Result of a migration operation."""

    success: bool
    message: str
    files_copied: int = 0


class MigrateTask:
    """
    DVT Migration Task.

    Handles two modes:
    - Mode A: Convert dbt project to DVT (when not in DVT project)
    - Mode B: Import dbt project INTO DVT project (when in DVT project)
    """

    def __init__(
        self,
        source_path: Optional[str] = None,
        profiles_only: bool = False,
        project_only: bool = False,
        full: bool = False,
        dry_run: bool = False,
        project_dir: Optional[str] = None,
    ):
        self.source_path = Path(source_path) if source_path else None
        self.profiles_only = profiles_only
        self.project_only = project_only
        self.full = full
        self.dry_run = dry_run
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()

    def run(self) -> bool:
        """Execute migration based on context and flags."""
        # Detect which mode we're in
        in_dvt_project = (self.project_dir / "dvt_project.yml").exists()

        if in_dvt_project and self.source_path:
            # Mode B: Import dbt project INTO current DVT project
            return self._import_dbt_project()
        elif in_dvt_project and not self.source_path:
            # Inside DVT project but no path - show help
            click.echo("You are inside a DVT project.")
            click.echo("To import a dbt project, provide the path:")
            click.echo("  dvt migrate /path/to/dbt_project")
            return True
        else:
            # Mode A: Convert current dbt project to DVT
            return self._convert_to_dvt()

    def _convert_to_dvt(self) -> bool:
        """Mode A: Convert dbt project in current directory to DVT."""
        results = []

        if self.profiles_only:
            results.append(self._migrate_profiles())
        elif self.project_only:
            results.append(self._migrate_project_file())
        elif self.full:
            results.append(self._migrate_profiles())
            results.append(self._migrate_project_file())
        else:
            results = self._auto_detect_and_migrate()

        self._show_summary(results)
        return all(r.success for r in results if r)

    def _auto_detect_and_migrate(self) -> List[MigrationResult]:
        """Auto-detect what needs to be migrated."""
        results = []

        click.echo("Detecting dbt configuration...")

        dbt_profiles_path = Path.home() / ".dbt" / "profiles.yml"
        dbt_project_path = self.project_dir / "dbt_project.yml"

        has_dbt_profiles = dbt_profiles_path.exists()
        has_dbt_project = dbt_project_path.exists()

        if has_dbt_profiles:
            click.echo(f"  Found ~/.dbt/profiles.yml")
        if has_dbt_project:
            click.echo(f"  Found dbt_project.yml")

        if not has_dbt_profiles and not has_dbt_project:
            click.echo("\nNo dbt configuration found - nothing to migrate.")
            click.echo("Use 'dvt init' to create a new DVT project.")
            return [MigrationResult(True, "Nothing to migrate")]

        click.echo("")

        # Migrate profiles if found
        if has_dbt_profiles:
            click.echo("Migrating profiles...")
            results.append(self._migrate_profiles())

        # Migrate project if found
        if has_dbt_project:
            click.echo("\nMigrating project...")
            results.append(self._migrate_project_file())

        return results

    def _migrate_profiles(self) -> MigrationResult:
        """Migrate project-specific profile from ~/.dbt/profiles.yml to ~/.dvt/profiles.yml.

        v0.59.0a2: Changed to be surgical - only copies the profile matching the current
        project, not all profiles from ~/.dbt/profiles.yml.

        v0.59.0a19: If profile not found in ~/.dbt/profiles.yml, creates a starter
        DuckDB profile (like dvt init does).
        """
        try:
            import yaml
        except ImportError:
            import ruamel.yaml as yaml

        old_path = Path.home() / ".dbt" / "profiles.yml"
        new_path = Path.home() / ".dvt" / "profiles.yml"

        # Get the profile name from dbt_project.yml
        dbt_project_path = self.project_dir / "dbt_project.yml"
        if dbt_project_path.exists():
            with open(dbt_project_path) as f:
                project_config = yaml.safe_load(f) or {}
            # Use 'profile' field, fall back to 'name', then directory name
            profile_name = project_config.get("profile", project_config.get("name", self.project_dir.name))
        else:
            # No dbt_project.yml, use directory name
            profile_name = self.project_dir.name

        # Check if profile exists in ~/.dbt/profiles.yml
        profile_to_migrate = None
        if old_path.exists():
            with open(old_path) as f:
                old_profiles = yaml.safe_load(f) or {}
            if profile_name in old_profiles:
                profile_to_migrate = {profile_name: old_profiles[profile_name]}

        # v0.59.0a19: If profile not found, create a starter DuckDB profile
        if profile_to_migrate is None:
            click.echo(f"  No profile '{profile_name}' found in ~/.dbt/profiles.yml")
            click.echo(f"  Creating starter DuckDB profile...")

            # Create .dvt directory and default.duckdb
            dvt_dir = self.project_dir / ".dvt"
            dvt_dir.mkdir(parents=True, exist_ok=True)
            duckdb_path = dvt_dir / "default.duckdb"

            # Create empty DuckDB file if it doesn't exist
            if not duckdb_path.exists():
                try:
                    import duckdb
                    conn = duckdb.connect(str(duckdb_path))
                    conn.close()
                except Exception:
                    # Just create empty file if duckdb import fails
                    duckdb_path.touch()

            # Create starter profile
            profile_to_migrate = {
                profile_name: {
                    "target": "dev",
                    "outputs": {
                        "dev": {
                            "type": "duckdb",
                            "path": str(duckdb_path.resolve()),
                            "threads": 4,
                        }
                    }
                }
            }

        # Merge with existing DVT profiles if any
        if new_path.exists():
            with open(new_path) as f:
                existing = yaml.safe_load(f) or {}
            # DVT profiles take precedence (don't overwrite)
            if profile_name not in existing:
                existing[profile_name] = profile_to_migrate[profile_name]
                merged = True
            else:
                click.echo(f"  Profile '{profile_name}' already exists in ~/.dvt/profiles.yml - skipping")
                return MigrationResult(True, f"Profile '{profile_name}' already exists")
            profiles = existing
        else:
            profiles = profile_to_migrate
            merged = False

        # Write to DVT profiles
        if not self.dry_run:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            with open(new_path, "w") as f:
                f.write("# DVT Profiles Configuration\n\n")
                yaml.dump(profiles, f, default_flow_style=False)

            action = "Merged" if merged else "Migrated"
            click.echo(f"  {action} profile '{profile_name}' to ~/.dvt/profiles.yml")
        else:
            click.echo(f"  [DRY RUN] Would migrate profile '{profile_name}'")

        return MigrationResult(True, f"Migrated profile '{profile_name}'")

    def _migrate_project_file(self) -> MigrationResult:
        """Create dvt_project.yml from fresh template (like dbt init) + DVT additions.

        v0.59.0a2: Creates fresh template matching dbt init format, plus DVT-specific
        flatfile-paths config. Creates flatfiles/ directory. User can copy project-specific
        configs from the backed-up dbt_project.yml.bak if needed.
        """
        try:
            import yaml
        except ImportError:
            import ruamel.yaml as yaml

        old_path = self.project_dir / "dbt_project.yml"
        new_path = self.project_dir / "dvt_project.yml"
        backup_path = self.project_dir / "dbt_project.yml.bak"

        if not old_path.exists():
            click.echo("  No dbt_project.yml found")
            return MigrationResult(False, "No dbt_project.yml found")

        if new_path.exists():
            click.echo("  dvt_project.yml already exists - skipping")
            return MigrationResult(True, "dvt_project.yml already exists")

        # Get project name and profile from dbt_project.yml
        project_name = self.project_dir.name
        profile_name = project_name  # Default to project name
        with open(old_path, "r") as f:
            try:
                config = yaml.safe_load(f)
                if config:
                    if "name" in config:
                        project_name = config["name"]
                    if "profile" in config:
                        profile_name = config["profile"]
            except Exception:
                pass

        if not self.dry_run:
            # 1. Backup dbt_project.yml
            if backup_path.exists():
                # Add timestamp if backup already exists
                import time

                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_path = self.project_dir / f"dbt_project.yml.{timestamp}.bak"
            shutil.copy2(old_path, backup_path)
            click.echo(f"  Backed up dbt_project.yml → {backup_path.name}")

            # 2. Create fresh dvt_project.yml from standard dbt init template + DVT additions
            dvt_project_content = f"""name: '{project_name}'
version: '1.0.0'

# This setting configures which "profile" dbt uses for this project.
profile: '{profile_name}'

# These configurations specify where dbt should look for different types of files.
# The `model-paths` config, for example, states that models in this project can be
# found in the "models/" directory. You probably won't need to change these!
model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

# DVT-specific: Path for flat files (CSV, Parquet, etc.) for local data ingestion
flatfile-paths: ["flatfiles"]

clean-targets:
  - "target"
  - "dbt_packages"

# Configuring models
# Full documentation: https://docs.getdbt.com/docs/configuring-models

# In this example config, we tell dbt to build all models in the example/
# directory as views. These settings can be overridden in the individual model
# files using the `{{ config(...) }}` macro.
models:
  {project_name}:
    # Config indicated by + and applies to all files under models/example/
    +materialized: view
"""
            with open(new_path, "w") as f:
                f.write(dvt_project_content)
            click.echo("  Created dvt_project.yml")

            # 3. Create flatfiles/ directory
            flatfiles_dir = self.project_dir / "flatfiles"
            flatfiles_dir.mkdir(exist_ok=True)
            gitignore_path = flatfiles_dir / ".gitignore"
            if not gitignore_path.exists():
                with open(gitignore_path, "w") as f:
                    f.write("# Ignore all flat files (CSV, Parquet, etc.)\n*\n!.gitignore\n")
            click.echo("  Created flatfiles/ directory")

            # 4. Create .dvt/ directory with computes.yml and metadata_store.duckdb
            dvt_dir = self.project_dir / ".dvt"
            dvt_dir.mkdir(exist_ok=True)

            # Create computes.yml
            computes_path = dvt_dir / "computes.yml"
            if not computes_path.exists():
                computes_content = """# DVT Compute Configuration
# See: https://github.com/dvt-core/dvt-core#compute-configuration

# Default compute engine for federation queries
target_compute: spark-local

# Available compute engines
computes:
  spark-local:
    type: local
    app_name: DVT-Spark
    config:
      spark.sql.execution.arrow.pyspark.enabled: "true"
      spark.sql.adaptive.enabled: "true"
"""
                with open(computes_path, "w") as f:
                    f.write(computes_content)
            click.echo("  Created .dvt/computes.yml")

            # Create metadata_store.duckdb
            metadata_store_path = dvt_dir / "metadata_store.duckdb"
            if not metadata_store_path.exists():
                try:
                    import duckdb
                    conn = duckdb.connect(str(metadata_store_path))
                    conn.close()
                except Exception:
                    metadata_store_path.touch()
            click.echo("  Created .dvt/metadata_store.duckdb")
        else:
            click.echo("  [DRY RUN] Would backup dbt_project.yml")
            click.echo("  [DRY RUN] Would create dvt_project.yml")
            click.echo("  [DRY RUN] Would create flatfiles/ directory")

        return MigrationResult(True, "Project migrated")

    def _import_dbt_project(self) -> bool:
        """Mode B: Import dbt/DVT project INTO current DVT project.

        v0.59.0a23: Now supports importing both dbt and DVT projects.
        Checks for dvt_project.yml first, then dbt_project.yml.

        v0.59.0a24: For dbt projects ONLY, patches sources.yml files to add
        DVT's required connection: config. DVT projects are expected to
        already have this config (user's responsibility).
        """
        try:
            import yaml
        except ImportError:
            import ruamel.yaml as yaml

        # Verify source is a dbt or DVT project (check DVT first)
        dvt_config_path = self.source_path / "dvt_project.yml"
        dbt_config_path = self.source_path / "dbt_project.yml"

        if dvt_config_path.exists():
            source_config_path = dvt_config_path
            project_type = "DVT"
        elif dbt_config_path.exists():
            source_config_path = dbt_config_path
            project_type = "dbt"
        else:
            click.echo(f"Error: No dvt_project.yml or dbt_project.yml found in {self.source_path}")
            return False

        # Get source project name and profile from project config
        with open(source_config_path) as f:
            project_config = yaml.safe_load(f)
        source_name = project_config.get("name", self.source_path.name)
        source_profile_name = project_config.get("profile", source_name)

        if self.dry_run:
            click.echo(f"Importing {project_type} project '{source_name}' (DRY RUN)...")
        else:
            click.echo(f"Importing {project_type} project '{source_name}' into current DVT project...")

        click.echo("")
        results = []

        # Copy directories
        dirs_to_copy = ["models", "seeds", "tests", "macros", "snapshots", "analyses"]
        models_copied = False
        for dir_name in dirs_to_copy:
            result = self._copy_directory(dir_name, source_name)
            if result:
                results.append(result)
                if dir_name == "models" and result.success and result.files_copied > 0:
                    models_copied = True

        # v0.59.0a24: Patch sources.yml for dbt projects ONLY
        # DVT projects should already have connection: config - user's responsibility
        if project_type == "dbt" and models_copied:
            # Get the default target from source profile to build connection name
            default_target = self._get_source_default_target(source_profile_name)
            connection_name = f"{source_name}_{default_target}"
            patched = self._patch_sources_connection(
                self.project_dir / "models" / source_name,
                connection_name
            )
            if patched > 0:
                click.echo(f"  Patched {patched} source(s) with connection: {connection_name}")
        elif project_type == "DVT":
            # Warn DVT project users to verify connection config
            models_dir = self.project_dir / "models" / source_name
            if models_dir.exists():
                sources_files = list(models_dir.rglob("*sources*.yml"))
                if sources_files:
                    click.echo(f"  Note: DVT project detected - verify sources.yml has connection: config")

        # Merge profile targets
        profile_result = self._import_profile_targets(source_name)
        results.append(profile_result)

        self._show_import_summary(source_name, results)
        return all(r.success for r in results if r)

    def _get_source_default_target(self, profile_name: str) -> str:
        """Get the default target from a source profile.

        Checks ~/.dvt/profiles.yml first, then ~/.dbt/profiles.yml.
        Returns 'default' if profile not found.
        """
        try:
            import yaml
        except ImportError:
            import ruamel.yaml as yaml

        # Check DVT profiles first
        dvt_profiles_path = Path.home() / ".dvt" / "profiles.yml"
        if dvt_profiles_path.exists():
            with open(dvt_profiles_path) as f:
                profiles = yaml.safe_load(f) or {}
            if profile_name in profiles:
                return profiles[profile_name].get("target", "default")

        # Then check dbt profiles
        dbt_profiles_path = Path.home() / ".dbt" / "profiles.yml"
        if dbt_profiles_path.exists():
            with open(dbt_profiles_path) as f:
                profiles = yaml.safe_load(f) or {}
            if profile_name in profiles:
                return profiles[profile_name].get("target", "default")

        return "default"

    def _patch_sources_connection(self, target_dir: Path, connection_name: str) -> int:
        """Add connection: config to all .yml files that contain sources definitions.

        ONLY called for dbt projects (not DVT projects).
        DVT requires sources to specify which connection they read from.
        For imported dbt projects, default to the imported project's connection.

        v0.59.0a24: New method for surgical sources.yml patching.
        Note: Sources can be defined in ANY .yml file (not just *sources*.yml).
        A file contains sources if it has a top-level 'sources:' key.

        Args:
            target_dir: Directory containing the copied models
            connection_name: Connection name to add (e.g., "Cocacola_DWH_postgres")

        Returns:
            Count of patched sources.
        """
        try:
            import yaml
        except ImportError:
            import ruamel.yaml as yaml

        if self.dry_run:
            # Count what would be patched by scanning ALL .yml files for sources: key
            count = 0
            for yml_file in target_dir.rglob("*.yml"):
                try:
                    with open(yml_file) as f:
                        content = yaml.safe_load(f) or {}
                    if content.get("sources"):
                        for source in content.get("sources", []):
                            if "connection" not in source:
                                count += 1
                except Exception:
                    pass
            if count > 0:
                click.echo(f"  [DRY RUN] Would patch {count} source(s) with connection: {connection_name}")
            return count

        patched_count = 0

        # Scan ALL .yml files for sources: key (sources can be in any yml file)
        for yml_file in target_dir.rglob("*.yml"):
            try:
                with open(yml_file) as f:
                    content = yaml.safe_load(f) or {}

                # Skip if no sources defined in this file
                if not content.get("sources"):
                    continue

                modified = False
                for source in content.get("sources", []):
                    if "connection" not in source:
                        source["connection"] = connection_name
                        modified = True
                        patched_count += 1

                if modified:
                    with open(yml_file, "w") as f:
                        # Add header comment
                        f.write("# DVT: Added connection config for multi-source support\n")
                        f.write(f"# connection: {connection_name} (auto-added by dvt migrate)\n\n")
                        yaml.dump(content, f, default_flow_style=False, sort_keys=False)
                    click.echo(f"    + Patched {yml_file.name}: added connection: {connection_name}")
            except Exception as e:
                click.echo(f"    ! Warning: Could not patch {yml_file.name}: {e}")

        return patched_count

    def _copy_directory(self, dir_name: str, source_name: str) -> Optional[MigrationResult]:
        """Copy a directory from source to target/<source_name>/.

        v0.59.0a23: Now skips if target directory already exists to prevent duplicates.
        """
        source_dir = self.source_path / dir_name
        if not source_dir.exists():
            return None

        target_dir = self.project_dir / dir_name / source_name

        # Check if already imported - skip to prevent duplicates
        if target_dir.exists():
            file_count = sum(1 for _ in target_dir.rglob("*") if _.is_file())
            click.echo(f"  Skipped {dir_name}/ (already exists with {file_count} files)")
            return MigrationResult(True, f"{dir_name}/ (skipped)", 0)

        if self.dry_run:
            file_count = sum(1 for _ in source_dir.rglob("*") if _.is_file())
            click.echo(f"  [DRY RUN] Would copy {dir_name}/ ({file_count} files) → {dir_name}/{source_name}/")
            return MigrationResult(True, f"{dir_name}/ (dry run)", file_count)

        target_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)

        file_count = sum(1 for _ in target_dir.rglob("*") if _.is_file())
        click.echo(f"  Copied {dir_name}/ ({file_count} files)")

        return MigrationResult(True, f"{dir_name}/", file_count)

    def _import_profile_targets(self, source_name: str) -> MigrationResult:
        """Import profile targets from source dbt project into DVT profile.

        v0.59.0a23: Now checks both ~/.dvt/profiles.yml and ~/.dbt/profiles.yml
        for the source profile, preferring DVT profiles.
        """
        try:
            import yaml
        except ImportError:
            import ruamel.yaml as yaml

        # Read DVT project to get profile name
        dvt_config_path = self.project_dir / "dvt_project.yml"
        with open(dvt_config_path) as f:
            dvt_config = yaml.safe_load(f)
        dvt_profile_name = dvt_config.get("profile", dvt_config.get("name"))

        # Read source dbt project to get its profile name
        source_config_path = self.source_path / "dbt_project.yml"
        with open(source_config_path) as f:
            source_config = yaml.safe_load(f)
        source_profile_name = source_config.get("profile", source_config.get("name"))

        # Read source profiles - check DVT profiles first, then dbt profiles
        dvt_profiles_path = Path.home() / ".dvt" / "profiles.yml"
        dbt_profiles_path = Path.home() / ".dbt" / "profiles.yml"

        source_profile = {}
        source_outputs = {}
        profile_source = None

        # First check ~/.dvt/profiles.yml
        if dvt_profiles_path.exists():
            with open(dvt_profiles_path) as f:
                dvt_all_profiles = yaml.safe_load(f) or {}
            if source_profile_name in dvt_all_profiles:
                source_profile = dvt_all_profiles[source_profile_name]
                source_outputs = source_profile.get("outputs", {})
                profile_source = "~/.dvt/profiles.yml"

        # If not found in DVT profiles, try ~/.dbt/profiles.yml
        if not source_outputs and dbt_profiles_path.exists():
            with open(dbt_profiles_path) as f:
                dbt_profiles = yaml.safe_load(f) or {}
            if source_profile_name in dbt_profiles:
                source_profile = dbt_profiles[source_profile_name]
                source_outputs = source_profile.get("outputs", {})
                profile_source = "~/.dbt/profiles.yml"

        if not source_outputs:
            click.echo(f"  No profile '{source_profile_name}' found in ~/.dvt/profiles.yml or ~/.dbt/profiles.yml")
            return MigrationResult(True, "No source profile found")

        click.echo(f"  Found profile '{source_profile_name}' in {profile_source} with {len(source_outputs)} target(s)")

        # Read current DVT profiles for destination
        if not dvt_profiles_path.exists():
            click.echo("  No ~/.dvt/profiles.yml found - skipping target import")
            return MigrationResult(False, "No DVT profiles found")

        with open(dvt_profiles_path) as f:
            dvt_profiles = yaml.safe_load(f) or {}

        dvt_profile = dvt_profiles.get(dvt_profile_name, {"target": "dev", "outputs": {}})

        # Merge source outputs with prefix
        merged_count = 0
        skipped_count = 0
        merged_names = []
        for output_name, output_config in source_outputs.items():
            new_name = f"{source_name}_{output_name}"
            if new_name not in dvt_profile.get("outputs", {}):
                dvt_profile.setdefault("outputs", {})[new_name] = output_config
                merged_count += 1
                merged_names.append(new_name)
            else:
                skipped_count += 1

        dvt_profiles[dvt_profile_name] = dvt_profile

        if not self.dry_run:
            if merged_count > 0:
                with open(dvt_profiles_path, "w") as f:
                    f.write("# DVT Profiles Configuration\n\n")
                    yaml.dump(dvt_profiles, f, default_flow_style=False)
                click.echo(f"  Merged {merged_count} target(s) into profile '{dvt_profile_name}'")
                if merged_names:
                    for name in merged_names:
                        click.echo(f"    + {name}")
            if skipped_count > 0:
                click.echo(f"  Skipped {skipped_count} target(s) (already exist)")
        else:
            click.echo(f"  [DRY RUN] Would merge {merged_count} target(s) into profile")

        return MigrationResult(True, f"Merged {merged_count} targets", merged_count)

    def _show_summary(self, results: List[MigrationResult]) -> None:
        """Show migration summary for Mode A."""
        if not results:
            return

        successful = [r for r in results if r and r.success]
        if not successful:
            return

        click.echo("")
        click.echo("=" * 60)
        click.echo("Migration complete!")
        click.echo("=" * 60)

        for result in successful:
            if result:
                click.echo(f"  {result.message}")

        click.echo("")
        click.echo("Your dbt configuration has been preserved as backups.")
        click.echo("Run 'dvt target list' to verify your connections.")
        click.echo("=" * 60)

    def _show_import_summary(self, source_name: str, results: List[MigrationResult]) -> None:
        """Show import summary for Mode B."""
        if self.dry_run:
            click.echo("")
            click.echo("No changes made (dry run).")
            return

        # Get copied directories
        copied_dirs = [r.message for r in results if r and r.success and "/" in r.message]

        click.echo("")
        click.echo("=" * 60)
        click.echo("Import complete!")
        click.echo("=" * 60)
        click.echo(f"  Project: {source_name}")

        for dir_result in copied_dirs:
            dir_name = dir_result.rstrip("/")
            click.echo(f"  {dir_name.capitalize()}: {dir_name}/{source_name}/")

        click.echo("")
        click.echo("Next steps:")
        click.echo(f"  1. Review {copied_dirs[0].split('/')[0] if copied_dirs else 'models'}/{source_name}/ for ref() adjustments")
        click.echo("  2. Update dvt_project.yml if needed")
        click.echo("  3. Run 'dvt target list' to see all targets")
        click.echo("=" * 60)
