"""Tests for utility functions."""

import subprocess

from cve_report_aggregator.utils import ASCII_LOGO, check_command_exists, get_scanner_version


class TestCheckCommandExists:
    """Tests for check_command_exists function."""

    def test_command_exists(self, mock_subprocess_success):
        """Test that existing commands are detected."""
        assert check_command_exists("grype") is True

    def test_command_not_exists(self, mock_subprocess_failure):
        """Test that non-existing commands return False."""
        assert check_command_exists("nonexistent-command") is False

    def test_command_check_handles_exceptions(self, monkeypatch):
        """Test that command check handles various exceptions."""

        def mock_run(*args, **kwargs):
            raise subprocess.CalledProcessError(127, args[0])

        monkeypatch.setattr(subprocess, "run", mock_run)
        assert check_command_exists("missing") is False


class TestGetScannerVersion:
    """Tests for get_scanner_version function."""

    def test_get_grype_version(self, mock_subprocess_success):
        """Test getting Grype version."""
        version = get_scanner_version("grype")
        assert version == "0.100.0"

    def test_get_trivy_version(self, mock_subprocess_success):
        """Test getting Trivy version."""
        version = get_scanner_version("trivy")
        assert version == "0.100.0"

    def test_version_not_found_format(self, monkeypatch):
        """Test handling version output without Version: prefix."""

        class MockResult:
            stdout = "grype 0.100.0\nSome other info"
            stderr = ""
            returncode = 0

        def mock_run(*args, **kwargs):
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)
        version = get_scanner_version("grype")
        assert version == "grype 0.100.0"  # Returns first line

    def test_version_command_timeout(self, monkeypatch):
        """Test handling timeout when getting version."""

        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(args[0], 5)

        monkeypatch.setattr(subprocess, "run", mock_run)
        version = get_scanner_version("grype")
        assert version == "unknown"

    def test_version_command_error(self, monkeypatch):
        """Test handling error when getting version."""

        def mock_run(*args, **kwargs):
            raise subprocess.CalledProcessError(1, args[0], stderr="Error")

        monkeypatch.setattr(subprocess, "run", mock_run)
        version = get_scanner_version("trivy")
        assert version == "unknown"

    def test_version_command_not_found(self, mock_subprocess_not_found):
        """Test handling when scanner command not found."""
        version = get_scanner_version("grype")
        assert version == "unknown"

    def test_version_empty_output(self, monkeypatch):
        """Test handling empty version output."""

        class MockResult:
            stdout = ""
            stderr = ""
            returncode = 0

        def mock_run(*args, **kwargs):
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)
        version = get_scanner_version("grype")
        assert version == "unknown"


class TestASCIILogo:
    """Tests for ASCII logo constant."""

    def test_ascii_logo_exists(self):
        """Test that ASCII logo is defined and non-empty."""
        assert ASCII_LOGO is not None
        assert len(ASCII_LOGO) > 0
        assert isinstance(ASCII_LOGO, str)

    def test_ascii_logo_multiline(self):
        """Test that ASCII logo is multiline."""
        assert "\n" in ASCII_LOGO
        lines = ASCII_LOGO.split("\n")
        assert len(lines) > 10  # Logo should have multiple lines
