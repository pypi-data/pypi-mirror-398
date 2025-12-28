"""Tests for vulnerability deduplication logic."""

import copy

from cve_report_aggregator.processing.aggregator import deduplicate_vulnerabilities


def test_deduplicate_grype_reports(sample_grype_report):
    """Test deduplication of Grype reports."""
    reports = [sample_grype_report]

    vuln_map = deduplicate_vulnerabilities(reports, mode="first-occurrence")

    assert len(vuln_map) == 1
    assert "CVE-2024-12345" in vuln_map

    entry = vuln_map["CVE-2024-12345"]
    assert entry["count"] == 1
    assert entry["selected_scanner"] == "grype"
    assert entry["vulnerability_data"]["severity"] == "High"
    assert len(entry["affected_sources"]) == 1


def test_deduplicate_trivy_reports(sample_trivy_report):
    """Test deduplication of Trivy reports."""
    reports = [sample_trivy_report]

    vuln_map = deduplicate_vulnerabilities(reports, mode="first-occurrence")

    assert len(vuln_map) == 1
    assert "CVE-2024-12345" in vuln_map

    entry = vuln_map["CVE-2024-12345"]
    assert entry["count"] == 1
    assert entry["selected_scanner"] == "trivy"
    assert len(entry["affected_sources"]) == 1


def test_deduplicate_trivy_with_fixed_version(sample_trivy_report_with_fix):
    """Test deduplication of Trivy reports with fixed versions."""
    reports = [sample_trivy_report_with_fix]

    vuln_map = deduplicate_vulnerabilities(reports, mode="first-occurrence")

    assert len(vuln_map) == 1
    assert "CVE-2024-54321" in vuln_map

    entry = vuln_map["CVE-2024-54321"]
    assert entry["vulnerability_data"]["fix"]["versions"] == ["3.0.9-r0"]
    assert entry["vulnerability_data"]["fix"]["state"] == "fixed"


def test_deduplicate_multiple_occurrences(sample_grype_report):
    """Test deduplication with multiple occurrences of same CVE."""
    # Create two reports with same vulnerability
    report1 = copy.deepcopy(sample_grype_report)
    report1["_source_file"] = "report1.json"

    report2 = copy.deepcopy(sample_grype_report)
    report2["_source_file"] = "report2.json"

    reports = [report1, report2]

    vuln_map = deduplicate_vulnerabilities(reports, mode="first-occurrence")

    assert len(vuln_map) == 1
    entry = vuln_map["CVE-2024-12345"]
    assert entry["count"] == 2
    assert len(entry["affected_sources"]) == 2


def test_highest_score_mode(sample_grype_report):
    """Test highest-score mode selects vulnerability with highest CVSS."""
    # Create two reports with different CVSS scores
    report1 = copy.deepcopy(sample_grype_report)
    report1["matches"][0]["vulnerability"]["cvss"] = [{"version": "3.1", "metrics": {"baseScore": 7.5}}]

    report2 = copy.deepcopy(sample_grype_report)
    report2["_source_file"] = "report2.json"
    report2["matches"][0]["vulnerability"]["cvss"] = [{"version": "3.1", "metrics": {"baseScore": 8.9}}]

    reports = [report1, report2]

    vuln_map = deduplicate_vulnerabilities(reports, mode="highest-score")

    entry = vuln_map["CVE-2024-12345"]
    # Should select the one with 8.9 score
    cvss_score = entry["vulnerability_data"]["cvss"][0]["metrics"]["baseScore"]
    assert cvss_score == 8.9


def test_deduplicate_ghsa_to_cve_mapping(sample_grype_report_with_ghsa):
    """Test that GHSA IDs are mapped to CVE IDs when available."""
    reports = [sample_grype_report_with_ghsa]

    vuln_map = deduplicate_vulnerabilities(reports, mode="first-occurrence")

    # Should use CVE ID as primary key, not GHSA
    assert "CVE-2024-99999" in vuln_map
    assert "GHSA-xxxx-yyyy-zzzz" not in vuln_map

    entry = vuln_map["CVE-2024-99999"]
    assert entry["count"] == 1
    # Related vulnerabilities should include the GHSA
    assert len(entry["related_vulnerabilities"]) == 1
    assert entry["related_vulnerabilities"][0]["id"] == "CVE-2024-99999"


def test_deduplicate_empty_vulnerability_id(sample_grype_report):
    """Test handling of vulnerabilities with empty IDs."""
    report = copy.deepcopy(sample_grype_report)
    # Add a match with empty vulnerability ID (Trivy format)
    report["_scanner"] = "trivy"
    report["ArtifactName"] = "test:latest"
    report["Results"] = [
        {
            "Type": "deb",
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "",  # Empty ID
                    "PkgName": "test",
                    "Severity": "High",
                }
            ],
        }
    ]

    reports = [report]
    vuln_map = deduplicate_vulnerabilities(reports, mode="first-occurrence")

    # Empty ID should be skipped
    assert "" not in vuln_map
    assert len(vuln_map) == 0


def test_deduplicate_match_details_aggregation(sample_grype_report):
    """Test that match details are aggregated and deduplicated."""
    report1 = copy.deepcopy(sample_grype_report)
    report1["matches"][0]["matchDetails"] = [{"type": "exact-direct-match"}, {"type": "fuzzy-match"}]

    report2 = copy.deepcopy(sample_grype_report)
    report2["_source_file"] = "report2.json"
    report2["matches"][0]["matchDetails"] = [
        {"type": "exact-direct-match"},  # Duplicate
        {"type": "cpe-match"},  # New
    ]

    reports = [report1, report2]
    vuln_map = deduplicate_vulnerabilities(reports, mode="first-occurrence")

    entry = vuln_map["CVE-2024-12345"]
    # Should have unique match details (exact-direct-match appears once despite being in both)
    match_types = {detail["type"] for detail in entry["match_details"]}
    assert "exact-direct-match" in match_types
    assert "fuzzy-match" in match_types
    assert "cpe-match" in match_types


def test_deduplicate_artifact_tracking(sample_grype_report):
    """Test that artifact information is tracked correctly."""
    reports = [sample_grype_report]
    vuln_map = deduplicate_vulnerabilities(reports, mode="first-occurrence")

    entry = vuln_map["CVE-2024-12345"]
    source = entry["affected_sources"][0]

    assert source["source_file"] == "test-report.json"
    assert source["image"] == "nginx:1.21"
    assert source["artifact"]["name"] == "openssl"
    assert source["artifact"]["version"] == "1.1.1k"
    assert source["artifact"]["type"] == "deb"
    assert source["artifact"]["location"] == "/usr/lib/libssl.so"


def test_deduplicate_artifact_no_location(sample_trivy_report):
    """Test handling artifacts without location information."""
    # Modify Trivy report to have no PkgPath
    report = copy.deepcopy(sample_trivy_report)
    report["Results"][0]["Vulnerabilities"][0].pop("PkgPath", None)

    reports = [report]
    vuln_map = deduplicate_vulnerabilities(reports, mode="first-occurrence")

    entry = vuln_map["CVE-2024-12345"]
    source = entry["affected_sources"][0]

    assert source["artifact"]["location"] is None


def test_deduplicate_mixed_scanners(sample_grype_report, sample_trivy_report):
    """Test deduplication across mixed Grype and Trivy reports."""
    # Both reports have the same CVE
    reports = [sample_grype_report, sample_trivy_report]

    vuln_map = deduplicate_vulnerabilities(reports, mode="first-occurrence")

    # Should deduplicate to single CVE
    assert len(vuln_map) == 1
    assert "CVE-2024-12345" in vuln_map

    entry = vuln_map["CVE-2024-12345"]
    assert entry["count"] == 2
    assert len(entry["affected_sources"]) == 2

    # First occurrence should be from Grype (alphabetically first)
    assert entry["selected_scanner"] == "grype"


def test_deduplicate_mixed_scanners_highest_score(sample_grype_report, sample_trivy_report_with_fix):
    """Test highest-score mode across mixed scanners."""
    # Grype report has CVSS 7.5, Trivy has CVSS 9.8
    reports = [sample_grype_report, sample_trivy_report_with_fix]

    vuln_map = deduplicate_vulnerabilities(reports, mode="highest-score")

    # Should have two separate CVEs
    assert len(vuln_map) == 2
    assert "CVE-2024-12345" in vuln_map
    assert "CVE-2024-54321" in vuln_map


def test_deduplicate_highest_score_updates_related_vulns(sample_grype_report_with_ghsa):
    """Test that related vulnerabilities are updated when selecting highest score."""
    report1 = copy.deepcopy(sample_grype_report_with_ghsa)
    report1["matches"][0]["vulnerability"]["cvss"] = [{"version": "3.1", "metrics": {"baseScore": 6.5}}]
    report1["matches"][0]["relatedVulnerabilities"] = [{"id": "CVE-2024-99999", "namespace": "nvd"}]

    report2 = copy.deepcopy(sample_grype_report_with_ghsa)
    report2["_source_file"] = "report2.json"
    report2["matches"][0]["vulnerability"]["cvss"] = [{"version": "3.1", "metrics": {"baseScore": 8.0}}]
    report2["matches"][0]["relatedVulnerabilities"] = [
        {"id": "CVE-2024-99999", "namespace": "nvd"},
        {"id": "GHSA-yyyy", "namespace": "github"},
    ]

    reports = [report1, report2]
    vuln_map = deduplicate_vulnerabilities(reports, mode="highest-score")

    entry = vuln_map["CVE-2024-99999"]
    # Should use related vulnerabilities from the higher score entry
    assert len(entry["related_vulnerabilities"]) == 2


def test_deduplicate_trivy_missing_vulnerability_id():
    """Test handling Trivy results with missing vulnerability data."""
    report = {
        "_source_file": "test.json",
        "_scanner": "trivy",
        "ArtifactName": "test:latest",
        "Results": [
            {
                "Type": "deb",
                "Vulnerabilities": [
                    {
                        # Missing VulnerabilityID
                        "PkgName": "test",
                        "Severity": "High",
                    }
                ],
            }
        ],
    }

    reports = [report]
    vuln_map = deduplicate_vulnerabilities(reports, mode="first-occurrence")

    # Should skip vulnerabilities without IDs
    assert len(vuln_map) == 0


def test_deduplicate_grype_no_related_cves(sample_grype_report):
    """Test Grype reports with no CVE in related vulnerabilities."""
    report = copy.deepcopy(sample_grype_report)
    # Use GHSA ID with only other GHSA IDs in related vulnerabilities
    report["matches"][0]["vulnerability"]["id"] = "GHSA-main"
    report["matches"][0]["relatedVulnerabilities"] = [
        {"id": "GHSA-related-1", "namespace": "github"},
        {"id": "GHSA-related-2", "namespace": "github"},
    ]

    reports = [report]
    vuln_map = deduplicate_vulnerabilities(reports, mode="first-occurrence")

    # Should use GHSA as primary key since no CVE available
    assert "GHSA-main" in vuln_map
    assert "CVE" not in list(vuln_map.keys())[0]


def test_deduplicate_null_cvss_filtering(sample_grype_report):
    """Test that null CVSS scores are filtered out."""
    report = copy.deepcopy(sample_grype_report)
    report["matches"][0]["vulnerability"]["cvss"] = [
        {"version": "3.1", "metrics": {"baseScore": None}},
        {"version": "3.1", "metrics": {"baseScore": 0}},
        {"version": "3.1", "metrics": {"baseScore": 7.5}},
    ]

    reports = [report]
    vuln_map = deduplicate_vulnerabilities(reports, mode="first-occurrence")

    entry = vuln_map["CVE-2024-12345"]
    # Should only have the valid score
    assert len(entry["vulnerability_data"]["cvss"]) == 1
    assert entry["vulnerability_data"]["cvss"][0]["metrics"]["baseScore"] == 7.5


def test_deduplicate_grype_with_string_source(sample_grype_report):
    """Test handling of Grype reports where source is a string instead of dict."""
    report = copy.deepcopy(sample_grype_report)
    # Simulate newer Grype format where source is a simple string
    report["source"] = "nginx:1.21"

    reports = [report]
    vuln_map = deduplicate_vulnerabilities(reports, mode="first-occurrence")

    entry = vuln_map["CVE-2024-12345"]
    # Should extract image name from string source
    assert entry["affected_sources"][0]["image"] == "nginx:1.21"


def test_deduplicate_grype_with_missing_source(sample_grype_report):
    """Test handling of Grype reports with missing source field."""
    report = copy.deepcopy(sample_grype_report)
    # Remove source field entirely
    del report["source"]

    reports = [report]
    vuln_map = deduplicate_vulnerabilities(reports, mode="first-occurrence")

    entry = vuln_map["CVE-2024-12345"]
    # Should use "unknown" as fallback
    assert entry["affected_sources"][0]["image"] == "unknown"


def test_deduplicate_grype_with_string_target(sample_grype_report):
    """Test handling of Grype reports where target is a string instead of dict."""
    report = copy.deepcopy(sample_grype_report)
    # Simulate format where source.target is a string
    report["source"] = {"target": "alpine:3.18"}

    reports = [report]
    vuln_map = deduplicate_vulnerabilities(reports, mode="first-occurrence")

    entry = vuln_map["CVE-2024-12345"]
    # Should extract image name from string target
    assert entry["affected_sources"][0]["image"] == "alpine:3.18"


def test_deduplicate_grype_with_none_source(sample_grype_report):
    """Test handling of Grype reports where source is explicitly None."""
    report = copy.deepcopy(sample_grype_report)
    # Simulate format where source is None
    report["source"] = None

    reports = [report]
    vuln_map = deduplicate_vulnerabilities(reports, mode="first-occurrence")

    entry = vuln_map["CVE-2024-12345"]
    # Should use "unknown" as fallback
    assert entry["affected_sources"][0]["image"] == "unknown"


def test_deduplicate_grype_with_empty_target(sample_grype_report):
    """Test handling of Grype reports where target is missing from source dict."""
    report = copy.deepcopy(sample_grype_report)
    # Simulate format where source dict exists but target is missing
    report["source"] = {"metadata": "some data"}

    reports = [report]
    vuln_map = deduplicate_vulnerabilities(reports, mode="first-occurrence")

    entry = vuln_map["CVE-2024-12345"]
    # Should use "unknown" as fallback
    assert entry["affected_sources"][0]["image"] == "unknown"


def test_extract_image_name_with_target_userinput():
    """Test extracting image name from source.target.userInput format."""
    from cve_report_aggregator.processing.aggregator import extract_image_name

    report = {"source": {"target": {"userInput": "nginx:1.21"}}}
    assert extract_image_name(report) == "nginx:1.21"


def test_extract_image_name_with_metadata_userinput():
    """Test extracting image name from source.metadata.userInput format (SBOM scans)."""
    from cve_report_aggregator.processing.aggregator import extract_image_name

    report = {
        "source": {"metadata": {"userInput": "quay.io/rfcurated/gitlab/gitlab-sidekiq-ee:18.4.2-jammy-fips-rfcurated"}}
    }
    assert extract_image_name(report) == "quay.io/rfcurated/gitlab/gitlab-sidekiq-ee:18.4.2-jammy-fips-rfcurated"


def test_extract_image_name_with_source_name():
    """Test extracting image name from source.name + version format."""
    from cve_report_aggregator.processing.aggregator import extract_image_name

    report = {"source": {"name": "myimage", "version": "v1.0.0"}}
    assert extract_image_name(report) == "myimage:v1.0.0"


def test_extract_image_name_with_source_name_only():
    """Test extracting image name from source.name without version."""
    from cve_report_aggregator.processing.aggregator import extract_image_name

    report = {"source": {"name": "myimage"}}
    assert extract_image_name(report) == "myimage"


def test_extract_image_name_with_string_source():
    """Test extracting image name from string source."""
    from cve_report_aggregator.processing.aggregator import extract_image_name

    report = {"source": "alpine:3.18"}
    assert extract_image_name(report) == "alpine:3.18"


def test_extract_image_name_with_string_target():
    """Test extracting image name from source.target as string."""
    from cve_report_aggregator.processing.aggregator import extract_image_name

    report = {"source": {"target": "debian:11"}}
    assert extract_image_name(report) == "debian:11"


def test_extract_image_name_with_missing_source():
    """Test extracting image name when source is missing."""
    from cve_report_aggregator.processing.aggregator import extract_image_name

    report = {}
    assert extract_image_name(report) == "unknown"


def test_extract_image_name_with_none_source():
    """Test extracting image name when source is None."""
    from cve_report_aggregator.processing.aggregator import extract_image_name

    report = {"source": None}
    assert extract_image_name(report) == "unknown"


def test_extract_image_name_priority_metadata_over_target():
    """Test that metadata.userInput takes priority over target.userInput."""
    from cve_report_aggregator.processing.aggregator import extract_image_name

    report = {
        "source": {
            "metadata": {"userInput": "from-metadata:latest"},
            "target": {"userInput": "from-target:latest"},
        }
    }
    assert extract_image_name(report) == "from-metadata:latest"
