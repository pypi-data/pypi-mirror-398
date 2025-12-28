# Retry Logic for Command Execution

## Overview

The CVE Report Aggregator implements automatic retry logic with exponential backoff for transient failures during
command execution. This ensures resilience against temporary network issues, TLS errors, and registry availability
problems that are common when pulling packages from remote OCI registries.

## Problem Statement

When downloading packages from remote registries, transient failures are common:

- TLS handshake failures (`tls: bad record MAC`)
- Network timeouts and connection resets
- Registry rate limiting
- Temporary S3/storage backend errors
- DNS resolution failures

Without retry logic, these transient errors would cause immediate failures, requiring manual intervention to restart the
aggregation process.

## Solution

The `ExecutorManager` class in `core/executor.py` now implements:

1. **Automatic Retry**: Commands that fail with transient errors are automatically retried
1. **Exponential Backoff**: Delay between retries increases exponentially to avoid overwhelming services
1. **Jitter**: Random variation in delays prevents thundering herd problems
1. **Smart Classification**: Only transient errors trigger retries; permanent errors fail immediately

## Configuration

### Default Settings

```python
DEFAULT_MAX_RETRIES = 3          # Maximum retry attempts
DEFAULT_INITIAL_DELAY = 1.0      # Initial delay in seconds
DEFAULT_MAX_DELAY = 30.0         # Maximum delay cap in seconds
DEFAULT_BACKOFF_MULTIPLIER = 2.0 # Exponential multiplier
DEFAULT_JITTER_FACTOR = 0.1      # 10% random jitter
```

### Retry Timing Example

With default settings, retry delays follow this pattern:

| Attempt | Base Delay | With Jitter (±10%) |
| ------- | ---------- | ------------------ |
| 1       | 1.0s       | 0.9s - 1.1s        |
| 2       | 2.0s       | 1.8s - 2.2s        |
| 3       | 4.0s       | 3.6s - 4.4s        |

## Retryable Errors

### By Exit Code

The following exit codes trigger automatic retries:

| Code | Description                    |
| ---- | ------------------------------ |
| 7    | curl: couldn't connect to host |
| 28   | curl: connection timeout       |
| 35   | curl: SSL connection error     |
| 52   | curl: empty reply from server  |
| 56   | curl: network data failure     |
| 124  | Command timeout                |
| 125  | Container runtime error        |
| 126  | Command cannot execute         |
| 137  | SIGKILL (OOM/resource issue)   |
| 143  | SIGTERM (interrupted)          |

### By Error Message Pattern

Errors containing these patterns (case-insensitive) are considered transient:

**Network Errors:**

- `connection refused`, `connection reset`, `connection timeout`
- `timeout`, `temporary failure`, `service unavailable`
- `socket error`, `network error`, `dns resolution`
- `no route to host`, `host unreachable`, `broken pipe`

**TLS/SSL Errors:**

- `ssl error`, `ssl:`, `tls:`, `tls handshake`
- `bad record mac`, `certificate verify failed`
- `x509:`, `cert_chain`

**Registry Errors:**

- `registry unavailable`, `manifest unknown`
- `blob upload unknown`, `layer download`
- `unexpected eof`, `incomplete read`
- `too many requests`, `rate limit`

**Resource Exhaustion:**

- `out of memory`, `disk quota exceeded`, `no space left`

### Non-Retryable Errors

These errors fail immediately without retries:

- `FileNotFoundError`: Command doesn't exist
- Authentication errors (401/403): Won't succeed with retries
- Package not found (404): Package doesn't exist
- Invalid arguments: Command syntax errors

## Usage

### Basic Usage (Default Retry Settings)

```python
from cve_report_aggregator.core.executor import ExecutorManager

# Uses default settings: 3 retries, 1s initial delay
output, error = ExecutorManager.execute(["grype", "--version"])
```

### Custom Retry Settings

```python
# More retries for flaky registry operations
output, error = ExecutorManager.execute(
    ["uds", "zarf", "package", "inspect", "sbom", "oci://registry.example.com/org/pkg:1.0"],
    max_retries=5,
    initial_delay=2.0,
    max_delay=60.0,
    backoff_multiplier=2.0,
)
```

### Disable Retries

```python
# No retries for operations that should succeed immediately
output, error = ExecutorManager.execute(
    ["echo", "test"],
    max_retries=0,
)
```

### With Configuration Context

```python
from cve_report_aggregator.core.config import get_config

config = get_config()
output, error = ExecutorManager.execute(
    ["uds", "zarf", "package", "list", "oci://registry.example.com/org"],
    config=config,  # Enables DEBUG logging if configured
    max_retries=5,
)
```

## Logging

The retry logic provides comprehensive logging at different levels:

### INFO Level

```bash
Executing command              command='uds zarf package inspect sbom ...'
Retrying command execution     attempt=1 max_retries=3 command='...'
Command succeeded after retry  attempt=2 command='...'
```

### WARNING Level

```bash
Command execution failed with retryable error  attempt=0 return_code=1 stderr='tls: bad record MAC'
```

### ERROR Level

```bash
Command execution failed       attempt=3 return_code=1 stderr='...'
Command execution failed - all retries exhausted  max_retries=3
```

### DEBUG Level

```bash
Waiting before retry  delay_seconds=2.15 attempt=1
```

## Architecture

### Class Structure

```python
class ExecutorManager:
    # Configuration constants
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_INITIAL_DELAY = 1.0
    DEFAULT_MAX_DELAY = 30.0
    DEFAULT_BACKOFF_MULTIPLIER = 2.0
    DEFAULT_JITTER_FACTOR = 0.1
    RETRYABLE_EXIT_CODES = {7, 28, 35, 52, 56, 124, 125, 126, 137, 143}

    @classmethod
    def _is_retryable_error(cls, error: Exception) -> bool:
        """Determine if error is transient and worth retrying."""
        ...

    @classmethod
    def _calculate_backoff_delay(cls, attempt, initial_delay, max_delay, ...) -> float:
        """Calculate exponential backoff delay with jitter."""
        ...

    @classmethod
    def execute(cls, command, cwd=None, config=None, max_retries=None, ...) -> tuple[str, Exception | None]:
        """Execute command with automatic retry logic."""
        ...
```

### Retry Flow

```bash
┌─────────────────────────────────────────────────────────────┐
│                    Execute Command                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Command Succeeds?   │
              └─────┬───────────┬─────┘
                    │           │
                   Yes          No
                    │           │
                    ▼           ▼
            ┌───────────┐  ┌─────────────────────┐
            │  Return   │  │ Is Error Retryable? │
            │  Success  │  └─────┬─────────┬─────┘
            └───────────┘        │         │
                               Yes         No
                                │          │
                                ▼          ▼
                    ┌───────────────┐  ┌───────────┐
                    │ Retries Left? │  │  Return   │
                    └───────┬───────┘  │   Error   │
                        │       │      └───────────┘
                       Yes      No
                        │       │
                        ▼       ▼
              ┌─────────────┐  ┌───────────┐
              │ Wait with   │  │  Return   │
              │  Backoff    │  │   Error   │
              └──────┬──────┘  └───────────┘
                     │
                     ▼
              ┌─────────────┐
              │   Retry     │
              │  Command    │──────────────┐
              └─────────────┘              │
                     ▲                     │
                     └─────────────────────┘
```

## Testing

### Running Tests

```bash
# Run executor tests
uv run pytest tests/core/ -v -k executor

# Run with coverage
uv run pytest tests/core/ --cov=src/cve_report_aggregator/core/executor
```

### Test Scenarios

The retry logic can be tested with simulated failures:

```python
# Test retryable error (TLS)
output, error = ExecutorManager.execute(
    ['sh', '-c', 'echo "tls: bad record MAC" >&2; exit 1'],
    max_retries=2,
    initial_delay=0.1,  # Fast retries for testing
)
# Should retry 2 times before failing

# Test non-retryable error
output, error = ExecutorManager.execute(
    ['nonexistent_command'],
    max_retries=3,
)
# Should fail immediately without retries
```

## Integration with Error Handling

The retry logic integrates with the centralized error handling system:

1. **Pre-retry Classification**: `_is_retryable_error()` determines if retry is worthwhile
1. **Post-failure Parsing**: After retries exhausted, `ErrorHandler.parse_download_error()` provides detailed error info
1. **Structured Logging**: All retry attempts are logged with context for debugging

```python
from cve_report_aggregator.core.error_handler import ErrorHandler
from cve_report_aggregator.core.executor import ExecutorManager

# Execute with retries
output, error = ExecutorManager.execute(command, max_retries=3)

if error:
    # Parse error for detailed classification
    handler = ErrorHandler()
    parsed_error = handler.parse_download_error(package, output, error)
    # Handle specific error type
```

## Best Practices

1. **Use Default Settings**: The defaults work well for most registry operations
1. **Increase Retries for Critical Operations**: Use `max_retries=5` for important downloads
1. **Don't Retry Authentication Errors**: These won't succeed; check credentials instead
1. **Monitor Retry Logs**: Frequent retries may indicate infrastructure issues
1. **Use Config for Debugging**: Pass `config` parameter to enable DEBUG logging

## Performance Considerations

- **Total Wait Time**: With defaults, max wait is ~7 seconds (1 + 2 + 4)
- **Memory**: No significant memory overhead
- **Thread Safety**: `ExecutorManager` methods are thread-safe (classmethod + subprocess)

## Future Enhancements

Potential improvements:

1. **Circuit Breaker**: Stop retrying after consecutive failures
1. **Retry Metrics**: Track retry rates for monitoring
1. **Custom Retry Strategies**: Allow pluggable retry policies
1. **Async Support**: Add async retry support for concurrent operations

## References

- **Implementation**: `src/cve_report_aggregator/core/executor.py`
- **Error Handling**: `docs/centralized-error-handling.md`
- **Error Classification**: `docs/error-handling-enhancement.md`
