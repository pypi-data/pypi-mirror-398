"""Tests for severity and CVSS scoring utilities."""

from cve_report_aggregator.processing.severity import (
    extract_cvss3_scores,
    filter_null_cvss_scores,
    get_highest_cvss3_score,
    get_severity_rank,
    select_highest_severity,
)


def test_get_severity_rank():
    """Test severity ranking."""
    assert get_severity_rank("Critical") == 5
    assert get_severity_rank("High") == 4
    assert get_severity_rank("Medium") == 3
    assert get_severity_rank("Low") == 2
    assert get_severity_rank("Negligible") == 1
    assert get_severity_rank("Unknown") == 0

    # Test case insensitivity
    assert get_severity_rank("critical") == 5
    assert get_severity_rank("CRITICAL") == 5


def test_extract_cvss3_scores_grype_format():
    """Test CVSS 3.x score extraction from Grype format."""
    vuln_data = {
        "cvss": [
            {"version": "3.1", "metrics": {"baseScore": 7.5}},
            {"version": "2.0", "metrics": {"baseScore": 6.0}},
            {"version": "3.0", "metrics": {"baseScore": 8.2}},
        ]
    }

    scores = extract_cvss3_scores(vuln_data)
    assert len(scores) == 2
    assert 7.5 in scores
    assert 8.2 in scores
    assert 6.0 not in scores  # v2 should be filtered out


def test_extract_cvss3_scores_trivy_format():
    """Test CVSS 3.x score extraction from Trivy format."""
    vuln_data = {
        "cvss": {
            "nvd": {"V3Score": 7.5, "V2Score": 6.0},
            "redhat": {"V3Score": 8.2},
        }
    }

    scores = extract_cvss3_scores(vuln_data)
    assert len(scores) == 2
    assert 7.5 in scores
    assert 8.2 in scores


def test_get_highest_cvss3_score():
    """Test getting highest CVSS 3.x score."""
    vuln_data = {
        "cvss": [
            {"version": "3.1", "metrics": {"baseScore": 7.5}},
            {"version": "3.0", "metrics": {"baseScore": 8.2}},
        ]
    }

    score = get_highest_cvss3_score(vuln_data)
    assert score == 8.2

    # Test with no scores
    empty_data = {"cvss": []}
    assert get_highest_cvss3_score(empty_data) is None


def test_filter_null_cvss_scores_grype():
    """Test filtering null CVSS scores from Grype format."""
    vuln_data = {
        "cvss": [
            {"version": "3.1", "metrics": {"baseScore": 7.5}},
            {"version": "3.1", "metrics": {"baseScore": None}},
            {"version": "3.1", "metrics": {"baseScore": 0}},
        ]
    }

    filtered = filter_null_cvss_scores(vuln_data)
    assert len(filtered["cvss"]) == 1
    assert filtered["cvss"][0]["metrics"]["baseScore"] == 7.5


def test_filter_null_cvss_scores_trivy():
    """Test filtering null CVSS scores from Trivy format."""
    vuln_data = {
        "cvss": {
            "nvd": {"V3Score": 7.5},
            "redhat": {"V3Score": None},
            "ubuntu": {"V3Score": 0},
        }
    }

    filtered = filter_null_cvss_scores(vuln_data)
    assert len(filtered["cvss"]) == 1
    assert "nvd" in filtered["cvss"]
    assert filtered["cvss"]["nvd"]["V3Score"] == 7.5


def test_select_highest_severity_by_cvss():
    """Test selecting highest severity based on CVSS scores."""
    current = {
        "severity": "High",
        "cvss": [{"version": "3.1", "metrics": {"baseScore": 7.5}}],
    }

    new = {
        "severity": "Medium",
        "cvss": [{"version": "3.1", "metrics": {"baseScore": 8.2}}],
    }

    # Should select new data despite lower severity string
    selected = select_highest_severity(current, new)
    assert selected == new


def test_select_highest_severity_by_string():
    """Test selecting highest severity when no CVSS scores available."""
    current = {"severity": "Medium", "cvss": []}
    new = {"severity": "High", "cvss": []}

    selected = select_highest_severity(current, new)
    assert selected == new
    assert selected["severity"] == "High"


def test_select_highest_severity_with_none():
    """Test selecting highest severity when current is None."""
    new = {"severity": "High", "cvss": []}

    selected = select_highest_severity(None, new)
    assert selected == new
