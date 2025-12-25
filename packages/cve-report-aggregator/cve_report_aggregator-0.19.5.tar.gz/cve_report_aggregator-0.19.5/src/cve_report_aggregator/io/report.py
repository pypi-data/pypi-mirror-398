"""Report generation for unified vulnerability data."""

from datetime import datetime
from typing import Any

from cve_report_aggregator.processing.aggregator import extract_image_name
from cve_report_aggregator.processing.severity import get_highest_cvss3_score


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
    # Get metadata
    first_report: dict[str, Any] = reports[0] if reports else {}
    scanner: str = first_report.get("_scanner", "grype")
    scanner_version: str = (
        first_report.get("SchemaVersion", "unknown")
        if scanner == "trivy"
        else first_report.get("descriptor", {}).get("version", "unknown")
    )

    # Calculate overall statistics
    total_occurrences: int = sum(entry["count"] for entry in vuln_map.values())
    unique_vulnerabilities: int = len(vuln_map)
    total_images: int = len({r.get("_source_file", "") for r in reports})

    # Severity breakdown and scanner source tracking
    # Single loop to count both overall severity and severity by scanner
    severity_counts: dict[str, int] = {
        "Critical": 0,
        "High": 0,
        "Medium": 0,
        "Low": 0,
        "Negligible": 0,
        "Unknown": 0,
    }
    severity_by_scanner: dict[str, dict[str, int]] = {}

    for entry in vuln_map.values():
        severity: str = entry["vulnerability_data"].get("severity", "Unknown")
        severity_normalized: str = severity.title() if severity else "Unknown"

        # Count overall severity (unique vulnerabilities)
        if severity_normalized in severity_counts:
            severity_counts[severity_normalized] += 1

        # Count severity by scanner source
        # A vulnerability can be detected by multiple scanners, so we count it for each scanner
        scanner_sources: list[str] = entry.get("scanner_sources", [entry.get("selected_scanner", "grype")])

        for scanner_name in scanner_sources:
            if scanner_name not in severity_by_scanner:
                severity_by_scanner[scanner_name] = {
                    "Critical": 0,
                    "High": 0,
                    "Medium": 0,
                    "Low": 0,
                    "Negligible": 0,
                    "Unknown": 0,
                }
            if severity_normalized in severity_by_scanner[scanner_name]:
                severity_by_scanner[scanner_name][severity_normalized] += 1

    # Calculate risk score (weighted severity)
    risk_weights = {"Critical": 10, "High": 7, "Medium": 4, "Low": 1, "Negligible": 0, "Unknown": 0}
    risk_score: int = sum(severity_counts[sev] * risk_weights[sev] for sev in severity_counts)

    # Determine overall risk level
    if severity_counts["Critical"] > 0:
        risk_level = "Critical"
    elif severity_counts["High"] > 5:
        risk_level = "High"
    elif severity_counts["High"] > 0 or severity_counts["Medium"] > 10:
        risk_level = "Medium"
    elif severity_counts["Medium"] > 0 or severity_counts["Low"] > 0:
        risk_level = "Low"
    else:
        risk_level = "Minimal"

    # Top 10 critical vulnerabilities
    top_critical: list[dict[str, Any]] = []
    for vuln_id, entry in sorted(vuln_map.items(), key=lambda x: x[1]["count"], reverse=True):
        vuln_data = entry["vulnerability_data"]
        severity = vuln_data.get("severity", "Unknown")

        if severity in ["Critical", "High"]:
            cvss_score = get_highest_cvss3_score(vuln_data)
            top_critical.append(
                {
                    "id": vuln_id,
                    "severity": severity,
                    "cvss_score": cvss_score,
                    "occurrences": entry["count"],
                    "description": vuln_data.get("description", "")[:200] + "..."
                    if len(vuln_data.get("description", "")) > 200
                    else vuln_data.get("description", ""),
                    "fix_available": bool(vuln_data.get("fix", {}).get("versions")),
                }
            )
            if len(top_critical) >= 10:
                break

    # Most affected components
    component_counts: dict[str, int] = {}
    for entry in vuln_map.values():
        for source in entry["affected_sources"]:
            artifact = source["artifact"]
            component_key = f"{artifact['name']}:{artifact['version']}"
            component_counts[component_key] = component_counts.get(component_key, 0) + 1

    top_components = sorted(component_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # Fixable vs non-fixable
    fixable_count = sum(1 for entry in vuln_map.values() if entry["vulnerability_data"].get("fix", {}).get("versions"))
    non_fixable_count = unique_vulnerabilities - fixable_count

    # Generate recommendations
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

    # Build executive summary
    executive_summary: dict[str, Any] = {
        "report_metadata": {
            "generated_at": datetime.now().isoformat(),
            "report_type": "Executive Summary",
            "scanner": scanner,
            "scanner_version": scanner_version,
            "total_images_scanned": total_images,
        },
        "risk_assessment": {
            "overall_risk_level": risk_level,
            "risk_score": risk_score,
            "risk_score_explanation": "Weighted score: Critical=10, High=7, Medium=4, Low=1, Negligible=0",
        },
        "key_metrics": {
            "unique_vulnerabilities": unique_vulnerabilities,
            "total_occurrences": total_occurrences,
            "vulnerabilities_by_severity": severity_counts,
            "vulnerabilities_by_severity_by_scanner": severity_by_scanner,
            "fixable_vulnerabilities": fixable_count,
            "non_fixable_vulnerabilities": non_fixable_count,
            "fix_availability_rate": round((fixable_count / unique_vulnerabilities * 100), 1)
            if unique_vulnerabilities > 0
            else 0,
        },
        "top_critical_vulnerabilities": top_critical,
        "most_affected_components": [
            {"component": comp, "vulnerability_count": count} for comp, count in top_components
        ],
        "recommendations": recommendations,
    }

    return executive_summary
