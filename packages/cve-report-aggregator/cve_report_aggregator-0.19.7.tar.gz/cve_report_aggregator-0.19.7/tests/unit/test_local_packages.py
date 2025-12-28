"""Unit tests for local package scanning functionality."""

from pathlib import Path
from unittest.mock import patch

import pytest

from cve_report_aggregator.context import AppContext
from cve_report_aggregator.core.models import AggregatorConfig, PackageConfig
from cve_report_aggregator.io.local_packages import (
    detect_local_packages,
    extract_package_metadata,
    extract_package_sboms,
    scan_local_packages,
)


@pytest.fixture
def mock_context(tmp_path: Path) -> AppContext:
    """Create a mock AppContext for testing.

    Args:
        tmp_path: Pytest temporary directory fixture

    Returns:
        AppContext with test configuration
    """
    # Ensure input_dir exists before creating config
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    config = AggregatorConfig(
        input_dir=reports_dir,
        output_file=tmp_path / "output.json",
        scanner="grype",
        mode="highest-score",
        log_level="DEBUG",
    )
    return AppContext(config)


@pytest.fixture
def mock_packages_dir(tmp_path: Path) -> Path:
    """Create a mock packages directory with test archives.

    Args:
        tmp_path: Pytest temporary directory fixture

    Returns:
        Path to packages directory with mock .tar.zst files
    """
    packages_dir = tmp_path / "packages"
    packages_dir.mkdir(parents=True, exist_ok=True)

    # Create mock .tar.zst files
    (packages_dir / "zarf-package-test1-amd64-1.0.0.tar.zst").touch()
    (packages_dir / "zarf-package-test2-amd64-2.0.0.tar.zst").touch()
    (packages_dir / "zarf-init-amd64-v0.64.0.tar.zst").touch()

    # Create a non-archive file (should be ignored)
    (packages_dir / "readme.txt").touch()

    return packages_dir


class TestDetectLocalPackages:
    """Tests for detect_local_packages function."""

    def test_detect_packages_success(self, mock_packages_dir: Path) -> None:
        """Test successful detection of .tar.zst archives (filters out init packages)."""
        archives = detect_local_packages(mock_packages_dir)

        # Should detect 2 regular packages (init package is filtered out)
        assert len(archives) == 2
        assert all(path.suffix == ".zst" for path in archives)
        assert all(path.name.endswith(".tar.zst") for path in archives)
        # Verify init package is filtered out
        assert all(not path.name.startswith("zarf-init-") for path in archives)

    def test_detect_packages_empty_directory(self, tmp_path: Path) -> None:
        """Test detection in empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        archives = detect_local_packages(empty_dir)

        assert len(archives) == 0

    def test_detect_packages_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test detection with nonexistent directory."""
        nonexistent = tmp_path / "nonexistent"

        archives = detect_local_packages(nonexistent)

        assert len(archives) == 0

    def test_detect_packages_sorted(self, mock_packages_dir: Path) -> None:
        """Test that returned archives are sorted."""
        archives = detect_local_packages(mock_packages_dir)

        # Verify archives are sorted by name
        archive_names = [a.name for a in archives]
        assert archive_names == sorted(archive_names)


class TestExtractPackageMetadata:
    """Tests for extract_package_metadata function."""

    def test_extract_metadata_success(self, tmp_path: Path, mock_context: AppContext) -> None:
        """Test successful metadata extraction."""
        # Create a test archive
        archive = tmp_path / "test-package.tar.zst"
        archive.touch()

        # Mock the zarf command output
        mock_output = """
kind: ZarfPackageConfig
metadata:
  name: test-package
  version: 1.0.0
  architecture: amd64
"""

        with patch("cve_report_aggregator.io.local_packages.ExecutorManager.execute") as mock_exec:
            mock_exec.return_value = (mock_output, None)

            metadata = extract_package_metadata(archive, mock_context)

            assert metadata.name == "test-package"
            assert metadata.version == "1.0.0"
            assert metadata.architecture == "amd64"

    def test_extract_metadata_missing_architecture(self, tmp_path: Path, mock_context: AppContext) -> None:
        """Test metadata extraction with missing architecture (defaults to amd64)."""
        archive = tmp_path / "test-package.tar.zst"
        archive.touch()

        # Mock output without architecture field
        mock_output = """
kind: ZarfPackageConfig
metadata:
  name: test-package
  version: 1.0.0
"""

        with patch("cve_report_aggregator.io.local_packages.ExecutorManager.execute") as mock_exec:
            mock_exec.return_value = (mock_output, None)

            metadata = extract_package_metadata(archive, mock_context)

            assert metadata.name == "test-package"
            assert metadata.version == "1.0.0"
            assert metadata.architecture == "amd64"  # Default

    def test_extract_metadata_command_failure(self, tmp_path: Path, mock_context: AppContext) -> None:
        """Test metadata extraction when zarf command fails."""
        archive = tmp_path / "test-package.tar.zst"
        archive.touch()

        with patch("cve_report_aggregator.io.local_packages.ExecutorManager.execute") as mock_exec:
            mock_exec.return_value = ("", RuntimeError("Command failed"))

            with pytest.raises(RuntimeError, match="Failed to inspect Zarf package"):
                extract_package_metadata(archive, mock_context)

    def test_extract_metadata_missing_name(self, tmp_path: Path, mock_context: AppContext) -> None:
        """Test metadata extraction with missing name field."""
        archive = tmp_path / "test-package.tar.zst"
        archive.touch()

        # Mock output without name field
        mock_output = """
kind: ZarfPackageConfig
metadata:
  version: 1.0.0
  architecture: amd64
"""

        with patch("cve_report_aggregator.io.local_packages.ExecutorManager.execute") as mock_exec:
            mock_exec.return_value = (mock_output, None)

            with pytest.raises(RuntimeError, match="Failed to parse metadata"):
                extract_package_metadata(archive, mock_context)

    def test_extract_metadata_nonexistent_archive(self, tmp_path: Path, mock_context: AppContext) -> None:
        """Test metadata extraction with nonexistent archive."""
        archive = tmp_path / "nonexistent.tar.zst"

        with pytest.raises(ValueError, match="Archive does not exist"):
            extract_package_metadata(archive, mock_context)


class TestExtractPackageSboms:
    """Tests for extract_package_sboms function."""

    def test_extract_sboms_success(self, tmp_path: Path, mock_context: AppContext) -> None:
        """Test successful SBOM extraction."""
        archive = tmp_path / "test-package.tar.zst"
        archive.touch()

        package = PackageConfig(
            name="test-package",
            version="1.0.0",
            architecture="amd64",
        )

        output_dir = tmp_path / "output"
        package_output_dir = output_dir / "test-package"

        # Create mock SBOM files
        package_output_dir.mkdir(parents=True, exist_ok=True)
        sbom1 = package_output_dir / "sbom1.json"
        sbom2 = package_output_dir / "sbom2.json"
        sbom1.write_text("{}")
        sbom2.write_text("{}")

        with patch("cve_report_aggregator.io.local_packages.ExecutorManager.execute") as mock_exec:
            mock_exec.return_value = ("Success", None)

            sboms = extract_package_sboms(archive, package, output_dir, mock_context)

            assert len(sboms) == 2
            assert all(sbom.suffix == ".json" for sbom in sboms)

    def test_extract_sboms_command_failure(self, tmp_path: Path, mock_context: AppContext) -> None:
        """Test SBOM extraction when zarf command fails."""
        archive = tmp_path / "test-package.tar.zst"
        archive.touch()

        package = PackageConfig(
            name="test-package",
            version="1.0.0",
            architecture="amd64",
        )

        output_dir = tmp_path / "output"

        with patch("cve_report_aggregator.io.local_packages.ExecutorManager.execute") as mock_exec:
            mock_exec.return_value = ("", RuntimeError("Command failed"))

            with pytest.raises(RuntimeError, match="Failed to extract SBOMs"):
                extract_package_sboms(archive, package, output_dir, mock_context)

    def test_extract_sboms_no_json_files(self, tmp_path: Path, mock_context: AppContext) -> None:
        """Test SBOM extraction when no JSON files are found."""
        archive = tmp_path / "test-package.tar.zst"
        archive.touch()

        package = PackageConfig(
            name="test-package",
            version="1.0.0",
            architecture="amd64",
        )

        output_dir = tmp_path / "output"
        package_output_dir = output_dir / "test-package"
        package_output_dir.mkdir(parents=True, exist_ok=True)

        # Create non-JSON file
        (package_output_dir / "readme.txt").write_text("test")

        with patch("cve_report_aggregator.io.local_packages.ExecutorManager.execute") as mock_exec:
            mock_exec.return_value = ("Success", None)

            sboms = extract_package_sboms(archive, package, output_dir, mock_context)

            assert len(sboms) == 0


class TestScanLocalPackages:
    """Tests for scan_local_packages function."""

    def test_scan_packages_success(self, tmp_path: Path, mock_context: AppContext) -> None:
        """Test successful scanning of local packages."""
        # Create a packages directory in tmp_path
        packages_dir = tmp_path / "packages"
        packages_dir.mkdir()

        # Create a mock archive
        mock_archive = packages_dir / "test.tar.zst"
        mock_archive.touch()

        # Mock Path.cwd() to return tmp_path
        with (
            patch("cve_report_aggregator.io.local_packages.Path.cwd") as mock_cwd,
            patch("cve_report_aggregator.io.local_packages.extract_package_metadata") as mock_extract_meta,
            patch("cve_report_aggregator.io.local_packages.extract_package_sboms") as mock_extract_sboms,
        ):
            mock_cwd.return_value = tmp_path

            # Mock extract_package_metadata
            mock_package = PackageConfig(
                name="test-package",
                version="1.0.0",
                architecture="amd64",
            )
            mock_extract_meta.return_value = mock_package

            # Mock extract_package_sboms
            mock_sbom = tmp_path / "sbom.json"
            mock_sbom.write_text("{}")
            mock_extract_sboms.return_value = [mock_sbom]

            sboms = scan_local_packages(tmp_path / "output", mock_context)

            assert len(sboms) == 1
            assert sboms[0] == mock_sbom

    def test_scan_packages_no_packages_dir(self, tmp_path: Path, mock_context: AppContext) -> None:
        """Test scanning when packages directory doesn't exist."""
        with patch("cve_report_aggregator.io.local_packages.Path.cwd") as mock_cwd:
            mock_cwd.return_value = tmp_path

            sboms = scan_local_packages(tmp_path / "output", mock_context)

            assert len(sboms) == 0

    def test_scan_packages_empty_directory(self, tmp_path: Path, mock_context: AppContext) -> None:
        """Test scanning with empty packages directory."""
        # Create an empty packages directory
        packages_dir = tmp_path / "packages"
        packages_dir.mkdir()

        with patch("cve_report_aggregator.io.local_packages.Path.cwd") as mock_cwd:
            mock_cwd.return_value = tmp_path

            sboms = scan_local_packages(tmp_path / "output", mock_context)

            assert len(sboms) == 0

    def test_scan_packages_handles_errors(self, tmp_path: Path, mock_context: AppContext) -> None:
        """Test that scanning continues on individual package errors."""
        # Create packages directory with archives
        packages_dir = tmp_path / "packages"
        packages_dir.mkdir()

        mock_archive1 = packages_dir / "test1.tar.zst"
        mock_archive2 = packages_dir / "test2.tar.zst"
        mock_archive1.touch()
        mock_archive2.touch()

        with (
            patch("cve_report_aggregator.io.local_packages.Path.cwd") as mock_cwd,
            patch("cve_report_aggregator.io.local_packages.extract_package_metadata") as mock_extract_meta,
            patch("cve_report_aggregator.io.local_packages.extract_package_sboms") as mock_extract_sboms,
        ):
            mock_cwd.return_value = tmp_path

            # First fails, second succeeds
            mock_extract_meta.side_effect = [
                RuntimeError("Failed to extract metadata"),
                PackageConfig(name="test2", version="2.0.0", architecture="amd64"),
            ]

            # Mock SBOM extraction for successful package
            mock_sbom = tmp_path / "sbom.json"
            mock_sbom.write_text("{}")
            mock_extract_sboms.return_value = [mock_sbom]

            # Should continue processing despite first archive failing
            sboms = scan_local_packages(tmp_path / "output", mock_context)

            # Should have SBOMs from second package only
            assert len(sboms) == 1

    def test_scan_packages_multiple_packages(self, tmp_path: Path, mock_context: AppContext) -> None:
        """Test scanning multiple local packages successfully."""
        packages_dir = tmp_path / "packages"
        packages_dir.mkdir()

        # Create multiple mock archives
        mock_archive1 = packages_dir / "test1.tar.zst"
        mock_archive2 = packages_dir / "test2.tar.zst"
        mock_archive1.touch()
        mock_archive2.touch()

        with (
            patch("cve_report_aggregator.io.local_packages.Path.cwd") as mock_cwd,
            patch("cve_report_aggregator.io.local_packages.extract_package_metadata") as mock_extract_meta,
            patch("cve_report_aggregator.io.local_packages.extract_package_sboms") as mock_extract_sboms,
        ):
            mock_cwd.return_value = tmp_path

            # Mock both packages successfully
            mock_extract_meta.side_effect = [
                PackageConfig(name="test1", version="1.0.0", architecture="amd64"),
                PackageConfig(name="test2", version="2.0.0", architecture="amd64"),
            ]

            # Mock SBOM extraction for both packages
            mock_sbom1 = tmp_path / "sbom1.json"
            mock_sbom2 = tmp_path / "sbom2.json"
            mock_sbom1.write_text("{}")
            mock_sbom2.write_text("{}")
            mock_extract_sboms.side_effect = [[mock_sbom1], [mock_sbom2]]

            sboms = scan_local_packages(tmp_path / "output", mock_context)

            # Should have SBOMs from both packages
            assert len(sboms) == 2

    def test_scan_packages_with_init_packages(self, tmp_path: Path, mock_context: AppContext) -> None:
        """Test that init packages are filtered out."""
        packages_dir = tmp_path / "packages"
        packages_dir.mkdir()

        # Create regular and init packages
        regular_archive = packages_dir / "test-package-amd64-1.0.0.tar.zst"
        init_archive = packages_dir / "zarf-init-amd64-v0.64.0.tar.zst"
        regular_archive.touch()
        init_archive.touch()

        with (
            patch("cve_report_aggregator.io.local_packages.Path.cwd") as mock_cwd,
            patch("cve_report_aggregator.io.local_packages.extract_package_metadata") as mock_extract_meta,
            patch("cve_report_aggregator.io.local_packages.extract_package_sboms") as mock_extract_sboms,
        ):
            mock_cwd.return_value = tmp_path

            # Mock metadata for regular package only
            mock_package = PackageConfig(
                name="test-package",
                version="1.0.0",
                architecture="amd64",
            )
            mock_extract_meta.return_value = mock_package

            # Mock SBOM extraction
            mock_sbom = tmp_path / "sbom.json"
            mock_sbom.write_text("{}")
            mock_extract_sboms.return_value = [mock_sbom]

            sboms = scan_local_packages(tmp_path / "output", mock_context)

            # Should only process regular package (init package filtered)
            assert len(sboms) == 1
            # extract_package_metadata should only be called once
            assert mock_extract_meta.call_count == 1


class TestExtractPackageMetadataEdgeCases:
    """Additional edge case tests for extract_package_metadata."""

    def test_extract_metadata_invalid_yaml(self, tmp_path: Path, mock_context: AppContext) -> None:
        """Test metadata extraction with invalid YAML."""
        archive = tmp_path / "test-package.tar.zst"
        archive.touch()

        # Mock output with invalid YAML
        mock_output = "{ invalid: yaml: format"

        with patch("cve_report_aggregator.io.local_packages.ExecutorManager.execute") as mock_exec:
            mock_exec.return_value = (mock_output, None)

            with pytest.raises(RuntimeError, match="Failed to parse metadata"):
                extract_package_metadata(archive, mock_context)

    def test_extract_metadata_empty_output(self, tmp_path: Path, mock_context: AppContext) -> None:
        """Test metadata extraction with empty command output."""
        archive = tmp_path / "test-package.tar.zst"
        archive.touch()

        with patch("cve_report_aggregator.io.local_packages.ExecutorManager.execute") as mock_exec:
            mock_exec.return_value = ("", None)

            with pytest.raises(RuntimeError, match="Failed to parse metadata"):
                extract_package_metadata(archive, mock_context)

    def test_extract_metadata_missing_version(self, tmp_path: Path, mock_context: AppContext) -> None:
        """Test metadata extraction with missing version field."""
        archive = tmp_path / "test-package.tar.zst"
        archive.touch()

        # Mock output without version field
        mock_output = """
kind: ZarfPackageConfig
metadata:
  name: test-package
  architecture: amd64
"""

        with patch("cve_report_aggregator.io.local_packages.ExecutorManager.execute") as mock_exec:
            mock_exec.return_value = (mock_output, None)

            with pytest.raises(RuntimeError, match="Failed to parse metadata"):
                extract_package_metadata(archive, mock_context)


class TestExtractPackageSbomsEdgeCases:
    """Additional edge case tests for extract_package_sboms."""

    def test_extract_sboms_nonexistent_archive(self, tmp_path: Path, mock_context: AppContext) -> None:
        """Test SBOM extraction with nonexistent archive."""
        archive = tmp_path / "nonexistent.tar.zst"

        package = PackageConfig(
            name="test-package",
            version="1.0.0",
            architecture="amd64",
        )

        output_dir = tmp_path / "output"

        with pytest.raises(ValueError, match="Archive does not exist"):
            extract_package_sboms(archive, package, output_dir, mock_context)

    def test_extract_sboms_creates_output_directory(self, tmp_path: Path, mock_context: AppContext) -> None:
        """Test that SBOM extraction creates output directory if it doesn't exist."""
        archive = tmp_path / "test-package.tar.zst"
        archive.touch()

        package = PackageConfig(
            name="test-package",
            version="1.0.0",
            architecture="amd64",
        )

        output_dir = tmp_path / "output"
        package_output_dir = output_dir / "test-package"

        with patch("cve_report_aggregator.io.local_packages.ExecutorManager.execute") as mock_exec:
            mock_exec.return_value = ("Success", None)

            # Create SBOM files after command execution (simulating zarf extract)
            def create_sboms(*args, **kwargs):
                package_output_dir.mkdir(parents=True, exist_ok=True)
                (package_output_dir / "sbom.json").write_text("{}")
                return ("Success", None)

            mock_exec.side_effect = create_sboms

            sboms = extract_package_sboms(archive, package, output_dir, mock_context)

            # Directory should be created
            assert package_output_dir.exists()
            assert len(sboms) == 1

    def test_extract_sboms_filters_nested_directories(self, tmp_path: Path, mock_context: AppContext) -> None:
        """Test that SBOM extraction only includes direct JSON files, not nested ones."""
        archive = tmp_path / "test-package.tar.zst"
        archive.touch()

        package = PackageConfig(
            name="test-package",
            version="1.0.0",
            architecture="amd64",
        )

        output_dir = tmp_path / "output"
        package_output_dir = output_dir / "test-package"
        package_output_dir.mkdir(parents=True, exist_ok=True)

        # Create JSON files at root level
        (package_output_dir / "sbom1.json").write_text("{}")
        (package_output_dir / "sbom2.json").write_text("{}")

        # Create nested directory with JSON files (should be excluded)
        nested_dir = package_output_dir / "nested"
        nested_dir.mkdir()
        (nested_dir / "nested_sbom.json").write_text("{}")

        with patch("cve_report_aggregator.io.local_packages.ExecutorManager.execute") as mock_exec:
            mock_exec.return_value = ("Success", None)

            sboms = extract_package_sboms(archive, package, output_dir, mock_context)

            # Should only include root-level JSON files
            assert len(sboms) == 2
            assert all(sbom.parent == package_output_dir for sbom in sboms)
