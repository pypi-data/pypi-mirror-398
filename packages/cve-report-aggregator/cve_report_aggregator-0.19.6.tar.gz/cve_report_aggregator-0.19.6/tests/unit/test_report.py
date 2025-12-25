"""Tests for report generation functionality."""

import copy

from cve_report_aggregator.io.report import create_executive_summary, create_unified_report


class TestCreateUnifiedReport:
    """Tests for create_unified_report function."""

    def test_create_report_with_grype_data(self, vuln_map_sample, sample_grype_report):
        """Test creating unified report from Grype data."""
        reports = [sample_grype_report]
        report = create_unified_report(vuln_map_sample, reports)

        # Verify metadata
        assert "metadata" in report
        assert report["metadata"]["scanner"] == "grype"
        assert report["metadata"]["scanner_version"] == "0.100.0"
        assert report["metadata"]["source_reports_count"] == 1
        assert "test-report.json" in report["metadata"]["source_reports"]

        # Verify summary
        assert "summary" in report
        assert report["summary"]["total_vulnerability_occurrences"] == 3  # 2 + 1
        assert report["summary"]["unique_vulnerabilities"] == 2

        # Verify severity breakdown
        assert "by_severity" in report["summary"]
        severity = report["summary"]["by_severity"]
        assert severity["High"] == 2
        assert severity["Critical"] == 1
        assert severity["Medium"] == 0
        assert severity["Low"] == 0

        # Verify vulnerabilities
        assert "vulnerabilities" in report
        assert len(report["vulnerabilities"]) == 2

        # Verify sorting (by count, descending)
        assert report["vulnerabilities"][0]["count"] >= report["vulnerabilities"][1]["count"]

        # Verify database info
        assert "database_info" in report
        assert report["database_info"]["built"] == "2024-01-01T00:00:00Z"
        assert report["database_info"]["schemaVersion"] == 5

    def test_create_report_with_trivy_data(self, vuln_map_sample, sample_trivy_report):
        """Test creating unified report from Trivy data."""
        reports = [sample_trivy_report]
        report = create_unified_report(vuln_map_sample, reports)

        # Verify metadata
        assert report["metadata"]["scanner"] == "trivy"
        assert report["metadata"]["scanner_version"] == "2.0.0"

        # Verify scanned images for Trivy format
        assert len(report["summary"]["scanned_images"]) == 1
        scanned = report["summary"]["scanned_images"][0]
        assert scanned["file"] == "test-trivy-report.json"
        assert scanned["image"] == "nginx:1.21"
        assert scanned["matches"] == 1

        # Verify database info for Trivy
        assert report["database_info"]["schema_version"] == "2.0.0"
        assert report["database_info"]["created_at"] == "2024-01-01T00:00:00Z"

    def test_create_report_empty_reports(self, vuln_map_sample):
        """Test creating report with empty reports list."""
        report = create_unified_report(vuln_map_sample, [])

        assert report["metadata"]["source_reports_count"] == 0
        assert report["metadata"]["scanner"] == "grype"  # Default
        assert report["summary"]["scanned_images"] == []

    def test_create_report_severity_normalization(self, sample_grype_report):
        """Test that severity values are normalized (title case)."""
        vuln_map = {
            "CVE-2024-11111": {
                "count": 1,
                "selected_scanner": "grype",
                "vulnerability_data": {
                    "id": "CVE-2024-11111",
                    "severity": "high",  # Lowercase
                },
                "related_vulnerabilities": [],
                "affected_sources": [],
                "match_details": [],
            },
            "CVE-2024-22222": {
                "count": 1,
                "selected_scanner": "grype",
                "vulnerability_data": {
                    "id": "CVE-2024-22222",
                    "severity": "CRITICAL",  # Uppercase
                },
                "related_vulnerabilities": [],
                "affected_sources": [],
                "match_details": [],
            },
        }

        reports = [sample_grype_report]
        report = create_unified_report(vuln_map, reports)

        # Both should be normalized to title case
        severity = report["summary"]["by_severity"]
        assert severity["High"] == 1
        assert severity["Critical"] == 1

    def test_create_report_unknown_severity(self, sample_grype_report):
        """Test handling vulnerabilities with unknown/missing severity."""
        vuln_map = {
            "CVE-2024-33333": {
                "count": 1,
                "selected_scanner": "grype",
                "vulnerability_data": {
                    "id": "CVE-2024-33333",
                    # No severity field
                },
                "related_vulnerabilities": [],
                "affected_sources": [],
                "match_details": [],
            }
        }

        reports = [sample_grype_report]
        report = create_unified_report(vuln_map, reports)

        assert report["summary"]["by_severity"]["Unknown"] == 1

    def test_create_report_multiple_images(self, sample_grype_report):
        """Test report with multiple scanned images."""
        report1 = copy.deepcopy(sample_grype_report)
        report1["_source_file"] = "image1.json"
        report1["source"]["target"]["userInput"] = "nginx:1.21"

        report2 = copy.deepcopy(sample_grype_report)
        report2["_source_file"] = "image2.json"
        report2["source"]["target"]["userInput"] = "alpine:3.18"
        report2["matches"] = []  # No matches in second image

        vuln_map = {
            "CVE-2024-12345": {
                "count": 1,
                "selected_scanner": "grype",
                "vulnerability_data": {"id": "CVE-2024-12345", "severity": "High"},
                "related_vulnerabilities": [],
                "affected_sources": [],
                "match_details": [],
            }
        }

        reports = [report1, report2]
        report = create_unified_report(vuln_map, reports)

        assert len(report["summary"]["scanned_images"]) == 2
        # Reports are processed in order
        assert report["summary"]["scanned_images"][0]["file"] == "image1.json"
        assert report["summary"]["scanned_images"][0]["image"] == "nginx:1.21"
        assert report["summary"]["scanned_images"][0]["matches"] == 1
        assert report["summary"]["scanned_images"][1]["file"] == "image2.json"
        assert report["summary"]["scanned_images"][1]["image"] == "alpine:3.18"
        assert report["summary"]["scanned_images"][1]["matches"] == 0

    def test_create_report_vulnerability_structure(self, sample_grype_report):
        """Test that vulnerability entries have correct structure."""
        vuln_map = {
            "CVE-2024-12345": {
                "count": 2,
                "selected_scanner": "grype",
                "vulnerability_data": {
                    "id": "CVE-2024-12345",
                    "severity": "High",
                    "description": "Test vuln",
                },
                "related_vulnerabilities": [{"id": "GHSA-xxxx", "namespace": "github"}],
                "affected_sources": [
                    {
                        "source_file": "report1.json",
                        "image": "nginx:1.21",
                        "artifact": {"name": "openssl", "version": "1.1.1k"},
                    }
                ],
                "match_details": [{"type": "exact"}],
            }
        }

        reports = [sample_grype_report]
        report = create_unified_report(vuln_map, reports)

        vuln = report["vulnerabilities"][0]
        assert vuln["vulnerability_id"] == "CVE-2024-12345"
        assert vuln["count"] == 2
        assert vuln["selected_scanner"] == "grype"
        assert "vulnerability" in vuln
        assert "related_vulnerabilities" in vuln
        assert "affected_sources" in vuln
        assert "match_details" in vuln

    def test_create_report_timestamp(self, vuln_map_sample, sample_grype_report):
        """Test that report includes generation timestamp."""
        reports = [sample_grype_report]
        report = create_unified_report(vuln_map_sample, reports)

        assert "generated_at" in report["metadata"]
        # Should be ISO format timestamp
        assert "T" in report["metadata"]["generated_at"]

    def test_create_report_with_package_info(self, vuln_map_sample, sample_grype_report):
        """Test that package name and version are included in metadata when provided."""
        reports = [sample_grype_report]
        report = create_unified_report(
            vuln_map_sample, reports, package_name="gitlab", package_version="18.4.2-uds.0-unicorn"
        )

        assert "package_name" in report["metadata"]
        assert report["metadata"]["package_name"] == "gitlab"
        assert "package_version" in report["metadata"]
        assert report["metadata"]["package_version"] == "18.4.2-uds.0-unicorn"

    def test_create_report_without_package_info(self, vuln_map_sample, sample_grype_report):
        """Test that package metadata fields are absent when not provided."""
        reports = [sample_grype_report]
        report = create_unified_report(vuln_map_sample, reports)

        assert "package_name" not in report["metadata"]
        assert "package_version" not in report["metadata"]

    def test_create_report_with_trivy_multiple_results(self):
        """Test Trivy report with multiple result types."""
        trivy_report = {
            "_source_file": "multi-result.json",
            "_scanner": "trivy",
            "ArtifactName": "myapp:latest",
            "SchemaVersion": "2.0.0",
            "CreatedAt": "2024-01-01T00:00:00Z",
            "Results": [
                {
                    "Type": "deb",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2024-11111",
                            "Severity": "HIGH",
                        }
                    ],
                },
                {
                    "Type": "npm",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2024-22222",
                            "Severity": "MEDIUM",
                        }
                    ],
                },
            ],
        }

        vuln_map = {
            "CVE-2024-11111": {
                "count": 1,
                "selected_scanner": "trivy",
                "vulnerability_data": {"id": "CVE-2024-11111", "severity": "High"},
                "related_vulnerabilities": [],
                "affected_sources": [],
                "match_details": [],
            },
            "CVE-2024-22222": {
                "count": 1,
                "selected_scanner": "trivy",
                "vulnerability_data": {"id": "CVE-2024-22222", "severity": "Medium"},
                "related_vulnerabilities": [],
                "affected_sources": [],
                "match_details": [],
            },
        }

        reports = [trivy_report]
        report = create_unified_report(vuln_map, reports)

        # Should count vulnerabilities from all result types
        scanned = report["summary"]["scanned_images"][0]
        assert scanned["matches"] == 2


class TestCreateExecutiveSummary:
    """Tests for create_executive_summary function."""

    def test_executive_summary_basic_structure(self, vuln_map_sample, sample_grype_report):
        """Test that executive summary has the correct basic structure."""
        reports = [sample_grype_report]
        summary = create_executive_summary(vuln_map_sample, reports)

        # Verify top-level structure
        assert "report_metadata" in summary
        assert "risk_assessment" in summary
        assert "key_metrics" in summary
        assert "top_critical_vulnerabilities" in summary
        assert "most_affected_components" in summary
        assert "recommendations" in summary

        # Verify report metadata
        assert summary["report_metadata"]["report_type"] == "Executive Summary"
        assert summary["report_metadata"]["scanner"] == "grype"
        assert "generated_at" in summary["report_metadata"]

    def test_executive_summary_severity_by_scanner(self, sample_grype_report):
        """Test that executive summary includes severity breakdown by scanner."""
        # Create a vulnerability map with different scanner sources
        vuln_map = {
            "CVE-2024-11111": {
                "count": 2,
                "selected_scanner": "grype",
                "scanner_sources": ["grype"],
                "vulnerability_data": {
                    "id": "CVE-2024-11111",
                    "severity": "High",
                    "description": "Test vulnerability from grype",
                },
                "related_vulnerabilities": [],
                "affected_sources": [],
                "match_details": [],
            },
            "CVE-2024-22222": {
                "count": 1,
                "selected_scanner": "trivy",
                "scanner_sources": ["trivy"],
                "vulnerability_data": {
                    "id": "CVE-2024-22222",
                    "severity": "Medium",
                    "description": "Test vulnerability from trivy",
                },
                "related_vulnerabilities": [],
                "affected_sources": [],
                "match_details": [],
            },
            "CVE-2024-33333": {
                "count": 1,
                "selected_scanner": "grype",
                "scanner_sources": ["grype", "trivy"],  # Found by both scanners
                "vulnerability_data": {
                    "id": "CVE-2024-33333",
                    "severity": "Critical",
                    "description": "Test vulnerability found by both scanners",
                },
                "related_vulnerabilities": [],
                "affected_sources": [],
                "match_details": [],
            },
        }

        reports = [sample_grype_report]
        summary = create_executive_summary(vuln_map, reports)

        # Verify key_metrics has the new field
        assert "vulnerabilities_by_severity_by_scanner" in summary["key_metrics"]

        severity_by_scanner = summary["key_metrics"]["vulnerabilities_by_severity_by_scanner"]

        # Verify grype scanner breakdown
        assert "grype" in severity_by_scanner
        assert severity_by_scanner["grype"]["High"] == 1  # CVE-2024-11111
        assert severity_by_scanner["grype"]["Medium"] == 0
        assert severity_by_scanner["grype"]["Critical"] == 1  # CVE-2024-33333
        assert severity_by_scanner["grype"]["Low"] == 0
        assert severity_by_scanner["grype"]["Negligible"] == 0
        assert severity_by_scanner["grype"]["Unknown"] == 0

        # Verify trivy scanner breakdown
        assert "trivy" in severity_by_scanner
        assert severity_by_scanner["trivy"]["High"] == 0
        assert severity_by_scanner["trivy"]["Medium"] == 1  # CVE-2024-22222
        assert severity_by_scanner["trivy"]["Critical"] == 1  # CVE-2024-33333 (found by both)
        assert severity_by_scanner["trivy"]["Low"] == 0
        assert severity_by_scanner["trivy"]["Negligible"] == 0
        assert severity_by_scanner["trivy"]["Unknown"] == 0

    def test_executive_summary_severity_by_scanner_single_scanner(self, sample_grype_report):
        """Test severity breakdown when all vulnerabilities are from a single scanner."""
        vuln_map = {
            "CVE-2024-11111": {
                "count": 1,
                "selected_scanner": "grype",
                "scanner_sources": ["grype"],
                "vulnerability_data": {
                    "id": "CVE-2024-11111",
                    "severity": "High",
                },
                "related_vulnerabilities": [],
                "affected_sources": [],
                "match_details": [],
            },
            "CVE-2024-22222": {
                "count": 1,
                "selected_scanner": "grype",
                "scanner_sources": ["grype"],
                "vulnerability_data": {
                    "id": "CVE-2024-22222",
                    "severity": "Medium",
                },
                "related_vulnerabilities": [],
                "affected_sources": [],
                "match_details": [],
            },
        }

        reports = [sample_grype_report]
        summary = create_executive_summary(vuln_map, reports)

        severity_by_scanner = summary["key_metrics"]["vulnerabilities_by_severity_by_scanner"]

        # Should only have grype
        assert "grype" in severity_by_scanner
        assert "trivy" not in severity_by_scanner

        # Verify counts
        assert severity_by_scanner["grype"]["High"] == 1
        assert severity_by_scanner["grype"]["Medium"] == 1
        assert severity_by_scanner["grype"]["Critical"] == 0

    def test_executive_summary_severity_by_scanner_backward_compatibility(self, sample_grype_report):
        """Test that summary works with old data that doesn't have scanner_sources field."""
        vuln_map = {
            "CVE-2024-11111": {
                "count": 1,
                "selected_scanner": "grype",
                # No scanner_sources field - should default to selected_scanner
                "vulnerability_data": {
                    "id": "CVE-2024-11111",
                    "severity": "High",
                },
                "related_vulnerabilities": [],
                "affected_sources": [],
                "match_details": [],
            },
        }

        reports = [sample_grype_report]
        summary = create_executive_summary(vuln_map, reports)

        severity_by_scanner = summary["key_metrics"]["vulnerabilities_by_severity_by_scanner"]

        # Should still work and use selected_scanner as default
        assert "grype" in severity_by_scanner
        assert severity_by_scanner["grype"]["High"] == 1

    def test_executive_summary_severity_normalization_by_scanner(self, sample_grype_report):
        """Test that severity values are normalized in scanner breakdown."""
        vuln_map = {
            "CVE-2024-11111": {
                "count": 1,
                "selected_scanner": "grype",
                "scanner_sources": ["grype"],
                "vulnerability_data": {
                    "id": "CVE-2024-11111",
                    "severity": "high",  # Lowercase
                },
                "related_vulnerabilities": [],
                "affected_sources": [],
                "match_details": [],
            },
            "CVE-2024-22222": {
                "count": 1,
                "selected_scanner": "trivy",
                "scanner_sources": ["trivy"],
                "vulnerability_data": {
                    "id": "CVE-2024-22222",
                    "severity": "CRITICAL",  # Uppercase
                },
                "related_vulnerabilities": [],
                "affected_sources": [],
                "match_details": [],
            },
        }

        reports = [sample_grype_report]
        summary = create_executive_summary(vuln_map, reports)

        severity_by_scanner = summary["key_metrics"]["vulnerabilities_by_severity_by_scanner"]

        # Both should be normalized to title case
        assert severity_by_scanner["grype"]["High"] == 1
        assert severity_by_scanner["trivy"]["Critical"] == 1
