"""Unit tests for pipeline module."""

from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from rich.progress import Progress, TaskID

from cve_report_aggregator.core.exceptions import ScannerExecutionError
from cve_report_aggregator.processing.pipeline import (
    PipelineResult,
    parallel_pipeline_processing,
    process_sbom_pipeline,
)


class TestPipelineResult:
    """Tests for PipelineResult dataclass."""

    def test_initialization_with_defaults(self, tmp_path):
        """Test PipelineResult initialization with default values."""
        sbom_file = tmp_path / "test.json"
        result = PipelineResult(sbom_file=sbom_file)

        assert result.sbom_file == sbom_file
        assert result.grype_report is None
        assert result.trivy_report is None
        assert result.error is None

    def test_initialization_with_all_fields(self, tmp_path):
        """Test PipelineResult initialization with all fields."""
        sbom_file = tmp_path / "test.json"
        grype_report = tmp_path / "grype.json"
        trivy_report = tmp_path / "trivy.json"
        error = "Test error"

        result = PipelineResult(
            sbom_file=sbom_file,
            grype_report=grype_report,
            trivy_report=trivy_report,
            error=error,
        )

        assert result.sbom_file == sbom_file
        assert result.grype_report == grype_report
        assert result.trivy_report == trivy_report
        assert result.error == error


class TestProcessSbomPipeline:
    """Tests for process_sbom_pipeline function."""

    @pytest.fixture
    def mock_progress(self):
        """Create a mock Progress instance."""
        progress = MagicMock(spec=Progress)
        return progress

    @pytest.fixture
    def test_dirs(self, tmp_path):
        """Create test directories."""
        sbom_file = tmp_path / "test.json"
        sbom_file.write_text('{"test": "sbom"}')
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        grype_output_dir = tmp_path / "grype"
        grype_output_dir.mkdir()
        trivy_output_dir = tmp_path / "trivy"
        trivy_output_dir.mkdir()

        return {
            "sbom_file": sbom_file,
            "reports_dir": reports_dir,
            "grype_output_dir": grype_output_dir,
            "trivy_output_dir": trivy_output_dir,
        }

    @patch("cve_report_aggregator.processing.pipeline.scan_sbom_with_grype")
    @patch("cve_report_aggregator.processing.pipeline.convert_to_cyclonedx")
    @patch("cve_report_aggregator.processing.pipeline.scan_with_trivy")
    def test_successful_pipeline_execution(self, mock_trivy, mock_convert, mock_grype, test_dirs, mock_progress):
        """Test successful execution of complete pipeline."""
        grype_report = test_dirs["grype_output_dir"] / "grype.json"
        cdx_file = test_dirs["trivy_output_dir"] / "cdx.json"
        trivy_report = test_dirs["trivy_output_dir"] / "trivy.json"

        mock_grype.return_value = grype_report
        mock_convert.return_value = cdx_file
        mock_trivy.return_value = trivy_report

        result = process_sbom_pipeline(
            sbom_file=test_dirs["sbom_file"],
            reports_dir=test_dirs["reports_dir"],
            grype_output_dir=test_dirs["grype_output_dir"],
            trivy_output_dir=test_dirs["trivy_output_dir"],
            verbose=False,
            progress=mock_progress,
            grype_task_id=cast(TaskID, 0),
            trivy_task_id=cast(TaskID, 1),
        )

        # Verify pipeline stages executed (both paths run in parallel)
        # Path 1: Grype scan
        mock_grype.assert_called_once_with(test_dirs["sbom_file"], test_dirs["grype_output_dir"], verbose=False)
        # Path 2: CycloneDX conversion from original SBOM (not Grype output)
        mock_convert.assert_called_once_with(test_dirs["sbom_file"], test_dirs["trivy_output_dir"], verbose=False)
        mock_trivy.assert_called_once_with(cdx_file, test_dirs["trivy_output_dir"], verbose=False)

        # Verify result
        assert result.sbom_file == test_dirs["sbom_file"]
        assert result.grype_report == grype_report
        assert result.trivy_report == trivy_report
        assert result.error is None

        # Verify progress updates
        assert mock_progress.update.call_count == 2

    @patch("cve_report_aggregator.processing.pipeline.scan_sbom_with_grype")
    def test_grype_stage_failure(self, mock_grype, test_dirs, mock_progress):
        """Test pipeline handling when Grype stage fails."""
        mock_grype.side_effect = RuntimeError("Grype scan failed")

        result = process_sbom_pipeline(
            sbom_file=test_dirs["sbom_file"],
            reports_dir=test_dirs["reports_dir"],
            grype_output_dir=test_dirs["grype_output_dir"],
            trivy_output_dir=test_dirs["trivy_output_dir"],
            verbose=False,
            progress=mock_progress,
            grype_task_id=cast(TaskID, 0),
            trivy_task_id=cast(TaskID, 1),
        )

        assert result.sbom_file == test_dirs["sbom_file"]
        assert result.grype_report is None
        assert result.trivy_report is None
        assert result.error == "Grype scan failed"

        # Progress should be updated even on failure
        assert mock_progress.update.call_count == 2

    @patch("cve_report_aggregator.processing.pipeline.scan_sbom_with_grype")
    @patch("cve_report_aggregator.processing.pipeline.convert_to_cyclonedx")
    def test_cyclonedx_conversion_failure(self, mock_convert, mock_grype, test_dirs, mock_progress):
        """Test pipeline handling when CycloneDX conversion fails."""
        grype_report = test_dirs["grype_output_dir"] / "grype.json"
        mock_grype.return_value = grype_report
        mock_convert.side_effect = RuntimeError("CycloneDX conversion failed")

        result = process_sbom_pipeline(
            sbom_file=test_dirs["sbom_file"],
            reports_dir=test_dirs["reports_dir"],
            grype_output_dir=test_dirs["grype_output_dir"],
            trivy_output_dir=test_dirs["trivy_output_dir"],
            verbose=False,
            progress=mock_progress,
            grype_task_id=cast(TaskID, 0),
            trivy_task_id=cast(TaskID, 1),
        )

        assert result.sbom_file == test_dirs["sbom_file"]
        # In parallel execution, Grype may still succeed even if Trivy path fails
        assert result.grype_report == grype_report
        assert result.trivy_report is None
        assert result.error == "CycloneDX conversion failed"

        # Both paths update progress even on partial failure
        assert mock_progress.update.call_count == 2

    @patch("cve_report_aggregator.processing.pipeline.scan_sbom_with_grype")
    @patch("cve_report_aggregator.processing.pipeline.convert_to_cyclonedx")
    @patch("cve_report_aggregator.processing.pipeline.scan_with_trivy")
    def test_trivy_stage_failure(self, mock_trivy, mock_convert, mock_grype, test_dirs, mock_progress):
        """Test pipeline handling when Trivy stage fails."""
        grype_report = test_dirs["grype_output_dir"] / "grype.json"
        cdx_file = test_dirs["trivy_output_dir"] / "cdx.json"

        mock_grype.return_value = grype_report
        mock_convert.return_value = cdx_file
        mock_trivy.side_effect = RuntimeError("Trivy scan failed")

        result = process_sbom_pipeline(
            sbom_file=test_dirs["sbom_file"],
            reports_dir=test_dirs["reports_dir"],
            grype_output_dir=test_dirs["grype_output_dir"],
            trivy_output_dir=test_dirs["trivy_output_dir"],
            verbose=False,
            progress=mock_progress,
            grype_task_id=cast(TaskID, 0),
            trivy_task_id=cast(TaskID, 1),
        )

        assert result.sbom_file == test_dirs["sbom_file"]
        assert result.grype_report == grype_report
        assert result.trivy_report is None
        assert result.error == "Trivy scan failed"

    @patch("cve_report_aggregator.processing.pipeline.scan_sbom_with_grype")
    @patch("cve_report_aggregator.processing.pipeline.convert_to_cyclonedx")
    @patch("cve_report_aggregator.processing.pipeline.scan_with_trivy")
    def test_verbose_mode_logging(self, mock_trivy, mock_convert, mock_grype, test_dirs, mock_progress):
        """Test that verbose mode produces appropriate logging."""
        grype_report = test_dirs["grype_output_dir"] / "grype.json"
        cdx_file = test_dirs["trivy_output_dir"] / "cdx.json"
        trivy_report = test_dirs["trivy_output_dir"] / "trivy.json"

        mock_grype.return_value = grype_report
        mock_convert.return_value = cdx_file
        mock_trivy.return_value = trivy_report

        result = process_sbom_pipeline(
            sbom_file=test_dirs["sbom_file"],
            reports_dir=test_dirs["reports_dir"],
            grype_output_dir=test_dirs["grype_output_dir"],
            trivy_output_dir=test_dirs["trivy_output_dir"],
            verbose=True,
            progress=mock_progress,
            grype_task_id=cast(TaskID, 0),
            trivy_task_id=cast(TaskID, 1),
        )

        # Verify verbose=False is passed to scanner functions (internal logging)
        mock_grype.assert_called_once_with(test_dirs["sbom_file"], test_dirs["grype_output_dir"], verbose=False)
        assert result.error is None


class TestParallelPipelineProcessing:
    """Tests for parallel_pipeline_processing function."""

    @pytest.fixture
    def test_dirs(self, tmp_path):
        """Create test directories with multiple SBOM files."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        sbom_files = []
        for i in range(3):
            sbom_file = reports_dir / f"sbom_{i}.json"
            sbom_file.write_text(f'{{"test": "sbom_{i}"}}')
            sbom_files.append(sbom_file)

        grype_output_dir = tmp_path / "grype"
        grype_output_dir.mkdir()
        trivy_output_dir = tmp_path / "trivy"
        trivy_output_dir.mkdir()

        return {
            "sbom_files": sbom_files,
            "reports_dir": reports_dir,
            "grype_output_dir": grype_output_dir,
            "trivy_output_dir": trivy_output_dir,
        }

    def test_empty_sbom_list(self, test_dirs):
        """Test handling of empty SBOM file list."""
        grype_reports, trivy_reports = parallel_pipeline_processing(
            sbom_files=[],
            reports_dir=test_dirs["reports_dir"],
            grype_output_dir=test_dirs["grype_output_dir"],
            trivy_output_dir=test_dirs["trivy_output_dir"],
            verbose=False,
            max_workers=2,
        )

        assert grype_reports == []
        assert trivy_reports == []

    @patch("cve_report_aggregator.processing.pipeline.scan_sbom_with_grype")
    @patch("cve_report_aggregator.processing.pipeline.convert_to_cyclonedx")
    @patch("cve_report_aggregator.processing.pipeline.scan_with_trivy")
    @patch("cve_report_aggregator.processing.pipeline.load_json_report")
    def test_single_sbom_processing(self, mock_load_json, mock_trivy, mock_convert, mock_grype, test_dirs):
        """Test single SBOM processing without parallelization overhead."""
        sbom_file = test_dirs["sbom_files"][0]
        grype_report = test_dirs["grype_output_dir"] / "grype.json"
        cdx_file = test_dirs["trivy_output_dir"] / "cdx.json"
        trivy_report = test_dirs["trivy_output_dir"] / "trivy.json"

        # Mock scanner tools
        mock_grype.return_value = grype_report
        mock_convert.return_value = cdx_file
        mock_trivy.return_value = trivy_report

        # Mock report loading - these will be mutated by adding scanner/source_file fields
        grype_mock_data = {"matches": [{"vulnerability": {"id": "CVE-2024-1"}}]}
        trivy_mock_data = {"Results": [{"Vulnerabilities": [{"VulnerabilityID": "CVE-2024-2"}]}]}
        mock_load_json.side_effect = [grype_mock_data, trivy_mock_data]

        grype_reports, trivy_reports = parallel_pipeline_processing(
            sbom_files=[sbom_file],
            reports_dir=test_dirs["reports_dir"],
            grype_output_dir=test_dirs["grype_output_dir"],
            trivy_output_dir=test_dirs["trivy_output_dir"],
            verbose=False,
            max_workers=1,
        )

        assert len(grype_reports) == 1
        assert len(trivy_reports) == 1
        # Verify fields were added by pipeline processing (note: fields have underscores)
        assert grype_reports[0]["_scanner"] == "grype"
        assert trivy_reports[0]["_scanner"] == "trivy"
        assert grype_reports[0]["_source_file"] == "sbom_0.json"
        assert trivy_reports[0]["_source_file"] == "sbom_0.json"
        # Verify original data is intact
        assert "matches" in grype_reports[0]
        assert "Results" in trivy_reports[0]

    @patch("cve_report_aggregator.processing.pipeline.scan_sbom_with_grype")
    @patch("cve_report_aggregator.processing.pipeline.convert_to_cyclonedx")
    @patch("cve_report_aggregator.processing.pipeline.scan_with_trivy")
    @patch("cve_report_aggregator.processing.pipeline.load_json_report")
    def test_multiple_sbom_parallel_processing(self, mock_load_json, mock_trivy, mock_convert, mock_grype, test_dirs):
        """Test parallel processing of multiple SBOMs."""

        # Mock scanner tools
        def mock_grype_func(sbom_file, output_dir, verbose=False):
            return output_dir / f"{sbom_file.stem}_grype.json"

        def mock_convert_func(grype_report, output_dir, verbose=False):
            return output_dir / f"{grype_report.stem}_cdx.json"

        def mock_trivy_func(cdx_file, output_dir, verbose=False):
            return output_dir / f"{cdx_file.stem}_trivy.json"

        mock_grype.side_effect = mock_grype_func
        mock_convert.side_effect = mock_convert_func
        mock_trivy.side_effect = mock_trivy_func

        # Mock report loading (3 SBOMs × 2 reports each = 6 reports)
        # Each SBOM needs a Grype report and a Trivy report
        mock_reports = []
        for i in range(3):
            # Grype report for SBOM i
            mock_reports.append({"matches": [{"vulnerability": {"id": f"CVE-2024-G{i}"}}]})
            # Trivy report for SBOM i
            mock_reports.append({"Results": [{"Vulnerabilities": [{"VulnerabilityID": f"CVE-2024-T{i}"}]}]})

        mock_load_json.side_effect = mock_reports

        grype_reports, trivy_reports = parallel_pipeline_processing(
            sbom_files=test_dirs["sbom_files"],
            reports_dir=test_dirs["reports_dir"],
            grype_output_dir=test_dirs["grype_output_dir"],
            trivy_output_dir=test_dirs["trivy_output_dir"],
            verbose=False,
            max_workers=2,
        )

        assert len(grype_reports) == 3
        assert len(trivy_reports) == 3
        # Verify all reports have correct scanner type (note: fields have underscores)
        assert all(report["_scanner"] == "grype" for report in grype_reports)
        assert all(report["_scanner"] == "trivy" for report in trivy_reports)
        # Verify original data is intact
        assert all("matches" in report for report in grype_reports)
        assert all("Results" in report for report in trivy_reports)

    @patch("cve_report_aggregator.processing.pipeline.scan_sbom_with_grype")
    def test_pipeline_failure_raises_exception(self, mock_grype, test_dirs):
        """Test that pipeline failures raise ScannerExecutionError."""
        sbom_file = test_dirs["sbom_files"][0]

        # Mock scanner failure
        mock_grype.side_effect = RuntimeError("Pipeline failed")

        with pytest.raises(ScannerExecutionError) as exc_info:
            parallel_pipeline_processing(
                sbom_files=[sbom_file],
                reports_dir=test_dirs["reports_dir"],
                grype_output_dir=test_dirs["grype_output_dir"],
                trivy_output_dir=test_dirs["trivy_output_dir"],
                verbose=False,
                max_workers=1,
            )

        error_message = str(exc_info.value)
        # Error details are in the stderr part
        assert "Pipeline failed" in error_message

    @patch("cve_report_aggregator.processing.pipeline.scan_sbom_with_grype")
    @patch("cve_report_aggregator.processing.pipeline.convert_to_cyclonedx")
    @patch("cve_report_aggregator.processing.pipeline.scan_with_trivy")
    @patch("cve_report_aggregator.processing.pipeline.load_json_report")
    def test_partial_pipeline_failures(self, mock_load_json, mock_trivy, mock_convert, mock_grype, test_dirs):
        """Test handling when some pipelines succeed and others fail."""

        def mock_grype_func(sbom_file, output_dir, verbose=False):
            # Fail on second SBOM
            if "sbom_1" in sbom_file.name:
                raise RuntimeError("Grype failed for sbom_1")
            return output_dir / f"{sbom_file.stem}_grype.json"

        mock_grype.side_effect = mock_grype_func

        with pytest.raises(ScannerExecutionError) as exc_info:
            parallel_pipeline_processing(
                sbom_files=test_dirs["sbom_files"],
                reports_dir=test_dirs["reports_dir"],
                grype_output_dir=test_dirs["grype_output_dir"],
                trivy_output_dir=test_dirs["trivy_output_dir"],
                verbose=False,
                max_workers=2,
            )

        error_message = str(exc_info.value)
        assert "Failed to process" in error_message
        assert "sbom_1.json" in error_message

    @patch("cve_report_aggregator.processing.pipeline.scan_sbom_with_grype")
    @patch("cve_report_aggregator.processing.pipeline.convert_to_cyclonedx")
    @patch("cve_report_aggregator.processing.pipeline.scan_with_trivy")
    @patch("cve_report_aggregator.processing.pipeline.load_json_report")
    def test_report_loading_failure(self, mock_load_json, mock_trivy, mock_convert, mock_grype, test_dirs):
        """Test handling when report loading fails."""

        def mock_grype_func(sbom_file, output_dir, verbose=False):
            return output_dir / f"{sbom_file.stem}_grype.json"

        def mock_convert_func(grype_report, output_dir, verbose=False):
            return output_dir / f"{grype_report.stem}_cdx.json"

        def mock_trivy_func(cdx_file, output_dir, verbose=False):
            return output_dir / f"{cdx_file.stem}_trivy.json"

        mock_grype.side_effect = mock_grype_func
        mock_convert.side_effect = mock_convert_func
        mock_trivy.side_effect = mock_trivy_func

        # Mock report loading failure - this happens in multi-file processing path
        # Single file raises directly, multi-file catches and adds to errors
        mock_load_json.side_effect = RuntimeError("Failed to load report")

        # Test with 2 files to trigger multi-file path which handles errors
        with pytest.raises(ScannerExecutionError) as exc_info:
            parallel_pipeline_processing(
                sbom_files=test_dirs["sbom_files"][:2],  # Use 2 files
                reports_dir=test_dirs["reports_dir"],
                grype_output_dir=test_dirs["grype_output_dir"],
                trivy_output_dir=test_dirs["trivy_output_dir"],
                verbose=False,
                max_workers=1,
            )

        error_message = str(exc_info.value)
        # Error should mention report loading failure
        assert "Failed to load" in error_message or "Failed to process" in error_message

    @patch("cve_report_aggregator.processing.pipeline.scan_sbom_with_grype")
    @patch("cve_report_aggregator.processing.pipeline.convert_to_cyclonedx")
    @patch("cve_report_aggregator.processing.pipeline.scan_with_trivy")
    @patch("cve_report_aggregator.processing.pipeline.load_json_report")
    @patch("cve_report_aggregator.processing.pipeline.get_optimal_workers")
    def test_max_workers_parameter(
        self, mock_get_workers, mock_load_json, mock_trivy, mock_convert, mock_grype, test_dirs
    ):
        """Test that max_workers parameter is used correctly."""
        mock_get_workers.return_value = 4

        def mock_grype_func(sbom_file, output_dir, verbose=False):
            return output_dir / f"{sbom_file.stem}_grype.json"

        def mock_convert_func(grype_report, output_dir, verbose=False):
            return output_dir / f"{grype_report.stem}_cdx.json"

        def mock_trivy_func(cdx_file, output_dir, verbose=False):
            return output_dir / f"{cdx_file.stem}_trivy.json"

        mock_grype.side_effect = mock_grype_func
        mock_convert.side_effect = mock_convert_func
        mock_trivy.side_effect = mock_trivy_func

        mock_load_json.side_effect = [
            {"matches": []},  # Grype
            {"Results": []},  # Trivy
        ] * 3

        grype_reports, trivy_reports = parallel_pipeline_processing(
            sbom_files=test_dirs["sbom_files"],
            reports_dir=test_dirs["reports_dir"],
            grype_output_dir=test_dirs["grype_output_dir"],
            trivy_output_dir=test_dirs["trivy_output_dir"],
            verbose=False,
            max_workers=4,
        )

        mock_get_workers.assert_called_once_with(4)
        assert len(grype_reports) == 3
        assert len(trivy_reports) == 3

    @patch("cve_report_aggregator.processing.pipeline.scan_sbom_with_grype")
    @patch("cve_report_aggregator.processing.pipeline.convert_to_cyclonedx")
    @patch("cve_report_aggregator.processing.pipeline.scan_with_trivy")
    @patch("cve_report_aggregator.processing.pipeline.load_json_report")
    def test_verbose_mode(self, mock_load_json, mock_trivy, mock_convert, mock_grype, test_dirs, capsys):
        """Test verbose mode produces appropriate output."""

        def mock_grype_func(sbom_file, output_dir, verbose=False):
            return output_dir / f"{sbom_file.stem}_grype.json"

        def mock_convert_func(grype_report, output_dir, verbose=False):
            return output_dir / f"{grype_report.stem}_cdx.json"

        def mock_trivy_func(cdx_file, output_dir, verbose=False):
            return output_dir / f"{cdx_file.stem}_trivy.json"

        mock_grype.side_effect = mock_grype_func
        mock_convert.side_effect = mock_convert_func
        mock_trivy.side_effect = mock_trivy_func

        mock_load_json.side_effect = [
            {"matches": []},
            {"Results": []},
        ] * 3

        grype_reports, trivy_reports = parallel_pipeline_processing(
            sbom_files=test_dirs["sbom_files"],
            reports_dir=test_dirs["reports_dir"],
            grype_output_dir=test_dirs["grype_output_dir"],
            trivy_output_dir=test_dirs["trivy_output_dir"],
            verbose=True,
            max_workers=2,
        )

        assert len(grype_reports) == 3
        assert len(trivy_reports) == 3
        # Rich output goes to stderr, can't easily test but verify no exceptions
