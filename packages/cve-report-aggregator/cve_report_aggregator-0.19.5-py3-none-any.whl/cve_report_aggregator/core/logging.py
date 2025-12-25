"""Centralized logging configuration using structlog.

This module provides a LogManager class for consistent, structured logging
across the entire application. It integrates with the global configuration
system and provides thread-safe logging with contextual information.

Features:
- Structured logging with JSON and console output
- Log level configuration from global config
- Context binding for request/session tracking
- Thread-safe operation
- Rich console output in development
- JSON output for production/parsing

Example:
    >>> from cve_report_aggregator.logging import LogManager
    >>> logger = LogManager.get_logger(__name__)
    >>> logger.info("Processing vulnerability", vuln_id="CVE-2024-12345", severity="High")
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import structlog
from structlog.types import FilteringBoundLogger, Processor

from .config import ConfigurationError, get_current_config, is_config_initialized
from .constants import LogLevel


class LogManager:
    """Centralized logging manager using structlog.

    This class provides a singleton-style interface to structlog configuration
    and logger creation. It integrates with the global configuration to set
    log levels and formats.

    Attributes:
        _configured: Whether structlog has been configured
        _loggers: Cache of created loggers by name
    """

    _configured: bool = False
    _loggers: dict[str, FilteringBoundLogger] = {}

    @classmethod
    def configure(
        cls,
        log_level: str | None = None,
        use_json: bool = False,
        use_colors: bool = True,
    ) -> None:
        """Configure structlog with application-wide settings.

        This should be called once at application startup. If not called
        explicitly, it will be auto-configured on first logger creation.

        Args:
            log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                      If None, uses config.log_level (DEBUG if True, else INFO)
            use_json: Use JSON output format instead of console format
            use_colors: Use colored output (only for console format)

        Example:
            >>> # Explicit configuration at startup
            >>> LogManager.configure(log_level="DEBUG", use_json=False)
            >>> logger = LogManager.get_logger(__name__)
        """
        if cls._configured:
            return

        # Determine log level from config or parameter
        if log_level is None:
            if is_config_initialized():
                try:
                    config = get_current_config()
                    # Use configured log_level, falling back to verbose flag
                    log_level = config.log_level
                except ConfigurationError:
                    log_level = "INFO"
            else:
                log_level = "INFO"

        # Convert string log level to Python logging numeric constant
        # Uses LogLevel enum for proper correlation with Python's logging module
        numeric_level = LogLevel.to_logging_level(log_level)

        # Configure standard library logging to use structlog
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=numeric_level,
        )

        # Build processor chain
        processors: list[Processor] = [
            # Merge contextvars (for log_context functionality)
            structlog.contextvars.merge_contextvars,
            # Add log level to event dict
            structlog.stdlib.add_log_level,
            # Add timestamp
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            # Add stack info for exceptions
            structlog.processors.StackInfoRenderer(),
            # Format exceptions
            structlog.processors.format_exc_info,
            # Decode unicode
            structlog.processors.UnicodeDecoder(),
        ]

        # Add output processor based on format preference
        if use_json:
            # JSON output for production/machine parsing
            processors.append(structlog.processors.JSONRenderer())
        else:
            # Console output for development/human reading
            if use_colors:
                processors.append(
                    structlog.dev.ConsoleRenderer(
                        colors=True,
                        exception_formatter=structlog.dev.plain_traceback,
                    )
                )
            else:
                processors.append(
                    structlog.dev.ConsoleRenderer(
                        colors=False,
                        exception_formatter=structlog.dev.plain_traceback,
                    )
                )

        # Configure structlog
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )

        cls._configured = True

    @classmethod
    def get_logger(
        cls,
        name: str | None = None,
        **initial_context: Any,
    ) -> FilteringBoundLogger:
        """Get a configured structlog logger.

        This method returns a FilteringBoundLogger with the specified name
        and initial context. Loggers are cached by name for efficiency.

        Args:
            name: Logger name (typically __name__ of the calling module)
            **initial_context: Initial context to bind to the logger

        Returns:
            Configured FilteringBoundLogger instance

        Example:
            >>> logger = LogManager.get_logger(__name__, component="scanner")
            >>> logger.info("Scanning image", image="nginx:1.21")

            >>> # Logger with context binding
            >>> logger = LogManager.get_logger(__name__)
            >>> logger = logger.bind(request_id="abc-123")
            >>> logger.info("Processing request")  # Includes request_id
        """
        # Auto-configure if not already configured
        if not cls._configured:
            cls.configure()

        # Use provided name or default to root logger
        logger_name = name or "cve_report_aggregator"

        # Check cache
        if logger_name in cls._loggers and not initial_context:
            return cls._loggers[logger_name]

        # Create new logger
        logger: FilteringBoundLogger = structlog.get_logger(logger_name)

        # Bind initial context if provided
        if initial_context:
            logger = logger.bind(**initial_context)
        else:
            # Cache logger without context
            cls._loggers[logger_name] = logger

        return logger

    @classmethod
    def reset(cls) -> None:
        """Reset LogManager state.

        This is primarily useful for testing to ensure clean state
        between test cases. Should not be called in production code.

        Example:
            >>> # In test teardown
            >>> def teardown():
            ...     LogManager.reset()
        """
        cls._configured = False
        cls._loggers.clear()

    @classmethod
    @contextmanager
    def log_context(cls, **context: Any) -> Generator[None]:
        """Context manager for temporarily binding context to all loggers.

        This uses structlog's contextvars integration to bind context
        that will be included in all log messages within the context.

        Args:
            **context: Context key-value pairs to bind

        Yields:
            None

        Example:
            >>> with LogManager.log_context(request_id="abc-123"):
            ...     logger = LogManager.get_logger(__name__)
            ...     logger.info("Processing")  # Includes request_id
            ...     other_module.process()  # Also includes request_id
        """
        bound_context = structlog.contextvars.bind_contextvars(**context)
        try:
            yield
        finally:
            structlog.contextvars.unbind_contextvars(*bound_context.keys())

    @classmethod
    def get_log_level(cls) -> str:
        """Get the current log level from configuration.

        Returns:
            Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)

        Example:
            >>> level = LogManager.get_log_level()
            >>> print(f"Current log level: {level}")
        """
        if is_config_initialized():
            try:
                config = get_current_config()
                return config.log_level
            except ConfigurationError:
                pass
        return "INFO"

    @classmethod
    def set_log_level(cls, level: str) -> None:
        """Dynamically change the log level.

        Args:
            level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

        Example:
            >>> LogManager.set_log_level("DEBUG")
            >>> logger = LogManager.get_logger(__name__)
            >>> logger.debug("This will now be shown")
        """
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger().setLevel(numeric_level)

        # Update all existing bound loggers' minimum level
        for logger in cls._loggers.values():
            if hasattr(logger, "_min_level"):
                # Access internal attribute - ty doesn't recognize this as a valid assignment
                logger._min_level = int(numeric_level)  # type: ignore[misc]


# Convenience function for common use case
def get_logger(name: str | None = None, **context: Any) -> FilteringBoundLogger:
    """Convenience function to get a logger.

    This is a shorthand for LogManager.get_logger() for easier imports.

    Args:
        name: Logger name (typically __name__)
        **context: Initial context to bind

    Returns:
        Configured FilteringBoundLogger instance

    Example:
        >>> from cve_report_aggregator.logging import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
    """
    return LogManager.get_logger(name, **context)


# Public API
__all__ = [
    "LogManager",
    "get_logger",
]
