"""Input/Output operations for CVE Report Aggregator.

This package contains components for data I/O:
- Package downloading from remote registries
- Report generation and output

Note: Download error exceptions are in cve_report_aggregator.core.exceptions.
"""

from .downloader import download_package_sboms
from .report import create_unified_report

__all__ = [
    # Downloader
    "download_package_sboms",
    # Report
    "create_unified_report",
]
