"""Comprehensive tests for the OpenAI client module.

This test suite validates the OpenAI Batch API integration for CVE enrichment,
including model validation, prompt building, batch job lifecycle, result parsing,
and error handling.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from cve_report_aggregator.enhance.models import SimpleCVEEnrichment
from cve_report_aggregator.enhance.openai_client import OpenAIEnricher


@pytest.fixture
def mock_openai_client(mocker):
    """Create a mock OpenAI client with proper model list response."""
    mock_client = mocker.MagicMock()

    # Mock models.list() response
    mock_model = mocker.MagicMock()
    mock_model.id = "gpt-5-nano"

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
    """Sample vulnerability list for batch enrichment."""
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


@pytest.fixture
def sample_cve_data_with_empty_fix():
    """Sample CVE data with empty fix versions."""
    return {
        "severity": "High",
        "description": "Test vulnerability",
        "cvss": [{"version": "3.1", "metrics": {"baseScore": 7.5}}],
        "fix": {"versions": []},  # Empty fix versions
    }


class TestOpenAIEnricherInitialization:
    """Tests for OpenAIEnricher initialization."""

    def test_init_with_defaults(self, mocker, mock_baseline_context):
        """Test initialization with default parameters."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            assert enricher.model == "gpt-5-nano"
            assert enricher.temperature == 1.0
            assert enricher.reasoning_effort == "medium"
            assert enricher.verbosity == "medium"
            assert enricher.max_completion_tokens is None
            assert enricher.seed is None
            assert enricher.metadata is None
            assert "Network Policy Enforcement" in enricher.baseline_context

    def test_init_with_custom_parameters(self, mocker, mock_baseline_context):
        """Test initialization with custom parameters."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-mini"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(
                api_key="test-api-key",
                model="gpt-5-mini",
                reasoning_effort="high",
                verbosity="low",
                max_completion_tokens=2048,
                seed=42,
                metadata={"project": "test"},
                baseline_context_path=mock_baseline_context,
            )

            assert enricher.model == "gpt-5-mini"
            assert enricher.reasoning_effort == "high"
            assert enricher.verbosity == "low"
            assert enricher.max_completion_tokens == 2048
            assert enricher.seed == 42
            assert enricher.metadata == {"project": "test"}

    def test_init_uses_default_baseline_context(self, mocker):
        """Test initialization with default baseline context path."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openai_class.return_value = mock_client

            # Mock the Path.exists() and read_text() for default path
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.read_text", return_value="# Default baseline context"):
                    enricher = OpenAIEnricher(api_key="test-api-key")

                    assert enricher.baseline_context == "# Default baseline context"


class TestModelValidation:
    """Tests for model validation functionality."""

    def test_validate_model_success(self, mocker, mock_baseline_context):
        """Test successful model validation."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model1 = Mock()
            mock_model1.id = "gpt-5-nano"
            mock_model2 = Mock()
            mock_model2.id = "gpt-5-mini"

            mock_models_response = Mock()
            mock_models_response.data = [mock_model1, mock_model2]
            mock_client.models.list.return_value = mock_models_response

            mock_openai_class.return_value = mock_client

            # Should not raise any exception
            enricher = OpenAIEnricher(
                api_key="test-api-key", model="gpt-5-nano", baseline_context_path=mock_baseline_context
            )

            assert enricher.model == "gpt-5-nano"

    def test_validate_model_not_available(self, mocker, mock_baseline_context):
        """Test model validation failure when model not available."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-4"

            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openai_class.return_value = mock_client

            with pytest.raises(ValueError, match="Model 'gpt-5-nano' is not available"):
                OpenAIEnricher(api_key="test-api-key", model="gpt-5-nano", baseline_context_path=mock_baseline_context)

    def test_validate_model_api_error(self, mocker, mock_baseline_context):
        """Test model validation when API call fails."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_client.models.list.side_effect = Exception("API connection failed")

            mock_openai_class.return_value = mock_client

            with pytest.raises(ValueError, match="Failed to validate model"):
                OpenAIEnricher(api_key="test-api-key", model="gpt-5-nano", baseline_context_path=mock_baseline_context)


class TestBaselineContextLoading:
    """Tests for baseline security context loading."""

    def test_load_baseline_context_success(self, mock_baseline_context):
        """Test successful loading of baseline context."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            assert "Network Policy Enforcement" in enricher.baseline_context
            assert "Pepr Policies" in enricher.baseline_context

    def test_load_baseline_context_file_not_found(self, tmp_path):
        """Test loading baseline context when file doesn't exist."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openai_class.return_value = mock_client

            nonexistent_file = tmp_path / "nonexistent.md"

            with pytest.raises(FileNotFoundError, match="Baseline context file not found"):
                OpenAIEnricher(api_key="test-api-key", baseline_context_path=nonexistent_file)


class TestPromptBuilding:
    """Tests for system and user prompt building."""

    def test_build_system_prompt(self, mocker, mock_baseline_context):
        """Test system prompt building includes baseline context."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            system_prompt = enricher.system_prompt

            assert "cybersecurity expert" in system_prompt
            assert "UDS Core" in system_prompt
            assert "NetworkPolicies" in system_prompt
            assert "Pepr" in system_prompt
            assert "Network Policy Enforcement" in system_prompt
            assert "SimpleCVEEnrichment" in system_prompt

    def test_build_user_prompt_basic(self, mocker, mock_baseline_context):
        """Test user prompt building with basic CVE data."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

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
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            user_prompt = enricher._build_user_prompt("CVE-2024-54321", sample_cve_data)

            assert "CVE-2024-54321" in user_prompt
            assert "CVSS 3.x Base Score: 9.8" in user_prompt
            assert "Critical" in user_prompt

    def test_build_user_prompt_with_fix_versions(self, mocker, mock_baseline_context, sample_cve_data):
        """Test user prompt building with fix version information."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            user_prompt = enricher._build_user_prompt("CVE-2024-54321", sample_cve_data)

            assert "Fixed in versions: 1.1.1w, 3.0.12" in user_prompt

    def test_build_user_prompt_without_optional_fields(self, mocker, mock_baseline_context):
        """Test user prompt building without CVSS or fix information."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            cve_data = {
                "severity": "Unknown",
                "description": "No description available",
            }

            user_prompt = enricher._build_user_prompt("CVE-2024-99999", cve_data)

            assert "CVE-2024-99999" in user_prompt
            assert "Unknown" in user_prompt
            # Should not include CVSS or fix info sections
            assert "CVSS 3.x Base Score" not in user_prompt
            assert "Fixed in versions" not in user_prompt

    def test_build_user_prompt_with_empty_fix_versions(
        self, mocker, mock_baseline_context, sample_cve_data_with_empty_fix
    ):
        """Test user prompt building with empty fix versions list."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            user_prompt = enricher._build_user_prompt("CVE-2024-77777", sample_cve_data_with_empty_fix)

            # Should not include fix info when versions list is empty
            assert "Fixed in versions" not in user_prompt


class TestBatchRequestCreation:
    """Tests for batch request creation."""

    def test_create_batch_request_basic(self, mocker, mock_baseline_context):
        """Test creating basic batch request with required parameters."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            cve_data = {"severity": "High", "description": "Test"}
            request = enricher._create_batch_request("CVE-2024-12345", cve_data, "custom-id-1")

            assert request["custom_id"] == "custom-id-1"
            assert request["method"] == "POST"
            assert request["url"] == "/v1/chat/completions"
            assert request["body"]["model"] == "gpt-5-nano"
            assert request["body"]["temperature"] == 1.0
            assert request["body"]["reasoning_effort"] == "medium"
            assert request["body"]["verbosity"] == "medium"
            assert request["body"]["response_format"] == {"type": "json_object"}
            assert len(request["body"]["messages"]) == 2
            assert request["body"]["messages"][0]["role"] == "system"
            assert request["body"]["messages"][1]["role"] == "user"

    def test_create_batch_request_with_optional_params(self, mocker, mock_baseline_context):
        """Test creating batch request with optional parameters."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-mini"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(
                api_key="test-api-key",
                model="gpt-5-mini",
                max_completion_tokens=4096,
                seed=42,
                metadata={"env": "test"},
                baseline_context_path=mock_baseline_context,
            )

            cve_data = {"severity": "Critical", "description": "Test"}
            request = enricher._create_batch_request("CVE-2024-54321", cve_data, "custom-id-2")

            assert request["body"]["max_completion_tokens"] == 4096
            assert request["body"]["seed"] == 42
            assert request["body"]["metadata"] == {"env": "test"}
            assert request["body"]["store"] is True  # Required when metadata is set

    def test_create_batch_request_without_optional_params(self, mocker, mock_baseline_context):
        """Test batch request doesn't include optional params when not set."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            cve_data = {"severity": "Low", "description": "Test"}
            request = enricher._create_batch_request("CVE-2024-99999", cve_data, "custom-id-3")

            assert "max_completion_tokens" not in request["body"]
            assert "seed" not in request["body"]
            assert "metadata" not in request["body"]
            assert "store" not in request["body"]


class TestEnrichReportSeverityFiltering:
    """Tests for severity filtering in enrich_report."""

    def test_enrich_report_default_severity_filter(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test enrichment with default severity filter (Critical and High)."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            # Mock batch job lifecycle
            mock_batch_file = Mock()
            mock_batch_file.id = "file-123"
            mock_client.files.create.return_value = mock_batch_file

            mock_batch = Mock()
            mock_batch.id = "batch-123"
            mock_batch.status = "completed"
            mock_batch.request_counts = Mock()
            mock_batch.output_file_id = "output-file-123"
            mock_client.batches.create.return_value = mock_batch
            mock_client.batches.retrieve.return_value = mock_batch

            # Mock output content
            output_data = {
                "cve_id": "CVE-2024-12345",
                "mitigation_summary": "UDS helps to mitigate CVE-2024-12345 by enforcing NetworkPolicies",
                "impact_analysis": "Without UDS Core controls, this could lead to data exfiltration.",
                "analysis_model": "gpt-5-nano",
                "analysis_timestamp": "2025-10-20T00:00:00Z",
            }
            mock_output_content = Mock()
            mock_output_content.read.return_value = json.dumps(
                {
                    "custom_id": "cve-0-CVE-2024-12345",
                    "response": {"body": {"choices": [{"message": {"content": json.dumps(output_data)}}]}},
                }
            ).encode("utf-8")
            mock_client.files.content.return_value = mock_output_content

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            with patch("time.sleep"):  # Skip actual sleep
                result = enricher.enrich_report(sample_vulnerabilities)

            # Should only enrich Critical and High severity CVEs (default filter)
            # CVE-2024-12345 (Critical) and CVE-2024-54321 (High) should be included
            # CVE-2024-99999 (Medium) should be filtered out
            assert len(result) == 1  # Only one result from mock
            assert "CVE-2024-12345" in result

    def test_enrich_report_custom_severity_filter(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test enrichment with custom severity filter."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            # Mock batch job lifecycle
            mock_batch_file = Mock()
            mock_batch_file.id = "file-123"
            mock_client.files.create.return_value = mock_batch_file

            mock_batch = Mock()
            mock_batch.id = "batch-123"
            mock_batch.status = "completed"
            mock_batch.request_counts = Mock()
            mock_batch.output_file_id = "output-file-123"
            mock_client.batches.create.return_value = mock_batch
            mock_client.batches.retrieve.return_value = mock_batch

            # Mock output content - all three CVEs
            outputs = []
            for idx, vuln in enumerate(sample_vulnerabilities):
                output_data = {
                    "cve_id": vuln["vulnerability_id"],
                    "mitigation_summary": f"UDS helps to mitigate {vuln['vulnerability_id']}",
                    "impact_analysis": "Impact analysis",
                    "analysis_model": "gpt-5-nano",
                    "analysis_timestamp": "2025-10-20T00:00:00Z",
                }
                outputs.append(
                    json.dumps(
                        {
                            "custom_id": f"cve-{idx}-{vuln['vulnerability_id']}",
                            "response": {"body": {"choices": [{"message": {"content": json.dumps(output_data)}}]}},
                        }
                    )
                )

            mock_output_content = Mock()
            mock_output_content.read.return_value = "\n".join(outputs).encode("utf-8")
            mock_client.files.content.return_value = mock_output_content

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            with patch("time.sleep"):
                # Allow all severities
                result = enricher.enrich_report(sample_vulnerabilities, severity_filter=["Critical", "High", "Medium"])

            # All three CVEs should be enriched
            assert len(result) == 3
            assert "CVE-2024-12345" in result
            assert "CVE-2024-54321" in result
            assert "CVE-2024-99999" in result

    def test_enrich_report_no_matching_severity(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test enrichment when no CVEs match severity filter."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            # Filter for only "Low" severity (none in sample data)
            result = enricher.enrich_report(sample_vulnerabilities, severity_filter=["Low"])

            assert result == {}

    def test_enrich_report_max_cves_limit(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test enrichment with max_cves limit."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            # Mock batch job lifecycle
            mock_batch_file = Mock()
            mock_batch_file.id = "file-123"
            mock_client.files.create.return_value = mock_batch_file

            mock_batch = Mock()
            mock_batch.id = "batch-123"
            mock_batch.status = "completed"
            mock_batch.request_counts = Mock()
            mock_batch.output_file_id = "output-file-123"
            mock_client.batches.create.return_value = mock_batch
            mock_client.batches.retrieve.return_value = mock_batch

            # Mock output for only 1 CVE
            output_data = {
                "cve_id": "CVE-2024-12345",
                "mitigation_summary": "UDS helps to mitigate CVE-2024-12345",
                "impact_analysis": "Impact analysis",
                "analysis_model": "gpt-5-nano",
                "analysis_timestamp": "2025-10-20T00:00:00Z",
            }
            mock_output_content = Mock()
            mock_output_content.read.return_value = json.dumps(
                {
                    "custom_id": "cve-0-CVE-2024-12345",
                    "response": {"body": {"choices": [{"message": {"content": json.dumps(output_data)}}]}},
                }
            ).encode("utf-8")
            mock_client.files.content.return_value = mock_output_content

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            with patch("time.sleep"):
                # Limit to 1 CVE
                result = enricher.enrich_report(sample_vulnerabilities, max_cves=1)

            # Only 1 CVE should be processed
            assert len(result) == 1

    def test_enrich_report_empty_vulnerabilities(self, mocker, mock_baseline_context):
        """Test enrichment with empty vulnerability list."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            result = enricher.enrich_report([])

            assert result == {}

    def test_enrich_report_missing_vulnerability_id(self, mocker, mock_baseline_context):
        """Test handling of vulnerabilities without ID."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

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


class TestBatchJobLifecycle:
    """Tests for batch job creation, polling, and completion."""

    def test_batch_job_success(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test successful batch job lifecycle."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            # Mock file upload
            mock_batch_file = Mock()
            mock_batch_file.id = "file-abc123"
            mock_client.files.create.return_value = mock_batch_file

            # Mock batch creation
            mock_batch = Mock()
            mock_batch.id = "batch-xyz789"
            mock_batch.status = "validating"
            mock_batch.request_counts = Mock()
            mock_client.batches.create.return_value = mock_batch

            # Mock batch polling (validating -> in_progress -> completed)
            mock_batch_in_progress = Mock()
            mock_batch_in_progress.id = "batch-xyz789"
            mock_batch_in_progress.status = "in_progress"
            mock_batch_in_progress.request_counts = Mock()

            mock_batch_completed = Mock()
            mock_batch_completed.id = "batch-xyz789"
            mock_batch_completed.status = "completed"
            mock_batch_completed.request_counts = Mock()
            mock_batch_completed.output_file_id = "output-file-123"

            mock_client.batches.retrieve.side_effect = [
                mock_batch_in_progress,
                mock_batch_completed,
            ]

            # Mock output file content
            output_data = {
                "cve_id": "CVE-2024-12345",
                "mitigation_summary": "UDS helps to mitigate CVE-2024-12345 by enforcing NetworkPolicies",
                "impact_analysis": "Without UDS Core, attackers could exploit this vulnerability.",
                "analysis_model": "gpt-5-nano",
                "analysis_timestamp": "2025-10-20T12:00:00Z",
            }
            mock_output_content = Mock()
            mock_output_content.read.return_value = json.dumps(
                {
                    "custom_id": "cve-0-CVE-2024-12345",
                    "response": {"body": {"choices": [{"message": {"content": json.dumps(output_data)}}]}},
                }
            ).encode("utf-8")
            mock_client.files.content.return_value = mock_output_content

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            with patch("time.sleep"):  # Skip actual sleep during polling
                result = enricher.enrich_report(sample_vulnerabilities)

            assert len(result) == 1
            assert "CVE-2024-12345" in result
            assert isinstance(result["CVE-2024-12345"], SimpleCVEEnrichment)
            assert result["CVE-2024-12345"].cve_id == "CVE-2024-12345"
            assert "NetworkPolicies" in result["CVE-2024-12345"].mitigation_summary

    def test_batch_job_failed_status(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test handling of failed batch job."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            # Mock batch job that fails
            mock_batch_file = Mock()
            mock_batch_file.id = "file-123"
            mock_client.files.create.return_value = mock_batch_file

            mock_batch = Mock()
            mock_batch.id = "batch-123"
            mock_batch.status = "failed"
            mock_batch.errors = {"message": "Internal error"}
            mock_batch.request_counts = Mock()
            mock_client.batches.create.return_value = mock_batch
            mock_client.batches.retrieve.return_value = mock_batch

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            with patch("time.sleep"):
                result = enricher.enrich_report(sample_vulnerabilities)

            # Should return empty dict on failure
            assert result == {}

    def test_batch_job_expired_status(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test handling of expired batch job."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_batch_file = Mock()
            mock_batch_file.id = "file-123"
            mock_client.files.create.return_value = mock_batch_file

            mock_batch = Mock()
            mock_batch.id = "batch-123"
            mock_batch.status = "expired"
            mock_batch.request_counts = Mock()
            mock_client.batches.create.return_value = mock_batch
            mock_client.batches.retrieve.return_value = mock_batch

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            with patch("time.sleep"):
                result = enricher.enrich_report(sample_vulnerabilities)

            assert result == {}

    def test_batch_job_cancelled_status(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test handling of cancelled batch job."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_batch_file = Mock()
            mock_batch_file.id = "file-123"
            mock_client.files.create.return_value = mock_batch_file

            mock_batch = Mock()
            mock_batch.id = "batch-123"
            mock_batch.status = "cancelled"
            mock_batch.request_counts = Mock()
            mock_client.batches.create.return_value = mock_batch
            mock_client.batches.retrieve.return_value = mock_batch

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            with patch("time.sleep"):
                result = enricher.enrich_report(sample_vulnerabilities)

            assert result == {}

    def test_batch_job_no_output_file(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test handling when batch completes but has no output file."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_batch_file = Mock()
            mock_batch_file.id = "file-123"
            mock_client.files.create.return_value = mock_batch_file

            mock_batch = Mock()
            mock_batch.id = "batch-123"
            mock_batch.status = "completed"
            mock_batch.output_file_id = None  # No output file
            mock_batch.error_file_id = None
            mock_batch.request_counts = Mock()
            mock_client.batches.create.return_value = mock_batch
            mock_client.batches.retrieve.return_value = mock_batch

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            with patch("time.sleep"):
                result = enricher.enrich_report(sample_vulnerabilities)

            assert result == {}

    def test_batch_job_with_error_file(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test handling error file when batch has no output."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_batch_file = Mock()
            mock_batch_file.id = "file-123"
            mock_client.files.create.return_value = mock_batch_file

            mock_batch = Mock()
            mock_batch.id = "batch-123"
            mock_batch.status = "completed"
            mock_batch.output_file_id = None
            mock_batch.error_file_id = "error-file-456"
            mock_batch.request_counts = Mock()
            mock_client.batches.create.return_value = mock_batch
            mock_client.batches.retrieve.return_value = mock_batch

            # Mock error file content
            error_data = [
                {"custom_id": "cve-0", "error": {"message": "Rate limit exceeded"}},
                {"custom_id": "cve-1", "error": {"message": "Invalid request"}},
            ]
            mock_error_content = Mock()
            mock_error_content.read.return_value = "\n".join([json.dumps(e) for e in error_data]).encode("utf-8")
            mock_client.files.content.return_value = mock_error_content

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            with patch("time.sleep"):
                result = enricher.enrich_report(sample_vulnerabilities)

            assert result == {}
            # Should have attempted to download error file
            mock_client.files.content.assert_called_once_with("error-file-456")

    def test_batch_job_error_file_download_fails(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test handling when error file download itself fails."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_batch_file = Mock()
            mock_batch_file.id = "file-123"
            mock_client.files.create.return_value = mock_batch_file

            mock_batch = Mock()
            mock_batch.id = "batch-123"
            mock_batch.status = "completed"
            mock_batch.output_file_id = None
            mock_batch.error_file_id = "error-file-456"
            mock_batch.request_counts = Mock()
            mock_client.batches.create.return_value = mock_batch
            mock_client.batches.retrieve.return_value = mock_batch

            # Simulate error file download failure
            mock_client.files.content.side_effect = Exception("Network error")

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            with patch("time.sleep"):
                result = enricher.enrich_report(sample_vulnerabilities)

            # Should handle exception gracefully and return empty dict
            assert result == {}
            mock_client.files.content.assert_called_once_with("error-file-456")


class TestResultParsing:
    """Tests for parsing batch results and enrichment extraction."""

    def test_parse_valid_enrichment(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test parsing valid enrichment response."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_batch_file = Mock()
            mock_batch_file.id = "file-123"
            mock_client.files.create.return_value = mock_batch_file

            mock_batch = Mock()
            mock_batch.id = "batch-123"
            mock_batch.status = "completed"
            mock_batch.output_file_id = "output-file-123"
            mock_batch.request_counts = Mock()
            mock_client.batches.create.return_value = mock_batch
            mock_client.batches.retrieve.return_value = mock_batch

            # Valid enrichment data
            output_data = {
                "cve_id": "CVE-2024-12345",
                "mitigation_summary": (
                    "UDS helps to mitigate CVE-2024-12345 by enforcing non-root execution through Pepr policies."
                ),
                "impact_analysis": (
                    "Without UDS Core controls, this vulnerability could enable privilege escalation "
                    "and container escape."
                ),
                "analysis_model": "gpt-5-nano",
                "analysis_timestamp": "2025-10-20T12:00:00Z",
            }
            mock_output_content = Mock()
            mock_output_content.read.return_value = json.dumps(
                {
                    "custom_id": "cve-0-CVE-2024-12345",
                    "response": {"body": {"choices": [{"message": {"content": json.dumps(output_data)}}]}},
                }
            ).encode("utf-8")
            mock_client.files.content.return_value = mock_output_content

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            with patch("time.sleep"):
                result = enricher.enrich_report(sample_vulnerabilities)

            assert len(result) == 1
            assert "CVE-2024-12345" in result
            enrichment = result["CVE-2024-12345"]
            assert enrichment.cve_id == "CVE-2024-12345"
            assert "Pepr policies" in enrichment.mitigation_summary
            assert "privilege escalation" in enrichment.impact_analysis
            assert enrichment.analysis_model == "gpt-5-nano"

    def test_parse_invalid_json_in_response(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test handling of invalid JSON in response content."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_batch_file = Mock()
            mock_batch_file.id = "file-123"
            mock_client.files.create.return_value = mock_batch_file

            mock_batch = Mock()
            mock_batch.id = "batch-123"
            mock_batch.status = "completed"
            mock_batch.output_file_id = "output-file-123"
            mock_batch.request_counts = Mock()
            mock_client.batches.create.return_value = mock_batch
            mock_client.batches.retrieve.return_value = mock_batch

            # Invalid JSON in content
            mock_output_content = Mock()
            mock_output_content.read.return_value = json.dumps(
                {
                    "custom_id": "cve-0-CVE-2024-12345",
                    "response": {"body": {"choices": [{"message": {"content": "This is not valid JSON"}}]}},
                }
            ).encode("utf-8")
            mock_client.files.content.return_value = mock_output_content

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            with patch("time.sleep"):
                result = enricher.enrich_report(sample_vulnerabilities)

            # Should skip invalid response and return empty
            assert result == {}

    def test_parse_validation_error(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test handling of Pydantic validation errors."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_batch_file = Mock()
            mock_batch_file.id = "file-123"
            mock_client.files.create.return_value = mock_batch_file

            mock_batch = Mock()
            mock_batch.id = "batch-123"
            mock_batch.status = "completed"
            mock_batch.output_file_id = "output-file-123"
            mock_batch.request_counts = Mock()
            mock_client.batches.create.return_value = mock_batch
            mock_client.batches.retrieve.return_value = mock_batch

            # Missing required fields for SimpleCVEEnrichment
            invalid_data = {
                "cve_id": "CVE-2024-12345",
                # Missing mitigation_summary, impact_analysis, etc.
            }
            mock_output_content = Mock()
            mock_output_content.read.return_value = json.dumps(
                {
                    "custom_id": "cve-0-CVE-2024-12345",
                    "response": {"body": {"choices": [{"message": {"content": json.dumps(invalid_data)}}]}},
                }
            ).encode("utf-8")
            mock_client.files.content.return_value = mock_output_content

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            with patch("time.sleep"):
                result = enricher.enrich_report(sample_vulnerabilities)

            # Should skip invalid data and return empty
            assert result == {}

    def test_parse_request_error_in_output(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test handling of individual request errors in output."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_batch_file = Mock()
            mock_batch_file.id = "file-123"
            mock_client.files.create.return_value = mock_batch_file

            mock_batch = Mock()
            mock_batch.id = "batch-123"
            mock_batch.status = "completed"
            mock_batch.output_file_id = "output-file-123"
            mock_batch.request_counts = Mock()
            mock_client.batches.create.return_value = mock_batch
            mock_client.batches.retrieve.return_value = mock_batch

            # Error in response
            mock_output_content = Mock()
            mock_output_content.read.return_value = json.dumps(
                {
                    "custom_id": "cve-0-CVE-2024-12345",
                    "error": {
                        "message": "Invalid request",
                        "code": "invalid_request_error",
                    },
                }
            ).encode("utf-8")
            mock_client.files.content.return_value = mock_output_content

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            with patch("time.sleep"):
                result = enricher.enrich_report(sample_vulnerabilities)

            # Should skip errored request
            assert result == {}

    def test_parse_multiple_enrichments(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test parsing multiple successful enrichments."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_batch_file = Mock()
            mock_batch_file.id = "file-123"
            mock_client.files.create.return_value = mock_batch_file

            mock_batch = Mock()
            mock_batch.id = "batch-123"
            mock_batch.status = "completed"
            mock_batch.output_file_id = "output-file-123"
            mock_batch.request_counts = Mock()
            mock_client.batches.create.return_value = mock_batch
            mock_client.batches.retrieve.return_value = mock_batch

            # Multiple valid enrichments
            outputs = []
            for idx in range(2):
                cve_id = f"CVE-2024-{12345 + idx}"
                output_data = {
                    "cve_id": cve_id,
                    "mitigation_summary": f"UDS helps to mitigate {cve_id} by enforcing security controls",
                    "impact_analysis": f"Impact analysis for {cve_id}",
                    "analysis_model": "gpt-5-nano",
                    "analysis_timestamp": "2025-10-20T12:00:00Z",
                }
                outputs.append(
                    json.dumps(
                        {
                            "custom_id": f"cve-{idx}-{cve_id}",
                            "response": {"body": {"choices": [{"message": {"content": json.dumps(output_data)}}]}},
                        }
                    )
                )

            mock_output_content = Mock()
            mock_output_content.read.return_value = "\n".join(outputs).encode("utf-8")
            mock_client.files.content.return_value = mock_output_content

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            with patch("time.sleep"):
                result = enricher.enrich_report(sample_vulnerabilities)

            assert len(result) == 2
            assert "CVE-2024-12345" in result
            assert "CVE-2024-12346" in result


class TestFileCleanup:
    """Tests for temporary file cleanup."""

    def test_temp_file_cleanup_on_success(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test that temporary batch file is cleaned up on success."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            mock_batch_file = Mock()
            mock_batch_file.id = "file-123"
            mock_client.files.create.return_value = mock_batch_file

            mock_batch = Mock()
            mock_batch.id = "batch-123"
            mock_batch.status = "completed"
            mock_batch.output_file_id = "output-file-123"
            mock_batch.request_counts = Mock()
            mock_client.batches.create.return_value = mock_batch
            mock_client.batches.retrieve.return_value = mock_batch

            output_data = {
                "cve_id": "CVE-2024-12345",
                "mitigation_summary": "UDS helps to mitigate CVE-2024-12345",
                "impact_analysis": "Impact analysis",
                "analysis_model": "gpt-5-nano",
                "analysis_timestamp": "2025-10-20T00:00:00Z",
            }
            mock_output_content = Mock()
            mock_output_content.read.return_value = json.dumps(
                {
                    "custom_id": "cve-0-CVE-2024-12345",
                    "response": {"body": {"choices": [{"message": {"content": json.dumps(output_data)}}]}},
                }
            ).encode("utf-8")
            mock_client.files.content.return_value = mock_output_content

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            # Track temp file creation
            temp_files_created = []

            original_named_temp_file = tempfile.NamedTemporaryFile

            def track_temp_file(*args, **kwargs):
                temp_file = original_named_temp_file(*args, **kwargs)
                temp_files_created.append(Path(temp_file.name))
                return temp_file

            with patch("tempfile.NamedTemporaryFile", side_effect=track_temp_file):
                with patch("time.sleep"):
                    enricher.enrich_report(sample_vulnerabilities)

            # Verify temp files were cleaned up
            for temp_file in temp_files_created:
                assert not temp_file.exists(), f"Temp file {temp_file} was not cleaned up"

    def test_temp_file_cleanup_on_error(self, mocker, mock_baseline_context, sample_vulnerabilities):
        """Test that temporary batch file is cleaned up even on error."""
        with patch("cve_report_aggregator.enhance.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "gpt-5-nano"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response

            # Simulate error during batch creation
            mock_client.files.create.side_effect = Exception("Upload failed")

            mock_openai_class.return_value = mock_client

            enricher = OpenAIEnricher(api_key="test-api-key", baseline_context_path=mock_baseline_context)

            temp_files_created = []

            original_named_temp_file = tempfile.NamedTemporaryFile

            def track_temp_file(*args, **kwargs):
                temp_file = original_named_temp_file(*args, **kwargs)
                temp_files_created.append(Path(temp_file.name))
                return temp_file

            with patch("tempfile.NamedTemporaryFile", side_effect=track_temp_file):
                with pytest.raises(Exception, match="Upload failed"):
                    enricher.enrich_report(sample_vulnerabilities)

            # Verify temp files were cleaned up even on error
            for temp_file in temp_files_created:
                assert not temp_file.exists(), f"Temp file {temp_file} was not cleaned up after error"
