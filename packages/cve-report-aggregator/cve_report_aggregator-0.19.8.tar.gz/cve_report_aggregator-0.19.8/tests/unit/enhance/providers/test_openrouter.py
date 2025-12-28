"""Comprehensive tests for the OpenRouter enricher provider.

This test suite validates the OpenRouter Chat Completions API integration for CVE enrichment,
including model validation, prompt building, concurrent enrichment, result parsing,
and error handling.
"""

import json
from unittest.mock import Mock, patch

import pytest

from cve_report_aggregator.enhance.base import Enricher
from cve_report_aggregator.enhance.exceptions import ModelValidationError
from cve_report_aggregator.enhance.providers.openrouter import OpenRouterEnricher


@pytest.fixture
def mock_openrouter_client(mocker):
    """Create a mock OpenRouter client with proper model list response."""
    mock_client = mocker.MagicMock()

    # Mock models.list() response
    mock_model = mocker.MagicMock()
    mock_model.id = "x-ai/grok-code-fast-1"

    mock_models_response = mocker.MagicMock()
    mock_models_response.data = [mock_model]

    mock_client.models.list.return_value = mock_models_response

    return mock_client


@pytest.fixture
def mock_baseline_context(tmp_path):
    """Create a temporary baseline security context file."""
    baseline_file = tmp_path / "baseline_security_context.md"
    baseline_content = """# Baseline Security Context

## Network Policy Enforcement
- Default deny all traffic
- Explicit allow rules for legitimate traffic

## Pepr Policies
- Non-root user enforcement
- Capability restrictions
"""
    baseline_file.write_text(baseline_content)
    return baseline_file


@pytest.fixture
def sample_cve_data():
    """Sample CVE data for testing."""
    return {
        "severity": "Critical",
        "description": "Remote code execution vulnerability in OpenSSL",
        "cvss": [
            {
                "version": "3.1",
                "metrics": {
                    "baseScore": 9.8,
                    "exploitabilityScore": 3.9,
                    "impactScore": 5.9,
                },
            }
        ],
        "fix": {"versions": ["1.1.1w", "3.0.12"]},
    }


@pytest.fixture
def sample_vulnerabilities():
    """Sample vulnerability list for enrichment."""
    return [
        {
            "vulnerability_id": "CVE-2024-12345",
            "vulnerability": {
                "id": "CVE-2024-12345",
                "severity": "Critical",
                "description": "Critical vulnerability",
                "cvss": [{"version": "3.1", "metrics": {"baseScore": 9.8}}],
            },
        },
        {
            "vulnerability_id": "CVE-2024-54321",
            "vulnerability": {
                "id": "CVE-2024-54321",
                "severity": "High",
                "description": "High severity vulnerability",
                "cvss": [{"version": "3.1", "metrics": {"baseScore": 7.5}}],
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


class TestOpenRouterEnricherInitialization:
    """Tests for OpenRouterEnricher initialization."""

    def test_init_with_defaults(self, mocker, mock_baseline_context):
        """Test initialization with default parameters."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "x-ai/grok-code-fast-1"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openrouter_class.return_value = mock_client

            enricher = OpenRouterEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            assert enricher.model == "x-ai/grok-code-fast-1"
            assert enricher.temperature == 1.0
            assert enricher.reasoning_effort == "medium"
            assert enricher.verbosity == "medium"
            assert enricher.max_completion_tokens is None
            assert enricher.seed is None
            assert enricher.metadata is None
            assert enricher.max_workers == 5
            assert "Network Policy Enforcement" in enricher.baseline_context

    def test_init_with_custom_parameters(self, mocker, mock_baseline_context):
        """Test initialization with custom parameters."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-mini"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openrouter_class.return_value = mock_client

            enricher = OpenRouterEnricher(
                api_key="test-api-key",
                model="gpt-5-mini",
                reasoning_effort="high",
                verbosity="low",
                max_completion_tokens=2048,
                seed=42,
                metadata={"project": "test"},
                max_workers=10,
                baseline_context_path=mock_baseline_context,
            )

            assert enricher.model == "gpt-5-mini"
            assert enricher.reasoning_effort == "high"
            assert enricher.verbosity == "low"
            assert enricher.max_completion_tokens == 2048
            assert enricher.seed == 42
            assert enricher.metadata == {"project": "test"}
            assert enricher.max_workers == 10

    def test_implements_enricher_protocol(self, mocker, mock_baseline_context):
        """Test that OpenRouterEnricher implements Enricher protocol."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "x-ai/grok-code-fast-1"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openrouter_class.return_value = mock_client

            enricher = OpenRouterEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            assert isinstance(enricher, Enricher)


class TestModelValidation:
    """Tests for model validation functionality."""

    def test_validate_model_success(self, mocker, mock_baseline_context):
        """Test successful model validation."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model1 = Mock()
            mock_model1.id = "x-ai/grok-code-fast-1"
            mock_model2 = Mock()
            mock_model2.id = "gpt-5-mini"

            mock_models_response = Mock()
            mock_models_response.data = [mock_model1, mock_model2]
            mock_client.models.list.return_value = mock_models_response

            mock_openrouter_class.return_value = mock_client

            # Should not raise any exception
            enricher = OpenRouterEnricher(
                api_key="test-api-key", model="x-ai/grok-code-fast-1", baseline_context_path=mock_baseline_context
            )

            assert enricher.model == "x-ai/grok-code-fast-1"

    def test_validate_model_not_available(self, mocker, mock_baseline_context):
        """Test model validation failure when model not available."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-4"

            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openrouter_class.return_value = mock_client

            with pytest.raises(ModelValidationError, match="not available"):
                OpenRouterEnricher(
                    api_key="test-api-key", model="x-ai/grok-code-fast-1", baseline_context_path=mock_baseline_context
                )

    def test_validate_model_api_error(self, mocker, mock_baseline_context):
        """Test model validation when API call fails."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_client.models.list.side_effect = Exception("API connection failed")

            mock_openrouter_class.return_value = mock_client

            with pytest.raises(ModelValidationError, match="Failed to validate model"):
                OpenRouterEnricher(
                    api_key="test-api-key", model="x-ai/grok-code-fast-1", baseline_context_path=mock_baseline_context
                )


class TestBaselineContextLoading:
    """Tests for baseline security context loading."""

    def test_load_baseline_context_success(self, mock_baseline_context):
        """Test successful loading of baseline context."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "x-ai/grok-code-fast-1"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openrouter_class.return_value = mock_client

            enricher = OpenRouterEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            assert "Network Policy Enforcement" in enricher.baseline_context
            assert "Pepr Policies" in enricher.baseline_context

    def test_load_baseline_context_file_not_found(self, tmp_path):
        """Test loading baseline context when file doesn't exist."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "x-ai/grok-code-fast-1"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openrouter_class.return_value = mock_client

            nonexistent_file = tmp_path / "nonexistent.md"

            with pytest.raises(FileNotFoundError, match="Baseline context file not found"):
                OpenRouterEnricher(api_key="test-api-key", baseline_context_path=nonexistent_file)


class TestPromptBuilding:
    """Tests for system and user prompt building."""

    def test_build_system_prompt(self, mocker, mock_baseline_context):
        """Test system prompt building includes baseline context."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "x-ai/grok-code-fast-1"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openrouter_class.return_value = mock_client

            enricher = OpenRouterEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            system_prompt = enricher.system_prompt

            assert "cybersecurity expert" in system_prompt
            assert "UDS Core" in system_prompt
            assert "NetworkPolicies" in system_prompt
            assert "Pepr" in system_prompt
            assert "Network Policy Enforcement" in system_prompt
            assert "SimpleCVEEnrichment" in system_prompt

    def test_build_user_prompt_basic(self, mocker, mock_baseline_context):
        """Test user prompt building with basic CVE data."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "x-ai/grok-code-fast-1"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openrouter_class.return_value = mock_client

            enricher = OpenRouterEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            cve_data = {
                "severity": "High",
                "description": "Test vulnerability description",
            }

            user_prompt = enricher._build_user_prompt("CVE-2024-12345", cve_data)

            assert "CVE-2024-12345" in user_prompt
            assert "High" in user_prompt
            assert "Test vulnerability description" in user_prompt
            assert "mitigation_summary" in user_prompt
            assert "impact_analysis" in user_prompt

    def test_build_user_prompt_with_cvss(self, mocker, mock_baseline_context, sample_cve_data):
        """Test user prompt building with CVSS scores."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "x-ai/grok-code-fast-1"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openrouter_class.return_value = mock_client

            enricher = OpenRouterEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            user_prompt = enricher._build_user_prompt("CVE-2024-54321", sample_cve_data)

            assert "CVE-2024-54321" in user_prompt
            assert "CVSS 3.x Base Score: 9.8" in user_prompt
            assert "Critical" in user_prompt

    def test_build_user_prompt_with_fix_versions(self, mocker, mock_baseline_context, sample_cve_data):
        """Test user prompt building with fix version information."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "x-ai/grok-code-fast-1"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openrouter_class.return_value = mock_client

            enricher = OpenRouterEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            user_prompt = enricher._build_user_prompt("CVE-2024-54321", sample_cve_data)

            assert "Fixed in versions: 1.1.1w, 3.0.12" in user_prompt


class TestEnrichSingleCVE:
    """Tests for single CVE enrichment."""

    def test_enrich_single_cve_success(self, mocker, mock_baseline_context):
        """Test successful enrichment of a single CVE."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "x-ai/grok-code-fast-1"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            # Mock chat completions response
            enrichment_data = {
                "cve_id": "CVE-2024-12345",
                "mitigation_summary": "UDS helps to mitigate CVE-2024-12345 by enforcing NetworkPolicies",
                "impact_analysis": "Without UDS Core controls, this could lead to data exfiltration.",
                "analysis_model": "x-ai/grok-code-fast-1",
                "analysis_timestamp": "2025-10-20T00:00:00Z",
            }
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = json.dumps(enrichment_data)
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_client.chat.send.return_value = mock_response

            mock_openrouter_class.return_value = mock_client

            enricher = OpenRouterEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            cve_data = {"severity": "Critical", "description": "Test vulnerability"}
            cve_id, enrichment = enricher._enrich_single_cve("CVE-2024-12345", cve_data)

            assert cve_id == "CVE-2024-12345"
            assert enrichment is not None
            assert enrichment.cve_id == "CVE-2024-12345"
            assert "NetworkPolicies" in enrichment.mitigation_summary

    def test_enrich_single_cve_empty_response(self, mocker, mock_baseline_context):
        """Test handling of empty response from API."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "x-ai/grok-code-fast-1"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            # Mock empty response
            mock_response = Mock()
            mock_response.choices = []
            mock_client.chat.send.return_value = mock_response

            mock_openrouter_class.return_value = mock_client

            enricher = OpenRouterEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            cve_data = {"severity": "Critical", "description": "Test vulnerability"}
            cve_id, enrichment = enricher._enrich_single_cve("CVE-2024-12345", cve_data)

            assert cve_id == "CVE-2024-12345"
            assert enrichment is None

    def test_enrich_single_cve_invalid_json(self, mocker, mock_baseline_context):
        """Test handling of invalid JSON in response."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "x-ai/grok-code-fast-1"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            # Mock response with invalid JSON
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = "This is not valid JSON"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_client.chat.send.return_value = mock_response

            mock_openrouter_class.return_value = mock_client

            enricher = OpenRouterEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            cve_data = {"severity": "Critical", "description": "Test vulnerability"}
            cve_id, enrichment = enricher._enrich_single_cve("CVE-2024-12345", cve_data)

            assert cve_id == "CVE-2024-12345"
            assert enrichment is None

    def test_enrich_single_cve_handles_markdown_wrapper(self, mocker, mock_baseline_context):
        """Test handling of JSON wrapped in markdown code blocks."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "x-ai/grok-code-fast-1"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            # Mock response with JSON wrapped in markdown
            enrichment_data = {
                "cve_id": "CVE-2024-12345",
                "mitigation_summary": "UDS helps to mitigate CVE-2024-12345 by enforcing NetworkPolicies",
                "impact_analysis": "Without UDS Core controls, this could lead to data exfiltration.",
                "analysis_model": "x-ai/grok-code-fast-1",
                "analysis_timestamp": "2025-10-20T00:00:00Z",
            }
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = f"```json\n{json.dumps(enrichment_data)}\n```"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_client.chat.send.return_value = mock_response

            mock_openrouter_class.return_value = mock_client

            enricher = OpenRouterEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            cve_data = {"severity": "Critical", "description": "Test vulnerability"}
            cve_id, enrichment = enricher._enrich_single_cve("CVE-2024-12345", cve_data)

            assert cve_id == "CVE-2024-12345"
            assert enrichment is not None
            assert enrichment.cve_id == "CVE-2024-12345"


class TestEnrichReportSeverityFiltering:
    """Tests for severity filtering in enrich_report."""

    def test_enrich_report_default_severity_filter(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test enrichment with default severity filter (Critical and High)."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "x-ai/grok-code-fast-1"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            # Mock chat completions response
            def create_response(model, messages, **kwargs):
                # Extract CVE ID from user message
                user_msg = messages[1]["content"]
                if "CVE-2024-12345" in user_msg:
                    cve_id = "CVE-2024-12345"
                elif "CVE-2024-54321" in user_msg:
                    cve_id = "CVE-2024-54321"
                else:
                    cve_id = "CVE-UNKNOWN"

                enrichment_data = {
                    "cve_id": cve_id,
                    "mitigation_summary": f"UDS helps to mitigate {cve_id} by enforcing NetworkPolicies",
                    "impact_analysis": "Without UDS Core controls, this could lead to data exfiltration.",
                    "analysis_model": "x-ai/grok-code-fast-1",
                    "analysis_timestamp": "2025-10-20T00:00:00Z",
                }
                mock_response = Mock()
                mock_choice = Mock()
                mock_message = Mock()
                mock_message.content = json.dumps(enrichment_data)
                mock_choice.message = mock_message
                mock_response.choices = [mock_choice]
                return mock_response

            mock_client.chat.send.side_effect = create_response

            mock_openrouter_class.return_value = mock_client

            enricher = OpenRouterEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            result = enricher.enrich_report(sample_vulnerabilities)

            # Should enrich Critical and High severity CVEs only
            assert len(result) == 2
            assert "CVE-2024-12345" in result
            assert "CVE-2024-54321" in result
            assert "CVE-2024-99999" not in result  # Medium severity excluded

    def test_enrich_report_no_matching_severity(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test enrichment when no CVEs match severity filter."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "x-ai/grok-code-fast-1"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openrouter_class.return_value = mock_client

            enricher = OpenRouterEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            # Filter for only "Low" severity (none in sample data)
            result = enricher.enrich_report(sample_vulnerabilities, severity_filter=["Low"])

            assert result == {}

    def test_enrich_report_empty_vulnerabilities(self, mocker, mock_baseline_context):
        """Test enrichment with empty vulnerability list."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "x-ai/grok-code-fast-1"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openrouter_class.return_value = mock_client

            enricher = OpenRouterEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            result = enricher.enrich_report([])

            assert result == {}


class TestEnrichReportConcurrency:
    """Tests for concurrent enrichment functionality."""

    def test_enrich_report_concurrent_execution(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test that enrichment runs concurrently with ThreadPoolExecutor."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "x-ai/grok-code-fast-1"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            call_count = [0]

            def create_response(model, messages, **kwargs):
                call_count[0] += 1
                user_msg = messages[1]["content"]
                if "CVE-2024-12345" in user_msg:
                    cve_id = "CVE-2024-12345"
                elif "CVE-2024-54321" in user_msg:
                    cve_id = "CVE-2024-54321"
                else:
                    cve_id = "CVE-UNKNOWN"

                enrichment_data = {
                    "cve_id": cve_id,
                    "mitigation_summary": f"UDS helps to mitigate {cve_id}",
                    "impact_analysis": "Impact analysis.",
                    "analysis_model": "x-ai/grok-code-fast-1",
                    "analysis_timestamp": "2025-10-20T00:00:00Z",
                }
                mock_response = Mock()
                mock_choice = Mock()
                mock_message = Mock()
                mock_message.content = json.dumps(enrichment_data)
                mock_choice.message = mock_message
                mock_response.choices = [mock_choice]
                return mock_response

            mock_client.chat.send.side_effect = create_response

            mock_openrouter_class.return_value = mock_client

            enricher = OpenRouterEnricher(
                api_key="test-api-key", baseline_context_path=mock_baseline_context, max_workers=3
            )

            result = enricher.enrich_report(sample_vulnerabilities)

            # Should have made 2 API calls (Critical and High severity CVEs)
            assert call_count[0] == 2
            assert len(result) == 2

    def test_enrich_report_handles_partial_failures(self, mocker, mock_baseline_context):
        """Test that partial failures don't block other enrichments."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "x-ai/grok-code-fast-1"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            # First call fails (for CVE-2024-12345), second call succeeds (for CVE-2024-54321)
            enrichment_data = {
                "cve_id": "CVE-2024-54321",
                "mitigation_summary": "UDS helps to mitigate CVE-2024-54321",
                "impact_analysis": "Impact analysis.",
                "analysis_model": "x-ai/grok-code-fast-1",
                "analysis_timestamp": "2025-10-20T00:00:00Z",
            }
            mock_success_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = json.dumps(enrichment_data)
            mock_choice.message = mock_message
            mock_success_response.choices = [mock_choice]

            # Use a list of side effects: first call raises, second returns success
            mock_client.chat.send.side_effect = [
                Exception("API error"),
                mock_success_response,
            ]

            mock_openrouter_class.return_value = mock_client

            enricher = OpenRouterEnricher(
                api_key="test-api-key", baseline_context_path=mock_baseline_context, max_workers=1
            )

            # Only use 2 CVEs (Critical and High) - we control the order with max_workers=1
            vulnerabilities = [
                {
                    "vulnerability_id": "CVE-2024-12345",
                    "vulnerability": {"severity": "Critical", "description": "Critical CVE"},
                },
                {
                    "vulnerability_id": "CVE-2024-54321",
                    "vulnerability": {"severity": "High", "description": "High CVE"},
                },
            ]

            result = enricher.enrich_report(vulnerabilities)

            # Should have 1 successful enrichment despite 1 failure
            assert len(result) == 1
            assert "CVE-2024-54321" in result


class TestResultParsing:
    """Tests for parsing enrichment results."""

    def test_parse_valid_enrichment(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test parsing valid enrichment response."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "x-ai/grok-code-fast-1"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            # Valid enrichment data
            enrichment_data = {
                "cve_id": "CVE-2024-12345",
                "mitigation_summary": (
                    "UDS helps to mitigate CVE-2024-12345 by enforcing non-root execution through Pepr policies."
                ),
                "impact_analysis": (
                    "Without UDS Core controls, this vulnerability could enable privilege escalation "
                    "and container escape."
                ),
                "analysis_model": "x-ai/grok-code-fast-1",
                "analysis_timestamp": "2025-10-20T12:00:00Z",
            }

            def create_response(model, messages, **kwargs):
                mock_response = Mock()
                mock_choice = Mock()
                mock_message = Mock()
                mock_message.content = json.dumps(enrichment_data)
                mock_choice.message = mock_message
                mock_response.choices = [mock_choice]
                return mock_response

            mock_client.chat.send.side_effect = create_response

            mock_openrouter_class.return_value = mock_client

            enricher = OpenRouterEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            result = enricher.enrich_report(sample_vulnerabilities[:1])  # Just Critical CVE

            assert len(result) == 1
            assert "CVE-2024-12345" in result
            enrichment = result["CVE-2024-12345"]
            assert enrichment.cve_id == "CVE-2024-12345"
            assert "Pepr policies" in enrichment.mitigation_summary
            assert "privilege escalation" in enrichment.impact_analysis
            assert enrichment.analysis_model == "x-ai/grok-code-fast-1"

    def test_parse_invalid_json_in_response(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test handling of invalid JSON in response content."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "x-ai/grok-code-fast-1"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            # Invalid JSON in content
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = "This is not valid JSON"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_client.chat.send.return_value = mock_response

            mock_openrouter_class.return_value = mock_client

            enricher = OpenRouterEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            result = enricher.enrich_report(sample_vulnerabilities)

            # Should skip invalid response and return empty
            assert result == {}


class TestMaxCVEsLimit:
    """Tests for max_cves limit functionality."""

    def test_enrich_report_respects_max_cves(self, mocker, mock_baseline_context):
        """Test that max_cves limit is respected."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "x-ai/grok-code-fast-1"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            call_count = [0]

            def create_response(model, messages, **kwargs):
                call_count[0] += 1
                enrichment_data = {
                    "cve_id": f"CVE-2024-{call_count[0]}",
                    "mitigation_summary": "UDS helps to mitigate this CVE",
                    "impact_analysis": "Impact analysis.",
                    "analysis_model": "x-ai/grok-code-fast-1",
                    "analysis_timestamp": "2025-10-20T00:00:00Z",
                }
                mock_response = Mock()
                mock_choice = Mock()
                mock_message = Mock()
                mock_message.content = json.dumps(enrichment_data)
                mock_choice.message = mock_message
                mock_response.choices = [mock_choice]
                return mock_response

            mock_client.chat.send.side_effect = create_response

            mock_openrouter_class.return_value = mock_client

            enricher = OpenRouterEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            # Create 5 Critical CVEs
            vulnerabilities = [
                {
                    "vulnerability_id": f"CVE-2024-{i}",
                    "vulnerability": {"severity": "Critical", "description": f"CVE {i}"},
                }
                for i in range(1, 6)
            ]

            # Request max 2 CVEs
            result = enricher.enrich_report(vulnerabilities, max_cves=2)

            # Should only enrich 2 CVEs
            assert call_count[0] == 2
            assert len(result) == 2
