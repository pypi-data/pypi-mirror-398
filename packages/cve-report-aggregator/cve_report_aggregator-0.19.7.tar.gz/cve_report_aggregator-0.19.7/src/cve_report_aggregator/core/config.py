"""Configuration management using Pydantic Settings with YAML support.

This module provides a comprehensive configuration system that supports:
- CLI arguments (highest priority)
- YAML configuration files
- Environment variables
- Default values (lowest priority)

Configuration precedence (from highest to lowest):
1. CLI arguments
2. YAML configuration file
3. Environment variables
4. Default values

The module also provides a global configuration manager for sharing configuration
across modules in a thread-safe, testable manner.
"""

from __future__ import annotations

import os
import threading
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from pydantic import Field, ValidationInfo, field_validator, model_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, YamlConfigSettingsSource

from .exceptions import ConfigurationError
from .models import AggregatorConfig, EnrichmentConfig, LogLevelType, ModeType, PackageConfig, ScannerType


class AggregatorSettings(BaseSettings):
    """Application settings with support for multiple configuration sources.

    This class extends Pydantic Settings to provide:
    - Environment variable loading with CVE_AGGREGATOR_ prefix
    - YAML file configuration support via YamlConfigSettingsSource
    - Type validation and coercion
    - Configuration merging with proper precedence

    Attributes:
        input_dir: Directory containing scan report files
        output_file: Path for the unified output report
        scanner: Scanner type to use (grype or trivy)
        mode: Aggregation mode for vulnerability processing
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        config_file: Optional path to YAML configuration file
        registry: Container registry URL
        organization: Organization or namespace in the registry
        packages: List of packages to scan
        downloadRemotePackages: Download SBOM reports from remote registry
        localOnly: Only scan local Zarf packages (skip remote downloads)
        enrich: CVE enrichment configuration (nested)
    """

    cwd: Path | None = None
    input_dir: Path | None = Field(default=None, validation_alias="inputDir")
    output_file: Path | None = Field(default=None, validation_alias="outputFile")
    scanner: ScannerType = "grype"
    mode: ModeType = "highest-score"
    log_level: LogLevelType = Field(default="INFO", validation_alias="logLevel")
    config_file: Path | None = Field(default=None, validation_alias="configFile")
    registry: str | None = None
    organization: str | None = None
    packages: list[PackageConfig] = []
    download_remote_packages: bool = Field(default=False, validation_alias="downloadRemotePackages")
    local_only: bool = Field(default=False, validation_alias="localOnly")
    max_workers: int | None = Field(default=None, validation_alias="maxWorkers")

    # CVE enrichment configuration (nested)
    enrich: EnrichmentConfig = Field(
        default_factory=EnrichmentConfig,
        description="CVE enrichment configuration",
    )

    model_config = SettingsConfigDict(
        env_prefix="CVE_AGGREGATOR_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        validate_assignment=True,
        extra="ignore",
        yaml_file=[".cve-aggregator.yaml", ".cve-aggregator.yml"],
        populate_by_name=True,  # Allow both alias and field name
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings sources and their priority order.

        Priority order (highest to lowest):
        1. init_settings - Values passed to __init__ (CLI args)
        2. yaml_settings - YAML configuration file
        3. env_settings - Environment variables
        4. dotenv_settings - .env file
        5. file_secret_settings - Secret files

        Returns:
            Tuple of settings sources in priority order
        """
        return (
            init_settings,
            YamlConfigSettingsSource(settings_cls),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )

    @model_validator(mode="after")
    def set_dynamic_defaults(self) -> AggregatorSettings:
        """Set dynamic defaults based on current working directory.

        This validator runs after all other settings sources and sets defaults
        for paths that are None. This ensures that Path.cwd() is evaluated at
        instance creation time, not at class definition time.

        For Docker convenience: When remote packages are configured and input_dir
        was not explicitly set, it defaults to output_file.parent / "reports"
        instead of cwd() / "reports". This allows users to mount a single output
        directory in Docker containers.

        Returns:
            Self with defaults applied
        """
        # Set cwd if not provided
        if self.cwd is None:
            self.cwd = Path.cwd()

        # Set output_file default if not provided (must be set before input_dir logic)
        if self.output_file is None:
            self.output_file = self.cwd / "unified-report.json"

        # Set input_dir default based on whether remote packages are configured
        if self.input_dir is None:
            # If packages are configured (remote package download), default to output_dir/reports
            # This makes Docker usage more convenient - only need to mount output directory
            if self.packages:
                output_dir = self.output_file.parent
                self.input_dir = output_dir / "reports"
                # Create the directory to ensure it exists
                self.input_dir.mkdir(parents=True, exist_ok=True)
            else:
                # For local-only scanning, keep traditional default
                self.input_dir = self.cwd / "reports"

        # If openai_api_key is not provided in enrich config, check environment variable
        # if both are None and enrichment is enabled, raise error
        if all(v is None for v in [self.enrich.api_key, os.environ.get("OPENAI_API_KEY")]) and self.enrich.enabled:
            raise ValueError(
                "OpenAI API key not provided. Either set OPENAI_API_KEY environment variable "
                "or provide apiKey in the enrich configuration section."
            )
        elif self.enrich.api_key is None and os.environ.get("OPENAI_API_KEY"):
            self.enrich.api_key = os.environ.get("OPENAI_API_KEY")

        return self

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, v: Any) -> str:
        """Normalize log level to uppercase for case-insensitive input.

        Allows users to specify log levels in any case (info, INFO, Info).

        Args:
            v: Log level value to normalize

        Returns:
            Uppercase log level string

        Raises:
            ValueError: If value is not a string
        """
        if isinstance(v, str):
            return v.upper()
        # If not a string, convert to string for Pydantic to validate against Literal
        return str(v).upper()

    @field_validator("input_dir", "output_file", mode="before")
    @classmethod
    def convert_str_to_path(cls, v: Any, info: ValidationInfo) -> Path | None:
        """Convert string paths to Path objects.

        Args:
            v: Value to convert
            info: Validation context

        Returns:
            Path object or None
        """
        if v is None:
            return None
        if isinstance(v, str):
            return Path(v)
        if isinstance(v, Path):
            return v
        # If it's neither str nor Path, let Pydantic handle validation
        return Path(v)

    def to_aggregator_config(self) -> AggregatorConfig:
        """Convert settings to validated AggregatorConfig.

        Returns:
            Validated AggregatorConfig instance

        Raises:
            ValidationError: If configuration validation fails
        """
        return AggregatorConfig(
            input_dir=self.input_dir,  # type: ignore[arg-type]
            output_file=self.output_file,  # type: ignore[arg-type]
            scanner=self.scanner,
            mode=self.mode,
            log_level=self.log_level,
            config_file=self.config_file,
            registry=self.registry,
            organization=self.organization,
            packages=self.packages,
            download_remote_packages=self.download_remote_packages,
            local_only=self.local_only,
            max_workers=self.max_workers,
            enrich=self.enrich,
        )


def load_settings(
    cli_args: dict[str, Any] | None = None,
    config_file_path: Path | None = None,
) -> AggregatorSettings:
    """Load settings from all sources with proper precedence.

    This function uses Pydantic Settings with YamlConfigSettingsSource to handle
    configuration loading. The precedence order is managed by settings_customise_sources.

    Configuration precedence (from highest to lowest):
    1. CLI arguments (cli_args parameter)
    2. Explicit config file (config_file_path parameter) OR auto-discovered YAML
    3. Environment variables
    4. Default values

    Args:
        cli_args: Dictionary of CLI arguments (highest priority)
        config_file_path: Explicit path to configuration file (overrides yaml_file)

    Returns:
        Loaded and validated settings

    Raises:
        ValidationError: If configuration validation fails

    Examples:
        >>> # Load with defaults and environment variables
        >>> settings = load_settings()

        >>> # Load with CLI arguments
        >>> settings = load_settings(cli_args={'verbose': True})

        >>> # Load with explicit config file
        >>> settings = load_settings(config_file_path=Path('./my-config.yaml'))
    """
    # Filter out None values from CLI args to avoid overriding valid config values
    filtered_cli_args = {k: v for k, v in (cli_args or {}).items() if v is not None}

    # If explicit config file provided, create a custom settings class with that file
    if config_file_path:
        # Create a custom settings class with the explicit config file
        class CustomSettings(AggregatorSettings):
            model_config = SettingsConfigDict(
                env_prefix="CVE_AGGREGATOR_",
                env_file=".env",
                env_file_encoding="utf-8",
                case_sensitive=False,
                validate_assignment=True,
                extra="ignore",
                yaml_file=str(config_file_path),
            )

        settings: AggregatorSettings = CustomSettings(**filtered_cli_args)
        # Store the config file path for reference
        settings.config_file = config_file_path
    else:
        # Use default settings with auto-discovery
        settings = AggregatorSettings(**filtered_cli_args)

    return settings


def get_config(
    cli_args: dict[str, Any] | None = None,
    config_file_path: Path | None = None,
) -> AggregatorConfig:
    """Load and validate complete configuration.

    This is the main entry point for configuration loading. It handles:
    - Loading from all configuration sources
    - Merging with proper precedence
    - Full validation of final configuration

    Args:
        cli_args: Dictionary of CLI arguments
        config_file_path: Optional path to configuration file

    Returns:
        Fully validated AggregatorConfig instance

    Raises:
        ValidationError: If configuration validation fails
        FileNotFoundError: If specified config file doesn't exist
        ValueError: If config file is invalid

    Examples:
        >>> # Load with CLI arguments
        >>> config = get_config(cli_args={'input_dir': Path('./reports'), 'verbose': True})
        >>> print(config.log_level)
        True

        >>> # Load with config file
        >>> config = get_config(config_file_path=Path('./config.yaml'))

        >>> # Load with both (CLI takes precedence)
        >>> config = get_config(
        ...     cli_args={'verbose': True},
        ...     config_file_path=Path('./config.yaml')
        ... )
    """
    settings = load_settings(cli_args=cli_args, config_file_path=config_file_path)
    return settings.to_aggregator_config()


# ============================================================================
# Global Configuration Manager
# ============================================================================
# This section provides a thread-safe singleton for sharing configuration
# across modules. It uses a module-level private variable with accessor
# functions and context managers for testing.
# ============================================================================


# Private module-level configuration instance
_config: AggregatorConfig | None = None
_config_lock = threading.Lock()


def set_config(config: AggregatorConfig) -> None:
    """Set the global configuration instance.

    This function should be called once at application startup to initialize
    the global configuration. It is thread-safe and will override any existing
    configuration.

    Args:
        config: Validated AggregatorConfig instance to set as global

    Example:
        >>> # Initialize at application startup
        >>> config = get_config(cli_args={'verbose': True})
        >>> set_config(config)
        >>> # Now all modules can access config via get_current_config()
    """
    global _config
    with _config_lock:
        _config = config


def get_current_config() -> AggregatorConfig:
    """Get the global configuration instance.

    This function provides read-only access to the global configuration.
    The configuration must be initialized with set_config() before calling
    this function.

    Returns:
        The global AggregatorConfig instance

    Raises:
        ConfigurationError: If configuration has not been initialized

    Example:
        >>> # Access from any module after initialization
        >>> config = get_current_config()
        >>> print(f"Verbose mode: {config.log_level}")
        >>> print(f"Scanner: {config.scanner}")
    """
    if _config is None:
        raise ConfigurationError(
            "Global configuration not initialized. "
            "Call set_config() at application startup before accessing configuration."
        )
    return _config


def is_config_initialized() -> bool:
    """Check if global configuration has been initialized.

    Returns:
        True if configuration is initialized, False otherwise

    Example:
        >>> if not is_config_initialized():
        ...     config = get_config()
        ...     set_config(config)
    """
    return _config is not None


def reset_config() -> None:
    """Reset the global configuration to None.

    This function is primarily useful for testing to ensure a clean state
    between test cases. It should not be called in production code.

    Warning:
        This function should only be used in tests. Calling it in production
        code can lead to ConfigurationError in other modules.

    Example:
        >>> # In test teardown
        >>> def teardown():
        ...     reset_config()
    """
    global _config
    with _config_lock:
        _config = None


@contextmanager
def config_context(config: AggregatorConfig) -> Generator[AggregatorConfig]:
    """Context manager for temporarily setting configuration.

    This is primarily useful for testing, allowing you to inject a test
    configuration that automatically gets cleaned up. The previous configuration
    (if any) is restored when the context exits.

    Args:
        config: Configuration to use within the context

    Yields:
        The configuration instance

    Example:
        >>> # In test code
        >>> test_config = AggregatorConfig(
        ...     input_dir=Path('./test-reports'),
        ...     output_file=Path('./test-output.json'),
        ...     log_level="DEBUG"
        ... )
        >>> with config_context(test_config):
        ...     # Code in this block uses test_config
        ...     assert get_current_config().log_level == "DEBUG"
        >>> # Original config is restored after block
    """
    global _config
    previous_config = _config
    try:
        with _config_lock:
            _config = config
        yield config
    finally:
        with _config_lock:
            _config = previous_config


# ============================================================================
# Public API
# ============================================================================

__all__ = [
    "AggregatorSettings",
    "load_settings",
    "get_config",
    "set_config",
    "get_current_config",
    "is_config_initialized",
    "reset_config",
    "config_context",
    "ConfigurationError",
]
