"""CVE Report Aggregator - Deduplicate and aggregate vulnerability scan reports.

This package provides tools for aggregating vulnerability scan reports from Grype
and Trivy scanners, deduplicating vulnerabilities by CVE ID, and generating unified
reports with CVSS 3.x scoring and occurrence tracking.
"""

from importlib.metadata import metadata, version

__version__ = version("cve-report-aggregator")

# Get author and email from package metadata
_metadata = metadata("cve-report-aggregator")
_author_email: str = _metadata.get("Author-email") or ""
if _author_email:
    # Parse "Name <email>" format
    if "<" in _author_email:
        __author__: str = _author_email.split("<")[0].strip()
        __email__: str = _author_email.split("<")[1].rstrip(">").strip()
    else:
        __author__ = ""
        __email__ = _author_email.strip()
else:
    __author__ = ""
    __email__ = ""

# Module imports after metadata extraction
from .core.models import ModeType, ScannerType
from .io.report import create_unified_report
from .processing.aggregator import deduplicate_vulnerabilities
from .processing.scanner import load_reports
from .processing.severity import (
    extract_cvss3_scores,
    filter_null_cvss_scores,
    get_highest_cvss3_score,
    get_severity_rank,
    select_highest_severity,
)
from .utils import check_command_exists, get_scanner_version

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    # Type definitions
    "ScannerType",
    "ModeType",
    # Core functions
    "load_reports",
    "deduplicate_vulnerabilities",
    "create_unified_report",
    # Severity utilities
    "get_severity_rank",
    "extract_cvss3_scores",
    "get_highest_cvss3_score",
    "filter_null_cvss_scores",
    "select_highest_severity",
    # Utility functions
    "check_command_exists",
    "get_scanner_version",
]
