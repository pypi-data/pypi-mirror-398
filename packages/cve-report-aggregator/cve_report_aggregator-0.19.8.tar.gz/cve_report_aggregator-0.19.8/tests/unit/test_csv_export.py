"""Unit tests for CSV export functionality."""

import csv

import pytest

from src.cve_report_aggregator.io.csv_export import (
    export_to_csv,
    extract_cvss_score,
    extract_impact_message,
    extract_mitigation_message,
)


@pytest.fixture
def sample_unified_report():
    """Sample unified report for testing."""
    return {
        "metadata": {"scanner": "grype", "timestamp": "2025-01-20T12:00:00Z"},
        "summary": {
            "total_vulnerability_occurrences": 8,
            "unique_vulnerabilities": 3,
            "by_severity": {"Critical": 1, "High": 1, "Medium": 1},
        },
        "vulnerabilities": [
            {
                "vulnerability_id": "CVE-2024-12345",
                "count": 5,
                "vulnerability": {
                    "severity": "Critical",
                    "cvss": [
                        {"version": "3.1", "metrics": {"baseScore": 9.8}},
                    ],
                },
            },
            {
                "vulnerability_id": "CVE-2024-12346",
                "count": 2,
                "vulnerability": {
                    "severity": "High",
                    "cvss": [
                        {"version": "3.1", "metrics": {"baseScore": 7.5}},
                    ],
                },
            },
            {
                "vulnerability_id": "CVE-2024-12347",
                "count": 1,
                "vulnerability": {
                    "severity": "Medium",
                    "cvss": [],
                },
            },
        ],
    }


@pytest.fixture
def sample_enrichments():
    """Sample enrichment data for testing."""
    return {
        "CVE-2024-12345": {
            "cve_id": "CVE-2024-12345",
            "mitigation_summary": ("UDS helps to mitigate CVE-2024-12345 by enforcing non-root container execution."),
            "impact_analysis": (
                "Without UDS Core controls, this critical vulnerability could allow remote code execution."
            ),
            "analysis_model": "x-ai/grok-code-fast-1",
            "analysis_timestamp": "2025-01-20T12:00:00Z",
        },
        "CVE-2024-12346": {
            "cve_id": "CVE-2024-12346",
            "mitigation_summary": "UDS helps to mitigate CVE-2024-12346 by blocking external network access.",
            "impact_analysis": "This vulnerability could enable lateral movement across the cluster.",
            "analysis_model": "x-ai/grok-code-fast-1",
            "analysis_timestamp": "2025-01-20T12:00:00Z",
        },
    }


class TestExtractFunctions:
    """Test extraction helper functions."""

    def test_extract_cvss_score_with_valid_score(self):
        """Test extracting valid CVSS 3.x score."""
        vuln_data = {
            "cvss": [
                {"version": "3.1", "metrics": {"baseScore": 9.8}},
            ]
        }
        assert extract_cvss_score(vuln_data) == "9.8"

    def test_extract_cvss_score_with_no_score(self):
        """Test extracting CVSS when no score available."""
        vuln_data = {"cvss": []}
        assert extract_cvss_score(vuln_data) == "N/A"

    def test_extract_cvss_score_with_multiple_scores(self):
        """Test extracting highest CVSS when multiple scores exist."""
        vuln_data = {
            "cvss": [
                {"version": "3.1", "metrics": {"baseScore": 7.5}},
                {"version": "3.0", "metrics": {"baseScore": 9.8}},
            ]
        }
        assert extract_cvss_score(vuln_data) == "9.8"

    def test_extract_impact_message_exists(self):
        """Test extracting impact message when it exists."""
        enrichment = {"impact_analysis": "This is a critical vulnerability that could lead to remote code execution."}
        assert (
            extract_impact_message(enrichment)
            == "This is a critical vulnerability that could lead to remote code execution."
        )

    def test_extract_impact_message_missing(self):
        """Test extracting impact message when it doesn't exist."""
        enrichment = {"mitigation_summary": "Some mitigation"}
        assert extract_impact_message(enrichment) == ""

    def test_extract_mitigation_message_exists(self):
        """Test extracting mitigation message when it exists."""
        enrichment = {"mitigation_summary": "UDS helps to mitigate CVE-2024-12345 by enforcing non-root execution."}
        assert (
            extract_mitigation_message(enrichment)
            == "UDS helps to mitigate CVE-2024-12345 by enforcing non-root execution."
        )

    def test_extract_mitigation_message_missing(self):
        """Test extracting mitigation message when it doesn't exist."""
        enrichment = {"impact_analysis": "Some impact"}
        assert extract_mitigation_message(enrichment) == ""


class TestCSVExport:
    """Test CSV export functionality."""

    def test_export_to_csv_without_enrichments(self, sample_unified_report, tmp_path):
        """Test CSV export without enrichments."""
        output_file = tmp_path / "test_report.csv"

        export_to_csv(sample_unified_report, output_file, enrichments=None)

        assert output_file.exists()

        # Read and verify CSV content
        with open(output_file, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

        # Should have 3 rows (one per vulnerability)
        assert len(rows) == 3

        # Verify header
        assert set(rows[0].keys()) == {"CVE ID", "Severity", "Count", "CVSS", "Impact", "Mitigation"}

        # Verify first row (Critical vulnerability)
        assert rows[0]["CVE ID"] == "CVE-2024-12345"
        assert rows[0]["Severity"] == "Critical"
        assert rows[0]["Count"] == "5"
        assert rows[0]["CVSS"] == "9.8"
        assert rows[0]["Impact"] == ""
        assert rows[0]["Mitigation"] == ""

        # Verify sorting (Critical > High > Medium)
        assert rows[0]["Severity"] == "Critical"
        assert rows[1]["Severity"] == "High"
        assert rows[2]["Severity"] == "Medium"

    def test_export_to_csv_with_enrichments(self, sample_unified_report, sample_enrichments, tmp_path):
        """Test CSV export with enrichments."""
        output_file = tmp_path / "test_report_enriched.csv"

        export_to_csv(sample_unified_report, output_file, enrichments=sample_enrichments)

        assert output_file.exists()

        # Read and verify CSV content
        with open(output_file, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

        # Verify enrichment data is included
        assert rows[0]["CVE ID"] == "CVE-2024-12345"
        assert (
            rows[0]["Impact"]
            == "Without UDS Core controls, this critical vulnerability could allow remote code execution."
        )
        assert (
            rows[0]["Mitigation"] == "UDS helps to mitigate CVE-2024-12345 by enforcing non-root container execution."
        )

        # Verify second CVE has enrichment
        assert rows[1]["CVE ID"] == "CVE-2024-12346"
        assert rows[1]["Impact"] == "This vulnerability could enable lateral movement across the cluster."
        assert rows[1]["Mitigation"] == "UDS helps to mitigate CVE-2024-12346 by blocking external network access."

        # Verify third CVE has no enrichment (not in enrichments dict)
        assert rows[2]["CVE ID"] == "CVE-2024-12347"
        assert rows[2]["Impact"] == ""
        assert rows[2]["Mitigation"] == ""

    def test_export_to_csv_empty_vulnerabilities(self, tmp_path):
        """Test CSV export with no vulnerabilities."""
        output_file = tmp_path / "test_empty.csv"
        report = {"vulnerabilities": []}

        export_to_csv(report, output_file, enrichments=None)

        # Should not create file when no vulnerabilities
        assert not output_file.exists()

    def test_export_to_csv_sorting_by_cvss(self, tmp_path):
        """Test that CVEs are sorted by CVSS score within same severity."""
        report = {
            "vulnerabilities": [
                {
                    "vulnerability_id": "CVE-2024-00001",
                    "count": 1,
                    "vulnerability": {
                        "severity": "High",
                        "cvss": [{"version": "3.1", "metrics": {"baseScore": 7.2}}],
                    },
                },
                {
                    "vulnerability_id": "CVE-2024-00002",
                    "count": 1,
                    "vulnerability": {
                        "severity": "High",
                        "cvss": [{"version": "3.1", "metrics": {"baseScore": 8.5}}],
                    },
                },
                {
                    "vulnerability_id": "CVE-2024-00003",
                    "count": 1,
                    "vulnerability": {
                        "severity": "High",
                        "cvss": [{"version": "3.1", "metrics": {"baseScore": 7.8}}],
                    },
                },
            ]
        }

        output_file = tmp_path / "test_sorting.csv"
        export_to_csv(report, output_file, enrichments=None)

        with open(output_file, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

        # Should be sorted by CVSS descending within High severity
        assert rows[0]["CVE ID"] == "CVE-2024-00002"  # 8.5
        assert rows[1]["CVE ID"] == "CVE-2024-00003"  # 7.8
        assert rows[2]["CVE ID"] == "CVE-2024-00001"  # 7.2
