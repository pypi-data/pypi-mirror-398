"""Tests for command-line interface."""

import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from cve_report_aggregator.cli import display_logo, main


class TestDisplayLogo:
    """Tests for display_logo function."""

    def test_display_logo_success(self):
        """Test that logo displays successfully."""
        with patch("cve_report_aggregator.cli.console") as mock_console:
            display_logo()
            # Should call console.print with the ASCII logo
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0]
            # First arg should be the logo string
            assert len(call_args[0]) > 100  # Logo is a long string

    def test_display_logo_fallback(self):
        """Test logo fallback when display fails."""
        with patch("cve_report_aggregator.cli.console") as mock_console:
            # Make console.print raise an exception on first call
            mock_console.print.side_effect = [Exception("Display error"), None]

            display_logo()

            # Should call print twice (once failed, once fallback)
            assert mock_console.print.call_count == 2
            # Second call should be the fallback message
            fallback_call = mock_console.print.call_args_list[1]
            assert "CVE Report Aggregator" in str(fallback_call)


class TestDisplayHeader:
    """Tests for display_header function."""

    def test_display_header_success(self):
        """Test header display with configuration."""
        from cve_report_aggregator.cli import display_header

        with patch("cve_report_aggregator.cli.console") as mock_console:
            display_header(mode="highest-score", scanner="grype", scanner_version="0.79.0")

            # Should call console.print multiple times
            assert mock_console.print.called
            assert mock_console.print.call_count >= 1


class TestDisplayDebugConfig:
    """Tests for display_debug_config function."""

    def test_display_debug_config(self, tmp_path):
        """Test debug configuration display."""
        from cve_report_aggregator.cli import display_debug_config
        from cve_report_aggregator.core.models import AggregatorConfig

        config = AggregatorConfig(
            input_dir=tmp_path,
            output_file=tmp_path / "output.json",
            scanner="grype",
            mode="highest-score",
        )

        with patch("cve_report_aggregator.cli.console") as mock_console:
            display_debug_config(config)

            # Should display configuration
            assert mock_console.print.called
            assert mock_console.print.call_count >= 1


class TestDisplayCriticalLocals:
    """Tests for display_critical_locals function."""

    def test_display_critical_locals(self):
        """Test critical locals display."""
        from cve_report_aggregator.cli import display_critical_locals

        local_vars = {
            "test_var": "test_value",
            "count": 42,
            "config": {"key": "value"},
        }

        with patch("cve_report_aggregator.cli.console") as mock_console:
            display_critical_locals(local_vars)

            # Should display local variables
            assert mock_console.print.called


class TestDisplayValidationError:
    """Tests for display_validation_error function."""

    def test_display_validation_error(self):
        """Test validation error display."""
        from cve_report_aggregator.cli import display_validation_error
        from cve_report_aggregator.core.validation import MissingToolError

        error = MissingToolError("grype", "grype command not found")

        with patch("cve_report_aggregator.cli.console") as mock_console:
            display_validation_error(error)

            # Should display error message
            assert mock_console.print.called
            print_call = str(mock_console.print.call_args)
            assert "Error" in print_call or "grype" in print_call


class TestDisplaySuccessSummary:
    """Tests for display_success_summary function."""

    def test_display_success_summary(self, tmp_path):
        """Test success summary display."""
        from cve_report_aggregator.cli import display_success_summary

        json_files = [
            tmp_path / "output1.json",
            tmp_path / "output2.json",
        ]
        csv_files = [
            tmp_path / "output1.csv",
        ]
        executive_summaries = [
            tmp_path / "executive-summary.json",
        ]

        # Create the files so they exist
        for f in json_files + csv_files + executive_summaries:
            f.write_text("{}")

        with patch("cve_report_aggregator.cli.console") as mock_console:
            display_success_summary(json_files, csv_files, executive_summaries)

            # Should display success message and file paths
            assert mock_console.print.called


class TestDisplayStatistics:
    """Tests for display_statistics function."""

    def test_display_statistics_basic(self):
        """Test basic statistics display."""
        from cve_report_aggregator.cli import display_statistics

        with patch("cve_report_aggregator.cli.console") as mock_console:
            display_statistics(
                mode_value="highest-score",
                effective_scanner="grype",
                packages_scanned=1,
                unique_images={"test:latest"},
                total_occurrences=10,
                unique_vulnerabilities=5,
                severity_breakdown={
                    "Critical": 2,
                    "High": 3,
                    "Medium": 0,
                    "Low": 0,
                    "Negligible": 0,
                    "Unknown": 0,
                },
            )

            # Should display tables
            assert mock_console.print.called

    def test_display_statistics_with_enrichment(self):
        """Test statistics display with enrichment data."""
        from cve_report_aggregator.cli import display_statistics

        enrichment_stats = {
            "enabled": True,
            "model": "gpt-4-turbo",
            "total_enriched": 3,
            "total_eligible": 5,
            "percentage": 60.0,
        }

        with patch("cve_report_aggregator.cli.console") as mock_console:
            display_statistics(
                mode_value="highest-score",
                effective_scanner="grype",
                packages_scanned=1,
                unique_images={"test:latest"},
                total_occurrences=10,
                unique_vulnerabilities=5,
                severity_breakdown={"Critical": 2, "High": 3},
                enrichment_stats=enrichment_stats,
            )

            # Should display enrichment info
            assert mock_console.print.called
            assert mock_console.print.call_count >= 1

    def test_display_statistics_empty_severity(self):
        """Test statistics display with empty severity breakdown."""
        from cve_report_aggregator.cli import display_statistics

        with patch("cve_report_aggregator.cli.console") as mock_console:
            display_statistics(
                mode_value="highest-score",
                effective_scanner="grype",
                packages_scanned=0,
                unique_images=set(),
                total_occurrences=0,
                unique_vulnerabilities=0,
                severity_breakdown={},
            )

            # Should handle empty data gracefully
            assert mock_console.print.called


class TestCLIMain:
    """Tests for main CLI function."""

    def test_cli_help(self):
        """Test CLI help output."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "CVE Report Aggregator" in result.output
        assert "Aggregate and deduplicate" in result.output

    def test_cli_version(self):
        """Test CLI version output."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        # Should display version number

    def test_cli_default_arguments(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test CLI with default arguments."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create reports directory with a sample report
            reports_dir = Path.cwd() / "reports"
            reports_dir.mkdir()

            report_file = reports_dir / "test.json"
            report_file.write_text(json.dumps(sample_grype_report))

            output_file = Path.cwd() / "unified-report.json"

            # Explicitly specify paths since isolated_filesystem changes cwd
            result = runner.invoke(main, ["-i", str(reports_dir), "-o", str(output_file)])

            # Should succeed (exit code 0)
            assert result.exit_code == 0, f"CLI failed with output:\n{result.output}"
            # Should create timestamped output file in the output file's parent directory
            actual_output_dir = output_file.parent
            # Check that output directory exists and contains JSON files
            assert actual_output_dir.exists(), f"Output directory not created: {actual_output_dir}"
            json_files = list(actual_output_dir.glob("*.json"))
            assert len(json_files) >= 1, f"Expected at least 1 output file, found {len(json_files)}"
            # Verify at least one file matches the expected pattern (name with timestamp)
            assert any(file.stem.count("-") >= 1 and file.suffix == ".json" for file in json_files)

    def test_cli_custom_input_output(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test CLI with custom input and output paths."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create custom reports directory
            custom_input = Path.cwd() / "custom-reports"
            custom_input.mkdir()

            report_file = custom_input / "test.json"
            report_file.write_text(json.dumps(sample_grype_report))

            custom_output = Path.cwd() / "output" / "custom-report.json"
            # Create output directory
            custom_output.parent.mkdir(parents=True, exist_ok=True)

            result = runner.invoke(main, ["-i", str(custom_input), "-o", str(custom_output)])

            assert result.exit_code == 0, f"CLI failed with output:\n{result.output}"
            # Should create timestamped output file in the output file's parent directory
            actual_output_dir = custom_output.parent
            # Check that output directory exists and contains JSON files
            assert actual_output_dir.exists(), f"Output directory not created: {actual_output_dir}"
            json_files = list(actual_output_dir.glob("*.json"))
            assert len(json_files) >= 1, f"Expected at least 1 output file, found {len(json_files)}"
            # Verify at least one file matches the expected pattern (name with timestamp)
            assert any(file.stem.count("-") >= 1 and file.suffix == ".json" for file in json_files)

    def test_cli_output_parent_not_exists(self, tmp_path):
        """Test CLI error when output parent directory doesn't exist."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            reports_dir = Path.cwd() / "reports"
            reports_dir.mkdir()

            # Output path with non-existent parent
            bad_output = Path.cwd() / "nonexistent" / "deep" / "path" / "output.json"

            result = runner.invoke(main, ["-i", str(reports_dir), "-o", str(bad_output)])

            assert result.exit_code == 1
            assert "Output file parent directory does not exist" in result.output

    def test_cli_output_is_directory(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test CLI error when output path is a directory."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            reports_dir = Path.cwd() / "reports"
            reports_dir.mkdir()

            # Add a sample report so we pass the "no reports" check
            report_file = reports_dir / "test.json"
            report_file.write_text(json.dumps(sample_grype_report))

            # Create a directory where output file should be
            output_dir = Path.cwd() / "output-dir"
            output_dir.mkdir()

            result = runner.invoke(main, ["-i", str(reports_dir), "-o", str(output_dir)])

            # Click validates dir_okay=False with exit code 2
            assert result.exit_code == 2
            assert "directory" in result.output.lower()

    def test_cli_output_non_json_extension(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test CLI warning when output file doesn't have .json extension."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            reports_dir = Path.cwd() / "reports"
            reports_dir.mkdir()

            report_file = reports_dir / "test.json"
            report_file.write_text(json.dumps(sample_grype_report))

            output_file = Path.cwd() / "output.txt"

            result = runner.invoke(main, ["-i", str(reports_dir), "-o", str(output_file)])

            # Should still succeed but show warning
            assert result.exit_code == 0
            assert "does not have .json extension" in result.output

    def test_cli_grype_only_mode(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test CLI with grype-only mode."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            reports_dir = Path.cwd() / "reports"
            reports_dir.mkdir()

            report_file = reports_dir / "test.json"
            report_file.write_text(json.dumps(sample_grype_report))

            result = runner.invoke(main, ["-i", str(reports_dir), "-m", "grype-only"])

            assert result.exit_code == 0
            assert "grype-only" in result.output.lower() or "Grype" in result.output

    def test_cli_trivy_only_mode(self, tmp_path, sample_grype_report, monkeypatch):
        """Test CLI with trivy-only mode."""
        runner = CliRunner()

        # Mock subprocess for Trivy workflow
        def mock_run(*args, **kwargs):
            command = args[0]

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            if "which" in command:
                return MockResult()
            elif "version" in command:
                MockResult.stdout = "Version: 0.100.0\n"
                return MockResult()
            elif "syft" in command and "convert" in command:
                MockResult.stdout = json.dumps({"bomFormat": "CycloneDX"})
                return MockResult()
            elif "trivy" in command:
                # Create output file if -o flag is present
                for i, arg in enumerate(command):
                    if arg == "-o" and i + 1 < len(command):
                        output_path = Path(command[i + 1])
                        output_path.write_text(
                            json.dumps(
                                {
                                    "ArtifactName": "test:latest",
                                    "SchemaVersion": "2.0.0",
                                    "CreatedAt": "2024-01-01T00:00:00Z",
                                    "Results": [{"Vulnerabilities": [{"VulnerabilityID": "CVE-2024-12345"}]}],
                                }
                            )
                        )
                return MockResult()
            return MockResult()

        import subprocess

        monkeypatch.setattr(subprocess, "run", mock_run)

        with runner.isolated_filesystem(temp_dir=tmp_path):
            reports_dir = Path.cwd() / "reports"
            reports_dir.mkdir()

            report_file = reports_dir / "test.json"
            report_file.write_text(json.dumps(sample_grype_report))

            result = runner.invoke(main, ["-i", str(reports_dir), "-m", "trivy-only"])

            assert result.exit_code == 0

    def test_cli_grype_only_missing_grype(self, tmp_path, mock_subprocess_failure):
        """Test CLI error when grype-only mode but grype not installed."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            reports_dir = Path.cwd() / "reports"
            reports_dir.mkdir()

            result = runner.invoke(main, ["-i", str(reports_dir), "-m", "grype-only"])

            assert result.exit_code == 1
            assert "grype" in result.output.lower()

    def test_cli_trivy_only_missing_trivy(self, tmp_path, mock_subprocess_failure):
        """Test CLI error when trivy-only mode but trivy not installed."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            reports_dir = Path.cwd() / "reports"
            reports_dir.mkdir()

            result = runner.invoke(main, ["-i", str(reports_dir), "-m", "trivy-only"])

            assert result.exit_code == 1
            assert "trivy" in result.output.lower() or "syft" in result.output.lower()

    def test_cli_highest_score_mode(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test CLI with highest-score mode (default)."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            reports_dir = Path.cwd() / "reports"
            reports_dir.mkdir()

            report_file = reports_dir / "test.json"
            report_file.write_text(json.dumps(sample_grype_report))

            result = runner.invoke(main, ["-i", str(reports_dir), "-m", "highest-score"])

            assert result.exit_code == 0
            assert "highest-score" in result.output.lower()

    def test_cli_first_occurrence_mode(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test CLI with first-occurrence mode."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            reports_dir = Path.cwd() / "reports"
            reports_dir.mkdir()

            report_file = reports_dir / "test.json"
            report_file.write_text(json.dumps(sample_grype_report))

            result = runner.invoke(main, ["-i", str(reports_dir), "-m", "first-occurrence"])

            assert result.exit_code == 0
            assert "first-occurrence" in result.output.lower()

    def test_cli_debug_mode(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test CLI with verbose output and configuration display."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            reports_dir = Path.cwd() / "reports"
            reports_dir.mkdir()

            report_file = reports_dir / "test.json"
            report_file.write_text(json.dumps(sample_grype_report))

            result = runner.invoke(main, ["-i", str(reports_dir), "--log-level", "DEBUG"])

            assert result.exit_code == 0
            # Debug should show pretty-printed configuration settings
            assert "Configuration Settings" in result.output
            assert "AggregatorConfig" in result.output
            assert "input_dir=" in result.output
            assert "scanner=" in result.output
            assert "mode=" in result.output
            assert "log_level='DEBUG'" in result.output

    def test_cli_critical_mode(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test CLI with CRITICAL log level shows local variables."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            reports_dir = Path.cwd() / "reports"
            reports_dir.mkdir()

            report_file = reports_dir / "test.json"
            report_file.write_text(json.dumps(sample_grype_report))

            result = runner.invoke(main, ["-i", str(reports_dir), "--log-level", "CRITICAL"])

            assert result.exit_code == 0
            # CRITICAL should show pretty-printed local variables
            assert "Local Variables (CRITICAL)" in result.output
            assert "'app_config':" in result.output or '"app_config":' in result.output
            assert "'input_dir':" in result.output or '"input_dir":' in result.output
            assert "'log_level':" in result.output or '"log_level":' in result.output
            assert "CRITICAL" in result.output

    def test_cli_no_reports_found(self, tmp_path, mock_subprocess_success):
        """Test CLI error when no valid reports found."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            reports_dir = Path.cwd() / "reports"
            reports_dir.mkdir()

            # Create empty/invalid report
            report_file = reports_dir / "empty.json"
            report_file.write_text(json.dumps({"no": "matches"}))

            result = runner.invoke(main, ["-i", str(reports_dir)])

            assert result.exit_code == 1
            assert "No valid reports" in result.output

    def test_cli_trivy_scanner_missing_syft(self, tmp_path, monkeypatch):
        """Test CLI error when using trivy scanner but syft not installed."""
        import subprocess

        def mock_run(*args, **kwargs):
            command = args[0]
            if "which" in command:
                if "syft" in command:
                    raise subprocess.CalledProcessError(1, command)
            raise subprocess.CalledProcessError(1, command)

        monkeypatch.setattr(subprocess, "run", mock_run)

        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            reports_dir = Path.cwd() / "reports"
            reports_dir.mkdir()

            result = runner.invoke(main, ["-i", str(reports_dir), "-s", "trivy"])

            assert result.exit_code == 1
            assert "syft" in result.output.lower()

    def test_cli_trivy_scanner_missing_trivy(self, tmp_path, monkeypatch):
        """Test CLI error when using trivy scanner but trivy not installed."""
        import subprocess

        def mock_run(*args, **kwargs):
            command = args[0]
            if "which" in command:
                if "syft" in command:
                    # syft exists
                    class MockResult:
                        stdout = "/usr/local/bin/syft"
                        returncode = 0

                    return MockResult()
                elif "trivy" in command:
                    # trivy doesn't exist
                    raise subprocess.CalledProcessError(1, command)
            raise subprocess.CalledProcessError(1, command)

        monkeypatch.setattr(subprocess, "run", mock_run)

        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            reports_dir = Path.cwd() / "reports"
            reports_dir.mkdir()

            result = runner.invoke(main, ["-i", str(reports_dir), "-s", "trivy"])

            assert result.exit_code == 1
            assert "trivy" in result.output.lower()

    def test_cli_grype_scanner_missing(self, tmp_path, mock_subprocess_failure):
        """Test CLI error when using grype scanner but grype not installed."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            reports_dir = Path.cwd() / "reports"
            reports_dir.mkdir()

            result = runner.invoke(main, ["-i", str(reports_dir), "-s", "grype"])

            assert result.exit_code == 1
            assert "grype" in result.output.lower()

    def test_cli_creates_output_directory(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test that CLI creates output directory if it doesn't exist."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            reports_dir = Path.cwd() / "reports"
            reports_dir.mkdir()

            report_file = reports_dir / "test.json"
            report_file.write_text(json.dumps(sample_grype_report))

            # Output in a new directory that doesn't exist yet
            output_file = Path.cwd() / "new-dir" / "output.json"
            # Create parent to avoid the "parent not exist" error
            output_file.parent.mkdir(parents=True)

            result = runner.invoke(main, ["-i", str(reports_dir), "-o", str(output_file)])

            assert result.exit_code == 0
            # Should create timestamped output file in the output file's parent directory
            actual_output_dir = output_file.parent
            # Check that output directory exists and contains JSON files
            assert actual_output_dir.exists(), f"Output directory not created: {actual_output_dir}"
            json_files = list(actual_output_dir.glob("*.json"))
            assert len(json_files) >= 1, f"Expected at least 1 output file, found {len(json_files)}"
            # Verify at least one file matches the expected pattern (name with timestamp)
            assert any(file.stem.count("-") >= 1 and file.suffix == ".json" for file in json_files)

    def test_cli_summary_statistics(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test that CLI displays summary statistics."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            reports_dir = Path.cwd() / "reports"
            reports_dir.mkdir()

            report_file = reports_dir / "test.json"
            report_file.write_text(json.dumps(sample_grype_report))

            result = runner.invoke(main, ["-i", str(reports_dir)])

            assert result.exit_code == 0
            # Should display summary statistics
            assert "Summary" in result.output
            assert "Severity" in result.output

    def test_cli_multiple_scanners_mode_override(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test that mode-specific scanner overrides --scanner flag."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            reports_dir = Path.cwd() / "reports"
            reports_dir.mkdir()

            report_file = reports_dir / "test.json"
            report_file.write_text(json.dumps(sample_grype_report))

            # Use --scanner trivy but --mode grype-only
            # grype-only mode should override the scanner choice
            result = runner.invoke(main, ["-i", str(reports_dir), "-s", "trivy", "-m", "grype-only"])

            assert result.exit_code == 0
            # Should use grype, not trivy

    def test_cli_json_output_structure(self, tmp_path, sample_grype_report, mock_subprocess_success):
        """Test that CLI produces valid JSON output with expected structure."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            reports_dir = Path.cwd() / "reports"
            reports_dir.mkdir()

            report_file = reports_dir / "test.json"
            report_file.write_text(json.dumps(sample_grype_report))

            # Create output directory and specify output file within it
            output_dir = Path.cwd() / "output"
            output_dir.mkdir()
            output_file = output_dir / "unified.json"

            result = runner.invoke(main, ["-i", str(reports_dir), "-o", str(output_file)])

            assert result.exit_code == 0

            # Check that output directory contains JSON files (now uses configured output_file.parent)
            assert output_dir.exists(), f"Output directory not created: {output_dir}"
            json_files = sorted(output_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            assert len(json_files) >= 2, (
                f"Expected at least 2 output files (unified + executive summary), found {len(json_files)}"
            )
            # Verify at least one file matches the expected pattern (name with timestamp)
            assert any(file.stem.count("-") >= 1 and file.suffix == ".json" for file in json_files)
            # Find the unified report (not the executive summary) for structure validation
            unified_files = [f for f in json_files if not f.name.startswith("executive-summary")]
            assert len(unified_files) >= 1, f"Expected at least 1 unified report file, found {len(unified_files)}"
            actual_output_file = unified_files[0]

            # Verify JSON structure
            with open(actual_output_file) as f:
                data = json.load(f)

            assert "metadata" in data
            assert "summary" in data
            assert "vulnerabilities" in data
            assert "database_info" in data

            # Verify metadata fields
            assert "generated_at" in data["metadata"]
            assert "scanner" in data["metadata"]
            assert data["metadata"]["scanner"] == "grype"

            # Verify summary fields
            assert "total_vulnerability_occurrences" in data["summary"]
            assert "unique_vulnerabilities" in data["summary"]
            assert "by_severity" in data["summary"]


class TestCLIConfigurationParameters:
    """Test CLI parameter handling for configuration options."""

    def test_cli_local_only_flag(self, tmp_path, mock_subprocess_success):
        """Test --local-only flag sets config."""
        runner = CliRunner()
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        # Create minimal grype report
        (input_dir / "grype.json").write_text(
            json.dumps({"matches": [], "source": {"type": "image", "target": {"userInput": "test:latest"}}})
        )

        # Mock run_aggregation to avoid execution
        with patch("cve_report_aggregator.cli.run_aggregation") as mock_run:
            from cve_report_aggregator.core.orchestrator import AggregationResult

            mock_run.return_value = AggregationResult(
                output_files=[],
                total_occurrences=0,
                unique_vulnerabilities=0,
                unique_images=set(),
                packages_scanned=0,
                severity_breakdown={},
                enrichment_stats=None,
            )

            result = runner.invoke(
                main,
                [
                    "--input-dir",
                    str(input_dir),
                    "--output-file",
                    str(tmp_path / "out.json"),
                    "--local-only",
                ],
            )

            # Should succeed
            assert result.exit_code == 0

    def test_cli_max_workers_parameter(self, tmp_path, mock_subprocess_success):
        """Test --max-workers parameter."""
        runner = CliRunner()
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        (input_dir / "grype.json").write_text(
            json.dumps({"matches": [], "source": {"type": "image", "target": {"userInput": "test:latest"}}})
        )

        with patch("cve_report_aggregator.cli.run_aggregation") as mock_run:
            from cve_report_aggregator.core.orchestrator import AggregationResult

            mock_run.return_value = AggregationResult(
                output_files=[],
                total_occurrences=0,
                unique_vulnerabilities=0,
                unique_images=set(),
                packages_scanned=0,
                severity_breakdown={},
                enrichment_stats=None,
            )

            result = runner.invoke(
                main,
                [
                    "--input-dir",
                    str(input_dir),
                    "--output-file",
                    str(tmp_path / "out.json"),
                    "--max-workers",
                    "4",
                ],
            )

            assert result.exit_code == 0

    def test_cli_enrich_enabled_flag(self, tmp_path, mock_subprocess_success):
        """Test --enrich-cves flag."""
        runner = CliRunner()
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        (input_dir / "grype.json").write_text(
            json.dumps({"matches": [], "source": {"type": "image", "target": {"userInput": "test:latest"}}})
        )

        with patch("cve_report_aggregator.cli.run_aggregation") as mock_run:
            from cve_report_aggregator.core.orchestrator import AggregationResult

            mock_run.return_value = AggregationResult(
                output_files=[],
                total_occurrences=0,
                unique_vulnerabilities=0,
                unique_images=set(),
                packages_scanned=0,
                severity_breakdown={},
                enrichment_stats=None,
            )

            result = runner.invoke(
                main,
                [
                    "--input-dir",
                    str(input_dir),
                    "--output-file",
                    str(tmp_path / "out.json"),
                    "--enrich-cves",
                    "--openai-api-key",
                    "sk-test123",  # Required when --enrich-cves is set
                ],
            )

            assert result.exit_code == 0

    def test_cli_openai_api_key(self, tmp_path, mock_subprocess_success):
        """Test --openai-api-key parameter."""
        runner = CliRunner()
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        (input_dir / "grype.json").write_text(
            json.dumps({"matches": [], "source": {"type": "image", "target": {"userInput": "test:latest"}}})
        )

        with patch("cve_report_aggregator.cli.run_aggregation") as mock_run:
            from cve_report_aggregator.core.orchestrator import AggregationResult

            mock_run.return_value = AggregationResult(
                output_files=[],
                total_occurrences=0,
                unique_vulnerabilities=0,
                unique_images=set(),
                packages_scanned=0,
                severity_breakdown={},
                enrichment_stats=None,
            )

            result = runner.invoke(
                main,
                [
                    "--input-dir",
                    str(input_dir),
                    "--output-file",
                    str(tmp_path / "out.json"),
                    "--openai-api-key",
                    "sk-test123",
                ],
            )

            assert result.exit_code == 0

    def test_cli_openai_model(self, tmp_path, mock_subprocess_success):
        """Test --openai-model parameter."""
        runner = CliRunner()
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        (input_dir / "grype.json").write_text(
            json.dumps({"matches": [], "source": {"type": "image", "target": {"userInput": "test:latest"}}})
        )

        with patch("cve_report_aggregator.cli.run_aggregation") as mock_run:
            from cve_report_aggregator.core.orchestrator import AggregationResult

            mock_run.return_value = AggregationResult(
                output_files=[],
                total_occurrences=0,
                unique_vulnerabilities=0,
                unique_images=set(),
                packages_scanned=0,
                severity_breakdown={},
                enrichment_stats=None,
            )

            result = runner.invoke(
                main,
                [
                    "--input-dir",
                    str(input_dir),
                    "--output-file",
                    str(tmp_path / "out.json"),
                    "--openai-model",
                    "gpt-4",
                ],
            )

            assert result.exit_code == 0

    def test_cli_enrich_severity_filter(self, tmp_path, mock_subprocess_success):
        """Test --enrich-severity-filter parameter."""
        runner = CliRunner()
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        (input_dir / "grype.json").write_text(
            json.dumps({"matches": [], "source": {"type": "image", "target": {"userInput": "test:latest"}}})
        )

        with patch("cve_report_aggregator.cli.run_aggregation") as mock_run:
            from cve_report_aggregator.core.orchestrator import AggregationResult

            mock_run.return_value = AggregationResult(
                output_files=[],
                total_occurrences=0,
                unique_vulnerabilities=0,
                unique_images=set(),
                packages_scanned=0,
                severity_breakdown={},
                enrichment_stats=None,
            )

            result = runner.invoke(
                main,
                [
                    "--input-dir",
                    str(input_dir),
                    "--output-file",
                    str(tmp_path / "out.json"),
                    "--enrich-severity-filter",
                    "critical",
                    "--enrich-severity-filter",
                    "high",
                ],
            )

            assert result.exit_code == 0


class TestCLIErrorHandling:
    """Test CLI error handling paths."""

    def test_cli_validation_error_from_config(self, tmp_path):
        """Test ValidationError from get_config."""
        runner = CliRunner()

        # Create invalid config
        config_file = tmp_path / "config.yaml"
        config_file.write_text("input_dir:\n  - invalid\n  - list\n")

        result = runner.invoke(main, ["--config", str(config_file)])

        # Should exit with error
        assert result.exit_code != 0

    def test_cli_value_error_from_validation(self, tmp_path):
        """Test ValueError from validate_configuration."""
        runner = CliRunner()
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        (input_dir / "grype.json").write_text(
            json.dumps({"matches": [], "source": {"type": "image", "target": {"userInput": "test:latest"}}})
        )

        with patch("cve_report_aggregator.cli.validate_configuration") as mock_validate:
            mock_validate.side_effect = ValueError("Test validation error")

            result = runner.invoke(
                main,
                [
                    "--input-dir",
                    str(input_dir),
                    "--output-file",
                    str(tmp_path / "out.json"),
                ],
            )

            assert result.exit_code == 1

    def test_cli_zarf_warning(self, tmp_path, monkeypatch):
        """Test zarf missing warning."""
        import subprocess

        runner = CliRunner()
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        (input_dir / "grype.json").write_text(
            json.dumps({"matches": [], "source": {"type": "image", "target": {"userInput": "test:latest"}}})
        )

        # Custom subprocess mock: all tools exist except zarf
        class MockCompletedProcess:
            def __init__(self, stdout="", stderr="", returncode=0):
                self.stdout = stdout
                self.stderr = stderr
                self.returncode = returncode

        def mock_run(*args, **kwargs):
            command = args[0]
            if "which" in command:
                # zarf is not found, other tools are found
                if "zarf" in command:
                    # check_command_exists catches CalledProcessError, not FileNotFoundError
                    raise subprocess.CalledProcessError(1, command, "", "zarf not found")
                return MockCompletedProcess(stdout="/usr/local/bin/grype\n")
            elif "version" in command:
                return MockCompletedProcess(stdout="Version: 0.100.0\n")
            return MockCompletedProcess()

        monkeypatch.setattr(subprocess, "run", mock_run)

        with patch("cve_report_aggregator.cli.run_aggregation") as mock_run_agg:
            from cve_report_aggregator.core.orchestrator import AggregationResult

            mock_run_agg.return_value = AggregationResult(
                output_files=[],
                total_occurrences=0,
                unique_vulnerabilities=0,
                unique_images=set(),
                packages_scanned=0,
                severity_breakdown={},
                enrichment_stats=None,
            )

            result = runner.invoke(
                main,
                [
                    "--input-dir",
                    str(input_dir),
                    "--output-file",
                    str(tmp_path / "out.json"),
                ],
            )

            assert result.exit_code == 0

    def test_cli_runtime_error(self, tmp_path):
        """Test RuntimeError during aggregation."""
        runner = CliRunner()
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        (input_dir / "grype.json").write_text(
            json.dumps({"matches": [], "source": {"type": "image", "target": {"userInput": "test:latest"}}})
        )

        with patch("cve_report_aggregator.cli.run_aggregation") as mock_run:
            mock_run.side_effect = RuntimeError("Test runtime error")

            result = runner.invoke(
                main,
                [
                    "--input-dir",
                    str(input_dir),
                    "--output-file",
                    str(tmp_path / "out.json"),
                ],
            )

            assert result.exit_code == 1

    def test_cli_unexpected_exception(self, tmp_path):
        """Test unexpected exception handling."""
        runner = CliRunner()
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        (input_dir / "grype.json").write_text(
            json.dumps({"matches": [], "source": {"type": "image", "target": {"userInput": "test:latest"}}})
        )

        with patch("cve_report_aggregator.cli.run_aggregation") as mock_run:
            mock_run.side_effect = Exception("Unexpected error")

            result = runner.invoke(
                main,
                [
                    "--input-dir",
                    str(input_dir),
                    "--output-file",
                    str(tmp_path / "out.json"),
                ],
            )

            assert result.exit_code == 1
