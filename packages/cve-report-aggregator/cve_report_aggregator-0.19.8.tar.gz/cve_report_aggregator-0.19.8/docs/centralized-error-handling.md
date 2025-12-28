# Centralized Error Handling Architecture

## Overview

The CVE Report Aggregator uses a centralized error handling system based on a Singleton pattern. All error parsing and
classification logic is consolidated in the `core` module, making it accessible and consistent across the entire
application.

## Architecture

### Core Components

#### 1. **ErrorHandler Singleton** (`core/error_handler.py`)

The `ErrorHandler` class implements the Singleton pattern to ensure consistent error handling behavior throughout the
application.

```python
from cve_report_aggregator.core.error_handler import ErrorHandler
from cve_report_aggregator.context import AppContext

# Get error handler from application context
context = AppContext(config)
handler = context.error_handler

# Or get the error handler directly (legacy approach)
handler = ErrorHandler()
```

**Methods:**

- `extract_http_status_code(error_output: str) -> int | None` - Extracts HTTP status codes from error messages
- `classify_error(error_output: str) -> str` - Classifies errors into categories (authentication, not_found, network,
  registry, unknown)
- `parse_download_error(package, error_output, original_error) -> DownloadError` - Parses command output and creates
  appropriate exception

#### 2. **Exception Hierarchy** (`core/exceptions.py`)

All download-related exceptions inherit from `DownloadError`, which itself inherits from the base `CVEAggregatorError`.

```bash
CVEAggregatorError (base for all application errors)
├── ConfigurationError
├── ScannerError
│   ├── ScannerNotFoundError
│   └── ScannerExecutionError
├── ReportError
│   ├── ReportLoadError
│   └── ReportValidationError
├── DownloadError (base for package download errors)
│   ├── AuthenticationError (401/403)
│   ├── PackageNotFoundError (404)
│   ├── NetworkError (connectivity issues)
│   └── RegistryError (5xx server errors)
└── AggregationError
```

### Error Pattern Matching

The ErrorHandler uses comprehensive regex patterns to classify errors:

**Authentication Errors (401/403):**

- "401 Unauthorized", "403 Forbidden"
- "authentication required", "access denied"
- "credentials.\*invalid", "token.\*expired"

**Package Not Found (404):**

- "404 Not Found", "package not found"
- "manifest unknown", "no such.\*package"

**Network Errors:**

- "connection refused", "connection timeout"
- "network.\*unreachable", "could not resolve host"

**Registry Errors (5xx):**

- "50\[0-9\]", "internal server error"
- "bad gateway", "service unavailable"

## Usage Examples

### Basic Error Handling

```python
from cve_report_aggregator.context import AppContext
from cve_report_aggregator.core.config import load_settings
from cve_report_aggregator.core.exceptions import AuthenticationError
from cve_report_aggregator.core.models import PackageConfig

# Initialize application context
settings = load_settings()
config = settings.to_aggregator_config()
context = AppContext(config)

# Get error handler from context
handler = context.error_handler

# Parse error output
package = PackageConfig(name="gitlab", version="18.4.2", architecture="amd64")
error_output = "Error: 401 Unauthorized - authentication required"
original_error = RuntimeError("Command failed")

parsed_error = handler.parse_download_error(package, error_output, original_error)

if isinstance(parsed_error, AuthenticationError):
    print(f"Authentication failed: {parsed_error.message}")
    print(f"Status code: {parsed_error.status_code}")
```

### Application-Level Error Handling

```python
from cve_report_aggregator.core.exceptions import (
    AuthenticationError,
    DownloadError,
    NetworkError,
    PackageNotFoundError,
)
from cve_report_aggregator.io import download_package_sboms

try:
    sbom_files = download_package_sboms(output_dir)
    print(f"Successfully downloaded {len(sbom_files)} SBOM files")

except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")
    # Prompt for credentials or check authentication config

except PackageNotFoundError as e:
    print(f"Package not found: {e.message}")
    print(f"Package: {e.package_name}-{e.package_version}")
    print(f"Architecture: {e.architecture}")
    # Verify package name, version, and architecture

except NetworkError as e:
    print(f"Network error: {e.message}")
    # Check connectivity, retry with backoff

except DownloadError as e:
    # Catch-all for other download errors
    print(f"Download failed: {e.message}")
```

### Custom Error Analysis

```python
from cve_report_aggregator.context import AppContext
from cve_report_aggregator.core.config import load_settings

# Initialize application context
settings = load_settings()
config = settings.to_aggregator_config()
context = AppContext(config)

# Get error handler from context
handler = context.error_handler

# Classify error type
error_message = "404 Not Found - manifest unknown"
error_type = handler.classify_error(error_message)
print(f"Error type: {error_type}")  # Output: not_found

# Extract status code
status_code = handler.extract_http_status_code(error_message)
print(f"HTTP Status: {status_code}")  # Output: 404
```

## Benefits of Centralization

### 1. **Dependency Injection via AppContext**

- **Consistency**: Single source of truth for error handling logic through AppContext
- **Explicit Dependencies**: ErrorHandler provided via AppContext, eliminating hidden dependencies
- **Testability**: Easy to mock and test in isolation by injecting mock context

### 2. **Separation of Concerns**

- Error parsing logic is completely separate from business logic
- Modules don't need to implement their own error classification
- Changes to error patterns only require updates in one place

### 3. **Reusability**

- ErrorHandler can be used across all modules (io, processing, enhance, etc.)
- Same error patterns apply to any command execution
- Consistent error messages and classifications

### 4. **Maintainability**

- All error patterns defined in one location
- Easy to add new error types or patterns
- Clear exception hierarchy for better error handling

## Module Organization

```
src/cve_report_aggregator/
├── context.py                # Application context (dependency injection)
├── core/
│   ├── exceptions.py          # All exception classes
│   ├── error_handler.py       # Error handler (no longer singleton)
│   ├── executor.py           # Command execution
│   ├── config.py             # Configuration management
│   └── models.py             # Data models
├── io/
│   ├── __init__.py           # Package exports
│   ├── downloader.py         # Receives context parameter with error_handler
│   └── report.py
└── processing/
    └── ...
```

## Migration from Old Architecture

### Before (Decentralized)

```python
# Error handling logic scattered across modules
from cve_report_aggregator.io.error_parser import parse_download_error
from cve_report_aggregator.io.exceptions import PackageDownloadError

# Each module had its own error parsing
parsed_error = parse_download_error(package, error_output, original_error)
```

### After (Centralized with Dependency Injection)

```python
# Error handler provided via AppContext
from cve_report_aggregator.context import AppContext
from cve_report_aggregator.core.exceptions import DownloadError

# Initialize context (typically done once at application startup)
context = AppContext(config)

# Access error handler through context
handler = context.error_handler
parsed_error = handler.parse_download_error(package, error_output, original_error)
```

### Backward Compatibility

```python
# Old imports still work (re-exported from io module)
from cve_report_aggregator.io import (
    AuthenticationError,
    PackageNotFoundError,
    # ...
)

# But new code should use core.exceptions
from cve_report_aggregator.core.exceptions import (
    AuthenticationError,
    DownloadError,
    PackageNotFoundError,
    # ...
)
```

## Testing

The centralized architecture makes testing straightforward:

```python
from cve_report_aggregator.context import AppContext
from cve_report_aggregator.core.config import load_settings
from cve_report_aggregator.core.error_handler import ErrorHandler
from cve_report_aggregator.core.models import PackageConfig

def test_error_classification():
    # Can test ErrorHandler directly
    handler = ErrorHandler()

    # Test authentication error
    assert handler.classify_error("401 Unauthorized") == "authentication"

    # Test not found error
    assert handler.classify_error("404 Not Found") == "not_found"

    # Test network error
    assert handler.classify_error("connection timeout") == "network"

def test_error_parsing_with_context():
    # Test through AppContext (integration test)
    settings = load_settings()
    config = settings.to_aggregator_config()
    context = AppContext(config)

    handler = context.error_handler
    package = PackageConfig(name="test", version="1.0.0", architecture="amd64")

    error = handler.parse_download_error(
        package,
        "401 Unauthorized",
        RuntimeError("Command failed")
    )

    assert isinstance(error, AuthenticationError)
    assert error.package_name == "test"
    assert error.status_code == 401
```

## Pre-flight Authentication Validation

The downloader module now includes pre-flight validation to verify registry authentication before attempting any package
downloads. This prevents wasting time and resources on downloads that will fail due to authentication issues.

### How It Works

Before submitting any download tasks to the ThreadPoolExecutor, the `download_package_sboms()` function calls
`validate_registry_authentication()`:

1. **Lightweight API Call**: Executes `uds zarf package list <registry>/<organization>` to test credentials
1. **Early Detection**: Identifies authentication errors (401/403) before attempting downloads
1. **Fail-Fast Behavior**: Raises `AuthenticationError` immediately if credentials are invalid
1. **Graceful Degradation**: Logs warnings for network/registry errors but continues (registry might not support list
   command)

### Example Usage

```python
from cve_report_aggregator.io import download_package_sboms
from cve_report_aggregator.core.exceptions import AuthenticationError

try:
    sbom_files = download_package_sboms(output_dir)
    print(f"Downloaded {len(sbom_files)} SBOM files")
except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")
    print(f"Status code: {e.status_code}")
    # User can fix credentials and retry
```

### Benefits

1. **Resource Efficiency**: Avoids wasting time on downloads that will fail
1. **Better User Experience**: Immediate feedback on authentication issues
1. **Clearer Errors**: User knows exactly what's wrong (credentials) vs ambiguous download failures
1. **Cost Optimization**: Reduces unnecessary API calls to the registry

### Testing

The validation function is thoroughly tested with 8 unit tests covering:

- Successful validation
- Authentication errors (401/403)
- Network errors (continue with warning)
- Registry errors (continue with warning)
- Integration with download flow
- Fail-fast behavior preventing downloads
- Debug mode messaging

## Retry Logic (Implemented)

The `ExecutorManager` now includes automatic retry logic with exponential backoff for transient errors. This integrates
seamlessly with the error handling system.

### Key Features

- **Automatic Retries**: Commands failing with transient errors are retried automatically
- **Exponential Backoff**: Delays increase exponentially (1s, 2s, 4s...) with jitter
- **Smart Classification**: Only transient errors (TLS, network, timeouts) trigger retries
- **Configurable**: Override defaults via `max_retries`, `initial_delay`, `max_delay` parameters

### Retryable Error Patterns

The following patterns trigger automatic retries:

- **TLS/SSL**: `tls:`, `ssl:`, `bad record mac`, `certificate verify failed`
- **Network**: `connection refused`, `timeout`, `dns resolution`, `no route to host`
- **Registry**: `manifest unknown`, `unexpected eof`, `rate limit`

### Usage Example

```python
from cve_report_aggregator.core.executor import ExecutorManager

# Default: 3 retries with exponential backoff
output, error = ExecutorManager.execute(["uds", "zarf", "package", "inspect", "..."])

# Custom retry settings for flaky operations
output, error = ExecutorManager.execute(
    ["uds", "zarf", "package", "inspect", "..."],
    max_retries=5,
    initial_delay=2.0,
)
```

See [Retry Logic Documentation](retry-logic.md) for complete details.

## Future Enhancements

Potential improvements:

1. **Error Metrics**: Track error rates by type for monitoring
1. **Custom Error Handlers**: Allow registering custom error handlers for specific patterns
1. **Error Aggregation**: Summarize common errors across multiple operations
1. **Localization**: Support for error messages in multiple languages
1. **Circuit Breaker**: Stop retrying after consecutive failures

## Best Practices

1. **Use AppContext for dependency injection**: Initialize `AppContext` at application startup and pass it to functions
   that need access to shared services
1. **Catch specific exceptions**: Prefer catching `AuthenticationError` over generic `DownloadError`
1. **Preserve original errors**: Always include `original_error` when creating exceptions
1. **Use structured logging**: Log error type along with error message
1. **Test error paths**: Ensure error handling logic is well-tested
1. **Pass context explicitly**: Functions should receive `context: AppContext` as a parameter rather than using global
   state

## References

- **Implementation**: `src/cve_report_aggregator/core/error_handler.py`
- **Exceptions**: `src/cve_report_aggregator/core/exceptions.py`
- **Tests**: `tests/io/test_error_parser.py`
- **Demo**: `examples/error_handling_demo.py`
- **Original Documentation**: `docs/error-handling-enhancement.md`
