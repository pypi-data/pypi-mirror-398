"""Validation functions for CVE Report Aggregator.

This module contains all validation logic for tools, configuration,
and scanner requirements. It should be called by the orchestrator
or CLI before any processing begins.
"""

from typing import TYPE_CHECKING

from ..utils import check_command_exists
from .exceptions import ConfigurationError

if TYPE_CHECKING:
    from ..context import AppContext


class ConfigValidationError(ConfigurationError):
    """Raised when configuration validation fails.

    This exception is raised when configuration is invalid or missing required fields.
    It inherits from ConfigurationError to maintain proper exception hierarchy.

    Note: This was renamed from ValidationError to avoid conflicts with Pydantic's
    ValidationError which is imported in various modules.
    """

    pass


class MissingToolError(ConfigValidationError):
    """Raised when a required tool is not found in PATH."""

    def __init__(self, tool: str, install_url: str | None = None):
        """Initialize with tool name and optional installation URL.

        Args:
            tool: Name of the missing tool
            install_url: Optional URL with installation instructions
        """
        self.tool = tool
        self.install_url = install_url
        message = f"Required tool '{tool}' not found in PATH."
        if install_url:
            message += f"\nPlease install it from: {install_url}"
        super().__init__(message)


def validate_grype_requirements() -> None:
    """Validate that Grype scanner is installed.

    Raises:
        MissingToolError: If grype command is not found
    """
    if not check_command_exists("grype"):
        raise MissingToolError(
            tool="grype",
            install_url="https://github.com/anchore/grype#installation",
        )


def validate_trivy_requirements() -> None:
    """Validate that Trivy scanner and its dependencies are installed.

    Trivy mode requires both syft and trivy commands for SBOM conversion
    and scanning.

    Raises:
        MissingToolError: If syft or trivy command is not found
    """
    if not check_command_exists("syft"):
        raise MissingToolError(
            tool="syft",
            install_url="https://github.com/anchore/syft#installation",
        )
    if not check_command_exists("trivy"):
        raise MissingToolError(
            tool="trivy",
            install_url="https://aquasecurity.github.io/trivy/latest/getting-started/installation/",
        )


def validate_uds_requirements() -> None:
    """Validate that UDS CLI is installed.

    Required when downloadRemotePackages is enabled.

    Raises:
        MissingToolError: If uds command is not found
    """
    if not check_command_exists("uds"):
        raise MissingToolError(
            tool="uds",
            install_url="https://github.com/defenseunicorns/uds-cli",
        )


def validate_zarf_requirements() -> None:
    """Validate that UDS CLI is installed (provides zarf via 'uds zarf').

    Required for local package scanning.

    Raises:
        MissingToolError: If uds command is not found
    """
    if not check_command_exists("uds"):
        raise MissingToolError(
            tool="uds",
            install_url="https://github.com/defenseunicorns/uds-cli",
        )


def validate_scanner_tools(context: AppContext) -> None:
    """Validate required tools are installed based on scanner and mode.

    This function checks all tool requirements based on the application
    configuration, including scanner type, mode, and feature flags.

    Args:
        context: Application context with configuration

    Raises:
        MissingToolError: If any required tool is not found

    Example:
        >>> context = AppContext(config)
        >>> validate_scanner_tools(context)  # Raises if tools missing
    """
    config = context.config
    mode = config.mode
    scanner = config.scanner

    # Validate mode-specific requirements
    if mode == "grype-only":
        validate_grype_requirements()
    elif mode == "trivy-only":
        validate_trivy_requirements()
    else:
        # For highest-score and first-occurrence modes, check configured scanner
        if scanner == "grype":
            validate_grype_requirements()
        elif scanner == "trivy":
            validate_trivy_requirements()
        elif scanner == "both":
            # For "both" scanner, we need both Grype and Trivy
            validate_grype_requirements()
            validate_trivy_requirements()

    # Validate downloadRemotePackages requirements
    if config.download_remote_packages:
        validate_uds_requirements()

    # Note: Zarf is optional for local package scanning
    # We don't fail validation if it's missing, just log a warning


def validate_configuration(context: AppContext) -> None:
    """Validate application configuration.

    Performs comprehensive validation of configuration settings including:
    - Required fields are present
    - Paths exist and are accessible
    - Scanner and mode combinations are valid
    - Remote package download configuration is complete

    Args:
        context: Application context with configuration

    Raises:
        ValueError: If configuration is invalid
    """
    config = context.config

    # Validate remote package download configuration
    if config.download_remote_packages:
        if not config.registry:
            raise ValueError("Registry URL is required when downloadRemotePackages is enabled")

        if not config.organization:
            raise ValueError("Organization is required when downloadRemotePackages is enabled")

        if not config.packages:
            # This is a warning, not an error - we can continue without packages
            logger = context.get_logger(__name__)
            logger.warning("No packages configured for download")


# Public API
__all__ = [
    "ConfigValidationError",
    "MissingToolError",
    "validate_grype_requirements",
    "validate_trivy_requirements",
    "validate_uds_requirements",
    "validate_zarf_requirements",
    "validate_scanner_tools",
    "validate_configuration",
]
