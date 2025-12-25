#!/usr/bin/env python
"""YAML formatting and validation utilities for the project.

This script provides automated YAML formatting using yamlfmt and validation
using yamllint, with the ability to automatically apply fixes when issues are found.

Usage:
    python scripts/format_yaml.py           # Format and validate YAML files (default)
    python scripts/format_yaml.py --check-only  # Check formatting only, no fixes
    python scripts/format_yaml.py --fix     # Same as default behavior (format and validate)

    # Or using uv:
    uv run format-yaml                       # Format and validate YAML files
    uv run format-yaml --check-only         # Check formatting only
    uv run format-yaml --fix                # Format and validate

The script runs yamlfmt to format YAML files and yamllint to validate them,
providing consistent YAML formatting across the codebase.
"""

import argparse
import shlex
import shutil
import subprocess
import sys


def run_command(cmd: str | list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command safely without shell injection vulnerabilities.

    Args:
        cmd: Command to run - either a string (will be safely parsed) or list of arguments
        check: Whether to exit on failure

    Returns:
        CompletedProcess instance with command results

    Note:
        This function uses shell=False for security. Commands are parsed into argument
        lists using shlex.split() to prevent shell injection attacks. If you genuinely
        need shell features (pipes, redirects, etc.), use Python equivalents instead.
    """
    # Convert string commands to lists safely
    if isinstance(cmd, str):
        print(f"Running: {cmd}")
        cmd_list = shlex.split(cmd)
    else:
        print(f"Running: {' '.join(cmd)}")
        cmd_list = cmd

    # Always use shell=False for security
    result = subprocess.run(cmd_list, shell=False, capture_output=True, text=True)

    if check and result.returncode != 0:
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        sys.exit(result.returncode)

    return result


def check_dependencies() -> bool:
    """Check if yamlfmt and yamllint are available."""
    missing_deps = []

    if not shutil.which("yamlfmt"):
        missing_deps.append("yamlfmt")

    if not shutil.which("yamllint"):
        missing_deps.append("yamllint")

    if missing_deps:
        print("Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nTo install:")
        if "yamlfmt" in missing_deps:
            print("  brew install yamlfmt  # or go install github.com/google/yamlfmt/cmd/yamlfmt@latest")
        if "yamllint" in missing_deps:
            print("  brew install yamllint  # or pip install yamllint")
        return False

    return True


def format_yaml_files() -> bool:
    """Format YAML files using yamlfmt and return True if successful."""
    print("\n🔧 Formatting YAML files with yamlfmt...")

    format_result = run_command("yamlfmt .", check=False)

    if format_result.returncode != 0:
        print("yamlfmt formatting failed")
        if format_result.stdout:
            print("yamlfmt output:", format_result.stdout)
        if format_result.stderr:
            print("yamlfmt errors:", format_result.stderr)
        return False

    print("✅ YAML formatting complete!")
    return True


def validate_yaml_files() -> bool:
    """Validate YAML files using yamllint and return True if successful."""
    print("\n🔍 Validating YAML files with yamllint...")

    lint_result = run_command("yamllint .", check=False)

    if lint_result.returncode != 0:
        print("yamllint validation failed")
        if lint_result.stdout:
            print("yamllint output:")
            print(lint_result.stdout)
        if lint_result.stderr:
            print("yamllint errors:")
            print(lint_result.stderr)
        return False

    print("✅ All YAML files pass yamllint validation!")
    return True


def main() -> None:
    """Run YAML formatting and validation."""
    parser = argparse.ArgumentParser(description="Format and validate YAML files")
    parser.add_argument("--check-only", action="store_true", help="Only validate YAML files, don't apply formatting")
    parser.add_argument("--fix", action="store_true", help="Format and validate YAML files (same as default behavior)")

    args = parser.parse_args()

    # Check for required dependencies
    if not check_dependencies():
        sys.exit(1)

    # Default behavior is to format and validate unless --check-only is specified
    should_format = not args.check_only

    if should_format:
        print("🔧 Running YAML formatting and validation...")

        # Format YAML files
        format_success = format_yaml_files()
        if not format_success:
            sys.exit(1)

        # Validate formatted files
        validation_success = validate_yaml_files()
        if not validation_success:
            sys.exit(1)

        print("\n✅ All YAML files formatted and validated successfully!")

    else:
        print("🔍 Running YAML validation only...")

        # Only validate, don't format
        validation_success = validate_yaml_files()
        if not validation_success:
            print("\n🔧 To fix formatting issues, run:")
            print("  uv run format-yaml")
            print("  # or")
            print("  python scripts/format_yaml.py")
            sys.exit(1)

        print("\n✅ All YAML files pass validation!")


if __name__ == "__main__":
    main()
