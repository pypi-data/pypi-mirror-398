"""Scanner integration for Grype and Trivy vulnerability scanners."""

import asyncio
import json
import tempfile
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import aiofiles
import aiofiles.os
from rich.console import Console

from ..core.constants import FIELD_ARTIFACTS, FIELD_DESCRIPTOR, FIELD_MATCHES, FIELD_SCANNER, FIELD_SOURCE_FILE
from ..core.exceptions import ReportLoadError
from ..core.json_utils import load_json_report
from ..core.models import ScannerType
from .parallel_scanner import parallel_scan_files
from .scanner_tools import convert_to_cyclonedx, scan_sbom_with_grype, scan_with_trivy

console = Console()


# =============================================================================
# File Classification Types
# =============================================================================


@dataclass
class ClassifiedFiles:
    """Result of classifying JSON files for Grype processing.

    Attributes:
        sbom_files: List of SBOM file paths to be scanned
        grype_reports: Cached Grype report data (path -> parsed JSON)
        skipped_files: Files that were skipped with reasons
    """

    sbom_files: list[Path] = field(default_factory=list)
    grype_reports: dict[Path, dict[str, Any]] = field(default_factory=dict)
    skipped_files: list[tuple[Path, str]] = field(default_factory=list)

    def has_sbom_files(self) -> bool:
        """Check if any SBOM files were found."""
        return len(self.sbom_files) > 0

    def has_grype_reports(self) -> bool:
        """Check if any Grype reports were found."""
        return len(self.grype_reports) > 0


# =============================================================================
# File Classification
# =============================================================================


def _is_grype_report(data: dict[str, Any]) -> bool:
    """Check if data is a Grype report."""
    return bool(data.get(FIELD_MATCHES))


def _is_sbom_file(data: dict[str, Any]) -> bool:
    """Check if data is a Syft SBOM."""
    return bool(data.get(FIELD_ARTIFACTS) and data.get(FIELD_DESCRIPTOR))


def classify_json_files_for_grype(
    json_files: list[Path],
    verbose: bool = False,
) -> ClassifiedFiles:
    """Classify JSON files into SBOM files and Grype reports.

    Also caches Grype report data to avoid redundant I/O.

    Args:
        json_files: List of JSON file paths to classify
        verbose: Enable detailed logging

    Returns:
        ClassifiedFiles with categorized files and cached data
    """
    classified = ClassifiedFiles()

    for file_path in json_files:
        # Skip CycloneDX intermediate files
        if ".cdx." in file_path.name:
            continue

        try:
            data = load_json_report(file_path)

            if _is_grype_report(data):
                classified.grype_reports[file_path] = data
            elif _is_sbom_file(data):
                classified.sbom_files.append(file_path)
            else:
                classified.skipped_files.append((file_path, "unknown format"))
                if verbose:
                    console.print(
                        f"[yellow]⊘[/yellow] Skipped (unknown format): {file_path.name}",
                        style="dim",
                    )
        except Exception as e:
            classified.skipped_files.append((file_path, str(e)))
            if verbose:
                console.print(
                    f"[yellow]⊘[/yellow] Skipped {file_path.name}: {e}",
                    style="dim",
                )

    return classified


# =============================================================================
# Report Loading
# =============================================================================


def load_cached_grype_reports(
    report_cache: dict[Path, dict[str, Any]],
    reports_dir: Path,
    verbose: bool = False,
) -> list[dict[str, Any]]:
    """Load cached Grype reports with metadata.

    Args:
        report_cache: Dictionary of cached report data (path -> parsed JSON)
        reports_dir: Base directory for relative paths
        verbose: Enable detailed logging

    Returns:
        List of Grype report dictionaries with source metadata
    """
    reports: list[dict[str, Any]] = []

    for report_file, data in report_cache.items():
        data[FIELD_SOURCE_FILE] = str(report_file.relative_to(reports_dir))
        data[FIELD_SCANNER] = "grype"
        reports.append(data)

        if verbose:
            match_count = len(data.get(FIELD_MATCHES, []))
            console.print(
                f"[green]✓[/green] Loaded: {report_file.name} ([cyan]{match_count}[/cyan] matches)",
                style="dim",
            )

    return reports


def _load_grype_scan_result(
    sbom_file: Path,
    grype_report_path: Path,
    reports_dir: Path,
    verbose: bool,
) -> dict[str, Any] | None:
    """Load a Grype scan result and add metadata.

    Args:
        sbom_file: Original SBOM file path
        grype_report_path: Path to Grype scan output
        reports_dir: Base directory for relative paths
        verbose: Enable detailed logging

    Returns:
        Report dictionary or None if no vulnerabilities found
    """
    grype_data = load_json_report(grype_report_path)

    # Only include reports with vulnerability matches
    if not grype_data.get(FIELD_MATCHES):
        if verbose:
            console.print(
                f"[yellow]⊘[/yellow] Skipped {sbom_file.name}: No vulnerabilities found",
                style="dim",
            )
        return None

    grype_data[FIELD_SOURCE_FILE] = str(sbom_file.relative_to(reports_dir))
    grype_data[FIELD_SCANNER] = "grype"
    return grype_data


# =============================================================================
# SBOM Scanning
# =============================================================================


def scan_sboms_with_grype(
    sbom_files: list[Path],
    reports_dir: Path,
    verbose: bool = False,
    max_workers: int | None = None,
) -> list[dict[str, Any]]:
    """Scan SBOM files with Grype in parallel.

    Args:
        sbom_files: List of SBOM file paths to scan
        reports_dir: Base directory for relative paths
        verbose: Enable detailed logging
        max_workers: Maximum concurrent workers (None = auto-detect)

    Returns:
        List of Grype report dictionaries (only non-empty reports)
    """
    if not sbom_files:
        return []

    reports: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)

        if verbose:
            console.print(
                f"[cyan]Scanning {len(sbom_files)} SBOM files with Grype...[/cyan]",
                style="dim",
            )

        try:
            # Scan SBOMs with Grype in parallel
            grype_results = parallel_scan_files(
                files=sbom_files,
                scan_func=scan_sbom_with_grype,
                output_dir=output_dir,
                verbose=verbose,
                max_workers=max_workers,
                operation_name="Scanning SBOMs with Grype",
            )

            # Load results and filter empty reports
            for sbom_file, grype_report_path in grype_results:
                try:
                    report_data = _load_grype_scan_result(sbom_file, grype_report_path, reports_dir, verbose)
                    if report_data:
                        reports.append(report_data)
                except Exception as e:
                    if verbose:
                        console.print(
                            f"[red]Error[/red] loading Grype report for {sbom_file.name}: {e}",
                            style="bold red",
                        )

        except Exception as e:
            # Handle scanning errors gracefully
            if verbose:
                console.print(
                    f"[red]Error[/red] scanning SBOMs with Grype: {e}",
                    style="bold red",
                )

    return reports


def _should_skip_empty_source_files(source_files: list[Path]) -> bool:
    """Check if source files list is empty.

    Args:
        source_files: List of source file paths

    Returns:
        True if source files list is empty, False otherwise
    """
    return not source_files


def _log_conversion_progress(file_count: int, file_type_label: str, verbose: bool) -> None:
    """Log conversion progress message if verbose mode is enabled.

    Args:
        file_count: Number of files being converted
        file_type_label: Label describing file type (e.g., "SBOMs", "Grype reports")
        verbose: Whether to print the message
    """
    if verbose:
        console.print(
            f"[cyan]Converting {file_count} {file_type_label} to CycloneDX in parallel...[/cyan]",
            style="dim",
        )


def _log_scanning_progress(file_count: int, verbose: bool) -> None:
    """Log scanning progress message if verbose mode is enabled.

    Args:
        file_count: Number of files being scanned
        verbose: Whether to print the message
    """
    if verbose:
        console.print(
            f"[cyan]Scanning {file_count} CycloneDX files with Trivy in parallel...[/cyan]",
            style="dim",
        )


def _convert_files_to_cyclonedx(
    source_files: list[Path],
    temp_path: Path,
    verbose: bool,
    max_workers: int | None,
    file_type_label: str,
) -> list[tuple[Path, Path]]:
    """Convert source files to CycloneDX format in parallel.

    Args:
        source_files: List of source file paths to convert
        temp_path: Temporary directory for intermediate files
        verbose: Enable detailed logging
        max_workers: Maximum concurrent workers (None = auto-detect)
        file_type_label: Label for logging (e.g., "SBOMs", "Grype reports")

    Returns:
        List of tuples containing (source_file_path, cyclonedx_file_path)
    """
    return parallel_scan_files(
        files=source_files,
        scan_func=convert_to_cyclonedx,
        output_dir=temp_path,
        verbose=verbose,
        max_workers=max_workers,
        operation_name=f"Converting {file_type_label} to CycloneDX",
    )


def _extract_cyclonedx_files(cdx_results: list[tuple[Path, Path]]) -> list[Path]:
    """Extract CycloneDX file paths from conversion results.

    Args:
        cdx_results: List of tuples containing (source_path, cdx_path)

    Returns:
        List of CycloneDX file paths
    """
    return [cdx_path for _, cdx_path in cdx_results]


def _scan_cyclonedx_files(
    cdx_files: list[Path],
    temp_path: Path,
    verbose: bool,
    max_workers: int | None,
) -> list[tuple[Path, Path]]:
    """Scan CycloneDX files with Trivy in parallel.

    Args:
        cdx_files: List of CycloneDX file paths to scan
        temp_path: Temporary directory for output files
        verbose: Enable detailed logging
        max_workers: Maximum concurrent workers (None = auto-detect)

    Returns:
        List of tuples containing (cdx_file_path, trivy_report_path)
    """
    return parallel_scan_files(
        files=cdx_files,
        scan_func=scan_with_trivy,
        output_dir=temp_path,
        verbose=verbose,
        max_workers=max_workers,
        operation_name="Scanning CycloneDX with Trivy",
    )


def _build_cyclonedx_to_source_mapping(cdx_results: list[tuple[Path, Path]]) -> dict[Path, Path]:
    """Build mapping from CycloneDX files to original source files.

    Args:
        cdx_results: List of tuples containing (source_path, cdx_path)

    Returns:
        Dictionary mapping CycloneDX file paths to source file paths
    """
    return {cdx_path: source_path for source_path, cdx_path in cdx_results}


def _load_trivy_reports_with_metadata(
    trivy_scan_results: list[tuple[Path, Path]],
    cdx_to_source: dict[Path, Path],
    reports_dir: Path,
) -> list[dict[str, Any]]:
    """Load Trivy reports and add source metadata.

    Args:
        trivy_scan_results: List of tuples containing (cdx_path, trivy_report_path)
        cdx_to_source: Mapping from CycloneDX files to original source files
        reports_dir: Base reports directory for calculating relative paths

    Returns:
        List of Trivy report dictionaries with source metadata
    """
    trivy_reports: list[dict[str, Any]] = []

    for cdx_path, trivy_report_path in trivy_scan_results:
        original_file = cdx_to_source.get(cdx_path)
        if original_file:
            trivy_data = load_json_report(trivy_report_path)
            trivy_data[FIELD_SOURCE_FILE] = str(original_file.relative_to(reports_dir))
            trivy_data[FIELD_SCANNER] = "trivy"
            trivy_reports.append(trivy_data)

    return trivy_reports


def _convert_and_scan_with_trivy(
    source_files: list[Path],
    reports_dir: Path,
    temp_path: Path,
    verbose: bool,
    max_workers: int | None,
    file_type_label: str,
) -> tuple[list[dict[str, Any]], list[Path]]:
    """Convert files to CycloneDX and scan with Trivy.

    This helper function handles the common pattern of:
    1. Converting source files to CycloneDX format in parallel
    2. Scanning the CycloneDX files with Trivy in parallel
    3. Loading and returning the Trivy reports with source metadata

    Args:
        source_files: List of source file paths to convert and scan
        reports_dir: Base reports directory for relative path calculation
        temp_path: Temporary directory for intermediate files
        verbose: Enable detailed logging
        max_workers: Maximum concurrent workers (None = auto-detect)
        file_type_label: Label for logging (e.g., "SBOMs", "Grype reports")

    Returns:
        Tuple containing:
        - List of Trivy report dictionaries with source metadata
        - List of generated CycloneDX file paths
    """
    # Early return if no source files
    if _should_skip_empty_source_files(source_files):
        return [], []

    # Log conversion progress
    _log_conversion_progress(len(source_files), file_type_label, verbose)

    # Convert to CycloneDX format in parallel
    cdx_results = _convert_files_to_cyclonedx(
        source_files=source_files,
        temp_path=temp_path,
        verbose=verbose,
        max_workers=max_workers,
        file_type_label=file_type_label,
    )

    # Extract CycloneDX files from results
    cdx_files = _extract_cyclonedx_files(cdx_results)
    if not cdx_files:
        return [], []

    # Log scanning progress
    _log_scanning_progress(len(cdx_files), verbose)

    # Scan CycloneDX files with Trivy in parallel
    trivy_scan_results = _scan_cyclonedx_files(
        cdx_files=cdx_files,
        temp_path=temp_path,
        verbose=verbose,
        max_workers=max_workers,
    )

    # Build mapping from CycloneDX files to original source files
    cdx_to_source = _build_cyclonedx_to_source_mapping(cdx_results)

    # Load Trivy reports and add metadata
    trivy_reports = _load_trivy_reports_with_metadata(
        trivy_scan_results=trivy_scan_results,
        cdx_to_source=cdx_to_source,
        reports_dir=reports_dir,
    )

    # Return both reports and CDX files for persistence tracking
    return trivy_reports, cdx_files


async def _save_trivy_report(
    cdx_file: Path,
    trivy_dir: Path,
) -> Path | None:
    """Asynchronously save a single CycloneDX file to persistent storage.

    Reads the source file and writes it to the destination directory
    using async file I/O for non-blocking operation.

    Args:
        cdx_file: CycloneDX file path to persist
        trivy_dir: Destination directory for saved reports

    Returns:
        Path to the saved file, or None if save failed
    """
    if not cdx_file.exists():
        return None

    dest_file = trivy_dir / cdx_file.name
    try:
        # Read source file asynchronously
        async with aiofiles.open(cdx_file, mode="rb") as src:
            content = await src.read()

        # Write to destination asynchronously
        async with aiofiles.open(dest_file, mode="wb") as dst:
            await dst.write(content)

        return dest_file
    except Exception:
        return None


async def save_trivy_reports(
    cdx_files: list[Path],
    persist_cyclonedx_dir: Path,
    verbose: bool = False,
) -> AsyncIterator[Path]:
    """Async generator that saves CycloneDX files and yields each saved path.

    Creates a 'trivy' subdirectory in persist_cyclonedx_dir and saves
    CycloneDX files to it one at a time, yielding each successfully saved path.
    This allows for streaming progress updates and memory-efficient processing.

    Args:
        cdx_files: List of CycloneDX file paths to persist
        persist_cyclonedx_dir: Base directory for persistent storage
        verbose: Enable detailed logging

    Yields:
        Path to each successfully saved file

    Example:
        >>> async for saved_path in save_trivy_reports(files, output_dir):
        ...     print(f"Saved: {saved_path}")
    """
    if not cdx_files:
        return

    # Create trivy subdirectory
    trivy_dir = persist_cyclonedx_dir / "trivy"
    await aiofiles.os.makedirs(trivy_dir, exist_ok=True)

    for cdx_file in cdx_files:
        if not cdx_file.exists():
            if verbose:
                console.print(
                    f"[yellow]⊘[/yellow] Skipped (file not found): {cdx_file.name}",
                    style="dim",
                )
            continue

        saved_path = await _save_trivy_report(cdx_file, trivy_dir)

        if saved_path:
            if verbose:
                console.print(
                    f"[green]✓[/green] Saved: {cdx_file.name} -> {saved_path.relative_to(persist_cyclonedx_dir)}",
                    style="dim",
                )
            yield saved_path
        elif verbose:
            console.print(
                f"[red]Error[/red] saving {cdx_file.name}",
                style="bold red",
            )


def _get_pipeline_processor():
    """Lazy import of pipeline to avoid circular dependency at module load time."""
    from .pipeline import parallel_pipeline_processing

    return parallel_pipeline_processing


def process_grype_reports(
    reports_dir: Path,
    verbose: bool = False,
    max_workers: int | None = None,
) -> list[dict[str, Any]]:
    """Process reports for Grype scanning with parallel execution.

    Handles two scenarios:
    1. Existing Grype reports - loaded directly without re-scanning
    2. SBOM files - scanned with Grype only (parallel execution)

    Args:
        reports_dir: Directory containing SBOM files and/or Grype reports
        verbose: Enable detailed logging
        max_workers: Maximum concurrent workers for SBOM processing (None = auto-detect)

    Returns:
        List of Grype report dictionaries

    Raises:
        ReportLoadError: If no JSON files found in directory
    """
    # Find all JSON files recursively
    json_files: list[Path] = list(reports_dir.rglob("*.json"))
    if not json_files:
        error_msg = f"No JSON files found in '{reports_dir}'"
        console.print(f"[red]Error:[/red] {error_msg}", style="bold red")
        raise ReportLoadError(str(reports_dir), "No JSON files found in directory")

    # Classify files into SBOMs and Grype reports
    classified = classify_json_files_for_grype(json_files, verbose)

    # Load cached Grype reports
    reports = load_cached_grype_reports(
        report_cache=classified.grype_reports,
        reports_dir=reports_dir,
        verbose=verbose,
    )

    # Scan SBOM files with Grype
    if classified.has_sbom_files():
        sbom_reports = scan_sboms_with_grype(
            sbom_files=classified.sbom_files,
            reports_dir=reports_dir,
            verbose=verbose,
            max_workers=max_workers,
        )
        reports.extend(sbom_reports)

    return reports


def _classify_json_files(
    json_files: list[Path],
    verbose: bool = False,
) -> tuple[list[Path], list[Path]]:
    """Classify JSON files into SBOM files and Grype reports.

    Args:
        json_files: List of JSON file paths to classify
        verbose: Whether to print detailed processing information

    Returns:
        Tuple of (sbom_files, grype_files)
    """
    sbom_files: list[Path] = []
    grype_files: list[Path] = []

    for report_file in json_files:
        # Skip CycloneDX intermediate files
        if ".cdx." in report_file.name:
            if verbose:
                console.print(
                    f"[yellow]⊘[/yellow] Skipped (CycloneDX intermediate file): {report_file.name}",
                    style="dim",
                )
            continue

        try:
            data: dict[str, Any] = load_json_report(report_file)

            if data.get(FIELD_ARTIFACTS) and data.get(FIELD_DESCRIPTOR):
                sbom_files.append(report_file)
            elif data.get(FIELD_MATCHES):
                grype_files.append(report_file)
            elif verbose:
                console.print(
                    f"[yellow]⊘[/yellow] Skipped (unknown format): {report_file.name}",
                    style="dim",
                )
        except json.JSONDecodeError as e:
            console.print(
                f"[red]Error[/red] parsing JSON in {report_file.name}: {e}",
                style="bold red",
            )
        except Exception as e:
            console.print(
                f"[red]Error[/red] processing {report_file.name}: {e}",
                style="bold red",
            )

    return sbom_files, grype_files


def _process_sbom_for_trivy(
    report_file: Path,
    reports_dir: Path,
    temp_path: Path,
    verbose: bool,
) -> tuple[dict[str, Any] | None, Path | None]:
    """Process a single SBOM file for Trivy scanning.

    Converts SBOM to CycloneDX and scans with Trivy.

    Args:
        report_file: Path to SBOM file
        reports_dir: Base directory for relative path calculation
        temp_path: Temporary directory for intermediate files
        verbose: Whether to print detailed processing information

    Returns:
        Tuple of (trivy_report, cdx_file) or (None, None) on error
    """
    if verbose:
        console.print(
            f"[cyan]Converting and scanning SBOM[/cyan] {report_file.name} with Trivy...",
            style="dim",
        )

    try:
        cdx_file = convert_to_cyclonedx(report_file, temp_path, verbose)
        trivy_report_path = scan_with_trivy(cdx_file, temp_path, verbose)
        trivy_data: dict[str, Any] = load_json_report(trivy_report_path)
        trivy_data[FIELD_SOURCE_FILE] = str(report_file.relative_to(reports_dir))
        trivy_data[FIELD_SCANNER] = "trivy"

        if verbose:
            console.print(f"  [green]✓[/green] Scanned: {report_file.name}", style="dim")

        return trivy_data, cdx_file
    except Exception as e:
        console.print(
            f"[red]Error[/red] processing {report_file.name}: {e}",
            style="bold red",
        )
        return None, None


def _persist_trivy_reports_sync(
    generated_cdx_files: list[Path],
    persist_cyclonedx_dir: Path,
    verbose: bool,
) -> None:
    """Persist generated CycloneDX files to storage directory.

    Args:
        generated_cdx_files: List of CycloneDX file paths
        persist_cyclonedx_dir: Directory to persist files to
        verbose: Whether to print detailed processing information
    """
    if verbose:
        trivy_dir = persist_cyclonedx_dir / "trivy"
        console.print(
            f"[cyan]Persisting {len(generated_cdx_files)} Trivy reports to {trivy_dir}/...[/cyan]",
            style="dim",
        )

    async def _persist_reports() -> None:
        async for _ in save_trivy_reports(generated_cdx_files, persist_cyclonedx_dir, verbose):
            pass

    asyncio.run(_persist_reports())


def process_trivy_reports(
    reports_dir: Path,
    verbose: bool = False,
    max_workers: int | None = None,
    persist_cyclonedx_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Process reports for Trivy scanning with parallel execution.

    Handles three scenarios:
    1. Syft SBOM files: Converts to CycloneDX first, then scans with Trivy
    2. Grype reports: Converts to CycloneDX first, then scans with Trivy
    3. CycloneDX files: Scans directly with Trivy

    Args:
        reports_dir: Directory containing JSON reports or SBOM files.
        verbose: Whether to print detailed processing information.
        max_workers: Maximum number of concurrent workers (None = auto-detect).
        persist_cyclonedx_dir: Optional directory to persist Trivy reports to.
            If provided, copies generated .cdx.json files to a 'trivy' subdirectory.

    Returns:
        List of Trivy report dictionaries
    """
    # Validate input directory
    json_files: list[Path] = list(reports_dir.rglob("*.json"))
    if not json_files:
        error_msg = f"No JSON files found in '{reports_dir}'"
        console.print(f"[red]Error:[/red] {error_msg}", style="bold red")
        raise ReportLoadError(str(reports_dir), "No JSON files found in directory")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path: Path = Path(temp_dir)
        trivy_reports: list[dict[str, Any]] = []
        generated_cdx_files: list[Path] = []

        # Step 1: Classify files
        sbom_files, grype_files = _classify_json_files(json_files, verbose)

        # Step 2: Process individual SBOMs that need conversion
        # Note: This handles SBOMs that were already loaded during classification
        # by re-checking the SBOM files list

        # Step 3: Process SBOM files in parallel
        sbom_reports, sbom_cdx_files = _convert_and_scan_with_trivy(
            source_files=sbom_files,
            reports_dir=reports_dir,
            temp_path=temp_path,
            verbose=verbose,
            max_workers=max_workers,
            file_type_label="SBOMs",
        )
        trivy_reports.extend(sbom_reports)
        generated_cdx_files.extend(sbom_cdx_files)

        # Step 4: Process Grype reports in parallel
        grype_converted_reports, grype_cdx_files = _convert_and_scan_with_trivy(
            source_files=grype_files,
            reports_dir=reports_dir,
            temp_path=temp_path,
            verbose=verbose,
            max_workers=max_workers,
            file_type_label="Grype reports",
        )
        trivy_reports.extend(grype_converted_reports)
        generated_cdx_files.extend(grype_cdx_files)

        # Step 5: Persist reports if configured
        if persist_cyclonedx_dir and generated_cdx_files:
            _persist_trivy_reports_sync(generated_cdx_files, persist_cyclonedx_dir, verbose)

        return trivy_reports


def process_both_reports(
    reports_dir: Path,
    verbose: bool = False,
    max_workers: int | None = None,
    persist_cyclonedx_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Process reports using both Grype and Trivy scanners.

    This function runs both scanners on all SBOM files and combines the results.
    It handles:
    1. Existing Grype reports - loaded directly
    2. SBOM files - scanned with both Grype and Trivy
    3. Results from both scanners are combined into a single list

    Args:
        reports_dir: Directory containing SBOM files and/or scan reports
        verbose: Enable detailed logging
        max_workers: Maximum concurrent workers for SBOM processing (None = auto-detect)
        persist_cyclonedx_dir: Optional directory to persist Trivy reports to.
            If provided, copies generated .cdx.json files to a 'trivy' subdirectory.

    Returns:
        Combined list of both Grype and Trivy report dictionaries
    """
    reports: list[dict[str, Any]] = []

    if verbose:
        console.print(
            "[cyan]Running both Grype and Trivy scanners...[/cyan]",
            style="dim",
        )

    # Run Grype scanner
    if verbose:
        console.print(
            "[cyan]Step 1/2: Running Grype scanner...[/cyan]",
            style="dim",
        )
    grype_reports = process_grype_reports(reports_dir, verbose, max_workers)
    reports.extend(grype_reports)

    if verbose:
        console.print(
            f"[green]✓[/green] Grype scanning complete: {len(grype_reports)} reports",
            style="dim",
        )

    # Run Trivy scanner
    if verbose:
        console.print(
            "[cyan]Step 2/2: Running Trivy scanner...[/cyan]",
            style="dim",
        )
    trivy_reports = process_trivy_reports(reports_dir, verbose, max_workers, persist_cyclonedx_dir)
    reports.extend(trivy_reports)

    if verbose:
        console.print(
            f"[green]✓[/green] Trivy scanning complete: {len(trivy_reports)} reports",
            style="dim",
        )
        console.print(
            f"[green]✓[/green] Total reports from both scanners: {len(reports)}",
            style="dim",
        )

    return reports


def load_reports(
    reports_dir: Path,
    scanner: ScannerType = "grype",
    verbose: bool = False,
    max_workers: int | None = None,
    persist_cyclonedx_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Loads all JSON report files from the specified directory with parallel processing.

    Scanner behavior:
    - Grype: Loads existing Grype reports and scans SBOM files with Grype only
    - Trivy: Converts SBOM/Grype reports to CycloneDX, then scans with Trivy only
    - Both: Runs both Grype and Trivy scanners and combines the results

    Args:
        reports_dir: Path object pointing to the directory containing JSON
            report files.
        scanner: Type of scanner ("grype", "trivy", or "both").
        verbose: Whether to print detailed loading information.
        max_workers: Maximum number of concurrent workers (None = auto-detect).
        persist_cyclonedx_dir: Optional directory to persist Trivy reports to.
            If provided, copies generated .cdx.json files to a 'trivy' subdirectory.
            Only applicable for "trivy" and "both" scanner modes.

    Returns:
        A list of dictionaries, each representing a loaded scan report.
        Only reports with vulnerability matches are included.
    """
    # For Grype scanner, load Grype reports and scan SBOMs with Grype only
    if scanner == "grype":
        return process_grype_reports(reports_dir, verbose, max_workers)

    # For Trivy scanner, convert and scan with Trivy only
    if scanner == "trivy":
        return process_trivy_reports(reports_dir, verbose, max_workers, persist_cyclonedx_dir)

    # For both scanners, run both Grype and Trivy and combine results
    return process_both_reports(reports_dir, verbose, max_workers, persist_cyclonedx_dir)
