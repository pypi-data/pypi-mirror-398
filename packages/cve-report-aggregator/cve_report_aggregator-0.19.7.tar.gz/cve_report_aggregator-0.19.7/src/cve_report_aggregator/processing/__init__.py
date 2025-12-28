"""Data processing and analysis modules for CVE Report Aggregator.

This package contains components for processing vulnerability data:
- Vulnerability aggregation and deduplication
- Scanner integration (Grype/Trivy)
- Severity scoring and selection
"""

from .aggregator import deduplicate_vulnerabilities
from .scanner import load_reports
from .severity import (
    extract_cvss3_scores,
    filter_null_cvss_scores,
    get_highest_cvss3_score,
    get_severity_rank,
    select_highest_severity,
)

__all__ = [
    # Aggregator
    "deduplicate_vulnerabilities",
    # Scanner
    "load_reports",
    # Severity
    "extract_cvss3_scores",
    "filter_null_cvss_scores",
    "get_highest_cvss3_score",
    "get_severity_rank",
    "select_highest_severity",
]
