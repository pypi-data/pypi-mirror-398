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
from pathlib import Path
from typing import TYPE_CHECKING

from .logging import get_logger

if TYPE_CHECKING:
    from .models import AggregatorConfig

logger = get_logger(__name__)


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

    # Default retry configuration
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_INITIAL_DELAY = 1.0  # seconds
    DEFAULT_MAX_DELAY = 30.0  # seconds
    DEFAULT_BACKOFF_MULTIPLIER = 2.0
    DEFAULT_JITTER_FACTOR = 0.1  # 10% jitter

    # Exit codes that indicate transient failures worth retrying
    RETRYABLE_EXIT_CODES = {
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

    @classmethod
    def _is_retryable_error(cls, error: Exception) -> bool:
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
            # Retry on specific exit codes
            if error.returncode in cls.RETRYABLE_EXIT_CODES:
                return True

            # Check error message for transient failure indicators
            error_output = (error.stderr or "") + (error.stdout or "")
            error_output_lower = error_output.lower()

            # Network-related errors
            transient_indicators = [
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
            ]

            return any(indicator in error_output_lower for indicator in transient_indicators)

        # TimeoutExpired is retryable
        if isinstance(error, subprocess.TimeoutExpired):
            return True

        # OSError and IOError may be retryable
        if isinstance(error, OSError | IOError):
            # Check errno if available
            if hasattr(error, "errno"):
                # EAGAIN, EWOULDBLOCK, EINTR, ETIMEDOUT, ECONNREFUSED, etc.
                retryable_errnos = {11, 35, 4, 60, 61, 110, 111}
                if error.errno in retryable_errnos:
                    return True

        # Default: don't retry unknown errors
        return False

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
        # Exponential backoff: initial_delay * (multiplier ^ attempt)
        delay = initial_delay * (backoff_multiplier**attempt)

        # Cap at max_delay
        delay = min(delay, max_delay)

        # Add random jitter to prevent thundering herd
        # Jitter is +/- jitter_factor of the delay
        jitter = delay * jitter_factor * (2 * random.random() - 1)
        delay += jitter

        # Ensure delay is never negative
        return max(0.0, delay)

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

        Implements exponential backoff retry logic for transient failures. Only errors
        that are deemed transient (network issues, timeouts, resource exhaustion) will
        be retried. Permanent errors (command not found, invalid arguments) will fail
        immediately.

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

        Example:
            >>> # Use global config (if initialized)
            >>> output, error = ExecutorManager.execute(["ls", "-la"])
            >>> if error:
            ...     print(f"Command failed: {error}")

            >>> # Provide explicit config
            >>> from .config import get_config
            >>> config = get_config()
            >>> output, error = ExecutorManager.execute(["grype", "--version"], config=config)

            >>> # Override working directory
            >>> output, error = ExecutorManager.execute(
            ...     ["git", "status"],
            ...     cwd="/tmp",
            ...     config=config
            ... )

            >>> # Custom retry settings for flaky operations
            >>> output, error = ExecutorManager.execute(
            ...     ["uds", "zarf", "package", "list", "oci://registry.example.com/org"],
            ...     max_retries=5,
            ...     initial_delay=2.0,
            ...     config=config
            ... )
        """
        # Use default retry settings if not provided
        max_retries = max_retries if max_retries is not None else cls.DEFAULT_MAX_RETRIES
        initial_delay = initial_delay if initial_delay is not None else cls.DEFAULT_INITIAL_DELAY
        max_delay = max_delay if max_delay is not None else cls.DEFAULT_MAX_DELAY
        backoff_multiplier = backoff_multiplier if backoff_multiplier is not None else cls.DEFAULT_BACKOFF_MULTIPLIER
        jitter_factor = cls.DEFAULT_JITTER_FACTOR

        # Determine working directory
        working_dir: str | Path | None = cwd
        if working_dir is None and config is not None:
            # Use config.cwd as fallback if no explicit cwd provided
            # Note: We use Path.cwd() from config, but it's already a Path
            working_dir = config.input_dir.parent if hasattr(config, "input_dir") else None

        # Convert Path to string for subprocess
        working_dir_str: str | None = str(working_dir) if working_dir else None

        # Log command execution (structlog will handle verbosity via config)
        is_debug = config and config.log_level == "DEBUG"

        # Track last error for retry logic
        last_error: Exception | None = None

        # Retry loop
        for attempt in range(max_retries + 1):
            # Log attempt
            if attempt == 0:
                if is_debug:
                    logger.debug("Executing command", command=" ".join(command), cwd=working_dir_str)
                else:
                    logger.info("Executing command", command=" ".join(command))
            else:
                logger.info(
                    "Retrying command execution",
                    command=" ".join(command),
                    attempt=attempt,
                    max_retries=max_retries,
                )

            try:
                # Capture stdout and stderr and return them
                result: subprocess.CompletedProcess[str] = subprocess.run(
                    command,
                    cwd=working_dir_str,
                    check=True,
                    text=True,
                    capture_output=True,
                )

                if is_debug and result.stdout:
                    # Log first 500 chars of output
                    logger.debug("Command output", output=result.stdout[:500])

                # Success - return immediately
                if attempt > 0:
                    logger.info(
                        "Command succeeded after retry",
                        command=" ".join(command),
                        attempt=attempt,
                    )

                return result.stdout, None

            except subprocess.CalledProcessError as e:
                last_error = e

                # Check if this error is retryable
                is_retryable = cls._is_retryable_error(e)

                # Log the error
                if is_retryable and attempt < max_retries:
                    logger.warning(
                        "Command execution failed with retryable error",
                        command=" ".join(command),
                        return_code=e.returncode,
                        attempt=attempt,
                        max_retries=max_retries,
                        stderr=e.stderr[:200] if e.stderr else None,
                    )
                else:
                    logger.error(
                        "Command execution failed",
                        command=" ".join(command),
                        return_code=e.returncode,
                        attempt=attempt,
                        stderr=e.stderr if e.stderr else None,
                    )

                # If not retryable or we've exhausted retries, fail immediately
                if not is_retryable or attempt >= max_retries:
                    # Return combined stdout + stderr for error context
                    return e.stdout + e.stderr, e

                # Calculate backoff delay and sleep
                delay = cls._calculate_backoff_delay(
                    attempt=attempt,
                    initial_delay=initial_delay,
                    max_delay=max_delay,
                    backoff_multiplier=backoff_multiplier,
                    jitter_factor=jitter_factor,
                )

                logger.debug(
                    "Waiting before retry",
                    delay_seconds=round(delay, 2),
                    attempt=attempt,
                )

                time.sleep(delay)

            except FileNotFoundError as e:
                # Command doesn't exist - not retryable
                logger.error("Command not found", command=command[0], error=str(e))
                return "", e

            except subprocess.TimeoutExpired as e:
                last_error = e

                # Timeout is retryable
                if attempt < max_retries:
                    logger.warning(
                        "Command execution timed out",
                        command=" ".join(command),
                        timeout=e.timeout,
                        attempt=attempt,
                        max_retries=max_retries,
                    )

                    # Calculate backoff delay and sleep
                    delay = cls._calculate_backoff_delay(
                        attempt=attempt,
                        initial_delay=initial_delay,
                        max_delay=max_delay,
                        backoff_multiplier=backoff_multiplier,
                        jitter_factor=jitter_factor,
                    )

                    logger.debug(
                        "Waiting before retry",
                        delay_seconds=round(delay, 2),
                        attempt=attempt,
                    )

                    time.sleep(delay)
                else:
                    logger.error(
                        "Command execution timed out - max retries exceeded",
                        command=" ".join(command),
                        timeout=e.timeout,
                        attempt=attempt,
                    )
                    return "", e

            except Exception as e:
                last_error = e

                # Check if this error is retryable
                is_retryable = cls._is_retryable_error(e)

                # Log the error
                if is_retryable and attempt < max_retries:
                    logger.warning(
                        "Unexpected error executing command (retryable)",
                        command=" ".join(command),
                        error=str(e),
                        error_type=type(e).__name__,
                        attempt=attempt,
                        max_retries=max_retries,
                    )

                    # Calculate backoff delay and sleep
                    delay = cls._calculate_backoff_delay(
                        attempt=attempt,
                        initial_delay=initial_delay,
                        max_delay=max_delay,
                        backoff_multiplier=backoff_multiplier,
                        jitter_factor=jitter_factor,
                    )

                    logger.debug(
                        "Waiting before retry",
                        delay_seconds=round(delay, 2),
                        attempt=attempt,
                    )

                    time.sleep(delay)
                else:
                    logger.error(
                        "Unexpected error executing command",
                        command=" ".join(command),
                        error=str(e),
                        error_type=type(e).__name__,
                        attempt=attempt,
                    )
                    return "", e

        # If we get here, we've exhausted all retries
        logger.error(
            "Command execution failed - all retries exhausted",
            command=" ".join(command),
            max_retries=max_retries,
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
        if it's been initialized. If the global config is not available, it falls back
        to basic execution without config-aware features.

        Args:
            command: The command to execute as a list of strings
            cwd: Optional working directory (overrides config.cwd if provided)
            max_retries: Maximum number of retry attempts (default: 3)
            initial_delay: Initial retry delay in seconds (default: 1.0)

        Returns:
            Tuple of (stdout, error) where error is None on success or Exception on failure

        Example:
            >>> # After initializing global config in main()
            >>> from .config import get_config, set_config
            >>> config = get_config(cli_args={'log_level': 'DEBUG'})
            >>> set_config(config)
            >>>
            >>> # Now execute commands anywhere in the codebase
            >>> output, error = ExecutorManager.execute_with_global_config(["grype", "--version"])
        """
        from .config import get_current_config, is_config_initialized

        # Try to use global config if available
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

        Example:
            >>> temp_dir, error = ExecutorManager.create_temp_directory()
            >>> if not error:
            ...     print(f"Created temp dir: {temp_dir}")
        """
        output, error = cls.execute(["mktemp", "-d"], config=config)
        if error:
            return Path(), error
        return Path(output.strip()), None


# Public API
__all__ = [
    "ExecutorManager",
]
