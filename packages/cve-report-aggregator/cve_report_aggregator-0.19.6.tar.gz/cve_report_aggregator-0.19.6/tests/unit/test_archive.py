"""Tests for the archive/tarball creation functionality."""

import tarfile
from unittest.mock import MagicMock

import pytest

from cve_report_aggregator.io.archive import create_tarball


@pytest.fixture
def mock_context():
    """Create a mock AppContext for testing."""
    context = MagicMock()
    logger = MagicMock()
    context.get_logger.return_value = logger
    return context


@pytest.fixture
def sample_output_files(tmp_path):
    """Create sample output files for tarball testing."""
    files = []

    # Create a JSON report file
    json_file = tmp_path / "reports" / "cve-report.json"
    json_file.parent.mkdir(parents=True, exist_ok=True)
    json_file.write_text('{"vulnerabilities": []}')
    files.append(json_file)

    # Create a CSV export file
    csv_file = tmp_path / "exports" / "cve-export.csv"
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    csv_file.write_text("cve_id,severity\nCVE-2024-1234,High")
    files.append(csv_file)

    # Create an SBOM file
    sbom_file = tmp_path / "sboms" / "component-sbom.json"
    sbom_file.parent.mkdir(parents=True, exist_ok=True)
    sbom_file.write_text('{"artifacts": []}')
    files.append(sbom_file)

    return files


class TestCreateTarball:
    """Tests for create_tarball function."""

    def test_creates_tarball_successfully(self, tmp_path, sample_output_files, mock_context):
        """Should create a valid gzip-compressed tarball."""
        tarball_path = tmp_path / "archive" / "artifacts.tar.gz"

        result = create_tarball(tarball_path, sample_output_files, mock_context)

        assert result == tarball_path
        assert tarball_path.exists()
        assert tarball_path.stat().st_size > 0

        # Verify it's a valid gzip tarball
        assert tarfile.is_tarfile(tarball_path)

    def test_tarball_contains_all_files(self, tmp_path, sample_output_files, mock_context):
        """Tarball should contain all specified files."""
        tarball_path = tmp_path / "archive" / "artifacts.tar.gz"

        create_tarball(tarball_path, sample_output_files, mock_context)

        # Extract and verify contents
        with tarfile.open(tarball_path, "r:gz") as tar:
            member_names = tar.getnames()

        expected_names = [f.name for f in sample_output_files]
        assert sorted(member_names) == sorted(expected_names)

    def test_tarball_stores_files_without_directory_structure(self, tmp_path, sample_output_files, mock_context):
        """Files should be stored with just their filename, not full path."""
        tarball_path = tmp_path / "archive" / "artifacts.tar.gz"

        create_tarball(tarball_path, sample_output_files, mock_context)

        with tarfile.open(tarball_path, "r:gz") as tar:
            for member in tar.getmembers():
                # Should be just filename, no directory separators
                assert "/" not in member.name
                assert "\\" not in member.name

    def test_creates_parent_directories(self, tmp_path, sample_output_files, mock_context):
        """Should create parent directories if they don't exist."""
        tarball_path = tmp_path / "deep" / "nested" / "archive" / "artifacts.tar.gz"

        assert not tarball_path.parent.exists()

        create_tarball(tarball_path, sample_output_files, mock_context)

        assert tarball_path.exists()

    def test_tarball_file_contents_preserved(self, tmp_path, mock_context):
        """File contents should be preserved in the tarball."""
        # Create a file with known content
        test_content = '{"test": "content", "number": 42}'
        test_file = tmp_path / "test.json"
        test_file.write_text(test_content)

        tarball_path = tmp_path / "archive" / "test.tar.gz"

        create_tarball(tarball_path, [test_file], mock_context)

        # Extract and verify content
        with tarfile.open(tarball_path, "r:gz") as tar:
            extracted = tar.extractfile("test.json")
            assert extracted is not None
            content = extracted.read().decode("utf-8")
            assert content == test_content

    def test_handles_empty_file_list(self, tmp_path, mock_context):
        """Should create an empty tarball for empty file list."""
        tarball_path = tmp_path / "archive" / "empty.tar.gz"

        result = create_tarball(tarball_path, [], mock_context)

        assert result == tarball_path
        assert tarball_path.exists()

        with tarfile.open(tarball_path, "r:gz") as tar:
            assert len(tar.getnames()) == 0

    def test_handles_large_files(self, tmp_path, mock_context):
        """Should handle larger files correctly."""
        # Create a file with ~1MB of content
        large_content = "x" * (1024 * 1024)
        large_file = tmp_path / "large.txt"
        large_file.write_text(large_content)

        tarball_path = tmp_path / "archive" / "large.tar.gz"

        create_tarball(tarball_path, [large_file], mock_context)

        # Tarball should exist and be compressed (smaller than original)
        assert tarball_path.exists()
        assert tarball_path.stat().st_size < large_file.stat().st_size

        # Verify content is preserved
        with tarfile.open(tarball_path, "r:gz") as tar:
            extracted = tar.extractfile("large.txt")
            assert extracted is not None
            content = extracted.read().decode("utf-8")
            assert content == large_content

    def test_handles_binary_files(self, tmp_path, mock_context):
        """Should handle binary files correctly."""
        # Create a binary file
        binary_content = bytes(range(256))
        binary_file = tmp_path / "binary.bin"
        binary_file.write_bytes(binary_content)

        tarball_path = tmp_path / "archive" / "binary.tar.gz"

        create_tarball(tarball_path, [binary_file], mock_context)

        # Verify content is preserved
        with tarfile.open(tarball_path, "r:gz") as tar:
            extracted = tar.extractfile("binary.bin")
            assert extracted is not None
            content = extracted.read()
            assert content == binary_content

    def test_raises_runtime_error_on_failure(self, tmp_path, mock_context):
        """Should raise RuntimeError when tarball creation fails."""
        # Try to create tarball with non-existent file
        non_existent_file = tmp_path / "does_not_exist.json"
        tarball_path = tmp_path / "archive" / "fail.tar.gz"

        with pytest.raises(RuntimeError, match="Tarball creation failed"):
            create_tarball(tarball_path, [non_existent_file], mock_context)

    def test_logs_creation_info(self, tmp_path, sample_output_files, mock_context):
        """Should log tarball creation information."""
        tarball_path = tmp_path / "archive" / "artifacts.tar.gz"

        create_tarball(tarball_path, sample_output_files, mock_context)

        # Verify logging calls
        logger = mock_context.get_logger.return_value

        # Should log start of creation
        logger.info.assert_any_call(
            "Creating tarball",
            tarball=str(tarball_path),
            file_count=len(sample_output_files),
        )

        # Should log successful completion
        assert any(call[0][0] == "Tarball created successfully" for call in logger.info.call_args_list)

    def test_logs_individual_files_in_debug(self, tmp_path, sample_output_files, mock_context):
        """Should log each file added in debug mode."""
        tarball_path = tmp_path / "archive" / "artifacts.tar.gz"

        create_tarball(tarball_path, sample_output_files, mock_context)

        logger = mock_context.get_logger.return_value

        # Should have debug logs for each file
        debug_calls = [call for call in logger.debug.call_args_list if "Added file" in str(call)]
        assert len(debug_calls) == len(sample_output_files)

    def test_logs_error_on_failure(self, tmp_path, mock_context):
        """Should log error when creation fails."""
        non_existent_file = tmp_path / "does_not_exist.json"
        tarball_path = tmp_path / "archive" / "fail.tar.gz"

        with pytest.raises(RuntimeError):
            create_tarball(tarball_path, [non_existent_file], mock_context)

        logger = mock_context.get_logger.return_value
        logger.error.assert_called()

    def test_overwrites_existing_tarball(self, tmp_path, mock_context):
        """Should overwrite existing tarball if it exists."""
        tarball_path = tmp_path / "archive" / "artifacts.tar.gz"
        tarball_path.parent.mkdir(parents=True, exist_ok=True)

        # Create initial tarball with one file
        file1 = tmp_path / "file1.txt"
        file1.write_text("file1 content")
        create_tarball(tarball_path, [file1], mock_context)

        _initial_size = tarball_path.stat().st_size

        # Create new tarball with different file
        file2 = tmp_path / "file2.txt"
        file2.write_text("file2 content is longer than file1")
        create_tarball(tarball_path, [file2], mock_context)

        # Verify it was overwritten
        with tarfile.open(tarball_path, "r:gz") as tar:
            names = tar.getnames()
            assert "file2.txt" in names
            assert "file1.txt" not in names


class TestTarballIntegration:
    """Integration tests for tarball with real file system operations."""

    def test_roundtrip_extract(self, tmp_path, sample_output_files, mock_context):
        """Files should survive roundtrip through tarball."""
        tarball_path = tmp_path / "archive" / "artifacts.tar.gz"
        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()

        create_tarball(tarball_path, sample_output_files, mock_context)

        # Extract all files
        with tarfile.open(tarball_path, "r:gz") as tar:
            tar.extractall(extract_dir)

        # Verify all files exist and have correct content
        for original_file in sample_output_files:
            extracted_file = extract_dir / original_file.name
            assert extracted_file.exists()
            assert extracted_file.read_text() == original_file.read_text()

    def test_handles_unicode_filenames(self, tmp_path, mock_context):
        """Should handle files with unicode characters in names."""
        unicode_file = tmp_path / "report-日本語.json"
        unicode_file.write_text('{"test": "unicode"}')

        tarball_path = tmp_path / "archive" / "unicode.tar.gz"

        create_tarball(tarball_path, [unicode_file], mock_context)

        with tarfile.open(tarball_path, "r:gz") as tar:
            names = tar.getnames()
            assert "report-日本語.json" in names

    def test_handles_files_with_special_characters(self, tmp_path, mock_context):
        """Should handle files with special characters in content."""
        special_content = '{"emoji": "🔒🛡️", "special": "<>&\'"}'
        special_file = tmp_path / "special.json"
        special_file.write_text(special_content, encoding="utf-8")

        tarball_path = tmp_path / "archive" / "special.tar.gz"

        create_tarball(tarball_path, [special_file], mock_context)

        with tarfile.open(tarball_path, "r:gz") as tar:
            extracted = tar.extractfile("special.json")
            assert extracted is not None
            content = extracted.read().decode("utf-8")
            assert content == special_content
