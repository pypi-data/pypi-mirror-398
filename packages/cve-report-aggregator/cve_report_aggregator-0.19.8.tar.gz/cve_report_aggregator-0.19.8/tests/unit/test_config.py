"""Tests for configuration management module using Pydantic Settings."""

from pathlib import Path

import pytest

from cve_report_aggregator.core.config import AggregatorSettings, get_config, load_settings
from cve_report_aggregator.core.models import AggregatorConfig, PackageConfig


@pytest.fixture
def create_example_config():
    """Fixture to create example YAML configuration files for testing."""

    def _create_config(output_path: Path) -> None:
        """Create an example YAML configuration file.

        Args:
            output_path: Path where to write the example config
        """
        example_config = """# CVE Report Aggregator Configuration
# This file can be placed at:
#   - ./.cve-aggregator.yaml (current directory - auto-discovered)
#   - ./.cve-aggregator.yml (current directory - auto-discovered)
# Or specify explicitly with --config flag

# Input directory containing scan report files (camelCase for YAML)
inputDir: ./reports

# Output file path for the unified report (camelCase for YAML)
outputFile: ./unified-report.json

# Scanner type: grype or trivy
scanner: grype

# Aggregation mode:
#   - highest-score: Select highest CVSS 3.x score across all reports
#   - first-occurrence: Use severity from first occurrence
#   - grype-only: Process only with Grype scanner
#   - trivy-only: Process only with Trivy scanner
mode: highest-score

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL (camelCase for YAML)
logLevel: INFO
"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(example_config)

    return _create_config


class TestAggregatorSettings:
    """Tests for AggregatorSettings class."""

    def test_default_settings(self):
        """Test that default settings are properly initialized."""
        settings = AggregatorSettings()

        assert settings.input_dir == Path.cwd() / "reports"
        assert settings.output_file == Path.cwd() / "unified-report.json"
        assert settings.scanner == "grype"
        assert settings.mode == "highest-score"
        assert settings.log_level == "INFO"
        assert settings.config_file is None

    def test_settings_from_dict(self, tmp_path):
        """Test creating settings from dictionary."""
        input_dir = tmp_path / "custom-reports"
        input_dir.mkdir()

        settings = AggregatorSettings(
            input_dir=input_dir,
            scanner="trivy",
            mode="first-occurrence",
            log_level="DEBUG",
        )

        assert settings.input_dir == input_dir
        assert settings.scanner == "trivy"
        assert settings.mode == "first-occurrence"
        assert settings.log_level == "DEBUG"

    def test_settings_with_env_vars(self, monkeypatch, tmp_path):
        """Test loading settings from environment variables."""
        input_dir = tmp_path / "env-reports"
        input_dir.mkdir()

        monkeypatch.setenv("CVE_AGGREGATOR_INPUT_DIR", str(input_dir))
        monkeypatch.setenv("CVE_AGGREGATOR_SCANNER", "trivy")
        monkeypatch.setenv("CVE_AGGREGATOR_LOG_LEVEL", "DEBUG")

        settings = AggregatorSettings()

        assert settings.input_dir == input_dir
        assert settings.scanner == "trivy"
        assert settings.log_level == "DEBUG"

    def test_to_aggregator_config(self, tmp_path):
        """Test converting settings to AggregatorConfig."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        settings = AggregatorSettings(input_dir=input_dir)
        config = settings.to_aggregator_config()

        assert isinstance(config, AggregatorConfig)
        assert config.input_dir == input_dir


class TestYamlConfigLoading:
    """Tests for YAML configuration file loading using YamlConfigSettingsSource."""

    def test_load_from_yaml_file(self, tmp_path, monkeypatch):
        """Test loading configuration from YAML file."""
        # Change to temp directory for test isolation
        monkeypatch.chdir(tmp_path)

        input_dir = tmp_path / "yaml-reports"
        input_dir.mkdir()

        # Create .cve-aggregator.yaml in current directory with camelCase keys
        config_file = tmp_path / ".cve-aggregator.yaml"
        config_file.write_text(
            f"""
inputDir: {input_dir}
scanner: trivy
mode: first-occurrence
logLevel: DEBUG
"""
        )

        # Settings should auto-discover the config file
        settings = AggregatorSettings()

        assert settings.input_dir == input_dir
        assert settings.scanner == "trivy"
        assert settings.mode == "first-occurrence"
        assert settings.log_level == "DEBUG"

    def test_load_from_yml_extension(self, tmp_path, monkeypatch):
        """Test loading from .yml extension."""
        monkeypatch.chdir(tmp_path)

        # Create .cve-aggregator.yml with camelCase keys
        config_file = tmp_path / ".cve-aggregator.yml"
        config_file.write_text(
            """
scanner: trivy
logLevel: DEBUG
"""
        )

        settings = AggregatorSettings()

        assert settings.scanner == "trivy"
        assert settings.log_level == "DEBUG"

    def test_yaml_file_priority_over_defaults(self, tmp_path, monkeypatch):
        """Test that YAML file takes priority over defaults."""
        monkeypatch.chdir(tmp_path)

        config_file = tmp_path / ".cve-aggregator.yaml"
        config_file.write_text(
            """
scanner: trivy
mode: grype-only
"""
        )

        settings = AggregatorSettings()

        # YAML values override defaults
        assert settings.scanner == "trivy"
        assert settings.mode == "grype-only"
        # Defaults still work for unspecified values
        assert settings.log_level == "INFO"


class TestLoadSettings:
    """Tests for load_settings function."""

    def test_load_with_defaults(self):
        """Test loading with default values."""
        settings = load_settings()

        assert settings.input_dir == Path.cwd() / "reports"
        assert settings.scanner == "grype"
        assert settings.log_level == "INFO"

    def test_load_with_cli_args(self, tmp_path):
        """Test loading with CLI arguments."""
        input_dir = tmp_path / "cli-reports"
        input_dir.mkdir()

        cli_args = {
            "input_dir": input_dir,
            "scanner": "trivy",
            "log_level": "DEBUG",
        }

        settings = load_settings(cli_args=cli_args)

        assert settings.input_dir == input_dir
        assert settings.scanner == "trivy"
        assert settings.log_level == "DEBUG"

    def test_load_with_explicit_config_file(self, tmp_path):
        """Test loading with explicit config file path."""
        input_dir = tmp_path / "explicit-reports"
        input_dir.mkdir()

        # Use camelCase keys in YAML
        config_file = tmp_path / "my-config.yaml"
        config_file.write_text(
            f"""
inputDir: {input_dir}
scanner: trivy
mode: trivy-only
"""
        )

        settings = load_settings(config_file_path=config_file)

        assert settings.input_dir == input_dir
        assert settings.scanner == "trivy"
        assert settings.mode == "trivy-only"
        assert settings.config_file == config_file

    def test_cli_overrides_yaml(self, tmp_path):
        """Test that CLI arguments override YAML config."""
        input_dir = tmp_path / "override-reports"
        input_dir.mkdir()

        # Use camelCase keys in YAML
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
scanner: trivy
logLevel: INFO
"""
        )

        cli_args = {
            "scanner": "grype",  # Override YAML
            "log_level": "DEBUG",  # Override YAML
        }

        settings = load_settings(cli_args=cli_args, config_file_path=config_file)

        # CLI args take precedence
        assert settings.scanner == "grype"
        assert settings.log_level == "DEBUG"

    def test_cli_none_values_dont_override(self, tmp_path):
        """Test that None CLI values don't override config values."""
        # Use camelCase keys in YAML
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
scanner: trivy
logLevel: DEBUG
"""
        )

        cli_args = {
            "scanner": None,  # Should not override
            "log_level": None,  # Should not override
        }

        settings = load_settings(cli_args=cli_args, config_file_path=config_file)

        # YAML values should be preserved
        assert settings.scanner == "trivy"
        assert settings.log_level == "DEBUG"

    def test_load_with_env_vars(self, monkeypatch, tmp_path):
        """Test that environment variables are loaded."""
        input_dir = tmp_path / "env-reports"
        input_dir.mkdir()

        monkeypatch.setenv("CVE_AGGREGATOR_INPUT_DIR", str(input_dir))
        monkeypatch.setenv("CVE_AGGREGATOR_SCANNER", "trivy")

        settings = load_settings()

        assert settings.input_dir == input_dir
        assert settings.scanner == "trivy"


class TestGetConfig:
    """Tests for get_config function."""

    def test_get_config_with_valid_args(self, tmp_path):
        """Test getting config with valid arguments."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        cli_args = {
            "input_dir": input_dir,
            "output_file": tmp_path / "output.json",
        }

        config = get_config(cli_args=cli_args)

        assert isinstance(config, AggregatorConfig)
        assert config.input_dir == input_dir

    def test_get_config_with_yaml(self, tmp_path):
        """Test getting config from YAML file."""
        input_dir = tmp_path / "yaml-reports"
        input_dir.mkdir()

        # Use camelCase keys in YAML
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            f"""
inputDir: {input_dir}
scanner: trivy
"""
        )

        config = get_config(config_file_path=config_file)

        assert isinstance(config, AggregatorConfig)
        assert config.input_dir == input_dir
        assert config.scanner == "trivy"


class TestRegistryAndPackages:
    """Tests for registry and packages configuration."""

    def test_registry_and_packages_from_yaml(self, tmp_path, monkeypatch):
        """Test loading registry and packages from YAML."""
        monkeypatch.chdir(tmp_path)

        config_file = tmp_path / ".cve-aggregator.yaml"
        config_file.write_text(
            """
registry: registry.defenseunicorns.com
organization: sld-45
packages:
  - name: gitlab
    version: 18.4.2-uds.0-unicorn
    architecture: amd64
  - name: gitlab-runner
    version: 18.4.0-uds.0-unicorn
    architecture: amd64
  - name: headlamp
    version: 0.35.0-uds.0-registry1
    architecture: amd64
"""
        )

        settings = AggregatorSettings()

        assert settings.registry == "registry.defenseunicorns.com"
        assert settings.organization == "sld-45"
        assert len(settings.packages) == 3
        assert settings.packages[0].name == "gitlab"
        assert settings.packages[0].version == "18.4.2-uds.0-unicorn"
        assert settings.packages[0].architecture == "amd64"
        assert settings.packages[1].name == "gitlab-runner"
        assert settings.packages[2].name == "headlamp"

    def test_packages_default_architecture(self, tmp_path, monkeypatch):
        """Test that packages use default architecture if not specified."""
        monkeypatch.chdir(tmp_path)

        config_file = tmp_path / ".cve-aggregator.yaml"
        config_file.write_text(
            """
packages:
  - name: test-package
    version: 1.0.0
"""
        )

        settings = AggregatorSettings()

        assert len(settings.packages) == 1
        assert settings.packages[0].architecture == "amd64"

    def test_to_aggregator_config_with_packages(self, tmp_path):
        """Test converting settings with packages to AggregatorConfig."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        packages = [
            PackageConfig(name="gitlab", version="18.4.2", architecture="amd64"),
            PackageConfig(name="gitlab-runner", version="18.4.0", architecture="arm64"),
        ]

        settings = AggregatorSettings(
            input_dir=input_dir,
            registry="registry.example.com",
            organization="test-org",
            packages=packages,
        )

        config = settings.to_aggregator_config()

        assert isinstance(config, AggregatorConfig)
        assert config.registry == "registry.example.com"
        assert config.organization == "test-org"
        assert len(config.packages) == 2
        assert config.packages[0].name == "gitlab"
        assert config.packages[1].architecture == "arm64"

    def test_empty_packages_list(self, tmp_path):
        """Test that empty packages list is handled correctly."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        settings = AggregatorSettings(input_dir=input_dir)

        assert settings.packages == []
        assert settings.registry is None
        assert settings.organization is None


class TestInputDirDefaultBehavior:
    """Tests for input_dir default behavior with remote packages."""

    def test_input_dir_defaults_to_cwd_reports_without_packages(self, tmp_path, monkeypatch):
        """Test that input_dir defaults to cwd/reports when no packages are configured."""
        monkeypatch.chdir(tmp_path)

        # Create reports directory for validation
        (tmp_path / "reports").mkdir()

        settings = AggregatorSettings()

        # Should default to cwd/reports for local-only scanning
        assert settings.input_dir == tmp_path / "reports"

    def test_input_dir_defaults_to_output_dir_reports_with_packages(self, tmp_path, monkeypatch):
        """Test that input_dir defaults to output_dir/reports when packages are configured."""
        monkeypatch.chdir(tmp_path)

        # Configure output file in a custom directory
        output_dir = tmp_path / "custom-output"
        output_dir.mkdir()
        output_file = output_dir / "report.json"

        # Configure packages (remote package download)
        packages = [
            PackageConfig(name="test-package", version="1.0.0", architecture="amd64"),
        ]

        settings = AggregatorSettings(
            output_file=output_file,
            packages=packages,
        )

        # input_dir should default to output_dir/reports for Docker convenience
        expected_input_dir = output_dir / "reports"
        assert settings.input_dir == expected_input_dir
        # Verify the directory was created
        assert expected_input_dir.exists()
        assert expected_input_dir.is_dir()

    def test_input_dir_explicit_override_with_packages(self, tmp_path):
        """Test that explicit input_dir overrides default even with packages configured."""
        # Create custom input directory
        custom_input = tmp_path / "my-custom-reports"
        custom_input.mkdir()

        # Create output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Configure packages
        packages = [
            PackageConfig(name="test-package", version="1.0.0"),
        ]

        settings = AggregatorSettings(
            input_dir=custom_input,
            output_file=output_dir / "report.json",
            packages=packages,
        )

        # Explicit input_dir should be respected
        assert settings.input_dir == custom_input
        # Should NOT create output_dir/reports
        assert not (output_dir / "reports").exists()

    def test_input_dir_with_packages_from_yaml(self, tmp_path, monkeypatch):
        """Test input_dir default behavior with packages loaded from YAML."""
        monkeypatch.chdir(tmp_path)

        # Create output directory
        output_dir = tmp_path / "my-output"
        output_dir.mkdir()

        config_file = tmp_path / ".cve-aggregator.yaml"
        config_file.write_text(
            f"""
outputFile: {output_dir / "unified.json"}
registry: registry.example.com
organization: test-org
packages:
  - name: test-pkg
    version: 1.0.0
"""
        )

        settings = AggregatorSettings()

        # input_dir should default to output_dir/reports
        expected_input_dir = output_dir / "reports"
        assert settings.input_dir == expected_input_dir
        assert expected_input_dir.exists()

    def test_input_dir_with_packages_cli_args(self, tmp_path):
        """Test input_dir default behavior with packages from CLI args."""
        output_dir = tmp_path / "cli-output"
        output_dir.mkdir()

        packages = [
            PackageConfig(name="cli-pkg", version="2.0.0"),
        ]

        cli_args = {
            "output_file": output_dir / "report.json",
            "packages": packages,
        }

        settings = load_settings(cli_args=cli_args)

        # input_dir should default to output_dir/reports
        expected_input_dir = output_dir / "reports"
        assert settings.input_dir == expected_input_dir
        assert expected_input_dir.exists()


class TestCreateExampleConfig:
    """Tests for create_example_config fixture."""

    def test_create_example_config(self, tmp_path, create_example_config):
        """Test creating example configuration file."""
        output_path = tmp_path / ".cve-aggregator.yaml"

        create_example_config(output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "CVE Report Aggregator Configuration" in content
        assert "inputDir:" in content
        assert "scanner:" in content

    def test_create_example_config_creates_parent_dirs(self, tmp_path, create_example_config):
        """Test that parent directories are created if needed."""
        output_path = tmp_path / "config" / "subdir" / ".cve-aggregator.yaml"

        create_example_config(output_path)

        assert output_path.exists()
        assert output_path.parent.exists()

    def test_example_config_is_valid_yaml(self, tmp_path, create_example_config):
        """Test that generated example config is valid YAML."""
        import yaml

        output_path = tmp_path / ".cve-aggregator.yaml"
        create_example_config(output_path)

        # Should be parseable as YAML (comments are ignored)
        content = output_path.read_text()
        # Remove comment-only lines for YAML parsing
        yaml_lines = [line for line in content.split("\n") if line.strip() and not line.strip().startswith("#")]
        yaml_content = "\n".join(yaml_lines)

        # Should parse without errors
        parsed = yaml.safe_load(yaml_content)
        assert isinstance(parsed, dict)


class TestAPIKeyRedaction:
    """Test that API keys are excluded from configuration representations using repr=False."""

    def test_aggregator_config_excludes_api_key(self, tmp_path):
        """Test that AggregatorConfig.__repr__() excludes the API key entirely (repr=False)."""
        from cve_report_aggregator.core.models import EnrichmentConfig

        # Create a config with an API key
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            enrich=EnrichmentConfig(
                enabled=True,
                api_key="sk-test123456789SENSITIVE",
                model="x-ai/grok-code-fast-1",
            ),
        )

        # Get the repr
        config_repr = repr(config)

        # Verify API key is excluded from repr (repr=False on the field)
        assert "api_key" not in config_repr, "API key field should be excluded from repr"
        assert "sk-test123456789SENSITIVE" not in config_repr, "Raw API key should not appear in repr"

        # Verify the key is still accessible internally
        assert config.enrich.api_key == "sk-test123456789SENSITIVE", "API key should still be accessible internally"

    def test_enrichment_config_excludes_api_key(self):
        """Test that EnrichmentConfig.__repr__() excludes the API key entirely (repr=False)."""
        from cve_report_aggregator.core.models import EnrichmentConfig

        # Create enrichment config with API key
        enrichment = EnrichmentConfig(
            enabled=True,
            api_key="sk-another-sensitive-key",
            model="gpt-4o",
        )

        # Get the repr
        enrichment_repr = repr(enrichment)

        # Verify API key is excluded from repr (repr=False on the field)
        assert "api_key" not in enrichment_repr, "API key field should be excluded from repr"
        assert "sk-another-sensitive-key" not in enrichment_repr, "Raw API key should not appear in repr"

        # Verify the key is still accessible internally
        assert enrichment.api_key == "sk-another-sensitive-key", "API key should still be accessible internally"

    def test_config_without_api_key(self, tmp_path):
        """Test that configs without API keys work normally."""
        from cve_report_aggregator.core.models import EnrichmentConfig

        # Create config without API key
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            enrich=EnrichmentConfig(
                enabled=False,
                api_key=None,
            ),
        )

        # Get the repr - should not fail
        config_repr = repr(config)

        # Should not contain REDACTED since there's no key
        assert "api_key=None" in config_repr or "api_key='<REDACTED>'" not in config_repr
