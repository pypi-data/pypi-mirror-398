"""Tests for orchestrator module."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from cve_report_aggregator.context import AppContext
from cve_report_aggregator.core.exceptions import ReportLoadError
from cve_report_aggregator.core.models import AggregatorConfig, PackageConfig
from cve_report_aggregator.core.orchestrator import (
    AggregationResult,
    acquire_sboms,
    aggregate_statistics,
    create_executive_summary_report,
    enrich_report,
    load_and_group_reports,
    process_package_reports,
    run_aggregation,
)


class TestAcquireSBOMs:
    """Tests for acquire_sboms function."""

    def test_acquire_sboms_local_packages(self, tmp_path, mock_subprocess_success):
        """Test SBOM acquisition from local packages."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            download_remote_packages=False,
        )
        context = AppContext(config)

        # Mock local package scanning
        with patch("cve_report_aggregator.core.orchestrator.scan_local_packages") as mock_scan:
            mock_scan.return_value = [tmp_path / "sbom1.json", tmp_path / "sbom2.json"]

            sboms, local_found = acquire_sboms(context)

            assert len(sboms) == 2
            assert local_found is True
            mock_scan.assert_called_once()

    def test_acquire_sboms_remote_packages(self, tmp_path):
        """Test SBOM acquisition from remote packages."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            download_remote_packages=True,
            registry="registry.example.com",
            organization="my-org",
            packages=[PackageConfig(name="test-package", version="1.0.0")],
        )
        context = AppContext(config)

        # Mock remote package downloading
        with (
            patch("cve_report_aggregator.core.orchestrator.check_command_exists") as mock_check,
            patch("cve_report_aggregator.core.orchestrator.download_package_sboms") as mock_download,
        ):
            mock_check.return_value = False  # No zarf command
            mock_download.return_value = [tmp_path / "remote-sbom1.json"]

            sboms, local_found = acquire_sboms(context)

            assert len(sboms) == 1
            assert local_found is False
            mock_download.assert_called_once()

    def test_acquire_sboms_no_sources(self, tmp_path):
        """Test SBOM acquisition when no sources are configured."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            download_remote_packages=False,
        )
        context = AppContext(config)

        with patch("cve_report_aggregator.core.orchestrator.check_command_exists") as mock_check:
            mock_check.return_value = False  # No zarf command

            sboms, local_found = acquire_sboms(context)

            assert len(sboms) == 0
            assert local_found is False

    def test_acquire_sboms_local_only_with_local_packages(self, tmp_path):
        """Test local_only mode with local packages found."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            local_only=True,
            download_remote_packages=True,  # Should be ignored
        )
        context = AppContext(config)

        with (
            patch("cve_report_aggregator.core.orchestrator.check_command_exists") as mock_check,
            patch("cve_report_aggregator.core.orchestrator.scan_local_packages") as mock_scan,
        ):
            mock_check.return_value = True  # Zarf command exists
            mock_scan.return_value = [tmp_path / "sbom1.json"]

            sboms, local_found = acquire_sboms(context)

            # Should return local packages
            assert len(sboms) == 1
            assert local_found is True

    def test_acquire_sboms_local_only_no_local_packages(self, tmp_path):
        """Test local_only mode with no local packages."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            local_only=True,
            download_remote_packages=True,  # Should be ignored
        )
        context = AppContext(config)

        with patch("cve_report_aggregator.core.orchestrator.check_command_exists") as mock_check:
            mock_check.return_value = False  # No zarf command

            sboms, local_found = acquire_sboms(context)

            # Should return empty (skip remote downloads)
            assert len(sboms) == 0
            assert local_found is False

    def test_acquire_sboms_local_scan_failure(self, tmp_path):
        """Test local package scan failure handling."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            download_remote_packages=True,
            registry="registry.example.com",
            organization="test-org",
            packages=[PackageConfig(name="test-package", version="1.0.0")],
        )
        context = AppContext(config)

        with (
            patch("cve_report_aggregator.core.orchestrator.scan_local_packages") as mock_scan,
            patch("cve_report_aggregator.core.orchestrator.download_package_sboms") as mock_download,
        ):
            # Simulate local scan failure with ValueError
            mock_scan.side_effect = ValueError("Scan failed")
            mock_download.return_value = [tmp_path / "remote.json"]

            sboms, local_found = acquire_sboms(context)

            # Should fall back to remote download
            assert len(sboms) == 1
            assert local_found is False

    def test_acquire_sboms_remote_download_failure(self, tmp_path):
        """Test remote download failure."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            download_remote_packages=True,
            registry="registry.example.com",
            organization="test-org",
            packages=[PackageConfig(name="test-package", version="1.0.0")],
        )
        context = AppContext(config)

        with (
            patch("cve_report_aggregator.core.orchestrator.check_command_exists") as mock_check,
            patch("cve_report_aggregator.core.orchestrator.download_package_sboms") as mock_download,
        ):
            mock_check.return_value = False  # No zarf
            mock_download.side_effect = RuntimeError("Download failed")

            # Should raise the download error
            with pytest.raises(RuntimeError, match="Download failed"):
                acquire_sboms(context)

    def test_acquire_sboms_local_only_skips_remote_when_local_found(self, tmp_path):
        """Test that local_only=True skips remote download even when local packages are found."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            local_only=True,
            download_remote_packages=True,
        )
        context = AppContext(config)

        with (
            patch("cve_report_aggregator.core.orchestrator.check_command_exists") as mock_check,
            patch("cve_report_aggregator.core.orchestrator.scan_local_packages") as mock_scan,
        ):
            mock_check.return_value = True
            mock_scan.return_value = [tmp_path / "local.json"]

            sboms, local_found = acquire_sboms(context)

            # Should return local packages and mark as found
            assert len(sboms) == 1
            assert local_found is True

    def test_acquire_sboms_no_zarf_no_remote(self, tmp_path):
        """Test when zarf is not available and remote downloads are disabled."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            download_remote_packages=False,
        )
        context = AppContext(config)

        with patch("cve_report_aggregator.core.orchestrator.check_command_exists") as mock_check:
            mock_check.return_value = False  # No zarf

            sboms, local_found = acquire_sboms(context)

            assert len(sboms) == 0
            assert local_found is False


class TestLoadAndGroupReports:
    """Tests for load_and_group_reports function."""

    def test_load_and_group_single_package(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test loading reports when no packages are configured."""
        # Create a sample report file
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        report_file = reports_dir / "test.json"
        report_file.write_text(json.dumps(sample_grype_report))

        config = AggregatorConfig(
            input_dir=reports_dir,
            output_file=tmp_path / "output.json",
        )
        context = AppContext(config)

        reports_by_package = load_and_group_reports(context)

        assert "unified" in reports_by_package
        assert len(reports_by_package["unified"]) >= 1

    def test_load_and_group_multiple_packages(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test loading reports grouped by package."""
        # Create package-specific report files
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        # Package 1
        pkg1_dir = reports_dir / "package1"
        pkg1_dir.mkdir()
        (pkg1_dir / "report1.json").write_text(json.dumps(sample_grype_report))

        # Package 2
        pkg2_dir = reports_dir / "package2"
        pkg2_dir.mkdir()
        (pkg2_dir / "report2.json").write_text(json.dumps(sample_grype_report))

        config = AggregatorConfig(
            input_dir=reports_dir,
            output_file=tmp_path / "output.json",
            download_remote_packages=True,
            packages=[
                PackageConfig(name="package1", version="1.0.0"),
                PackageConfig(name="package2", version="2.0.0"),
            ],
        )
        context = AppContext(config)

        reports_by_package = load_and_group_reports(context)

        assert "package1" in reports_by_package
        assert "package2" in reports_by_package
        assert len(reports_by_package["package1"]) >= 1
        assert len(reports_by_package["package2"]) >= 1

    def test_load_and_group_no_reports(self, tmp_path, mock_subprocess_success):
        """Test error when no reports are found."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        config = AggregatorConfig(
            input_dir=reports_dir,
            output_file=tmp_path / "output.json",
        )
        context = AppContext(config)

        # load_reports raises ReportLoadError when no JSON files are found
        with pytest.raises(ReportLoadError, match="No JSON files found"):
            load_and_group_reports(context)

    def test_load_and_group_reports_unknown_package_fallback(self, tmp_path, sample_grype_report):
        """Test loading reports with unknown package (no directory structure)."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        # Create report directly in reports dir (no subdirectory)
        report_file = reports_dir / "report.json"
        report_file.write_text(json.dumps(sample_grype_report))

        config = AggregatorConfig(
            input_dir=reports_dir,
            output_file=tmp_path / "output.json",
            download_remote_packages=True,
            packages=[PackageConfig(name="package1", version="1.0.0")],
        )
        context = AppContext(config)

        reports_by_package = load_and_group_reports(context)

        # Should fall back to "unknown" for files without directory structure
        assert "unknown" in reports_by_package
        assert len(reports_by_package["unknown"]) >= 1

    def test_load_and_group_reports_grype_only_mode(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test loading reports in grype-only mode."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        report_file = reports_dir / "test.json"
        report_file.write_text(json.dumps(sample_grype_report))

        config = AggregatorConfig(
            input_dir=reports_dir,
            output_file=tmp_path / "output.json",
            mode="grype-only",
        )
        context = AppContext(config)

        reports_by_package = load_and_group_reports(context)

        assert "unified" in reports_by_package

    def test_load_and_group_reports_trivy_only_mode(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test loading reports in trivy-only mode."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        report_file = reports_dir / "test.json"
        report_file.write_text(json.dumps(sample_grype_report))

        config = AggregatorConfig(
            input_dir=reports_dir,
            output_file=tmp_path / "output.json",
            mode="trivy-only",
            scanner="trivy",
        )
        context = AppContext(config)

        # Mock load_reports to return trivy reports
        with patch("cve_report_aggregator.core.orchestrator.load_reports") as mock_load:
            mock_load.return_value = [sample_grype_report]

            _reports_by_package = load_and_group_reports(context)

            mock_load.assert_called_once()
            # Verify scanner is set to trivy
            call_kwargs = mock_load.call_args[1]
            assert call_kwargs["scanner"] == "trivy"


class TestProcessPackageReports:
    """Tests for process_package_reports function."""

    def test_process_package_reports_basic(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test processing reports for a single package."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
        )
        context = AppContext(config)

        # Prepare report
        report = sample_grype_report.copy()
        report["_source_file"] = "test.json"
        reports = [report]

        json_path, csv_path, vuln_map = process_package_reports(
            package_name="test-package",
            package_reports=reports,
            context=context,
        )

        # Verify output files exist
        assert json_path.exists()
        assert csv_path is None or csv_path.exists()
        assert len(vuln_map) > 0

        # Verify JSON structure
        with open(json_path) as f:
            data = json.load(f)

        assert "metadata" in data
        assert "summary" in data
        assert "vulnerabilities" in data

    def test_process_package_reports_with_version(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test processing reports with package version."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            packages=[PackageConfig(name="test-package", version="1.0.0")],
        )
        context = AppContext(config)

        # Prepare report
        report = sample_grype_report.copy()
        report["_source_file"] = "test.json"
        reports = [report]

        json_path, csv_path, vuln_map = process_package_reports(
            package_name="test-package",
            package_reports=reports,
            context=context,
        )

        # Verify filename includes version
        assert "1.0.0" in json_path.name
        assert json_path.exists()

    def test_process_package_reports_csv_export_failure(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test CSV export failure handling."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
        )
        context = AppContext(config)

        report = sample_grype_report.copy()
        report["_source_file"] = "test.json"
        reports = [report]

        with patch("cve_report_aggregator.core.orchestrator.export_to_csv") as mock_csv:
            mock_csv.side_effect = Exception("CSV export failed")

            json_path, csv_path, vuln_map = process_package_reports(
                package_name="test-package",
                package_reports=reports,
                context=context,
            )

            # Should handle CSV failure gracefully
            assert json_path.exists()
            assert csv_path is None

    def test_process_package_reports_with_enrichment(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test processing reports with enrichment enabled."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
        )
        config.enrich.enabled = True
        config.enrich.api_key = "test-key"
        context = AppContext(config)

        report = sample_grype_report.copy()
        report["_source_file"] = "test.json"
        reports = [report]

        with patch("cve_report_aggregator.core.orchestrator.create_enricher") as mock_create_enricher:
            from cve_report_aggregator.enhance.models import SimpleCVEEnrichment

            mock_enricher = mock_create_enricher.return_value
            mock_enrichment = SimpleCVEEnrichment(
                cve_id="CVE-2024-12345",
                mitigation_summary="Test mitigation",
                impact_analysis="Test impact",
                analysis_model="gpt-4-turbo",
                analysis_timestamp="2024-01-01T00:00:00Z",
            )
            mock_enricher.enrich_report.return_value = {"CVE-2024-12345": mock_enrichment}

            json_path, csv_path, vuln_map = process_package_reports(
                package_name="test-package",
                package_reports=reports,
                context=context,
            )

            # Verify enrichment was called
            mock_enricher.enrich_report.assert_called_once()

            # Verify enrichments in output
            with open(json_path) as f:
                data = json.load(f)

            assert "enrichments" in data


class TestEnrichReport:
    """Tests for enrich_report function."""

    def test_enrich_report_no_api_key(self, tmp_path, sample_grype_report):
        """Test enrichment with no API key."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
        )
        config.enrich.enabled = True  # Enable enrichment but no API key
        context = AppContext(config)

        unified_report = {
            "metadata": {},
            "summary": {},
            "vulnerabilities": [
                {
                    "vulnerability_id": "CVE-2024-12345",
                    "vulnerability": {"severity": "Critical"},
                }
            ],
        }

        result = enrich_report(unified_report, "test-package", context)

        # Should return report unchanged
        assert result == unified_report
        assert "enrichments" not in result

    def test_enrich_report_success(self, tmp_path):
        """Test successful CVE enrichment."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
        )
        config.enrich.enabled = True
        config.enrich.api_key = "test-key"
        config.enrich.severities = ["Critical", "High"]
        context = AppContext(config)

        unified_report = {
            "metadata": {},
            "summary": {},
            "vulnerabilities": [
                {
                    "vulnerability_id": "CVE-2024-12345",
                    "vulnerability": {"severity": "Critical"},
                }
            ],
        }

        with patch("cve_report_aggregator.core.orchestrator.create_enricher") as mock_create_enricher:
            from cve_report_aggregator.enhance.models import SimpleCVEEnrichment

            mock_enricher = mock_create_enricher.return_value
            mock_enrichment = SimpleCVEEnrichment(
                cve_id="CVE-2024-12345",
                mitigation_summary="UDS helps mitigate this vulnerability",
                impact_analysis="Without UDS controls, this vulnerability could be exploited.",
                analysis_model="gpt-4-turbo",
                analysis_timestamp="2024-01-01T00:00:00Z",
            )
            mock_enricher.enrich_report.return_value = {"CVE-2024-12345": mock_enrichment}

            result = enrich_report(unified_report, "test-package", context)

        # Verify enrichments were added
        assert "enrichments" in result
        assert "CVE-2024-12345" in result["enrichments"]
        assert "summary" in result
        assert "enrichment" in result["summary"]
        assert result["summary"]["enrichment"]["enriched_cves"] == 1

    def test_enrich_report_error(self, tmp_path):
        """Test enrichment with error during processing."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
        )
        config.enrich.enabled = True
        config.enrich.api_key = "test-key"
        config.enrich.severities = ["Critical"]
        context = AppContext(config)

        unified_report = {
            "metadata": {},
            "summary": {},
            "vulnerabilities": [
                {
                    "vulnerability_id": "CVE-2024-12345",
                    "vulnerability": {"severity": "Critical"},
                }
            ],
        }

        with patch("cve_report_aggregator.core.orchestrator.create_enricher") as mock_create_enricher:
            mock_create_enricher.side_effect = Exception("OpenAI API error")

            result = enrich_report(unified_report, "test-package", context)

        # Should handle error gracefully
        assert "enrichments" in result
        assert result["enrichments"] == {}
        assert "summary" in result
        assert "enrichment" in result["summary"]
        assert result["summary"]["enrichment"]["enriched_cves"] == 0
        assert "error" in result["summary"]["enrichment"]

    def test_enrich_report_error_without_summary(self, tmp_path):
        """Test enrichment error handling when summary key does not exist."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
        )
        config.enrich.enabled = True
        config.enrich.api_key = "test-key"
        config.enrich.severities = ["Critical"]
        context = AppContext(config)

        unified_report = {
            "metadata": {},
            # No summary key
            "vulnerabilities": [
                {
                    "vulnerability_id": "CVE-2024-12345",
                    "vulnerability": {"severity": "Critical"},
                }
            ],
        }

        with patch("cve_report_aggregator.core.orchestrator.create_enricher") as mock_create_enricher:
            mock_enricher = mock_create_enricher.return_value
            mock_enricher.enrich_report.side_effect = Exception("OpenAI API error")

            result = enrich_report(unified_report, "test-package", context)

        # Should handle error gracefully and create summary with error info
        assert "enrichments" in result
        assert result["enrichments"] == {}
        # Summary is now created with enrichment error info even if it didn't exist
        assert "summary" in result
        assert "enrichment" in result["summary"]
        assert result["summary"]["enrichment"]["enriched_cves"] == 0
        assert "error" in result["summary"]["enrichment"]


class TestCreateExecutiveSummaryReport:
    """Tests for create_executive_summary_report function."""

    def test_create_executive_summary_report(self, tmp_path, vuln_map_sample, sample_grype_report):
        """Test creating executive summary report."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
        )
        context = AppContext(config)

        all_reports = [sample_grype_report]
        all_vuln_maps = vuln_map_sample

        summary_path = create_executive_summary_report(all_vuln_maps, all_reports, context)

        # Verify summary file exists
        assert summary_path.exists()
        assert summary_path.name.startswith("executive-summary")

        # Verify content
        with open(summary_path) as f:
            data = json.load(f)

        # Executive summary has different structure
        assert "report_metadata" in data
        assert "key_metrics" in data


class TestAggregateStatistics:
    """Tests for aggregate_statistics function."""

    def test_aggregate_statistics_single_report(self, tmp_path, sample_grype_report):
        """Test aggregating statistics from a single report."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
        )
        context = AppContext(config)

        # Create a sample unified report
        output_dir = Path.home() / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        unified_report_path = output_dir / "test-unified.json"

        unified_report = {
            "metadata": {},
            "summary": {
                "total_vulnerability_occurrences": 10,
                "unique_vulnerabilities": 5,
                "scanned_images": [{"image": "test:latest"}],
                "by_severity": {
                    "Critical": 2,
                    "High": 3,
                    "Medium": 0,
                    "Low": 0,
                    "Negligible": 0,
                    "Unknown": 0,
                },
            },
            "vulnerabilities": [],
        }

        with open(unified_report_path, "w") as f:
            json.dump(unified_report, f)

        result = aggregate_statistics([unified_report_path], context)

        assert result.total_occurrences == 10
        assert result.unique_vulnerabilities == 5
        assert len(result.unique_images) == 1
        assert result.severity_breakdown["Critical"] == 2
        assert result.severity_breakdown["High"] == 3
        assert result.packages_scanned == 1

    def test_aggregate_statistics_with_enrichment(self, tmp_path):
        """Test aggregating statistics with enrichment data."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
        )
        context = AppContext(config)

        output_dir = Path.home() / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        unified_report_path = output_dir / "test-enriched.json"

        unified_report = {
            "metadata": {},
            "summary": {
                "total_vulnerability_occurrences": 10,
                "unique_vulnerabilities": 5,
                "scanned_images": [{"image": "test:latest"}],
                "by_severity": {
                    "Critical": 2,
                    "High": 3,
                    "Medium": 0,
                    "Low": 0,
                    "Negligible": 0,
                    "Unknown": 0,
                },
                "enrichment": {
                    "enabled": True,
                    "model": "gpt-4-turbo",
                    "enriched_cves": 3,
                    "eligible_cves": 5,
                },
            },
            "vulnerabilities": [],
        }

        with open(unified_report_path, "w") as f:
            json.dump(unified_report, f)

        result = aggregate_statistics([unified_report_path], context)

        # Verify enrichment statistics
        assert result.enrichment_stats is not None
        assert result.enrichment_stats["enabled"] is True
        assert result.enrichment_stats["model"] == "gpt-4-turbo"
        assert result.enrichment_stats["total_enriched"] == 3
        assert result.enrichment_stats["total_eligible"] == 5
        assert result.enrichment_stats["percentage"] == 60.0

    def test_aggregate_statistics_skips_executive_summary(self, tmp_path):
        """Test that executive summary files are skipped."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
        )
        context = AppContext(config)

        output_dir = Path.home() / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create executive summary file
        exec_summary_path = output_dir / "executive-summary-12345.json"
        exec_summary = {"metadata": {}, "summary": {}}
        with open(exec_summary_path, "w") as f:
            json.dump(exec_summary, f)

        result = aggregate_statistics([exec_summary_path], context)

        # Should not count executive summary
        assert result.packages_scanned == 0
        assert result.total_occurrences == 0

    def test_aggregate_statistics_skips_csv_files(self, tmp_path):
        """Test that CSV files are skipped."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
        )
        context = AppContext(config)

        output_dir = Path.home() / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create CSV file
        csv_path = output_dir / "test-report.csv"
        csv_path.write_text("CVE-ID,Severity\n")

        result = aggregate_statistics([csv_path], context)

        # Should not process CSV files
        assert result.packages_scanned == 0

    def test_aggregate_statistics_handles_read_errors(self, tmp_path):
        """Test handling of file read errors."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
        )
        context = AppContext(config)

        output_dir = Path.home() / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create invalid JSON file
        invalid_path = output_dir / "invalid.json"
        invalid_path.write_text("not valid json")

        result = aggregate_statistics([invalid_path], context)

        # Should continue despite errors
        assert result.packages_scanned == 1  # Counts as a package even if read fails
        assert result.total_occurrences == 0  # But no data extracted


class TestRunAggregation:
    """Tests for run_aggregation function."""

    def test_run_aggregation_success(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test complete aggregation workflow."""
        # Create a sample report file
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        report_file = reports_dir / "test.json"
        report_file.write_text(json.dumps(sample_grype_report))

        config = AggregatorConfig(
            input_dir=reports_dir,
            output_file=tmp_path / "output.json",
        )
        context = AppContext(config)

        result = run_aggregation(context)

        # Verify result
        assert isinstance(result, AggregationResult)
        assert len(result.output_files) >= 1
        assert result.total_occurrences >= 0
        assert result.unique_vulnerabilities >= 0
        assert result.packages_scanned >= 1

    def test_run_aggregation_no_reports(self, tmp_path, mock_subprocess_success):
        """Test aggregation with no reports found."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        config = AggregatorConfig(
            input_dir=reports_dir,
            output_file=tmp_path / "output.json",
        )
        context = AppContext(config)

        # load_reports raises ReportLoadError when no JSON files are found
        with pytest.raises(ReportLoadError, match="No JSON files found"):
            run_aggregation(context)

    def test_run_aggregation_with_executive_summary(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test aggregation creates executive summary."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        # Create multiple package reports
        pkg1_dir = reports_dir / "package1"
        pkg1_dir.mkdir()
        (pkg1_dir / "report1.json").write_text(json.dumps(sample_grype_report))

        pkg2_dir = reports_dir / "package2"
        pkg2_dir.mkdir()
        (pkg2_dir / "report2.json").write_text(json.dumps(sample_grype_report))

        config = AggregatorConfig(
            input_dir=reports_dir,
            output_file=tmp_path / "output.json",
            download_remote_packages=True,
            registry="registry.example.com",  # Add required registry
            organization="test-org",  # Add required organization
            packages=[
                PackageConfig(name="package1", version="1.0.0"),
                PackageConfig(name="package2", version="2.0.0"),
            ],
        )
        context = AppContext(config)

        # Mock remote package downloading to avoid actual download
        with (
            patch("cve_report_aggregator.core.orchestrator.check_command_exists") as mock_check,
            patch("cve_report_aggregator.core.orchestrator.download_package_sboms") as mock_download,
        ):
            mock_check.return_value = False  # No zarf command
            mock_download.return_value = []  # No SBOMs downloaded

            result = run_aggregation(context)

        # Verify executive summary was created
        exec_summaries = [f for f in result.output_files if f.name.startswith("executive-summary")]
        assert len(exec_summaries) == 1

    def test_run_aggregation_merges_vulnerability_maps(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test that vulnerability maps are merged across packages."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        # Create reports with same CVE in different packages
        pkg1_dir = reports_dir / "package1"
        pkg1_dir.mkdir()
        (pkg1_dir / "report1.json").write_text(json.dumps(sample_grype_report))

        pkg2_dir = reports_dir / "package2"
        pkg2_dir.mkdir()
        (pkg2_dir / "report2.json").write_text(json.dumps(sample_grype_report))

        config = AggregatorConfig(
            input_dir=reports_dir,
            output_file=tmp_path / "output.json",
            download_remote_packages=True,
            registry="registry.example.com",  # Add required registry
            organization="test-org",  # Add required organization
            packages=[
                PackageConfig(name="package1", version="1.0.0"),
                PackageConfig(name="package2", version="2.0.0"),
            ],
        )
        context = AppContext(config)

        # Mock remote package downloading
        with (
            patch("cve_report_aggregator.core.orchestrator.check_command_exists") as mock_check,
            patch("cve_report_aggregator.core.orchestrator.download_package_sboms") as mock_download,
        ):
            mock_check.return_value = False
            mock_download.return_value = []

            result = run_aggregation(context)

        # Verify packages were processed
        assert result.packages_scanned == 2

    def test_run_aggregation_with_sboms(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test aggregation workflow with SBOM acquisition."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        report_file = reports_dir / "test.json"
        report_file.write_text(json.dumps(sample_grype_report))

        config = AggregatorConfig(
            input_dir=reports_dir,
            output_file=tmp_path / "output.json",
            download_remote_packages=True,
            registry="registry.example.com",
            organization="test-org",
            packages=[PackageConfig(name="test-package", version="1.0.0")],
        )
        context = AppContext(config)

        with (
            patch("cve_report_aggregator.core.orchestrator.check_command_exists") as mock_check,
            patch("cve_report_aggregator.core.orchestrator.download_package_sboms") as mock_download,
        ):
            mock_check.return_value = False
            mock_download.return_value = [reports_dir / "downloaded-sbom.json"]

            result = run_aggregation(context)

            # Verify SBOMs were acquired
            mock_download.assert_called_once()
            assert isinstance(result, AggregationResult)


class TestAcquireSBOMsConfiguredPackages:
    """Tests for acquire_sboms with configured packages (local and remote)."""

    def test_acquire_sboms_remote_only_in_auto_detect(self, tmp_path):
        """Test auto-detect mode falling back to remote downloads."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            download_remote_packages=True,
            registry="registry.example.com",
            organization="test-org",
            packages=[PackageConfig(name="test-pkg", version="1.0.0")],
        )
        context = AppContext(config)

        with (
            patch("cve_report_aggregator.core.orchestrator.check_command_exists") as mock_check,
            patch("cve_report_aggregator.core.orchestrator.download_package_sboms") as mock_download,
        ):
            mock_check.return_value = False  # No zarf
            mock_download.return_value = [tmp_path / "downloaded.json"]

            sboms, local_found = acquire_sboms(context)
            assert len(sboms) == 1
            assert local_found is False
            mock_download.assert_called_once()

    def test_acquire_sboms_no_packages_auto_detect_with_runtime_error(self, tmp_path):
        """Test auto-detect mode when scan_local_packages raises RuntimeError."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            download_remote_packages=False,
        )
        context = AppContext(config)

        with (
            patch("cve_report_aggregator.core.orchestrator.check_command_exists") as mock_check,
            patch("cve_report_aggregator.core.orchestrator.scan_local_packages") as mock_scan,
        ):
            mock_check.return_value = True
            mock_scan.side_effect = RuntimeError("Scan error")

            # Should handle error gracefully and return empty
            sboms, local_found = acquire_sboms(context)
            assert len(sboms) == 0
            assert local_found is False

    def test_acquire_sboms_configured_local_packages(self, tmp_path):
        """Test acquiring SBOMs from configured local packages."""
        packages_dir = Path.cwd() / "packages"
        packages_dir.mkdir(exist_ok=True)

        # Create a mock archive file
        archive_name = "zarf-package-test-pkg-amd64-1.0.0.tar.zst"
        archive_path = packages_dir / archive_name
        archive_path.write_bytes(b"mock archive")

        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            packages=[PackageConfig(name="test-pkg", version="1.0.0", source="local")],
        )
        context = AppContext(config)

        try:
            with (
                patch("cve_report_aggregator.core.orchestrator.check_command_exists") as mock_check,
                patch("cve_report_aggregator.core.orchestrator._extract_local_package_sboms") as mock_extract,
            ):
                mock_check.return_value = True  # Zarf available
                mock_extract.return_value = [tmp_path / "sbom1.json", tmp_path / "sbom2.json"]

                sboms, local_found = acquire_sboms(context)

                assert len(sboms) == 2
                assert local_found is True
                mock_extract.assert_called_once()
        finally:
            # Cleanup
            if archive_path.exists():
                archive_path.unlink()
            if packages_dir.exists() and not any(packages_dir.iterdir()):
                packages_dir.rmdir()

    def test_acquire_sboms_configured_remote_packages(self, tmp_path):
        """Test acquiring SBOMs from configured remote packages."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            registry="registry.example.com",
            organization="test-org",
            packages=[PackageConfig(name="remote-pkg", version="2.0.0", source="remote")],
        )
        context = AppContext(config)

        with patch("cve_report_aggregator.core.orchestrator.download_package_sboms") as mock_download:
            mock_download.return_value = [tmp_path / "remote-sbom.json"]

            sboms, local_found = acquire_sboms(context)

            assert len(sboms) == 1
            assert local_found is False
            mock_download.assert_called_once()

    def test_acquire_sboms_mixed_local_and_remote(self, tmp_path):
        """Test acquiring SBOMs from mixed local and remote packages."""
        packages_dir = Path.cwd() / "packages"
        packages_dir.mkdir(exist_ok=True)

        archive_name = "zarf-package-local-pkg-amd64-1.0.0.tar.zst"
        archive_path = packages_dir / archive_name
        archive_path.write_bytes(b"mock archive")

        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            registry="registry.example.com",
            organization="test-org",
            packages=[
                PackageConfig(name="local-pkg", version="1.0.0", source="local"),
                PackageConfig(name="remote-pkg", version="2.0.0", source="remote"),
            ],
        )
        context = AppContext(config)

        try:
            with (
                patch("cve_report_aggregator.core.orchestrator.check_command_exists") as mock_check,
                patch("cve_report_aggregator.core.orchestrator._extract_local_package_sboms") as mock_extract,
                patch("cve_report_aggregator.core.orchestrator.download_package_sboms") as mock_download,
            ):
                mock_check.return_value = True
                mock_extract.return_value = [tmp_path / "local-sbom.json"]
                mock_download.return_value = [tmp_path / "remote-sbom.json"]

                sboms, local_found = acquire_sboms(context)

                assert len(sboms) == 2
                assert local_found is True
                mock_extract.assert_called_once()
                mock_download.assert_called_once()
        finally:
            if archive_path.exists():
                archive_path.unlink()
            if packages_dir.exists() and not any(packages_dir.iterdir()):
                packages_dir.rmdir()

    def test_acquire_sboms_local_only_skips_remote_packages(self, tmp_path):
        """Test local_only mode skips configured remote packages."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            local_only=True,
            registry="registry.example.com",
            organization="test-org",
            packages=[PackageConfig(name="remote-pkg", version="1.0.0", source="remote")],
        )
        context = AppContext(config)

        with patch("cve_report_aggregator.core.orchestrator.download_package_sboms") as mock_download:
            sboms, local_found = acquire_sboms(context)

            # Should skip remote downloads
            assert len(sboms) == 0
            assert local_found is False
            mock_download.assert_not_called()

    def test_acquire_sboms_no_zarf_skips_local(self, tmp_path):
        """Test that local packages are skipped when zarf is not available."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            packages=[PackageConfig(name="local-pkg", version="1.0.0", source="local")],
        )
        context = AppContext(config)

        with patch("cve_report_aggregator.core.orchestrator.check_command_exists") as mock_check:
            mock_check.return_value = False  # No zarf

            sboms, local_found = acquire_sboms(context)

            assert len(sboms) == 0
            assert local_found is False

    def test_acquire_sboms_missing_packages_dir(self, tmp_path):
        """Test error when packages directory doesn't exist."""
        # Ensure packages dir doesn't exist
        packages_dir = Path.cwd() / "packages"
        if packages_dir.exists():
            import shutil

            shutil.rmtree(packages_dir)

        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            packages=[PackageConfig(name="local-pkg", version="1.0.0", source="local")],
        )
        context = AppContext(config)

        with patch("cve_report_aggregator.core.orchestrator.check_command_exists") as mock_check:
            mock_check.return_value = True  # Zarf available

            with pytest.raises(ValueError, match="Local packages configured but directory not found"):
                acquire_sboms(context)


class TestLoadAndGroupReportsEdgeCases:
    """Additional tests for load_and_group_reports edge cases."""

    def test_load_and_group_reports_trivy_pipeline_warning(self, tmp_path, sample_grype_report):
        """Test warning when using trivy scanner without highest-score mode."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        report_file = reports_dir / "test.json"
        report_file.write_text(json.dumps(sample_grype_report))

        config = AggregatorConfig(
            input_dir=reports_dir,
            output_file=tmp_path / "output.json",
            scanner="trivy",
            mode="first-occurrence",  # Not highest-score
        )
        context = AppContext(config)

        with patch("cve_report_aggregator.core.orchestrator.load_reports") as mock_load:
            mock_load.return_value = [sample_grype_report]

            # Should log a warning about mode mismatch
            _reports = load_and_group_reports(context)

            # Verify it still works
            assert mock_load.called


class TestRunAggregationWithArchive:
    """Tests for run_aggregation with archive_dir (tarball creation)."""

    def test_run_aggregation_creates_tarball(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test that tarball is created when archive_dir is configured."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()

        # Create a report file
        report_file = reports_dir / "test.json"
        report_file.write_text(json.dumps(sample_grype_report))

        config = AggregatorConfig(
            input_dir=reports_dir,
            output_file=tmp_path / "output.json",
            archive_dir=archive_dir,
        )
        context = AppContext(config)

        with patch("cve_report_aggregator.core.orchestrator.check_command_exists") as mock_check:
            mock_check.return_value = False

            result = run_aggregation(context)

        # Verify tarball was created
        assert result.tarball_path is not None
        assert result.tarball_path.exists()
        assert result.tarball_path.name == "artifacts.tar.gz"

    def test_run_aggregation_tarball_failure_continues(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test that aggregation continues even if tarball creation fails."""
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()

        report_file = reports_dir / "test.json"
        report_file.write_text(json.dumps(sample_grype_report))

        config = AggregatorConfig(
            input_dir=reports_dir,
            output_file=tmp_path / "output.json",
            archive_dir=archive_dir,
        )
        context = AppContext(config)

        with (
            patch("cve_report_aggregator.core.orchestrator.check_command_exists") as mock_check,
            patch("cve_report_aggregator.io.archive.create_tarball") as mock_tarball,
        ):
            mock_check.return_value = False
            mock_tarball.side_effect = Exception("Tarball creation failed")

            # Should not raise, but continue without tarball
            result = run_aggregation(context)

        # Aggregation should still succeed
        assert result is not None
        assert result.tarball_path is None


class TestEnrichReportEdgeCases:
    """Additional tests for enrich_report edge cases."""

    def test_enrich_report_creates_summary_on_success(self, tmp_path):
        """Test that enrichment creates summary section."""
        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
        )
        config.enrich.enabled = True
        config.enrich.api_key = "test-key"
        context = AppContext(config)

        unified_report = {
            "metadata": {},
            # No summary initially
            "vulnerabilities": [
                {
                    "vulnerability_id": "CVE-2024-1",
                    "vulnerability": {"severity": "Critical"},
                }
            ],
        }

        with patch("cve_report_aggregator.core.orchestrator.create_enricher") as mock_create_enricher:
            from cve_report_aggregator.enhance.models import SimpleCVEEnrichment

            mock_enricher = mock_create_enricher.return_value
            mock_enrichment = SimpleCVEEnrichment(
                cve_id="CVE-2024-1",
                mitigation_summary="Test",
                impact_analysis="Test",
                analysis_model="gpt-4",
                analysis_timestamp="2024-01-01T00:00:00Z",
            )
            mock_enricher.enrich_report.return_value = {"CVE-2024-1": mock_enrichment}

            result = enrich_report(unified_report, "test-pkg", context)

            # Verify summary was created
            assert "summary" in result
            assert "enrichment" in result["summary"]
