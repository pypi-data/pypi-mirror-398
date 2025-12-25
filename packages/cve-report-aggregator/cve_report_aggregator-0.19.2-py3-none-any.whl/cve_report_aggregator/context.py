"""Application context for dependency injection.

This module provides the AppContext class which holds all shared services
and configuration for the application. This eliminates the need for singletons
and provides explicit dependency injection.

Example:
    >>> from cve_report_aggregator.core.config import AggregatorConfig
    >>> from cve_report_aggregator.context import AppContext
    >>>
    >>> config = AggregatorConfig(...)
    >>> context = AppContext(config)
    >>>
    >>> # Get services from context
    >>> logger = context.get_logger(__name__)
    >>> error_handler = context.error_handler
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .core.error_handler import ErrorHandler
from .core.logging import LogManager

if TYPE_CHECKING:
    from structlog.types import FilteringBoundLogger

    from .core.models import AggregatorConfig


class AppContext:
    """Application-wide context holding shared services and configuration.

    This class provides a centralized location for all shared services,
    eliminating the need for singleton patterns and enabling proper
    dependency injection throughout the application.

    Attributes:
        config: Application configuration
        error_handler: Error classification and parsing service
        _log_manager: Internal LogManager instance (use get_logger() instead)

    Example:
        >>> config = AggregatorConfig(...)
        >>> context = AppContext(config)
        >>>
        >>> # Access services
        >>> logger = context.get_logger(__name__)
        >>> error_handler = context.error_handler
        >>>
        >>> # Pass context to functions
        >>> download_package_sboms(output_dir, context)
    """

    def __init__(self, config: AggregatorConfig) -> None:
        """Initialize application context with configuration.

        Args:
            config: Application configuration

        Example:
            >>> from cve_report_aggregator.core.config import load_settings
            >>> settings = load_settings()
            >>> config = settings.to_aggregator_config()
            >>> context = AppContext(config)
        """
        self.config = config

        # Configure logging based on config
        LogManager.configure(
            log_level=config.log_level,
            use_json=False,  # Always use console format for now
            use_colors=True,  # Enable colors for better readability
        )

        # Create error handler (no longer singleton)
        self.error_handler = ErrorHandler()

    def get_logger(self, name: str | None = None, **context: Any) -> FilteringBoundLogger:
        """Get a configured logger with optional context.

        Args:
            name: Logger name (typically __name__ of the calling module)
            **context: Initial context to bind to the logger

        Returns:
            Configured FilteringBoundLogger instance

        Example:
            >>> context = AppContext(config)
            >>> logger = context.get_logger(__name__)
            >>> logger.info("Processing started")
            >>>
            >>> # With bound context
            >>> logger = context.get_logger(__name__, package="nginx")
            >>> logger.info("Scanning package")  # Includes package="nginx"
        """
        return LogManager.get_logger(name, **context)

    def with_config(self, **config_updates: Any) -> AppContext:
        """Create a new context with updated configuration.

        This is useful for creating temporary contexts with modified
        configuration without mutating the original context.

        Args:
            **config_updates: Configuration fields to update

        Returns:
            New AppContext with updated configuration

        Example:
            >>> original_context = AppContext(config)
            >>> debug_context = original_context.with_config(log_level="DEBUG")
            >>> # original_context unchanged, debug_context has DEBUG level
        """
        from copy import deepcopy

        new_config = deepcopy(self.config)
        for key, value in config_updates.items():
            if hasattr(new_config, key):
                setattr(new_config, key, value)
        return AppContext(new_config)


# Public API
__all__ = [
    "AppContext",
]
