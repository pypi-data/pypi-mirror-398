"""Tests for main entry point."""

import sys
from unittest.mock import patch

from cve_report_aggregator.__main__ import run


class TestMain:
    """Tests for main entry point function."""

    def test_run_displays_logo(self, monkeypatch):
        """Test that run() displays logo when not --version."""
        # Mock sys.argv without --version
        monkeypatch.setattr(sys, "argv", ["cve-report-aggregator"])

        # Mock the display_logo and main functions
        with (
            patch("cve_report_aggregator.__main__.display_logo") as mock_logo,
            patch("cve_report_aggregator.__main__.main") as mock_main,
        ):
            run()

            # Logo should be displayed
            mock_logo.assert_called_once()
            mock_main.assert_called_once()

    def test_run_skips_logo_with_version_flag(self, monkeypatch):
        """Test that run() skips logo when --version flag present."""
        # Mock sys.argv with --version
        monkeypatch.setattr(sys, "argv", ["cve-report-aggregator", "--version"])

        # Mock the display_logo and main functions
        with (
            patch("cve_report_aggregator.__main__.display_logo") as mock_logo,
            patch("cve_report_aggregator.__main__.main") as mock_main,
        ):
            run()

            # Logo should NOT be displayed
            mock_logo.assert_not_called()
            mock_main.assert_called_once()

    def test_run_as_main(self, monkeypatch):
        """Test running module as __main__."""
        # This is a bit meta, but we want to ensure the if __name__ == "__main__" block works
        monkeypatch.setattr(sys, "argv", ["cve-report-aggregator", "--version"])

        with patch("cve_report_aggregator.__main__.run"):
            # We can't easily test the actual if __name__ == "__main__" block
            # but we can verify the function exists and is callable
            assert callable(run)
