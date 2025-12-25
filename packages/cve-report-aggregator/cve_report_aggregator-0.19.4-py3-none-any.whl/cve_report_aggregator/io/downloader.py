"""Package downloader for fetching SBOM reports from remote registries."""

from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

from ..core.constants import (
    DEFAULT_CPU_COUNT,
    DEFAULT_PROTOCOL,
    MAX_WORKER_LIMIT,
    RESERVED_THREADS,
    THREAD_MULTIPLIER,
    UDS_LOG_LEVEL_MAP,
)
from ..core.exceptions import AuthenticationError, ConfigurationError
from ..core.executor import ExecutorManager
from ..core.models import PackageConfig

if TYPE_CHECKING:
    from ..context import AppContext

console = Console()


def validate_registry_authentication(registry: str, organization: str, context: AppContext) -> None:
    """Validate registry authentication before attempting any downloads.

    Makes a lightweight API call to verify that the registry credentials are valid.
    This prevents wasting time and resources attempting downloads that will fail
    due to authentication issues.

    Uses the `uds zarf package list` command to check registry access. This command
    will fail with a 401/403 error if credentials are invalid or missing.

    Args:
        registry: Container registry URL
        organization: Organization or namespace in the registry
        context: Application context with config and services

    Raises:
        AuthenticationError: If registry credentials are invalid or missing
        RuntimeError: If the validation check fails for other reasons
    """
    config = context.config
    logger = context.get_logger(__name__)
    is_debug = config.log_level == "DEBUG"

    # Map application log level to UDS CLI log level
    uds_log_level = UDS_LOG_LEVEL_MAP.get(config.log_level, "info")

    # Construct a test registry reference
    # We'll try to list packages from the organization to validate credentials
    registry_ref = f"{DEFAULT_PROTOCOL}://{registry}/{organization}"

    if is_debug:
        logger.debug(
            "Validating registry authentication",
            registry=registry,
            organization=organization,
        )

    # Build the validation command
    # uds zarf package list <registry>/<organization> --log-level <level>
    command = [
        "uds",
        "zarf",
        "package",
        "list",
        registry_ref,
        "--log-level",
        uds_log_level,
    ]

    # Execute the command
    output, error = ExecutorManager.execute(command, cwd=None, config=config)

    if error:
        # Parse the error using error handler from context
        error_handler = context.error_handler

        # Classify the error to determine if it's an authentication issue
        error_type = error_handler.classify_error(output)

        if error_type == "authentication":
            # Extract status code if available
            status_code = error_handler.extract_http_status_code(output)

            # Create a detailed authentication error
            auth_error = AuthenticationError(
                package_name="<validation>",
                package_version="<none>",
                status_code=status_code or 401,
                original_error=error,
            )

            logger.error(
                "Registry authentication validation failed",
                registry=registry,
                organization=organization,
                error_type="AuthenticationError",
                error=str(auth_error),
            )

            raise auth_error

        # If it's not an authentication error, it might be a network or other issue
        # We'll log it but not necessarily fail - the registry might just not support
        # the list command, but package downloads might still work
        logger.warning(
            "Registry validation returned an error, but continuing anyway",
            registry=registry,
            organization=organization,
            error_type=error_type,
            error=output,
        )

    if is_debug:
        logger.debug(
            "Registry authentication validation successful",
            registry=registry,
            organization=organization,
        )


def download_package_sboms(output_dir: Path, context: AppContext) -> list[Path]:
    """Download SBOM reports for all configured packages using concurrent workers.

    This function uses ThreadPoolExecutor to download SBOM reports in parallel,
    significantly improving performance when processing multiple packages.
    The `uds zarf package inspect sbom` command is used to download SBOM reports
    from a remote registry for each package specified in the configuration.

    Args:
        output_dir: Directory to store downloaded SBOM reports
        context: Application context with config and services

    Returns:
        List of paths to downloaded SBOM JSON files

    Raises:
        ValueError: If required configuration is missing
        RuntimeError: If download fails for any package
    """
    import os
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from threading import Lock

    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn

    config = context.config
    logger = context.get_logger(__name__)

    # Validate required configuration
    if not config.download_remote_packages:
        logger.debug("download_remote_packages is False, skipping package downloads")
        return []

    if not config.registry:
        raise ValueError("Registry URL is required when download_remote_packages is enabled")

    if not config.organization:
        raise ValueError("Organization is required when download_remote_packages is enabled")

    if not config.packages:
        logger.warning("No packages configured for download")
        return []

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine number of workers based on system resources
    cpu_count = os.cpu_count() or DEFAULT_CPU_COUNT
    max_threads = cpu_count * THREAD_MULTIPLIER - RESERVED_THREADS
    if config.max_workers is not None:
        # Use user-specified max_workers, but cap at recommended maximum if needed
        if config.max_workers > max_threads:
            logger.warning(
                f"max_workers ({config.max_workers}) is greater than the recommended maximum ({max_threads}). "
                "This may cause performance issues, therefore, it will be capped."
            )
            max_workers = max_threads
        else:
            max_workers = config.max_workers
    else:
        # Auto-detect optimal worker count for I/O-bound operations
        # No point creating more threads than packages to download
        max_workers = min(len(config.packages), MAX_WORKER_LIMIT, max_threads)

    is_debug = config.log_level == "DEBUG"

    # Thread-safe structures
    downloaded_files: list[Path] = []
    files_lock = Lock()

    if is_debug:
        console.print(f"\n[cyan]Downloading SBOM reports for {len(config.packages)} packages...")
        console.print(f"[cyan]Using {max_workers} concurrent workers[/cyan]\n")

    # Type narrowing with runtime validation
    # These should have been validated earlier, but we check again for safety
    if config.registry is None:
        raise ConfigurationError("Registry URL is required for package downloads")
    if config.organization is None:
        raise ConfigurationError("Organization is required for package downloads")

    registry: str = config.registry
    organization: str = config.organization

    # Validate registry authentication before attempting any downloads
    # This prevents wasting time/resources on failed downloads due to auth issues
    try:
        validate_registry_authentication(registry, organization, context)
    except AuthenticationError as e:
        logger.error(
            "Pre-flight authentication check failed - aborting all downloads",
            registry=registry,
            organization=organization,
            error=str(e),
        )
        if is_debug:
            console.print(f"\n[red]✗[/red] Authentication failed: {e.message}")
            console.print("[yellow]Please check your registry credentials and try again.[/yellow]\n")
        raise

    # Function to download a single package (will be run in thread pool)
    def download_single_package(package: PackageConfig) -> tuple[PackageConfig, list[Path] | Exception]:
        """Download SBOM for a single package.

        Returns:
            Tuple of (package, result) where result is either:
            - list[Path]: Successfully downloaded SBOM files
            - Exception: Error that occurred during download
        """
        try:
            sbom_files = download_package_sbom(
                package=package,
                registry=registry,
                organization=organization,
                output_dir=output_dir,
                context=context,
            )
            return (package, sbom_files)
        except Exception as e:
            return (package, e)

    # Download packages in parallel using ThreadPoolExecutor with progress tracking
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=not is_debug,  # Keep progress visible in debug mode
        ) as progress:
            # Add progress task
            task_id = progress.add_task(
                f"[cyan]Downloading {len(config.packages)} packages...", total=len(config.packages)
            )

            # Submit all download tasks
            future_to_package = {
                executor.submit(download_single_package, package): package for package in config.packages
            }

            # Process completed downloads as they finish
            for future in as_completed(future_to_package):
                package, result = future.result()

                if isinstance(result, Exception):
                    # Download failed - result is now a specific PackageDownloadError subclass
                    error = result
                    error_type = type(error).__name__

                    logger.error(
                        "Package download failed",
                        package=package.name,
                        version=package.version,
                        error_type=error_type,
                        error=str(error),
                    )

                    if is_debug:
                        # Show error type and message
                        # Use .message attribute for PackageDownloadError, fallback to str(error) for others
                        error_msg = error.message if hasattr(error, "message") else str(error)
                        console.print(f"  [red]✗[/red] {package.name}-{package.version}: [{error_type}] {error_msg}")

                    # Update progress
                    progress.update(task_id, advance=1)

                    # Continue with other packages instead of failing completely
                    continue
                else:
                    # Download succeeded
                    sbom_files = result

                    # Thread-safe append to results
                    with files_lock:
                        downloaded_files.extend(sbom_files)

                    if is_debug:
                        for sbom_file in sbom_files:
                            console.print(f"  [green]✓[/green] Downloaded: {sbom_file.name}")

                    # Update progress
                    progress.update(task_id, advance=1)

    if is_debug:
        console.print(
            f"\n[green]✓[/green] Downloaded {len(downloaded_files)} SBOM files from {len(config.packages)} packages\n"
        )

    return downloaded_files


def download_package_sbom(
    package: PackageConfig,
    registry: str,
    organization: str,
    output_dir: Path,
    context: AppContext,
    protocol: str = DEFAULT_PROTOCOL,
) -> list[Path]:
    """Download SBOM report for a single package from remote registry.

    Uses the `uds zarf package inspect sbom` command to download the SBOM
    report for a specific package. The command extracts SBOM files directly
    to the output directory under a package-specific subdirectory.

    Command format:
        uds zarf package inspect sbom <registry>/<organization>/<package-name>-<version> \\
            -a <architecture> --output <output-dir>/<package-name>

    Args:
        package: Package configuration (name, version, architecture)
        registry: Container registry URL
        organization: Organization or namespace in the registry
        output_dir: Directory to store the downloaded SBOM files
        context: Application context with config and services
        protocol: Protocol prefix (default: oci)

    Returns:
        List of paths to downloaded SBOM JSON files

    Raises:
        RuntimeError: If the download command fails
        ValueError: If package configuration is invalid
    """
    # Validate package configuration
    if not package.name:
        raise ValueError("Package name is required")
    if not package.version:
        raise ValueError("Package version is required")
    if not package.architecture:
        raise ValueError("Package architecture is required")

    # Get config and logger from context
    config = context.config
    logger = context.get_logger(__name__)
    is_debug = config.log_level == "DEBUG"

    # Map application log level to UDS CLI log level
    # Application: DEBUG, INFO, WARNING, ERROR, CRITICAL
    # UDS CLI: trace, debug, info, warn
    uds_log_level = UDS_LOG_LEVEL_MAP.get(config.log_level, "info")

    # Construct package reference
    # Format: <registry>/<organization>/<package-name>:<version>
    package_ref = f"{registry}/{organization}/{package.name}:{package.version}"

    # Build the command
    # uds zarf package inspect sbom <package-ref> -a <arch> --output <dir> --log-level <level>
    # Note: The uds command automatically creates a subdirectory named after the package
    # So passing --output reports will create reports/<package-name>/
    command = [
        "uds",
        "zarf",
        "package",
        "inspect",
        "sbom",
        f"{protocol}://{package_ref}",
        "-a",
        package.architecture,
        "--output",
        str(output_dir),
        "--log-level",
        uds_log_level,
    ]

    # The uds command will create this directory
    package_output_dir = output_dir / package.name

    if is_debug:
        logger.info(
            "Downloading package SBOM",
            package=package.name,
            version=package.version,
            architecture=package.architecture,
            registry=registry,
            organization=organization,
            output_dir=str(package_output_dir),
        )

    # Execute the command
    output, error = ExecutorManager.execute(command, cwd=None, config=config)

    if error:
        # Parse the error using error handler from context
        error_handler = context.error_handler
        parsed_error = error_handler.parse_download_error(
            package=package,
            error_output=output,  # Combined stdout + stderr from ExecutorManager
            original_error=error,
        )

        logger.error(
            "SBOM download failed",
            package=package.name,
            version=package.version,
            error_type=type(parsed_error).__name__,
            error=str(parsed_error),
        )
        raise parsed_error

    # Find all JSON files in the downloaded directory
    sbom_files: list[Path] = []
    if package_output_dir.exists():
        # Search for JSON files recursively
        json_files = list(package_output_dir.rglob("*.json"))

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
            "No SBOM JSON files found for package",
            package=package.name,
            version=package.version,
        )

    return sbom_files
