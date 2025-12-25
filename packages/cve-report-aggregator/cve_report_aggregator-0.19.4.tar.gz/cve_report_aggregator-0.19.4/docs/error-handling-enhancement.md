# Error Handling Enhancement for Package Pulling

## Overview

This document describes the enhanced error handling system for the Zarf package pulling functionality in the CVE Report
Aggregator. The enhancements enable the application to classify and report specific error types when package downloads
fail, providing users with actionable feedback.

## Problem Statement

Previously, when a package could not be pulled from a registry, the application would return generic error messages that
didn't help users understand the root cause:

- Was authentication missing or invalid? (401/403)
- Did the package not exist? (404)
- Was there a network connectivity issue?
- Was the registry experiencing problems? (5xx)
- Was there a configuration error?

## Solution

The enhanced error handling system introduces:

1. **Specialized Exception Classes**: A hierarchy of exception types for different failure scenarios
1. **Error Parsing Logic**: Pattern matching and HTTP status code extraction from command output
1. **Contextual Error Messages**: Specific, actionable error messages for each error type
1. **Comprehensive Testing**: Unit tests covering all error classification scenarios

## Architecture

### Exception Hierarchy

```bash
Exception
└── PackageDownloadError (base class)
    ├── AuthenticationError (401/403)
    ├── PackageNotFoundError (404)
    ├── NetworkError (connectivity issues)
    ├── RegistryError (5xx server errors)
    └── ConfigurationError (invalid config)
```

### New Modules

#### `src/cve_report_aggregator/io/exceptions.py`

Defines the exception hierarchy with the following classes:

- **`PackageDownloadError`**: Base exception for all download failures

  - Stores: `package_name`, `package_version`, `message`, `original_error`
  - Formats messages consistently with package details

- **`AuthenticationError`**: Authentication/authorization failures

  - Stores: `status_code` (401 or 403)
  - Provides guidance on checking credentials and permissions

- **`PackageNotFoundError`**: Package doesn't exist in registry

  - Stores: `architecture` (optional)
  - Suggests verifying package name, version, registry, and architecture

- **`NetworkError`**: Network connectivity issues

  - Indicates connection problems, timeouts, or DNS failures
  - Suggests checking internet connection and registry availability

- **`RegistryError`**: Registry server errors (5xx)

  - Stores: `status_code` (500-599)
  - Indicates temporary registry issues

- **`ConfigurationError`**: Invalid package configuration

  - Stores: `config_issue` description
  - Reports specific configuration problems

#### `src/cve_report_aggregator/io/error_parser.py`

Provides error parsing and classification utilities:

- **`extract_http_status_code(error_output: str) -> int | None`**

  - Extracts HTTP status codes from error messages
  - Supports multiple formats: basic (404), HTTP protocol (HTTP/1.1 404), status prefix (status: 404)
  - Validates codes are in valid range (100-599)

- **`classify_error(error_output: str) -> str`**

  - Classifies errors into categories: 'authentication', 'not_found', 'network', 'registry', 'unknown'
  - Uses regex pattern matching for common error messages
  - Falls back to HTTP status code analysis

- **`parse_download_error(package, error_output, original_error) -> PackageDownloadError`**

  - Creates appropriate exception subclass based on error classification
  - Preserves original exception for debugging
  - Includes package context in error messages

### Error Pattern Matching

The system recognizes various error patterns:

**Authentication Errors:**

- "401 Unauthorized", "403 Forbidden"
- "authentication required", "access denied"
- "unauthorized", "permission denied"
- "credentials.\*invalid", "token.\*expired"

**Package Not Found Errors:**

- "404 Not Found", "package not found"
- "manifest unknown", "not found in registry"
- "no such.\*package", "does not exist"

**Network Errors:**

- "connection refused", "connection timeout"
- "network.\*unreachable", "dial tcp.\*timeout"
- "no route to host", "temporary failure in name resolution"
- "could not resolve host"

**Registry Errors:**

- "50\[0-9\] " (any 5xx status code)
- "internal server error", "bad gateway"
- "service unavailable", "gateway timeout"

## Integration

### Updated `download_package_sbom()`

```python
# Before: Generic RuntimeError
if error:
    error_msg = f"Failed to download SBOM for {package.name}-{package.version}"
    raise RuntimeError(error_msg) from error

# After: Specific exception with classification
if error:
    parsed_error = parse_download_error(
        package=package,
        error_output=output,
        original_error=error,
    )
    logger.error(
        "SBOM download failed",
        package=package.name,
        version=package.version,
        error_type=type(parsed_error).__name__,
        error=str(parsed_error),
    )
    raise parsed_error
```

### Updated `download_package_sboms()`

Enhanced error reporting in concurrent downloads:

```python
if isinstance(result, Exception):
    error = result
    error_type = type(error).__name__

    logger.error(
        "Package download failed",
        package=package.name,
        version=package.version,
        error_type=error_type,
        error=str(error),
    )

    if is_debug:
        console.print(f"  [red]✗[/red] {package.name}-{package.version}: [{error_type}] {error.message}")
```

## Example Error Messages

### Authentication Error (401)

```bash
Failed to download gitlab-18.4.2-uds.0-unicorn: Authentication required.
Please check your registry credentials.
```

### Package Not Found (404)

```bash
Failed to download gitlab-runner-18.4.0-uds.0-unicorn: Package not found in registry.
Verify the package name and version are correct. Check that the registry and organization
are correct. Verify that architecture 'amd64' is available for this package.
```

### Network Error

```bash
Failed to download headlamp-0.35.0-uds.0-registry1: Network error occurred.
Check your internet connection and registry availability.
```

### Registry Error (503)

```bash
Failed to download gitlab-18.4.2-uds.0-unicorn: Registry server error (HTTP 503).
The registry may be experiencing issues. Please try again later.
```

## Testing

### Test Coverage

24 comprehensive unit tests covering:

- **HTTP Status Code Extraction** (6 tests)

  - Basic format extraction
  - HTTP protocol format
  - Status prefix format
  - Invalid/missing codes
  - Edge cases

- **Error Classification** (6 tests)

  - Authentication errors
  - Not found errors
  - Network errors
  - Registry errors
  - Unknown errors
  - Case-insensitive matching

- **Error Parsing** (7 tests)

  - Authentication error parsing (401, 403)
  - Package not found parsing
  - Network error parsing
  - Registry error parsing
  - Unknown error parsing
  - Original error preservation

- **Exception Hierarchy** (5 tests)

  - Base exception attributes
  - Inheritance verification
  - Architecture inclusion
  - Status code storage
  - Message formatting

### Running Tests

```bash
# Run error parser tests
uv run pytest tests/io/test_error_parser.py -v

# Run with coverage
uv run pytest tests/io/test_error_parser.py --cov=src/cve_report_aggregator/io
```

All tests pass with 77% coverage for error_parser.py and 91% coverage for exceptions.py.

## Benefits

1. **Better User Experience**: Users receive specific, actionable error messages instead of generic failures
1. **Easier Debugging**: Structured logging includes error types and classifications
1. **Programmatic Handling**: Calling code can catch specific exception types and handle them differently
1. **Comprehensive Testing**: 24 unit tests ensure reliable error classification
1. **Maintainability**: Clear separation between error detection, classification, and reporting

## Related Features

### Retry Logic (Implemented)

Automatic retry with exponential backoff is now implemented in `ExecutorManager` for transient errors. See
[Retry Logic Documentation](retry-logic.md) for details.

**Key Features:**

- Automatic retries for TLS errors, network timeouts, and registry issues
- Exponential backoff with jitter (default: 3 retries, 1s initial delay)
- Smart classification: only transient errors trigger retries

## Future Enhancements

Potential improvements for future iterations:

1. **Credential Helpers**: Integrate with Docker/Podman credential helpers for authentication
1. **Error Aggregation**: Summarize common errors across multiple packages
1. **Metrics**: Track error rates by type for monitoring
1. **Documentation Links**: Include links to troubleshooting guides in error messages

## Migration Guide

### For Users

No changes required to existing workflows. Error messages are now more informative and actionable.

### For Developers

When catching package download errors:

```python
# Old approach (still works)
try:
    download_package_sboms(output_dir)
except Exception as e:
    print(f"Download failed: {e}")

# New approach (more specific handling)
from cve_report_aggregator.io import (
    AuthenticationError,
    PackageNotFoundError,
    NetworkError,
)

try:
    download_package_sboms(output_dir)
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
    # Prompt for credentials
except PackageNotFoundError as e:
    print(f"Package not found: {e}")
    # Verify package name/version
except NetworkError as e:
    print(f"Network error: {e}")
    # Check connectivity
```

## References

- Source: `src/cve_report_aggregator/io/`
  - `exceptions.py` - Exception definitions
  - `error_parser.py` - Parsing logic
  - `downloader.py` - Integration
- Tests: `tests/io/test_error_parser.py`
- Related: `src/cve_report_aggregator/core/executor.py` (command execution)
