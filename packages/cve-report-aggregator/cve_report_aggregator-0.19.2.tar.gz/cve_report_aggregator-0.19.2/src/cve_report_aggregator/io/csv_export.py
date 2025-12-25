"""CSV export functionality for vulnerability reports."""

import csv
from pathlib import Path
from typing import Any

from ..core.logging import get_logger
from ..processing.severity import get_highest_cvss3_score

logger = get_logger(__name__)


def extract_cvss_score(vuln_data: dict[str, Any]) -> str:
    """Extract the highest CVSS 3.x score from vulnerability data.

    Args:
        vuln_data: Vulnerability data dictionary

    Returns:
        CVSS score as string, or "N/A" if no score available
    """
    score = get_highest_cvss3_score(vuln_data)
    return f"{score:.1f}" if score else "N/A"


def extract_impact_message(enrichment: dict[str, Any]) -> str:
    """Extract impact analysis from enrichment data.

    Args:
        enrichment: Enrichment data dictionary

    Returns:
        Impact analysis message, or empty string if not available
    """
    impact: str = enrichment.get("impact_analysis", "")
    return impact


def extract_mitigation_message(enrichment: dict[str, Any]) -> str:
    """Extract mitigation summary from enrichment data.

    Args:
        enrichment: Enrichment data dictionary

    Returns:
        Mitigation summary message, or empty string if not available
    """
    mitigation: str = enrichment.get("mitigation_summary", "")
    return mitigation


def export_to_csv(
    unified_report: dict[str, Any],
    output_path: Path,
    enrichments: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Export unified vulnerability report to CSV format.

    Args:
        unified_report: Unified JSON report dictionary
        output_path: Path for the CSV output file
        enrichments: Optional dictionary of CVE enrichments (cve_id -> enrichment_data)

    Raises:
        IOError: If CSV file cannot be written
    """
    logger.info("Generating CSV export", output_path=str(output_path))

    vulnerabilities = unified_report.get("vulnerabilities", [])

    if not vulnerabilities:
        logger.warning("No vulnerabilities to export")
        return

    # Prepare CSV rows
    rows = []
    for vuln in vulnerabilities:
        cve_id = vuln.get("vulnerability_id", "Unknown")
        vuln_data = vuln.get("vulnerability", {})
        severity = vuln_data.get("severity", "Unknown")
        count = vuln.get("count", 0)
        cvss = extract_cvss_score(vuln_data)

        # Get enrichment data if available
        impact = ""
        mitigation = ""
        if enrichments and cve_id in enrichments:
            enrichment = enrichments[cve_id]
            impact = extract_impact_message(enrichment)
            mitigation = extract_mitigation_message(enrichment)

        rows.append(
            {
                "CVE ID": cve_id,
                "Severity": severity,
                "Count": count,
                "CVSS": cvss,
                "Impact": impact,
                "Mitigation": mitigation,
            }
        )

    # Sort by severity rank (Critical > High > Medium > Low > Unknown)
    severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Negligible": 4, "Unknown": 5}
    rows.sort(key=lambda x: (severity_order.get(x["Severity"], 999), -float(x["CVSS"]) if x["CVSS"] != "N/A" else 0))

    # Write CSV file
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["CVE ID", "Severity", "Count", "CVSS", "Impact", "Mitigation"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(rows)

        logger.info(
            "CSV export complete",
            output_path=str(output_path),
            total_rows=len(rows),
        )

    except OSError as e:
        logger.error("Failed to write CSV file", error=str(e), output_path=str(output_path))
        raise
