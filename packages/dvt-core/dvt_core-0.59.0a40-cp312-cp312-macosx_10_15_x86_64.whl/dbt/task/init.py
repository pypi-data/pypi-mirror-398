import copy
import os
import re
import shutil
from pathlib import Path
from typing import Optional

import click
import yaml

import dbt.config
import dbt_common.clients.system
from dbt.adapters.factory import get_include_paths, load_plugin
from dbt.compute.metadata import ProjectMetadataStore
from dbt.config.profile import read_profile
from dbt.contracts.util import Identifier as ProjectName
from dbt.events.types import (
    ConfigFolderDirectory,
    InvalidProfileTemplateYAML,
    NoSampleProfileFound,
    ProfileWrittenWithProjectTemplateYAML,
    ProfileWrittenWithSample,
    ProfileWrittenWithTargetTemplateYAML,
    ProjectCreated,
    ProjectNameAlreadyExists,
    SettingUpProfile,
    StarterProjectPath,
)
from dbt.flags import get_flags
from dbt.task.base import BaseTask, move_to_nearest_project_dir
from dbt.version import _get_adapter_plugin_names
from dbt_common.events.functions import fire_event
from dbt_common.exceptions import DbtRuntimeError

DOCS_URL = "https://docs.getdbt.com/docs/configure-your-profile"
SLACK_URL = "https://community.getdbt.com/"

# These files are not needed for the starter project but exist for finding the resource path
# PLACEHOLDER files are used instead of .gitkeep because setuptools doesn't include hidden files
# gitignore.txt is renamed to .gitignore after copying (setuptools doesn't include hidden files)
IGNORE_FILES = ["__init__.py", "__pycache__", "PLACEHOLDER", "gitignore.txt"]

# Content for .gitignore file (created programmatically because setuptools skips hidden files)
GITIGNORE_CONTENT = """target/
dbt_packages/
logs/
flatfiles/
"""


# https://click.palletsprojects.com/en/8.0.x/api/#types
# click v7.0 has UNPROCESSED, STRING, INT, FLOAT, BOOL, and UUID available.
click_type_mapping = {
    "string": click.STRING,
    "int": click.INT,
    "float": click.FLOAT,
    "bool": click.BOOL,
    None: None,
}


class InitTask(BaseTask):
    def copy_starter_repo(self, project_name: str) -> None:
        # Lazy import to avoid ModuleNotFoundError
        from dbt.include.dvt_starter_project import (
            PACKAGE_PATH as starter_project_directory,
        )

        fire_event(StarterProjectPath(dir=starter_project_directory))
        shutil.copytree(
            starter_project_directory, project_name, ignore=shutil.ignore_patterns(*IGNORE_FILES)
        )

        # Create .gitignore file (setuptools doesn't include hidden files)
        gitignore_path = Path(project_name) / ".gitignore"
        with open(gitignore_path, "w") as f:
            f.write(GITIGNORE_CONTENT)

    def create_profiles_dir(self, profiles_dir: str) -> bool:
        """Create the user's profiles directory if it doesn't already exist."""
        profiles_path = Path(profiles_dir)
        if not profiles_path.exists():
            fire_event(ConfigFolderDirectory(dir=str(profiles_dir)))
            dbt_common.clients.system.make_directory(profiles_dir)
            return True
        return False

    def create_profile_from_sample(self, adapter: str, profile_name: str):
        """Create a profile entry using the adapter's sample_profiles.yml

        Renames the profile in sample_profiles.yml to match that of the project."""
        # Line below raises an exception if the specified adapter is not found
        load_plugin(adapter)
        adapter_path = get_include_paths(adapter)[0]
        sample_profiles_path = adapter_path / "sample_profiles.yml"

        if not sample_profiles_path.exists():
            fire_event(NoSampleProfileFound(adapter=adapter))
        else:
            with open(sample_profiles_path, "r") as f:
                sample_profile = f.read()
            sample_profile_name = list(yaml.safe_load(sample_profile).keys())[0]
            # Use a regex to replace the name of the sample_profile with
            # that of the project without losing any comments from the sample
            sample_profile = re.sub(f"^{sample_profile_name}:", f"{profile_name}:", sample_profile)
            profiles_filepath = Path(get_flags().PROFILES_DIR) / Path("profiles.yml")
            if profiles_filepath.exists():
                with open(profiles_filepath, "a") as f:
                    f.write("\n" + sample_profile)
            else:
                with open(profiles_filepath, "w") as f:
                    f.write(sample_profile)
                fire_event(
                    ProfileWrittenWithSample(name=profile_name, path=str(profiles_filepath))
                )

    def generate_target_from_input(self, profile_template: dict, target: dict = {}) -> dict:
        """Generate a target configuration from profile_template and user input."""
        profile_template_local = copy.deepcopy(profile_template)
        for key, value in profile_template_local.items():
            if key.startswith("_choose"):
                choice_type = key[8:].replace("_", " ")
                option_list = list(value.keys())
                prompt_msg = (
                    "\n".join([f"[{n + 1}] {v}" for n, v in enumerate(option_list)])
                    + f"\nDesired {choice_type} option (enter a number)"
                )
                numeric_choice = click.prompt(prompt_msg, type=click.INT)
                choice = option_list[numeric_choice - 1]
                # Complete the chosen option's values in a recursive call
                target = self.generate_target_from_input(
                    profile_template_local[key][choice], target
                )
            else:
                if key.startswith("_fixed"):
                    # _fixed prefixed keys are not presented to the user
                    target[key[7:]] = value
                else:
                    hide_input = value.get("hide_input", False)
                    default = value.get("default", None)
                    hint = value.get("hint", None)
                    type = click_type_mapping[value.get("type", None)]
                    text = key + (f" ({hint})" if hint else "")
                    target[key] = click.prompt(
                        text, default=default, hide_input=hide_input, type=type
                    )
        return target

    def get_profile_name_from_current_project(self) -> str:
        """Reads dvt_project.yml in the current directory to retrieve the
        profile name.
        """
        with open("dvt_project.yml") as f:
            dvt_project = yaml.safe_load(f)
        return dvt_project["profile"]

    def write_profile(self, profile: dict, profile_name: str):
        """Given a profile, write it to the current project's profiles.yml.
        This will overwrite any profile with a matching name."""
        # Create the profile directory if it doesn't exist
        profiles_filepath = Path(get_flags().PROFILES_DIR) / Path("profiles.yml")

        profiles = {profile_name: profile}

        if profiles_filepath.exists():
            with open(profiles_filepath, "r") as f:
                profiles = yaml.safe_load(f) or {}
                profiles[profile_name] = profile

        # Write the profiles dictionary to a brand-new or pre-existing file
        with open(profiles_filepath, "w") as f:
            yaml.dump(profiles, f)

    def create_profile_from_profile_template(self, profile_template: dict, profile_name: str):
        """Create and write a profile using the supplied profile_template."""
        initial_target = profile_template.get("fixed", {})
        prompts = profile_template.get("prompts", {})
        target = self.generate_target_from_input(prompts, initial_target)
        target_name = target.pop("target", "dev")
        profile = {"outputs": {target_name: target}, "target": target_name}
        self.write_profile(profile, profile_name)

    def create_profile_from_target(self, adapter: str, profile_name: str):
        """Create a profile without defaults using target's profile_template.yml if available, or
        sample_profiles.yml as a fallback."""
        # Line below raises an exception if the specified adapter is not found
        load_plugin(adapter)
        adapter_path = get_include_paths(adapter)[0]
        profile_template_path = adapter_path / "profile_template.yml"

        if profile_template_path.exists():
            with open(profile_template_path) as f:
                profile_template = yaml.safe_load(f)
            self.create_profile_from_profile_template(profile_template, profile_name)
            profiles_filepath = Path(get_flags().PROFILES_DIR) / Path("profiles.yml")
            fire_event(
                ProfileWrittenWithTargetTemplateYAML(
                    name=profile_name, path=str(profiles_filepath)
                )
            )
        else:
            # For adapters without a profile_template.yml defined, fallback on
            # sample_profiles.yml
            self.create_profile_from_sample(adapter, profile_name)

    def check_if_profile_exists(self, profile_name: str) -> bool:
        """
        Validate that the specified profile exists. Can't use the regular profile validation
        routine because it assumes the project file exists
        """
        profiles_dir = get_flags().PROFILES_DIR
        raw_profiles = read_profile(profiles_dir)
        return profile_name in raw_profiles

    def check_if_can_write_profile(self, profile_name: Optional[str] = None) -> bool:
        """Using either a provided profile name or that specified in dbt_project.yml,
        check if the profile already exists in profiles.yml, and if so ask the
        user whether to proceed and overwrite it."""
        profiles_file = Path(get_flags().PROFILES_DIR) / Path("profiles.yml")
        if not profiles_file.exists():
            return True
        profile_name = profile_name or self.get_profile_name_from_current_project()
        with open(profiles_file, "r") as f:
            profiles = yaml.safe_load(f) or {}
        if profile_name in profiles.keys():
            # Profile already exists, just skip profile setup
            click.echo(f"Profile '{profile_name}' already exists in {profiles_file}, skipping profile setup.")
            return False
        else:
            return True

    def create_profile_using_project_profile_template(self, profile_name):
        """Create a profile using the project's profile_template.yml"""
        with open("profile_template.yml") as f:
            profile_template = yaml.safe_load(f)
        self.create_profile_from_profile_template(profile_template, profile_name)
        profiles_filepath = Path(get_flags().PROFILES_DIR) / Path("profiles.yml")
        fire_event(
            ProfileWrittenWithProjectTemplateYAML(name=profile_name, path=str(profiles_filepath))
        )

    def ask_for_adapter_choice(self) -> str:
        """Ask the user which adapter (database) they'd like to use."""
        available_adapters = list(_get_adapter_plugin_names())

        if not available_adapters:
            raise dbt.exceptions.NoAdaptersAvailableError()

        prompt_msg = (
            "Which database would you like to use?\n"
            + "\n".join([f"[{n + 1}] {v}" for n, v in enumerate(available_adapters)])
            + "\n\n(Don't see the one you want? https://docs.getdbt.com/docs/available-adapters)"
            + "\n\nEnter a number"
        )
        numeric_choice = click.prompt(prompt_msg, type=click.INT)
        return available_adapters[numeric_choice - 1]

    def setup_profile(self, profile_name: str) -> None:
        """Set up a new profile for a project"""
        fire_event(SettingUpProfile())
        if not self.check_if_can_write_profile(profile_name=profile_name):
            return
        # If a profile_template.yml exists in the project root, that effectively
        # overrides the profile_template.yml for the given target.
        profile_template_path = Path("profile_template.yml")
        if profile_template_path.exists():
            try:
                # This relies on a valid profile_template.yml from the user,
                # so use a try: except to fall back to the default on failure
                self.create_profile_using_project_profile_template(profile_name)
                return
            except Exception:
                fire_event(InvalidProfileTemplateYAML())
        adapter = self.ask_for_adapter_choice()
        self.create_profile_from_target(adapter, profile_name=profile_name)

    def get_valid_project_name(self) -> str:
        """Returns a valid project name, either from CLI arg or user prompt."""

        # Lazy import to avoid ModuleNotFoundError
        from dbt.include.global_project import PROJECT_NAME as GLOBAL_PROJECT_NAME

        name = self.args.project_name
        internal_package_names = {GLOBAL_PROJECT_NAME}
        available_adapters = list(_get_adapter_plugin_names())
        for adapter_name in available_adapters:
            internal_package_names.update(f"dbt_{adapter_name}")
        while not ProjectName.is_valid(name) or name in internal_package_names:
            if name:
                click.echo(name + " is not a valid project name.")
            name = click.prompt("Enter a name for your project (letters, digits, underscore)")

        return name

    def create_new_project(self, project_name: str, profile_name: str):
        self.copy_starter_repo(project_name)
        os.chdir(project_name)
        with open("dvt_project.yml", "r") as f:
            content = f"{f.read()}".format(project_name=project_name, profile_name=profile_name)
        with open("dvt_project.yml", "w") as f:
            f.write(content)

        # v0.59.0: Create project-level .dvt/ structure
        # 1. Create .dvt/ directory
        project_dvt_dir = Path(".") / ".dvt"
        project_dvt_dir.mkdir(parents=True, exist_ok=True)

        # 2. Create .dvt/jdbc_jars/ directory
        from dbt.config.compute import ComputeRegistry
        ComputeRegistry.ensure_jdbc_jars_dir(".")

        # 3. Create .dvt/computes.yml with defaults
        registry = ComputeRegistry(project_dir=".")
        registry.ensure_config_exists()
        click.echo("  ✓ Compute config initialized (.dvt/computes.yml)")

        # 4. Initialize project metadata store (.dvt/metadata_store.duckdb)
        self._initialize_metadata_store(Path("."))

        # 5. Create default DuckDB database for starter profile
        self._create_default_duckdb(Path("."))

        # 6. v0.59.0: Create flatfiles/ directory
        self._create_flatfiles_dir()

        fire_event(
            ProjectCreated(
                project_name=project_name,
                docs_url=DOCS_URL,
                slack_url=SLACK_URL,
            )
        )

    def _create_project_in_place(self, project_name: str, profile_name: str) -> None:
        """
        Create DVT project in the current directory (no folder creation).

        v0.59.0a5: When user runs `dvt init` without a project name in an empty
        folder, we initialize the project in place using the folder name.

        This copies starter project contents to current directory and sets up
        all DVT infrastructure (.dvt/, flatfiles/, etc.).
        """
        from dbt.include.dvt_starter_project import (
            PACKAGE_PATH as starter_project_directory,
        )
        from dbt.config.compute import ComputeRegistry

        # Track if dvt_project.yml already existed (don't modify if so)
        dvt_project_existed = Path("dvt_project.yml").exists()

        # Copy starter project contents to current directory (not a subfolder)
        for item in Path(starter_project_directory).iterdir():
            if item.name in IGNORE_FILES or item.name.startswith('__'):
                continue
            dest = Path(".") / item.name
            if item.is_dir():
                if not dest.exists():
                    shutil.copytree(item, dest, ignore=shutil.ignore_patterns(*IGNORE_FILES))
            else:
                if not dest.exists():
                    shutil.copy2(item, dest)

        # Create .gitignore file (setuptools doesn't include hidden files)
        gitignore_path = Path(".") / ".gitignore"
        if not gitignore_path.exists():
            with open(gitignore_path, "w") as f:
                f.write(GITIGNORE_CONTENT)

        # Update dvt_project.yml with project name ONLY if it was just created
        # (existing files may have Jinja templates that conflict with .format())
        if not dvt_project_existed:
            with open("dvt_project.yml", "r") as f:
                content = f.read().replace("{project_name}", project_name).replace("{profile_name}", profile_name)
            with open("dvt_project.yml", "w") as f:
                f.write(content)

        # Create .dvt/ directory
        project_dvt_dir = Path(".") / ".dvt"
        project_dvt_dir.mkdir(parents=True, exist_ok=True)

        # Create .dvt/jdbc_jars/ directory
        ComputeRegistry.ensure_jdbc_jars_dir(".")

        # Create .dvt/computes.yml with defaults
        registry = ComputeRegistry(project_dir=".")
        registry.ensure_config_exists()
        click.echo("  ✓ Compute config initialized (.dvt/computes.yml)")

        # Initialize project metadata store
        self._initialize_metadata_store(Path("."))

        # Create default DuckDB database for starter profile
        self._create_default_duckdb(Path("."))

        # Create flatfiles/ directory
        self._create_flatfiles_dir()

        fire_event(
            ProjectCreated(
                project_name=project_name,
                docs_url=DOCS_URL,
                slack_url=SLACK_URL,
            )
        )

    def _initialize_metadata_store(self, project_root: Path) -> None:
        """
        Initialize the DVT metadata store in .dvt/metadata_store.duckdb.

        v0.55.0: Creates project-level metadata store with:
        - column_metadata table for schema info
        - row_counts table for cached row counts

        NOTE: Static registry data (type mappings, syntax rules) comes from
        the shipped adapters_registry.duckdb, not the project store.

        This is idempotent - calling on an existing store will reinitialize it.
        """
        try:
            store = ProjectMetadataStore(project_root)
            store.initialize()
            store.close()
            click.echo("  ✓ Metadata store initialized (.dvt/metadata_store.duckdb)")
        except ImportError:
            # DuckDB not installed - skip metadata store (optional feature)
            click.echo("  ⚠ DuckDB not installed - skipping metadata store")
        except Exception as e:
            # Don't fail init on metadata store errors
            click.echo(f"  ⚠ Could not initialize metadata store: {e}")

    def _create_flatfiles_dir(self) -> None:
        """
        Create empty flatfiles/ directory at project root (gitignored).

        v0.59.0: For local file staging and data ingestion.
        """
        flatfiles_dir = Path(".") / "flatfiles"
        flatfiles_dir.mkdir(parents=True, exist_ok=True)
        click.echo("  ✓ flatfiles/ directory created")

    def _create_default_duckdb(self, project_root: Path) -> None:
        """
        Create empty default.duckdb file for starter profile.

        v0.59.0a14: Creates .dvt/default.duckdb so the DuckDB starter
        profile works immediately without needing dbt-duckdb adapter.
        The file is an empty DuckDB database.
        """
        try:
            import duckdb
            duckdb_path = project_root / ".dvt" / "default.duckdb"
            if not duckdb_path.exists():
                # Create empty DuckDB database
                conn = duckdb.connect(str(duckdb_path))
                conn.close()
                click.echo("  ✓ Default DuckDB database created (.dvt/default.duckdb)")
        except ImportError:
            # DuckDB not available - skip (user will need to install dbt-duckdb)
            pass
        except Exception as e:
            click.echo(f"  ⚠ Could not create default DuckDB: {e}")

    def _add_project_profile(self, project_name: str, project_path: Optional[Path] = None) -> None:
        """
        Add a project profile with a DuckDB starter adapter to ~/.dvt/profiles.yml.

        v0.59.0a11: Uses ABSOLUTE path to project's .dvt/default.duckdb
        v0.59.0a24: Ensures profiles directory is created if it doesn't exist.
        Surgically adds 'dev' output if missing from existing profile.

        Args:
            project_name: Name of the project to add profile for
            project_path: Optional path to project directory (defaults to cwd)
        """
        profiles_dir = Path(get_flags().PROFILES_DIR)
        profiles_path = profiles_dir / "profiles.yml"

        # v0.59.0a24: Ensure profiles directory exists
        profiles_dir.mkdir(parents=True, exist_ok=True)

        # Get absolute project path for DuckDB file
        # Use provided path or fall back to current directory
        project_dir = (project_path or Path.cwd()).resolve()
        duckdb_path = str(project_dir / ".dvt" / "default.duckdb")

        # DuckDB starter configuration with ABSOLUTE path
        duckdb_output = {
            "type": "duckdb",
            "path": duckdb_path,
            "threads": 4,
        }

        if profiles_path.exists():
            # Read existing profiles
            with open(profiles_path, "r") as f:
                existing_profiles = yaml.safe_load(f) or {}

            action = None

            if project_name in existing_profiles:
                profile_data = existing_profiles[project_name]

                if profile_data and isinstance(profile_data, dict):
                    outputs = profile_data.get("outputs", {})

                    if outputs and isinstance(outputs, dict):
                        # Check if 'dev' output exists
                        if "dev" in outputs:
                            # Profile has 'dev' output - check if it's DuckDB type
                            click.echo(f"  Profile '{project_name}' already configured in profiles.yml")
                            return
                        else:
                            # Profile has outputs but missing 'dev' - surgically add it
                            outputs["dev"] = duckdb_output
                            profile_data["outputs"] = outputs
                            existing_profiles[project_name] = profile_data
                            action = "add_dev"
                    else:
                        # Profile has no outputs - add dev
                        profile_data["outputs"] = {"dev": duckdb_output}
                        if "target" not in profile_data:
                            profile_data["target"] = "dev"
                        existing_profiles[project_name] = profile_data
                        action = "fix_outputs"
                else:
                    # Profile is None or invalid - create fresh
                    existing_profiles[project_name] = {
                        "target": "dev",
                        "outputs": {"dev": duckdb_output}
                    }
                    action = "fix_invalid"
            else:
                # Profile doesn't exist - add it
                existing_profiles[project_name] = {
                    "target": "dev",
                    "outputs": {"dev": duckdb_output}
                }
                action = "add"

            # Write profiles back with header
            with open(profiles_path, "w") as f:
                f.write("# DVT Profiles Configuration\n")
                f.write("# =============================================================================\n")
                f.write("# Configure your database connections below. For documentation, see:\n")
                f.write("# https://docs.getdbt.com/docs/configure-your-profile\n")
                f.write("#\n")
                f.write("# After modifying connections, run: dvt target sync\n")
                f.write("# =============================================================================\n\n")
                yaml.dump(existing_profiles, f, default_flow_style=False, sort_keys=False)

            # Print appropriate message
            if action == "add":
                click.echo(f"  ✓ Profile '{project_name}' added to profiles.yml")
            elif action == "add_dev":
                click.echo(f"  ✓ Added 'dev' (DuckDB) output to profile '{project_name}'")
            elif action == "fix_outputs":
                click.echo(f"  ✓ Profile '{project_name}' updated with DuckDB starter output")
            elif action == "fix_invalid":
                click.echo(f"  ✓ Profile '{project_name}' fixed with DuckDB starter configuration")
        else:
            # Create new profiles.yml with header and profile
            new_profile = {
                project_name: {
                    "target": "dev",
                    "outputs": {"dev": duckdb_output}
                }
            }
            with open(profiles_path, "w") as f:
                f.write("# DVT Profiles Configuration\n")
                f.write("# =============================================================================\n")
                f.write("# Configure your database connections below. For documentation, see:\n")
                f.write("# https://docs.getdbt.com/docs/configure-your-profile\n")
                f.write("#\n")
                f.write("# After modifying connections, run: dvt target sync\n")
                f.write("# =============================================================================\n\n")
                yaml.dump(new_profile, f, default_flow_style=False, sort_keys=False)

            click.echo(f"  ✓ profiles.yml created with '{project_name}' profile")

    def _convert_dbt_to_dvt(self) -> None:
        """
        Convert dbt project to DVT project.

        v0.59.0a2: When `dvt init` is issued inside a dbt project (has dbt_project.yml
        but no dvt_project.yml), this method:

        1. Backs up dbt_project.yml → dbt_project.yml.bak
        2. Gets project name and profile from dbt_project.yml
        3. Creates fresh dvt_project.yml from standard dbt init template + DVT additions
        4. Creates flatfiles/ directory
        5. Migrates project-specific profile from ~/.dbt/profiles.yml to ~/.dvt/profiles.yml

        Note: Fresh template is used for consistency. User can copy project-specific
        configs (like models: overrides) from the backup if needed.
        """
        import shutil

        dbt_project_file = Path("dbt_project.yml")
        backup_file = Path("dbt_project.yml.bak")

        # 1. Backup dbt_project.yml
        if dbt_project_file.exists():
            if backup_file.exists():
                # Add timestamp if backup already exists
                import time
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_file = Path(f"dbt_project.yml.{timestamp}.bak")
            shutil.copy2(dbt_project_file, backup_file)
            click.echo(f"  ✓ Backed up dbt_project.yml → {backup_file.name}")

        # 2. Get project name and profile from dbt_project.yml
        with open(dbt_project_file, "r") as f:
            dbt_content = f.read()

        project_name = Path.cwd().name
        profile_name = project_name  # Default to project name
        try:
            config = yaml.safe_load(dbt_content)
            if config:
                if "name" in config:
                    project_name = config["name"]
                if "profile" in config:
                    profile_name = config["profile"]
        except Exception:
            pass

        # 3. Create fresh dvt_project.yml from standard dbt init template + DVT additions
        # This matches what dbt init creates, plus DVT-specific flatfile-paths
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
        with open("dvt_project.yml", "w") as f:
            f.write(dvt_project_content)
        click.echo(f"  ✓ Created dvt_project.yml")

        # 5. Create flatfiles/ directory
        flatfiles_dir = Path("flatfiles")
        flatfiles_dir.mkdir(exist_ok=True)
        # Add .gitignore to flatfiles/
        gitignore_path = flatfiles_dir / ".gitignore"
        if not gitignore_path.exists():
            with open(gitignore_path, "w") as f:
                f.write("# Ignore all flat files (CSV, Parquet, etc.)\n*\n!.gitignore\n")
        click.echo("  ✓ Created flatfiles/ directory")

        # 6. Migrate profiles from ~/.dbt/ to ~/.dvt/
        from dbt.task.migrate import MigrateTask
        task = MigrateTask(profiles_only=True)
        task._migrate_profiles()

        # Get project name from the content for display
        project_name = Path.cwd().name
        try:
            config = yaml.safe_load(dbt_content)
            if config and "name" in config:
                project_name = config["name"]
        except Exception:
            pass

        click.echo("")
        click.echo("=" * 60)
        click.echo("DVT project initialized from dbt project!")
        click.echo("=" * 60)
        click.echo(f"  Project: {project_name}")
        click.echo(f"  Config:  dvt_project.yml")
        click.echo(f"  Backup:  {backup_file.name}")
        click.echo("")
        click.echo("Next steps:")
        click.echo("  1. Review dvt_project.yml")
        click.echo("  2. Run 'dvt target list' to verify connections")
        click.echo("  3. Run 'dvt run' to build your models")
        click.echo("=" * 60)

    def _initialize_user_metadata_db(self) -> None:
        """
        Initialize the user-level metadata database at ~/.dvt/.data/mdm.duckdb.

        v0.59.0: Copies data from the packaged adapters_registry.duckdb to the
        user-level database. This ensures users have access to type mappings,
        syntax rules, and adapter queries even if the package is not accessible.

        ALWAYS recreates the database on init for easy testing and updates.
        """
        try:
            import duckdb
            from dbt.compute.metadata import AdaptersRegistry

            # Get paths
            dvt_home = Path.home() / ".dvt"
            data_dir = dvt_home / ".data"
            user_db_path = data_dir / "mdm.duckdb"

            # Create directories
            data_dir.mkdir(parents=True, exist_ok=True)

            # ALWAYS recreate for testing (remove if exists)
            if user_db_path.exists():
                user_db_path.unlink()

            # Get packaged registry path
            registry = AdaptersRegistry()
            source_db_path = registry.get_registry_path()

            # Connect to source (read-only) and destination
            source_conn = duckdb.connect(str(source_db_path), read_only=True)
            dest_conn = duckdb.connect(str(user_db_path))

            # Get data from source and copy to destination
            # (DuckDB doesn't support cross-database queries, so we fetch and insert)

            # Copy datatype_mappings table
            mappings = source_conn.execute("SELECT * FROM datatype_mappings").fetchall()
            dest_conn.execute("DROP TABLE IF EXISTS datatype_mappings")
            dest_conn.execute("""
                CREATE TABLE datatype_mappings (
                    adapter_name VARCHAR,
                    adapter_type VARCHAR,
                    spark_type VARCHAR,
                    spark_version VARCHAR,
                    is_complex BOOLEAN,
                    cast_expression VARCHAR,
                    notes VARCHAR
                )
            """)

            # Insert data
            if mappings:
                dest_conn.executemany(
                    "INSERT INTO datatype_mappings VALUES (?, ?, ?, ?, ?, ?, ?)",
                    mappings
                )

            # Copy adapter_queries table
            queries = source_conn.execute("SELECT * FROM adapter_queries").fetchall()
            dest_conn.execute("DROP TABLE IF EXISTS adapter_queries")
            dest_conn.execute("""
                CREATE TABLE adapter_queries (
                    adapter_name VARCHAR,
                    query_type VARCHAR,
                    query_template VARCHAR,
                    notes VARCHAR
                )
            """)
            if queries:
                dest_conn.executemany(
                    "INSERT INTO adapter_queries VALUES (?, ?, ?, ?)",
                    queries
                )

            # Copy syntax_registry table
            syntax = source_conn.execute("SELECT * FROM syntax_registry").fetchall()
            dest_conn.execute("DROP TABLE IF EXISTS syntax_registry")
            dest_conn.execute("""
                CREATE TABLE syntax_registry (
                    adapter_name VARCHAR,
                    quote_start VARCHAR,
                    quote_end VARCHAR,
                    case_sensitivity VARCHAR,
                    reserved_keywords VARCHAR
                )
            """)
            if syntax:
                dest_conn.executemany(
                    "INSERT INTO syntax_registry VALUES (?, ?, ?, ?, ?)",
                    syntax
                )

            # Copy value_transformations table (v0.59.0a32: seed pattern transformations)
            transforms = []
            try:
                transforms = source_conn.execute("SELECT * FROM value_transformations").fetchall()
                dest_conn.execute("DROP TABLE IF EXISTS value_transformations")
                dest_conn.execute("""
                    CREATE TABLE value_transformations (
                        pattern VARCHAR NOT NULL,
                        target_type VARCHAR NOT NULL,
                        transform_expr VARCHAR NOT NULL,
                        priority INTEGER DEFAULT 50,
                        description VARCHAR,
                        PRIMARY KEY (pattern)
                    )
                """)
                if transforms:
                    dest_conn.executemany(
                        "INSERT INTO value_transformations VALUES (?, ?, ?, ?, ?)",
                        transforms
                    )
            except Exception:
                # Table might not exist in older registries
                pass

            source_conn.close()
            dest_conn.close()

            mappings_count = len(mappings) if mappings else 0
            queries_count = len(queries) if queries else 0
            syntax_count = len(syntax) if syntax else 0
            transforms_count = len(transforms) if transforms else 0

            click.echo(f"  ✓ User metadata database initialized (~/.dvt/.data/mdm.duckdb)")
            click.echo(f"    - {mappings_count} type mappings (all adapters x all types x all Spark versions)")
            click.echo(f"    - {queries_count} adapter queries")
            click.echo(f"    - {syntax_count} syntax rules")
            if transforms_count > 0:
                click.echo(f"    - {transforms_count} value transformation patterns (for dvt seed)")

        except ImportError:
            # DuckDB not installed - skip
            click.echo("  ⚠ DuckDB not installed - skipping user metadata database")
        except Exception as e:
            # Don't fail init on metadata errors
            click.echo(f"  ⚠ Could not initialize user metadata database: {e}")

    def _show_init_success(self, project_name: str) -> None:
        """
        Display success message and next steps after project initialization.

        v0.59.0: Non-interactive flow - a DuckDB starter adapter is created,
        user can modify it to use their actual database connections.
        """
        click.echo("")
        click.echo("=" * 60)
        click.echo("DVT project initialized successfully!")
        click.echo("=" * 60)
        click.echo(f"\nProject: {project_name}")
        click.echo(f"Profile: ~/.dvt/profiles.yml")
        click.echo("")
        click.echo("A DuckDB starter adapter has been configured.")
        click.echo("Modify ~/.dvt/profiles.yml to add your database connections.")
        click.echo("")
        click.echo("Next Steps:")
        click.echo(f"  1. cd {project_name}")
        click.echo("  2. dvt run              # Test with DuckDB starter")
        click.echo("  3. Edit ~/.dvt/profiles.yml to add real connections")
        click.echo("  4. dvt target list      # Verify connections")
        click.echo("")
        click.echo("Docs: https://docs.getdbt.com/docs/configure-your-profile")
        click.echo("=" * 60)

    def run(self):
        """Entry point for the init task."""
        profiles_dir = get_flags().PROFILES_DIR
        # Ensure profiles_dir is a string (may be PosixPath from default_profiles_dir())
        if hasattr(profiles_dir, '__fspath__'):
            profiles_dir = str(profiles_dir)
        self.create_profiles_dir(profiles_dir)

        # v0.58.8: Initialize user-level metadata database with packaged registry data
        self._initialize_user_metadata_db()

        try:
            move_to_nearest_project_dir(self.args.project_dir)
            in_project = True
        except dbt_common.exceptions.DbtRuntimeError:
            in_project = False

        # v0.59.0: Check for dbt project that needs migration
        dbt_project_file = Path("dbt_project.yml")
        dvt_project_file = Path("dvt_project.yml")
        in_dbt_project = dbt_project_file.exists() and not dvt_project_file.exists()

        if in_dbt_project:
            # Detected dbt project - convert to DVT project
            click.echo("Detected existing dbt project (dbt_project.yml).")
            click.echo("Converting to DVT project...")
            click.echo("")
            self._convert_dbt_to_dvt()
            in_project = True  # Now we have a DVT project

        if in_project:
            # If --profile was specified, it means use an existing profile, which is not
            # applicable to this case
            if self.args.profile:
                raise DbtRuntimeError(
                    msg="Can not init existing project with specified profile, edit dvt_project.yml instead"
                )

            # v0.55.0: Ensure project-level .dvt/ structure exists
            from dbt.config.compute import ComputeRegistry

            # Create .dvt/ directory and jdbc_jars/
            ComputeRegistry.ensure_jdbc_jars_dir(".")

            # Ensure computes.yml exists at project level
            registry = ComputeRegistry(project_dir=".")
            registry.ensure_config_exists()

            # Initialize metadata store if not already present
            self._initialize_metadata_store(Path("."))

            # Create default DuckDB database for starter profile
            self._create_default_duckdb(Path("."))

            # v0.59.0a11: Ensure profile has 'dev' DuckDB output
            # Get project name from dvt_project.yml
            try:
                with open("dvt_project.yml", "r") as f:
                    project_config = yaml.safe_load(f)
                    project_name = project_config.get("name", Path.cwd().name)
            except (FileNotFoundError, yaml.YAMLError):
                # If we can't read project name, use folder name
                project_name = Path.cwd().name

            # v0.59.0a24: Always add profile (don't let exceptions be swallowed)
            try:
                self._add_project_profile(project_name)
            except Exception as e:
                click.echo(f"  ⚠ Could not add profile: {e}")
        else:
            # When dvt init is run outside of an existing project,
            # create a new project.
            #
            # v0.59.0a5: Two modes:
            # 1. dvt init <project_name> → Create new folder with that name
            # 2. dvt init (no args, in empty folder) → Init in place using folder name

            user_profile_name = self.args.profile

            if self.args.project_name:
                # Mode 1: User specified project name → create new folder
                project_name = self.args.project_name
                if not ProjectName.is_valid(project_name):
                    click.echo(f"'{project_name}' is not a valid project name.")
                    click.echo("Project names must contain only letters, digits, and underscores.")
                    return

                project_path = Path(project_name)
                if project_path.exists():
                    fire_event(ProjectNameAlreadyExists(name=project_name))
                    return

                if user_profile_name:
                    if not self.check_if_profile_exists(user_profile_name):
                        raise DbtRuntimeError(
                            msg="Could not find profile named '{}'".format(user_profile_name)
                        )
                    self.create_new_project(project_name, user_profile_name)
                else:
                    self.create_new_project(project_name, project_name)

                # create_new_project changes CWD into the project directory
                # and already sets up .dvt/ structure, so just add profile
                self._add_project_profile(project_name)  # Uses CWD which is now inside project
                self._show_init_success(project_name)
            else:
                # Mode 2: No project name → init in current folder using folder name
                project_name = Path.cwd().name

                # Validate folder name as project name
                if not ProjectName.is_valid(project_name):
                    click.echo(f"Current folder '{project_name}' is not a valid project name.")
                    click.echo("Project names must contain only letters, digits, and underscores.")
                    click.echo("Use: dvt init <valid_project_name>")
                    return

                click.echo(f"Initializing DVT project '{project_name}' in current folder...")
                click.echo("")

                profile_name = user_profile_name if user_profile_name else project_name
                if user_profile_name and not self.check_if_profile_exists(user_profile_name):
                    raise DbtRuntimeError(
                        msg="Could not find profile named '{}'".format(user_profile_name)
                    )

                # Init in place (no folder creation)
                self._create_project_in_place(project_name, profile_name)
                self._add_project_profile(project_name)
                self._show_init_success(project_name)
