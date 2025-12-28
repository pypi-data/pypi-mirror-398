"""Comprehensive tests for models module.

This test suite validates Pydantic models including field validation,
custom validators, and repr methods with sensitive data redaction.
"""

from typing import cast

import pytest
from pydantic import ValidationError

from cve_report_aggregator.core.models import (
    AggregatorConfig,
    EnrichmentConfig,
    LogLevelType,
    ModeType,
    PackageConfig,
    ScannerType,
)


class TestPackageConfig:
    """Tests for PackageConfig model."""

    def test_package_config_basic(self):
        """Test basic PackageConfig creation."""
        pkg = PackageConfig(name="test-package", version="1.0.0", architecture="amd64")

        assert pkg.name == "test-package"
        assert pkg.version == "1.0.0"
        assert pkg.architecture == "amd64"

    def test_package_config_default_architecture(self):
        """Test that architecture defaults to amd64."""
        pkg = PackageConfig(name="test", version="1.0.0")

        assert pkg.architecture == "amd64"

    def test_package_config_arm64(self):
        """Test PackageConfig with arm64 architecture."""
        pkg = PackageConfig(name="test", version="1.0.0", architecture="arm64")

        assert pkg.architecture == "arm64"

    def test_package_config_repr(self):
        """Test PackageConfig string representation."""
        pkg = PackageConfig(name="gitlab", version="18.4.2", architecture="amd64")

        repr_str = repr(pkg)
        assert "gitlab" in repr_str
        assert "18.4.2" in repr_str
        assert "amd64" in repr_str

    def test_package_config_local_source(self):
        """Test PackageConfig with local source."""
        pkg = PackageConfig(
            name="gitlab",
            version="18.4.2-uds.0-unicorn",
            architecture="amd64",
            source="local",
        )
        assert pkg.source == "local"
        assert pkg.name == "gitlab"

    def test_package_config_remote_source(self):
        """Test PackageConfig with explicit remote source."""
        pkg = PackageConfig(
            name="headlamp",
            version="0.35.0-uds.0-registry1",
            architecture="amd64",
            source="remote",
        )
        assert pkg.source == "remote"

    def test_package_config_default_source_is_remote(self):
        """Test that default source is remote."""
        pkg = PackageConfig(name="gitlab", version="18.4.2")
        assert pkg.source == "remote"

    def test_package_config_mixed_sources(self):
        """Test creating multiple packages with different sources."""
        local_pkg = PackageConfig(name="gitlab", version="18.4.2", source="local")
        remote_pkg = PackageConfig(name="headlamp", version="0.35.0", source="remote")

        assert local_pkg.source == "local"
        assert remote_pkg.source == "remote"


class TestEnrichmentConfig:
    """Tests for EnrichmentConfig model."""

    def test_enrichment_config_defaults(self):
        """Test EnrichmentConfig with default values."""
        config = EnrichmentConfig()

        assert config.enabled is False
        assert config.provider == "openrouter"  # Default provider is now openrouter
        assert config.model == "x-ai/grok-code-fast-1"
        assert config.api_key is None
        assert config.reasoning_effort == "medium"
        assert config.severities == ["Critical", "High"]
        assert config.verbosity == "medium"
        assert config.max_completion_tokens is None
        assert config.seed is None
        assert config.metadata is None

    def test_enrichment_config_with_api_key(self):
        """Test EnrichmentConfig with API key."""
        config = EnrichmentConfig(
            enabled=True,
            api_key="sk-1234567890abcdef",
        )

        assert config.enabled is True
        assert config.api_key == "sk-1234567890abcdef"

    def test_enrichment_config_custom_model(self):
        """Test EnrichmentConfig with custom model."""
        config = EnrichmentConfig(model="gpt-5-mini")

        assert config.model == "gpt-5-mini"

    def test_enrichment_config_custom_reasoning_effort(self):
        """Test EnrichmentConfig with custom reasoning effort."""
        config = EnrichmentConfig(reasoning_effort="high")

        assert config.reasoning_effort == "high"

    def test_enrichment_config_invalid_reasoning_effort(self):
        """Test that invalid reasoning effort raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EnrichmentConfig(reasoning_effort="ultra")  # Invalid value

        assert "pattern" in str(exc_info.value).lower()

    def test_enrichment_config_custom_verbosity(self):
        """Test EnrichmentConfig with custom verbosity."""
        config = EnrichmentConfig(verbosity="low")

        assert config.verbosity == "low"

    def test_enrichment_config_invalid_verbosity(self):
        """Test that invalid verbosity raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EnrichmentConfig(verbosity="extreme")  # Invalid value

        assert "pattern" in str(exc_info.value).lower()

    def test_enrichment_config_custom_severities(self):
        """Test EnrichmentConfig with custom severity list."""
        config = EnrichmentConfig(severities=["Critical", "High", "Medium"])

        assert config.severities == ["Critical", "High", "Medium"]

    def test_enrichment_config_all_severities(self):
        """Test EnrichmentConfig with all severity levels."""
        config = EnrichmentConfig(severities=["Critical", "High", "Medium", "Low"])

        assert len(config.severities) == 4
        assert "Low" in config.severities

    def test_enrichment_config_with_optional_params(self):
        """Test EnrichmentConfig with all optional parameters."""
        config = EnrichmentConfig(
            enabled=True,
            model="gpt-5-mini",
            api_key="test-key",
            reasoning_effort="high",
            verbosity="high",
            max_completion_tokens=4096,
            seed=42,
            metadata={"env": "test", "version": "1.0"},
        )

        assert config.max_completion_tokens == 4096
        assert config.seed == 42
        assert config.metadata == {"env": "test", "version": "1.0"}

    def test_enrichment_config_model_validation_gpt4(self):
        """Test model validation with GPT-4 models."""
        config = EnrichmentConfig(model="gpt-4")
        assert config.model == "gpt-4"

        config = EnrichmentConfig(model="gpt-4-turbo")
        assert config.model == "gpt-4-turbo"

        config = EnrichmentConfig(model="gpt-4o")
        assert config.model == "gpt-4o"

        config = EnrichmentConfig(model="gpt-4o-mini")
        assert config.model == "gpt-4o-mini"

    def test_enrichment_config_model_validation_gpt5(self):
        """Test model validation with GPT-5 models."""
        config = EnrichmentConfig(model="x-ai/grok-code-fast-1")
        assert config.model == "x-ai/grok-code-fast-1"

        config = EnrichmentConfig(model="gpt-5-mini")
        assert config.model == "gpt-5-mini"

    def test_enrichment_config_model_validation_o1(self):
        """Test model validation with O1 reasoning models."""
        config = EnrichmentConfig(model="o1-preview")
        assert config.model == "o1-preview"

        config = EnrichmentConfig(model="o1-mini")
        assert config.model == "o1-mini"

    def test_enrichment_config_model_validation_o3(self):
        """Test model validation with O3 reasoning models."""
        config = EnrichmentConfig(model="o3-mini")
        assert config.model == "o3-mini"

    def test_enrichment_config_invalid_model_name(self):
        """Test that invalid model name raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EnrichmentConfig(model="claude-3-opus")  # Not a valid OpenRouter or OpenAI model

        error_msg = str(exc_info.value)
        assert "Invalid model name" in error_msg
        assert "claude-3-opus" in error_msg

    def test_enrichment_config_invalid_model_empty(self):
        """Test that empty model name raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EnrichmentConfig(model="")

        assert "Invalid model name" in str(exc_info.value)

    def test_enrichment_config_repr_without_api_key(self):
        """Test repr without API key shows normal output."""
        config = EnrichmentConfig(enabled=True, model="gpt-4")

        repr_str = repr(config)
        assert "gpt-4" in repr_str
        assert "enabled=True" in repr_str
        assert "REDACTED" not in repr_str

    def test_enrichment_config_repr_with_api_key(self):
        """Test repr excludes API key field entirely for security (repr=False)."""
        config = EnrichmentConfig(
            enabled=True,
            api_key="sk-proj-1234567890abcdef1234567890abcdef",
            model="gpt-4",
        )

        repr_str = repr(config)
        # With repr=False, the api_key field is completely excluded from repr
        assert "api_key" not in repr_str
        assert "sk-proj-1234567890abcdef1234567890abcdef" not in repr_str
        assert "gpt-4" in repr_str
        # Verify the key is still accessible internally
        assert config.api_key == "sk-proj-1234567890abcdef1234567890abcdef"

    def test_enrichment_config_camel_case_aliases(self):
        """Test that camelCase aliases work for field names."""
        # Pydantic supports camelCase via validation_alias and populate_by_name
        # ty doesn't recognize this at static analysis time, so we ignore the type error
        config = EnrichmentConfig(
            apiKey="test-key",  # type: ignore[call-arg]
            reasoningEffort="high",  # type: ignore[call-arg]
            maxCompletionTokens=2048,  # type: ignore[call-arg]
        )

        assert config.api_key == "test-key"
        assert config.reasoning_effort == "high"
        assert config.max_completion_tokens == 2048

    def test_enrichment_config_populate_by_name(self):
        """Test that both snake_case and camelCase can be used."""
        # Using snake_case
        config1 = EnrichmentConfig(api_key="key1", reasoning_effort="low")
        assert config1.api_key == "key1"

        # Using camelCase - ty doesn't recognize Pydantic aliases
        config2 = EnrichmentConfig(apiKey="key2", reasoningEffort="high")  # type: ignore[call-arg]
        assert config2.api_key == "key2"

    def test_enrichment_config_validate_assignment(self):
        """Test that field assignment validation is enabled."""
        config = EnrichmentConfig()

        # Valid assignment
        config.model = "gpt-4o"
        assert config.model == "gpt-4o"

        # Invalid assignment should raise ValidationError
        with pytest.raises(ValidationError):
            config.model = "invalid-model"


class TestAggregatorConfig:
    """Tests for AggregatorConfig model."""

    def test_aggregator_config_basic(self, tmp_path):
        """Test basic AggregatorConfig creation."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
        )

        assert config.input_dir == input_dir.resolve()
        assert config.output_file == (tmp_path / "output.json").resolve()
        assert config.scanner == "grype"
        assert config.mode == "highest-score"
        assert config.log_level == "INFO"

    def test_aggregator_config_with_enrichment(self, tmp_path):
        """Test AggregatorConfig with nested enrichment config."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
            enrich=EnrichmentConfig(
                enabled=True,
                api_key="test-key",
                model="gpt-4",
            ),
        )

        assert config.enrich.enabled is True
        assert config.enrich.api_key == "test-key"
        assert config.enrich.model == "gpt-4"

    def test_aggregator_config_with_packages(self, tmp_path):
        """Test AggregatorConfig with package list."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        packages = [
            PackageConfig(name="gitlab", version="18.4.2", architecture="amd64"),
            PackageConfig(name="runner", version="18.4.0", architecture="arm64"),
        ]

        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
            packages=packages,
        )

        assert len(config.packages) == 2
        assert config.packages[0].name == "gitlab"
        assert config.packages[1].architecture == "arm64"

    def test_aggregator_config_download_remote_packages(self, tmp_path):
        """Test AggregatorConfig with remote package downloads."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
            download_remote_packages=True,
            registry="registry.example.com",
            organization="test-org",
        )

        assert config.download_remote_packages is True
        assert config.registry == "registry.example.com"
        assert config.organization == "test-org"

    def test_aggregator_config_invalid_input_dir(self, tmp_path):
        """Test that non-existent input directory raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AggregatorConfig(
                input_dir=tmp_path / "nonexistent",
                output_file=tmp_path / "output.json",
            )

        assert "Input directory does not exist" in str(exc_info.value)

    def test_aggregator_config_input_dir_not_directory(self, tmp_path):
        """Test that input path must be a directory."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("not a directory")

        with pytest.raises(ValidationError) as exc_info:
            AggregatorConfig(
                input_dir=file_path,
                output_file=tmp_path / "output.json",
            )

        assert "Input path is not a directory" in str(exc_info.value)

    def test_aggregator_config_output_dir_not_exists(self, tmp_path):
        """Test that output file parent directory must exist."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        with pytest.raises(ValidationError) as exc_info:
            AggregatorConfig(
                input_dir=input_dir,
                output_file=tmp_path / "nonexistent" / "output.json",
            )

        assert "Output file parent directory does not exist" in str(exc_info.value)

    def test_aggregator_config_output_is_directory(self, tmp_path):
        """Test that output path cannot be a directory."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        output_dir = tmp_path / "output_dir"
        output_dir.mkdir()

        with pytest.raises(ValidationError) as exc_info:
            AggregatorConfig(
                input_dir=input_dir,
                output_file=output_dir,
            )

        assert "Output path is a directory, not a file" in str(exc_info.value)

    def test_aggregator_config_valid_config_file(self, tmp_path):
        """Test AggregatorConfig with valid config file."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        config_file = tmp_path / "config.yaml"
        config_file.write_text("scanner: grype\n")

        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
            config_file=config_file,
        )

        assert config.config_file == config_file.resolve()

    def test_aggregator_config_invalid_config_file(self, tmp_path):
        """Test that non-existent config file raises ValidationError."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        with pytest.raises(ValidationError) as exc_info:
            AggregatorConfig(
                input_dir=input_dir,
                output_file=tmp_path / "output.json",
                config_file=tmp_path / "nonexistent.yaml",
            )

        assert "Configuration file does not exist" in str(exc_info.value)

    def test_aggregator_config_config_file_is_directory(self, tmp_path):
        """Test that config file cannot be a directory."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        config_dir = tmp_path / "config_dir"
        config_dir.mkdir()

        with pytest.raises(ValidationError) as exc_info:
            AggregatorConfig(
                input_dir=input_dir,
                output_file=tmp_path / "output.json",
                config_file=config_dir,
            )

        assert "Configuration path is not a file" in str(exc_info.value)

    def test_aggregator_config_max_workers(self, tmp_path):
        """Test AggregatorConfig with max_workers."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
            max_workers=8,
        )

        assert config.max_workers == 8

    def test_aggregator_config_camel_case_aliases(self, tmp_path):
        """Test that camelCase aliases work for field names."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        # Pydantic supports camelCase via validation_alias and populate_by_name
        # ty doesn't recognize this at static analysis time, so we ignore the type error
        config = AggregatorConfig(
            inputDir=input_dir,  # type: ignore[call-arg]
            outputFile=tmp_path / "output.json",  # type: ignore[call-arg]
            logLevel="DEBUG",  # type: ignore[call-arg]
            downloadRemotePackages=True,  # type: ignore[call-arg]
            maxWorkers=4,  # type: ignore[call-arg]
        )

        assert config.input_dir == input_dir.resolve()
        assert config.log_level == "DEBUG"
        assert config.download_remote_packages is True
        assert config.max_workers == 4

    def test_aggregator_config_repr_without_api_key(self, tmp_path):
        """Test repr without API key shows normal output."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
        )

        repr_str = repr(config)
        assert "reports" in repr_str
        assert "REDACTED" not in repr_str

    def test_aggregator_config_repr_with_api_key(self, tmp_path):
        """Test repr excludes nested API key in enrichment config (repr=False)."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
            enrich=EnrichmentConfig(
                enabled=True,
                api_key="sk-proj-secret123456789",
            ),
        )

        repr_str = repr(config)
        # With repr=False on EnrichmentConfig.api_key, it's excluded from repr entirely
        assert "api_key" not in repr_str
        assert "sk-proj-secret123456789" not in repr_str
        # Verify the key is still accessible internally
        assert config.enrich.api_key == "sk-proj-secret123456789"

    def test_aggregator_config_all_scanner_types(self, tmp_path):
        """Test all valid scanner types."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        scanners: list[ScannerType] = ["grype", "trivy"]
        for scanner in scanners:
            config = AggregatorConfig(
                input_dir=input_dir,
                output_file=tmp_path / "output.json",
                scanner=scanner,
            )
            assert config.scanner == scanner

    def test_aggregator_config_all_mode_types(self, tmp_path):
        """Test all valid mode types."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        modes: list[ModeType] = ["highest-score", "first-occurrence", "grype-only", "trivy-only"]
        for mode in modes:
            config = AggregatorConfig(
                input_dir=input_dir,
                output_file=tmp_path / "output.json",
                mode=mode,
            )
            assert config.mode == mode

    def test_aggregator_config_all_log_levels(self, tmp_path):
        """Test all valid log levels."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        log_levels: list[LogLevelType] = ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for log_level in log_levels:
            config = AggregatorConfig(
                input_dir=input_dir,
                output_file=tmp_path / "output.json",
                log_level=log_level,
            )
            assert config.log_level == log_level

    def test_aggregator_config_local_only(self, tmp_path):
        """Test local_only configuration."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
            local_only=True,
        )

        assert config.local_only is True

    def test_aggregator_config_validate_assignment(self, tmp_path):
        """Test that field assignment validation is enabled."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
        )

        # Valid assignment
        config.log_level = "DEBUG"
        assert config.log_level == "DEBUG"

    def test_aggregator_config_frozen_false(self, tmp_path):
        """Test that config is not frozen and can be modified."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
        )

        # Should be able to modify fields
        config.log_level = "DEBUG"
        assert config.log_level == "DEBUG"

    def test_aggregator_config_populate_by_name(self, tmp_path):
        """Test that both snake_case and camelCase can be used."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        # Using snake_case
        config1 = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output1.json",
            log_level="DEBUG",
        )
        assert config1.log_level == "DEBUG"

        # Using camelCase - ty doesn't recognize Pydantic aliases
        config2 = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output2.json",
            logLevel=cast(LogLevelType, "INFO"),  # type: ignore[call-arg]
        )
        assert config2.log_level == "INFO"
