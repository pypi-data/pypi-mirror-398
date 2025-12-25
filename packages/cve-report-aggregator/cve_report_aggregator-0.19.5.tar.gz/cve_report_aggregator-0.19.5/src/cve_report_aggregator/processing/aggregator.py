"""Core vulnerability deduplication logic."""

from collections import defaultdict
from typing import Any, cast

from ..core.constants import (
    CVE_PREFIX,
    DEFAULT_IMAGE_NAME,
    FIELD_MATCH_DETAILS,
    FIELD_RELATED_VULNERABILITIES,
    FIELD_SCANNER,
    FIELD_SOURCE_FILE,
    FIELD_VULNERABILITY,
    SCANNER_GRYPE,
    SCANNER_TRIVY,
    TRIVY_ARTIFACT_NAME,
    TRIVY_FIXED_VERSION,
    TRIVY_INSTALLED_VERSION,
    TRIVY_PKG_NAME,
    TRIVY_PKG_PATH,
    TRIVY_VULN_ID,
)
from ..core.models import ModeType
from .severity import filter_null_cvss_scores, select_highest_severity


def extract_image_name(report: dict[str, Any]) -> str:
    """Extract image name from Grype report source field.

    Handles multiple possible source field formats:
    1. source.target.userInput (original format)
    2. source.metadata.userInput (newer SBOM scan format)
    3. source as string
    4. source.target as string
    5. Missing/None source

    Args:
        report: Grype report dictionary.

    Returns:
        Image name string, or "unknown" if not extractable.
    """
    source = report.get("source")

    # Handle string source
    if isinstance(source, str):
        return source

    # Handle dict source
    if isinstance(source, dict):
        # Try source.metadata.userInput first (newer format)
        metadata = source.get("metadata")
        if isinstance(metadata, dict):
            user_input = metadata.get("userInput")
            if user_input and isinstance(user_input, str):
                return cast(str, user_input)

        # Try source.target.userInput (original format)
        target = source.get("target")
        if isinstance(target, dict):
            user_input = target.get("userInput")
            if user_input and isinstance(user_input, str):
                return cast(str, user_input)
        elif isinstance(target, str):
            return target

        # Try source.name as fallback
        name = source.get("name")
        if name and isinstance(name, str):
            # Combine with version if available
            version = source.get("version")
            if version and isinstance(version, str):
                return f"{cast(str, name)}:{cast(str, version)}"
            return cast(str, name)

    # Fallback to unknown
    return "unknown"


def _create_vulnerability_entry() -> dict[str, Any]:
    """Factory function for creating a new vulnerability entry.

    Returns:
        Dictionary with default structure for tracking vulnerability occurrences.
    """
    return {
        "count": 0,
        "affected_sources": [],
        "artifacts": [],
        "vulnerability_data": None,
        "selected_scanner": None,
        "scanner_sources": [],  # Track all scanners that detected this vulnerability
        "related_vulnerabilities": [],
        "match_details": [],
    }


def _extract_cve_ids(related_vulnerabilities: list[dict[str, Any]]) -> list[str]:
    """Extract CVE IDs from related vulnerabilities list.

    Args:
        related_vulnerabilities: List of related vulnerability dictionaries.

    Returns:
        List of CVE IDs found in related vulnerabilities.
    """
    cve_ids: list[str] = []
    related: dict[str, Any]
    for related in related_vulnerabilities:
        vuln_id = related.get("id", "")
        if vuln_id.startswith(CVE_PREFIX):
            cve_ids.append(vuln_id)
    return cve_ids


def _select_vulnerability_data(
    mode: ModeType,
    current_data: dict[str, Any] | None,
    new_data: dict[str, Any],
    scanner: str,
    vuln_entry: dict[str, Any],
    related_vulnerabilities: list[dict[str, Any]] | None = None,
) -> None:
    """Select and update vulnerability data based on aggregation mode.

    This function modifies vuln_entry in place, updating vulnerability_data,
    selected_scanner, and related_vulnerabilities based on the specified mode.

    Args:
        mode: Aggregation mode (highest-score or first-occurrence).
        current_data: Currently stored vulnerability data (may be None).
        new_data: New vulnerability data to potentially use.
        scanner: Scanner that produced the new data.
        vuln_entry: Vulnerability entry dictionary to update (modified in place).
        related_vulnerabilities: Optional related vulnerabilities for Grype format.
    """
    if mode == "highest-score":
        previous_data = current_data
        vuln_entry["vulnerability_data"] = select_highest_severity(current_data, new_data)
        # Update scanner and related vulnerabilities if we selected new data
        if vuln_entry["vulnerability_data"] != previous_data:
            vuln_entry["selected_scanner"] = scanner
            if related_vulnerabilities is not None:
                vuln_entry["related_vulnerabilities"] = related_vulnerabilities
    elif current_data is None:
        vuln_entry["vulnerability_data"] = new_data
        vuln_entry["selected_scanner"] = scanner
        if related_vulnerabilities is not None:
            vuln_entry["related_vulnerabilities"] = related_vulnerabilities


def _process_trivy_vulnerability(
    vuln: dict[str, Any],
    result: dict[str, Any],
    source_name: str,
    image_name: str,
    scanner: str,
    mode: ModeType,
    vuln_map: dict[str, dict[str, Any]],
) -> None:
    """Process a single Trivy vulnerability and update the vulnerability map.

    Args:
        vuln: Trivy vulnerability dictionary.
        result: Trivy result containing type information.
        source_name: Name of the source file.
        image_name: Name of the scanned image/artifact.
        scanner: Scanner type (should be "trivy").
        mode: Aggregation mode.
        vuln_map: Vulnerability tracking map (modified in place).
    """
    vuln_id: str = vuln.get(TRIVY_VULN_ID, "")
    if not vuln_id:
        return

    # Trivy already uses CVE IDs as primary keys
    primary_id: str = vuln_id

    # Get or create vulnerability entry
    vuln_entry: dict[str, Any] = vuln_map[primary_id]
    vuln_entry["count"] += 1

    # Track scanner source (add if not already present)
    if scanner not in vuln_entry["scanner_sources"]:
        vuln_entry["scanner_sources"].append(scanner)

    # Track source information
    source_info: dict[str, Any] = {
        "source_file": source_name,
        "image": image_name,
        "artifact": {
            "name": vuln.get(TRIVY_PKG_NAME, "unknown"),
            "version": vuln.get(TRIVY_INSTALLED_VERSION, "unknown"),
            "type": result.get("Type", "unknown"),
            "location": vuln.get(TRIVY_PKG_PATH, None),
        },
    }
    vuln_entry["affected_sources"].append(source_info)

    # Convert to Grype-like format
    new_vuln_data: dict[str, Any] = {
        "id": vuln_id,
        "severity": vuln.get("Severity", "Unknown"),
        "description": vuln.get("Description", ""),
        "cvss": vuln.get("CVSS", {}),
        "references": vuln.get("References", []),
        "publishedDate": vuln.get("PublishedDate", ""),
        "lastModifiedDate": vuln.get("LastModifiedDate", ""),
    }
    if vuln.get(TRIVY_FIXED_VERSION):
        new_vuln_data["fix"] = {
            "versions": [vuln[TRIVY_FIXED_VERSION]],
            "state": "fixed",
        }

    # Filter out null/invalid CVSS scores
    new_vuln_data = filter_null_cvss_scores(new_vuln_data)

    # Select vulnerability data based on mode
    _select_vulnerability_data(
        mode=mode,
        current_data=vuln_entry["vulnerability_data"],
        new_data=new_vuln_data,
        scanner=scanner,
        vuln_entry=vuln_entry,
    )


def _process_grype_match(
    match: dict[str, Any],
    source_name: str,
    image_name: str,
    scanner: str,
    mode: ModeType,
    vuln_map: dict[str, dict[str, Any]],
) -> None:
    """Process a single Grype match and update the vulnerability map.

    Args:
        match: Grype match dictionary.
        source_name: Name of the source file.
        image_name: Name of the scanned image/artifact.
        scanner: Scanner type (should be "grype").
        mode: Aggregation mode.
        vuln_map: Vulnerability tracking map (modified in place).
    """
    # Get the primary vulnerability ID (GHSA or CVE)
    vuln_id = match[FIELD_VULNERABILITY]["id"]

    # Check related vulnerabilities for CVE IDs
    related_vulns = match.get(FIELD_RELATED_VULNERABILITIES, [])
    cve_ids = _extract_cve_ids(related_vulns)

    # Use first CVE as primary key if available, otherwise use GHSA
    primary_id = cve_ids[0] if cve_ids else vuln_id

    # Get or create vulnerability entry
    vuln_entry: dict[str, Any] = vuln_map[primary_id]
    vuln_entry["count"] += 1

    # Track scanner source (add if not already present)
    if scanner not in vuln_entry["scanner_sources"]:
        vuln_entry["scanner_sources"].append(scanner)

    # Track source information
    source_info: dict[str, Any] = {
        "source_file": source_name,
        "image": image_name,
        "artifact": {
            "name": match["artifact"]["name"],
            "version": match["artifact"]["version"],
            "type": match["artifact"]["type"],
            "location": match["artifact"]["locations"][0]["path"] if match["artifact"].get("locations") else None,
        },
    }
    vuln_entry["affected_sources"].append(source_info)

    # Filter out null/invalid CVSS scores
    filtered_vuln_data: dict[str, Any] = filter_null_cvss_scores(match[FIELD_VULNERABILITY])

    # Select vulnerability data based on mode
    _select_vulnerability_data(
        mode=mode,
        current_data=vuln_entry["vulnerability_data"],
        new_data=filtered_vuln_data,
        scanner=scanner,
        vuln_entry=vuln_entry,
        related_vulnerabilities=related_vulns,
    )

    # Add unique match details
    detail: dict[str, Any]
    for detail in match.get(FIELD_MATCH_DETAILS, []):
        if detail not in vuln_entry["match_details"]:
            vuln_entry["match_details"].append(detail)


def deduplicate_vulnerabilities(reports: list[dict[str, Any]], mode: ModeType = "highest-score") -> dict[str, Any]:
    """Deduplicates vulnerabilities across all reports.

    Groups vulnerabilities by CVE ID (or GHSA if no CVE) and tracks
    occurrence counts, affected sources, and artifact details.

    Args:
        reports: List of report dictionaries (Grype or Trivy format).
        mode: Aggregation mode - "highest-score" selects vulnerability data with highest
            CVSS 3.x score across all scanner reports, "first-occurrence" uses first
            occurrence (alphabetical order).

    Returns:
        A dictionary mapping vulnerability IDs to aggregated data including:
        count, affected_sources, vulnerability_data, related_vulnerabilities,
        match_details, and scanner_sources (list of scanners that detected each vuln).
    """
    # Track vulnerabilities by their primary ID
    vuln_map: dict[str, dict[str, Any]] = defaultdict(_create_vulnerability_entry)

    # Process each report
    report: dict[str, Any]
    for report in reports:
        source_name: str = report[FIELD_SOURCE_FILE]
        scanner: str = report.get(FIELD_SCANNER, SCANNER_GRYPE)

        if scanner == SCANNER_TRIVY:
            # Process Trivy format
            image_name: str = report.get(TRIVY_ARTIFACT_NAME, DEFAULT_IMAGE_NAME)

            result: dict[str, Any]
            for result in report.get("Results", []):
                vuln: dict[str, Any]
                for vuln in result.get("Vulnerabilities", []):
                    _process_trivy_vulnerability(
                        vuln=vuln,
                        result=result,
                        source_name=source_name,
                        image_name=image_name,
                        scanner=scanner,
                        mode=mode,
                        vuln_map=vuln_map,
                    )

        else:
            # Process Grype format
            image_name = extract_image_name(report)

            match: dict[str, Any]
            for match in report.get("matches", []):
                _process_grype_match(
                    match=match,
                    source_name=source_name,
                    image_name=image_name,
                    scanner=scanner,
                    mode=mode,
                    vuln_map=vuln_map,
                )

    return vuln_map
