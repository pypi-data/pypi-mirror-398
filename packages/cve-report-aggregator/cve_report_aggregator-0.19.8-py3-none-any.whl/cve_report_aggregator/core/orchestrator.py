"""Orchestration logic for CVE Report Aggregator.

This module contains the main workflow coordination for aggregating
vulnerability reports. It handles SBOM acquisition, report loading,
deduplication, enrichment, and report generation.

The orchestrator is designed to be testable independently from the CLI
and can be used from other entry points (API, GUI, etc.).
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..core.models import PackageConfig, ScannerType
from ..enhance import create_enricher
from ..io.csv_export import export_to_csv
from ..io.downloader import download_package_sboms
from ..io.local_packages import scan_local_packages
from ..io.report import create_executive_summary, create_unified_report
from ..processing.aggregator import deduplicate_vulnerabilities
from ..processing.scanner import load_reports
from ..utils import check_command_exists

if TYPE_CHECKING:
    from structlog.types import FilteringBoundLogger

    from ..context import AppContext
    from ..core.models import AggregatorConfig


@dataclass
class AggregationResult:
    """Result of the aggregation process.

    Contains all output files, statistics, and metadata from the
    aggregation workflow.

    Attributes:
        output_files: List of all generated file paths (JSON, CSV, summaries)
        tarball_path: Optional path to created tarball archive
        total_occurrences: Total vulnerability occurrences across all reports
        unique_vulnerabilities: Number of unique vulnerabilities (deduplicated)
        unique_images: Set of unique images scanned
        severity_breakdown: Count of vulnerabilities by severity level
        enrichment_stats: Optional enrichment statistics
        packages_scanned: Number of packages processed
    """

    output_files: list[Path] = field(default_factory=list)
    tarball_path: Path | None = None
    total_occurrences: int = 0
    unique_vulnerabilities: int = 0
    unique_images: set[str] = field(default_factory=set)
    severity_breakdown: dict[str, int] = field(
        default_factory=lambda: {
            "Critical": 0,
            "High": 0,
            "Medium": 0,
            "Low": 0,
            "Negligible": 0,
            "Unknown": 0,
        }
    )
    enrichment_stats: dict[str, Any] | None = None
    packages_scanned: int = 0


def _extract_local_package_sboms(
    package: PackageConfig,
    packages_dir: Path,
    input_dir: Path,
    context: AppContext,
    logger: FilteringBoundLogger,
) -> list[Path]:
    """Extract SBOMs from a single local package archive.

    Args:
        package: Package configuration
        packages_dir: Directory containing package archives
        input_dir: Output directory for extracted SBOMs
        context: Application context
        logger: Logger instance

    Returns:
        List of extracted SBOM file paths

    Raises:
        ValueError: If package archive not found
    """
    from ..io.local_packages import extract_package_sboms

    archive_name = f"zarf-package-{package.name}-{package.architecture}-{package.version}.tar.zst"
    archive_path = packages_dir / archive_name

    if not archive_path.exists():
        raise ValueError(f"Local package archive not found: {archive_name}. Expected at: {archive_path}")

    logger.info(
        "Extracting SBOMs from local package",
        package=package.name,
        version=package.version,
        archive=archive_name,
    )

    sbom_files = extract_package_sboms(
        archive_path=archive_path,
        package=package,
        output_dir=input_dir,
        context=context,
    )

    logger.info(
        "Extracted SBOMs from local package",
        package=package.name,
        sbom_count=len(sbom_files),
    )

    return sbom_files


def _process_configured_local_packages(
    local_packages: list[PackageConfig],
    input_dir: Path,
    context: AppContext,
    logger: FilteringBoundLogger,
) -> list[Path]:
    """Process all configured local packages.

    Args:
        local_packages: List of local package configurations
        input_dir: Output directory for extracted SBOMs
        context: Application context
        logger: Logger instance

    Returns:
        List of all extracted SBOM file paths

    Raises:
        ValueError: If packages directory not found or extraction fails
    """
    if not local_packages or not check_command_exists("uds"):
        return []

    logger.info("Processing local packages", count=len(local_packages))

    packages_dir = Path.cwd() / "packages"
    if not packages_dir.exists():
        raise ValueError(
            f"Local packages configured but directory not found: {packages_dir}. "
            f"Expected to find {len(local_packages)} package archive(s)."
        )

    all_sboms: list[Path] = []
    for package in local_packages:
        sbom_files = _extract_local_package_sboms(package, packages_dir, input_dir, context, logger)
        all_sboms.extend(sbom_files)

    return all_sboms


def _process_configured_remote_packages(
    remote_packages: list[PackageConfig],
    config: AggregatorConfig,
    input_dir: Path,
    context: AppContext,
    logger: FilteringBoundLogger,
) -> list[Path]:
    """Process all configured remote packages.

    Args:
        remote_packages: List of remote package configurations
        config: Aggregator configuration
        input_dir: Output directory for downloaded SBOMs
        context: Application context
        logger: Logger instance

    Returns:
        List of downloaded SBOM file paths
    """
    if not remote_packages:
        return []

    if config.local_only:
        logger.warning(
            "Local-only mode enabled: Skipping remote package downloads",
            skipped=len(remote_packages),
        )
        return []

    logger.info("Downloading remote packages", count=len(remote_packages))

    # Temporarily update config with only remote packages
    original_packages = config.packages
    config.packages = remote_packages

    try:
        downloaded_sboms = download_package_sboms(output_dir=input_dir, context=context)
        logger.info("Downloaded remote SBOMs", count=len(downloaded_sboms))
        return downloaded_sboms
    finally:
        # Always restore original packages list
        config.packages = original_packages


def _auto_detect_local_packages(
    input_dir: Path,
    context: AppContext,
    logger: FilteringBoundLogger,
) -> list[Path] | None:
    """Auto-detect and process local Zarf packages.

    Args:
        input_dir: Output directory for extracted SBOMs
        context: Application context
        logger: Logger instance

    Returns:
        List of SBOM paths if local packages found, None otherwise
    """
    if not check_command_exists("uds"):
        return None

    try:
        local_sboms = scan_local_packages(output_dir=input_dir, context=context)
        if local_sboms:
            logger.info("Auto-detected local Zarf packages", count=len(local_sboms))
            return local_sboms
    except (ValueError, RuntimeError) as e:
        logger.warning("Local package scan failed", error=str(e))

    return None


def _download_remote_packages_fallback(
    config: AggregatorConfig,
    input_dir: Path,
    context: AppContext,
    logger: FilteringBoundLogger,
) -> list[Path]:
    """Download remote packages as fallback when no local packages found.

    Args:
        config: Aggregator configuration
        input_dir: Output directory for downloaded SBOMs
        context: Application context
        logger: Logger instance

    Returns:
        List of downloaded SBOM file paths

    Raises:
        ValueError, RuntimeError: If download fails
    """
    if not config.download_remote_packages:
        return []

    downloaded_sboms = download_package_sboms(output_dir=input_dir, context=context)
    logger.info("Downloaded remote SBOMs", count=len(downloaded_sboms))
    return downloaded_sboms


def acquire_sboms(context: AppContext) -> tuple[list[Path], bool]:
    """Acquire SBOM files from mixed local and remote sources.

    Supports three modes of operation:
    1. Mixed packages: Process packages based on their "source" field (local or remote)
    2. Auto-detect (legacy): Check ./packages/ directory first, fallback to remote
    3. Local-only: Only process local packages, skip all remote downloads

    Args:
        context: Application context with configuration

    Returns:
        Tuple of (list of SBOM file paths, whether any local packages were processed)

    Raises:
        ValueError: If package processing fails
        RuntimeError: If SBOM acquisition fails
    """
    config = context.config
    logger = context.get_logger(__name__)
    input_dir = config.input_dir

    # Mode 1: Process configured packages based on their source field
    if config.packages:
        local_packages = [p for p in config.packages if p.source == "local"]
        remote_packages = [p for p in config.packages if p.source == "remote"]

        logger.info(
            "Processing configured packages",
            total=len(config.packages),
            local=len(local_packages),
            remote=len(remote_packages),
        )

        local_sboms = _process_configured_local_packages(local_packages, input_dir, context, logger)
        remote_sboms = _process_configured_remote_packages(remote_packages, config, input_dir, context, logger)

        all_sboms = local_sboms + remote_sboms
        has_local_packages = len(local_sboms) > 0
        return (all_sboms, has_local_packages)

    # Mode 2: Auto-detect local packages, fallback to remote
    logger.info("No packages configured, using auto-detect mode")

    local_sboms = _auto_detect_local_packages(input_dir, context, logger)
    if local_sboms:
        return (local_sboms, True)

    # Mode 3: Local-only mode - skip remote downloads
    if config.local_only:
        logger.info("Local-only mode enabled: No local packages found, skipping remote downloads")
        return ([], False)

    # Fallback: Download remote packages if enabled
    remote_sboms = _download_remote_packages_fallback(config, input_dir, context, logger)
    return (remote_sboms, False)


def load_and_group_reports(context: AppContext) -> dict[str, list[dict[str, Any]]]:
    """Load all reports and group them by package.

    If multiple packages are configured (from remote downloads or local packages),
    reports are grouped by package name based on their directory structure.
    Otherwise, all reports are grouped under "unified".

    Args:
        context: Application context with configuration

    Returns:
        Dictionary mapping package name to list of report dictionaries

    Raises:
        ValueError: If no valid reports are found
    """
    config = context.config
    logger = context.get_logger(__name__)
    input_dir = config.input_dir

    # Determine effective scanner based on mode
    effective_scanner: ScannerType
    if config.mode == "grype-only":
        effective_scanner = "grype"
    elif config.mode == "trivy-only":
        effective_scanner = "trivy"
    else:
        effective_scanner = config.scanner

    # Load all reports (with parallel processing)
    # For Trivy scanner, pipeline mode is always enabled: Grype → CycloneDX → Trivy
    # This generates both Grype and Trivy reports for comprehensive coverage
    if effective_scanner == "trivy":
        logger.info("Trivy scanner: using pipeline mode (Grype + Trivy) for comprehensive coverage")
        # Pipeline mode works best with highest-score aggregation for proper deduplication
        if config.mode not in ["highest-score"]:
            logger.warning(
                f"Pipeline mode works best with 'highest-score' mode. Current mode: {config.mode}. "
                "Consider using --mode highest-score for accurate severity selection."
            )

    # Persist Trivy reports (CycloneDX format) to the input directory when using Trivy or both scanners
    # This allows users to inspect the intermediate reports in the 'trivy' subdirectory
    persist_cyclonedx = input_dir if effective_scanner in ("trivy", "both") else None

    reports = load_reports(
        input_dir,
        scanner=effective_scanner,
        verbose=(config.log_level == "DEBUG"),
        max_workers=config.max_workers,
        persist_cyclonedx_dir=persist_cyclonedx,
    )

    if not reports:
        raise ValueError("No valid reports with vulnerabilities found")

    logger.info(
        "Loaded reports",
        count=len(reports),
        scanner=effective_scanner,
    )

    # Group reports by package if multiple packages are configured
    reports_by_package: dict[str, list[dict[str, Any]]] = {}

    if config.download_remote_packages and config.packages:
        # Group reports by package name extracted from directory structure
        # Files are organized as: <package-name>/<file>.json
        for report in reports:
            source_file = report.get("_source_file", "")
            # Extract package name from directory path (first component)
            path_parts = Path(source_file).parts
            if len(path_parts) > 1:
                package_name = path_parts[0]
            else:
                # Fallback: just the filename if no directory
                package_name = "unknown"

            if package_name not in reports_by_package:
                reports_by_package[package_name] = []
            reports_by_package[package_name].append(report)
    else:
        # Single unified report for all reports
        reports_by_package["unified"] = reports

    return reports_by_package


def _find_package_version(package_name: str, config: AggregatorConfig) -> str | None:
    """Find package version from configuration.

    Args:
        package_name: Name of the package to look up
        config: Aggregator configuration

    Returns:
        Package version if found, None otherwise
    """
    if not config.packages:
        return None

    for pkg in config.packages:
        if pkg.name == package_name:
            return pkg.version
    return None


def _determine_output_path(package_name: str, package_version: str | None, output_dir: Path) -> Path:
    """Determine output file path for a package report.

    Uses package version if available, otherwise uses timestamp.

    Args:
        package_name: Name of the package
        package_version: Optional package version
        output_dir: Directory to write output to

    Returns:
        Path for the JSON output file
    """
    from datetime import datetime

    if package_version:
        return output_dir / f"{package_name}-{package_version}.json"

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return output_dir / f"{package_name}-{timestamp}.json"


def _write_json_report(
    unified_report: dict[str, Any],
    json_path: Path,
    package_name: str,
    logger: FilteringBoundLogger,
) -> None:
    """Write unified report to JSON file.

    Args:
        unified_report: Report data to write
        json_path: Path to write to
        package_name: Name of the package (for logging)
        logger: Logger instance
    """
    import json

    with open(json_path, "w") as f:
        json.dump(unified_report, f, indent=2)

    logger.info(
        "Created unified report",
        package=package_name,
        output=str(json_path),
    )


def _export_csv_report(
    unified_report: dict[str, Any],
    json_path: Path,
    package_name: str,
    logger: FilteringBoundLogger,
) -> Path | None:
    """Export unified report to CSV format.

    Args:
        unified_report: Report data to export
        json_path: Path to JSON file (CSV path derived from this)
        package_name: Name of the package (for logging)
        logger: Logger instance

    Returns:
        Path to CSV file if successful, None on error
    """
    try:
        csv_path = json_path.with_suffix(".csv")
        enrichments_dict = unified_report.get("enrichments", {})
        export_to_csv(unified_report, csv_path, enrichments=enrichments_dict)
        logger.info(
            "Created CSV export",
            package=package_name,
            output=str(csv_path),
        )
        return csv_path
    except Exception as e:
        logger.warning(
            "CSV export failed",
            package=package_name,
            error=str(e),
        )
        return None


def process_package_reports(
    package_name: str,
    package_reports: list[dict[str, Any]],
    context: AppContext,
) -> tuple[Path, Path | None, dict[str, Any]]:
    """Process reports for a single package.

    This function coordinates:
    1. Vulnerability deduplication
    2. Unified report creation
    3. CVE enrichment (if enabled)
    4. Report persistence (JSON and CSV)

    Args:
        package_name: Name of the package
        package_reports: List of reports for this package
        context: Application context with configuration

    Returns:
        Tuple of (JSON output path, CSV output path, vulnerability map)
    """
    config = context.config
    logger = context.get_logger(__name__)

    # Find package version from configuration
    package_version = _find_package_version(package_name, config)

    # Deduplicate vulnerabilities for this package
    vuln_map = deduplicate_vulnerabilities(package_reports, config.mode)

    logger.info(
        "Deduplicated vulnerabilities",
        package=package_name,
        unique_count=len(vuln_map),
    )

    # Create unified report
    unified_report = create_unified_report(
        vuln_map,
        package_reports,
        package_name=package_name,
        package_version=package_version,
    )

    # Enrich CVEs with OpenAI if enabled
    if config.enrich.enabled:
        unified_report = enrich_report(
            unified_report=unified_report,
            package_name=package_name,
            context=context,
        )

    # Write reports to disk using configured output directory
    output_dir = config.output_file.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = _determine_output_path(package_name, package_version, output_dir)
    _write_json_report(unified_report, json_path, package_name, logger)
    csv_path = _export_csv_report(unified_report, json_path, package_name, logger)

    return (json_path, csv_path, vuln_map)


def _count_eligible_cves(vulnerabilities: list[dict[str, Any]], severity_filter: list[str]) -> int:
    """Count CVEs matching the severity filter.

    Args:
        vulnerabilities: List of vulnerability dictionaries
        severity_filter: List of severity levels to match

    Returns:
        Number of CVEs matching the severity filter
    """
    return sum(1 for vuln in vulnerabilities if vuln.get("vulnerability", {}).get("severity") in severity_filter)


def _build_enrichment_summary(
    vulnerabilities: list[dict[str, Any]],
    enriched_count: int,
    config: Any,
    error: str | None = None,
) -> dict[str, Any]:
    """Build enrichment summary statistics.

    Args:
        vulnerabilities: List of vulnerability dictionaries
        enriched_count: Number of successfully enriched CVEs
        config: Enrichment configuration
        error: Error message if enrichment failed

    Returns:
        Enrichment summary dictionary
    """
    eligible_cves = _count_eligible_cves(vulnerabilities, config.severities)
    summary: dict[str, Any] = {
        "enabled": True,
        "total_cves": len(vulnerabilities),
        "eligible_cves": eligible_cves,
        "enriched_cves": enriched_count,
        "severity_filter": config.severities,
    }
    if enriched_count > 0:
        summary["model"] = config.model
    if error:
        summary["error"] = error
    return summary


def enrich_report(
    unified_report: dict[str, Any],
    package_name: str,
    context: AppContext,
) -> dict[str, Any]:
    """Enrich unified report with OpenRouter CVE analysis.

    Args:
        unified_report: Unified report dictionary
        package_name: Name of the package being enriched
        context: Application context with configuration

    Returns:
        Updated unified report with enrichment data

    Note:
        Configuration errors are re-raised (invalid API key, unknown provider).
        API/network errors are logged but allow processing to continue.
    """
    from ..enhance.exceptions import ConfigurationError, EnrichmentError

    config = context.config
    logger = context.get_logger(__name__)

    if not config.enrich.api_key:
        logger.warning(
            "CVE enrichment enabled but no API key provided",
            package=package_name,
        )
        return unified_report

    vulnerabilities = unified_report.get("vulnerabilities", [])

    try:
        # Use factory to create enricher based on configuration
        enricher = create_enricher(config.enrich)

        # Enrich vulnerabilities
        enrichments = enricher.enrich_report(
            vulnerabilities=vulnerabilities,
            max_cves=None,
            severity_filter=config.enrich.severities,
        )

        # Add enrichments to unified report
        unified_report["enrichments"] = {cve_id: enrichment.model_dump() for cve_id, enrichment in enrichments.items()}

        # Update summary with enrichment statistics
        if "summary" not in unified_report:
            unified_report["summary"] = {}
        unified_report["summary"]["enrichment"] = _build_enrichment_summary(
            vulnerabilities, len(enrichments), config.enrich
        )

        logger.info(
            "Enriched CVEs",
            package=package_name,
            enriched=len(enrichments),
            total=len(vulnerabilities),
        )

    except ConfigurationError:
        # Configuration errors should propagate - they indicate a setup problem
        raise

    except EnrichmentError as e:
        # Expected enrichment errors (API issues, timeouts) - continue without enrichment
        logger.warning(
            "CVE enrichment failed, continuing without enrichment",
            package=package_name,
            error=str(e),
            error_type=type(e).__name__,
        )
        unified_report["enrichments"] = {}
        if "summary" not in unified_report:
            unified_report["summary"] = {}
        unified_report["summary"]["enrichment"] = _build_enrichment_summary(
            vulnerabilities, 0, config.enrich, error=str(e)
        )

    except Exception as e:
        # Unexpected errors - log at error level but continue
        logger.error(
            "Unexpected error during CVE enrichment",
            package=package_name,
            error=str(e),
            error_type=type(e).__name__,
        )
        unified_report["enrichments"] = {}
        if "summary" not in unified_report:
            unified_report["summary"] = {}
        unified_report["summary"]["enrichment"] = _build_enrichment_summary(
            vulnerabilities, 0, config.enrich, error=str(e)
        )

    return unified_report


def create_executive_summary_report(
    all_vuln_maps: dict[str, Any],
    all_reports: list[dict[str, Any]],
    context: AppContext,
) -> Path:
    """Create executive summary for all packages.

    Args:
        all_vuln_maps: Merged vulnerability maps from all packages
        all_reports: All reports from all packages
        context: Application context

    Returns:
        Path to executive summary JSON file
    """
    import json
    from datetime import datetime

    logger = context.get_logger(__name__)

    # Create executive summary
    executive_summary = create_executive_summary(all_vuln_maps, all_reports)

    # Generate timestamp for executive summary
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Write executive summary using configured output directory
    output_dir = context.config.output_file.parent
    executive_summary_file = output_dir / f"executive-summary-{timestamp}.json"
    with open(executive_summary_file, "w") as f:
        json.dump(executive_summary, f, indent=2)

    logger.info(
        "Created executive summary",
        output=str(executive_summary_file),
    )

    return executive_summary_file


def aggregate_statistics(output_files: list[Path], context: AppContext) -> AggregationResult:
    """Aggregate statistics from all generated reports.

    Reads all unified JSON reports and aggregates statistics including
    total occurrences, unique vulnerabilities, severity breakdown, and
    enrichment statistics.

    Args:
        output_files: List of all generated output files
        context: Application context

    Returns:
        AggregationResult with aggregated statistics
    """

    logger = context.get_logger(__name__)

    result = AggregationResult()
    result.output_files = output_files

    # Count packages (only unified JSON reports, not executive summaries or CSV)
    unified_json = [f for f in output_files if f.suffix == ".json" and not f.name.startswith("executive-summary")]
    result.packages_scanned = len(unified_json)

    total_enriched = 0
    total_eligible = 0
    enrichment_enabled = False
    enrichment_model: str | None = None

    # Aggregate statistics from unified reports
    for output_file_path in output_files:
        # Skip executive summary files and CSV files
        if output_file_path.name.startswith("executive-summary") or output_file_path.suffix == ".csv":
            continue

        try:
            from .json_utils import load_json_report

            report_data = load_json_report(output_file_path)

            result.total_occurrences += report_data["summary"]["total_vulnerability_occurrences"]
            result.unique_vulnerabilities += report_data["summary"]["unique_vulnerabilities"]

            # Collect unique images from scanned_images
            for scanned_image in report_data["summary"]["scanned_images"]:
                result.unique_images.add(scanned_image["image"])

            for severity, count in report_data["summary"]["by_severity"].items():
                result.severity_breakdown[severity] = result.severity_breakdown.get(severity, 0) + count

            # Aggregate enrichment statistics
            if "enrichment" in report_data.get("summary", {}):
                enrichment_data = report_data["summary"]["enrichment"]
                if enrichment_data.get("enabled"):
                    enrichment_enabled = True
                    total_enriched += enrichment_data.get("enriched_cves", 0)
                    total_eligible += enrichment_data.get("eligible_cves", 0)
                    if not enrichment_model:
                        enrichment_model = enrichment_data.get("model")

        except Exception as e:
            logger.warning(
                "Failed to read report for statistics",
                file=str(output_file_path),
                error=str(e),
            )
            continue

    # Set enrichment statistics if enabled
    if enrichment_enabled:
        enrichment_pct = (total_enriched / total_eligible * 100) if total_eligible > 0 else 0
        result.enrichment_stats = {
            "enabled": True,
            "model": enrichment_model,
            "total_enriched": total_enriched,
            "total_eligible": total_eligible,
            "percentage": enrichment_pct,
        }

    return result


def _merge_vulnerability_entry(
    all_vuln_maps: dict[str, Any],
    vuln_id: str,
    vuln_entry: dict[str, Any],
) -> None:
    """Merge a vulnerability entry into the aggregate map.

    If the vulnerability already exists, merges counts and affected sources.
    Otherwise, adds the new entry.

    Args:
        all_vuln_maps: Aggregate vulnerability map (modified in-place)
        vuln_id: Vulnerability identifier
        vuln_entry: Vulnerability data to merge
    """
    if vuln_id not in all_vuln_maps:
        all_vuln_maps[vuln_id] = vuln_entry
    else:
        # Merge counts and affected sources
        all_vuln_maps[vuln_id]["count"] += vuln_entry["count"]
        all_vuln_maps[vuln_id]["affected_sources"].extend(vuln_entry["affected_sources"])
        all_vuln_maps[vuln_id]["match_details"].extend(vuln_entry["match_details"])


def _collect_artifacts_for_tarball(
    output_files: list[Path],
    input_dir: Path | None,
    logger: FilteringBoundLogger,
) -> list[Path]:
    """Collect all artifact files for tarball archive.

    Includes output files and SBOM files from input directory.

    Args:
        output_files: List of generated output files
        input_dir: Input directory containing SBOM files
        logger: Logger instance

    Returns:
        List of all files to include in tarball
    """
    all_artifact_files: list[Path] = list(output_files)

    if input_dir and input_dir.exists():
        sbom_files = list(input_dir.rglob("*.json"))
        all_artifact_files.extend(sbom_files)
        logger.info(
            "Including SBOM artifacts in tarball",
            input_dir=str(input_dir),
            sbom_count=len(sbom_files),
        )

    return all_artifact_files


def _create_tarball_archive(
    archive_dir: Path,
    artifact_files: list[Path],
    result: AggregationResult,
    context: AppContext,
    logger: FilteringBoundLogger,
) -> None:
    """Create tarball archive of all artifacts.

    Handles errors gracefully, logging warnings but not failing the workflow.

    Args:
        archive_dir: Directory to create tarball in
        artifact_files: Files to include in tarball
        result: Aggregation result (modified in-place to set tarball_path)
        context: Application context
        logger: Logger instance
    """
    from ..io.archive import create_tarball

    tarball_path = archive_dir / "artifacts.tar.gz"

    try:
        created_tarball = create_tarball(
            tarball_path=tarball_path,
            output_files=artifact_files,
            context=context,
        )
        result.tarball_path = created_tarball
        logger.info(
            "Created tarball",
            tarball=str(created_tarball),
            total_files=len(artifact_files),
        )
    except Exception as e:
        logger.warning(
            "Tarball creation failed but continuing",
            error=str(e),
        )


def _process_all_packages(
    reports_by_package: dict[str, list[dict[str, Any]]],
    context: AppContext,
    logger: FilteringBoundLogger,
) -> tuple[list[Path], list[dict[str, Any]], dict[str, Any]]:
    """Process all packages and collect results.

    Args:
        reports_by_package: Reports grouped by package name
        context: Application context
        logger: Logger instance

    Returns:
        Tuple of (output_files, all_reports, merged_vuln_maps)
    """
    output_files: list[Path] = []
    all_reports: list[dict[str, Any]] = []
    all_vuln_maps: dict[str, Any] = {}

    for package_name, package_reports in reports_by_package.items():
        logger.info(
            "Processing package",
            package=package_name,
            report_count=len(package_reports),
        )

        json_path, csv_path, vuln_map = process_package_reports(
            package_name=package_name,
            package_reports=package_reports,
            context=context,
        )

        output_files.append(json_path)
        if csv_path:
            output_files.append(csv_path)

        all_reports.extend(package_reports)

        # Merge vulnerability maps across packages
        for vuln_id, vuln_entry in vuln_map.items():
            _merge_vulnerability_entry(all_vuln_maps, vuln_id, vuln_entry)

    return output_files, all_reports, all_vuln_maps


def run_aggregation(context: AppContext) -> AggregationResult:
    """Main orchestration function that coordinates the entire workflow.

    This is the primary entry point for the aggregation process. It:
    1. Acquires SBOMs (local or remote)
    2. Loads and groups reports by package
    3. Processes each package (deduplicate, enrich, export)
    4. Creates executive summary
    5. Aggregates statistics
    6. Creates tarball archive (if configured)

    Args:
        context: Application context with configuration and services

    Returns:
        AggregationResult with output files and statistics

    Raises:
        ValueError: If configuration is invalid or no reports found
        RuntimeError: If critical processing steps fail
    """
    logger = context.get_logger(__name__)
    config = context.config

    logger.info("Starting aggregation workflow")

    # Step 1: Acquire SBOMs (local or remote)
    sboms, local_sboms_found = acquire_sboms(context)
    if sboms:
        logger.info(
            "Acquired SBOMs",
            count=len(sboms),
            source="local" if local_sboms_found else "remote",
        )

    # Step 2: Load and group reports by package
    reports_by_package = load_and_group_reports(context)
    logger.info("Grouped reports by package", packages=list(reports_by_package.keys()))

    # Step 3: Process each package's reports
    output_files, all_reports, all_vuln_maps = _process_all_packages(reports_by_package, context, logger)

    # Step 4: Create executive summary for all packages
    if all_vuln_maps and all_reports:
        executive_summary_file = create_executive_summary_report(
            all_vuln_maps=all_vuln_maps,
            all_reports=all_reports,
            context=context,
        )
        output_files.append(executive_summary_file)

    # Step 5: Aggregate statistics
    result = aggregate_statistics(output_files, context)

    # Step 6: Create tarball archive (default: ~/output, or configured archive_dir)
    archive_dir = config.archive_dir or (Path.home() / "output")
    archive_dir.mkdir(parents=True, exist_ok=True)
    artifact_files = _collect_artifacts_for_tarball(output_files, config.input_dir, logger)
    if artifact_files:
        _create_tarball_archive(archive_dir, artifact_files, result, context, logger)

    logger.info(
        "Aggregation workflow completed",
        packages_scanned=result.packages_scanned,
        unique_vulnerabilities=result.unique_vulnerabilities,
        output_files=len(output_files),
    )

    return result


# Public API
__all__ = [
    "AggregationResult",
    "acquire_sboms",
    "load_and_group_reports",
    "process_package_reports",
    "enrich_report",
    "create_executive_summary_report",
    "aggregate_statistics",
    "run_aggregation",
]
