"""Custom exceptions for CVE report aggregation.

This module provides a hierarchy of custom exceptions that improve
error handling and make it easier to catch and handle specific error
conditions throughout the application.
"""


class CVEAggregatorError(Exception):
    """Base exception for all CVE aggregator errors.

    All custom exceptions in this application should inherit from this base class.
    """

    pass


class ConfigurationError(CVEAggregatorError):
    """Raised when configuration is invalid or missing.

    Examples:
        - Required configuration field is missing
        - Configuration file is malformed
        - Invalid configuration values
    """

    pass


class ScannerError(CVEAggregatorError):
    """Base exception for scanner-related errors."""

    pass


class ScannerNotFoundError(ScannerError):
    """Raised when a required scanner tool is not installed or not found in PATH.

    This includes tools like grype, syft, trivy, and uds.
    """

    def __init__(self, scanner: str, message: str | None = None) -> None:
        """Initialize scanner not found error.

        Args:
            scanner: Name of the scanner tool that was not found
            message: Optional custom error message
        """
        self.scanner = scanner
        if message is None:
            message = f"Scanner '{scanner}' not found. Please install it before running the aggregator."
        super().__init__(message)


class ScannerExecutionError(ScannerError):
    """Raised when a scanner command fails during execution.

    This includes errors like:
    - Scanner crashes
    - Invalid scanner output
    - Scanner returns non-zero exit code
    """

    def __init__(self, scanner: str, command: list[str], stderr: str | None = None) -> None:
        """Initialize scanner execution error.

        Args:
            scanner: Name of the scanner that failed
            command: The command that was executed
            stderr: Standard error output from the scanner
        """
        self.scanner = scanner
        self.command = command
        self.stderr = stderr
        message = f"Scanner '{scanner}' execution failed: {' '.join(command)}"
        if stderr:
            message += f"\nStderr: {stderr}"
        super().__init__(message)


class ReportError(CVEAggregatorError):
    """Base exception for report-related errors."""

    pass


class ReportLoadError(ReportError):
    """Raised when a report file cannot be loaded or parsed.

    Examples:
        - JSON parse errors
        - Invalid report format
        - Missing required fields
    """

    def __init__(self, file_path: str, reason: str) -> None:
        """Initialize report load error.

        Args:
            file_path: Path to the report file that failed to load
            reason: Description of why the load failed
        """
        self.file_path = file_path
        self.reason = reason
        super().__init__(f"Failed to load report '{file_path}': {reason}")


class ReportValidationError(ReportError):
    """Raised when a report has invalid or unexpected structure.

    Examples:
        - Missing required fields
        - Invalid data types
        - Unexpected report format
    """

    pass


class DownloadError(CVEAggregatorError):
    """Base exception for all package download failures.

    This is the base class for more specific download error types.
    Use the specific subclasses (AuthenticationError, PackageNotFoundError, etc.)
    for better error handling and user feedback.

    Attributes:
        package_name: Name of the package that failed to download
        package_version: Version of the package that failed to download
        message: Human-readable error message
        original_error: The original exception that caused this error (if any)
    """

    def __init__(
        self,
        package_name: str,
        package_version: str,
        message: str,
        original_error: Exception | None = None,
    ):
        """Initialize the exception.

        Args:
            package_name: Name of the package
            package_version: Version of the package
            message: Error message describing the failure
            original_error: The underlying exception that caused this error
        """
        self.package_name = package_name
        self.package_version = package_version
        self.message = message
        self.original_error = original_error
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format the error message with package details.

        Returns:
            Formatted error message
        """
        base_msg = f"Failed to download {self.package_name}-{self.package_version}: {self.message}"
        if self.original_error:
            base_msg += f" (Original error: {self.original_error})"
        return base_msg


class AuthenticationError(DownloadError):
    """Exception raised when authentication fails (401/403 errors).

    This typically indicates:
    - Missing or invalid registry credentials
    - Expired authentication token
    - Insufficient permissions to access the package
    """

    def __init__(
        self,
        package_name: str,
        package_version: str,
        status_code: int | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize authentication error.

        Args:
            package_name: Name of the package
            package_version: Version of the package
            status_code: HTTP status code (401 or 403)
            original_error: The underlying exception
        """
        self.status_code = status_code
        message = self._build_message(status_code)
        super().__init__(package_name, package_version, message, original_error)

    def _build_message(self, status_code: int | None) -> str:
        """Build appropriate message based on status code.

        Args:
            status_code: HTTP status code

        Returns:
            Formatted error message
        """
        if status_code == 401:
            return "Authentication required. Please check your registry credentials."
        elif status_code == 403:
            return "Access forbidden. You may not have permission to access this package."
        else:
            return "Authentication or authorization failed. Please verify your credentials and permissions."


class PackageNotFoundError(DownloadError):
    """Exception raised when package does not exist (404 error).

    This typically indicates:
    - Package name is incorrect
    - Package version does not exist
    - Package architecture is not available
    - Wrong registry or organization
    """

    def __init__(
        self,
        package_name: str,
        package_version: str,
        architecture: str | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize package not found error.

        Args:
            package_name: Name of the package
            package_version: Version of the package
            architecture: Package architecture (if relevant)
            original_error: The underlying exception
        """
        self.architecture = architecture
        message = self._build_message(architecture)
        super().__init__(package_name, package_version, message, original_error)

    def _build_message(self, architecture: str | None) -> str:
        """Build appropriate message including architecture if provided.

        Args:
            architecture: Package architecture

        Returns:
            Formatted error message
        """
        base = "Package not found in registry."
        suggestions = [
            "Verify the package name and version are correct",
            "Check that the registry and organization are correct",
        ]

        if architecture:
            suggestions.append(f"Verify that architecture '{architecture}' is available for this package")

        return f"{base} {' '.join(suggestions)}."


class NetworkError(DownloadError):
    """Exception raised when network-related errors occur.

    This typically indicates:
    - Network connectivity issues
    - DNS resolution failures
    - Timeout errors
    - Connection refused
    """

    def __init__(
        self,
        package_name: str,
        package_version: str,
        original_error: Exception | None = None,
    ):
        """Initialize network error.

        Args:
            package_name: Name of the package
            package_version: Version of the package
            original_error: The underlying exception
        """
        message = "Network error occurred. Check your internet connection and registry availability."
        super().__init__(package_name, package_version, message, original_error)


class RegistryError(DownloadError):
    """Exception raised when registry returns server errors (5xx).

    This typically indicates:
    - Registry service is down or unavailable
    - Registry is experiencing issues
    - Temporary service outage
    """

    def __init__(
        self,
        package_name: str,
        package_version: str,
        status_code: int | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize registry error.

        Args:
            package_name: Name of the package
            package_version: Version of the package
            status_code: HTTP status code (5xx)
            original_error: The underlying exception
        """
        self.status_code = status_code
        message = (
            f"Registry server error (HTTP {status_code}). "
            "The registry may be experiencing issues. Please try again later."
        )
        super().__init__(package_name, package_version, message, original_error)


class AggregationError(CVEAggregatorError):
    """Raised when vulnerability deduplication/aggregation fails.

    Examples:
        - Data inconsistencies
        - Invalid vulnerability data
        - Aggregation logic errors
    """

    pass


class EnrichmentError(CVEAggregatorError):
    """Raised when CVE enrichment with OpenAI API fails.

    Examples:
        - API timeout or rate limiting
        - Batch processing failure
        - Invalid API response
        - OpenAI service unavailable
    """

    pass
