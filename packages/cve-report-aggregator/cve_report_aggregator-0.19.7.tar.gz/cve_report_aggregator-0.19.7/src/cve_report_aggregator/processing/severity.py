"""Severity and CVSS score utilities for vulnerability assessment."""

from typing import Any

from ..core.constants import (
    CVSS_VERSION_3_PREFIX,
    FIELD_CVSS,
    FIELD_SEVERITY,
    TRIVY_V2_SCORE,
    TRIVY_V3_SCORE,
    SeverityRank,
)


def get_severity_rank(severity: str) -> int:
    """Get numeric rank for severity level (higher = more severe).

    Args:
        severity: Severity string (e.g., "Critical", "High", "Medium").

    Returns:
        Integer rank where higher numbers indicate more severe vulnerabilities.
    """
    return SeverityRank.from_string(severity).value


def extract_cvss3_scores(vuln_data: dict[str, Any]) -> list[float]:
    """Extract all valid CVSS 3.x base scores from vulnerability data.

    Handles both Grype and Trivy CVSS data formats:
    - Grype: cvss is array of objects with version and metrics.baseScore
    - Trivy: cvss is dict with vendor keys, each having V3Score

    Args:
        vuln_data: Vulnerability data dictionary.

    Returns:
        List of valid CVSS 3.x base scores (non-null, non-zero).
    """
    scores: list[float] = []
    cvss_data = vuln_data.get(FIELD_CVSS)

    if not cvss_data:
        return scores

    # Handle Grype format: cvss is array
    if isinstance(cvss_data, list):
        entry: dict[str, Any]
        for entry in cvss_data:
            if not isinstance(entry, dict):
                continue

            version: str = entry.get("version", "")
            # Check if it's CVSS version 3.x
            if not version.startswith(CVSS_VERSION_3_PREFIX):
                continue

            # Extract base score from metrics
            metrics: dict[str, Any] = entry.get("metrics", {})
            if isinstance(metrics, dict):
                base_score: float | None = metrics.get("baseScore")
                if base_score is not None and base_score > 0:
                    scores.append(float(base_score))

    # Handle Trivy format: cvss is dict with vendor keys
    elif isinstance(cvss_data, dict):
        _vendor: str
        vendor_data: Any
        for _vendor, vendor_data in cvss_data.items():
            if not isinstance(vendor_data, dict):
                continue

            # Look for V3Score (CVSS version 3.x)
            v3_score: float | None = vendor_data.get(TRIVY_V3_SCORE)
            if v3_score is not None and v3_score > 0:
                scores.append(float(v3_score))

    return scores


def get_highest_cvss3_score(vuln_data: dict[str, Any]) -> float | None:
    """Get the highest CVSS 3.x base score from vulnerability data.

    Args:
        vuln_data: Vulnerability data dictionary.

    Returns:
        Highest CVSS 3.x score, or None if no valid scores found.
    """
    scores: list[float] = extract_cvss3_scores(vuln_data)
    return max(scores) if scores else None


def filter_null_cvss_scores(vuln_data: dict[str, Any]) -> dict[str, Any]:
    """Remove CVSS entries with null/zero base scores from vulnerability data.

    This function filters out invalid CVSS scores (null, N/A, or zero) from the
    vulnerability data, ensuring only valid CVSS scores are included in reports.

    Args:
        vuln_data: Vulnerability data dictionary.

    Returns:
        Vulnerability data with filtered CVSS array (only valid scores remain).
    """
    if FIELD_CVSS not in vuln_data or not vuln_data[FIELD_CVSS]:
        return vuln_data

    # Handle Grype format: cvss is array
    if isinstance(vuln_data[FIELD_CVSS], list):
        filtered_list: list[dict[str, Any]] = []
        entry: dict[str, Any]
        for entry in vuln_data[FIELD_CVSS]:
            if not isinstance(entry, dict):
                continue

            # Check if base score exists and is valid
            metrics: dict[str, Any] = entry.get("metrics", {})
            if isinstance(metrics, dict):
                base_score: float | None = metrics.get("baseScore")
                # Only include entries with non-null, non-zero scores
                if base_score is not None and base_score > 0:
                    filtered_list.append(entry)

        # Update the cvss array with filtered results
        vuln_data = vuln_data.copy()
        vuln_data[FIELD_CVSS] = filtered_list

    # Handle Trivy format: cvss is dict with vendor keys
    elif isinstance(vuln_data[FIELD_CVSS], dict):
        filtered_dict: dict[str, Any] = {}
        vendor: str
        vendor_data: Any
        for vendor, vendor_data in vuln_data[FIELD_CVSS].items():
            if not isinstance(vendor_data, dict):
                continue

            # Check for valid V3Score or V2Score
            v3_score: float | None = vendor_data.get(TRIVY_V3_SCORE)
            v2_score: float | None = vendor_data.get(TRIVY_V2_SCORE)

            # Only include entries with at least one valid score
            if (v3_score is not None and v3_score > 0) or (v2_score is not None and v2_score > 0):
                filtered_dict[vendor] = vendor_data

        # Update the cvss dict with filtered results
        vuln_data = vuln_data.copy()
        vuln_data[FIELD_CVSS] = filtered_dict

    return vuln_data


def select_highest_severity(current_data: dict[str, Any] | None, new_data: dict[str, Any]) -> dict[str, Any]:
    """Select vulnerability data with highest severity based on CVSS 3.x scores.

    Prioritizes CVSS 3.x base score comparison over severity string comparison.
    Falls back to severity string comparison if no CVSS 3.x scores are available.

    Args:
        current_data: Currently stored vulnerability data, or None if no data exists yet.
        new_data: New vulnerability data to compare.

    Returns:
        Vulnerability data with the higher CVSS 3.x score or severity rating.
    """
    if current_data is None:
        return new_data

    # Try to compare using CVSS 3.x scores first
    current_score: float | None = get_highest_cvss3_score(current_data)
    new_score: float | None = get_highest_cvss3_score(new_data)

    # If both have CVSS 3.x scores, compare numerically
    if current_score is not None and new_score is not None:
        return new_data if new_score > current_score else current_data

    # If only new data has CVSS 3.x score, prefer it
    if current_score is None and new_score is not None:
        return new_data

    # If only current data has CVSS 3.x score, keep it
    if current_score is not None and new_score is None:
        return current_data

    # Fall back to severity string comparison if no CVSS 3.x scores
    current_severity: str = current_data.get(FIELD_SEVERITY, "Unknown")
    new_severity: str = new_data.get(FIELD_SEVERITY, "Unknown")

    current_rank: int = get_severity_rank(current_severity)
    new_rank: int = get_severity_rank(new_severity)

    return new_data if new_rank > current_rank else current_data
