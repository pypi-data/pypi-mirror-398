"""Command executor module with configuration-aware execution.

This module provides an ExecutorManager class for consistent command execution
across the entire application. It integrates with the global configuration
system and provides structured logging for all command executions.

Features:
- Configuration-aware command execution
- Automatic working directory management
- Structured logging with verbosity control
- Thread-safe operation
- Comprehensive error handling
- Support for both synchronous execution
- Exponential backoff retry logic for transient failures

Example:
    >>> from cve_report_aggregator.executor import ExecutorManager
    >>> # Execute with global config
    >>> output, error = ExecutorManager.execute(["grype", "--version"])
    >>> if error:
    ...     print(f"Command failed: {error}")

    >>> # Execute with explicit config
    >>> from cve_report_aggregator.config import get_config
    >>> config = get_config()
    >>> output, error = ExecutorManager.execute(
    ...     ["git", "status"],
    ...     cwd="/tmp",
    ...     config=config
    ... )

    >>> # Execute with custom retry settings
    >>> output, error = ExecutorManager.execute(
    ...     ["grype", "--version"],
    ...     max_retries=5,
    ...     initial_delay=2.0,
    ...     config=config
    ... )
"""

from __future__ import annotations

import random
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from .logging import get_logger

if TYPE_CHECKING:
    from .models import AggregatorConfig

logger = get_logger(__name__)


# =============================================================================
# Configuration and Constants
# =============================================================================


@dataclass
class RetryConfig:
    """Configuration for retry behavior with exponential backoff."""

    max_retries: int
    initial_delay: float
    max_delay: float
    backoff_multiplier: float
    jitter_factor: float

    @classmethod
    def default(cls) -> RetryConfig:
        """Create default retry configuration."""
        return cls(
            max_retries=3,
            initial_delay=1.0,
            max_delay=30.0,
            backoff_multiplier=2.0,
            jitter_factor=0.1,
        )


# Exit codes that indicate transient failures worth retrying
RETRYABLE_EXIT_CODES = frozenset(
    {
        # Network-related errors
        124,  # Timeout
        125,  # Container runtime errors
        126,  # Command invoked cannot execute
        # Connection errors
        7,  # curl: couldn't connect to host
        28,  # curl: connection timeout
        35,  # curl: SSL connection error
        52,  # curl: empty reply from server
        56,  # curl: failure in receiving network data
        # Registry/download errors
        137,  # SIGKILL (OOM or resource exhaustion)
        143,  # SIGTERM (graceful shutdown interrupted)
    }
)

# Error message indicators for transient failures
TRANSIENT_ERROR_INDICATORS = (
    # Network-related errors
    "connection refused",
    "connection reset",
    "connection timeout",
    "timeout",
    "temporary failure",
    "service unavailable",
    "too many requests",
    "rate limit",
    "socket error",
    "network error",
    "dns resolution",
    "no route to host",
    "host unreachable",
    "broken pipe",
    "connection aborted",
    # TLS/SSL errors
    "ssl error",
    "ssl:",
    "tls:",
    "tls handshake",
    "bad record mac",
    "certificate verify failed",
    "x509:",
    "cert_chain",
    # Registry-specific errors
    "registry unavailable",
    "manifest unknown",
    "blob upload unknown",
    "layer download",
    "unexpected eof",
    "incomplete read",
    # Resource exhaustion
    "out of memory",
    "disk quota exceeded",
    "no space left",
)

# OS error numbers that are retryable
RETRYABLE_ERRNOS = frozenset({11, 35, 4, 60, 61, 110, 111})


# =============================================================================
# Error Classification
# =============================================================================


def _is_retryable_error(error: Exception) -> bool:
    """Determine if an error is transient and worth retrying.

    Args:
        error: The exception that occurred

    Returns:
        True if the error is transient and should be retried
    """
    # FileNotFoundError is not retryable - command doesn't exist
    if isinstance(error, FileNotFoundError):
        return False

    # CalledProcessError - check exit code
    if isinstance(error, subprocess.CalledProcessError):
        return _is_retryable_process_error(error)

    # TimeoutExpired is retryable
    if isinstance(error, subprocess.TimeoutExpired):
        return True

    # OSError and IOError may be retryable
    if isinstance(error, OSError | IOError):
        return _is_retryable_os_error(error)

    # Default: don't retry unknown errors
    return False


def _is_retryable_process_error(error: subprocess.CalledProcessError) -> bool:
    """Check if a CalledProcessError is retryable.

    Args:
        error: The CalledProcessError to check

    Returns:
        True if the error is transient
    """
    # Retry on specific exit codes
    if error.returncode in RETRYABLE_EXIT_CODES:
        return True

    # Check error message for transient failure indicators
    error_output = (error.stderr or "") + (error.stdout or "")
    error_output_lower = error_output.lower()

    return any(indicator in error_output_lower for indicator in TRANSIENT_ERROR_INDICATORS)


def _is_retryable_os_error(error: OSError | IOError) -> bool:
    """Check if an OSError/IOError is retryable.

    Args:
        error: The OS error to check

    Returns:
        True if the error is transient
    """
    if hasattr(error, "errno") and error.errno in RETRYABLE_ERRNOS:
        return True
    return False


# =============================================================================
# Backoff Calculation
# =============================================================================


def _calculate_backoff_delay(retry_config: RetryConfig, attempt: int) -> float:
    """Calculate exponential backoff delay with jitter.

    Args:
        retry_config: Retry configuration
        attempt: Current retry attempt (0-based)

    Returns:
        Delay in seconds before next retry
    """
    # Exponential backoff: initial_delay * (multiplier ^ attempt)
    delay = retry_config.initial_delay * (retry_config.backoff_multiplier**attempt)

    # Cap at max_delay
    delay = min(delay, retry_config.max_delay)

    # Add random jitter to prevent thundering herd
    jitter = delay * retry_config.jitter_factor * (2 * random.random() - 1)
    delay += jitter

    # Ensure delay is never negative
    return max(0.0, delay)


def _wait_with_backoff(retry_config: RetryConfig, attempt: int) -> None:
    """Wait for the calculated backoff delay.

    Args:
        retry_config: Retry configuration
        attempt: Current retry attempt (0-based)
    """
    delay = _calculate_backoff_delay(retry_config, attempt)

    logger.debug(
        "Waiting before retry",
        delay_seconds=round(delay, 2),
        attempt=attempt,
    )

    time.sleep(delay)


# =============================================================================
# Logging Helpers
# =============================================================================


def _log_execution_attempt(
    command: list[str],
    working_dir: str | None,
    attempt: int,
    max_retries: int,
    is_debug: bool,
) -> None:
    """Log command execution attempt.

    Args:
        command: Command being executed
        working_dir: Working directory
        attempt: Current attempt (0-based)
        max_retries: Maximum retries
        is_debug: Whether debug mode is enabled
    """
    if attempt == 0:
        if is_debug:
            logger.debug("Executing command", command=" ".join(command), cwd=working_dir)
        else:
            logger.info("Executing command", command=" ".join(command))
    else:
        logger.info(
            "Retrying command execution",
            command=" ".join(command),
            attempt=attempt,
            max_retries=max_retries,
        )


def _log_success_after_retry(command: list[str], attempt: int) -> None:
    """Log successful command execution after retry.

    Args:
        command: Command that succeeded
        attempt: Successful attempt number
    """
    if attempt > 0:
        logger.info(
            "Command succeeded after retry",
            command=" ".join(command),
            attempt=attempt,
        )


# =============================================================================
# Error Handlers
# =============================================================================


def _handle_called_process_error(
    error: subprocess.CalledProcessError,
    command: list[str],
    attempt: int,
    retry_config: RetryConfig,
) -> tuple[str, Exception | None] | None:
    """Handle CalledProcessError with retry logic.

    Args:
        error: The error that occurred
        command: Command that failed
        attempt: Current attempt (0-based)
        retry_config: Retry configuration

    Returns:
        Tuple of (output, error) if should not retry, None if should retry
    """
    is_retryable = _is_retryable_error(error)

    if is_retryable and attempt < retry_config.max_retries:
        logger.warning(
            "Command execution failed with retryable error",
            command=" ".join(command),
            return_code=error.returncode,
            attempt=attempt,
            max_retries=retry_config.max_retries,
            stderr=error.stderr[:200] if error.stderr else None,
        )
        _wait_with_backoff(retry_config, attempt)
        return None  # Signal to retry

    # Log final failure
    logger.error(
        "Command execution failed",
        command=" ".join(command),
        return_code=error.returncode,
        attempt=attempt,
        stderr=error.stderr if error.stderr else None,
    )
    return error.stdout + error.stderr, error


def _handle_timeout_error(
    error: subprocess.TimeoutExpired,
    command: list[str],
    attempt: int,
    retry_config: RetryConfig,
) -> tuple[str, Exception | None] | None:
    """Handle TimeoutExpired with retry logic.

    Args:
        error: The timeout error
        command: Command that timed out
        attempt: Current attempt (0-based)
        retry_config: Retry configuration

    Returns:
        Tuple of (output, error) if should not retry, None if should retry
    """
    if attempt < retry_config.max_retries:
        logger.warning(
            "Command execution timed out",
            command=" ".join(command),
            timeout=error.timeout,
            attempt=attempt,
            max_retries=retry_config.max_retries,
        )
        _wait_with_backoff(retry_config, attempt)
        return None  # Signal to retry

    logger.error(
        "Command execution timed out - max retries exceeded",
        command=" ".join(command),
        timeout=error.timeout,
        attempt=attempt,
    )
    return "", error


def _handle_generic_error(
    error: Exception,
    command: list[str],
    attempt: int,
    retry_config: RetryConfig,
) -> tuple[str, Exception | None] | None:
    """Handle generic exception with retry logic.

    Args:
        error: The exception that occurred
        command: Command that failed
        attempt: Current attempt (0-based)
        retry_config: Retry configuration

    Returns:
        Tuple of (output, error) if should not retry, None if should retry
    """
    is_retryable = _is_retryable_error(error)

    if is_retryable and attempt < retry_config.max_retries:
        logger.warning(
            "Unexpected error executing command (retryable)",
            command=" ".join(command),
            error=str(error),
            error_type=type(error).__name__,
            attempt=attempt,
            max_retries=retry_config.max_retries,
        )
        _wait_with_backoff(retry_config, attempt)
        return None  # Signal to retry

    logger.error(
        "Unexpected error executing command",
        command=" ".join(command),
        error=str(error),
        error_type=type(error).__name__,
        attempt=attempt,
    )
    return "", error


# =============================================================================
# Main Executor Class
# =============================================================================


class ExecutorManager:
    """Centralized command execution manager.

    This class provides a singleton-style interface for executing shell commands
    with consistent error handling, logging, and configuration integration.

    All command execution should go through this manager to ensure:
    - Consistent error handling and logging
    - Configuration-aware defaults (working directory, verbosity)
    - Structured logging of command execution
    - Proper error propagation and reporting
    - Automatic retry with exponential backoff for transient failures
    """

    # Default retry configuration (for backwards compatibility)
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_INITIAL_DELAY = 1.0
    DEFAULT_MAX_DELAY = 30.0
    DEFAULT_BACKOFF_MULTIPLIER = 2.0
    DEFAULT_JITTER_FACTOR = 0.1

    # Expose for external use (backwards compatibility)
    RETRYABLE_EXIT_CODES = RETRYABLE_EXIT_CODES

    @classmethod
    def _is_retryable_error(cls, error: Exception) -> bool:
        """Determine if an error is transient and worth retrying.

        Args:
            error: The exception that occurred

        Returns:
            True if the error is transient and should be retried
        """
        return _is_retryable_error(error)

    @classmethod
    def _calculate_backoff_delay(
        cls,
        attempt: int,
        initial_delay: float,
        max_delay: float,
        backoff_multiplier: float,
        jitter_factor: float,
    ) -> float:
        """Calculate exponential backoff delay with jitter.

        Args:
            attempt: Current retry attempt (0-based)
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            backoff_multiplier: Multiplier for exponential backoff
            jitter_factor: Random jitter factor (0-1)

        Returns:
            Delay in seconds before next retry
        """
        config = RetryConfig(
            max_retries=0,  # Not used in calculation
            initial_delay=initial_delay,
            max_delay=max_delay,
            backoff_multiplier=backoff_multiplier,
            jitter_factor=jitter_factor,
        )
        return _calculate_backoff_delay(config, attempt)

    @classmethod
    def _build_retry_config(
        cls,
        max_retries: int | None,
        initial_delay: float | None,
        max_delay: float | None,
        backoff_multiplier: float | None,
    ) -> RetryConfig:
        """Build retry configuration with defaults.

        Args:
            max_retries: Max retries override
            initial_delay: Initial delay override
            max_delay: Max delay override
            backoff_multiplier: Backoff multiplier override

        Returns:
            Complete RetryConfig
        """
        return RetryConfig(
            max_retries=max_retries if max_retries is not None else cls.DEFAULT_MAX_RETRIES,
            initial_delay=initial_delay if initial_delay is not None else cls.DEFAULT_INITIAL_DELAY,
            max_delay=max_delay if max_delay is not None else cls.DEFAULT_MAX_DELAY,
            backoff_multiplier=backoff_multiplier if backoff_multiplier is not None else cls.DEFAULT_BACKOFF_MULTIPLIER,
            jitter_factor=cls.DEFAULT_JITTER_FACTOR,
        )

    @classmethod
    def _determine_working_dir(
        cls,
        cwd: str | Path | None,
        config: AggregatorConfig | None,
    ) -> str | None:
        """Determine working directory for command execution.

        Args:
            cwd: Explicit working directory
            config: Optional configuration

        Returns:
            Working directory as string, or None
        """
        working_dir: str | Path | None = cwd

        if working_dir is None and config is not None:
            working_dir = config.input_dir.parent if hasattr(config, "input_dir") else None

        return str(working_dir) if working_dir else None

    @classmethod
    def _execute_command(
        cls,
        command: list[str],
        working_dir: str | None,
    ) -> subprocess.CompletedProcess[str]:
        """Execute a command and return the result.

        Args:
            command: Command to execute
            working_dir: Working directory

        Returns:
            CompletedProcess result

        Raises:
            subprocess.CalledProcessError: If command fails
            FileNotFoundError: If command not found
            subprocess.TimeoutExpired: If command times out
        """
        return subprocess.run(
            command,
            cwd=working_dir,
            check=True,
            text=True,
            capture_output=True,
        )

    @classmethod
    def execute(
        cls,
        command: list[str],
        cwd: str | Path | None = None,
        config: AggregatorConfig | None = None,
        max_retries: int | None = None,
        initial_delay: float | None = None,
        max_delay: float | None = None,
        backoff_multiplier: float | None = None,
    ) -> tuple[str, Exception | None]:
        """Execute a command in the shell with configuration-aware defaults and retry logic.

        This method executes shell commands with optional working directory and
        configuration context. If a config is provided, it will use config.cwd as
        the default working directory and adjust logging based on config.log_level.

        Implements exponential backoff retry logic for transient failures.

        Args:
            command: The command to execute as a list of strings
            cwd: Working directory for the command (overrides config.cwd if provided)
            config: Optional configuration for defaults (uses global config if None)
            max_retries: Maximum number of retry attempts (default: 3)
            initial_delay: Initial retry delay in seconds (default: 1.0)
            max_delay: Maximum retry delay in seconds (default: 30.0)
            backoff_multiplier: Exponential backoff multiplier (default: 2.0)

        Returns:
            Tuple of (stdout, error) where error is None on success or Exception on failure
        """
        # Build configuration
        retry_config = cls._build_retry_config(max_retries, initial_delay, max_delay, backoff_multiplier)
        working_dir = cls._determine_working_dir(cwd, config)
        is_debug = bool(config and config.log_level == "DEBUG")

        # Track last error for retry logic
        last_error: Exception | None = None

        # Retry loop
        for attempt in range(retry_config.max_retries + 1):
            _log_execution_attempt(command, working_dir, attempt, retry_config.max_retries, is_debug)

            try:
                result = cls._execute_command(command, working_dir)

                if is_debug and result.stdout:
                    logger.debug("Command output", output=result.stdout[:500])

                _log_success_after_retry(command, attempt)
                return result.stdout, None

            except FileNotFoundError as e:
                logger.error("Command not found", command=command[0], error=str(e))
                return "", e

            except subprocess.CalledProcessError as e:
                last_error = e
                handler_result = _handle_called_process_error(e, command, attempt, retry_config)
                if handler_result is not None:
                    return handler_result
                # handler_result is None means retry

            except subprocess.TimeoutExpired as e:
                last_error = e
                handler_result = _handle_timeout_error(e, command, attempt, retry_config)
                if handler_result is not None:
                    return handler_result

            except Exception as e:
                last_error = e
                handler_result = _handle_generic_error(e, command, attempt, retry_config)
                if handler_result is not None:
                    return handler_result

        # All retries exhausted
        logger.error(
            "Command execution failed - all retries exhausted",
            command=" ".join(command),
            max_retries=retry_config.max_retries,
        )

        return "", last_error

    @classmethod
    def execute_with_global_config(
        cls,
        command: list[str],
        cwd: str | Path | None = None,
        max_retries: int | None = None,
        initial_delay: float | None = None,
    ) -> tuple[str, Exception | None]:
        """Execute a command using the global configuration.

        This is a convenience method that automatically uses the global configuration
        if it's been initialized.

        Args:
            command: The command to execute as a list of strings
            cwd: Optional working directory (overrides config.cwd if provided)
            max_retries: Maximum number of retry attempts (default: 3)
            initial_delay: Initial retry delay in seconds (default: 1.0)

        Returns:
            Tuple of (stdout, error) where error is None on success or Exception on failure
        """
        from .config import get_current_config, is_config_initialized

        config: AggregatorConfig | None = None
        if is_config_initialized():
            try:
                config = get_current_config()
            except Exception as e:
                logger.warning("Failed to get global config", error=str(e))

        return cls.execute(
            command,
            cwd=cwd,
            config=config,
            max_retries=max_retries,
            initial_delay=initial_delay,
        )

    @classmethod
    def create_temp_directory(cls, config: AggregatorConfig | None = None) -> tuple[Path, Exception | None]:
        """Create a temporary directory using mktemp.

        Args:
            config: Optional configuration for logging

        Returns:
            Tuple of (temp_dir_path, error) where error is None on success
        """
        output, error = cls.execute(["mktemp", "-d"], config=config)
        if error:
            return Path(), error
        return Path(output.strip()), None


# Public API
__all__ = [
    "ExecutorManager",
    "RetryConfig",
]
