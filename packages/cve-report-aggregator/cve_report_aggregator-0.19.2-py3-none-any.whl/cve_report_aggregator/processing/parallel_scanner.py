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
from pathlib import Path
from typing import Any

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
        ScannerExecutionError: If any scan fails

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
    if not files:
        return []

    workers = get_optimal_workers(max_workers)

    # Single file optimization - no need for parallelization
    if len(files) == 1:
        if verbose:
            console.print(
                f"[dim cyan]{operation_name}[/dim cyan] single file with 1 worker...",
                style="dim",
            )
        result = scan_func(files[0], output_dir, verbose)
        return [(files[0], result)]

    # Multiple files - use parallel execution
    if verbose:
        console.print(
            f"[dim cyan]{operation_name}[/dim cyan] {len(files)} files with {workers} workers...",
            style="dim",
        )

    results: list[tuple[Path, Path]] = []
    errors: list[tuple[Path, Exception]] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task_id = progress.add_task(
            f"[cyan]{operation_name}...",
            total=len(files),
        )

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
                    results.append(result_tuple)
                except Exception as exc:
                    errors.append((file_path, exc))
                    if verbose:
                        console.print(
                            f"[red]Error[/red] scanning {file_path.name}: {exc}",
                            style="bold red",
                        )

    # Report results
    if verbose:
        if results:
            console.print(
                f"  [green]✓[/green] Successfully scanned {len(results)}/{len(files)} files",
                style="dim",
            )
        if errors:
            console.print(
                f"  [yellow]⚠[/yellow] Failed to scan {len(errors)}/{len(files)} files (continuing with partial results)",  # noqa: E501
                style="yellow",
            )
            for path, exc in errors:
                console.print(f"    - {path.name}: {exc}", style="dim")

    # Only raise exception if ALL scans failed (no results at all)
    if errors and not results:
        error_details = "\n".join([f"  - {path.name}: {str(exc)}" for path, exc in errors])
        raise ScannerExecutionError(
            scanner="parallel_scanner",
            command=["parallel_scan"],
            stderr=f"Failed to scan all {len(errors)} files:\n{error_details}",
        )

    # Log warning if some files failed but we have partial results
    if errors and results:
        import structlog

        logger = structlog.get_logger(__name__)
        logger.warning(
            "Some files failed to scan, continuing with partial results",
            failed_count=len(errors),
            success_count=len(results),
            failed_files=[path.name for path, _ in errors],
        )

    return results


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
    if not items:
        return []

    workers = get_optimal_workers(max_workers)

    # Single item optimization
    if len(items) == 1:
        if verbose:
            console.print(
                f"[dim cyan]{operation_name}[/dim cyan] single item with 1 worker...",
                style="dim",
            )
        return [process_func(items[0], verbose)]

    # Multiple items - use parallel execution
    if verbose:
        console.print(
            f"[dim cyan]{operation_name}[/dim cyan] {len(items)} items with {workers} workers...",
            style="dim",
        )

    results: list[Any] = []
    errors: list[tuple[Any, Exception]] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task_id = progress.add_task(
            f"[cyan]{operation_name}...",
            total=len(items),
        )

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
                    results.append(result)
                    progress.update(task_id, advance=1)
                except Exception as exc:
                    errors.append((item, exc))
                    progress.update(task_id, advance=1)
                    if verbose:
                        console.print(
                            f"[red]Error[/red] processing item: {exc}",
                            style="bold red",
                        )

    # Report results
    if verbose:
        if results:
            console.print(
                f"  [green]✓[/green] Successfully processed {len(results)}/{len(items)} items",
                style="dim",
            )
        if errors:
            console.print(
                f"  [red]✗[/red] Failed to process {len(errors)}/{len(items)} items",
                style="bold red",
            )

    # Raise exception if any processing failed
    if errors:
        error_details = "\n".join([f"  - {str(exc)}" for _, exc in errors])
        raise Exception(f"Failed to process {len(errors)} items:\n{error_details}")

    return results
