"""
Compute Task

Handles DVT compute engine management commands:
- test: List all compute engines with connection status
- edit: Open computes.yml in user's editor
- validate: Validate compute engine configurations

v0.5.97: Simplified CLI - removed register/remove (use dvt compute edit instead)
         computes.yml with comprehensive samples replaces interactive registration.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from dbt.config.compute import ComputeRegistry, SparkPlatform, DEFAULT_COMPUTES_YAML
from dbt_common.exceptions import DbtRuntimeError


class ComputeTask:
    """Task for managing DVT compute engines."""

    def __init__(self, project_dir=None):
        """
        Initialize ComputeTask.

        :param project_dir: Path to project root directory (str or Path, defaults to cwd)
        """
        # Convert Path to string for consistent handling
        if project_dir is not None:
            self.project_dir = str(project_dir)
        else:
            self.project_dir = str(Path.cwd())
        self.registry = ComputeRegistry(self.project_dir)

    def list_computes(self) -> bool:
        """
        List all compute engines with their names and basic info.

        v0.51.1: Simple list command for quick reference.

        :returns: True always (for CLI exit code)
        """
        clusters = self.registry.list()

        if not clusters:
            print("No compute engines configured.")
            print("\nRun 'dvt compute edit' to configure compute engines.")
            return True

        print(f"\nCompute Engines ({len(clusters)} configured)")
        print("-" * 40)

        for cluster in clusters:
            default_marker = " (default)" if cluster.name == self.registry.target_compute else ""
            platform = cluster.detect_platform()
            print(f"  {cluster.name}{default_marker}")
            print(f"    Platform: {platform.value}")
            if cluster.description:
                print(f"    Description: {cluster.description}")

        print("")
        print(f"Default: {self.registry.target_compute}")
        print(f"Config:  {self.registry.get_config_path()}")

        return True

    def test_single_compute(self, compute_name: str) -> bool:
        """
        Test a specific compute engine by name.

        v0.5.99: Added single compute testing via `dvt compute test <name>`.

        :param compute_name: Name of the compute engine to test
        :returns: True if test passes, False otherwise
        """
        clusters = self.registry.list()
        cluster = None

        # Find the cluster by name
        for c in clusters:
            if c.name == compute_name:
                cluster = c
                break

        if cluster is None:
            print(f"❌ Compute engine '{compute_name}' not found.")
            print(f"\nAvailable compute engines:")
            for c in clusters:
                default_marker = " (default)" if c.name == self.registry.target_compute else ""
                print(f"  - {c.name}{default_marker}")
            print(f"\nRun 'dvt compute edit' to configure compute engines.")
            return False

        # Test the specific cluster
        print(f"\n" + "=" * 70)
        print(f"Testing Compute Engine: {compute_name}")
        print("=" * 70)

        default_marker = " (default)" if cluster.name == self.registry.target_compute else ""
        platform = cluster.detect_platform()

        print(f"\n{cluster.name}{default_marker}")
        print(f"  Type: {cluster.type}")
        print(f"  Platform: {platform.value}")
        if cluster.description:
            print(f"  Description: {cluster.description}")

        # Test the cluster
        status, message = self._test_single_cluster(cluster)

        if status == "ok":
            print(f"  Status: ✅ {message}")
        elif status == "warning":
            print(f"  Status: ⚠️  {message}")
        elif status == "error":
            print(f"  Status: ❌ {message}")

        print("\n" + "-" * 70)

        return status in ("ok", "warning")

    def _test_single_cluster(self, cluster) -> tuple:
        """
        Test a single cluster and return status.

        v0.5.98: Full connectivity testing with three stages:
        1. Config validation
        2. Session creation + SELECT 1 test
        3. (Optional) JDBC read test

        v0.51.1: Enhanced session isolation - forcefully stop ALL Spark sessions
        before and after each test to prevent config bleed between computes.

        :param cluster: ComputeCluster to test
        :returns: Tuple of (status, message) where status is 'ok', 'warning', or 'error'
        """
        platform = cluster.detect_platform()

        if cluster.type == "spark":
            # Stage 1: Config validation
            config_result = self._validate_cluster_config(cluster, platform)
            if config_result[0] == "error":
                return config_result

            # Stage 2: Full connectivity test (session + SQL)
            try:
                # v0.51.1: Force stop ALL Spark sessions before testing
                # This ensures each compute engine test gets a completely fresh JVM context
                self._force_stop_all_spark_sessions()

                strategy = self._get_strategy_for_cluster(cluster, platform)
                if strategy is None:
                    return config_result  # Return config validation result

                success, message = strategy.test_connectivity()

                # v0.51.1: Force stop ALL sessions after test to not interfere with next compute
                self._force_stop_all_spark_sessions()

                if success:
                    return ("ok", message)
                else:
                    return ("error", message)

            except ImportError as e:
                # Missing dependency (PySpark, databricks-connect, etc.)
                return ("warning", str(e))
            except AttributeError as e:
                # databricks-connect may have compatibility issues with pyspark
                if "Hook" in str(e) or "SparkSession" in str(e):
                    return ("warning", f"databricks-connect/pyspark version conflict: {str(e)[:50]}")
                return ("error", f"Connectivity test failed: {str(e)}")
            except Exception as e:
                return ("error", f"Connectivity test failed: {str(e)}")

        return ("ok", "Configuration valid")

    def _force_stop_all_spark_sessions(self) -> None:
        """
        Force stop ALL Spark sessions to ensure complete isolation.

        v0.51.1: This is critical for compute testing because:
        1. Different computes have different spark.jars.packages configs
        2. Spark's getOrCreate() returns existing session without re-applying config
        3. We need a fresh JVM context for each compute's JDBC drivers

        This method:
        1. Stops active session
        2. Clears the local session cache used by LocalStrategy
        3. Forces garbage collection to release JVM resources
        """
        try:
            from pyspark.sql import SparkSession

            # Stop active session
            active = SparkSession.getActiveSession()
            if active:
                active.stop()

            # Clear local strategy cache
            try:
                from dbt.compute.strategies.local import _SPARK_SESSION_CACHE
                _SPARK_SESSION_CACHE.clear()
            except (ImportError, AttributeError):
                pass

            # Give JVM time to release resources
            import time
            time.sleep(0.5)

        except ImportError:
            pass  # PySpark not installed
        except Exception:
            pass  # Best effort cleanup

    def _validate_cluster_config(self, cluster, platform: SparkPlatform) -> tuple:
        """
        Validate cluster configuration (Stage 1).

        :param cluster: ComputeCluster to validate
        :param platform: Detected SparkPlatform
        :returns: Tuple of (status, message)
        """
        if platform == SparkPlatform.LOCAL:
            try:
                import pyspark  # noqa: F401
                # PySpark 4.0+ doesn't have __version__ attribute, use importlib
                try:
                    from importlib.metadata import version
                    pyspark_version = version("pyspark")
                except Exception:
                    pyspark_version = "unknown"
                return ("ok", f"PySpark {pyspark_version} available")
            except ImportError:
                return ("error", "PySpark not installed")

        elif platform == SparkPlatform.EMR:
            required = ["master"]
            missing = [k for k in required if k not in cluster.config]
            if missing:
                return ("error", f"Missing config: {', '.join(missing)}")
            master = cluster.config.get("master", "")
            if master.lower() != "yarn":
                return ("error", f"EMR requires master='yarn', got: {master}")
            return ("ok", "EMR config valid")

        elif platform == SparkPlatform.DATAPROC:
            required = ["project", "region", "cluster"]
            missing = [k for k in required if k not in cluster.config]
            if missing:
                return ("error", f"Missing config: {', '.join(missing)}")
            return ("ok", "Dataproc config valid")

        elif platform == SparkPlatform.STANDALONE:
            master = cluster.config.get("master", "")
            if not master.startswith("spark://"):
                return ("error", f"Standalone requires master='spark://...', got: {master}")
            return ("ok", f"Standalone config valid ({master})")

        else:
            # External/generic
            if "master" in cluster.config:
                return ("ok", f"External cluster at {cluster.config['master']}")
            return ("ok", "Configuration valid")

    def _get_strategy_for_cluster(self, cluster, platform: SparkPlatform):
        """
        Get the connection strategy for a cluster.

        :param cluster: ComputeCluster
        :param platform: Detected SparkPlatform
        :returns: BaseConnectionStrategy instance or None
        """
        try:
            if platform == SparkPlatform.LOCAL:
                from dbt.compute.strategies.local import LocalStrategy
                return LocalStrategy(cluster.config, app_name=f"DVT-{cluster.name}")

            elif platform == SparkPlatform.EMR:
                from dbt.compute.strategies import get_emr_strategy
                EMRStrategy = get_emr_strategy()
                return EMRStrategy(cluster.config, app_name=f"DVT-{cluster.name}")

            elif platform == SparkPlatform.DATAPROC:
                from dbt.compute.strategies import get_dataproc_strategy
                DataprocStrategy = get_dataproc_strategy()
                return DataprocStrategy(cluster.config, app_name=f"DVT-{cluster.name}")

            elif platform == SparkPlatform.STANDALONE:
                from dbt.compute.strategies import get_standalone_strategy
                StandaloneStrategy = get_standalone_strategy()
                return StandaloneStrategy(cluster.config, app_name=f"DVT-{cluster.name}")

            else:
                # External - no specific strategy, skip connectivity test
                return None

        except ImportError as e:
            raise ImportError(f"Missing dependency for {platform.value}: {str(e)}")

    def edit_config(self) -> bool:
        """
        Open computes.yml in user's preferred editor.

        Uses EDITOR environment variable, falls back to common editors.

        :returns: True if editor launched successfully
        """
        # Ensure config exists with full template
        config_path = self.registry.ensure_config_exists()

        # If file doesn't have full samples, write the template
        with open(config_path, "r") as f:
            content = f.read()
        if "DATABRICKS" not in content:
            # Write full template to get all the samples
            with open(config_path, "w") as f:
                f.write(DEFAULT_COMPUTES_YAML)

        print(f"Opening: {config_path}")
        print("")
        print("After editing, run 'dvt compute validate' to check syntax.")
        print("")

        # Get editor from environment or use defaults
        editor = os.environ.get("EDITOR")
        if not editor:
            editor = os.environ.get("VISUAL")
        if not editor:
            # Try common editors
            for ed in ["code", "nano", "vim", "vi", "notepad"]:
                try:
                    subprocess.run(["which", ed], capture_output=True, check=True)
                    editor = ed
                    break
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue

        if not editor:
            print(f"No editor found. Please open manually: {config_path}")
            return False

        try:
            # Handle VS Code specially (--wait flag)
            if editor in ("code", "code-insiders"):
                subprocess.run([editor, "--wait", str(config_path)])
            else:
                subprocess.run([editor, str(config_path)])

            # Reload and validate after edit
            print("\nValidating changes...")
            return self.validate_config()

        except Exception as e:
            print(f"Error opening editor: {e}", file=sys.stderr)
            print(f"Please open manually: {config_path}")
            return False

    def validate_config(self) -> bool:
        """
        Validate computes.yml syntax and configuration.

        :returns: True if configuration is valid
        """
        config_path = self.registry.get_config_path()

        if not config_path.exists():
            print(f"✗ Config file not found: {config_path}")
            print("\nRun 'dvt compute edit' to create one.")
            return False

        print(f"Validating: {config_path}")
        print("")

        try:
            # Try to load the YAML
            import yaml
            with open(config_path, "r") as f:
                data = yaml.safe_load(f)

            if not data:
                print("✗ Config file is empty")
                return False

            errors = []
            warnings = []

            # Check target_compute
            target = data.get("target_compute")
            if not target:
                errors.append("Missing 'target_compute' field")

            # Check computes section
            computes = data.get("computes", {})
            if not computes:
                errors.append("No compute engines defined in 'computes' section")
            else:
                # Validate each compute
                for name, config in computes.items():
                    if config is None:
                        continue  # Skip commented-out entries

                    if not isinstance(config, dict):
                        errors.append(f"Compute '{name}': invalid configuration (expected dict)")
                        continue

                    # Check type
                    compute_type = config.get("type")
                    if not compute_type:
                        errors.append(f"Compute '{name}': missing 'type' field")
                    elif compute_type not in ("spark",):
                        warnings.append(f"Compute '{name}': unknown type '{compute_type}' (only 'spark' supported)")

                    # Check config section
                    if "config" not in config:
                        warnings.append(f"Compute '{name}': no 'config' section (will use defaults)")

                # Check target_compute references valid engine
                if target and target not in computes:
                    errors.append(f"target_compute '{target}' not found in computes section")

            # Print results
            if errors:
                print("Errors:")
                for err in errors:
                    print(f"  ✗ {err}")
                print("")

            if warnings:
                print("Warnings:")
                for warn in warnings:
                    print(f"  ⚠ {warn}")
                print("")

            if not errors and not warnings:
                print("✓ Configuration is valid")
                print(f"  Target compute: {target}")
                print(f"  Engines defined: {len([c for c in computes.values() if c])}")
                return True

            if not errors:
                print("✓ Configuration is valid (with warnings)")
                return True

            return False

        except yaml.YAMLError as e:
            print(f"✗ YAML syntax error:")
            print(f"  {e}")
            return False

        except Exception as e:
            print(f"✗ Validation failed: {e}")
            return False
