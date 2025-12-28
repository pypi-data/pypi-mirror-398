"""Tests for scanner_tools module."""

import subprocess

import pytest

from cve_report_aggregator.core.exceptions import ScannerNotFoundError
from cve_report_aggregator.processing.scanner_tools import scan_sbom_with_grype


class TestScanSbomWithGrypeFileNotFound:
    """Tests for FileNotFoundError in scan_sbom_with_grype."""

    def test_grype_command_not_found(self, tmp_path, monkeypatch):
        """Test handling when grype command is not found."""
        sbom_file = tmp_path / "test.json"
        sbom_file.write_text('{"test": "sbom"}')
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        def mock_run(*args, **kwargs):
            raise FileNotFoundError("grype not found")

        monkeypatch.setattr(subprocess, "run", mock_run)

        with pytest.raises(ScannerNotFoundError) as exc_info:
            scan_sbom_with_grype(sbom_file, output_dir, verbose=False)

        assert "grype" in str(exc_info.value)

    def test_grype_command_not_found_verbose(self, tmp_path, monkeypatch):
        """Test handling when grype command is not found with verbose mode."""
        sbom_file = tmp_path / "test.json"
        sbom_file.write_text('{"test": "sbom"}')
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        def mock_run(*args, **kwargs):
            raise FileNotFoundError("grype not found")

        monkeypatch.setattr(subprocess, "run", mock_run)

        with pytest.raises(ScannerNotFoundError) as exc_info:
            scan_sbom_with_grype(sbom_file, output_dir, verbose=True)

        assert "grype" in str(exc_info.value)
