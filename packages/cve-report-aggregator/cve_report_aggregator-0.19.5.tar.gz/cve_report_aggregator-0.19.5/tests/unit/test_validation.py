"""Tests for validation module."""

import pytest

from cve_report_aggregator.context import AppContext
from cve_report_aggregator.core.models import AggregatorConfig
from cve_report_aggregator.core.validation import (
    ConfigValidationError,
    MissingToolError,
    validate_configuration,
    validate_grype_requirements,
    validate_scanner_tools,
    validate_trivy_requirements,
    validate_uds_requirements,
    validate_zarf_requirements,
)


class TestValidateGrypeRequirements:
    """Tests for validate_grype_requirements function."""

    def test_validate_grype_requirements_success(self, mock_subprocess_success):
        """Test validation when grype is installed."""
        # Should not raise
        validate_grype_requirements()

    def test_validate_grype_requirements_missing(self, mock_subprocess_failure):
        """Test validation when grype is not installed."""
        with pytest.raises(MissingToolError) as exc_info:
            validate_grype_requirements()

        assert "grype" in str(exc_info.value)
        assert exc_info.value.tool == "grype"
        assert exc_info.value.install_url is not None


class TestValidateTrivyRequirements:
    """Tests for validate_trivy_requirements function."""

    def test_validate_trivy_requirements_success(self, mock_subprocess_success):
        """Test validation when trivy and syft are installed."""
        # Should not raise
        validate_trivy_requirements()

    def test_validate_trivy_requirements_missing_syft(self, monkeypatch):
        """Test validation when syft is missing."""
        import subprocess

        def mock_run(*args, **kwargs):
            command = args[0]
            if "syft" in command:
                raise subprocess.CalledProcessError(1, command)
            return MagicMock(returncode=0)

        from unittest.mock import MagicMock

        monkeypatch.setattr(subprocess, "run", mock_run)

        with pytest.raises(MissingToolError) as exc_info:
            validate_trivy_requirements()

        assert "syft" in str(exc_info.value)
        assert exc_info.value.tool == "syft"

    def test_validate_trivy_requirements_missing_trivy(self, monkeypatch):
        """Test validation when trivy is missing."""
        import subprocess

        def mock_run(*args, **kwargs):
            command = args[0]
            if "trivy" in command:
                raise subprocess.CalledProcessError(1, command)
            return MagicMock(returncode=0)

        from unittest.mock import MagicMock

        monkeypatch.setattr(subprocess, "run", mock_run)

        with pytest.raises(MissingToolError) as exc_info:
            validate_trivy_requirements()

        assert "trivy" in str(exc_info.value)
        assert exc_info.value.tool == "trivy"


class TestValidateUDSRequirements:
    """Tests for validate_uds_requirements function."""

    def test_validate_uds_requirements_success(self, mock_subprocess_success):
        """Test validation when uds is installed."""
        # Should not raise
        validate_uds_requirements()

    def test_validate_uds_requirements_missing(self, mock_subprocess_failure):
        """Test validation when uds is not installed."""
        with pytest.raises(MissingToolError) as exc_info:
            validate_uds_requirements()

        assert "uds" in str(exc_info.value)
        assert exc_info.value.tool == "uds"


class TestValidateZarfRequirements:
    """Tests for validate_zarf_requirements function (now checks for uds)."""

    def test_validate_zarf_requirements_success(self, mock_subprocess_success):
        """Test validation when uds is installed."""
        # Should not raise
        validate_zarf_requirements()

    def test_validate_zarf_requirements_missing(self, mock_subprocess_failure):
        """Test validation when uds is not installed."""
        with pytest.raises(MissingToolError) as exc_info:
            validate_zarf_requirements()

        assert "uds" in str(exc_info.value)
        assert exc_info.value.tool == "uds"


class TestValidateScannerTools:
    """Tests for validate_scanner_tools function."""

    def test_validate_scanner_tools_grype_only_mode(self, tmp_path, mock_subprocess_success):
        """Test validation for grype-only mode."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            mode="grype-only",
        )
        context = AppContext(config)

        # Should not raise
        validate_scanner_tools(context)

    def test_validate_scanner_tools_trivy_only_mode(self, tmp_path, mock_subprocess_success):
        """Test validation for trivy-only mode."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            mode="trivy-only",
        )
        context = AppContext(config)

        # Should not raise
        validate_scanner_tools(context)

    def test_validate_scanner_tools_grype_scanner(self, tmp_path, mock_subprocess_success):
        """Test validation for grype scanner in highest-score mode."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            scanner="grype",
            mode="highest-score",
        )
        context = AppContext(config)

        # Should not raise
        validate_scanner_tools(context)

    def test_validate_scanner_tools_trivy_scanner(self, tmp_path, mock_subprocess_success):
        """Test validation for trivy scanner in highest-score mode."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            scanner="trivy",
            mode="highest-score",
        )
        context = AppContext(config)

        # Should not raise
        validate_scanner_tools(context)

    def test_validate_scanner_tools_missing_grype(self, tmp_path, mock_subprocess_failure):
        """Test validation error when grype is missing."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            mode="grype-only",
        )
        context = AppContext(config)

        with pytest.raises(MissingToolError):
            validate_scanner_tools(context)

    def test_validate_scanner_tools_with_remote_packages(self, tmp_path, mock_subprocess_success):
        """Test validation with remote package download enabled."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            download_remote_packages=True,
            registry="registry.example.com",
            organization="my-org",
        )
        context = AppContext(config)

        # Should not raise
        validate_scanner_tools(context)

    def test_validate_scanner_tools_missing_uds(self, tmp_path, mock_subprocess_failure):
        """Test validation error when uds is missing for remote packages."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            download_remote_packages=True,
            registry="registry.example.com",
            organization="my-org",
        )
        context = AppContext(config)

        with pytest.raises(MissingToolError):
            validate_scanner_tools(context)


class TestValidateConfiguration:
    """Tests for validate_configuration function."""

    def test_validate_configuration_valid(self, tmp_path, mock_subprocess_success):
        """Test validation with valid configuration."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
        )
        context = AppContext(config)

        # Should not raise
        validate_configuration(context)

    def test_validate_configuration_remote_packages_missing_registry(self, tmp_path):
        """Test validation error when registry is missing for remote packages."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            download_remote_packages=True,
            organization="my-org",  # Registry missing
        )
        context = AppContext(config)

        with pytest.raises(ValueError, match="Registry URL is required"):
            validate_configuration(context)

    def test_validate_configuration_remote_packages_missing_organization(self, tmp_path):
        """Test validation error when organization is missing for remote packages."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            download_remote_packages=True,
            registry="registry.example.com",  # Organization missing
        )
        context = AppContext(config)

        with pytest.raises(ValueError, match="Organization is required"):
            validate_configuration(context)


class TestConfigValidationError:
    """Tests for ConfigValidationError class."""

    def test_config_validation_error_inheritance(self):
        """Test that ConfigValidationError is a subclass of ConfigurationError."""
        from cve_report_aggregator.core.exceptions import ConfigurationError

        error = ConfigValidationError("Test error")
        assert isinstance(error, ConfigurationError)
        assert isinstance(error, Exception)
        assert str(error) == "Test error"


class TestMissingToolError:
    """Tests for MissingToolError class."""

    def test_missing_tool_error_basic(self):
        """Test MissingToolError with basic parameters."""
        error = MissingToolError(tool="test-tool")
        assert error.tool == "test-tool"
        assert "test-tool" in str(error)
        assert error.install_url is None

    def test_missing_tool_error_with_url(self):
        """Test MissingToolError with installation URL."""
        url = "https://example.com/install"
        error = MissingToolError(tool="test-tool", install_url=url)
        assert error.tool == "test-tool"
        assert error.install_url == url
        assert "test-tool" in str(error)
        assert url in str(error)

    def test_missing_tool_error_inheritance(self):
        """Test that MissingToolError inherits from ConfigValidationError."""
        error = MissingToolError(tool="test-tool")
        assert isinstance(error, ConfigValidationError)
        assert isinstance(error, Exception)


class TestValidateConfigurationEdgeCases:
    """Additional edge case tests for validate_configuration."""

    def test_validate_configuration_with_packages_but_no_remote_download(self, tmp_path, mock_subprocess_success):
        """Test validation when packages are specified but remote download is disabled."""
        from cve_report_aggregator.core.models import PackageConfig

        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            download_remote_packages=False,
            packages=[PackageConfig(name="test", version="1.0.0")],
        )
        context = AppContext(config)

        # Should not raise - packages can be specified without remote download
        validate_configuration(context)

    def test_validate_configuration_combined_requirements(self, tmp_path, mock_subprocess_success):
        """Test validation with multiple requirements enabled."""
        from cve_report_aggregator.core.models import PackageConfig

        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            scanner="trivy",
            mode="trivy-only",
            download_remote_packages=True,
            registry="registry.example.com",
            organization="my-org",
            packages=[PackageConfig(name="test", version="1.0.0")],
        )
        context = AppContext(config)

        # Should validate all tools (trivy, syft, uds)
        validate_configuration(context)


class TestValidateScannerToolsEdgeCases:
    """Additional edge case tests for validate_scanner_tools."""

    def test_validate_scanner_tools_first_occurrence_mode(self, tmp_path, mock_subprocess_success):
        """Test validation for first-occurrence mode (should use configured scanner)."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            scanner="grype",
            mode="first-occurrence",
        )
        context = AppContext(config)

        # Should validate grype scanner
        validate_scanner_tools(context)

    def test_validate_scanner_tools_local_only_mode(self, tmp_path, mock_subprocess_success):
        """Test validation with local_only mode enabled."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            local_only=True,
            download_remote_packages=True,  # Should be ignored
        )
        context = AppContext(config)

        # Should not require UDS since local_only is True
        validate_scanner_tools(context)
