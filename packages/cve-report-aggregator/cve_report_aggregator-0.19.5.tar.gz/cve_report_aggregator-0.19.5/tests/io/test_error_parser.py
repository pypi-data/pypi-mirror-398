"""Unit tests for error parsing functionality."""

import pytest

from cve_report_aggregator.core.error_handler import ERROR_PATTERNS, ErrorHandler
from cve_report_aggregator.core.exceptions import (
    AuthenticationError,
    DownloadError,
    NetworkError,
    PackageNotFoundError,
    RegistryError,
)
from cve_report_aggregator.core.models import PackageConfig


class TestExtractHttpStatusCode:
    """Test HTTP status code extraction from error output."""

    @pytest.fixture
    def handler(self):
        """Get ErrorHandler instance."""
        return ErrorHandler()

    def test_extract_basic_status_code(self, handler):
        """Test extraction of basic status code format."""
        assert handler.extract_http_status_code("Error: 401 Unauthorized") == 401
        assert handler.extract_http_status_code("404 Not Found") == 404
        assert handler.extract_http_status_code("500 Internal Server Error") == 500

    def test_extract_http_protocol_format(self, handler):
        """Test extraction from HTTP protocol format."""
        assert handler.extract_http_status_code("HTTP/1.1 401 Unauthorized") == 401
        assert handler.extract_http_status_code("HTTP/2.0 404 Not Found") == 404

    def test_extract_status_prefix_format(self, handler):
        """Test extraction from status prefix format."""
        assert handler.extract_http_status_code("status: 401") == 401
        assert handler.extract_http_status_code("status 404") == 404

    def test_extract_no_status_code(self, handler):
        """Test when no status code is present."""
        assert handler.extract_http_status_code("No status code here") is None
        assert handler.extract_http_status_code("Error occurred") is None

    def test_extract_invalid_status_code(self, handler):
        """Test when status code is out of valid range."""
        assert handler.extract_http_status_code("999 Invalid") is None
        assert handler.extract_http_status_code("99 Too Small") is None

    def test_extract_first_valid_status_code(self, handler):
        """Test extraction of first valid status code when multiple are present."""
        assert handler.extract_http_status_code("404 Not Found, later 200 OK") == 404

    def test_extract_status_code_boundary_values(self, handler):
        """Test status code extraction at boundaries (100-599)."""
        assert handler.extract_http_status_code("100 Continue") == 100
        assert handler.extract_http_status_code("599 Custom") == 599
        assert handler.extract_http_status_code("600 Invalid") is None
        assert handler.extract_http_status_code("99 Invalid") is None

    def test_extract_status_code_with_context(self, handler):
        """Test extraction with surrounding text."""
        assert handler.extract_http_status_code("Server returned 502 Bad Gateway error") == 502
        assert handler.extract_http_status_code("The request failed with status: 503") == 503

    def test_extract_status_code_value_error(self, handler):
        """Test handling of ValueError during conversion."""
        # This tests the except (ValueError, IndexError) branch
        assert handler.extract_http_status_code("HTTP/1.1 abc Invalid") is None

    def test_extract_status_code_pattern_matching(self, handler):
        """Test different regex pattern matching."""
        # Test basic pattern
        assert handler.extract_http_status_code("Response: 401") == 401

        # Test HTTP protocol pattern
        assert handler.extract_http_status_code("HTTP/1.0 403 Forbidden") == 403

        # Test status prefix pattern
        assert handler.extract_http_status_code("status:404") == 404


class TestClassifyError:
    """Test error classification based on patterns."""

    @pytest.fixture
    def handler(self):
        """Get ErrorHandler instance."""
        return ErrorHandler()

    def test_classify_authentication_errors(self, handler):
        """Test classification of authentication errors."""
        assert handler.classify_error("401 Unauthorized") == "authentication"
        assert handler.classify_error("403 Forbidden") == "authentication"
        assert handler.classify_error("Error: authentication required") == "authentication"
        assert handler.classify_error("access denied to registry") == "authentication"
        assert handler.classify_error("Token has expired") == "authentication"

    def test_classify_authentication_error_patterns(self, handler):
        """Test all authentication error patterns."""
        auth_test_cases = [
            "401 Unauthorized",
            "403 Forbidden",
            "authentication required",
            "access denied",
            "unauthorized access",
            "permission denied",
            "credentials are invalid",
            "token has expired",
        ]
        for test_case in auth_test_cases:
            assert handler.classify_error(test_case) == "authentication", f"Failed for: {test_case}"

    def test_classify_not_found_errors(self, handler):
        """Test classification of not found errors."""
        assert handler.classify_error("404 Not Found") == "not_found"
        assert handler.classify_error("package not found in registry") == "not_found"
        assert handler.classify_error("manifest unknown") == "not_found"
        assert handler.classify_error("no such package") == "not_found"

    def test_classify_not_found_error_patterns(self, handler):
        """Test all not found error patterns."""
        not_found_test_cases = [
            "404 Not Found",
            "package not found",
            "manifest unknown in registry",
            "not found in registry",
            "no such image package",
            "image does not exist",
        ]
        for test_case in not_found_test_cases:
            assert handler.classify_error(test_case) == "not_found", f"Failed for: {test_case}"

    def test_classify_network_errors(self, handler):
        """Test classification of network errors."""
        assert handler.classify_error("connection refused") == "network"
        assert handler.classify_error("connection timeout") == "network"
        assert handler.classify_error("network unreachable") == "network"
        assert handler.classify_error("could not resolve host") == "network"

    def test_classify_network_error_patterns(self, handler):
        """Test all network error patterns."""
        network_test_cases = [
            "connection refused by server",
            "connection timeout occurred",
            "network is unreachable",
            "dial tcp connection timeout",
            "no route to host",
            "temporary failure in name resolution",
            "could not resolve host name",
        ]
        for test_case in network_test_cases:
            assert handler.classify_error(test_case) == "network", f"Failed for: {test_case}"

    def test_classify_registry_errors(self, handler):
        """Test classification of registry server errors."""
        assert handler.classify_error("500 Internal Server Error") == "registry"
        assert handler.classify_error("502 Bad Gateway") == "registry"
        assert handler.classify_error("503 Service Unavailable") == "registry"

    def test_classify_registry_error_patterns(self, handler):
        """Test all registry error patterns."""
        registry_test_cases = [
            "500 Internal Server Error",
            "501 Not Implemented",
            "502 Bad Gateway",
            "503 Service Unavailable",
            "504 Gateway Timeout",
            "505 HTTP Version Not Supported",
            "internal server error occurred",
            "bad gateway error",
            "service unavailable right now",
            "gateway timeout exceeded",
        ]
        for test_case in registry_test_cases:
            assert handler.classify_error(test_case) == "registry", f"Failed for: {test_case}"

    def test_classify_unknown_errors(self, handler):
        """Test classification of unknown errors."""
        assert handler.classify_error("Something went wrong") == "unknown"
        assert handler.classify_error("Unexpected error") == "unknown"

    def test_classify_case_insensitive(self, handler):
        """Test that classification is case-insensitive."""
        assert handler.classify_error("AUTHENTICATION REQUIRED") == "authentication"
        assert handler.classify_error("Package Not Found") == "not_found"
        assert handler.classify_error("CONNECTION TIMEOUT") == "network"

    def test_classify_error_http_status_fallback_401(self, handler):
        """Test HTTP status code fallback for 401."""
        # Test case with no pattern match but HTTP 401
        assert handler.classify_error("Error code: 401") == "authentication"

    def test_classify_error_http_status_fallback_403(self, handler):
        """Test HTTP status code fallback for 403."""
        assert handler.classify_error("Error code: 403") == "authentication"

    def test_classify_error_http_status_fallback_404(self, handler):
        """Test HTTP status code fallback for 404."""
        assert handler.classify_error("Error code: 404") == "not_found"

    def test_classify_error_http_status_fallback_5xx(self, handler):
        """Test HTTP status code fallback for 5xx errors."""
        assert handler.classify_error("Error code: 500") == "registry"
        assert handler.classify_error("Error code: 502") == "registry"
        assert handler.classify_error("Error code: 599") == "registry"

    def test_classify_error_pattern_priority(self, handler):
        """Test that pattern matching takes priority over status code."""
        # Even with a different status code, pattern should win
        assert handler.classify_error("500 authentication required") == "authentication"
        assert handler.classify_error("401 package not found") == "not_found"


class TestParseDownloadError:
    """Test parsing of download errors into specific exception types."""

    @pytest.fixture
    def sample_package(self):
        """Create a sample package config for testing."""
        return PackageConfig(name="test-package", version="1.0.0", architecture="amd64")

    @pytest.fixture
    def handler(self):
        """Get ErrorHandler instance."""
        return ErrorHandler()

    def test_parse_authentication_error_401(self, sample_package, handler):
        """Test parsing of 401 authentication error."""
        error_output = "Error: 401 Unauthorized - authentication required"
        original_error = RuntimeError("Command failed")

        result = handler.parse_download_error(sample_package, error_output, original_error)

        assert isinstance(result, AuthenticationError)
        assert result.package_name == "test-package"
        assert result.package_version == "1.0.0"
        assert result.status_code == 401
        assert "Authentication required" in str(result)

    def test_parse_authentication_error_403(self, sample_package, handler):
        """Test parsing of 403 forbidden error."""
        error_output = "Error: 403 Forbidden - access denied"
        original_error = RuntimeError("Command failed")

        result = handler.parse_download_error(sample_package, error_output, original_error)

        assert isinstance(result, AuthenticationError)
        assert result.status_code == 403
        assert "Access forbidden" in str(result)

    def test_parse_authentication_error_without_status_code(self, sample_package, handler):
        """Test parsing of authentication error without explicit status code."""
        error_output = "Error: authentication required"
        original_error = RuntimeError("Command failed")

        result = handler.parse_download_error(sample_package, error_output, original_error)

        assert isinstance(result, AuthenticationError)
        assert result.status_code is None
        assert "Authentication or authorization failed" in str(result)

    def test_parse_not_found_error(self, sample_package, handler):
        """Test parsing of package not found error."""
        error_output = "Error: 404 Not Found - package not found in registry"
        original_error = RuntimeError("Command failed")

        result = handler.parse_download_error(sample_package, error_output, original_error)

        assert isinstance(result, PackageNotFoundError)
        assert result.package_name == "test-package"
        assert result.package_version == "1.0.0"
        assert result.architecture == "amd64"
        assert "not found" in str(result).lower()

    def test_parse_network_error(self, sample_package, handler):
        """Test parsing of network error."""
        error_output = "Error: connection timeout - could not reach registry"
        original_error = RuntimeError("Command failed")

        result = handler.parse_download_error(sample_package, error_output, original_error)

        assert isinstance(result, NetworkError)
        assert result.package_name == "test-package"
        assert "Network error" in str(result)

    def test_parse_registry_error(self, sample_package, handler):
        """Test parsing of registry server error."""
        error_output = "Error: 500 Internal Server Error"
        original_error = RuntimeError("Command failed")

        result = handler.parse_download_error(sample_package, error_output, original_error)

        assert isinstance(result, RegistryError)
        assert result.status_code == 500
        assert "Registry server error" in str(result)

    def test_parse_unknown_error(self, sample_package, handler):
        """Test parsing of unknown error type."""
        error_output = "Something unexpected happened"
        original_error = RuntimeError("Command failed")

        result = handler.parse_download_error(sample_package, error_output, original_error)

        assert isinstance(result, DownloadError)
        assert not isinstance(result, (AuthenticationError, PackageNotFoundError, NetworkError, RegistryError))
        assert result.package_name == "test-package"

    def test_parse_unknown_error_truncates_output(self, sample_package, handler):
        """Test that unknown error truncates long output to 200 chars."""
        error_output = "x" * 500  # 500 character error message
        original_error = RuntimeError("Command failed")

        result = handler.parse_download_error(sample_package, error_output, original_error)

        assert isinstance(result, DownloadError)
        # Message should contain truncated output (200 chars)
        assert "Unknown error occurred. Output: " + ("x" * 200) in result.message

    def test_parse_error_preserves_original(self, sample_package, handler):
        """Test that original error is preserved in parsed exception."""
        error_output = "401 Unauthorized"
        original_error = RuntimeError("Command failed with exit code 1")

        result = handler.parse_download_error(sample_package, error_output, original_error)

        assert result.original_error == original_error
        assert "Original error" in str(result)


class TestPackageDownloadErrorHierarchy:
    """Test exception hierarchy and attributes."""

    def test_base_exception_attributes(self):
        """Test base DownloadError attributes."""
        error = DownloadError(
            package_name="test-pkg",
            package_version="2.0.0",
            message="Test error",
            original_error=ValueError("Original"),
        )

        assert error.package_name == "test-pkg"
        assert error.package_version == "2.0.0"
        assert error.message == "Test error"
        assert isinstance(error.original_error, ValueError)

    def test_authentication_error_inheritance(self):
        """Test that AuthenticationError inherits from DownloadError."""
        error = AuthenticationError(
            package_name="test-pkg",
            package_version="1.0.0",
            status_code=401,
        )

        assert isinstance(error, DownloadError)
        assert isinstance(error, AuthenticationError)

    def test_authentication_error_401_message(self):
        """Test AuthenticationError message for 401."""
        error = AuthenticationError(
            package_name="test-pkg",
            package_version="1.0.0",
            status_code=401,
        )

        assert "Authentication required" in str(error)
        assert "registry credentials" in str(error)

    def test_authentication_error_403_message(self):
        """Test AuthenticationError message for 403."""
        error = AuthenticationError(
            package_name="test-pkg",
            package_version="1.0.0",
            status_code=403,
        )

        assert "Access forbidden" in str(error)
        assert "permission" in str(error)

    def test_authentication_error_generic_message(self):
        """Test AuthenticationError message for other status codes."""
        error = AuthenticationError(
            package_name="test-pkg",
            package_version="1.0.0",
            status_code=None,
        )

        assert "Authentication or authorization failed" in str(error)

    def test_not_found_error_with_architecture(self):
        """Test PackageNotFoundError includes architecture info."""
        error = PackageNotFoundError(
            package_name="test-pkg",
            package_version="1.0.0",
            architecture="arm64",
        )

        assert error.architecture == "arm64"
        assert "arm64" in str(error)

    def test_not_found_error_without_architecture(self):
        """Test PackageNotFoundError without architecture."""
        error = PackageNotFoundError(
            package_name="test-pkg",
            package_version="1.0.0",
            architecture=None,
        )

        assert error.architecture is None
        error_str = str(error)
        assert "Package not found" in error_str
        assert "Verify the package name and version are correct" in error_str

    def test_network_error_message(self):
        """Test NetworkError message."""
        error = NetworkError(
            package_name="test-pkg",
            package_version="1.0.0",
        )

        error_str = str(error)
        assert "Network error occurred" in error_str
        assert "internet connection" in error_str

    def test_registry_error_status_code(self):
        """Test RegistryError includes status code."""
        error = RegistryError(
            package_name="test-pkg",
            package_version="1.0.0",
            status_code=503,
        )

        assert error.status_code == 503
        assert "503" in str(error)

    def test_registry_error_message_format(self):
        """Test RegistryError message formatting."""
        error = RegistryError(
            package_name="test-pkg",
            package_version="1.0.0",
            status_code=502,
        )

        error_str = str(error)
        assert "Registry server error" in error_str
        assert "HTTP 502" in error_str
        assert "experiencing issues" in error_str

    def test_error_message_formatting(self):
        """Test that error messages are properly formatted."""
        error = AuthenticationError(
            package_name="my-package",
            package_version="3.2.1",
            status_code=401,
        )

        error_str = str(error)
        assert "my-package" in error_str
        assert "3.2.1" in error_str
        assert "Authentication required" in error_str

    def test_download_error_with_original_error(self):
        """Test DownloadError formatting with original error."""
        original = ValueError("Invalid value")
        error = DownloadError(
            package_name="test-pkg",
            package_version="1.0.0",
            message="Download failed",
            original_error=original,
        )

        error_str = str(error)
        assert "Download failed" in error_str
        assert "Original error: Invalid value" in error_str

    def test_download_error_without_original_error(self):
        """Test DownloadError formatting without original error."""
        error = DownloadError(
            package_name="test-pkg",
            package_version="1.0.0",
            message="Download failed",
            original_error=None,
        )

        error_str = str(error)
        assert "Download failed" in error_str
        assert "Original error" not in error_str


class TestErrorPatterns:
    """Test ERROR_PATTERNS constant and regex patterns."""

    def test_error_patterns_structure(self):
        """Test that ERROR_PATTERNS has expected structure."""
        assert "authentication" in ERROR_PATTERNS
        assert "not_found" in ERROR_PATTERNS
        assert "network" in ERROR_PATTERNS
        assert "registry" in ERROR_PATTERNS

    def test_authentication_patterns_count(self):
        """Test authentication patterns list."""
        auth_patterns = ERROR_PATTERNS["authentication"]
        assert len(auth_patterns) >= 8  # Should have at least 8 patterns

    def test_not_found_patterns_count(self):
        """Test not found patterns list."""
        not_found_patterns = ERROR_PATTERNS["not_found"]
        assert len(not_found_patterns) >= 6  # Should have at least 6 patterns

    def test_network_patterns_count(self):
        """Test network patterns list."""
        network_patterns = ERROR_PATTERNS["network"]
        assert len(network_patterns) >= 7  # Should have at least 7 patterns

    def test_registry_patterns_count(self):
        """Test registry patterns list."""
        registry_patterns = ERROR_PATTERNS["registry"]
        assert len(registry_patterns) >= 5  # Should have at least 5 patterns

    def test_patterns_are_compiled_regex(self):
        """Test that all patterns are compiled regex objects."""
        import re

        for error_type, patterns in ERROR_PATTERNS.items():
            for pattern in patterns:
                assert isinstance(pattern, re.Pattern), f"Pattern in {error_type} is not compiled regex"

    def test_patterns_case_insensitive(self):
        """Test that all patterns use case-insensitive matching."""
        import re

        for error_type, patterns in ERROR_PATTERNS.items():
            for pattern in patterns:
                assert pattern.flags & re.IGNORECASE, f"Pattern in {error_type} is not case-insensitive"


class TestErrorHandlerEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def handler(self):
        """Get ErrorHandler instance."""
        return ErrorHandler()

    def test_empty_error_output(self, handler):
        """Test handling of empty error output."""
        assert handler.extract_http_status_code("") is None
        assert handler.classify_error("") == "unknown"

    def test_whitespace_only_error_output(self, handler):
        """Test handling of whitespace-only error output."""
        assert handler.extract_http_status_code("   ") is None
        assert handler.classify_error("   ") == "unknown"

    def test_multiple_error_types_in_output(self, handler):
        """Test that first matching pattern wins."""
        # Both authentication and not_found keywords, but authentication pattern should match first
        error_output = "401 Unauthorized - package not found"
        assert handler.classify_error(error_output) == "authentication"

    def test_parse_download_error_with_empty_output(self, handler):
        """Test parsing download error with empty output."""
        package = PackageConfig(name="test", version="1.0.0")
        result = handler.parse_download_error(package, "", RuntimeError("Failed"))

        assert isinstance(result, DownloadError)
        assert not isinstance(result, (AuthenticationError, PackageNotFoundError))

    def test_status_code_with_non_numeric_suffix(self, handler):
        """Test status code extraction with non-numeric suffix doesn't match."""
        # The regex pattern uses word boundaries, so "404x" won't match
        assert handler.extract_http_status_code("Error 404x Not Found") is None
        # But "404 " (with space) will match
        assert handler.extract_http_status_code("Error 404 Not Found") == 404

    def test_classify_error_all_categories(self, handler):
        """Test that all error categories can be matched."""
        test_cases = {
            "authentication": "401 Unauthorized",
            "not_found": "404 Not Found",
            "network": "connection timeout",
            "registry": "500 Internal Server Error",
            "unknown": "random error message",
        }

        for expected_type, error_msg in test_cases.items():
            result = handler.classify_error(error_msg)
            assert result == expected_type, f"Failed to classify '{error_msg}' as '{expected_type}'"
