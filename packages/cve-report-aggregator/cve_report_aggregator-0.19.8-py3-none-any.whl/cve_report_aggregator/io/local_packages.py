"""Local Zarf package scanner for extracting SBOMs from .tar.zst archives."""

from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

from ..core.executor import ExecutorManager
from ..core.models import PackageConfig

if TYPE_CHECKING:
    from ..context import AppContext

console = Console()


def detect_local_packages(packages_dir: Path) -> list[Path]:
    """Detect local Zarf package archives in the packages directory.

    Searches for .tar.zst files which are Zarf package archives.
    Filters out Zarf init packages (zarf-init-*) as they contain
    infrastructure components rather than application packages.

    Args:
        packages_dir: Directory to search for Zarf packages

    Returns:
        List of paths to .tar.zst archive files (excluding init packages)

    Example:
        >>> packages = detect_local_packages(Path("./packages"))
        >>> for pkg in packages:
        ...     print(f"Found: {pkg.name}")
    """
    if not packages_dir.exists() or not packages_dir.is_dir():
        return []

    # Find all .tar.zst files (Zarf package archives)
    archives = list(packages_dir.glob("*.tar.zst"))

    # Filter out Zarf init packages (they contain infrastructure, not app packages)
    filtered_archives = [archive for archive in archives if not archive.name.startswith("zarf-init-")]

    return sorted(filtered_archives)


def extract_package_metadata(archive_path: Path, context: AppContext) -> PackageConfig:
    """Extract package metadata from Zarf archive using uds zarf inspect.

    Uses the `uds zarf package inspect definition` command to extract package
    name, version, and architecture from the archive metadata.

    Command format:
        uds zarf package inspect definition <archive> --no-color

    Args:
        archive_path: Path to Zarf package archive (.tar.zst)
        context: Application context with config and services

    Returns:
        PackageConfig with extracted metadata

    Raises:
        RuntimeError: If zarf command fails or metadata cannot be parsed
        ValueError: If required metadata fields are missing

    Example:
        >>> archive = Path("./packages/zarf-package-gitlab-amd64-18.4.2-uds.0-unicorn.tar.zst")
        >>> metadata = extract_package_metadata(archive, context)
        >>> print(f"{metadata.name} v{metadata.version} ({metadata.architecture})")
    """
    config = context.config
    logger = context.get_logger(__name__)
    is_debug = config.log_level == "DEBUG"

    if not archive_path.exists():
        raise ValueError(f"Archive does not exist: {archive_path}")

    if is_debug:
        logger.debug(
            "Extracting package metadata",
            archive=str(archive_path.name),
        )

    # Build the command: uds zarf package inspect definition <archive> --no-color
    command = [
        "uds",
        "zarf",
        "package",
        "inspect",
        "definition",
        str(archive_path),
        "--no-color",
    ]

    # Execute the command
    output, error = ExecutorManager.execute(command, cwd=None, config=config)

    if error:
        logger.error(
            "Failed to extract package metadata",
            archive=str(archive_path.name),
            error=str(error),
        )
        raise RuntimeError(f"Failed to inspect Zarf package: {archive_path.name}") from error

    # Parse YAML output to extract metadata
    # The output is YAML format, we need to extract:
    # - metadata.name
    # - metadata.version
    # - metadata.architecture
    try:
        # Parse as simple key-value pairs (lightweight YAML parsing)
        # Since we only need a few fields, we'll use regex/string parsing
        # to avoid adding PyYAML dependency

        name = None
        version = None
        architecture = None

        # Parse line by line
        for line in output.split("\n"):
            line = line.strip()

            # Look for metadata fields
            if line.startswith("name:"):
                name = line.split(":", 1)[1].strip()
            elif line.startswith("version:"):
                version = line.split(":", 1)[1].strip()
            elif line.startswith("architecture:"):
                architecture = line.split(":", 1)[1].strip()

        # Validate required fields
        if not name:
            raise ValueError("Package name not found in metadata")
        if not version:
            raise ValueError("Package version not found in metadata")
        if not architecture:
            # Default to amd64 if not specified
            architecture = "amd64"
            logger.warning(
                "Architecture not found in metadata, defaulting to amd64",
                archive=str(archive_path.name),
            )

        if is_debug:
            logger.debug(
                "Extracted package metadata",
                name=name,
                version=version,
                architecture=architecture,
            )

        return PackageConfig(
            name=name,
            version=version,
            architecture=architecture,
        )

    except (ValueError, KeyError, IndexError) as e:
        logger.error(
            "Failed to parse package metadata",
            archive=str(archive_path.name),
            error=str(e),
        )
        raise RuntimeError(f"Failed to parse metadata from {archive_path.name}") from e


def extract_package_sboms(
    archive_path: Path,
    package: PackageConfig,
    output_dir: Path,
    context: AppContext,
) -> list[Path]:
    """Extract SBOM files from Zarf package archive.

    Uses the `uds zarf package inspect` command with `--sbom-out` flag to extract
    SBOM files from the archive to the output directory.

    Command format:
        uds zarf package inspect --sbom-out <output_dir>/<package_name> --no-color <archive>

    Args:
        archive_path: Path to Zarf package archive (.tar.zst)
        package: Package configuration (name, version, architecture)
        output_dir: Directory to store the extracted SBOM files
        context: Application context with config and services

    Returns:
        List of paths to extracted SBOM JSON files

    Raises:
        RuntimeError: If zarf command fails or no SBOMs are found

    Example:
        >>> archive = Path("./packages/zarf-package-gitlab-amd64-18.4.2-uds.0-unicorn.tar.zst")
        >>> pkg = PackageConfig(name="gitlab", version="18.4.2-uds.0-unicorn", architecture="amd64")
        >>> sboms = extract_package_sboms(archive, pkg, Path("./reports"), context)
        >>> print(f"Extracted {len(sboms)} SBOM files")
    """
    config = context.config
    logger = context.get_logger(__name__)
    is_debug = config.log_level == "DEBUG"

    if not archive_path.exists():
        raise ValueError(f"Archive does not exist: {archive_path}")

    # Create package-specific output directory
    package_output_dir = output_dir / package.name
    package_output_dir.mkdir(parents=True, exist_ok=True)

    if is_debug:
        logger.info(
            "Extracting SBOMs from local package",
            package=package.name,
            version=package.version,
            architecture=package.architecture,
            archive=str(archive_path.name),
            output_dir=str(package_output_dir),
        )

    # Build the command
    # uds zarf package inspect --sbom-out <output_dir> --no-color <archive>
    command = [
        "uds",
        "zarf",
        "package",
        "inspect",
        str(archive_path),
        "--sbom-out",
        str(package_output_dir),
        "--no-color",
    ]

    # Execute the command
    output, error = ExecutorManager.execute(command, cwd=None, config=config)

    if error:
        logger.error(
            "Failed to extract SBOMs",
            package=package.name,
            version=package.version,
            archive=str(archive_path.name),
            error=str(error),
        )
        raise RuntimeError(f"Failed to extract SBOMs from {archive_path.name}: {error}") from error

    # Find all JSON files in the extracted directory
    sbom_files: list[Path] = []
    if package_output_dir.exists():
        # Search for JSON files at root level only (excludes nested directories)
        json_files = list(package_output_dir.glob("*.json"))

        for json_file in json_files:
            sbom_files.append(json_file)

            if is_debug:
                logger.debug(
                    "Found SBOM file",
                    package=package.name,
                    file=str(json_file.relative_to(output_dir)),
                )

    if not sbom_files:
        logger.warning(
            "No SBOM JSON files found in extracted archive",
            package=package.name,
            version=package.version,
            archive=str(archive_path.name),
        )

    return sbom_files


def scan_local_packages(output_dir: Path, context: AppContext) -> list[Path]:
    """Scan local Zarf package archives and extract SBOMs.

    This is the main entry point for processing local Zarf packages.
    It detects archives in the packages/ directory, extracts metadata,
    and then extracts SBOM files for scanning.

    Workflow:
        1. Check if packages/ directory exists
        2. Find all .tar.zst files in packages/
        3. For each archive:
           - Extract metadata (name, version, architecture)
           - Extract SBOMs to output_dir/<package_name>/
        4. Return list of all extracted SBOM files

    Args:
        output_dir: Directory to store extracted SBOM files
        context: Application context with config and services

    Returns:
        List of paths to extracted SBOM JSON files

    Raises:
        ValueError: If packages directory doesn't exist
        RuntimeError: If extraction fails for any package

    Example:
        >>> context = AppContext(config)
        >>> sbom_files = scan_local_packages(Path("./reports"), context)
        >>> print(f"Extracted {len(sbom_files)} SBOM files from local packages")
    """
    config = context.config
    logger = context.get_logger(__name__)
    is_debug = config.log_level == "DEBUG"

    # Determine packages directory (defaults to ./packages)
    packages_dir = Path.cwd() / "packages"

    if not packages_dir.exists():
        logger.debug(
            "Packages directory does not exist, skipping local package scan",
            packages_dir=str(packages_dir),
        )
        return []

    # Detect local packages
    archives = detect_local_packages(packages_dir)

    if not archives:
        logger.debug(
            "No local Zarf packages found",
            packages_dir=str(packages_dir),
        )
        return []

    if is_debug:
        console.print(f"\n[cyan]Found {len(archives)} local Zarf package(s) in {packages_dir.name}/[/cyan]")
        for archive in archives:
            console.print(f"  • [dim]{archive.name}[/dim]")
        console.print()

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process each archive
    all_sbom_files: list[Path] = []
    processed_packages: list[PackageConfig] = []

    for archive in archives:
        try:
            # Extract metadata
            package = extract_package_metadata(archive, context)

            if is_debug:
                console.print(f"[cyan]Processing:[/cyan] {package.name} v{package.version} ({package.architecture})")

            # Extract SBOMs
            sbom_files = extract_package_sboms(
                archive_path=archive,
                package=package,
                output_dir=output_dir,
                context=context,
            )

            all_sbom_files.extend(sbom_files)
            processed_packages.append(package)

            if is_debug:
                console.print(f"  [green]✓[/green] Extracted {len(sbom_files)} SBOM file(s)")

        except (ValueError, RuntimeError) as e:
            logger.error(
                "Failed to process local package",
                archive=str(archive.name),
                error=str(e),
            )
            if is_debug:
                console.print(f"  [red]✗[/red] Error: {e}")

            # Continue with other packages instead of failing completely
            continue

    # Update config with processed packages (for use in report generation)
    # This ensures that the unified reports use package version in filenames
    if processed_packages and not config.packages:
        config.packages = processed_packages

    if is_debug and all_sbom_files:
        console.print(
            f"\n[green]✓[/green] Extracted {len(all_sbom_files)} SBOM file(s) "
            f"from {len(processed_packages)} local package(s)\n"
        )

    return all_sbom_files


# Public API
__all__ = [
    "detect_local_packages",
    "extract_package_metadata",
    "extract_package_sboms",
    "scan_local_packages",
]
