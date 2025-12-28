"""Test case-insensitive log level support across all configuration sources."""

import os
from pathlib import Path
from typing import cast

import pytest

from cve_report_aggregator.core.config import AggregatorSettings, get_config, load_settings
from cve_report_aggregator.core.models import LogLevelType


class TestLogLevelCaseInsensitive:
    """Test that log_level accepts case-insensitive values from all sources."""

    @pytest.mark.parametrize(
        "input_value,expected",
        [
            ("debug", "DEBUG"),
            ("DEBUG", "DEBUG"),
            ("Debug", "DEBUG"),
            ("info", "INFO"),
            ("INFO", "INFO"),
            ("Info", "INFO"),
            ("warning", "WARNING"),
            ("WARNING", "WARNING"),
            ("Warning", "WARNING"),
            ("error", "ERROR"),
            ("ERROR", "ERROR"),
            ("Error", "ERROR"),
            ("critical", "CRITICAL"),
            ("CRITICAL", "CRITICAL"),
            ("Critical", "CRITICAL"),
        ],
    )
    def test_log_level_case_insensitive_direct(self, input_value: str, expected: str, tmp_path: Path):
        """Test AggregatorSettings normalizes log_level to uppercase."""
        # Create a temporary input directory to satisfy validation
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        # Cast to LogLevelType to satisfy ty's strict type checking
        settings = AggregatorSettings(log_level=cast(LogLevelType, input_value), input_dir=input_dir)
        assert settings.log_level == expected

    @pytest.mark.parametrize(
        "input_value,expected",
        [
            ("debug", "DEBUG"),
            ("Info", "INFO"),
            ("WARNING", "WARNING"),
            ("error", "ERROR"),
            ("Critical", "CRITICAL"),
        ],
    )
    def test_log_level_case_insensitive_via_cli_args(self, input_value: str, expected: str, tmp_path: Path):
        """Test get_config normalizes log_level from CLI arguments."""
        # Create a temporary input directory to satisfy validation
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        config = get_config(cli_args={"log_level": input_value, "input_dir": input_dir})
        assert config.log_level == expected

    @pytest.mark.parametrize(
        "env_value,expected",
        [
            ("debug", "DEBUG"),
            ("Info", "INFO"),
            ("WARNING", "WARNING"),
        ],
    )
    def test_log_level_case_insensitive_from_env_var(self, env_value: str, expected: str, monkeypatch, tmp_path: Path):
        """Test log_level normalization from environment variables."""
        # Create a temporary input directory to satisfy validation
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        # Clean environment
        for key in list(os.environ.keys()):
            if key.startswith("CVE_AGGREGATOR_"):
                monkeypatch.delenv(key, raising=False)

        # Set test environment variable
        monkeypatch.setenv("CVE_AGGREGATOR_LOG_LEVEL", env_value)

        settings = AggregatorSettings(input_dir=input_dir)
        assert settings.log_level == expected

    def test_log_level_case_insensitive_from_yaml(self, tmp_path: Path):
        """Test log_level normalization from YAML configuration file."""
        # Create YAML config with lowercase log level
        config_file = tmp_path / "test-config.yaml"
        config_file.write_text("logLevel: debug\nscanner: grype\nmode: highest-score\n")

        settings = load_settings(config_file_path=config_file)
        assert settings.log_level == "DEBUG"

    def test_log_level_mixed_case_from_yaml(self, tmp_path: Path):
        """Test log_level with mixed case from YAML."""
        config_file = tmp_path / "test-config.yaml"
        config_file.write_text("logLevel: Warning\nscanner: grype\n")

        settings = load_settings(config_file_path=config_file)
        assert settings.log_level == "WARNING"
