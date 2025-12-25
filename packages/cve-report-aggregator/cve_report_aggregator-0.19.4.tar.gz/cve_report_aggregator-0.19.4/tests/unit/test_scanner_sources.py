"""Tests for scanner source tracking functionality.

This module tests that the aggregator correctly tracks which scanners
detected each vulnerability, especially when using the "both" scanner option.
"""

from cve_report_aggregator.io.report import create_unified_report
from cve_report_aggregator.processing.aggregator import deduplicate_vulnerabilities


class TestScannerSourceTracking:
    """Tests for scanner source tracking in vulnerability aggregation."""

    def test_grype_only_scanner_sources(self):
        """Test that Grype-only scans track scanner source correctly."""
        grype_report = {
            "_source_file": "test-grype.json",
            "_scanner": "grype",
            "source": {"target": {"userInput": "nginx:1.21"}},
            "matches": [
                {
                    "vulnerability": {
                        "id": "CVE-2024-12345",
                        "severity": "High",
                        "description": "Test vulnerability",
                        "cvss": [{"version": "3.1", "metrics": {"baseScore": 7.5}}],
                    },
                    "relatedVulnerabilities": [],
                    "matchDetails": [{"type": "exact"}],
                    "artifact": {
                        "name": "openssl",
                        "version": "1.1.1k",
                        "type": "deb",
                        "locations": [{"path": "/usr/lib/libssl.so"}],
                    },
                }
            ],
        }

        vuln_map = deduplicate_vulnerabilities([grype_report])

        assert "CVE-2024-12345" in vuln_map
        assert vuln_map["CVE-2024-12345"]["scanner_sources"] == ["grype"]
        assert vuln_map["CVE-2024-12345"]["selected_scanner"] == "grype"

    def test_trivy_only_scanner_sources(self):
        """Test that Trivy-only scans track scanner source correctly."""
        trivy_report = {
            "_source_file": "test-trivy.json",
            "_scanner": "trivy",
            "ArtifactName": "nginx:1.21",
            "Results": [
                {
                    "Type": "deb",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2024-12345",
                            "PkgName": "openssl",
                            "InstalledVersion": "1.1.1k",
                            "Severity": "HIGH",
                            "Description": "Test vulnerability",
                            "CVSS": {"nvd": {"V3Score": 7.5}},
                        }
                    ],
                }
            ],
        }

        vuln_map = deduplicate_vulnerabilities([trivy_report])

        assert "CVE-2024-12345" in vuln_map
        assert vuln_map["CVE-2024-12345"]["scanner_sources"] == ["trivy"]
        assert vuln_map["CVE-2024-12345"]["selected_scanner"] == "trivy"

    def test_both_scanners_same_cve(self):
        """Test that both scanners are tracked when both detect the same CVE."""
        grype_report = {
            "_source_file": "test-grype.json",
            "_scanner": "grype",
            "source": {"target": {"userInput": "nginx:1.21"}},
            "matches": [
                {
                    "vulnerability": {
                        "id": "CVE-2024-12345",
                        "severity": "High",
                        "description": "Test vulnerability",
                        "cvss": [{"version": "3.1", "metrics": {"baseScore": 7.5}}],
                    },
                    "relatedVulnerabilities": [],
                    "matchDetails": [{"type": "exact"}],
                    "artifact": {
                        "name": "openssl",
                        "version": "1.1.1k",
                        "type": "deb",
                        "locations": [{"path": "/usr/lib/libssl.so"}],
                    },
                }
            ],
        }

        trivy_report = {
            "_source_file": "test-trivy.json",
            "_scanner": "trivy",
            "ArtifactName": "nginx:1.21",
            "Results": [
                {
                    "Type": "deb",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2024-12345",
                            "PkgName": "openssl",
                            "InstalledVersion": "1.1.1k",
                            "Severity": "HIGH",
                            "Description": "Test vulnerability",
                            "CVSS": {"nvd": {"V3Score": 7.5}},
                        }
                    ],
                }
            ],
        }

        vuln_map = deduplicate_vulnerabilities([grype_report, trivy_report])

        assert "CVE-2024-12345" in vuln_map
        # Both scanners should be tracked
        assert set(vuln_map["CVE-2024-12345"]["scanner_sources"]) == {"grype", "trivy"}
        # Count should be 2 (one from each scanner)
        assert vuln_map["CVE-2024-12345"]["count"] == 2

    def test_both_scanners_different_cves(self):
        """Test that each scanner is tracked separately for different CVEs."""
        grype_report = {
            "_source_file": "test-grype.json",
            "_scanner": "grype",
            "source": {"target": {"userInput": "nginx:1.21"}},
            "matches": [
                {
                    "vulnerability": {
                        "id": "CVE-2024-11111",
                        "severity": "High",
                        "cvss": [{"version": "3.1", "metrics": {"baseScore": 7.5}}],
                    },
                    "relatedVulnerabilities": [],
                    "matchDetails": [],
                    "artifact": {
                        "name": "openssl",
                        "version": "1.1.1k",
                        "type": "deb",
                        "locations": [],
                    },
                }
            ],
        }

        trivy_report = {
            "_source_file": "test-trivy.json",
            "_scanner": "trivy",
            "ArtifactName": "nginx:1.21",
            "Results": [
                {
                    "Type": "deb",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2024-22222",
                            "PkgName": "libssl",
                            "InstalledVersion": "1.1.1k",
                            "Severity": "CRITICAL",
                            "CVSS": {"nvd": {"V3Score": 9.8}},
                        }
                    ],
                }
            ],
        }

        vuln_map = deduplicate_vulnerabilities([grype_report, trivy_report])

        # Grype-only CVE
        assert "CVE-2024-11111" in vuln_map
        assert vuln_map["CVE-2024-11111"]["scanner_sources"] == ["grype"]

        # Trivy-only CVE
        assert "CVE-2024-22222" in vuln_map
        assert vuln_map["CVE-2024-22222"]["scanner_sources"] == ["trivy"]

    def test_scanner_sources_in_unified_report(self):
        """Test that scanner_sources appears in the final unified report."""
        grype_report = {
            "_source_file": "test-grype.json",
            "_scanner": "grype",
            "source": {"target": {"userInput": "nginx:1.21"}},
            "descriptor": {"version": "0.100.0", "db": {}},
            "matches": [
                {
                    "vulnerability": {
                        "id": "CVE-2024-12345",
                        "severity": "High",
                        "cvss": [{"version": "3.1", "metrics": {"baseScore": 7.5}}],
                    },
                    "relatedVulnerabilities": [],
                    "matchDetails": [],
                    "artifact": {
                        "name": "openssl",
                        "version": "1.1.1k",
                        "type": "deb",
                        "locations": [],
                    },
                }
            ],
        }

        trivy_report = {
            "_source_file": "test-trivy.json",
            "_scanner": "trivy",
            "ArtifactName": "nginx:1.21",
            "SchemaVersion": "2.0.0",
            "CreatedAt": "2024-01-01T00:00:00Z",
            "Results": [
                {
                    "Type": "deb",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2024-12345",
                            "PkgName": "openssl",
                            "InstalledVersion": "1.1.1k",
                            "Severity": "HIGH",
                            "CVSS": {"nvd": {"V3Score": 7.5}},
                        }
                    ],
                }
            ],
        }

        vuln_map = deduplicate_vulnerabilities([grype_report, trivy_report])
        unified_report = create_unified_report(vuln_map, [grype_report, trivy_report])

        # Check that scanner_sources is in the output
        assert "vulnerabilities" in unified_report
        assert len(unified_report["vulnerabilities"]) == 1

        vuln = unified_report["vulnerabilities"][0]
        assert "scanner_sources" in vuln
        assert set(vuln["scanner_sources"]) == {"grype", "trivy"}

    def test_multiple_occurrences_same_scanner(self):
        """Test that scanner source is not duplicated for multiple occurrences."""
        grype_report1 = {
            "_source_file": "test-grype-1.json",
            "_scanner": "grype",
            "source": {"target": {"userInput": "nginx:1.21"}},
            "matches": [
                {
                    "vulnerability": {
                        "id": "CVE-2024-12345",
                        "severity": "High",
                        "cvss": [{"version": "3.1", "metrics": {"baseScore": 7.5}}],
                    },
                    "relatedVulnerabilities": [],
                    "matchDetails": [],
                    "artifact": {
                        "name": "openssl",
                        "version": "1.1.1k",
                        "type": "deb",
                        "locations": [],
                    },
                }
            ],
        }

        grype_report2 = {
            "_source_file": "test-grype-2.json",
            "_scanner": "grype",
            "source": {"target": {"userInput": "alpine:3.18"}},
            "matches": [
                {
                    "vulnerability": {
                        "id": "CVE-2024-12345",
                        "severity": "High",
                        "cvss": [{"version": "3.1", "metrics": {"baseScore": 7.5}}],
                    },
                    "relatedVulnerabilities": [],
                    "matchDetails": [],
                    "artifact": {
                        "name": "openssl",
                        "version": "1.1.1k",
                        "type": "apk",
                        "locations": [],
                    },
                }
            ],
        }

        vuln_map = deduplicate_vulnerabilities([grype_report1, grype_report2])

        assert "CVE-2024-12345" in vuln_map
        # Scanner should only appear once in the list
        assert vuln_map["CVE-2024-12345"]["scanner_sources"] == ["grype"]
        # But count should be 2
        assert vuln_map["CVE-2024-12345"]["count"] == 2

    def test_ghsa_with_cve_scanner_sources(self):
        """Test scanner sources for GHSA IDs that map to CVEs."""
        grype_report = {
            "_source_file": "test-grype.json",
            "_scanner": "grype",
            "source": {"target": {"userInput": "python:3.11"}},
            "matches": [
                {
                    "vulnerability": {
                        "id": "GHSA-xxxx-yyyy-zzzz",
                        "severity": "Medium",
                        "cvss": [{"version": "3.1", "metrics": {"baseScore": 6.5}}],
                    },
                    "relatedVulnerabilities": [
                        {
                            "id": "CVE-2024-99999",
                            "namespace": "nvd:cpe",
                        }
                    ],
                    "matchDetails": [],
                    "artifact": {
                        "name": "requests",
                        "version": "2.28.0",
                        "type": "python",
                        "locations": [],
                    },
                }
            ],
        }

        vuln_map = deduplicate_vulnerabilities([grype_report])

        # Should be keyed by CVE, not GHSA
        assert "CVE-2024-99999" in vuln_map
        assert vuln_map["CVE-2024-99999"]["scanner_sources"] == ["grype"]

    def test_scanner_sources_highest_score_mode(self):
        """Test that scanner sources are tracked correctly in highest-score mode."""
        grype_report = {
            "_source_file": "test-grype.json",
            "_scanner": "grype",
            "source": {"target": {"userInput": "nginx:1.21"}},
            "matches": [
                {
                    "vulnerability": {
                        "id": "CVE-2024-12345",
                        "severity": "High",
                        "cvss": [{"version": "3.1", "metrics": {"baseScore": 7.5}}],
                    },
                    "relatedVulnerabilities": [],
                    "matchDetails": [],
                    "artifact": {
                        "name": "openssl",
                        "version": "1.1.1k",
                        "type": "deb",
                        "locations": [],
                    },
                }
            ],
        }

        trivy_report = {
            "_source_file": "test-trivy.json",
            "_scanner": "trivy",
            "ArtifactName": "nginx:1.21",
            "Results": [
                {
                    "Type": "deb",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2024-12345",
                            "PkgName": "openssl",
                            "InstalledVersion": "1.1.1k",
                            "Severity": "CRITICAL",  # Higher severity
                            "CVSS": {"nvd": {"V3Score": 9.8}},  # Higher score
                        }
                    ],
                }
            ],
        }

        # Use highest-score mode (default)
        vuln_map = deduplicate_vulnerabilities([grype_report, trivy_report], mode="highest-score")

        assert "CVE-2024-12345" in vuln_map
        # Both scanners should be in sources
        assert set(vuln_map["CVE-2024-12345"]["scanner_sources"]) == {"grype", "trivy"}
        # But Trivy should be selected due to higher score
        assert vuln_map["CVE-2024-12345"]["selected_scanner"] == "trivy"
        # Verify the higher severity was selected
        assert vuln_map["CVE-2024-12345"]["vulnerability_data"]["severity"] == "CRITICAL"

    def test_scanner_sources_first_occurrence_mode(self):
        """Test that scanner sources are tracked correctly in first-occurrence mode."""
        grype_report = {
            "_source_file": "test-grype.json",
            "_scanner": "grype",
            "source": {"target": {"userInput": "nginx:1.21"}},
            "matches": [
                {
                    "vulnerability": {
                        "id": "CVE-2024-12345",
                        "severity": "High",
                        "cvss": [{"version": "3.1", "metrics": {"baseScore": 7.5}}],
                    },
                    "relatedVulnerabilities": [],
                    "matchDetails": [],
                    "artifact": {
                        "name": "openssl",
                        "version": "1.1.1k",
                        "type": "deb",
                        "locations": [],
                    },
                }
            ],
        }

        trivy_report = {
            "_source_file": "test-trivy.json",
            "_scanner": "trivy",
            "ArtifactName": "nginx:1.21",
            "Results": [
                {
                    "Type": "deb",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2024-12345",
                            "PkgName": "openssl",
                            "InstalledVersion": "1.1.1k",
                            "Severity": "CRITICAL",
                            "CVSS": {"nvd": {"V3Score": 9.8}},
                        }
                    ],
                }
            ],
        }

        # Use first-occurrence mode
        vuln_map = deduplicate_vulnerabilities([grype_report, trivy_report], mode="first-occurrence")

        assert "CVE-2024-12345" in vuln_map
        # Both scanners should be in sources
        assert set(vuln_map["CVE-2024-12345"]["scanner_sources"]) == {"grype", "trivy"}
        # Grype should be selected (first occurrence)
        assert vuln_map["CVE-2024-12345"]["selected_scanner"] == "grype"
        # Verify the first occurrence data was kept
        assert vuln_map["CVE-2024-12345"]["vulnerability_data"]["severity"] == "High"

    def test_empty_scanner_sources_list(self):
        """Test that scanner_sources is initialized as empty list."""
        from cve_report_aggregator.processing.aggregator import _create_vulnerability_entry

        entry = _create_vulnerability_entry()

        assert "scanner_sources" in entry
        assert entry["scanner_sources"] == []
        assert isinstance(entry["scanner_sources"], list)
