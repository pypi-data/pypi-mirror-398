"""Data models and type definitions for CVE report aggregation."""

import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Type aliases for better type hints
ScannerType = Literal["grype", "trivy", "both"]
ModeType = Literal["highest-score", "first-occurrence", "grype-only", "trivy-only"]
LogLevelType = Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
PackageSourceType = Literal["local", "remote"]

# Pattern for safe package identifiers (alphanumeric, dots, dashes, underscores)
# Used to prevent command injection via package names, versions, etc.
_SAFE_IDENTIFIER_PATTERN: re.Pattern[str] = re.compile(r"^[a-zA-Z0-9._-]+$")


class PackageConfig(BaseModel):
    """Configuration for a package to scan.

    Supports both local (from ./packages/ directory) and remote (from OCI registry) packages.
    The source field determines where the package comes from:
    - "local": Package is in ./packages/ directory (archive file)
    - "remote": Package will be downloaded from registry

    Attributes:
        name: Package name
        version: Package version
        architecture: Package architecture (e.g., amd64, arm64)
        source: Package source - "local" or "remote" (default: "remote")
    """

    name: str = Field(description="Package name")
    version: str = Field(description="Package version")
    architecture: str = Field(default="amd64", description="Package architecture")
    source: PackageSourceType = Field(default="remote", description="Package source: local or remote")

    @field_validator("name", "version", "architecture")
    @classmethod
    def validate_safe_identifier(cls, v: str, info: object) -> str:
        """Validate that identifiers contain only safe characters.

        Prevents command injection by ensuring package names, versions, and architectures
        only contain alphanumeric characters, dots, dashes, and underscores.

        Args:
            v: Value to validate
            info: Validation info (unused but required by Pydantic)

        Returns:
            Validated value

        Raises:
            ValueError: If value contains unsafe characters
        """
        if not _SAFE_IDENTIFIER_PATTERN.match(v):
            raise ValueError(f"Invalid characters in '{v}'. Only alphanumeric, dots, dashes, and underscores allowed.")
        return v


class EnrichmentConfig(BaseModel):
    """Configuration for CVE enrichment with AI providers.

    Supports OpenRouter as the AI provider for CVE enrichment analysis.
    OpenRouter provides access to multiple AI models through a unified API.

    Attributes:
        enabled: Enable CVE enrichment
        provider: Enrichment provider (openrouter)
        model: AI model to use (e.g., x-ai/grok-code-fast-1, gpt-5-mini, gpt-4o)
        api_key: OpenRouter API key
        reasoning_effort: Reasoning effort level (minimal, low, medium, high)
        severities: List of severity levels to enrich
        verbosity: Verbosity level for model responses (low, medium, high)
        max_completion_tokens: Optional upper bound for total tokens
        seed: Optional seed for reproducible results
        metadata: Optional metadata tags for API requests
        max_workers: Maximum number of concurrent API requests
    """

    model_config = ConfigDict(
        validate_assignment=True,
        populate_by_name=True,
    )

    enabled: bool = Field(default=False, description="Enable CVE enrichment")
    provider: Literal["openrouter"] = Field(default="openrouter", description="Enrichment provider")
    model: str = Field(default="x-ai/grok-code-fast-1", description="AI model to use via OpenRouter")
    api_key: str | None = Field(default=None, validation_alias="apiKey", description="OpenRouter API key", repr=False)
    reasoning_effort: str = Field(
        default="medium",
        validation_alias="reasoningEffort",
        pattern="^(minimal|low|medium|high)$",
        description="Reasoning effort level",
    )
    severities: list[str] = Field(
        default=["Critical", "High"],
        description="Severity levels to enrich",
    )
    verbosity: str = Field(
        default="medium",
        pattern="^(low|medium|high)$",
        description="Verbosity level for model responses",
    )
    max_completion_tokens: int | None = Field(
        default=None,
        validation_alias="maxCompletionTokens",
        description="Optional upper bound for total tokens including reasoning tokens",
    )
    seed: int | None = Field(
        default=None,
        description="Optional seed for reproducible results",
    )
    metadata: dict[str, str] | None = Field(
        default=None,
        description="Optional metadata tags for API requests",
    )
    max_workers: int = Field(
        default=5,
        ge=1,
        le=20,
        validation_alias="maxWorkers",
        description=(
            "Maximum number of concurrent API requests for CVE enrichment. "
            "Higher values speed up enrichment but may hit rate limits. "
            "Default: 5 workers."
        ),
    )

    # Note: api_key field uses repr=False to prevent accidental exposure in logs/debugging

    @field_validator("model")
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        """Validate AI model name format.

        Validates model names for both OpenRouter and OpenAI providers.
        OpenRouter uses format: provider/model-name (e.g., x-ai/grok-code-fast-1)
        OpenAI uses direct model names (e.g., gpt-4o, o1-preview)

        Args:
            v: Model name to validate

        Returns:
            Validated model name

        Raises:
            ValueError: If model name doesn't match valid patterns

        Examples:
            >>> EnrichmentConfig(model="gpt-4o")  # Valid - OpenAI
            >>> EnrichmentConfig(model="x-ai/grok-code-fast-1")  # Valid - OpenRouter
            >>> EnrichmentConfig(model="anthropic/claude-3.5-sonnet")  # Valid - OpenRouter
        """
        # OpenRouter format: provider/model-name
        if "/" in v:
            # Validate OpenRouter format
            parts = v.split("/")
            if len(parts) != 2 or not all(parts):
                raise ValueError(
                    f"Invalid OpenRouter model format: '{v}'. "
                    f"Expected format: 'provider/model-name'. "
                    f"Examples: 'x-ai/grok-code-fast-1', 'anthropic/claude-3.5-sonnet'"
                )
            return v

        # OpenAI model prefixes (these models are available via OpenRouter)
        valid_openai_prefixes = [
            "gpt-3.5",  # GPT-3.5 models
            "gpt-4",  # GPT-4 base models
            "gpt-4o",  # GPT-4o optimized models
            "gpt-5",  # GPT-5 models (nano, mini, etc.)
            "o1",  # O1 reasoning models
            "o3",  # O3 reasoning models
        ]

        # Check if model name starts with any valid OpenAI prefix
        if any(v.startswith(prefix) for prefix in valid_openai_prefixes):
            return v

        # If neither format matches, raise error
        raise ValueError(
            f"Invalid model name: '{v}'. "
            f"Use OpenRouter format 'provider/model-name' (e.g., 'x-ai/grok-code-fast-1') "
            f"or OpenAI model name (e.g., 'gpt-4o', 'o1-preview')"
        )


class AggregatorConfig(BaseModel):
    """Configuration model for CVE Report Aggregator.

    This model provides comprehensive validation of all configuration
    parameters including paths, scanner selection, and operational modes.

    Attributes:
        input_dir: Directory containing scan report files
        output_file: Path for the unified output report
        scanner: Scanner type to use (grype, trivy, or both)
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

    model_config = ConfigDict(
        validate_assignment=True,
        frozen=False,
        populate_by_name=True,
    )

    input_dir: Path = Field(
        default=Path.cwd() / "reports",
        description="Input directory containing scan report files",
        validation_alias="inputDir",
    )
    output_file: Path = Field(
        default=Path.cwd() / "unified-report.json",
        description="Output file path for the unified report",
        validation_alias="outputFile",
    )
    scanner: ScannerType = Field(
        default="grype",
        description="Vulnerability scanner to use (grype, trivy, or both)",
    )
    mode: ModeType = Field(
        default="highest-score",
        description="Aggregation mode for vulnerability processing",
    )
    log_level: LogLevelType = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        validation_alias="logLevel",
    )
    config_file: Path | None = Field(
        default=None,
        description="Path to YAML configuration file",
        validation_alias="configFile",
    )
    registry: str | None = Field(
        default=None,
        description="Container registry URL",
    )
    organization: str | None = Field(
        default=None,
        description="Organization or namespace in the registry",
    )
    packages: list[PackageConfig] = Field(
        default_factory=list,
        description="List of packages to scan",
    )
    download_remote_packages: bool = Field(
        default=False,
        description="Download SBOM reports from remote registry for specified packages",
        validation_alias="downloadRemotePackages",
    )
    local_only: bool = Field(
        default=False,
        description="Only scan local Zarf packages (skip remote downloads)",
        validation_alias="localOnly",
    )
    max_workers: int | None = Field(
        default=None,
        description=(
            "Maximum number of concurrent workers for parallel operations (default: auto-detect based on CPU count)"
        ),
        validation_alias="maxWorkers",
    )
    archive_dir: Path | None = Field(
        default=None,
        description=(
            "Directory for tarball archive output. "
            "If set, creates a compressed tarball of all output artifacts. "
            "Useful for Docker deployments where a single mount point is preferred."
        ),
        validation_alias="archiveDir",
    )

    # CVE enrichment configuration (nested)
    enrich: EnrichmentConfig = Field(
        default_factory=EnrichmentConfig,
        description="CVE enrichment configuration",
    )

    # Note: API key in enrich.api_key uses repr=False to prevent exposure in logs

    @field_validator("input_dir")
    @classmethod
    def validate_input_dir(cls, v: Path) -> Path:
        """Validate that input directory exists and is accessible.

        Args:
            v: Input directory path

        Returns:
            Validated and resolved Path object

        Raises:
            ValueError: If directory doesn't exist or isn't accessible
        """
        resolved = v.resolve()
        if not resolved.exists():
            raise ValueError(f"Input directory does not exist: {resolved}")
        if not resolved.is_dir():
            raise ValueError(f"Input path is not a directory: {resolved}")
        return resolved

    @field_validator("output_file")
    @classmethod
    def validate_output_file(cls, v: Path) -> Path:
        """Validate output file path.

        Args:
            v: Output file path

        Returns:
            Validated and resolved Path object

        Raises:
            ValueError: If parent directory doesn't exist or path is invalid
        """
        resolved = v.resolve()
        if not resolved.parent.exists():
            raise ValueError(f"Output file parent directory does not exist: {resolved.parent}")
        if resolved.exists() and resolved.is_dir():
            raise ValueError(f"Output path is a directory, not a file: {resolved}")
        return resolved

    @field_validator("config_file")
    @classmethod
    def validate_config_file(cls, v: Path | None) -> Path | None:
        """Validate configuration file if provided.

        Args:
            v: Configuration file path

        Returns:
            Validated and resolved Path object or None

        Raises:
            ValueError: If config file doesn't exist or isn't readable
        """
        if v is None:
            return None
        resolved = v.resolve()
        if not resolved.exists():
            raise ValueError(f"Configuration file does not exist: {resolved}")
        if not resolved.is_file():
            raise ValueError(f"Configuration path is not a file: {resolved}")
        return resolved
