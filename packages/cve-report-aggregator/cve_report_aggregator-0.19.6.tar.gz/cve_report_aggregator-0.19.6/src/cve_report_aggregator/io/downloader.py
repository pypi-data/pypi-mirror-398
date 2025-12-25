"""Package downloader for fetching SBOM reports from remote registries."""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn

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


# =============================================================================
# Configuration and Result Types
# =============================================================================


@dataclass
class WorkerConfig:
    """Configuration for parallel worker execution."""

    max_workers: int
    cpu_count: int
    package_count: int


@dataclass
class DownloadResult:
    """Result from a package download operation."""

    package: PackageConfig
    sbom_files: list[Path] = field(default_factory=list)
    error: Exception | None = None

    @property
    def is_success(self) -> bool:
        """Check if download was successful."""
        return self.error is None


@dataclass
class DownloadTracker:
    """Thread-safe tracker for download results."""

    downloaded_files: list[Path] = field(default_factory=list)
    errors: list[tuple[PackageConfig, Exception]] = field(default_factory=list)
    _lock: Lock = field(default_factory=Lock)

    def add_success(self, sbom_files: list[Path]) -> None:
        """Record successful download."""
        with self._lock:
            self.downloaded_files.extend(sbom_files)

    def add_error(self, package: PackageConfig, error: Exception) -> None:
        """Record download error."""
        with self._lock:
            self.errors.append((package, error))


# =============================================================================
# Worker Calculation
# =============================================================================


def _calculate_optimal_workers(
    config_max_workers: int | None,
    package_count: int,
    logger: Any,
) -> WorkerConfig:
    """Calculate optimal number of workers for package downloads.

    Args:
        config_max_workers: User-specified maximum workers, or None for auto
        package_count: Number of packages to download
        logger: Logger instance for warnings

    Returns:
        WorkerConfig with calculated worker count
    """
    cpu_count = os.cpu_count() or DEFAULT_CPU_COUNT
    max_threads = cpu_count * THREAD_MULTIPLIER - RESERVED_THREADS

    if config_max_workers is not None:
        if config_max_workers > max_threads:
            logger.warning(
                f"max_workers ({config_max_workers}) is greater than the recommended maximum ({max_threads}). "
                "This may cause performance issues, therefore, it will be capped."
            )
            max_workers = max_threads
        else:
            max_workers = config_max_workers
    else:
        # Auto-detect optimal worker count for I/O-bound operations
        max_workers = min(package_count, MAX_WORKER_LIMIT, max_threads)

    return WorkerConfig(
        max_workers=max_workers,
        cpu_count=cpu_count,
        package_count=package_count,
    )


# =============================================================================
# Validation
# =============================================================================


def _validate_download_config(config: Any) -> tuple[str, str]:
    """Validate download configuration and return registry details.

    Args:
        config: Application configuration

    Returns:
        Tuple of (registry, organization)

    Raises:
        ValueError: If required configuration is missing
        ConfigurationError: If configuration is invalid
    """
    if not config.download_remote_packages:
        return "", ""

    if not config.registry:
        raise ValueError("Registry URL is required when download_remote_packages is enabled")

    if not config.organization:
        raise ValueError("Organization is required when download_remote_packages is enabled")

    # Type narrowing validation
    if config.registry is None:
        raise ConfigurationError("Registry URL is required for package downloads")
    if config.organization is None:
        raise ConfigurationError("Organization is required for package downloads")

    return config.registry, config.organization


def _validate_authentication(
    registry: str,
    organization: str,
    context: AppContext,
    is_debug: bool,
) -> None:
    """Validate registry authentication before downloads.

    Args:
        registry: Container registry URL
        organization: Organization in the registry
        context: Application context
        is_debug: Whether debug mode is enabled

    Raises:
        AuthenticationError: If authentication fails
    """
    logger = context.get_logger(__name__)

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


# =============================================================================
# Download Execution
# =============================================================================


def _download_single_package_safe(
    package: PackageConfig,
    registry: str,
    organization: str,
    output_dir: Path,
    context: AppContext,
) -> DownloadResult:
    """Download SBOM for a single package with error handling.

    Args:
        package: Package to download
        registry: Container registry URL
        organization: Organization in the registry
        output_dir: Directory for downloads
        context: Application context

    Returns:
        DownloadResult with either sbom_files or error
    """
    try:
        sbom_files = download_package_sbom(
            package=package,
            registry=registry,
            organization=organization,
            output_dir=output_dir,
            context=context,
        )
        return DownloadResult(package=package, sbom_files=sbom_files)
    except Exception as e:
        return DownloadResult(package=package, error=e)


def _process_download_result(
    result: DownloadResult,
    tracker: DownloadTracker,
    logger: Any,
    is_debug: bool,
) -> None:
    """Process a download result and update tracker.

    Args:
        result: Download result to process
        tracker: Tracker to update
        logger: Logger instance
        is_debug: Whether debug mode is enabled
    """
    if result.error:
        error = result.error
        error_type = type(error).__name__

        logger.error(
            "Package download failed",
            package=result.package.name,
            version=result.package.version,
            error_type=error_type,
            error=str(error),
        )

        if is_debug:
            error_msg = error.message if hasattr(error, "message") else str(error)
            console.print(f"  [red]✗[/red] {result.package.name}-{result.package.version}: [{error_type}] {error_msg}")

        tracker.add_error(result.package, error)
    else:
        tracker.add_success(result.sbom_files)

        if is_debug:
            for sbom_file in result.sbom_files:
                console.print(f"  [green]✓[/green] Downloaded: {sbom_file.name}")


def _execute_parallel_downloads(
    packages: list[PackageConfig],
    registry: str,
    organization: str,
    output_dir: Path,
    context: AppContext,
    worker_config: WorkerConfig,
    is_debug: bool,
) -> DownloadTracker:
    """Execute parallel package downloads with progress tracking.

    Args:
        packages: List of packages to download
        registry: Container registry URL
        organization: Organization in the registry
        output_dir: Directory for downloads
        context: Application context
        worker_config: Worker configuration
        is_debug: Whether debug mode is enabled

    Returns:
        DownloadTracker with results and errors
    """
    logger = context.get_logger(__name__)
    tracker = DownloadTracker()

    with ThreadPoolExecutor(max_workers=worker_config.max_workers) as executor:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=not is_debug,
        ) as progress:
            task_id = progress.add_task(
                f"[cyan]Downloading {len(packages)} packages...",
                total=len(packages),
            )

            # Submit all download tasks
            future_to_package = {
                executor.submit(
                    _download_single_package_safe,
                    package,
                    registry,
                    organization,
                    output_dir,
                    context,
                ): package
                for package in packages
            }

            # Process completed downloads
            for future in as_completed(future_to_package):
                result = future.result()
                _process_download_result(result, tracker, logger, is_debug)
                progress.update(task_id, advance=1)

    return tracker


# =============================================================================
# Public API
# =============================================================================


def validate_registry_authentication(registry: str, organization: str, context: AppContext) -> None:
    """Validate registry authentication before attempting any downloads.

    Makes a lightweight API call to verify that the registry credentials are valid.
    This prevents wasting time and resources attempting downloads that will fail
    due to authentication issues.

    Uses the `uds zarf package list` command to check registry access.

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
    registry_ref = f"{DEFAULT_PROTOCOL}://{registry}/{organization}"

    if is_debug:
        logger.debug(
            "Validating registry authentication",
            registry=registry,
            organization=organization,
        )

    # Build the validation command
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
            status_code = error_handler.extract_http_status_code(output)
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

        # If it's not an authentication error, log warning but continue
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

    Args:
        output_dir: Directory to store downloaded SBOM reports
        context: Application context with config and services

    Returns:
        List of paths to downloaded SBOM JSON files

    Raises:
        ValueError: If required configuration is missing
        RuntimeError: If download fails for any package
    """
    config = context.config
    logger = context.get_logger(__name__)

    # Early exit if downloads are disabled
    if not config.download_remote_packages:
        logger.debug("download_remote_packages is False, skipping package downloads")
        return []

    # Validate configuration
    registry, organization = _validate_download_config(config)

    if not config.packages:
        logger.warning("No packages configured for download")
        return []

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Calculate optimal workers
    worker_config = _calculate_optimal_workers(
        config_max_workers=config.max_workers,
        package_count=len(config.packages),
        logger=logger,
    )

    is_debug = config.log_level == "DEBUG"

    if is_debug:
        console.print(f"\n[cyan]Downloading SBOM reports for {len(config.packages)} packages...")
        console.print(f"[cyan]Using {worker_config.max_workers} concurrent workers[/cyan]\n")

    # Validate authentication before downloads
    _validate_authentication(registry, organization, context, is_debug)

    # Execute parallel downloads
    tracker = _execute_parallel_downloads(
        packages=config.packages,
        registry=registry,
        organization=organization,
        output_dir=output_dir,
        context=context,
        worker_config=worker_config,
        is_debug=is_debug,
    )

    if is_debug:
        console.print(
            f"\n[green]✓[/green] Downloaded {len(tracker.downloaded_files)} SBOM files "
            f"from {len(config.packages)} packages\n"
        )

    return tracker.downloaded_files


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
    report for a specific package.

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
    uds_log_level = UDS_LOG_LEVEL_MAP.get(config.log_level, "info")

    # Construct package reference
    package_ref = f"{registry}/{organization}/{package.name}:{package.version}"

    # Build the command
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
            error_output=output,
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
