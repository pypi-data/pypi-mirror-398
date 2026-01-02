"""
Java Task Module

Handles DVT java management commands:
- check: Check Java and show compatibility with installed PySpark
- search: Find ALL Java installations on the system
- set: Interactive selection to set JAVA_HOME
- install: Guide for installing compatible Java

v0.51.3: New module for comprehensive Java management.
"""

import os
import platform
from typing import List, Optional

import click

from dbt.compute.java_compat import (
    JavaInstallation,
    find_all_java_installations,
    get_current_java,
    get_pyspark_info,
    get_pyspark_versions_for_java,
    check_java_pyspark_compatibility,
    set_java_home_persistent,
    PYSPARK_JAVA_COMPATIBILITY,
)


class JavaTask:
    """Task for managing Java installations."""

    def check(self) -> bool:
        """
        Check current Java installation and PySpark compatibility.

        Returns:
            bool: True if Java is compatible with installed PySpark
        """
        click.echo()
        click.echo(click.style("Java Status", fg="cyan", bold=True))
        click.echo("-" * 40)

        # Get current Java
        java = get_current_java()
        if java:
            click.echo(f"  JAVA_HOME: {java.path}")
            click.echo(f"  Version:   Java {java.version}")
            click.echo(f"  Vendor:    {java.vendor}")
            click.echo(f"  Details:   {java.version_string}")
        else:
            click.echo(click.style("  ✗ Java not found!", fg="red"))
            click.echo()
            click.echo("  Run 'dvt java search' to find Java installations")
            click.echo("  Run 'dvt java install' for installation guide")
            click.echo()
            return False

        click.echo()
        click.echo(click.style("PySpark Status", fg="cyan", bold=True))
        click.echo("-" * 40)

        # Get PySpark info
        pyspark = get_pyspark_info()
        if pyspark:
            click.echo(f"  Version:       {pyspark.version}")
            click.echo(f"  Required Java: {', '.join(str(v) for v in pyspark.java_supported)}")
            click.echo(f"  Recommended:   Java {pyspark.java_recommended}")
        else:
            click.echo(click.style("  ✗ PySpark not installed!", fg="red"))
            click.echo()
            click.echo("  Install with: pip install pyspark")
            click.echo()
            return False

        click.echo()
        click.echo(click.style("Compatibility", fg="cyan", bold=True))
        click.echo("-" * 40)

        # Check compatibility
        is_compat, msg = check_java_pyspark_compatibility(java.version, pyspark.major_minor)
        if is_compat:
            click.echo(click.style(f"  ✓ {msg}", fg="green"))
        else:
            click.echo(click.style(f"  ✗ {msg}", fg="red"))
            click.echo()
            click.echo("  Run 'dvt java set' to select a compatible Java version")

        click.echo()
        return is_compat

    def search(self) -> List[JavaInstallation]:
        """
        Find all Java installations on the system.

        Returns:
            List of JavaInstallation objects
        """
        click.echo()
        click.echo(click.style("Searching for Java installations...", fg="cyan"))
        click.echo()

        installations = find_all_java_installations()

        if not installations:
            click.echo(click.style("No Java installations found.", fg="yellow"))
            click.echo()
            click.echo("Run 'dvt java install' for installation guide")
            click.echo()
            return []

        click.echo(f"Found {len(installations)} Java installation(s):")
        click.echo()

        # Get PySpark info for compatibility display
        pyspark = get_pyspark_info()

        for i, inst in enumerate(installations, 1):
            # Mark current
            current_marker = click.style(" * CURRENT", fg="green") if inst.is_current else ""

            # Check compatibility with installed PySpark
            if pyspark:
                is_compat, _ = check_java_pyspark_compatibility(inst.version, pyspark.major_minor)
                compat_marker = click.style(" ✓", fg="green") if is_compat else click.style(" ✗", fg="red")
            else:
                compat_marker = ""

            click.echo(f"  [{i}] Java {inst.version} ({inst.vendor}){current_marker}{compat_marker}")
            click.echo(f"      {inst.path}")

            # Show which PySpark versions this Java supports
            compatible_pyspark = get_pyspark_versions_for_java(inst.version)
            if compatible_pyspark:
                click.echo(f"      Compatible with: PySpark {', '.join(compatible_pyspark)}")
            click.echo()

        return installations

    def set_java_home(self, installation: Optional[JavaInstallation] = None) -> bool:
        """
        Interactively select and set JAVA_HOME.

        If no installation provided, presents interactive menu.

        Args:
            installation: Pre-selected JavaInstallation (optional)

        Returns:
            bool: True if successful
        """
        if installation:
            # Direct set
            success, msg = set_java_home_persistent(installation.path)
            if success:
                click.echo(click.style(f"✓ JAVA_HOME set to: {installation.path}", fg="green"))
                click.echo(f"  {msg}")
            else:
                click.echo(click.style(f"✗ {msg}", fg="red"))
            return success

        # Interactive selection
        installations = find_all_java_installations()
        if not installations:
            click.echo(click.style("No Java installations found.", fg="yellow"))
            click.echo("Run 'dvt java install' for installation guide")
            return False

        # Get PySpark info for compatibility display
        pyspark = get_pyspark_info()

        click.echo()
        click.echo(click.style("Select Java installation:", fg="cyan", bold=True))
        click.echo()

        for i, inst in enumerate(installations, 1):
            # Mark current
            current_marker = click.style(" (current)", fg="blue") if inst.is_current else ""

            # Check compatibility with installed PySpark
            if pyspark:
                is_compat, _ = check_java_pyspark_compatibility(inst.version, pyspark.major_minor)
                if is_compat:
                    compat_marker = click.style(" ✓ compatible", fg="green")
                else:
                    compat_marker = click.style(" ✗ incompatible", fg="red")
            else:
                compat_marker = ""

            click.echo(f"  [{i}] Java {inst.version} ({inst.vendor}){current_marker}{compat_marker}")
            click.echo(f"      {inst.path}")
            click.echo()

        # Get user choice
        while True:
            try:
                choice = click.prompt("Your choice", type=int)
                if 1 <= choice <= len(installations):
                    break
                click.echo(click.style(f"Please enter a number between 1 and {len(installations)}", fg="yellow"))
            except click.Abort:
                click.echo("\nAborted.")
                return False

        selected = installations[choice - 1]

        # Warn if incompatible with PySpark
        if pyspark:
            is_compat, msg = check_java_pyspark_compatibility(selected.version, pyspark.major_minor)
            if not is_compat:
                click.echo()
                click.echo(click.style(f"⚠️  Warning: {msg}", fg="yellow"))
                if not click.confirm("Continue anyway?"):
                    return False

        # Set JAVA_HOME
        success, msg = set_java_home_persistent(selected.path)
        click.echo()
        if success:
            click.echo(click.style(f"✓ JAVA_HOME set to: {selected.path}", fg="green"))
            click.echo(f"  {msg}")
        else:
            click.echo(click.style(f"✗ {msg}", fg="red"))

        return success

    def install_guide(self) -> None:
        """
        Show installation guide for compatible Java version.

        Displays platform-specific installation instructions based on
        the installed PySpark version.
        """
        click.echo()

        # Get PySpark info
        pyspark = get_pyspark_info()
        if pyspark:
            click.echo(click.style(f"Java Installation Guide for PySpark {pyspark.version}", fg="cyan", bold=True))
            click.echo("=" * 60)
            click.echo()
            click.echo(f"PySpark {pyspark.major_minor} requires Java: {', '.join(str(v) for v in pyspark.java_supported)}")
            click.echo(f"Recommended: Java {pyspark.java_recommended}")
            recommended = pyspark.java_recommended
        else:
            click.echo(click.style("Java Installation Guide", fg="cyan", bold=True))
            click.echo("=" * 60)
            click.echo()
            click.echo("PySpark is not installed. Assuming Java 17+ for latest PySpark.")
            recommended = 17

        click.echo()
        os_type = platform.system()

        if os_type == "Darwin":  # macOS
            click.echo(click.style("📦 macOS Installation Options:", fg="yellow", bold=True))
            click.echo()
            click.echo("  Option 1: Homebrew (recommended)")
            click.echo(click.style(f"    brew install openjdk@{recommended}", fg="green"))
            click.echo()
            click.echo("  Option 2: SDKMAN (multiple versions)")
            click.echo(click.style("    curl -s \"https://get.sdkman.io\" | bash", fg="green"))
            click.echo(click.style(f"    sdk install java {recommended}.0.2-tem", fg="green"))
            click.echo()
            click.echo("  Option 3: Download manually")
            click.echo(click.style("    https://adoptium.net/", fg="blue"))
            click.echo()
            click.echo("  After installation:")
            click.echo(f"    export JAVA_HOME=$(/usr/libexec/java_home -v {recommended})")

        elif os_type == "Linux":
            click.echo(click.style("📦 Linux Installation Options:", fg="yellow", bold=True))
            click.echo()
            click.echo("  Ubuntu/Debian:")
            click.echo(click.style("    sudo apt-get update", fg="green"))
            click.echo(click.style(f"    sudo apt-get install openjdk-{recommended}-jdk", fg="green"))
            click.echo()
            click.echo("  RHEL/CentOS/Fedora:")
            click.echo(click.style(f"    sudo dnf install java-{recommended}-openjdk-devel", fg="green"))
            click.echo()
            click.echo("  Arch Linux:")
            click.echo(click.style(f"    sudo pacman -S jdk{recommended}-openjdk", fg="green"))
            click.echo()
            click.echo("  SDKMAN (any distro):")
            click.echo(click.style("    curl -s \"https://get.sdkman.io\" | bash", fg="green"))
            click.echo(click.style(f"    sdk install java {recommended}.0.2-tem", fg="green"))
            click.echo()
            click.echo("  After installation:")
            click.echo(f"    export JAVA_HOME=/usr/lib/jvm/java-{recommended}-openjdk")

        elif os_type == "Windows":
            click.echo(click.style("📦 Windows Installation Options:", fg="yellow", bold=True))
            click.echo()
            click.echo("  Option 1: Winget (Windows 11/10)")
            click.echo(click.style(f"    winget install EclipseAdoptium.Temurin.{recommended}.JDK", fg="green"))
            click.echo()
            click.echo("  Option 2: Chocolatey")
            click.echo(click.style(f"    choco install temurin{recommended}", fg="green"))
            click.echo()
            click.echo("  Option 3: Scoop")
            click.echo(click.style("    scoop bucket add java", fg="green"))
            click.echo(click.style(f"    scoop install temurin{recommended}-jdk", fg="green"))
            click.echo()
            click.echo("  Option 4: Download manually")
            click.echo(click.style("    https://adoptium.net/", fg="blue"))
            click.echo()
            click.echo("  After installation:")
            click.echo("    Set JAVA_HOME in System Environment Variables")

        click.echo()
        click.echo(click.style("After installing Java:", fg="cyan"))
        click.echo("  1. Restart your terminal")
        click.echo("  2. Run 'dvt java search' to verify")
        click.echo("  3. Run 'dvt java set' to select the installation")
        click.echo()
