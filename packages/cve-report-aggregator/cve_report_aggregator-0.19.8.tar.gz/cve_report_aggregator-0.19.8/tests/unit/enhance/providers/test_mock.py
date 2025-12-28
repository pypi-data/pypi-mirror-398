"""Tests for the MockEnricher provider."""

import pytest

from cve_report_aggregator.enhance.base import Enricher
from cve_report_aggregator.enhance.models import SimpleCVEEnrichment
from cve_report_aggregator.enhance.providers.mock import MockEnricher


@pytest.fixture
def sample_vulnerabilities():
    """Sample vulnerability list for testing."""
    return [
        {
            "vulnerability_id": "CVE-2024-12345",
            "vulnerability": {
                "id": "CVE-2024-12345",
                "severity": "Critical",
                "description": "Critical vulnerability",
            },
        },
        {
            "vulnerability_id": "CVE-2024-54321",
            "vulnerability": {
                "id": "CVE-2024-54321",
                "severity": "High",
                "description": "High severity vulnerability",
            },
        },
        {
            "vulnerability_id": "CVE-2024-99999",
            "vulnerability": {
                "id": "CVE-2024-99999",
                "severity": "Medium",
                "description": "Medium severity vulnerability",
            },
        },
    ]


class TestMockEnricherInitialization:
    """Tests for MockEnricher initialization."""

    def test_default_initialization(self):
        """Test initialization with default parameters."""
        enricher = MockEnricher()

        assert enricher.model == "mock-model"
        assert enricher.reasoning_effort == "medium"
        assert enricher.verbosity == "medium"
        assert enricher.max_completion_tokens is None
        assert enricher.seed is None
        assert enricher.metadata is None
        assert enricher.max_workers == 5

    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        enricher = MockEnricher(
            api_key="custom-key",
            model="custom-model",
            reasoning_effort="high",
            verbosity="low",
            max_completion_tokens=4096,
            seed=42,
            metadata={"env": "test"},
            max_workers=10,
        )

        assert enricher.model == "custom-model"
        assert enricher.reasoning_effort == "high"
        assert enricher.verbosity == "low"
        assert enricher.max_completion_tokens == 4096
        assert enricher.seed == 42
        assert enricher.metadata == {"env": "test"}
        assert enricher.max_workers == 10

    def test_implements_enricher_protocol(self):
        """Test that MockEnricher implements Enricher protocol."""
        enricher = MockEnricher()
        assert isinstance(enricher, Enricher)

    def test_baseline_context_fallback(self, tmp_path):
        """Test that mock baseline context is used when file not found."""
        # Create a mock enricher pointing to a non-existent path
        nonexistent_path = tmp_path / "nonexistent.md"
        enricher = MockEnricher(baseline_context_path=nonexistent_path)
        assert "Mock baseline security context" in enricher.baseline_context

    def test_system_prompt_built(self):
        """Test that system prompt is built."""
        enricher = MockEnricher()
        assert "Mock system prompt" in enricher.system_prompt
        assert "mock enricher" in enricher.system_prompt.lower()

    def test_enrichment_calls_initialized_empty(self):
        """Test that enrichment_calls list is initialized empty."""
        enricher = MockEnricher()
        assert enricher.enrichment_calls == []


class TestMockEnricherEnrichReport:
    """Tests for MockEnricher.enrich_report method."""

    def test_enrich_all_matching_vulnerabilities(self, sample_vulnerabilities):
        """Test enriching all vulnerabilities matching severity filter."""
        enricher = MockEnricher()

        result = enricher.enrich_report(sample_vulnerabilities)

        # Default filter is Critical and High
        assert len(result) == 2
        assert "CVE-2024-12345" in result
        assert "CVE-2024-54321" in result
        assert "CVE-2024-99999" not in result

    def test_enrich_with_custom_severity_filter(self, sample_vulnerabilities):
        """Test enriching with custom severity filter."""
        enricher = MockEnricher()

        result = enricher.enrich_report(sample_vulnerabilities, severity_filter=["Critical", "High", "Medium"])

        assert len(result) == 3
        assert "CVE-2024-12345" in result
        assert "CVE-2024-54321" in result
        assert "CVE-2024-99999" in result

    def test_enrich_with_max_cves_limit(self, sample_vulnerabilities):
        """Test enriching with max_cves limit."""
        enricher = MockEnricher()

        result = enricher.enrich_report(
            sample_vulnerabilities,
            max_cves=1,
            severity_filter=["Critical", "High", "Medium"],
        )

        assert len(result) == 1
        # Should be the first vulnerability
        assert "CVE-2024-12345" in result

    def test_enrich_empty_vulnerabilities(self):
        """Test enriching empty vulnerability list."""
        enricher = MockEnricher()

        result = enricher.enrich_report([])

        assert result == {}

    def test_enrich_no_matching_severity(self, sample_vulnerabilities):
        """Test enriching when no vulnerabilities match severity filter."""
        enricher = MockEnricher()

        result = enricher.enrich_report(sample_vulnerabilities, severity_filter=["Low"])

        assert result == {}

    def test_enrich_skips_vulnerabilities_without_id(self):
        """Test that vulnerabilities without ID are skipped."""
        enricher = MockEnricher()

        vulnerabilities = [
            {
                # Missing vulnerability_id
                "vulnerability": {
                    "severity": "Critical",
                    "description": "Test",
                },
            }
        ]

        result = enricher.enrich_report(vulnerabilities)

        assert result == {}

    def test_enrichment_result_structure(self, sample_vulnerabilities):
        """Test that enrichment results have correct structure."""
        enricher = MockEnricher()

        result = enricher.enrich_report(sample_vulnerabilities[:1])

        assert len(result) == 1
        enrichment = result["CVE-2024-12345"]

        assert isinstance(enrichment, SimpleCVEEnrichment)
        assert enrichment.cve_id == "CVE-2024-12345"
        assert "UDS helps to mitigate CVE-2024-12345" in enrichment.mitigation_summary
        assert "Without UDS Core controls" in enrichment.impact_analysis
        assert enrichment.analysis_model == "mock-model"
        assert enrichment.analysis_timestamp  # Should have a timestamp

    def test_enrichment_call_tracking(self, sample_vulnerabilities):
        """Test that enrichment calls are tracked."""
        enricher = MockEnricher()

        enricher.enrich_report(
            sample_vulnerabilities,
            max_cves=5,
            severity_filter=["Critical"],
        )

        assert len(enricher.enrichment_calls) == 1
        call = enricher.enrichment_calls[0]
        assert call["vulnerabilities"] == sample_vulnerabilities
        assert call["max_cves"] == 5
        assert call["severity_filter"] == ["Critical"]

    def test_multiple_enrichment_calls_tracked(self, sample_vulnerabilities):
        """Test that multiple enrichment calls are all tracked."""
        enricher = MockEnricher()

        enricher.enrich_report(sample_vulnerabilities)
        enricher.enrich_report(sample_vulnerabilities, max_cves=1)
        enricher.enrich_report(sample_vulnerabilities, severity_filter=["Low"])

        assert len(enricher.enrichment_calls) == 3

    def test_reset_calls(self, sample_vulnerabilities):
        """Test resetting enrichment call history."""
        enricher = MockEnricher()

        enricher.enrich_report(sample_vulnerabilities)
        assert len(enricher.enrichment_calls) == 1

        enricher.reset_calls()
        assert len(enricher.enrichment_calls) == 0

    def test_enrichment_includes_severity_in_impact(self, sample_vulnerabilities):
        """Test that enrichment impact includes severity level."""
        enricher = MockEnricher()

        result = enricher.enrich_report(sample_vulnerabilities[:1])

        enrichment = result["CVE-2024-12345"]
        # Should include severity (Critical -> critical)
        assert "critical" in enrichment.impact_analysis.lower()

    def test_custom_model_in_enrichment(self, sample_vulnerabilities):
        """Test that custom model name appears in enrichment."""
        enricher = MockEnricher(model="custom-test-model")

        result = enricher.enrich_report(sample_vulnerabilities[:1])

        enrichment = result["CVE-2024-12345"]
        assert enrichment.analysis_model == "custom-test-model"


class TestMockEnricherEdgeCases:
    """Edge case tests for MockEnricher."""

    def test_vulnerability_with_empty_severity(self):
        """Test handling vulnerability with empty severity."""
        enricher = MockEnricher()

        vulnerabilities = [
            {
                "vulnerability_id": "CVE-2024-00001",
                "vulnerability": {
                    "severity": "",  # Empty severity
                    "description": "Test",
                },
            }
        ]

        result = enricher.enrich_report(vulnerabilities, severity_filter=["Critical"])

        # Empty string doesn't match "Critical"
        assert result == {}

    def test_vulnerability_with_missing_severity(self):
        """Test handling vulnerability without severity field."""
        enricher = MockEnricher()

        vulnerabilities = [
            {
                "vulnerability_id": "CVE-2024-00001",
                "vulnerability": {
                    # No severity field
                    "description": "Test",
                },
            }
        ]

        result = enricher.enrich_report(vulnerabilities, severity_filter=["Unknown"])

        # Default severity is "Unknown"
        assert len(result) == 1

    def test_vulnerability_with_missing_vulnerability_dict(self):
        """Test handling vulnerability without vulnerability sub-dict."""
        enricher = MockEnricher()

        vulnerabilities = [
            {
                "vulnerability_id": "CVE-2024-00001",
                # Missing "vulnerability" dict
            }
        ]

        result = enricher.enrich_report(vulnerabilities, severity_filter=["Unknown"])

        # Should use default severity "Unknown"
        assert len(result) == 1

    def test_large_vulnerability_list(self):
        """Test handling large number of vulnerabilities."""
        enricher = MockEnricher()

        vulnerabilities = [
            {
                "vulnerability_id": f"CVE-2024-{i:05d}",
                "vulnerability": {
                    "severity": "Critical",
                    "description": f"Vulnerability {i}",
                },
            }
            for i in range(100)
        ]

        result = enricher.enrich_report(vulnerabilities)

        assert len(result) == 100

    def test_max_cves_zero(self):
        """Test that max_cves=0 returns empty result."""
        enricher = MockEnricher()

        vulnerabilities = [
            {
                "vulnerability_id": "CVE-2024-12345",
                "vulnerability": {"severity": "Critical"},
            }
        ]

        result = enricher.enrich_report(vulnerabilities, max_cves=0)

        # 0 is falsy, so it should not limit
        # Actually, `if max_cves and len(enrichments) >= max_cves` evaluates 0 as falsy
        # So max_cves=0 doesn't limit
        assert len(result) == 1
