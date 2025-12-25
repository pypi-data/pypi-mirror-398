"""Core functionality for CVE Report Aggregator.

This package contains the core business logic, configuration management,
validation, and orchestration for the CVE Report Aggregator application.

Key modules:
- config: Multi-source configuration loading and management
- models: Pydantic data models and type definitions
- validation: Tool and configuration validation
- orchestrator: Main workflow coordination
- error_handler: Centralized error handling
- executor: Command execution utilities
- logging: Structured logging setup
- constants: Application constants
- exceptions: Custom exception types
"""

from .config import get_config, get_current_config, set_config
from .error_handler import ErrorHandler
from .exceptions import (
    AuthenticationError,
    ConfigurationError,
    DownloadError,
    NetworkError,
    PackageNotFoundError,
)
from .executor import ExecutorManager
from .logging import get_logger
from .models import AggregatorConfig, EnrichmentConfig, ModeType, PackageConfig, ScannerType
from .orchestrator import AggregationResult, run_aggregation
from .validation import (
    ConfigValidationError,
    MissingToolError,
    validate_configuration,
    validate_grype_requirements,
    validate_scanner_tools,
    validate_trivy_requirements,
    validate_uds_requirements,
    validate_zarf_requirements,
)

__all__ = [
    # Configuration
    "get_config",
    "get_current_config",
    "set_config",
    "AggregatorConfig",
    "EnrichmentConfig",
    "PackageConfig",
    # Type definitions
    "ScannerType",
    "ModeType",
    # Validation
    "ConfigValidationError",
    "MissingToolError",
    "validate_scanner_tools",
    "validate_configuration",
    "validate_grype_requirements",
    "validate_trivy_requirements",
    "validate_uds_requirements",
    "validate_zarf_requirements",
    # Orchestration
    "run_aggregation",
    "AggregationResult",
    # Error handling
    "ErrorHandler",
    "ConfigurationError",
    "DownloadError",
    "PackageNotFoundError",
    "AuthenticationError",
    "NetworkError",
    # Command execution
    "ExecutorManager",
    # Logging
    "get_logger",
]
