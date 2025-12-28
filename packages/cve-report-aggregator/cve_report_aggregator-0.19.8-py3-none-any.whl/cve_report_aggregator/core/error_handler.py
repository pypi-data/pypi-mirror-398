"""Centralized error handling for CVE Report Aggregator.

This module provides a singleton ErrorHandler class that encapsulates
error parsing and classification logic for use across all modules.
"""

import re
from typing import TYPE_CHECKING

from .exceptions import AuthenticationError, DownloadError, NetworkError, PackageNotFoundError, RegistryError

if TYPE_CHECKING:
    from .models import PackageConfig


# Error patterns to match in command output
ERROR_PATTERNS = {
    # Authentication errors (401/403)
    "authentication": [
        re.compile(r"401 Unauthorized", re.IGNORECASE),
        re.compile(r"403 Forbidden", re.IGNORECASE),
        re.compile(r"authentication required", re.IGNORECASE),
        re.compile(r"access denied", re.IGNORECASE),
        re.compile(r"unauthorized", re.IGNORECASE),
        re.compile(r"permission denied", re.IGNORECASE),
        re.compile(r"credentials.*invalid", re.IGNORECASE),
        re.compile(r"token.*expired", re.IGNORECASE),
    ],
    # Package not found errors (404)
    "not_found": [
        re.compile(r"404 Not Found", re.IGNORECASE),
        re.compile(r"package not found", re.IGNORECASE),
        re.compile(r"manifest unknown", re.IGNORECASE),
        re.compile(r"not found in registry", re.IGNORECASE),
        re.compile(r"no such.*package", re.IGNORECASE),
        re.compile(r"does not exist", re.IGNORECASE),
    ],
    # Network errors
    "network": [
        re.compile(r"connection refused", re.IGNORECASE),
        re.compile(r"connection timeout", re.IGNORECASE),
        re.compile(r"network.*unreachable", re.IGNORECASE),
        re.compile(r"dial tcp.*timeout", re.IGNORECASE),
        re.compile(r"no route to host", re.IGNORECASE),
        re.compile(r"temporary failure in name resolution", re.IGNORECASE),
        re.compile(r"could not resolve host", re.IGNORECASE),
    ],
    # Registry server errors (5xx)
    "registry": [
        re.compile(r"50[0-9] ", re.IGNORECASE),
        re.compile(r"internal server error", re.IGNORECASE),
        re.compile(r"bad gateway", re.IGNORECASE),
        re.compile(r"service unavailable", re.IGNORECASE),
        re.compile(r"gateway timeout", re.IGNORECASE),
    ],
}


class ErrorHandler:
    """Error handler for parsing and classifying errors.

    This class provides centralized error handling logic that can be used
    across all modules in the application. Instances are typically created
    and managed by the AppContext for dependency injection.

    Example:
        >>> handler = ErrorHandler()
        >>> status_code = handler.extract_http_status_code("401 Unauthorized")
        >>> error_type = handler.classify_error("Package not found")
        >>> parsed_error = handler.parse_download_error(package, error_output, original_error)
    """

    def extract_http_status_code(self, error_output: str) -> int | None:
        """Extract HTTP status code from error output.

        Args:
            error_output: Error message from command execution

        Returns:
            HTTP status code if found, None otherwise

        Examples:
            >>> handler = ErrorHandler.get_instance()
            >>> handler.extract_http_status_code("Error: 401 Unauthorized")
            401
            >>> handler.extract_http_status_code("HTTP/1.1 404 Not Found")
            404
            >>> handler.extract_http_status_code("No status code here")
            None
        """
        # Match various HTTP status code formats
        patterns = [
            r"\b([1-5][0-9]{2})\b",  # Basic: "404", "401", etc.
            r"HTTP/\d\.\d\s+(\d{3})",  # HTTP protocol format: "HTTP/1.1 404"
            r"status[:\s]+(\d{3})",  # Status prefix: "status: 404" or "status 404"
        ]

        for pattern in patterns:
            match = re.search(pattern, error_output)
            if match:
                try:
                    code = int(match.group(1))
                    # Validate it's a real HTTP status code (100-599)
                    if 100 <= code <= 599:
                        return code
                except (ValueError, IndexError):
                    continue

        return None

    def classify_error(self, error_output: str) -> str:
        """Classify error type based on output patterns.

        Args:
            error_output: Error message from command execution

        Returns:
            Error type: 'authentication', 'not_found', 'network', 'registry', or 'unknown'

        Examples:
            >>> handler = ErrorHandler.get_instance()
            >>> handler.classify_error("Error: 401 Unauthorized")
            'authentication'
            >>> handler.classify_error("Error: Package not found in registry")
            'not_found'
            >>> handler.classify_error("Error: connection timeout")
            'network'
        """
        # Check each error pattern category
        for error_type, patterns in ERROR_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(error_output):
                    return error_type

        # Check HTTP status codes as fallback
        status_code = self.extract_http_status_code(error_output)
        if status_code:
            if status_code in (401, 403):
                return "authentication"
            elif status_code == 404:
                return "not_found"
            elif 500 <= status_code < 600:
                return "registry"

        return "unknown"

    def parse_download_error(
        self,
        package: PackageConfig,
        error_output: str,
        original_error: Exception,
    ) -> DownloadError:
        """Parse command error output and create appropriate exception.

        This method analyzes the error output from UDS/Zarf commands and creates
        a specific exception type based on the error patterns found.

        Args:
            package: Package configuration
            error_output: Combined stdout + stderr from command execution
            original_error: The original exception from subprocess

        Returns:
            Specific DownloadError subclass based on error type

        Examples:
            >>> handler = ErrorHandler.get_instance()
            >>> pkg = PackageConfig(name="test", version="1.0.0", architecture="amd64")
            >>> error = handler.parse_download_error(pkg, "401 Unauthorized", RuntimeError())
            >>> isinstance(error, AuthenticationError)
            True
        """
        error_type = self.classify_error(error_output)
        status_code = self.extract_http_status_code(error_output)

        # Create appropriate exception based on error type
        if error_type == "authentication":
            return AuthenticationError(
                package_name=package.name,
                package_version=package.version,
                status_code=status_code,
                original_error=original_error,
            )

        elif error_type == "not_found":
            return PackageNotFoundError(
                package_name=package.name,
                package_version=package.version,
                architecture=package.architecture,
                original_error=original_error,
            )

        elif error_type == "network":
            return NetworkError(
                package_name=package.name,
                package_version=package.version,
                original_error=original_error,
            )

        elif error_type == "registry":
            return RegistryError(
                package_name=package.name,
                package_version=package.version,
                status_code=status_code,
                original_error=original_error,
            )

        else:
            # Unknown error - return generic DownloadError with output
            return DownloadError(
                package_name=package.name,
                package_version=package.version,
                message=f"Unknown error occurred. Output: {error_output[:200]}",
                original_error=original_error,
            )


# Public API
__all__ = [
    "ErrorHandler",
]
