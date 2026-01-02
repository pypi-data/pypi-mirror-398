"""
Java/PySpark Compatibility Module

Centralized logic for:
- Java installation detection (cross-platform)
- PySpark version detection
- Java/PySpark compatibility checking
- Spark cluster version detection

v0.51.3: New module for comprehensive Java/Spark management.
"""

import glob
import os
import platform
import re
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple


# =============================================================================
# COMPATIBILITY MATRIX
# =============================================================================
# PySpark major.minor -> Java requirements
# Based on Apache Spark official documentation

PYSPARK_JAVA_COMPATIBILITY: Dict[str, Dict] = {
    "4.0": {"min": 17, "max": 21, "recommended": 17, "supported": [17, 21]},
    "3.5": {"min": 8, "max": 17, "recommended": 17, "supported": [8, 11, 17]},
    "3.4": {"min": 8, "max": 17, "recommended": 11, "supported": [8, 11, 17]},
    "3.3": {"min": 8, "max": 11, "recommended": 11, "supported": [8, 11]},
    "3.2": {"min": 8, "max": 11, "recommended": 11, "supported": [8, 11]},
    "3.1": {"min": 8, "max": 11, "recommended": 11, "supported": [8, 11]},
    "3.0": {"min": 8, "max": 11, "recommended": 8, "supported": [8, 11]},
}

# Available PySpark versions for interactive selection
PYSPARK_VERSIONS = [
    ("4.0.1", "4.0", "latest"),
    ("3.5.3", "3.5", "stable"),
    ("3.4.3", "3.4", ""),
    ("3.3.4", "3.3", ""),
    ("3.2.4", "3.2", ""),
]


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class JavaInstallation:
    """Represents a Java installation found on the system."""
    path: str  # JAVA_HOME path
    version: int  # Major version (8, 11, 17, 21)
    version_string: str  # Full version string (e.g., "openjdk version 17.0.1")
    vendor: str  # e.g., "OpenJDK", "Oracle", "Adoptium", "Amazon Corretto"
    is_current: bool = False  # True if this is the active JAVA_HOME


@dataclass
class PySparkInfo:
    """PySpark installation information."""
    version: str  # Full version (e.g., "4.0.1")
    major_minor: str  # Major.minor (e.g., "4.0")
    java_min: int
    java_max: int
    java_recommended: int
    java_supported: List[int]


# =============================================================================
# JAVA DETECTION FUNCTIONS
# =============================================================================

def get_java_version(java_bin_path: str) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    """
    Get Java major version, full version string, and vendor from java binary.

    :param java_bin_path: Path to java binary
    :returns: Tuple of (major_version, version_string, vendor) or (None, None, None)
    """
    try:
        result = subprocess.run(
            [java_bin_path, "-version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        version_output = result.stderr + result.stdout

        # Parse version (e.g., "openjdk version \"21.0.5\"" or "java version \"1.8.0\"")
        version_match = re.search(r'version "(\d+)\.?', version_output)
        if not version_match:
            return None, None, None

        major = int(version_match.group(1))
        # Handle old Java versioning (1.8 = Java 8)
        if major == 1:
            minor_match = re.search(r'version "1\.(\d+)', version_output)
            if minor_match:
                major = int(minor_match.group(1))

        # Extract first line as version string
        version_string = version_output.split('\n')[0].strip()

        # Detect vendor
        vendor = "Unknown"
        lower_output = version_output.lower()
        if "openjdk" in lower_output:
            if "temurin" in lower_output or "adoptium" in lower_output:
                vendor = "Eclipse Adoptium"
            elif "corretto" in lower_output:
                vendor = "Amazon Corretto"
            elif "zulu" in lower_output:
                vendor = "Azul Zulu"
            elif "graalvm" in lower_output:
                vendor = "GraalVM"
            else:
                vendor = "OpenJDK"
        elif "java(tm)" in lower_output or "oracle" in lower_output:
            vendor = "Oracle"
        elif "ibm" in lower_output:
            vendor = "IBM"

        return major, version_string, vendor

    except Exception:
        return None, None, None


def get_current_java() -> Optional[JavaInstallation]:
    """
    Get the currently configured Java installation (from JAVA_HOME or PATH).

    :returns: JavaInstallation or None if not found
    """
    import shutil

    # Check JAVA_HOME first
    java_home = os.environ.get("JAVA_HOME")
    if java_home and os.path.exists(java_home):
        java_bin = os.path.join(java_home, "bin", "java")
        if platform.system() == "Windows":
            java_bin += ".exe"
        if os.path.exists(java_bin):
            version, version_str, vendor = get_java_version(java_bin)
            if version:
                return JavaInstallation(
                    path=java_home,
                    version=version,
                    version_string=version_str or f"Java {version}",
                    vendor=vendor or "Unknown",
                    is_current=True
                )

    # Check PATH
    java_bin = shutil.which("java")
    if java_bin:
        version, version_str, vendor = get_java_version(java_bin)
        if version:
            # Infer JAVA_HOME from binary location
            java_home = os.path.dirname(os.path.dirname(os.path.realpath(java_bin)))
            return JavaInstallation(
                path=java_home,
                version=version,
                version_string=version_str or f"Java {version}",
                vendor=vendor or "Unknown",
                is_current=True
            )

    return None


def _check_java_path(path: str, is_current: bool = False) -> Optional[JavaInstallation]:
    """
    Check if a path contains a valid Java installation.

    :param path: JAVA_HOME path to check
    :param is_current: Whether this is the current JAVA_HOME
    :returns: JavaInstallation or None
    """
    if not os.path.exists(path):
        return None

    java_bin = os.path.join(path, "bin", "java")
    if platform.system() == "Windows":
        java_bin += ".exe"

    if not os.path.exists(java_bin):
        return None

    version, version_str, vendor = get_java_version(java_bin)
    if version:
        return JavaInstallation(
            path=path,
            version=version,
            version_string=version_str or f"Java {version}",
            vendor=vendor or "Unknown",
            is_current=is_current
        )
    return None


def _find_java_macos() -> List[JavaInstallation]:
    """Find Java installations on macOS."""
    installations = []

    # 1. Use java_home utility to list all
    try:
        result = subprocess.run(
            ["/usr/libexec/java_home", "-V"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # Parse output - paths are at the end of each line
        for line in result.stderr.split('\n'):
            match = re.search(r'(/[^\s]+)$', line.strip())
            if match:
                path = match.group(1)
                inst = _check_java_path(path)
                if inst:
                    installations.append(inst)
    except Exception:
        pass

    # 2. Search common paths
    search_patterns = [
        "/Library/Java/JavaVirtualMachines/*/Contents/Home",
        "/usr/local/opt/openjdk@*/libexec/openjdk.jdk/Contents/Home",
        "/usr/local/Cellar/openjdk@*/*/libexec/openjdk.jdk/Contents/Home",
        "/opt/homebrew/opt/openjdk@*/libexec/openjdk.jdk/Contents/Home",
        os.path.expanduser("~/.sdkman/candidates/java/*"),
        os.path.expanduser("~/Library/Java/JavaVirtualMachines/*/Contents/Home"),
    ]

    for pattern in search_patterns:
        try:
            for path in glob.glob(pattern):
                inst = _check_java_path(path)
                if inst:
                    installations.append(inst)
        except Exception:
            continue

    return installations


def _find_java_linux() -> List[JavaInstallation]:
    """Find Java installations on Linux."""
    installations = []

    # 1. Check update-alternatives
    try:
        result = subprocess.run(
            ["update-alternatives", "--list", "java"],
            capture_output=True,
            text=True,
            timeout=10
        )
        for line in result.stdout.strip().split('\n'):
            if line and os.path.exists(line):
                # Path is typically /usr/lib/jvm/java-X-openjdk/bin/java
                bin_path = os.path.dirname(line)
                java_home = os.path.dirname(bin_path)
                inst = _check_java_path(java_home)
                if inst:
                    installations.append(inst)
    except Exception:
        pass

    # 2. Search common paths
    search_patterns = [
        "/usr/lib/jvm/java-*-openjdk*",
        "/usr/lib/jvm/jdk-*",
        "/usr/lib/jvm/temurin-*",
        "/usr/lib/jvm/adoptium-*",
        "/usr/java/jdk*",
        "/opt/java/*",
        "/opt/jdk*",
        os.path.expanduser("~/.sdkman/candidates/java/*"),
    ]

    for pattern in search_patterns:
        try:
            for path in glob.glob(pattern):
                inst = _check_java_path(path)
                if inst:
                    installations.append(inst)
        except Exception:
            continue

    return installations


def _find_java_windows() -> List[JavaInstallation]:
    """Find Java installations on Windows."""
    installations = []

    # 1. Check Windows Registry
    try:
        import winreg
        reg_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\JavaSoft\Java Development Kit"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\JavaSoft\JDK"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Eclipse Adoptium\JDK"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\AdoptOpenJDK\JDK"),
        ]
        for hkey, subkey in reg_paths:
            try:
                key = winreg.OpenKey(hkey, subkey)
                i = 0
                while True:
                    try:
                        version = winreg.EnumKey(key, i)
                        version_key = winreg.OpenKey(key, version)
                        java_home, _ = winreg.QueryValueEx(version_key, "JavaHome")
                        inst = _check_java_path(java_home)
                        if inst:
                            installations.append(inst)
                        i += 1
                    except OSError:
                        break
            except FileNotFoundError:
                pass
    except ImportError:
        pass

    # 2. Search common paths
    search_patterns = [
        r"C:\Program Files\Java\jdk*",
        r"C:\Program Files\Eclipse Adoptium\jdk-*",
        r"C:\Program Files\OpenJDK\jdk-*",
        r"C:\Program Files\AdoptOpenJDK\jdk-*",
        r"C:\Program Files\Amazon Corretto\jdk*",
        r"C:\Program Files\Zulu\zulu-*",
        os.path.expanduser(r"~\scoop\apps\openjdk*\current"),
        os.path.expanduser(r"~\scoop\apps\temurin*\current"),
    ]

    for pattern in search_patterns:
        try:
            for path in glob.glob(pattern):
                inst = _check_java_path(path)
                if inst:
                    installations.append(inst)
        except Exception:
            continue

    return installations


def find_all_java_installations() -> List[JavaInstallation]:
    """
    Find ALL Java installations on the system (cross-platform).

    :returns: List of JavaInstallation objects, sorted by version (newest first)
    """
    os_type = platform.system()
    installations = []

    # Get current Java first
    current = get_current_java()
    current_path = current.path if current else None

    # Find all installations based on OS
    if os_type == "Darwin":
        installations = _find_java_macos()
    elif os_type == "Linux":
        installations = _find_java_linux()
    elif os_type == "Windows":
        installations = _find_java_windows()

    # Mark current and remove duplicates
    seen_paths = set()
    unique = []
    for inst in installations:
        normalized_path = os.path.normpath(inst.path)
        if normalized_path not in seen_paths:
            seen_paths.add(normalized_path)
            inst.is_current = (normalized_path == os.path.normpath(current_path)) if current_path else False
            unique.append(inst)

    # Add current if not already found
    if current and os.path.normpath(current.path) not in seen_paths:
        unique.append(current)

    # Sort by version (newest first)
    return sorted(unique, key=lambda x: x.version, reverse=True)


def _is_valid_java_home(path: str) -> bool:
    """
    Check if a path is a valid JAVA_HOME directory.

    A valid JAVA_HOME should contain bin/java and not be a system path like /usr.
    """
    if not path:
        return False

    # Reject system paths that aren't proper JDK directories
    invalid_paths = ["/usr", "/usr/local", "/"]
    if os.path.normpath(path) in invalid_paths:
        return False

    # Check for bin/java or bin/java.exe
    java_bin = os.path.join(path, "bin", "java")
    if platform.system() == "Windows":
        java_bin += ".exe"

    return os.path.isfile(java_bin)


def select_best_java(installations: List[JavaInstallation], supported_versions: List[int]) -> Optional[JavaInstallation]:
    """
    Select the best Java installation from a list for given supported versions.

    Prefers: (1) proper JDK directory, (2) highest supported version, (3) not current but valid

    :param installations: List of JavaInstallation
    :param supported_versions: List of supported Java major versions
    :returns: Best JavaInstallation or None
    """
    if not installations or not supported_versions:
        return None

    # Filter to only compatible versions with valid JDK paths
    compatible = [
        inst for inst in installations
        if inst.version in supported_versions and _is_valid_java_home(inst.path)
    ]
    if not compatible:
        return None

    # Prefer proper JDK directories (not /usr or similar)
    # Sort by: highest version first
    compatible.sort(key=lambda x: x.version, reverse=True)

    # Return the highest version compatible Java with a valid path
    return compatible[0]


# =============================================================================
# PYSPARK DETECTION FUNCTIONS
# =============================================================================

def get_pyspark_info() -> Optional[PySparkInfo]:
    """
    Get installed PySpark version and compatibility requirements.

    :returns: PySparkInfo or None if PySpark not installed
    """
    try:
        import importlib.metadata
        version = importlib.metadata.version("pyspark")

        # Extract major.minor
        parts = version.split(".")
        if len(parts) >= 2:
            major_minor = f"{parts[0]}.{parts[1]}"
        else:
            major_minor = parts[0]

        # Look up compatibility requirements
        compat = PYSPARK_JAVA_COMPATIBILITY.get(major_minor)
        if compat:
            return PySparkInfo(
                version=version,
                major_minor=major_minor,
                java_min=compat["min"],
                java_max=compat["max"],
                java_recommended=compat["recommended"],
                java_supported=compat["supported"]
            )
        else:
            # Unknown version - assume latest requirements
            return PySparkInfo(
                version=version,
                major_minor=major_minor,
                java_min=17,
                java_max=21,
                java_recommended=17,
                java_supported=[17, 21]
            )
    except Exception:
        return None


def get_pyspark_versions_for_java(java_version: int) -> List[str]:
    """
    Get list of PySpark versions compatible with a given Java version.

    :param java_version: Java major version
    :returns: List of PySpark major.minor versions
    """
    compatible = []
    for pyspark_version, compat in PYSPARK_JAVA_COMPATIBILITY.items():
        if java_version in compat["supported"]:
            compatible.append(pyspark_version)
    return sorted(compatible, reverse=True)


# =============================================================================
# COMPATIBILITY CHECKING
# =============================================================================

def check_java_pyspark_compatibility(java_version: int, pyspark_major_minor: str) -> Tuple[bool, str]:
    """
    Check if Java version is compatible with PySpark version.

    :param java_version: Java major version (e.g., 17)
    :param pyspark_major_minor: PySpark major.minor (e.g., "4.0")
    :returns: Tuple of (is_compatible, message)
    """
    compat = PYSPARK_JAVA_COMPATIBILITY.get(pyspark_major_minor)
    if not compat:
        return True, f"Unknown PySpark version {pyspark_major_minor}, assuming compatible"

    if java_version in compat["supported"]:
        return True, f"Java {java_version} is compatible with PySpark {pyspark_major_minor}"

    supported_str = ", ".join(str(v) for v in compat["supported"])
    return False, f"Java {java_version} is NOT compatible with PySpark {pyspark_major_minor}. Requires Java {supported_str}."


def validate_java_for_spark() -> Tuple[bool, str]:
    """
    Validate that current Java is compatible with installed PySpark.

    :returns: Tuple of (is_valid, message)
    """
    # Check PySpark
    pyspark = get_pyspark_info()
    if not pyspark:
        return False, "PySpark is not installed. Install it with: pip install pyspark"

    # Check Java
    java = get_current_java()
    if not java:
        return False, f"Java not found. PySpark {pyspark.version} requires Java {pyspark.java_supported}. Run 'dvt java search' to find installations."

    # Check compatibility
    is_compat, msg = check_java_pyspark_compatibility(java.version, pyspark.major_minor)
    if not is_compat:
        return False, f"{msg} Run 'dvt java set' to select a compatible Java version."

    return True, f"Java {java.version} is compatible with PySpark {pyspark.version}"


# =============================================================================
# CLUSTER VERSION DETECTION
# =============================================================================

def detect_spark_cluster_version(master_url: str, timeout: int = 30) -> Optional[str]:
    """
    Detect Spark version from a running cluster.

    Connects to the cluster and queries spark.version.

    :param master_url: Spark master URL (spark://host:port)
    :param timeout: Connection timeout in seconds
    :returns: Spark version string (e.g., "3.2.4") or None if detection fails
    """
    try:
        from pyspark.sql import SparkSession
        import concurrent.futures

        def _detect():
            spark = None
            try:
                spark = (SparkSession.builder
                    .appName("DVT-VersionDetect")
                    .master(master_url)
                    .config("spark.ui.enabled", "false")
                    .config("spark.ui.showConsoleProgress", "false")
                    .getOrCreate())
                return spark.version
            finally:
                if spark:
                    try:
                        spark.stop()
                    except Exception:
                        pass

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_detect)
            return future.result(timeout=timeout)

    except Exception:
        return None


# =============================================================================
# SHELL CONFIG MODIFICATION
# =============================================================================

def get_shell_config_file() -> Tuple[Optional[str], str]:
    """
    Get the appropriate shell config file for the current OS and shell.

    :returns: Tuple of (config_file_path, shell_name) or (None, "unknown")
    """
    os_type = platform.system()

    if os_type == "Windows":
        # PowerShell profile
        profile = os.path.expandvars(r"$PROFILE")
        if profile and "$" not in profile:
            return profile, "PowerShell"
        return None, "unknown"

    # Unix-like (macOS, Linux)
    shell = os.environ.get("SHELL", "")
    home = os.path.expanduser("~")

    if "zsh" in shell:
        return os.path.join(home, ".zshrc"), "zsh"
    elif "bash" in shell:
        # Check for .bashrc first (Linux), then .bash_profile (macOS)
        bashrc = os.path.join(home, ".bashrc")
        if os.path.exists(bashrc):
            return bashrc, "bash"
        return os.path.join(home, ".bash_profile"), "bash"
    elif "fish" in shell:
        return os.path.join(home, ".config", "fish", "config.fish"), "fish"

    # Default to .profile
    return os.path.join(home, ".profile"), "sh"


def set_java_home_persistent(java_home: str) -> Tuple[bool, str]:
    """
    Set JAVA_HOME persistently by modifying shell config file.

    :param java_home: Path to JAVA_HOME
    :returns: Tuple of (success, message)
    """
    config_file, shell = get_shell_config_file()
    if not config_file:
        return False, f"Could not determine shell config file for {platform.system()}"

    os_type = platform.system()

    try:
        # Create export line based on shell
        if shell == "PowerShell":
            export_line = f'$env:JAVA_HOME = "{java_home}"'
            path_line = f'$env:PATH = "$env:JAVA_HOME\\bin;$env:PATH"'
            lines_to_add = f"\n# DVT Java Configuration\n{export_line}\n{path_line}\n"
        elif shell == "fish":
            export_line = f'set -gx JAVA_HOME "{java_home}"'
            path_line = 'set -gx PATH "$JAVA_HOME/bin" $PATH'
            lines_to_add = f"\n# DVT Java Configuration\n{export_line}\n{path_line}\n"
        else:
            export_line = f'export JAVA_HOME="{java_home}"'
            path_line = 'export PATH="$JAVA_HOME/bin:$PATH"'
            lines_to_add = f"\n# DVT Java Configuration\n{export_line}\n{path_line}\n"

        # Read existing config
        existing_content = ""
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                existing_content = f.read()

        # Check if we already have a DVT Java section
        if "# DVT Java Configuration" in existing_content:
            # Replace existing section
            pattern = r"# DVT Java Configuration\n[^\n]+\n[^\n]+\n"
            new_content = re.sub(pattern, lines_to_add.lstrip("\n"), existing_content)
        else:
            # Append to file
            new_content = existing_content + lines_to_add

        # Write back
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, "w") as f:
            f.write(new_content)

        # Also set for current session
        os.environ["JAVA_HOME"] = java_home
        bin_path = os.path.join(java_home, "bin")
        os.environ["PATH"] = bin_path + os.pathsep + os.environ.get("PATH", "")

        return True, f"Updated {config_file}. Run 'source {config_file}' or restart terminal."

    except Exception as e:
        return False, f"Failed to update {config_file}: {str(e)}"
