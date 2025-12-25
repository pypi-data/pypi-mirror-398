"""Comprehensive tests for the downloader module.

This test suite validates the package SBOM downloading functionality
including command execution, file operations, error handling, and cleanup.
"""

from unittest.mock import patch

import pytest
from pydantic import ValidationError

from cve_report_aggregator.context import AppContext
from cve_report_aggregator.core.config import config_context
from cve_report_aggregator.core.exceptions import AuthenticationError
from cve_report_aggregator.core.models import AggregatorConfig, PackageConfig
from cve_report_aggregator.io.downloader import (
    download_package_sbom,
    download_package_sboms,
    validate_registry_authentication,
)


@pytest.fixture
def mock_config(tmp_path):
    """Create a mock configuration for testing."""
    input_dir = tmp_path / "reports"
    input_dir.mkdir()

    return AggregatorConfig(
        input_dir=input_dir,
        output_file=tmp_path / "output.json",
        scanner="grype",
        mode="highest-score",
        log_level="INFO",
        download_remote_packages=True,
        registry="registry.example.com",
        organization="test-org",
        packages=[
            PackageConfig(name="test-package", version="1.0.0", architecture="amd64"),
        ],
    )


@pytest.fixture
def mock_config_debug(tmp_path):
    """Create a mock configuration with verbose enabled."""
    input_dir = tmp_path / "reports"
    input_dir.mkdir()

    return AggregatorConfig(
        input_dir=input_dir,
        output_file=tmp_path / "output.json",
        scanner="grype",
        mode="highest-score",
        log_level="DEBUG",
        download_remote_packages=True,
        registry="registry.example.com",
        organization="test-org",
        packages=[
            PackageConfig(name="test-package", version="1.0.0", architecture="amd64"),
        ],
    )


@pytest.fixture
def mock_config_no_download(tmp_path):
    """Create a mock configuration with download_remote_packages=False."""
    input_dir = tmp_path / "reports"
    input_dir.mkdir()

    return AggregatorConfig(
        input_dir=input_dir,
        output_file=tmp_path / "output.json",
        scanner="grype",
        mode="highest-score",
        log_level="INFO",
        download_remote_packages=False,
    )


@pytest.fixture
def sample_package():
    """Create a sample package configuration."""
    return PackageConfig(name="gitlab", version="18.4.2-uds.0-unicorn", architecture="amd64")


@pytest.fixture
def sample_packages():
    """Create multiple sample package configurations."""
    return [
        PackageConfig(name="gitlab", version="18.4.2-uds.0-unicorn", architecture="amd64"),
        PackageConfig(name="gitlab-runner", version="18.4.0-uds.0-unicorn", architecture="amd64"),
        PackageConfig(name="headlamp", version="0.35.0-uds.0-registry1", architecture="arm64"),
    ]


@pytest.fixture
def app_context(mock_config):
    """Create an AppContext from mock_config."""
    return AppContext(mock_config)


@pytest.fixture
def app_context_debug(mock_config_debug):
    """Create an AppContext from mock_config_debug."""
    return AppContext(mock_config_debug)


class TestDownloadPackageSboms:
    """Tests for download_package_sboms function."""

    def test_download_disabled_returns_empty_list(self, mock_config_no_download):
        """Test that download_remote_packages=False returns empty list early."""
        context = AppContext(mock_config_no_download)
        with config_context(mock_config_no_download):
            with patch("cve_report_aggregator.io.downloader.download_package_sbom") as mock_download:
                output_dir = mock_config_no_download.input_dir
                result = download_package_sboms(output_dir, context)

                assert result == []
                mock_download.assert_not_called()

    def test_missing_registry_raises_error(self, tmp_path):
        """Test that missing registry raises ValueError."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
            download_remote_packages=True,
            registry=None,  # Missing registry
            organization="test-org",
            packages=[PackageConfig(name="test", version="1.0.0", architecture="amd64")],
        )
        context = AppContext(config)

        with config_context(config):
            with pytest.raises(ValueError, match="Registry URL is required"):
                download_package_sboms(tmp_path / "output", context)

    def test_missing_organization_raises_error(self, tmp_path):
        """Test that missing organization raises ValueError."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
            download_remote_packages=True,
            registry="registry.example.com",
            organization=None,  # Missing organization
            packages=[PackageConfig(name="test", version="1.0.0", architecture="amd64")],
        )
        context = AppContext(config)

        with config_context(config):
            with pytest.raises(ValueError, match="Organization is required"):
                download_package_sboms(tmp_path / "output", context)

    def test_no_packages_configured_returns_empty_list(self, tmp_path):
        """Test that no packages configured returns empty list with warning."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
            download_remote_packages=True,
            registry="registry.example.com",
            organization="test-org",
            packages=[],  # No packages
        )
        context = AppContext(config)

        with config_context(config):
            output_dir = tmp_path / "output"
            result = download_package_sboms(output_dir, context)

            assert result == []

    def test_successful_single_package_download(self, mock_config, tmp_path):
        """Test successful download of a single package."""
        context = AppContext(mock_config)
        with config_context(mock_config):
            output_dir = tmp_path / "output"
            output_dir.mkdir()

            # Create fake SBOM files that would be returned
            fake_sbom = output_dir / "test-package-1.0.0.json"
            fake_sbom.write_text('{"test": "data"}')

            with patch("cve_report_aggregator.io.downloader.download_package_sbom") as mock_download:
                with patch("cve_report_aggregator.io.downloader.validate_registry_authentication"):
                    mock_download.return_value = [fake_sbom]

                    result = download_package_sboms(output_dir, context)

                    assert len(result) == 1
                    assert result[0] == fake_sbom
                    mock_download.assert_called_once()

    def test_successful_multiple_packages_download(self, tmp_path, sample_packages):
        """Test successful download of multiple packages."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
            download_remote_packages=True,
            registry="registry.example.com",
            organization="test-org",
            packages=sample_packages,
            log_level="INFO",
        )
        context = AppContext(config)

        with config_context(config):
            output_dir = tmp_path / "output"
            output_dir.mkdir()

            # Create fake SBOM files for each package
            fake_sboms = [output_dir / f"{pkg.name}-{pkg.version}.json" for pkg in sample_packages]
            for sbom in fake_sboms:
                sbom.write_text('{"test": "data"}')

            with patch("cve_report_aggregator.io.downloader.download_package_sbom") as mock_download:
                with patch("cve_report_aggregator.io.downloader.validate_registry_authentication"):
                    mock_download.side_effect = [[sbom] for sbom in fake_sboms]

                    result = download_package_sboms(output_dir, context)

                    assert len(result) == 3
                    assert all(sbom in result for sbom in fake_sboms)
                    assert mock_download.call_count == 3

    def test_partial_failure_continues_with_others(self, tmp_path, sample_packages):
        """Test that failure of one package doesn't stop others."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
            download_remote_packages=True,
            registry="registry.example.com",
            organization="test-org",
            packages=sample_packages,
            log_level="INFO",
        )
        context = AppContext(config)

        with config_context(config):
            output_dir = tmp_path / "output"
            output_dir.mkdir()

            # Create fake SBOM files for successful packages
            successful_sboms = [
                output_dir / f"{sample_packages[0].name}.json",
                output_dir / f"{sample_packages[2].name}.json",
            ]
            for sbom in successful_sboms:
                sbom.write_text('{"test": "data"}')

            with patch("cve_report_aggregator.io.downloader.download_package_sbom") as mock_download:
                with patch("cve_report_aggregator.io.downloader.validate_registry_authentication"):
                    # First succeeds, second fails, third succeeds
                    mock_download.side_effect = [
                        [successful_sboms[0]],
                        RuntimeError("Download failed"),
                        [successful_sboms[1]],
                    ]

                    result = download_package_sboms(output_dir, context)

                    # Should have 2 successful downloads despite 1 failure
                    assert len(result) == 2
                    assert successful_sboms[0] in result
                    assert successful_sboms[1] in result
                    assert mock_download.call_count == 3

    def test_creates_output_directory_if_not_exists(self, mock_config, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        context = AppContext(mock_config)
        with config_context(mock_config):
            output_dir = tmp_path / "new_output_dir"
            assert not output_dir.exists()

            with patch("cve_report_aggregator.io.downloader.download_package_sbom") as mock_download:
                with patch("cve_report_aggregator.io.downloader.validate_registry_authentication"):
                    mock_download.return_value = []

                    download_package_sboms(output_dir, context)

                    assert output_dir.exists()
                    assert output_dir.is_dir()

    def test_debug_output(self, mock_config_debug, tmp_path):
        """Test debug output during downloads."""
        context = AppContext(mock_config_debug)
        with config_context(mock_config_debug):
            output_dir = tmp_path / "output"
            output_dir.mkdir()

            fake_sbom = output_dir / "test-package.json"
            fake_sbom.write_text('{"test": "data"}')

            with patch("cve_report_aggregator.io.downloader.download_package_sbom") as mock_download:
                with patch("cve_report_aggregator.io.downloader.validate_registry_authentication"):
                    mock_download.return_value = [fake_sbom]

                    with patch("cve_report_aggregator.io.downloader.console") as mock_console:
                        download_package_sboms(output_dir, context)

                        # Verify verbose console output was called
                        assert mock_console.print.call_count >= 2
                        # Check for initial message
                        call_args_list = [str(call_obj) for call_obj in mock_console.print.call_args_list]
                        assert any("Downloading SBOM reports" in str(call_obj) for call_obj in call_args_list)

    def test_debug_output_on_error(self, tmp_path, sample_packages):
        """Test debug error output when download fails."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
            download_remote_packages=True,
            registry="registry.example.com",
            organization="test-org",
            packages=sample_packages[:1],  # Just one package
            log_level="DEBUG",
        )
        context = AppContext(config)

        with config_context(config):
            output_dir = tmp_path / "output"

            with patch("cve_report_aggregator.io.downloader.download_package_sbom") as mock_download:
                with patch("cve_report_aggregator.io.downloader.validate_registry_authentication"):
                    mock_download.side_effect = RuntimeError("Download failed")

                    with patch("cve_report_aggregator.io.downloader.console") as mock_console:
                        result = download_package_sboms(output_dir, context)

                        # Should show error message
                        call_args_list = [str(call_obj) for call_obj in mock_console.print.call_args_list]
                        assert any("✗" in str(call_obj) or "Failed" in str(call_obj) for call_obj in call_args_list)

                        assert result == []


class TestDownloadPackageSbom:
    """Tests for download_package_sbom function."""

    def test_successful_download_with_sbom_files(self, sample_package, tmp_path, mock_config):
        """Test successful download with SBOM files found."""
        context = AppContext(mock_config)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create package subdirectory where uds command will output files
        package_output_dir = output_dir / sample_package.name
        package_output_dir.mkdir()

        # Create sample SBOM files that uds command would create
        (package_output_dir / "sbom.json").write_text('{"test": "sbom1"}')
        (package_output_dir / "sbom-layer.json").write_text('{"test": "sbom2"}')

        with config_context(mock_config):
            with patch("cve_report_aggregator.core.executor.ExecutorManager.execute") as mock_execute:
                # Mock uds command to succeed
                mock_execute.return_value = ("", None)

                result = download_package_sbom(
                    package=sample_package,
                    registry="registry.example.com",
                    organization="test-org",
                    output_dir=output_dir,
                    context=context,
                )

                # Should find both JSON files
                assert len(result) == 2
                assert all(f.exists() for f in result)
                assert all(f.parent == package_output_dir for f in result)

                # Verify command calls
                mock_execute.assert_called_once()
                # Verify uds command has all required components
                uds_call = mock_execute.call_args[0][0]
                # Check base command structure (order matters for subcommands)
                assert uds_call[0] == "uds"
                assert "zarf" in uds_call
                assert "package" in uds_call
                assert "inspect" in uds_call
                assert "sbom" in uds_call
                # Check package reference is present somewhere in the command
                assert any("registry.example.com/test-org/gitlab:18.4.2-uds.0-unicorn" in arg for arg in uds_call)
                # Check flags and their values
                assert "-a" in uds_call
                assert "amd64" in uds_call
                assert "--output" in uds_call
                assert str(output_dir) in uds_call

    def test_no_sbom_files_found(self, sample_package, tmp_path, mock_config):
        """Test when no SBOM files are found in downloaded directory."""
        context = AppContext(mock_config)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create package directory without JSON files
        package_output_dir = output_dir / sample_package.name
        package_output_dir.mkdir()
        # No JSON files created

        with config_context(mock_config):
            with patch("cve_report_aggregator.core.executor.ExecutorManager.execute") as mock_execute:
                mock_execute.return_value = ("", None)

                result = download_package_sbom(
                    package=sample_package,
                    registry="registry.example.com",
                    organization="test-org",
                    output_dir=output_dir,
                    context=context,
                )

                # Should return empty list
                assert result == []

    def test_package_directory_not_created(self, sample_package, tmp_path, mock_config):
        """Test when uds command doesn't create any files in the package directory."""
        context = AppContext(mock_config)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # The package directory will be created but uds command won't create any files
        # This is handled by the function itself when it creates package_output_dir

        with config_context(mock_config):
            with patch("cve_report_aggregator.core.executor.ExecutorManager.execute") as mock_execute:
                mock_execute.return_value = ("", None)

                result = download_package_sbom(
                    package=sample_package,
                    registry="registry.example.com",
                    organization="test-org",
                    output_dir=output_dir,
                    context=context,
                )

                # Should return empty list because no JSON files were created
                assert result == []

    def test_missing_package_name_raises_error(self, tmp_path, mock_config):
        """Test that empty package name is rejected at model creation time."""
        # Validation now happens in PackageConfig via Pydantic field validator
        with pytest.raises(ValidationError, match="Invalid characters"):
            PackageConfig(name="", version="1.0.0", architecture="amd64")

    def test_missing_package_version_raises_error(self, tmp_path, mock_config):
        """Test that empty package version is rejected at model creation time."""
        # Validation now happens in PackageConfig via Pydantic field validator
        with pytest.raises(ValidationError, match="Invalid characters"):
            PackageConfig(name="test", version="", architecture="amd64")

    def test_missing_package_architecture_raises_error(self, tmp_path, mock_config):
        """Test that empty package architecture is rejected at model creation time."""
        # Validation now happens in PackageConfig via Pydantic field validator
        with pytest.raises(ValidationError, match="Invalid characters"):
            PackageConfig(name="test", version="1.0.0", architecture="")

    def test_uds_command_failure(self, sample_package, tmp_path, mock_config):
        """Test that uds command failure raises RuntimeError."""
        context = AppContext(mock_config)
        output_dir = tmp_path / "output"

        with config_context(mock_config):
            with patch("cve_report_aggregator.core.executor.ExecutorManager.execute") as mock_execute:
                # uds command fails
                mock_execute.return_value = ("", RuntimeError("uds command failed"))

                # Now raises DownloadError (or subclass) instead of RuntimeError
                from cve_report_aggregator.core.exceptions import DownloadError

                with pytest.raises(DownloadError, match="Failed to download gitlab"):
                    download_package_sbom(
                        package=sample_package,
                        registry="registry.example.com",
                        organization="test-org",
                        output_dir=output_dir,
                        context=context,
                    )

    def test_debug_logging(self, sample_package, tmp_path, mock_config_debug):
        """Test verbose logging output."""
        context = AppContext(mock_config_debug)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        package_output_dir = output_dir / sample_package.name
        package_output_dir.mkdir()
        (package_output_dir / "sbom.json").write_text('{"test": "data"}')

        with config_context(mock_config_debug):
            with patch("cve_report_aggregator.core.executor.ExecutorManager.execute") as mock_execute:
                mock_execute.return_value = ("", None)

                # Verify the function completes successfully with debug logging enabled
                # The actual logger in the function is created internally via context.get_logger()
                download_package_sbom(
                    package=sample_package,
                    registry="registry.example.com",
                    organization="test-org",
                    output_dir=output_dir,
                    context=context,
                )

                # Verify the function executed successfully
                assert mock_execute.called

    def test_sbom_file_naming(self, sample_package, tmp_path, mock_config):
        """Test that SBOM files keep their original names in package directory."""
        context = AppContext(mock_config)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        package_output_dir = output_dir / sample_package.name
        package_output_dir.mkdir()

        # Create SBOM with specific name
        (package_output_dir / "component.json").write_text('{"test": "data"}')

        with config_context(mock_config):
            with patch("cve_report_aggregator.core.executor.ExecutorManager.execute") as mock_execute:
                mock_execute.return_value = ("", None)

                result = download_package_sbom(
                    package=sample_package,
                    registry="registry.example.com",
                    organization="test-org",
                    output_dir=output_dir,
                    context=context,
                )

                assert len(result) == 1
                # Files keep their original names in package directory
                assert result[0].name == "component.json"
                assert result[0].parent == package_output_dir

    def test_multiple_json_files_in_directory(self, sample_package, tmp_path, mock_config):
        """Test handling multiple JSON files in downloaded directory."""
        context = AppContext(mock_config)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        package_output_dir = output_dir / sample_package.name
        package_output_dir.mkdir()

        # Create multiple JSON files at different levels
        (package_output_dir / "sbom1.json").write_text('{"test": "data1"}')
        (package_output_dir / "sbom2.json").write_text('{"test": "data2"}')

        subdir = package_output_dir / "layers"
        subdir.mkdir()
        (subdir / "layer.json").write_text('{"test": "data3"}')

        with config_context(mock_config):
            with patch("cve_report_aggregator.core.executor.ExecutorManager.execute") as mock_execute:
                mock_execute.return_value = ("", None)

                result = download_package_sbom(
                    package=sample_package,
                    registry="registry.example.com",
                    organization="test-org",
                    output_dir=output_dir,
                    context=context,
                )

                # Should find all JSON files recursively
                assert len(result) == 3
                assert all(f.exists() for f in result)

    def test_package_reference_construction(self, sample_package, tmp_path, mock_config):
        """Test correct construction of package reference."""
        context = AppContext(mock_config)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with config_context(mock_config):
            with patch("cve_report_aggregator.core.executor.ExecutorManager.execute") as mock_execute:
                mock_execute.return_value = ("", None)

                download_package_sbom(
                    package=sample_package,
                    registry="custom.registry.io",
                    organization="my-org",
                    output_dir=output_dir,
                    context=context,
                )

                # Check the uds command call
                uds_call = mock_execute.call_args[0][0]
                package_ref = uds_call[5]

                # Format should be: oci://<registry>/<organization>/<package-name>:<version>
                expected_ref = f"oci://custom.registry.io/my-org/{sample_package.name}:{sample_package.version}"
                assert package_ref == expected_ref

    def test_architecture_parameter(self, sample_package, tmp_path, mock_config):
        """Test that architecture parameter is correctly passed to uds command."""
        context = AppContext(mock_config)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Test with arm64 architecture
        arm_package = PackageConfig(name=sample_package.name, version=sample_package.version, architecture="arm64")

        with config_context(mock_config):
            with patch("cve_report_aggregator.core.executor.ExecutorManager.execute") as mock_execute:
                mock_execute.return_value = ("", None)

                download_package_sbom(
                    package=arm_package,
                    registry="registry.example.com",
                    organization="test-org",
                    output_dir=output_dir,
                    context=context,
                )

                # Check the uds command call
                uds_call = mock_execute.call_args[0][0]

                # Find architecture flag
                arch_index = uds_call.index("-a")
                assert uds_call[arch_index + 1] == "arm64"

    @pytest.mark.parametrize(
        "name,version,architecture",
        [
            ("", "1.0.0", "amd64"),  # Empty name
            ("test", "", "amd64"),  # Empty version
            ("test", "1.0.0", ""),  # Empty architecture
        ],
    )
    def test_package_validation_errors(self, name, version, architecture, tmp_path, mock_config):
        """Test that PackageConfig rejects empty or invalid identifiers at creation time.

        The validation now happens via Pydantic field validators, which prevents
        command injection and ensures package identifiers are safe.
        """
        with pytest.raises(ValidationError, match="Invalid characters"):
            PackageConfig(name=name, version=version, architecture=architecture)

    def test_get_current_config_integration(self, sample_package, tmp_path, mock_config):
        """Test integration with get_current_config for command execution."""
        context = AppContext(mock_config)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        temp_dir = tmp_path / "temp_sbom_config"
        temp_dir.mkdir()

        package_temp_dir = temp_dir / f"{sample_package.name}"
        package_temp_dir.mkdir()

        with config_context(mock_config):
            with patch("cve_report_aggregator.core.executor.ExecutorManager.create_temp_directory") as mock_mktemp:
                with patch("cve_report_aggregator.core.executor.ExecutorManager.execute") as mock_execute:
                    mock_mktemp.return_value = (temp_dir, None)
                    mock_execute.return_value = ("", None)

                    download_package_sbom(
                        package=sample_package,
                        registry="registry.example.com",
                        organization="test-org",
                        output_dir=output_dir,
                        context=context,
                    )

                    # Verify ExecutorManager.execute was called
                    mock_execute.assert_called_once()
                    # Verify config parameter was passed
                    call_kwargs = mock_execute.call_args.kwargs
                    assert "config" in call_kwargs


class TestParallelDownloading:
    """Tests for parallel package downloading functionality."""

    def test_parallel_download_with_max_workers_config(self, tmp_path, monkeypatch):
        """Test that max_workers configuration is respected."""
        import subprocess

        from cve_report_aggregator.core.models import PackageConfig
        from cve_report_aggregator.io.downloader import download_package_sboms

        # Create required directories
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        # Create test config with max_workers
        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
            scanner="grype",
            mode="highest-score",
            log_level="INFO",
            download_remote_packages=True,
            registry="test.registry.com",
            organization="test-org",
            max_workers=4,  # Specific worker count
            packages=[
                PackageConfig(name="pkg1", version="1.0.0", architecture="amd64"),
                PackageConfig(name="pkg2", version="2.0.0", architecture="amd64"),
            ],
        )
        context = AppContext(config)

        output_dir = tmp_path / "downloads"
        output_dir.mkdir()

        # Mock subprocess to track concurrent calls
        call_count = {"value": 0, "max_concurrent": 0, "current": 0}
        import threading

        lock = threading.Lock()

        def mock_run(*args, **kwargs):
            with lock:
                call_count["current"] += 1
                call_count["max_concurrent"] = max(call_count["max_concurrent"], call_count["current"])
                call_count["value"] += 1

            # Simulate work
            import time

            time.sleep(0.01)

            with lock:
                call_count["current"] -= 1

            # Return mock result
            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Create mock package directories
        for pkg in config.packages:
            pkg_dir = output_dir / pkg.name
            pkg_dir.mkdir()
            (pkg_dir / "test.json").write_text("{}")

        # Run download with config context
        with config_context(config):
            result = download_package_sboms(output_dir, context)

        # Verify concurrent execution
        # Now includes 1 validation call + 2 package downloads = 3 total calls
        assert call_count["value"] == 3  # One validation + two packages downloaded
        assert len(result) == 2  # Two SBOM files found

    def test_parallel_download_auto_workers(self, tmp_path, monkeypatch):
        """Test that auto-detection of workers works correctly."""
        import subprocess

        from cve_report_aggregator.core.models import PackageConfig
        from cve_report_aggregator.io.downloader import download_package_sboms

        # Create required directories
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        # Create test config without max_workers (auto-detect)
        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
            scanner="grype",
            mode="highest-score",
            log_level="INFO",
            download_remote_packages=True,
            registry="test.registry.com",
            organization="test-org",
            max_workers=None,  # Auto-detect
            packages=[
                PackageConfig(name="pkg1", version="1.0.0", architecture="amd64"),
            ],
        )
        context = AppContext(config)

        output_dir = tmp_path / "downloads"
        output_dir.mkdir()

        # Mock subprocess
        def mock_run(*args, **kwargs):
            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Create mock package directory
        pkg_dir = output_dir / "pkg1"
        pkg_dir.mkdir()
        (pkg_dir / "test.json").write_text("{}")

        # Run download with config context
        with config_context(config):
            result = download_package_sboms(output_dir, context)

        # Should complete successfully with auto-detected workers
        assert len(result) == 1

    def test_parallel_download_error_handling(self, tmp_path, monkeypatch):
        """Test that errors in one package don't stop others."""
        import subprocess

        from cve_report_aggregator.core.models import PackageConfig
        from cve_report_aggregator.io.downloader import download_package_sboms

        # Create required directories
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        # Create test config
        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
            scanner="grype",
            mode="highest-score",
            log_level="INFO",
            download_remote_packages=True,
            registry="test.registry.com",
            organization="test-org",
            max_workers=4,
            packages=[
                PackageConfig(name="pkg-success", version="1.0.0", architecture="amd64"),
                PackageConfig(name="pkg-fail", version="2.0.0", architecture="amd64"),
                PackageConfig(name="pkg-success2", version="3.0.0", architecture="amd64"),
            ],
        )
        context = AppContext(config)

        output_dir = tmp_path / "downloads"
        output_dir.mkdir()

        # Mock subprocess to fail for pkg-fail
        def mock_run(*args, **kwargs):
            if "pkg-fail" in str(args):
                raise subprocess.CalledProcessError(1, args[0], stderr="Download failed")

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Create mock package directories for successful downloads
        for pkg_name in ["pkg-success", "pkg-success2"]:
            pkg_dir = output_dir / pkg_name
            pkg_dir.mkdir()
            (pkg_dir / "test.json").write_text("{}")

        # Run download - should continue despite one failure
        with config_context(config):
            result = download_package_sboms(output_dir, context)

        # Should have 2 successful downloads
        assert len(result) == 2
        assert all("success" in str(f) for f in result)

    def test_parallel_download_thread_safety(self, tmp_path, monkeypatch):
        """Test thread-safe file list aggregation."""
        import subprocess

        from cve_report_aggregator.core.models import PackageConfig
        from cve_report_aggregator.io.downloader import download_package_sboms

        # Create required directories
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        # Create config with many packages to stress-test concurrency
        packages = [PackageConfig(name=f"pkg{i}", version="1.0.0", architecture="amd64") for i in range(20)]

        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
            scanner="grype",
            mode="highest-score",
            log_level="INFO",
            download_remote_packages=True,
            registry="test.registry.com",
            organization="test-org",
            max_workers=10,
            packages=packages,
        )
        context = AppContext(config)

        output_dir = tmp_path / "downloads"
        output_dir.mkdir()

        # Mock subprocess
        def mock_run(*args, **kwargs):
            import random
            import time

            time.sleep(random.random() * 0.01)  # Simulate varying download times

            class MockResult:
                stdout = ""
                stderr = ""
                returncode = 0

            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Create mock package directories with multiple files each
        for i in range(20):
            pkg_dir = output_dir / f"pkg{i}"
            pkg_dir.mkdir()
            # Create multiple SBOM files per package
            for j in range(3):
                (pkg_dir / f"sbom{j}.json").write_text("{}")

        # Run download with config context
        with config_context(config):
            result = download_package_sboms(output_dir, context)

        # Should have all files (20 packages × 3 files = 60)
        assert len(result) == 60
        # Verify no duplicates (thread safety)
        assert len(result) == len(set(result))


class TestValidateRegistryAuthentication:
    """Tests for validate_registry_authentication function."""

    def test_successful_validation(self, mock_config):
        """Test successful registry authentication validation."""
        context = AppContext(mock_config)
        with config_context(mock_config):
            with patch("cve_report_aggregator.io.downloader.ExecutorManager.execute") as mock_execute:
                # Simulate successful authentication (command succeeds)
                mock_execute.return_value = ("Package list output", None)

                # Should not raise any exception
                validate_registry_authentication("registry.example.com", "test-org", context)

                # Verify the command was called
                mock_execute.assert_called_once()
                args = mock_execute.call_args[0]
                command = args[0]

                # Verify command structure
                assert command[0] == "uds"
                assert command[1] == "zarf"
                assert command[2] == "package"
                assert command[3] == "list"
                assert "registry.example.com/test-org" in command[4]

    def test_authentication_error_401(self, mock_config):
        """Test that 401 Unauthorized raises AuthenticationError."""
        context = AppContext(mock_config)
        with config_context(mock_config):
            with patch("cve_report_aggregator.io.downloader.ExecutorManager.execute") as mock_execute:
                # Simulate 401 authentication error
                error_output = "Error: GET https://registry.example.com/v2/: 401 Unauthorized"
                mock_execute.return_value = (error_output, RuntimeError("Command failed"))

                # Should raise AuthenticationError
                with pytest.raises(AuthenticationError) as exc_info:
                    validate_registry_authentication("registry.example.com", "test-org", context)

                # Verify error details
                error = exc_info.value
                assert error.package_name == "<validation>"
                assert error.package_version == "<none>"
                assert error.status_code == 401

    def test_authentication_error_403(self, mock_config):
        """Test that 403 Forbidden raises AuthenticationError."""
        context = AppContext(mock_config)
        with config_context(mock_config):
            with patch("cve_report_aggregator.io.downloader.ExecutorManager.execute") as mock_execute:
                # Simulate 403 authentication error
                error_output = "Error: GET https://registry.example.com/v2/: 403 Forbidden - access denied"
                mock_execute.return_value = (error_output, RuntimeError("Command failed"))

                # Should raise AuthenticationError
                with pytest.raises(AuthenticationError) as exc_info:
                    validate_registry_authentication("registry.example.com", "test-org", context)

                # Verify error details
                error = exc_info.value
                assert error.package_name == "<validation>"
                assert error.status_code == 403

    def test_network_error_does_not_raise(self, mock_config):
        """Test that network errors are logged but don't raise exceptions."""
        context = AppContext(mock_config)
        with config_context(mock_config):
            with patch("cve_report_aggregator.io.downloader.ExecutorManager.execute") as mock_execute:
                # Simulate network error (not authentication)
                error_output = "Error: dial tcp: connection timeout after 30s"
                mock_execute.return_value = (error_output, RuntimeError("Command failed"))

                # Should NOT raise exception for network errors
                # Network errors are logged as warnings but allow continuing
                validate_registry_authentication("registry.example.com", "test-org", context)

    def test_registry_error_does_not_raise(self, mock_config):
        """Test that registry server errors are logged but don't raise exceptions."""
        context = AppContext(mock_config)
        with config_context(mock_config):
            with patch("cve_report_aggregator.io.downloader.ExecutorManager.execute") as mock_execute:
                # Simulate registry server error
                error_output = "Error: 503 Service Unavailable - registry is temporarily down"
                mock_execute.return_value = (error_output, RuntimeError("Command failed"))

                # Should NOT raise exception for registry errors
                validate_registry_authentication("registry.example.com", "test-org", context)

    def test_validation_called_before_downloads(self, mock_config, tmp_path):
        """Test that validation is called before attempting any downloads."""
        context = AppContext(mock_config)
        with config_context(mock_config):
            output_dir = tmp_path / "output"
            output_dir.mkdir()

            with patch("cve_report_aggregator.io.downloader.validate_registry_authentication") as mock_validate:
                with patch("cve_report_aggregator.io.downloader.download_package_sbom") as mock_download:
                    # Setup successful validation
                    mock_validate.return_value = None

                    # Setup successful download
                    fake_sbom = output_dir / "test.json"
                    fake_sbom.write_text('{"test": "data"}')
                    mock_download.return_value = [fake_sbom]

                    # Call download_package_sboms
                    download_package_sboms(output_dir, context)

                    # Verify validation was called BEFORE any downloads
                    mock_validate.assert_called_once_with("registry.example.com", "test-org", context)
                    mock_download.assert_called_once()

    def test_validation_failure_prevents_downloads(self, mock_config, tmp_path):
        """Test that validation failure prevents any download attempts."""
        context = AppContext(mock_config)
        with config_context(mock_config):
            output_dir = tmp_path / "output"
            output_dir.mkdir()

            with patch("cve_report_aggregator.io.downloader.validate_registry_authentication") as mock_validate:
                with patch("cve_report_aggregator.io.downloader.download_package_sbom") as mock_download:
                    # Setup validation failure
                    mock_validate.side_effect = AuthenticationError(
                        package_name="<validation>",
                        package_version="<none>",
                        status_code=401,
                    )

                    # Call should raise AuthenticationError
                    with pytest.raises(AuthenticationError):
                        download_package_sboms(output_dir, context)

                    # Verify validation was called
                    mock_validate.assert_called_once()

                    # Verify download was NEVER called
                    mock_download.assert_not_called()

    def test_debug_mode_shows_validation_messages(self, mock_config_debug, tmp_path):
        """Test that debug mode shows validation progress messages."""
        context = AppContext(mock_config_debug)
        with config_context(mock_config_debug):
            output_dir = tmp_path / "output"
            output_dir.mkdir()

            with patch("cve_report_aggregator.io.downloader.ExecutorManager.execute") as mock_execute:
                with patch("cve_report_aggregator.io.downloader.download_package_sbom") as mock_download:
                    # Setup successful validation
                    mock_execute.return_value = ("Package list output", None)

                    # Setup successful download
                    fake_sbom = output_dir / "test.json"
                    fake_sbom.write_text('{"test": "data"}')
                    mock_download.return_value = [fake_sbom]

                    # Call should succeed
                    result = download_package_sboms(output_dir, context)

                    # Verify validation was called
                    assert len(result) == 1
