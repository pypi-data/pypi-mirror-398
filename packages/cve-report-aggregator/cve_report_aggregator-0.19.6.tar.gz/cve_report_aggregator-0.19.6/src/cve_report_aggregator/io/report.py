"""Report generation for unified vulnerability data."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from cve_report_aggregator.processing.aggregator import extract_image_name
from cve_report_aggregator.processing.severity import get_highest_cvss3_score

# =============================================================================
# Severity Statistics
# =============================================================================


@dataclass
class SeverityStatistics:
    """Aggregated severity statistics for executive summary.

    Attributes:
        overall_counts: Dictionary of severity level to count
        by_scanner: Dictionary of scanner name to severity counts
        risk_score: Weighted risk score based on severity counts
        risk_level: Overall risk level (Critical, High, Medium, Low, Minimal)
    """

    overall_counts: dict[str, int]
    by_scanner: dict[str, dict[str, int]]
    risk_score: int
    risk_level: str


def _initialize_severity_counts() -> dict[str, int]:
    """Initialize severity counts dictionary with all levels at zero."""
    return {
        "Critical": 0,
        "High": 0,
        "Medium": 0,
        "Low": 0,
        "Negligible": 0,
        "Unknown": 0,
    }


def _normalize_severity(severity: str | None) -> str:
    """Normalize severity string to title case.

    Args:
        severity: Raw severity string from vulnerability data

    Returns:
        Normalized severity string in title case, or "Unknown" if empty/None
    """
    return severity.title() if severity else "Unknown"


def _update_scanner_counts(
    by_scanner: dict[str, dict[str, int]],
    scanner_sources: list[str],
    severity: str,
) -> None:
    """Update per-scanner severity counts.

    Args:
        by_scanner: Dictionary to update with scanner-specific counts
        scanner_sources: List of scanner names that detected this vulnerability
        severity: Normalized severity level
    """
    for scanner_name in scanner_sources:
        if scanner_name not in by_scanner:
            by_scanner[scanner_name] = _initialize_severity_counts()

        if severity in by_scanner[scanner_name]:
            by_scanner[scanner_name][severity] += 1


def _calculate_risk_score(severity_counts: dict[str, int]) -> int:
    """Calculate weighted risk score from severity counts.

    Risk weights: Critical=10, High=7, Medium=4, Low=1, Negligible=0, Unknown=0

    Args:
        severity_counts: Dictionary of severity level to count

    Returns:
        Total weighted risk score
    """
    risk_weights = {
        "Critical": 10,
        "High": 7,
        "Medium": 4,
        "Low": 1,
        "Negligible": 0,
        "Unknown": 0,
    }
    return sum(severity_counts[sev] * risk_weights[sev] for sev in severity_counts)


def _determine_risk_level(severity_counts: dict[str, int]) -> str:
    """Determine overall risk level from severity counts.

    Args:
        severity_counts: Dictionary of severity level to count

    Returns:
        Risk level string: Critical, High, Medium, Low, or Minimal
    """
    if severity_counts["Critical"] > 0:
        return "Critical"
    if severity_counts["High"] > 5:
        return "High"
    if severity_counts["High"] > 0 or severity_counts["Medium"] > 10:
        return "Medium"
    if severity_counts["Medium"] > 0 or severity_counts["Low"] > 0:
        return "Low"
    return "Minimal"


def calculate_severity_statistics(vuln_map: dict[str, Any]) -> SeverityStatistics:
    """Calculate severity statistics from vulnerability map.

    Processes all vulnerabilities in a single pass to calculate:
    - Overall severity counts
    - Per-scanner severity counts
    - Weighted risk score
    - Overall risk level

    Args:
        vuln_map: Dictionary mapping vulnerability IDs to aggregated data

    Returns:
        SeverityStatistics with counts, risk score, and risk level
    """
    overall_counts = _initialize_severity_counts()
    by_scanner: dict[str, dict[str, int]] = {}

    # Count severities in a single pass
    for entry in vuln_map.values():
        severity = _normalize_severity(entry["vulnerability_data"].get("severity"))

        # Update overall counts
        if severity in overall_counts:
            overall_counts[severity] += 1

        # Update per-scanner counts
        scanner_sources = entry.get("scanner_sources", [entry.get("selected_scanner", "grype")])
        _update_scanner_counts(by_scanner, scanner_sources, severity)

    # Calculate risk metrics
    risk_score = _calculate_risk_score(overall_counts)
    risk_level = _determine_risk_level(overall_counts)

    return SeverityStatistics(
        overall_counts=overall_counts,
        by_scanner=by_scanner,
        risk_score=risk_score,
        risk_level=risk_level,
    )


# =============================================================================
# Top Vulnerabilities Extraction
# =============================================================================


def _truncate_description(description: str, max_length: int = 200) -> str:
    """Truncate description to maximum length with ellipsis.

    Args:
        description: Full description string
        max_length: Maximum length before truncation

    Returns:
        Truncated description with "..." if needed
    """
    if len(description) <= max_length:
        return description
    return description[:max_length] + "..."


def extract_top_critical_vulnerabilities(
    vuln_map: dict[str, Any],
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Extract top critical/high severity vulnerabilities.

    Sorts vulnerabilities by occurrence count and filters to Critical/High
    severity only.

    Args:
        vuln_map: Dictionary mapping vulnerability IDs to aggregated data
        limit: Maximum number of vulnerabilities to return

    Returns:
        List of top vulnerability dictionaries with id, severity, cvss_score,
        occurrences, description, and fix_available fields
    """
    top_vulns: list[dict[str, Any]] = []

    # Sort by occurrence count (descending)
    sorted_vulns = sorted(
        vuln_map.items(),
        key=lambda x: x[1]["count"],
        reverse=True,
    )

    for vuln_id, entry in sorted_vulns:
        vuln_data = entry["vulnerability_data"]
        severity = vuln_data.get("severity", "Unknown")

        # Only include Critical and High severity
        if severity not in ["Critical", "High"]:
            continue

        top_vulns.append(
            {
                "id": vuln_id,
                "severity": severity,
                "cvss_score": get_highest_cvss3_score(vuln_data),
                "occurrences": entry["count"],
                "description": _truncate_description(vuln_data.get("description", "")),
                "fix_available": bool(vuln_data.get("fix", {}).get("versions")),
            }
        )

        if len(top_vulns) >= limit:
            break

    return top_vulns


# =============================================================================
# Component Analysis
# =============================================================================


def analyze_affected_components(
    vuln_map: dict[str, Any],
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Analyze most affected components by vulnerability count.

    Args:
        vuln_map: Dictionary mapping vulnerability IDs to aggregated data
        limit: Maximum number of components to return

    Returns:
        List of top affected components with component name and vulnerability_count
    """
    component_counts: dict[str, int] = {}

    # Count vulnerabilities per component
    for entry in vuln_map.values():
        for source in entry["affected_sources"]:
            artifact = source["artifact"]
            component_key = f"{artifact['name']}:{artifact['version']}"
            component_counts[component_key] = component_counts.get(component_key, 0) + 1

    # Sort and limit
    top_components = sorted(
        component_counts.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:limit]

    return [{"component": comp, "vulnerability_count": count} for comp, count in top_components]


# =============================================================================
# Recommendations Generation
# =============================================================================


def generate_recommendations(
    severity_counts: dict[str, int],
    fixable_count: int,
    non_fixable_count: int,
) -> list[str]:
    """Generate actionable recommendations based on vulnerability statistics.

    Args:
        severity_counts: Dictionary of severity level to count
        fixable_count: Number of vulnerabilities with available fixes
        non_fixable_count: Number of vulnerabilities without fixes

    Returns:
        List of recommendation strings prioritized by severity
    """
    recommendations: list[str] = []

    if severity_counts["Critical"] > 0:
        recommendations.append(
            f"URGENT: Address {severity_counts['Critical']} critical vulnerabilities immediately. "
            "These pose the highest risk to your systems."
        )

    if severity_counts["High"] > 0:
        recommendations.append(
            f"HIGH PRIORITY: Review and remediate {severity_counts['High']} high-severity vulnerabilities. "
            "These should be addressed in the next maintenance cycle."
        )

    if fixable_count > 0:
        recommendations.append(
            f"{fixable_count} vulnerabilities have fixes available. "
            "Prioritize updating affected components to patched versions."
        )

    if non_fixable_count > 0:
        recommendations.append(
            f"{non_fixable_count} vulnerabilities have no fixes available yet. "
            "Consider implementing compensating controls or monitoring for patches."
        )

    if not recommendations:
        recommendations.append("Good job! No critical or high-severity vulnerabilities detected.")

    return recommendations


# =============================================================================
# Scanner Metadata
# =============================================================================


def _extract_scanner_version(report: dict[str, Any], scanner: str) -> str:
    """Extract scanner version from report based on scanner type.

    Args:
        report: First report dictionary containing scanner metadata
        scanner: Scanner type ("trivy" or "grype")

    Returns:
        Scanner version string or "unknown" if not found
    """
    if scanner == "trivy":
        return report.get("SchemaVersion", "unknown")
    return report.get("descriptor", {}).get("version", "unknown")


def create_unified_report(
    vuln_map: dict[str, Any],
    reports: list[dict[str, Any]],
    package_name: str | None = None,
    package_version: str | None = None,
) -> dict[str, Any]:
    """Creates a unified report structure with aggregated vulnerability data.

    Args:
        vuln_map: Dictionary mapping vulnerability IDs to aggregated
            vulnerability data.
        reports: List of original report dictionaries.
        package_name: Optional package name to include in metadata.
        package_version: Optional package version to include in metadata.

    Returns:
        A dictionary containing the complete unified report with metadata,
        summary statistics, vulnerability details, and database information.
    """
    # Get metadata from the first report
    first_report: dict[str, Any] = reports[0] if reports else {}
    scanner: str = first_report.get("_scanner", "grype")

    # Calculate statistics
    total_matches: int = sum(entry["count"] for entry in vuln_map.values())
    unique_vulnerabilities: int = len(vuln_map)

    # Initialize all severity levels with 0
    severity_counts: dict[str, int] = {
        "Critical": 0,
        "High": 0,
        "Medium": 0,
        "Low": 0,
        "Negligible": 0,
        "Unknown": 0,
    }

    # Group by severity
    for _vuln_id, entry in vuln_map.items():
        severity: str = entry["vulnerability_data"].get("severity", "Unknown")
        # Handle case variations (Trivy uses uppercase, Grype uses title case)
        severity_normalized: str = severity.title() if severity else "Unknown"
        if severity_normalized not in severity_counts:
            severity_counts[severity_normalized] = 0
        severity_counts[severity_normalized] += entry["count"]

    # Create unified matches list
    unified_matches: list[dict[str, Any]] = []
    vuln_id: str
    for vuln_id, entry in sorted(vuln_map.items(), key=lambda x: x[1]["count"], reverse=True):
        unified_match: dict[str, Any] = {
            "vulnerability_id": vuln_id,
            "count": entry["count"],
            "vulnerability": entry["vulnerability_data"],
            "selected_scanner": entry["selected_scanner"],
            # Use get() with default for backward compatibility with existing tests
            "scanner_sources": entry.get("scanner_sources", [entry["selected_scanner"]]),
            "related_vulnerabilities": entry["related_vulnerabilities"],
            "affected_sources": entry["affected_sources"],
            "match_details": entry["match_details"],
        }
        unified_matches.append(unified_match)

    # Build scanner-specific metadata
    if scanner == "trivy":
        scanner_version: str = first_report.get("SchemaVersion", "unknown")
        scanned_images: list[dict[str, Any]] = [
            {
                "file": r["_source_file"],
                "image": r.get("ArtifactName", "unknown"),
                "matches": sum(len(result.get("Vulnerabilities", [])) for result in r.get("Results", [])),
            }
            for r in reports
        ]
        db_info: dict[str, Any] = {
            "schema_version": first_report.get("SchemaVersion", ""),
            "created_at": first_report.get("CreatedAt", ""),
        }
    else:
        scanner_version = first_report.get("descriptor", {}).get("version", "unknown")
        scanned_images = [
            {
                "file": r["_source_file"],
                "image": extract_image_name(r),
                "matches": len(r.get("matches", [])),
            }
            for r in reports
        ]
        db_info = first_report.get("descriptor", {}).get("db", {})

    # Build metadata with optional package information
    metadata: dict[str, Any] = {
        "generated_at": datetime.now().isoformat(),
        "scanner": scanner,
        "scanner_version": scanner_version,
        "source_reports_count": len(reports),
        "source_reports": [r["_source_file"] for r in reports],
    }

    # Add package information if available
    if package_name:
        metadata["package_name"] = package_name
    if package_version:
        metadata["package_version"] = package_version

    # Build unified report
    unified_report: dict[str, Any] = {
        "metadata": metadata,
        "summary": {
            "total_vulnerability_occurrences": total_matches,
            "unique_vulnerabilities": unique_vulnerabilities,
            "by_severity": severity_counts,
            "scanned_images": scanned_images,
        },
        "vulnerabilities": unified_matches,
        "database_info": db_info,
    }

    return unified_report


def _calculate_fix_availability(vuln_map: dict[str, Any]) -> tuple[int, int, float]:
    """Calculate fix availability statistics.

    Args:
        vuln_map: Dictionary mapping vulnerability IDs to aggregated data

    Returns:
        Tuple of (fixable_count, non_fixable_count, fix_rate_percentage)
    """
    unique_vulnerabilities = len(vuln_map)
    fixable_count = sum(1 for entry in vuln_map.values() if entry["vulnerability_data"].get("fix", {}).get("versions"))
    non_fixable_count = unique_vulnerabilities - fixable_count
    fix_rate = round((fixable_count / unique_vulnerabilities * 100), 1) if unique_vulnerabilities > 0 else 0.0

    return fixable_count, non_fixable_count, fix_rate


def create_executive_summary(vuln_map: dict[str, Any], reports: list[dict[str, Any]]) -> dict[str, Any]:
    """Create an executive summary report with high-level statistics and insights.

    This report is designed for management and stakeholders, providing:
    - Overall risk assessment
    - Key metrics and trends
    - Top vulnerabilities by severity
    - Affected components summary
    - Actionable recommendations

    Args:
        vuln_map: Dictionary mapping vulnerability IDs to aggregated data
        reports: List of original report dictionaries

    Returns:
        Executive summary report dictionary
    """
    # Extract metadata
    first_report = reports[0] if reports else {}
    scanner = first_report.get("_scanner", "grype")
    scanner_version = _extract_scanner_version(first_report, scanner)

    # Calculate basic statistics
    total_occurrences = sum(entry["count"] for entry in vuln_map.values())
    unique_vulnerabilities = len(vuln_map)
    total_images = len({r.get("_source_file", "") for r in reports})

    # Calculate severity statistics and risk assessment
    severity_stats = calculate_severity_statistics(vuln_map)

    # Extract top vulnerabilities and affected components
    top_critical = extract_top_critical_vulnerabilities(vuln_map, limit=10)
    top_components = analyze_affected_components(vuln_map, limit=10)

    # Calculate fix availability
    fixable_count, non_fixable_count, fix_rate = _calculate_fix_availability(vuln_map)

    # Generate recommendations
    recommendations = generate_recommendations(
        severity_stats.overall_counts,
        fixable_count,
        non_fixable_count,
    )

    # Build executive summary
    return {
        "report_metadata": {
            "generated_at": datetime.now().isoformat(),
            "report_type": "Executive Summary",
            "scanner": scanner,
            "scanner_version": scanner_version,
            "total_images_scanned": total_images,
        },
        "risk_assessment": {
            "overall_risk_level": severity_stats.risk_level,
            "risk_score": severity_stats.risk_score,
            "risk_score_explanation": "Weighted score: Critical=10, High=7, Medium=4, Low=1, Negligible=0",
        },
        "key_metrics": {
            "unique_vulnerabilities": unique_vulnerabilities,
            "total_occurrences": total_occurrences,
            "vulnerabilities_by_severity": severity_stats.overall_counts,
            "vulnerabilities_by_severity_by_scanner": severity_stats.by_scanner,
            "fixable_vulnerabilities": fixable_count,
            "non_fixable_vulnerabilities": non_fixable_count,
            "fix_availability_rate": fix_rate,
        },
        "top_critical_vulnerabilities": top_critical,
        "most_affected_components": top_components,
        "recommendations": recommendations,
    }
