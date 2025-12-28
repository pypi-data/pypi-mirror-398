"""Parallel scanning utilities using ThreadPoolExecutor for concurrent vulnerability scans.

This module provides parallel execution of vulnerability scans (Grype/Trivy) to significantly
reduce total scanning time when processing multiple SBOM files or reports.

Key features:
- Thread-safe scanning with configurable worker count
- Automatic CPU detection for optimal parallelism
- Progress tracking for concurrent operations
- Comprehensive error handling and logging
- Compatible with both Grype and Trivy scanners
"""

import os
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TextColumn, TimeElapsedColumn

from ..core.exceptions import ScannerExecutionError

console = Console()


def get_optimal_workers(max_workers: int | None = None) -> int:
    """Determine optimal number of worker threads.

    Args:
        max_workers: User-specified maximum workers, or None for auto-detection

    Returns:
        Optimal number of workers (bounded between 1 and CPU count)

    Examples:
        >>> get_optimal_workers(None)  # Auto-detect
        4  # On 4-core system
        >>> get_optimal_workers(8)  # User override
        8
        >>> get_optimal_workers(0)  # Invalid, returns 1
        1
    """
    if max_workers is not None and max_workers > 0:
        return max_workers

    # Auto-detect based on CPU count
    cpu_count = os.cpu_count() or 1
    # Use CPU count but cap at reasonable maximum for I/O-bound operations
    return min(cpu_count, 8)


# =============================================================================
# Result Collection Pattern
# =============================================================================


@dataclass
class ScanResultCollector:
    """Collects scan results and errors in a structured way.

    This class provides a clean interface for collecting results from parallel
    scan operations, with built-in error tracking and reporting capabilities.
    """

    results: list[tuple[Path, Path]] = field(default_factory=list)
    errors: list[tuple[Path, Exception]] = field(default_factory=list)

    def add_result(self, input_path: Path, output_path: Path) -> None:
        """Add a successful scan result."""
        self.results.append((input_path, output_path))

    def add_error(self, file_path: Path, error: Exception) -> None:
        """Add a scan error."""
        self.errors.append((file_path, error))

    def has_results(self) -> bool:
        """Check if any results were collected."""
        return len(self.results) > 0

    def has_errors(self) -> bool:
        """Check if any errors occurred."""
        return len(self.errors) > 0

    def raise_if_all_failed(self) -> None:
        """Raise exception if all scans failed (no results at all).

        Raises:
            ScannerExecutionError: If all scans failed
        """
        if self.has_errors() and not self.has_results():
            error_details = "\n".join([f"  - {path.name}: {str(exc)}" for path, exc in self.errors])
            raise ScannerExecutionError(
                scanner="parallel_scanner",
                command=["parallel_scan"],
                stderr=f"Failed to scan all {len(self.errors)} files:\n{error_details}",
            )

    def log_partial_failure_if_needed(self) -> None:
        """Log warning if some files failed but we have partial results."""
        if self.has_errors() and self.has_results():
            logger = structlog.get_logger(__name__)
            logger.warning(
                "Some files failed to scan, continuing with partial results",
                failed_count=len(self.errors),
                success_count=len(self.results),
                failed_files=[path.name for path, _ in self.errors],
            )


@dataclass
class ItemResultCollector:
    """Collects results and errors for generic item processing."""

    results: list[Any] = field(default_factory=list)
    errors: list[tuple[Any, Exception]] = field(default_factory=list)

    def add_result(self, result: Any) -> None:
        """Add a successful processing result."""
        self.results.append(result)

    def add_error(self, item: Any, error: Exception) -> None:
        """Add a processing error."""
        self.errors.append((item, error))

    def has_results(self) -> bool:
        """Check if any results were collected."""
        return len(self.results) > 0

    def has_errors(self) -> bool:
        """Check if any errors occurred."""
        return len(self.errors) > 0

    def raise_if_errors(self) -> None:
        """Raise exception if any processing failed.

        Raises:
            Exception: If any items failed to process
        """
        if self.has_errors():
            error_details = "\n".join([f"  - {str(exc)}" for _, exc in self.errors])
            raise Exception(f"Failed to process {len(self.errors)} items:\n{error_details}")


# =============================================================================
# Progress Reporting
# =============================================================================


def _report_scan_results(
    total_files: int,
    collector: ScanResultCollector,
    verbose: bool,
) -> None:
    """Report scan results to console.

    Args:
        total_files: Total number of files scanned
        collector: Result collector with results and errors
        verbose: Enable detailed logging
    """
    if not verbose:
        return

    if collector.has_results():
        console.print(
            f"  [green]✓[/green] Successfully scanned {len(collector.results)}/{total_files} files",
            style="dim",
        )

    if collector.has_errors():
        console.print(
            f"  [yellow]⚠[/yellow] Failed to scan {len(collector.errors)}/{total_files} files "
            "(continuing with partial results)",
            style="yellow",
        )
        for path, exc in collector.errors:
            console.print(f"    - {path.name}: {exc}", style="dim")


def _report_item_results(
    total_items: int,
    collector: ItemResultCollector,
    verbose: bool,
) -> None:
    """Report item processing results to console.

    Args:
        total_items: Total number of items processed
        collector: Result collector with results and errors
        verbose: Enable detailed logging
    """
    if not verbose:
        return

    if collector.has_results():
        console.print(
            f"  [green]✓[/green] Successfully processed {len(collector.results)}/{total_items} items",
            style="dim",
        )

    if collector.has_errors():
        console.print(
            f"  [red]✗[/red] Failed to process {len(collector.errors)}/{total_items} items",
            style="bold red",
        )


# =============================================================================
# Single Item Processing (Optimization for single-item case)
# =============================================================================


def _scan_single_file(
    file: Path,
    scan_func: Callable[[Path, Path, bool], Path],
    output_dir: Path,
    verbose: bool,
    operation_name: str,
) -> list[tuple[Path, Path]]:
    """Process a single file without parallelization overhead.

    Args:
        file: File to scan
        scan_func: Scanner function to execute
        output_dir: Directory for output
        verbose: Verbose logging flag
        operation_name: Description for logging

    Returns:
        List containing single (input_path, output_path) tuple
    """
    if verbose:
        console.print(
            f"[dim cyan]{operation_name}[/dim cyan] single file with 1 worker...",
            style="dim",
        )

    result = scan_func(file, output_dir, verbose)
    return [(file, result)]


def _process_single_item(
    item: Any,
    process_func: Callable[[Any, bool], Any],
    verbose: bool,
    operation_name: str,
) -> list[Any]:
    """Process a single item without parallelization overhead.

    Args:
        item: Item to process
        process_func: Function to process the item
        verbose: Verbose logging flag
        operation_name: Description for logging

    Returns:
        List containing single processed result
    """
    if verbose:
        console.print(
            f"[dim cyan]{operation_name}[/dim cyan] single item with 1 worker...",
            style="dim",
        )

    return [process_func(item, verbose)]


# =============================================================================
# Core Scanning Functions
# =============================================================================


def scan_file_with_progress(
    scan_func: Callable[[Path, Path, bool], Path],
    file_path: Path,
    output_dir: Path,
    verbose: bool,
    progress: Progress,
    task_id: TaskID,
) -> tuple[Path, Path]:
    """Scan a single file and update progress.

    Args:
        scan_func: Scanner function to execute
        file_path: Path to file to scan
        output_dir: Directory for output
        verbose: Verbose logging flag
        progress: Rich progress instance
        task_id: Task ID for progress updates

    Returns:
        Tuple of (input_path, output_path)

    Raises:
        ScannerExecutionError: If scanning fails
    """
    try:
        result_path = scan_func(file_path, output_dir, verbose)
        progress.update(task_id, advance=1)
        return (file_path, result_path)
    except Exception as e:
        progress.update(task_id, advance=1)
        # Extract function name for error reporting
        func_name = getattr(scan_func, "__name__", str(scan_func))
        raise ScannerExecutionError(
            scanner="parallel_scanner",
            command=[func_name],
            stderr=str(e),
        ) from e


def _execute_parallel_scans(
    files: list[Path],
    scan_func: Callable[[Path, Path, bool], Path],
    output_dir: Path,
    verbose: bool,
    workers: int,
    operation_name: str,
) -> ScanResultCollector:
    """Execute parallel file scans with progress tracking.

    Args:
        files: List of files to scan
        scan_func: Scanner function to execute
        output_dir: Directory for output
        verbose: Verbose logging flag
        workers: Number of worker threads
        operation_name: Description for progress display

    Returns:
        ScanResultCollector with results and errors
    """
    collector = ScanResultCollector()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task_id = progress.add_task(f"[cyan]{operation_name}...", total=len(files))

        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all tasks
            future_to_file: dict[Future[tuple[Path, Path]], Path] = {
                executor.submit(
                    scan_file_with_progress,
                    scan_func,
                    file_path,
                    output_dir,
                    verbose,
                    progress,
                    task_id,
                ): file_path
                for file_path in files
            }

            # Collect results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result_tuple = future.result()
                    collector.add_result(*result_tuple)
                except Exception as exc:
                    collector.add_error(file_path, exc)
                    if verbose:
                        console.print(
                            f"[red]Error[/red] scanning {file_path.name}: {exc}",
                            style="bold red",
                        )

    return collector


def _execute_parallel_items(
    items: list[Any],
    process_func: Callable[[Any, bool], Any],
    verbose: bool,
    workers: int,
    operation_name: str,
) -> ItemResultCollector:
    """Execute parallel item processing with progress tracking.

    Args:
        items: List of items to process
        process_func: Function to process each item
        verbose: Verbose logging flag
        workers: Number of worker threads
        operation_name: Description for progress display

    Returns:
        ItemResultCollector with results and errors
    """
    collector = ItemResultCollector()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task_id = progress.add_task(f"[cyan]{operation_name}...", total=len(items))

        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all tasks
            future_to_item: dict[Future[Any], Any] = {
                executor.submit(process_func, item, verbose): item for item in items
            }

            # Collect results as they complete
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    collector.add_result(result)
                    progress.update(task_id, advance=1)
                except Exception as exc:
                    collector.add_error(item, exc)
                    progress.update(task_id, advance=1)
                    if verbose:
                        console.print(
                            f"[red]Error[/red] processing item: {exc}",
                            style="bold red",
                        )

    return collector


# =============================================================================
# Public API
# =============================================================================


def parallel_scan_files(
    files: list[Path],
    scan_func: Callable[[Path, Path, bool], Path],
    output_dir: Path,
    verbose: bool = False,
    max_workers: int | None = None,
    operation_name: str = "Scanning",
) -> list[tuple[Path, Path]]:
    """Execute parallel scans on multiple files using ThreadPoolExecutor.

    This function distributes file scanning across multiple worker threads,
    significantly reducing total processing time for large batches of files.

    Args:
        files: List of file paths to scan
        scan_func: Scanner function (e.g., scan_with_trivy, convert_to_cyclonedx)
        output_dir: Directory to store scan results
        verbose: Enable detailed logging
        max_workers: Maximum concurrent workers (None = auto-detect)
        operation_name: Description for progress display

    Returns:
        List of (input_path, output_path) tuples for successful scans

    Raises:
        ScannerExecutionError: If all scans fail

    Examples:
        >>> from pathlib import Path
        >>> files = [Path("sbom1.json"), Path("sbom2.json")]
        >>> results = parallel_scan_files(
        ...     files=files,
        ...     scan_func=scan_with_trivy,
        ...     output_dir=Path("./output"),
        ...     max_workers=4
        ... )
        >>> len(results)
        2
    """
    # Early exit for empty input
    if not files:
        return []

    # Single file optimization
    if len(files) == 1:
        return _scan_single_file(files[0], scan_func, output_dir, verbose, operation_name)

    # Multiple files - use parallel execution
    workers = get_optimal_workers(max_workers)

    if verbose:
        console.print(
            f"[dim cyan]{operation_name}[/dim cyan] {len(files)} files with {workers} workers...",
            style="dim",
        )

    # Execute parallel scans
    collector = _execute_parallel_scans(
        files=files,
        scan_func=scan_func,
        output_dir=output_dir,
        verbose=verbose,
        workers=workers,
        operation_name=operation_name,
    )

    # Report results
    _report_scan_results(len(files), collector, verbose)

    # Raise exception if all scans failed
    collector.raise_if_all_failed()

    # Log warning for partial failures
    collector.log_partial_failure_if_needed()

    return collector.results


def parallel_process_items(
    items: list[Any],
    process_func: Callable[[Any, bool], Any],
    verbose: bool = False,
    max_workers: int | None = None,
    operation_name: str = "Processing",
) -> list[Any]:
    """Generic parallel processing for any items with a processing function.

    This is a more flexible version of parallel_scan_files that works with
    any processing function and item type.

    Args:
        items: List of items to process
        process_func: Function to process each item (takes item and verbose flag)
        verbose: Enable detailed logging
        max_workers: Maximum concurrent workers (None = auto-detect)
        operation_name: Description for progress display

    Returns:
        List of processed results

    Raises:
        Exception: If any processing fails

    Examples:
        >>> def process_report(report_data, verbose):
        ...     # Process report and return result
        ...     return transformed_data
        >>> results = parallel_process_items(
        ...     items=report_list,
        ...     process_func=process_report,
        ...     max_workers=4
        ... )
    """
    # Early exit for empty input
    if not items:
        return []

    # Single item optimization
    if len(items) == 1:
        return _process_single_item(items[0], process_func, verbose, operation_name)

    # Multiple items - use parallel execution
    workers = get_optimal_workers(max_workers)

    if verbose:
        console.print(
            f"[dim cyan]{operation_name}[/dim cyan] {len(items)} items with {workers} workers...",
            style="dim",
        )

    # Execute parallel processing
    collector = _execute_parallel_items(
        items=items,
        process_func=process_func,
        verbose=verbose,
        workers=workers,
        operation_name=operation_name,
    )

    # Report results
    _report_item_results(len(items), collector, verbose)

    # Raise exception if any processing failed
    collector.raise_if_errors()

    return collector.results
