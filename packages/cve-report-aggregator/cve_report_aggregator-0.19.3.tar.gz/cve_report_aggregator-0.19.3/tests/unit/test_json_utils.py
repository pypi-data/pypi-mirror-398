"""Comprehensive tests for json_utils module.

This test suite validates JSON loading functionality including error handling
for various failure scenarios (invalid JSON, file I/O errors, type validation).
"""

import json
from pathlib import Path

import pytest

from cve_report_aggregator.core.exceptions import ReportLoadError
from cve_report_aggregator.core.json_utils import load_json_report


class TestLoadJsonReport:
    """Tests for load_json_report function."""

    def test_load_valid_json_report(self, tmp_path):
        """Test loading a valid JSON report file."""
        report_file = tmp_path / "report.json"
        report_data = {
            "matches": [{"vulnerability": {"id": "CVE-2024-12345"}}],
            "source": {"target": {"userInput": "nginx:1.21"}},
        }
        report_file.write_text(json.dumps(report_data))

        result = load_json_report(report_file)

        assert result == report_data
        assert isinstance(result, dict)
        assert "matches" in result
        assert "source" in result

    def test_load_json_with_nested_structures(self, tmp_path):
        """Test loading JSON with deeply nested structures."""
        report_file = tmp_path / "nested.json"
        report_data = {
            "level1": {"level2": {"level3": {"data": "value", "array": [1, 2, 3], "nested": {"key": "val"}}}}
        }
        report_file.write_text(json.dumps(report_data))

        result = load_json_report(report_file)

        assert result == report_data
        assert result["level1"]["level2"]["level3"]["data"] == "value"

    def test_load_json_with_unicode_characters(self, tmp_path):
        """Test loading JSON with unicode characters."""
        report_file = tmp_path / "unicode.json"
        report_data = {
            "description": "Test vulnerability with unicode: 中文 العربية 日本語",
            "special_chars": "Ñoño €100 ©2024",
        }
        report_file.write_text(json.dumps(report_data, ensure_ascii=False))

        result = load_json_report(report_file)

        assert result == report_data
        assert "中文" in result["description"]

    def test_load_json_empty_dict(self, tmp_path):
        """Test loading an empty JSON object."""
        report_file = tmp_path / "empty.json"
        report_file.write_text("{}")

        result = load_json_report(report_file)

        assert result == {}
        assert isinstance(result, dict)

    def test_invalid_json_syntax(self, tmp_path):
        """Test that invalid JSON syntax raises ReportLoadError."""
        report_file = tmp_path / "invalid.json"
        report_file.write_text('{"invalid": "json" missing brace')

        with pytest.raises(ReportLoadError) as exc_info:
            load_json_report(report_file)

        assert "Invalid JSON" in str(exc_info.value)
        assert str(report_file) in str(exc_info.value)

    def test_json_with_trailing_comma(self, tmp_path):
        """Test that JSON with trailing comma raises ReportLoadError."""
        report_file = tmp_path / "trailing.json"
        report_file.write_text('{"key": "value",}')  # Trailing comma (invalid JSON)

        with pytest.raises(ReportLoadError) as exc_info:
            load_json_report(report_file)

        assert "Invalid JSON" in str(exc_info.value)

    def test_json_array_raises_error(self, tmp_path):
        """Test that JSON array (not object) raises ReportLoadError."""
        report_file = tmp_path / "array.json"
        report_file.write_text("[1, 2, 3]")

        with pytest.raises(ReportLoadError) as exc_info:
            load_json_report(report_file)

        assert "Expected JSON object (dict), got list" in str(exc_info.value)
        assert str(report_file) in str(exc_info.value)

    def test_json_string_raises_error(self, tmp_path):
        """Test that JSON string raises ReportLoadError."""
        report_file = tmp_path / "string.json"
        report_file.write_text('"just a string"')

        with pytest.raises(ReportLoadError) as exc_info:
            load_json_report(report_file)

        assert "Expected JSON object (dict), got str" in str(exc_info.value)

    def test_json_number_raises_error(self, tmp_path):
        """Test that JSON number raises ReportLoadError."""
        report_file = tmp_path / "number.json"
        report_file.write_text("12345")

        with pytest.raises(ReportLoadError) as exc_info:
            load_json_report(report_file)

        assert "Expected JSON object (dict), got int" in str(exc_info.value)

    def test_json_null_raises_error(self, tmp_path):
        """Test that JSON null raises ReportLoadError."""
        report_file = tmp_path / "null.json"
        report_file.write_text("null")

        with pytest.raises(ReportLoadError) as exc_info:
            load_json_report(report_file)

        assert "Expected JSON object (dict), got NoneType" in str(exc_info.value)

    def test_file_not_found(self, tmp_path):
        """Test that missing file raises ReportLoadError with OSError."""
        nonexistent_file = tmp_path / "nonexistent.json"

        with pytest.raises(ReportLoadError) as exc_info:
            load_json_report(nonexistent_file)

        assert "File read error" in str(exc_info.value)
        assert str(nonexistent_file) in str(exc_info.value)

    def test_file_permission_denied(self, tmp_path):
        """Test that permission denied raises ReportLoadError with OSError."""
        report_file = tmp_path / "protected.json"
        report_file.write_text('{"test": "data"}')

        # Make file unreadable (platform dependent)
        import os
        import stat

        os.chmod(report_file, 0o000)

        try:
            with pytest.raises(ReportLoadError) as exc_info:
                load_json_report(report_file)

            assert "File read error" in str(exc_info.value)
        finally:
            # Restore permissions for cleanup
            os.chmod(report_file, stat.S_IRUSR | stat.S_IWUSR)

    def test_directory_instead_of_file(self, tmp_path):
        """Test that directory raises ReportLoadError with OSError."""
        directory = tmp_path / "directory"
        directory.mkdir()

        with pytest.raises(ReportLoadError) as exc_info:
            load_json_report(directory)

        assert "File read error" in str(exc_info.value) or "Expected JSON object" in str(exc_info.value)

    def test_empty_file(self, tmp_path):
        """Test that empty file raises ReportLoadError."""
        report_file = tmp_path / "empty.json"
        report_file.write_text("")

        with pytest.raises(ReportLoadError) as exc_info:
            load_json_report(report_file)

        assert "Invalid JSON" in str(exc_info.value)

    def test_file_with_only_whitespace(self, tmp_path):
        """Test that file with only whitespace raises ReportLoadError."""
        report_file = tmp_path / "whitespace.json"
        report_file.write_text("   \n\t   ")

        with pytest.raises(ReportLoadError) as exc_info:
            load_json_report(report_file)

        assert "Invalid JSON" in str(exc_info.value)

    def test_file_with_bom(self, tmp_path):
        """Test that JSON file with UTF-8 BOM raises ReportLoadError."""
        report_file = tmp_path / "bom.json"
        report_data = {"test": "data"}
        # Write with UTF-8 BOM (Python's json module doesn't handle this automatically)
        report_file.write_bytes(b"\xef\xbb\xbf" + json.dumps(report_data).encode("utf-8"))

        # BOM causes JSONDecodeError in standard json module
        with pytest.raises(ReportLoadError) as exc_info:
            load_json_report(report_file)

        assert "Invalid JSON" in str(exc_info.value)

    def test_malformed_unicode(self, tmp_path):
        """Test that malformed unicode raises ReportLoadError."""
        report_file = tmp_path / "bad_unicode.json"
        # Write invalid UTF-8 sequence
        report_file.write_bytes(b'{"test": "\xff\xfe invalid unicode"}')

        with pytest.raises(ReportLoadError) as exc_info:
            load_json_report(report_file)

        # Could be either a decode error (Unexpected error) or invalid JSON
        assert "unexpected error" in str(exc_info.value).lower() or "invalid json" in str(exc_info.value).lower()

    def test_very_large_json_file(self, tmp_path):
        """Test loading a large JSON file."""
        report_file = tmp_path / "large.json"
        # Create a large but valid JSON structure
        large_data = {"vulnerabilities": [{"id": f"CVE-2024-{i:05d}", "severity": "High"} for i in range(1000)]}
        report_file.write_text(json.dumps(large_data))

        result = load_json_report(report_file)

        assert len(result["vulnerabilities"]) == 1000
        assert result["vulnerabilities"][0]["id"] == "CVE-2024-00000"

    def test_json_with_comments_fails(self, tmp_path):
        """Test that JSON with comments (invalid JSON) raises error."""
        report_file = tmp_path / "comments.json"
        report_file.write_text("""
        {
            // This is a comment
            "key": "value"  /* inline comment */
        }
        """)

        with pytest.raises(ReportLoadError) as exc_info:
            load_json_report(report_file)

        assert "Invalid JSON" in str(exc_info.value)

    def test_exception_chaining(self, tmp_path):
        """Test that exceptions are properly chained."""
        report_file = tmp_path / "invalid.json"
        report_file.write_text("{invalid}")

        with pytest.raises(ReportLoadError) as exc_info:
            load_json_report(report_file)

        # Verify exception chaining
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, json.JSONDecodeError)

    def test_path_object_input(self, tmp_path):
        """Test that Path object is accepted as input."""
        report_file = tmp_path / "test.json"
        report_data = {"test": "value"}
        report_file.write_text(json.dumps(report_data))

        # Explicitly use Path object
        result = load_json_report(Path(report_file))

        assert result == report_data

    def test_symlink_to_json_file(self, tmp_path):
        """Test loading JSON through a symbolic link."""
        import os
        import sys

        # Skip on Windows where symlinks require special privileges
        if sys.platform == "win32":
            pytest.skip("Symlinks require special privileges on Windows")

        report_file = tmp_path / "original.json"
        report_data = {"test": "symlink"}
        report_file.write_text(json.dumps(report_data))

        symlink = tmp_path / "link.json"
        os.symlink(report_file, symlink)

        result = load_json_report(symlink)

        assert result == report_data
