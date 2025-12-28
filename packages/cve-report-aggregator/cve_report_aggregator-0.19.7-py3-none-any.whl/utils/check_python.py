#!/usr/bin/env python3
"""Check Python version compatibility for CVE Report Aggregator.

This utility verifies the current Python version and checks package compatibility,
providing recommendations for development and Docker builds.

Usage:
    uv run check-python      # Check Python version and package compatibility
"""

import sys


def check_python_version() -> tuple[int, int, int]:
    """Check current Python version.

    Returns:
        Tuple of (major, minor, micro) version numbers
    """
    version = sys.version_info
    print(f"Current Python: {version.major}.{version.minor}.{version.micro}")
    print(f"Full version: {sys.version}")
    return version.major, version.minor, version.micro


def check_package_compatibility(python_version: tuple[int, int, int]) -> None:
    """Check if key packages support the Python version.

    Args:
        python_version: Tuple of (major, minor, micro) version numbers
    """
    packages: dict[str, dict[str, str]] = {
        "3.12": {
            "rich": "Full support",
            "click": "Full support",
            "rich-click": "Full support",
            "pytest": "Full support",
            "pytest-cov": "Full support",
            "ruff": "Full support",
            "mypy": "Full support",
        },
        "3.13": {
            "rich": "Full support",
            "click": "Full support",
            "rich-click": "Full support",
            "pytest": "Full support",
            "pytest-cov": "Full support",
            "ruff": "Full support",
            "mypy": "Full support",
        },
    }

    version_str = f"{python_version[0]}.{python_version[1]}"
    if version_str in packages:
        print(f"\nPackage compatibility for Python {version_str}:")
        print("-" * 50)
        for pkg, status in packages[version_str].items():
            print(f"  {pkg:15} {status}")
    else:
        print(f"Unknown Python version: {version_str}")
        print("This project requires Python 3.12+")


def check_installed_packages() -> None:
    """Check which packages are actually installed."""
    print("\nInstalled package check:")
    print("-" * 50)

    packages_to_check = [
        "rich",
        "click",
        "rich_click",
        "pytest",
        "pytest_cov",
        "ruff",
        "mypy",
    ]

    for package in packages_to_check:
        package_import = package.replace("-", "_")
        try:
            module = __import__(package_import)
            version = getattr(module, "__version__", "unknown")
            print(f"  {package:20} {version}")
        except ImportError:
            print(f"{package:20} not installed")


def suggest_dockerfile() -> None:
    """Suggest which Dockerfile to use based on Python version."""
    print("\n" + "=" * 60)
    print("Docker Build Recommendations:")
    print("=" * 60)

    version = sys.version_info

    if version.major == 3 and version.minor == 13:
        print("\nPython 3.13 detected - Full support available")
        print("\nRecommended Docker image:")
        print("   - python:3.13-alpine for production builds")
        print("   - python:3.13-slim for development")

    elif version.major == 3 and version.minor == 12:
        print("\nPython 3.12 - Full support available")
        print("\nRecommended Docker images:")
        print("   - python:3.12.12-alpine (current production)")
        print("   - python:3.12-slim for development")

    else:
        print(f"\nPython {version.major}.{version.minor} is not supported")
        print("This project requires Python 3.12 or higher")

    print("\nDocker build commands:")
    print("  # Build Docker image")
    print("  docker build -f docker/Dockerfile -t cve-report-aggregator:latest .")
    print("\n  # Run CLI in container")
    print("  docker run --rm -v $(pwd)/reports:/home/cve-aggregator/reports \\")
    print("    cve-report-aggregator:latest -i reports -o unified-report.json")
    print("\n  # Check scanner versions")
    print("  docker run --rm cve-report-aggregator:latest grype version")
    print("  docker run --rm cve-report-aggregator:latest trivy --version")


def check_external_tools() -> None:
    """Check if external vulnerability scanners are installed."""
    print("\n" + "=" * 60)
    print("External Scanner Availability:")
    print("=" * 60)

    import subprocess

    tools = {
        "grype": "Grype vulnerability scanner",
        "trivy": "Trivy vulnerability scanner",
        "syft": "Syft SBOM generator",
        "uds": "UDS CLI (optional)",
    }

    for tool, description in tools.items():
        try:
            result = subprocess.run(
                ["which", tool],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                path = result.stdout.strip()
                # Get version
                try:
                    version_result = subprocess.run(
                        [tool, "version"] if tool != "trivy" else [tool, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=2,
                    )
                    version = version_result.stdout.strip().split("\n")[0]
                    print(f"  {tool:10} {description:30} ({version})")
                except Exception:
                    print(f"  {tool:10} {description:30} (at {path})")
            else:
                print(f"{tool:10} {description:30} (not found)")
        except Exception:
            print(f"{tool:10} {description:30} (error checking)")


def main() -> None:
    """Run all compatibility checks."""
    import argparse

    parser = argparse.ArgumentParser(description="Check Python version compatibility for CVE Report Aggregator")
    parser.add_argument("--packages-only", action="store_true", help="Only check installed packages")
    parser.add_argument("--docker-only", action="store_true", help="Only show Docker recommendations")
    parser.add_argument("--scanners-only", action="store_true", help="Only check external scanners")
    args = parser.parse_args()

    print("=" * 60)
    print("CVE Report Aggregator - Compatibility Check")
    print("=" * 60)

    if args.scanners_only:
        check_external_tools()
    elif args.packages_only:
        version = check_python_version()
        check_package_compatibility(version)
        check_installed_packages()
    elif args.docker_only:
        check_python_version()
        suggest_dockerfile()
    else:
        # Run all checks
        version = check_python_version()
        check_package_compatibility(version)
        check_installed_packages()
        check_external_tools()
        suggest_dockerfile()

    print("\n" + "=" * 60)
    print("Check complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
