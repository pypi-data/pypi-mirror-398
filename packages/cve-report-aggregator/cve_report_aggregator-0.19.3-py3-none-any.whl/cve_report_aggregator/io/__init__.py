"""Input/Output operations for CVE Report Aggregator.

This package contains components for data I/O:
- Package downloading from remote registries
- Report generation and output

Note: Download error exceptions have been moved to core.exceptions for centralization.
Import them from cve_report_aggregator.core.exceptions instead.
"""

# Re-export download exceptions from core for backward compatibility
from ..core.exceptions import (
    AuthenticationError,
    DownloadError,
    NetworkError,
    PackageNotFoundError,
    RegistryError,
)
from .downloader import download_package_sboms
from .report import create_unified_report

__all__ = [
    # Downloader
    "download_package_sboms",
    # Report
    "create_unified_report",
    # Exceptions (re-exported from core.exceptions for backward compatibility)
    "DownloadError",
    "AuthenticationError",
    "PackageNotFoundError",
    "NetworkError",
    "RegistryError",
]
