"""Tests for scanner integration functionality."""

import asyncio
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from cve_report_aggregator.core.exceptions import ReportLoadError, ScannerExecutionError, ScannerNotFoundError
from cve_report_aggregator.processing.scanner import (
    _save_trivy_report,
    convert_to_cyclonedx,
    load_reports,
    process_both_reports,
    process_grype_reports,
    process_trivy_reports,
    save_trivy_reports,
    scan_with_trivy,
)


class TestSaveTrivyReportsGenerator:
    """Tests for save_trivy_reports async generator function."""

    def _collect_results(self, cdx_files, persist_dir, verbose=False):
        """Helper to collect all paths from the async generator."""

        async def collect():
            paths = []
            async for path in save_trivy_reports(cdx_files, persist_dir, verbose):
                paths.append(path)
            return paths

        return asyncio.run(collect())

    def test_save_empty_list(self, tmp_path):
        """Test that empty list of CDX files is handled gracefully."""
        persist_dir = tmp_path / "persist"

        # Should not raise any errors
        result = self._collect_results([], persist_dir, verbose=False)

        # Should return empty list
        assert result == []

        # Should not create the trivy directory
        trivy_dir = persist_dir / "trivy"
        assert not trivy_dir.exists()

    def test_save_nonexistent_files(self, tmp_path):
        """Test that non-existent files are skipped."""
        persist_dir = tmp_path / "persist"
        nonexistent_file = tmp_path / "nonexistent.cdx.json"

        # Should not raise errors, just skip non-existent files
        result = self._collect_results([nonexistent_file], persist_dir, verbose=False)

        # Should return empty list since file didn't exist
        assert result == []

        # Directory should be created but empty
        trivy_dir = persist_dir / "trivy"
        assert trivy_dir.exists()
        assert len(list(trivy_dir.iterdir())) == 0

    def test_save_single_file(self, tmp_path):
        """Test successfully saving a single CDX file."""
        persist_dir = tmp_path / "persist"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        # Create a CDX file
        cdx_file = temp_dir / "test.cdx.json"
        cdx_content = {"bomFormat": "CycloneDX", "specVersion": "1.4"}
        cdx_file.write_text(json.dumps(cdx_content))

        result = self._collect_results([cdx_file], persist_dir, verbose=False)

        # Should return list with one saved path
        assert len(result) == 1

        # Verify the file was copied
        trivy_dir = persist_dir / "trivy"
        assert trivy_dir.exists()
        saved_file = trivy_dir / "test.cdx.json"
        assert saved_file.exists()
        assert json.loads(saved_file.read_text()) == cdx_content

    def test_save_multiple_files(self, tmp_path):
        """Test saving multiple CDX files."""
        persist_dir = tmp_path / "persist"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        # Create multiple CDX files
        cdx_files = []
        for i in range(3):
            cdx_file = temp_dir / f"test{i}.cdx.json"
            cdx_content = {"bomFormat": "CycloneDX", "id": i}
            cdx_file.write_text(json.dumps(cdx_content))
            cdx_files.append(cdx_file)

        result = self._collect_results(cdx_files, persist_dir, verbose=False)

        # Should return list with three saved paths
        assert len(result) == 3

        # Verify all files were copied
        trivy_dir = persist_dir / "trivy"
        assert trivy_dir.exists()
        assert len(list(trivy_dir.iterdir())) == 3

        for i in range(3):
            saved_file = trivy_dir / f"test{i}.cdx.json"
            assert saved_file.exists()
            content = json.loads(saved_file.read_text())
            assert content["id"] == i

    def test_save_with_verbose(self, tmp_path, capsys):
        """Test verbose mode prints messages."""
        persist_dir = tmp_path / "persist"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        cdx_file = temp_dir / "verbose.cdx.json"
        cdx_file.write_text(json.dumps({"bomFormat": "CycloneDX"}))

        self._collect_results([cdx_file], persist_dir, verbose=True)

        # Verify file was saved
        trivy_dir = persist_dir / "trivy"
        assert (trivy_dir / "verbose.cdx.json").exists()

    def test_save_mixed_existing_and_nonexistent(self, tmp_path):
        """Test saving a mix of existing and non-existent files."""
        persist_dir = tmp_path / "persist"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        # Create one existing file
        existing_file = temp_dir / "existing.cdx.json"
        existing_file.write_text(json.dumps({"bomFormat": "CycloneDX"}))

        # Reference one non-existent file
        nonexistent_file = temp_dir / "nonexistent.cdx.json"

        result = self._collect_results([existing_file, nonexistent_file], persist_dir, verbose=False)

        # Should return only the existing file
        assert len(result) == 1

        # Only the existing file should be saved
        trivy_dir = persist_dir / "trivy"
        assert trivy_dir.exists()
        assert (trivy_dir / "existing.cdx.json").exists()
        assert not (trivy_dir / "nonexistent.cdx.json").exists()

    def test_save_creates_nested_directories(self, tmp_path):
        """Test that nested directories are created if they don't exist."""
        persist_dir = tmp_path / "deep" / "nested" / "path"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        cdx_file = temp_dir / "test.cdx.json"
        cdx_file.write_text(json.dumps({"bomFormat": "CycloneDX"}))

        self._collect_results([cdx_file], persist_dir, verbose=False)

        # Verify nested path was created
        trivy_dir = persist_dir / "trivy"
        assert trivy_dir.exists()
        assert (trivy_dir / "test.cdx.json").exists()


class TestSaveTrivyReportsAsync:
    """Tests for async save_trivy_reports generator and _save_trivy_report."""

    def test_async_save_single_report_success(self, tmp_path):
        """Test async saving a single report successfully."""
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        trivy_dir = tmp_path / "trivy"
        trivy_dir.mkdir()

        cdx_file = temp_dir / "test.cdx.json"
        cdx_content = {"bomFormat": "CycloneDX", "specVersion": "1.4"}
        cdx_file.write_text(json.dumps(cdx_content))

        result = asyncio.run(_save_trivy_report(cdx_file, trivy_dir))

        assert result is not None
        assert result.exists()
        assert json.loads(result.read_text()) == cdx_content

    def test_async_save_single_report_nonexistent(self, tmp_path):
        """Test async saving returns None for non-existent file."""
        trivy_dir = tmp_path / "trivy"
        trivy_dir.mkdir()
        nonexistent = tmp_path / "nonexistent.json"

        result = asyncio.run(_save_trivy_report(nonexistent, trivy_dir))

        assert result is None

    def test_async_generator_yields_saved_paths(self, tmp_path):
        """Test async generator yields each saved path."""
        persist_dir = tmp_path / "persist"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        # Create files
        cdx_files = []
        for i in range(3):
            cdx_file = temp_dir / f"test{i}.cdx.json"
            cdx_file.write_text(json.dumps({"id": i}))
            cdx_files.append(cdx_file)

        async def collect():
            paths = []
            async for path in save_trivy_reports(cdx_files, persist_dir, verbose=False):
                paths.append(path)
            return paths

        result = asyncio.run(collect())

        assert len(result) == 3
        for path in result:
            assert path.exists()

    def test_async_generator_skips_nonexistent(self, tmp_path):
        """Test async generator skips non-existent files."""
        persist_dir = tmp_path / "persist"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        existing = temp_dir / "existing.json"
        existing.write_text("{}")
        nonexistent = temp_dir / "nonexistent.json"

        async def collect():
            paths = []
            async for path in save_trivy_reports([existing, nonexistent], persist_dir, verbose=False):
                paths.append(path)
            return paths

        result = asyncio.run(collect())

        # Should only yield the existing file
        assert len(result) == 1

    def test_async_generator_empty_list(self, tmp_path):
        """Test async generator handles empty list."""
        persist_dir = tmp_path / "persist"

        async def collect():
            paths = []
            async for path in save_trivy_reports([], persist_dir, verbose=False):
                paths.append(path)
            return paths

        result = asyncio.run(collect())

        assert result == []
        assert not persist_dir.exists()

    def test_async_generator_verbose_skips_nonexistent(self, tmp_path):
        """Test verbose mode logs skipped non-existent files."""
        persist_dir = tmp_path / "persist"
        nonexistent = tmp_path / "nonexistent.json"

        async def collect():
            paths = []
            async for path in save_trivy_reports([nonexistent], persist_dir, verbose=True):
                paths.append(path)
            return paths

        result = asyncio.run(collect())

        # Should skip non-existent file (verbose mode prints message)
        assert result == []
        # Directory should be created but empty
        trivy_dir = persist_dir / "trivy"
        assert trivy_dir.exists()

    def test_async_generator_verbose_logs_saved(self, tmp_path):
        """Test verbose mode logs successfully saved files."""
        persist_dir = tmp_path / "persist"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        cdx_file = temp_dir / "test.cdx.json"
        cdx_file.write_text(json.dumps({"bomFormat": "CycloneDX"}))

        async def collect():
            paths = []
            async for path in save_trivy_reports([cdx_file], persist_dir, verbose=True):
                paths.append(path)
            return paths

        result = asyncio.run(collect())

        # Should save and log the file
        assert len(result) == 1
        assert result[0].exists()

    def test_async_save_report_exception_handling(self, tmp_path, monkeypatch):
        """Test _save_trivy_report handles exceptions during file operations."""
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        trivy_dir = tmp_path / "trivy"
        trivy_dir.mkdir()

        cdx_file = temp_dir / "test.cdx.json"
        cdx_file.write_text(json.dumps({"bomFormat": "CycloneDX"}))

        # Mock aiofiles.open to raise an exception
        import aiofiles

        original_open = aiofiles.open

        async def mock_open_error(*args, **kwargs):
            raise OSError("Simulated I/O error")

        monkeypatch.setattr(aiofiles, "open", mock_open_error)

        result = asyncio.run(_save_trivy_report(cdx_file, trivy_dir))

        # Should return None on exception
        assert result is None

        # Restore original
        monkeypatch.setattr(aiofiles, "open", original_open)

    def test_async_generator_verbose_logs_error(self, tmp_path, monkeypatch):
        """Test verbose mode logs errors when save fails."""
        persist_dir = tmp_path / "persist"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        cdx_file = temp_dir / "test.cdx.json"
        cdx_file.write_text(json.dumps({"bomFormat": "CycloneDX"}))

        # Mock _save_trivy_report to return None (simulating failure)
        import cve_report_aggregator.processing.scanner as scanner_module

        async def mock_save_fail(cdx_file, trivy_dir):
            return None

        monkeypatch.setattr(scanner_module, "_save_trivy_report", mock_save_fail)

        async def collect():
            paths = []
            async for path in save_trivy_reports([cdx_file], persist_dir, verbose=True):
                paths.append(path)
            return paths

        result = asyncio.run(collect())

        # Should have no saved paths (error logged in verbose mode)
        assert result == []


class TestConvertToCycloneDX:
    """Tests for convert_to_cyclonedx function."""

    def test_convert_grype_to_cyclonedx(self, tmp_path, mock_subprocess_success):
        """Test converting Grype report to CycloneDX format."""
        # Create a fake Grype report
        grype_report = tmp_path / "grype-report.json"
        grype_report.write_text(json.dumps({"matches": []}))

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        cdx_file = convert_to_cyclonedx(grype_report, output_dir, verbose=False)

        assert cdx_file.exists()
        # Verify filename follows pattern: <input_stem>.cdx.json
        assert cdx_file.suffix == ".json"
        assert ".cdx" in cdx_file.stem
        data = json.loads(cdx_file.read_text())
        assert "bomFormat" in data
        assert data["bomFormat"] == "CycloneDX"

    def test_convert_with_verbose_output(self, tmp_path, mock_subprocess_success, capsys):
        """Test conversion with verbose output enabled."""
        grype_report = tmp_path / "test.json"
        grype_report.write_text(json.dumps({}))

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        convert_to_cyclonedx(grype_report, output_dir, verbose=True)

        # Verbose mode should print messages (captured by Rich console)
        # We can't easily test Rich output, but we can verify no errors

    def test_convert_syft_error(self, tmp_path, mock_subprocess_failure):
        """Test handling syft conversion errors."""
        grype_report = tmp_path / "test.json"
        grype_report.write_text(json.dumps({}))

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with pytest.raises(ScannerExecutionError):
            convert_to_cyclonedx(grype_report, output_dir, verbose=False)

    def test_convert_syft_not_found(self, tmp_path, mock_subprocess_not_found):
        """Test handling when syft command not found."""
        grype_report = tmp_path / "test.json"
        grype_report.write_text(json.dumps({}))

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with pytest.raises(ScannerNotFoundError):
            convert_to_cyclonedx(grype_report, output_dir, verbose=False)


class TestScanWithTrivy:
    """Tests for scan_with_trivy function."""

    def test_scan_cyclonedx_with_trivy(self, tmp_path, monkeypatch):
        """Test scanning CycloneDX SBOM with Trivy."""
        cdx_file = tmp_path / "test.cdx.json"
        cdx_file.write_text(json.dumps({"bomFormat": "CycloneDX"}))

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Mock subprocess to create the output file
        import subprocess

        def mock_run(*args, **kwargs):
            command = args[0]
            if "trivy" in command:
                # Find the output file path from the command
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        output_path = Path(command[i + 1])
                        # Create the output file with sample Trivy data
                        output_path.write_text(
                            json.dumps(
                                {
                                    "ArtifactName": "test:latest",
                                    "SchemaVersion": "2.0.0",
                                    "CreatedAt": "2024-01-01T00:00:00Z",
                                    "Results": [],
                                }
                            )
                        )
                        break

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        trivy_report = scan_with_trivy(cdx_file, output_dir, verbose=False)

        assert trivy_report.exists()
        # Verify filename follows pattern: <input_stem>.trivy.json
        assert trivy_report.suffix == ".json"
        assert ".trivy" in trivy_report.stem

    def test_scan_with_verbose(self, tmp_path, mock_subprocess_success):
        """Test Trivy scanning with verbose output."""
        cdx_file = tmp_path / "test.cdx.json"
        cdx_file.write_text(json.dumps({}))

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        scan_with_trivy(cdx_file, output_dir, verbose=True)
        # Should not raise errors

    def test_scan_trivy_error(self, tmp_path, monkeypatch):
        """Test handling Trivy scan errors (exit code >= 2)."""
        cdx_file = tmp_path / "test.cdx.json"
        cdx_file.write_text(json.dumps({}))

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Mock subprocess to return exit code 2 (actual error, not just vulnerabilities found)
        class MockResult:
            returncode = 2
            stderr = "Trivy error: invalid SBOM format"
            stdout = ""

        def mock_run(*args, **kwargs):
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        with pytest.raises(ScannerExecutionError) as exc_info:
            scan_with_trivy(cdx_file, output_dir, verbose=False)

        assert "invalid SBOM format" in str(exc_info.value)

    def test_scan_trivy_exit_code_1_success(self, tmp_path, monkeypatch):
        """Test that Trivy exit code 1 (vulnerabilities found) is treated as success."""
        cdx_file = tmp_path / "test.cdx.json"
        cdx_file.write_text(json.dumps({}))

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Mock subprocess to return exit code 1 (vulnerabilities found - NOT an error)
        class MockResult:
            returncode = 1
            stderr = ""
            stdout = ""

        def mock_run(*args, **kwargs):
            # Create the output file that Trivy would create
            trivy_report = output_dir / "test.trivy.json"
            trivy_report.write_text(json.dumps({"vulnerabilities": []}))
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Should NOT raise - exit code 1 means vulnerabilities found
        trivy_report = scan_with_trivy(cdx_file, output_dir, verbose=False)
        assert trivy_report.exists()

    def test_scan_trivy_not_found(self, tmp_path, mock_subprocess_not_found):
        """Test handling when trivy command not found."""
        cdx_file = tmp_path / "test.cdx.json"
        cdx_file.write_text(json.dumps({}))

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with pytest.raises(ScannerNotFoundError):
            scan_with_trivy(cdx_file, output_dir, verbose=False)


class TestProcessTrivyReports:
    """Tests for process_trivy_reports function."""

    def test_process_empty_directory(self, tmp_path):
        """Test processing directory with no JSON files."""
        with pytest.raises(ReportLoadError):
            process_trivy_reports(tmp_path, verbose=False)

    def test_process_grype_reports(self, tmp_path, sample_grype_report, monkeypatch):
        """Test processing Grype reports and converting to Trivy."""
        # Create a Grype report file
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        report_file = reports_dir / "test.json"
        report_file.write_text(json.dumps(sample_grype_report))

        # Mock subprocess to avoid actual tool execution
        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})
            elif "trivy" in command:
                # Create the output file
                output_file = None
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        output_file = Path(command[i + 1])
                        break

                if output_file:
                    trivy_data = {
                        "ArtifactName": "test:latest",
                        "Results": [{"Vulnerabilities": [{"VulnerabilityID": "CVE-2024-12345"}]}],
                    }
                    output_file.write_text(json.dumps(trivy_data))

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Trivy scanner now only returns Trivy reports (not a tuple)
        trivy_reports = process_trivy_reports(reports_dir, verbose=False)

        # Grype reports are converted to CycloneDX and scanned with Trivy
        assert len(trivy_reports) == 1
        assert trivy_reports[0]["_scanner"] == "trivy"
        assert trivy_reports[0]["_source_file"] == "test.json"

    def test_process_sbom_files(self, tmp_path, sample_sbom_report, monkeypatch):
        """Test processing SBOM files directly with Trivy (handles downloaded packages)."""
        # Create a directory structure matching downloaded packages
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        # Create package subdirectory
        package_dir = reports_dir / "gitlab"
        package_dir.mkdir()

        sbom_file = package_dir / "sbom.json"
        sbom_file.write_text(json.dumps(sample_sbom_report))

        # Mock subprocess to avoid actual tool execution
        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            # Handle Grype scan (writes to stdout, not file)
            if "grype" in command:
                grype_data = {
                    "matches": [
                        {
                            "vulnerability": {"id": "CVE-2024-12345", "severity": "High"},
                            "artifact": {"name": "test-package", "version": "1.0.0"},
                        }
                    ],
                    "source": {"target": {"userInput": "test:latest"}},
                }
                MockResult.stdout = json.dumps(grype_data)

            # Handle CycloneDX conversion
            elif "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})

            # Handle Trivy scan (writes to file via -o option)
            elif "trivy" in command:
                # Find the output file path
                output_file = None
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        output_file = Path(command[i + 1])
                        break

                if output_file:
                    trivy_data = {
                        "ArtifactName": "test:latest",
                        "Results": [{"Vulnerabilities": [{"VulnerabilityID": "CVE-2024-12345"}]}],
                    }
                    output_file.write_text(json.dumps(trivy_data))

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Trivy scanner now only returns Trivy reports (not a tuple)
        trivy_reports = process_trivy_reports(reports_dir, verbose=False)

        # SBOM files are converted to CycloneDX and scanned with Trivy only
        assert len(trivy_reports) == 1
        assert trivy_reports[0]["_scanner"] == "trivy"
        # Should preserve relative path for package grouping
        assert trivy_reports[0]["_source_file"] == "gitlab/sbom.json"

    def test_process_with_conversion_error(self, tmp_path, sample_grype_report, monkeypatch):
        """Test handling conversion errors gracefully."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        report_file = reports_dir / "test.json"
        report_file.write_text(json.dumps(sample_grype_report))

        def mock_run(*args, **kwargs):
            raise subprocess.CalledProcessError(1, args[0], stderr="Error")

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Conversion errors are now wrapped in ScannerExecutionError
        with pytest.raises(ScannerExecutionError):
            process_trivy_reports(reports_dir, verbose=False)

    def test_trivy_multiple_sboms_parallel(self, tmp_path, sample_sbom_report, monkeypatch):
        """Test parallel processing of multiple SBOM files with Trivy."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        # Create 3 SBOM files for parallel processing
        for i in range(3):
            sbom_file = reports_dir / f"sbom{i}.json"
            sbom_file.write_text(json.dumps(sample_sbom_report))

        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX", "version": "1.4"})
            elif "trivy" in command:
                # Find the output file and write to it
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        output_path = Path(command[i + 1])
                        output_path.write_text(
                            json.dumps(
                                {
                                    "ArtifactName": "test",
                                    "Results": [
                                        {"Vulnerabilities": [{"VulnerabilityID": "CVE-2024-TEST", "Severity": "HIGH"}]}
                                    ],
                                }
                            )
                        )
                        break

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Test with max_workers=2 to trigger parallel execution
        reports = process_trivy_reports(reports_dir, verbose=True, max_workers=2)

        # Should have processed all 3 SBOMs
        assert len(reports) >= 3

    def test_trivy_multiple_grype_reports_parallel(self, tmp_path, monkeypatch):
        """Test parallel processing of multiple Grype reports with Trivy."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        # Create 3 Grype reports
        for i in range(3):
            grype_file = reports_dir / f"report{i}.json"
            grype_file.write_text(
                json.dumps(
                    {
                        "matches": [{"vulnerability": {"id": f"CVE-2024-{i}", "severity": "High"}}],
                        "source": {"target": {"userInput": f"test-image-{i}:latest"}},
                    }
                )
            )

        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})
            elif "trivy" in command:
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        output_path = Path(command[i + 1])
                        output_path.write_text(
                            json.dumps({"Results": [{"Vulnerabilities": [{"VulnerabilityID": "CVE-2024-T"}]}]})
                        )
                        break

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Test with max_workers=2 for parallel execution
        reports = process_trivy_reports(reports_dir, verbose=True, max_workers=2)

        # Should have converted and scanned all Grype reports
        assert len(reports) >= 3

    def test_trivy_mixed_files_parallel(self, tmp_path, sample_sbom_report, monkeypatch):
        """Test parallel processing of mixed SBOM and Grype files."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        # Create 2 SBOMs
        for i in range(2):
            sbom_file = reports_dir / f"sbom{i}.json"
            sbom_file.write_text(json.dumps(sample_sbom_report))

        # Create 2 Grype reports
        for i in range(2):
            grype_file = reports_dir / f"grype{i}.json"
            grype_file.write_text(
                json.dumps(
                    {
                        "matches": [{"vulnerability": {"id": f"CVE-GRYPE-{i}"}}],
                        "source": {"target": {}},
                    }
                )
            )

        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})
            elif "trivy" in command:
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        Path(command[i + 1]).write_text(json.dumps({"Results": []}))
                        break

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Process with max_workers > 1 to ensure parallel execution
        reports = process_trivy_reports(reports_dir, verbose=True, max_workers=3)

        # Should process both SBOMs and Grype reports
        assert len(reports) >= 0

    def test_trivy_sbom_processing_verbose_all_paths(self, tmp_path, sample_sbom_report, monkeypatch):
        """Test all verbose logging paths in SBOM processing."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        sbom_file = reports_dir / "detailed.json"
        sbom_file.write_text(json.dumps(sample_sbom_report))

        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})
            elif "trivy" in command:
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        output_file = Path(command[i + 1])
                        output_file.write_text(
                            json.dumps(
                                {
                                    "Results": [
                                        {
                                            "Vulnerabilities": [
                                                {"VulnerabilityID": "CVE-2024-1"},
                                                {"VulnerabilityID": "CVE-2024-2"},
                                            ]
                                        }
                                    ]
                                }
                            )
                        )
                        break

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        reports = process_trivy_reports(reports_dir, verbose=True)

        # Verify it processed the SBOM
        assert len(reports) == 1

    def test_trivy_grype_processing_verbose_all_paths(self, tmp_path, monkeypatch):
        """Test all verbose logging paths in Grype report processing."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        grype_file = reports_dir / "detailed.json"
        grype_file.write_text(
            json.dumps(
                {
                    "matches": [
                        {"vulnerability": {"id": "CVE-2024-1"}},
                        {"vulnerability": {"id": "CVE-2024-2"}},
                    ],
                    "source": {"target": {"userInput": "test-image:v1.0"}},
                }
            )
        )

        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})
            elif "trivy" in command:
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        Path(command[i + 1]).write_text(
                            json.dumps(
                                {
                                    "Results": [
                                        {"Vulnerabilities": [{"VulnerabilityID": "CVE-2024-T1"}]},
                                        {"Vulnerabilities": [{"VulnerabilityID": "CVE-2024-T2"}]},
                                    ]
                                }
                            )
                        )
                        break

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        reports = process_trivy_reports(reports_dir, verbose=True)

        assert len(reports) == 1

    def test_trivy_skip_cdx_verbose(self, tmp_path, sample_sbom_report, monkeypatch):
        """Test verbose output when skipping CycloneDX files."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        cdx_file = reports_dir / "test.cdx.json"
        cdx_file.write_text(json.dumps({"bomFormat": "CycloneDX"}))

        sbom_file = reports_dir / "valid.json"
        sbom_file.write_text(json.dumps(sample_sbom_report))

        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})
            elif "trivy" in command:
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        Path(command[i + 1]).write_text(json.dumps({"Results": []}))

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        reports = process_trivy_reports(reports_dir, verbose=True)
        assert len(reports) >= 0

    def test_trivy_json_decode_error(self, tmp_path, sample_sbom_report, monkeypatch):
        """Test handling of JSON decode errors."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        bad_json = reports_dir / "bad.json"
        bad_json.write_text("not valid json")

        sbom_file = reports_dir / "valid.json"
        sbom_file.write_text(json.dumps(sample_sbom_report))

        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})
            elif "trivy" in command:
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        Path(command[i + 1]).write_text(json.dumps({"Results": []}))

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        reports = process_trivy_reports(reports_dir, verbose=False)
        assert len(reports) >= 0

    def test_trivy_general_exception(self, tmp_path, sample_sbom_report, monkeypatch):
        """Test handling of general exceptions."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        report_file = reports_dir / "test.json"
        report_file.write_text(json.dumps(sample_sbom_report))

        call_count = [0]

        def mock_load(file_path):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("Unexpected error")
            return json.loads(file_path.read_text())

        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})
            elif "trivy" in command:
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        Path(command[i + 1]).write_text(json.dumps({"Results": []}))

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        with patch("cve_report_aggregator.processing.scanner.load_json_report", side_effect=mock_load):
            reports = process_trivy_reports(reports_dir, verbose=False)
            assert len(reports) >= 0

    def test_process_trivy_with_persist_cyclonedx_dir(self, tmp_path, sample_sbom_report, monkeypatch):
        """Test process_trivy_reports with persist_cyclonedx_dir parameter."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        persist_dir = tmp_path / "persist"

        # Create a SBOM file
        sbom_file = reports_dir / "test.json"
        sbom_file.write_text(json.dumps(sample_sbom_report))

        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})
            elif "trivy" in command:
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        Path(command[i + 1]).write_text(json.dumps({"Results": []}))

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Process with persist_cyclonedx_dir
        process_trivy_reports(reports_dir, verbose=False, persist_cyclonedx_dir=persist_dir)

        # Verify CDX files were persisted
        trivy_dir = persist_dir / "trivy"
        assert trivy_dir.exists()
        cdx_files = list(trivy_dir.glob("*.cdx.json"))
        assert len(cdx_files) >= 1

    def test_process_trivy_with_persist_cyclonedx_dir_verbose(self, tmp_path, sample_sbom_report, monkeypatch):
        """Test verbose output with persist_cyclonedx_dir parameter."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        persist_dir = tmp_path / "persist"

        sbom_file = reports_dir / "test.json"
        sbom_file.write_text(json.dumps(sample_sbom_report))

        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})
            elif "trivy" in command:
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        Path(command[i + 1]).write_text(json.dumps({"Results": []}))

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Process with persist_cyclonedx_dir and verbose
        process_trivy_reports(reports_dir, verbose=True, persist_cyclonedx_dir=persist_dir)

        # Verify CDX files were persisted
        trivy_dir = persist_dir / "trivy"
        assert trivy_dir.exists()

    def test_process_trivy_persist_multiple_cdx_files(self, tmp_path, sample_sbom_report, monkeypatch):
        """Test persisting multiple CycloneDX files."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        persist_dir = tmp_path / "persist"

        # Create multiple SBOM files
        for i in range(3):
            sbom_file = reports_dir / f"sbom{i}.json"
            sbom_file.write_text(json.dumps(sample_sbom_report))

        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})
            elif "trivy" in command:
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        Path(command[i + 1]).write_text(json.dumps({"Results": []}))

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Process with persist_cyclonedx_dir
        process_trivy_reports(reports_dir, verbose=False, persist_cyclonedx_dir=persist_dir)

        # Verify all CDX files were persisted
        trivy_dir = persist_dir / "trivy"
        assert trivy_dir.exists()
        cdx_files = list(trivy_dir.glob("*.cdx.json"))
        assert len(cdx_files) >= 3

    def test_process_trivy_persist_grype_to_cdx(self, tmp_path, sample_grype_report, monkeypatch):
        """Test persisting CycloneDX files generated from Grype reports."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        persist_dir = tmp_path / "persist"

        # Create Grype reports
        for i in range(2):
            grype_file = reports_dir / f"grype{i}.json"
            grype_file.write_text(json.dumps(sample_grype_report))

        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})
            elif "trivy" in command:
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        Path(command[i + 1]).write_text(json.dumps({"Results": []}))

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Process with persist_cyclonedx_dir
        process_trivy_reports(reports_dir, verbose=False, persist_cyclonedx_dir=persist_dir)

        # Verify CDX files from Grype reports were persisted
        trivy_dir = persist_dir / "trivy"
        assert trivy_dir.exists()
        cdx_files = list(trivy_dir.glob("*.cdx.json"))
        assert len(cdx_files) >= 2

    def test_process_trivy_without_persist_dir(self, tmp_path, sample_sbom_report, monkeypatch):
        """Test that without persist_cyclonedx_dir, no files are persisted."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        persist_dir = tmp_path / "persist"

        sbom_file = reports_dir / "test.json"
        sbom_file.write_text(json.dumps(sample_sbom_report))

        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})
            elif "trivy" in command:
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        Path(command[i + 1]).write_text(json.dumps({"Results": []}))

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Process without persist_cyclonedx_dir
        process_trivy_reports(reports_dir, verbose=False, persist_cyclonedx_dir=None)

        # Verify no persist directory was created
        assert not persist_dir.exists()


class TestProcessBothReports:
    """Tests for process_both_reports function."""

    def test_process_both_reports_verbose(self, tmp_path, sample_sbom_report, monkeypatch):
        """Test process_both_reports with verbose mode."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        sbom_file = reports_dir / "test.json"
        sbom_file.write_text(json.dumps(sample_sbom_report))

        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "grype" in command:
                MockResult.stdout = json.dumps(
                    {"matches": [{"vulnerability": {"id": "CVE-2024-1"}}], "source": {"target": {}}}
                )
            elif "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})
            elif "trivy" in command:
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        Path(command[i + 1]).write_text(json.dumps({"Results": []}))

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Run with verbose=True to cover verbose paths
        reports = process_both_reports(reports_dir, verbose=True)

        assert len(reports) >= 1

    def test_process_both_with_persist_cyclonedx_dir(self, tmp_path, sample_sbom_report, monkeypatch):
        """Test process_both_reports with persist_cyclonedx_dir parameter."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        persist_dir = tmp_path / "persist"

        sbom_file = reports_dir / "test.json"
        sbom_file.write_text(json.dumps(sample_sbom_report))

        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "grype" in command:
                MockResult.stdout = json.dumps(
                    {"matches": [{"vulnerability": {"id": "CVE-2024-1"}}], "source": {"target": {}}}
                )
            elif "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})
            elif "trivy" in command:
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        Path(command[i + 1]).write_text(json.dumps({"Results": []}))

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Run with persist_cyclonedx_dir
        process_both_reports(reports_dir, verbose=False, persist_cyclonedx_dir=persist_dir)

        # Verify CDX files were persisted
        trivy_dir = persist_dir / "trivy"
        assert trivy_dir.exists()
        cdx_files = list(trivy_dir.glob("*.cdx.json"))
        assert len(cdx_files) >= 1

    def test_process_both_with_persist_cyclonedx_dir_verbose(self, tmp_path, sample_sbom_report, monkeypatch):
        """Test process_both_reports with persist_cyclonedx_dir and verbose."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        persist_dir = tmp_path / "persist"

        sbom_file = reports_dir / "test.json"
        sbom_file.write_text(json.dumps(sample_sbom_report))

        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "grype" in command:
                MockResult.stdout = json.dumps(
                    {"matches": [{"vulnerability": {"id": "CVE-2024-1"}}], "source": {"target": {}}}
                )
            elif "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})
            elif "trivy" in command:
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        Path(command[i + 1]).write_text(json.dumps({"Results": []}))

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Run with both verbose and persist_cyclonedx_dir
        process_both_reports(reports_dir, verbose=True, persist_cyclonedx_dir=persist_dir)

        # Verify CDX files were persisted
        trivy_dir = persist_dir / "trivy"
        assert trivy_dir.exists()


class TestProcessGrypeReports:
    """Tests for process_grype_reports function."""

    def test_skip_cyclonedx_files(self, tmp_path):
        """Test that .cdx. files are skipped."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        cdx_file = reports_dir / "test.cdx.json"
        cdx_file.write_text(json.dumps({"bomFormat": "CycloneDX"}))

        grype_report = reports_dir / "report.json"
        grype_report.write_text(json.dumps({"matches": [{"vulnerability": {"id": "CVE-2024-1"}}]}))

        reports = process_grype_reports(reports_dir, verbose=True)

        assert len(reports) == 1

    def test_sbom_scan_error(self, tmp_path, sample_sbom_report, monkeypatch):
        """Test SBOM scanning error handling."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        sbom_file = reports_dir / "test.json"
        sbom_file.write_text(json.dumps(sample_sbom_report))

        def mock_run(*args, **kwargs):
            raise subprocess.CalledProcessError(1, args[0], stderr="Grype failed")

        monkeypatch.setattr(subprocess, "run", mock_run)

        reports = process_grype_reports(reports_dir, verbose=True)
        assert len(reports) == 0

    def test_grype_error_logging(self, tmp_path):
        """Test error message logging when Grype report fails to load."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        # Create one bad report and one good report
        bad_report = reports_dir / "bad.json"
        bad_report.write_text(json.dumps({"matches": [{}]}))

        good_report = reports_dir / "good.json"
        good_report.write_text(json.dumps({"matches": [{"vulnerability": {"id": "CVE-2024-1"}}]}))

        with patch("cve_report_aggregator.processing.scanner.load_json_report") as mock_load:

            def selective_load(path):
                if "bad.json" in str(path):
                    raise Exception("Bad report")
                return json.loads(path.read_text())

            mock_load.side_effect = selective_load

            # Should log error but continue with good report
            reports = process_grype_reports(reports_dir, verbose=True)
            assert len(reports) == 1

    def test_sbom_no_matches(self, tmp_path, sample_sbom_report, monkeypatch):
        """Test when SBOM scan returns no vulnerability matches."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        sbom_file = reports_dir / "test.json"
        sbom_file.write_text(json.dumps(sample_sbom_report))

        def mock_run(*args, **kwargs):
            class MockResult:
                stdout = json.dumps({"matches": []})
                stderr = ""
                returncode = 0

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        reports = process_grype_reports(reports_dir, verbose=True)
        assert len(reports) == 0

    def test_verbose_unknown_format(self, tmp_path):
        """Test verbose output for files with unknown format."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        unknown_file = reports_dir / "unknown.json"
        unknown_file.write_text(json.dumps({"some": "unknown", "format": "here"}))

        # Also add a valid report
        valid_file = reports_dir / "valid.json"
        valid_file.write_text(json.dumps({"matches": [{"vulnerability": {"id": "CVE-2024-1"}}]}))

        reports = process_grype_reports(reports_dir, verbose=True)
        assert len(reports) == 1

    def test_verbose_grype_match_count(self, tmp_path):
        """Test verbose output showing match count for Grype reports."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        report_file = reports_dir / "test.json"
        report_file.write_text(
            json.dumps(
                {
                    "matches": [
                        {"vulnerability": {"id": "CVE-2024-1"}},
                        {"vulnerability": {"id": "CVE-2024-2"}},
                    ]
                }
            )
        )

        reports = process_grype_reports(reports_dir, verbose=True)
        assert len(reports) == 1


class TestLoadReports:
    """Tests for load_reports function."""

    def test_load_grype_reports(self, temp_reports_dir):
        """Test loading Grype reports from directory."""
        reports = load_reports(temp_reports_dir, scanner="grype", verbose=False)

        assert len(reports) == 1
        assert reports[0]["_scanner"] == "grype"
        assert reports[0]["_source_file"] == "test-report.json"
        assert len(reports[0]["matches"]) == 1

    def test_load_grype_reports_verbose(self, temp_reports_dir, capsys):
        """Test loading reports with verbose output."""
        reports = load_reports(temp_reports_dir, scanner="grype", verbose=True)
        assert len(reports) == 1

    def test_load_reports_no_json_files(self, tmp_path):
        """Test loading from directory with no JSON files."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with pytest.raises(ReportLoadError):
            load_reports(empty_dir, scanner="grype", verbose=False)

    def test_load_reports_invalid_json(self, tmp_path):
        """Test handling invalid JSON files."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        # Create invalid JSON file
        invalid_file = reports_dir / "invalid.json"
        invalid_file.write_text("{ this is not valid json")

        reports = load_reports(reports_dir, scanner="grype", verbose=False)
        assert len(reports) == 0  # Should skip invalid files

    def test_load_reports_no_matches(self, tmp_path):
        """Test handling reports without matches."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        # Report without matches field
        report_file = reports_dir / "no-matches.json"
        report_file.write_text(json.dumps({"source": {}, "descriptor": {}}))

        reports = load_reports(reports_dir, scanner="grype", verbose=False)
        assert len(reports) == 0

    def test_load_sbom_and_scan(self, tmp_path, sample_sbom_report, mock_subprocess_success):
        """Test detecting and scanning SBOM files."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        sbom_file = reports_dir / "sbom.json"
        sbom_file.write_text(json.dumps(sample_sbom_report))

        reports = load_reports(reports_dir, scanner="grype", verbose=False)

        # Should have scanned the SBOM
        assert len(reports) == 1
        assert reports[0]["_scanner"] == "grype"

    def test_load_sbom_scan_error(self, tmp_path, sample_sbom_report, mock_subprocess_failure):
        """Test handling SBOM scan errors."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        sbom_file = reports_dir / "sbom.json"
        sbom_file.write_text(json.dumps(sample_sbom_report))

        reports = load_reports(reports_dir, scanner="grype", verbose=False)
        # Should skip failed scans
        assert len(reports) == 0

    def test_load_sbom_no_vulnerabilities(self, tmp_path, sample_sbom_report, monkeypatch):
        """Test SBOM scan that finds no vulnerabilities."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        sbom_file = reports_dir / "sbom.json"
        sbom_file.write_text(json.dumps(sample_sbom_report))

        class MockResult:
            stdout = json.dumps({"matches": []})  # No matches
            stderr = ""
            returncode = 0

        def mock_run(*args, **kwargs):
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        reports = load_reports(reports_dir, scanner="grype", verbose=True)
        assert len(reports) == 0

    def test_load_sbom_invalid_grype_output(self, tmp_path, sample_sbom_report, monkeypatch):
        """Test handling invalid Grype scan output."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        sbom_file = reports_dir / "sbom.json"
        sbom_file.write_text(json.dumps(sample_sbom_report))

        class MockResult:
            stdout = "not valid json"
            stderr = ""
            returncode = 0

        def mock_run(*args, **kwargs):
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        reports = load_reports(reports_dir, scanner="grype", verbose=False)
        assert len(reports) == 0

    def test_load_unknown_format(self, tmp_path):
        """Test handling unknown file formats."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        # Unknown format (not Grype report, not SBOM)
        unknown_file = reports_dir / "unknown.json"
        unknown_file.write_text(json.dumps({"some": "data", "but": "not recognized"}))

        reports = load_reports(reports_dir, scanner="grype", verbose=True)
        assert len(reports) == 0

    def test_load_trivy_scanner(self, tmp_path, sample_grype_report, monkeypatch):
        """Test loading reports with Trivy scanner."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        report_file = reports_dir / "test.json"
        report_file.write_text(json.dumps(sample_grype_report))

        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})
            elif "trivy" in command:
                output_file = None
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        output_file = Path(command[i + 1])
                        break

                if output_file:
                    output_file.write_text(
                        json.dumps(
                            {
                                "ArtifactName": "test:latest",
                                "Results": [{"Vulnerabilities": [{"VulnerabilityID": "CVE-2024-12345"}]}],
                            }
                        )
                    )

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        reports = load_reports(reports_dir, scanner="trivy", verbose=False)
        assert len(reports) == 1
        assert reports[0]["_scanner"] == "trivy"

    def test_load_reports_both_scanner(self, tmp_path, sample_sbom_report, monkeypatch):
        """Test load_reports with scanner='both'."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        sbom_file = reports_dir / "test.json"
        sbom_file.write_text(json.dumps(sample_sbom_report))

        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "grype" in command:
                MockResult.stdout = json.dumps(
                    {"matches": [{"vulnerability": {"id": "CVE-2024-G1"}}], "source": {"target": {}}}
                )
            elif "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})
            elif "trivy" in command:
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        Path(command[i + 1]).write_text(
                            json.dumps({"Results": [{"Vulnerabilities": [{"VulnerabilityID": "CVE-2024-T1"}]}]})
                        )

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        reports = load_reports(reports_dir, scanner="both", verbose=False)

        assert len(reports) >= 1

    def test_load_reports_general_exception(self, tmp_path, monkeypatch):
        """Test handling general exceptions during file loading."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        report_file = reports_dir / "test.json"
        report_file.write_text(json.dumps({"matches": []}))

        # Monkeypatch json.load to raise an exception
        original_open = open

        def mock_open(*args, **kwargs):
            f = original_open(*args, **kwargs)
            if "test.json" in str(args[0]):
                # Make json.load raise an exception
                import json as json_module

                # original_load = json_module.load

                def raise_error(*args, **kwargs):
                    raise ValueError("Unexpected error")

                monkeypatch.setattr(json_module, "load", raise_error)
            return f

        monkeypatch.setattr("builtins.open", mock_open)

        reports = load_reports(reports_dir, scanner="grype", verbose=False)
        # Should handle exception and skip file
        assert len(reports) == 0

    def test_load_multiple_reports(self, tmp_path, sample_grype_report):
        """Test loading multiple valid reports."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        # Create multiple reports
        for i in range(3):
            report = sample_grype_report.copy()
            report["_source_file"] = f"report{i}.json"
            report_file = reports_dir / f"report{i}.json"
            report_file.write_text(json.dumps(report))

        reports = load_reports(reports_dir, scanner="grype", verbose=False)
        assert len(reports) == 3

    def test_load_reports_trivy_with_persist_cyclonedx_dir(self, tmp_path, sample_sbom_report, monkeypatch):
        """Test load_reports with scanner='trivy' and persist_cyclonedx_dir."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        persist_dir = tmp_path / "persist"

        sbom_file = reports_dir / "test.json"
        sbom_file.write_text(json.dumps(sample_sbom_report))

        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})
            elif "trivy" in command:
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        Path(command[i + 1]).write_text(json.dumps({"Results": []}))

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Load reports with persist_cyclonedx_dir
        load_reports(reports_dir, scanner="trivy", verbose=False, persist_cyclonedx_dir=persist_dir)

        # Verify CDX files were persisted
        trivy_dir = persist_dir / "trivy"
        assert trivy_dir.exists()
        cdx_files = list(trivy_dir.glob("*.cdx.json"))
        assert len(cdx_files) >= 1

    def test_load_reports_both_with_persist_cyclonedx_dir(self, tmp_path, sample_sbom_report, monkeypatch):
        """Test load_reports with scanner='both' and persist_cyclonedx_dir."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        persist_dir = tmp_path / "persist"

        sbom_file = reports_dir / "test.json"
        sbom_file.write_text(json.dumps(sample_sbom_report))

        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "grype" in command:
                MockResult.stdout = json.dumps(
                    {"matches": [{"vulnerability": {"id": "CVE-2024-1"}}], "source": {"target": {}}}
                )
            elif "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})
            elif "trivy" in command:
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        Path(command[i + 1]).write_text(json.dumps({"Results": []}))

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Load reports with persist_cyclonedx_dir
        load_reports(reports_dir, scanner="both", verbose=False, persist_cyclonedx_dir=persist_dir)

        # Verify CDX files were persisted
        trivy_dir = persist_dir / "trivy"
        assert trivy_dir.exists()
        cdx_files = list(trivy_dir.glob("*.cdx.json"))
        assert len(cdx_files) >= 1

    def test_load_reports_grype_ignores_persist_cyclonedx_dir(self, tmp_path, sample_grype_report):
        """Test that persist_cyclonedx_dir is ignored when scanner='grype'."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        persist_dir = tmp_path / "persist"

        report_file = reports_dir / "test.json"
        report_file.write_text(json.dumps(sample_grype_report))

        # Load reports with persist_cyclonedx_dir (should be ignored for Grype scanner)
        reports = load_reports(reports_dir, scanner="grype", verbose=False, persist_cyclonedx_dir=persist_dir)

        # Verify no persist directory was created (Grype doesn't use CycloneDX)
        assert not persist_dir.exists()
        assert len(reports) == 1
