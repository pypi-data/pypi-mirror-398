"""Constants and enumerations for CVE report aggregation.

This module centralizes all magic strings, constants, and configuration
values used throughout the application to improve maintainability and
reduce duplication.
"""

import logging
from enum import Enum

# Scanner Types
SCANNER_GRYPE = "grype"
SCANNER_TRIVY = "trivy"

# Aggregation Modes
MODE_HIGHEST_SCORE = "highest-score"
MODE_FIRST_OCCURRENCE = "first-occurrence"
MODE_GRYPE_ONLY = "grype-only"
MODE_TRIVY_ONLY = "trivy-only"

# Log Levels (aligned with Python's logging module)
# See: https://docs.python.org/3/library/logging.html#logging-levels
LOG_LEVEL_TRACE = "TRACE"  # Custom level below DEBUG
LOG_LEVEL_DEBUG = "DEBUG"  # logging.DEBUG = 10
LOG_LEVEL_INFO = "INFO"  # logging.INFO = 20
LOG_LEVEL_WARNING = "WARNING"  # logging.WARNING = 30
LOG_LEVEL_ERROR = "ERROR"  # logging.ERROR = 40
LOG_LEVEL_CRITICAL = "CRITICAL"  # logging.CRITICAL = 50

# Mapping of string log levels to Python logging numeric levels
LOG_LEVEL_MAP: dict[str, int] = {
    LOG_LEVEL_TRACE: logging.DEBUG - 5,  # 5 (custom level below DEBUG)
    LOG_LEVEL_DEBUG: logging.DEBUG,  # 10
    LOG_LEVEL_INFO: logging.INFO,  # 20
    LOG_LEVEL_WARNING: logging.WARNING,  # 30
    LOG_LEVEL_ERROR: logging.ERROR,  # 40
    LOG_LEVEL_CRITICAL: logging.CRITICAL,  # 50
}

# Severity Levels
SEVERITY_CRITICAL = "Critical"
SEVERITY_HIGH = "High"
SEVERITY_MEDIUM = "Medium"
SEVERITY_LOW = "Low"
SEVERITY_NEGLIGIBLE = "Negligible"
SEVERITY_UNKNOWN = "Unknown"

# CVSS Version Prefixes
CVSS_VERSION_3_PREFIX = "3"

# Vulnerability ID Prefixes
CVE_PREFIX = "CVE-"
GHSA_PREFIX = "GHSA-"

# Report Field Names
FIELD_MATCHES = "matches"
FIELD_ARTIFACTS = "artifacts"
FIELD_DESCRIPTOR = "descriptor"
FIELD_SOURCE_FILE = "_source_file"
FIELD_SCANNER = "_scanner"
FIELD_VULNERABILITY = "vulnerability"
FIELD_RELATED_VULNERABILITIES = "relatedVulnerabilities"
FIELD_MATCH_DETAILS = "matchDetails"
FIELD_CVSS = "cvss"
FIELD_SEVERITY = "severity"
FIELD_RESULTS = "Results"
FIELD_VULNERABILITIES = "Vulnerabilities"

# Trivy-specific field names
TRIVY_ARTIFACT_NAME = "ArtifactName"
TRIVY_VULN_ID = "VulnerabilityID"
TRIVY_PKG_NAME = "PkgName"
TRIVY_INSTALLED_VERSION = "InstalledVersion"
TRIVY_PKG_PATH = "PkgPath"
TRIVY_FIXED_VERSION = "FixedVersion"
TRIVY_V3_SCORE = "V3Score"
TRIVY_V2_SCORE = "V2Score"

# Default Values
DEFAULT_ARCHITECTURE = "amd64"
DEFAULT_SCANNER = SCANNER_GRYPE
DEFAULT_MODE = MODE_HIGHEST_SCORE
DEFAULT_LOG_LEVEL = LOG_LEVEL_INFO
DEFAULT_MAX_WORKERS = 32
DEFAULT_IMAGE_NAME = "unknown"
DEFAULT_PROTOCOL = "oci"

# UDS CLI Log Level Mapping
UDS_LOG_LEVEL_MAP = {
    LOG_LEVEL_DEBUG: "debug",
    LOG_LEVEL_INFO: "info",
    LOG_LEVEL_WARNING: "warn",
    LOG_LEVEL_ERROR: "warn",
    LOG_LEVEL_CRITICAL: "trace",
}


class LogLevel(Enum):
    """Enumeration of log levels aligned with Python's logging module.

    Values are tuples of (string_name, numeric_level) where numeric_level
    corresponds to Python's logging.DEBUG, logging.INFO, etc.
    """

    TRACE = (LOG_LEVEL_TRACE, logging.DEBUG - 5)  # 5 (custom level below DEBUG)
    DEBUG = (LOG_LEVEL_DEBUG, logging.DEBUG)  # 10
    INFO = (LOG_LEVEL_INFO, logging.INFO)  # 20
    WARNING = (LOG_LEVEL_WARNING, logging.WARNING)  # 30
    ERROR = (LOG_LEVEL_ERROR, logging.ERROR)  # 40
    CRITICAL = (LOG_LEVEL_CRITICAL, logging.CRITICAL)  # 50

    def __init__(self, level_name: str, level_value: int) -> None:
        """Initialize log level with name and numeric value.

        Args:
            level_name: String name of the log level
            level_value: Numeric value aligned with Python logging
        """
        self.level_name = level_name
        self.level_value = level_value

    @classmethod
    def from_string(cls, level: str) -> LogLevel:
        """Get LogLevel from string.

        Args:
            level: Log level string (case-insensitive)

        Returns:
            Corresponding LogLevel enum value, defaults to INFO if not found

        Examples:
            >>> LogLevel.from_string("debug").level_value
            10
            >>> LogLevel.from_string("INFO").level_name
            'INFO'
        """
        normalized = level.upper() if level else "INFO"
        for log_level in cls:
            if log_level.level_name == normalized:
                return log_level
        return cls.INFO

    @classmethod
    def to_logging_level(cls, level: str) -> int:
        """Convert string log level to Python logging numeric level.

        Args:
            level: Log level string (case-insensitive)

        Returns:
            Numeric log level for use with Python's logging module

        Examples:
            >>> LogLevel.to_logging_level("DEBUG")
            10
            >>> LogLevel.to_logging_level("warning")
            30
        """
        return cls.from_string(level).level_value


class SeverityRank(Enum):
    """Enumeration of severity levels with numeric rankings.

    Higher values indicate more severe vulnerabilities.
    """

    UNKNOWN = 0
    NEGLIGIBLE = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5

    @classmethod
    def from_string(cls, severity: str) -> SeverityRank:
        """Get SeverityRank from severity string.

        Args:
            severity: Severity string (case-insensitive)

        Returns:
            Corresponding SeverityRank enum value

        Examples:
            >>> SeverityRank.from_string("critical").value
            5
            >>> SeverityRank.from_string("Low").value
            2
        """
        normalized = severity.title() if severity else "Unknown"
        return cls[normalized.upper()] if normalized.upper() in cls.__members__ else cls.UNKNOWN


# =============================================================================
# Parallel Processing Configuration
# =============================================================================

# Default CPU count fallback when os.cpu_count() returns None
DEFAULT_CPU_COUNT = 4

# Thread pool sizing
THREAD_MULTIPLIER = 2  # Multiply CPU count by this factor
RESERVED_THREADS = 2  # Reserve threads for OS and other processes

# Worker pool limits
MIN_WORKER_COUNT = 1  # Minimum number of concurrent workers
MAX_WORKER_LIMIT = 20  # Maximum number of concurrent workers (prevent resource exhaustion)

# Polling intervals (in seconds)
# Batch API polling interval: 10 seconds balances responsiveness with API rate limits.
# Shorter intervals increase API calls but detect completion faster.
# Longer intervals reduce API calls but delay detection of batch completion.
# 10 seconds is a reasonable middle ground for typical batch sizes (10-100 CVEs).
BATCH_POLL_INTERVAL = 10

# Timeouts
# Batch API completion window: 24 hours is the maximum allowed by the Batch API.
# Batches must complete within this window or they will be cancelled.
# See: https://openrouter.ai/docs/sdks/python/batches
# For CVE enrichment, typical batches complete in minutes to hours depending on size.
BATCH_TIMEOUT_HOURS = 24
