"""OpenRouter API client for CVE enrichment with security context analysis.

This module provides the OpenRouterEnricher class that uses the OpenRouter
Chat Completions API to analyze CVEs in the context of UDS Core security controls.
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from openrouter import OpenRouter
from openrouter.components import Reasoning
from pydantic import ValidationError

from ...core.logging import get_logger
from ..base import BaseEnricher
from ..exceptions import EnrichmentError, ModelValidationError
from ..models import SimpleCVEEnrichment

logger = get_logger(__name__)


class OpenRouterEnricher(BaseEnricher):
    """OpenRouter Chat Completions API-based CVE enrichment engine.

    Uses OpenRouter Chat Completions API to analyze CVEs in the context of UDS Core
    security controls (NetworkPolicies and Pepr admission policies) to generate
    mitigation strategies.

    Attributes:
        client: OpenRouter client instance
        model: OpenRouter model to use (e.g., "x-ai/grok-code-fast-1")
        temperature: Fixed at 1.0 (required by some models)
        baseline_context: Baseline security context from UDS Core
        reasoning_effort: Reasoning effort level for model
        verbosity: Verbosity level for model responses
        max_workers: Maximum number of concurrent API requests

    Example:
        >>> enricher = OpenRouterEnricher(
        ...     api_key="sk-or-v1-...",
        ...     model="x-ai/grok-code-fast-1",
        ... )
        >>> enrichments = enricher.enrich_report(vulnerabilities)
        >>> for cve_id, enrichment in enrichments.items():
        ...     print(f"{cve_id}: {enrichment.mitigation_summary}")
    """

    def __init__(
        self,
        api_key: str,
        model: str = "x-ai/grok-code-fast-1",
        reasoning_effort: str = "medium",
        verbosity: str = "medium",
        max_completion_tokens: int | None = None,
        seed: int | None = None,
        metadata: dict[str, str] | None = None,
        baseline_context_path: Path | None = None,
        max_workers: int = 5,
    ) -> None:
        """Initialize OpenRouter API enricher.

        Args:
            api_key: OpenRouter API key
            model: OpenRouter model to use (default: x-ai/grok-code-fast-1)
            reasoning_effort: Reasoning effort level (minimal, low, medium, high)
            verbosity: Verbosity level for model responses (low, medium, high)
            max_completion_tokens: Optional upper bound for total tokens including reasoning tokens
            seed: Optional seed for reproducible results
            metadata: Optional metadata tags for OpenRouter requests
            baseline_context_path: Path to baseline security context markdown file.
                If None, uses default from package.
            max_workers: Maximum number of concurrent API requests (default: 5)

        Raises:
            ModelValidationError: If specified model is not available
            FileNotFoundError: If baseline context file not found

        Note:
            Temperature is fixed at 1.0 as required by some models.
        """
        self._models_cache: list[Any] | None = None
        self.client = OpenRouter(api_key=api_key)
        self.temperature = 1.0
        self.reasoning_effort = reasoning_effort
        self.verbosity = verbosity
        self.max_completion_tokens = max_completion_tokens
        self.seed = seed
        self.metadata = metadata
        self.max_workers = max_workers

        # Validate model before calling parent init
        self._validate_model_availability(model)

        # Call parent init which loads baseline context and builds system prompt
        super().__init__(model=model, baseline_context_path=baseline_context_path)

        logger.info(
            "OpenRouter API enricher initialized",
            model=model,
            temperature=self.temperature,
            reasoning_effort=self.reasoning_effort,
            verbosity=self.verbosity,
            max_completion_tokens=self.max_completion_tokens,
            max_workers=self.max_workers,
            seed=self.seed,
        )

    @property
    def _models(self) -> list[Any]:
        """List of available models from OpenRouter API (cached)."""
        if self._models_cache is None:
            self._models_cache = self.client.models.list().data
        return self._models_cache

    def _clear_model_cache(self) -> None:
        """Clear cached model data to force refresh on next access."""
        self._models_cache = None

    def _get_parameters_for_model(self, model: str) -> list[str]:
        """Get supported parameters for a specific model.

        Args:
            model: Model identifier

        Returns:
            List of supported parameter names

        Raises:
            ModelValidationError: If model not found
        """
        for _model in self._models:
            if _model.id == model:
                return _model.supported_parameters
        raise ModelValidationError(
            f"Model {model} not found in available models",
            model=model,
        )

    def _validate_model_availability(self, model: str) -> None:
        """Validate that the specified model is available via OpenRouter API.

        Args:
            model: Model identifier to validate

        Raises:
            ModelValidationError: If model is not available or API call fails
        """
        try:
            logger.debug("Validating model availability", model=model)

            # List all available models from OpenRouter
            models = self.client.models.list()
            available_model_ids = [m.id for m in models.data]

            # Check if configured model is in the list
            if model not in available_model_ids:
                logger.error(
                    "Model not available",
                    requested_model=model,
                    available_models=available_model_ids[:10],
                )
                raise ModelValidationError(
                    f"Model '{model}' is not available. "
                    f"Available models include: {', '.join(available_model_ids[:10])}",
                    model=model,
                    available_models=available_model_ids,
                )

            logger.debug("Model validation successful", model=model)

        except ModelValidationError:
            raise
        except Exception as e:
            logger.error("Failed to validate model", error=str(e), model=model)
            raise ModelValidationError(
                f"Failed to validate model '{model}': {str(e)}",
                model=model,
            ) from e

    def _build_system_prompt(self) -> str:
        """Build system prompt with baseline security context.

        Returns:
            System prompt for OpenRouter including UDS Core security documentation
        """
        return f"""You are a cybersecurity expert analyzing Common Vulnerabilities and Exposures (CVEs) \
in the context of a Kubernetes cluster running UDS Core.

UDS Core provides defense-in-depth security through:
- NetworkPolicies enforcing zero-trust networking
- Pepr admission policies preventing insecure configurations
- Istio service mesh providing mTLS and traffic control

Your task is to provide:
1. A 2 sentence explanation of how UDS Core helps mitigate the CVE
2. A 1 sentence impact analysis of what could happen WITHOUT UDS Core controls

Mitigation Format: "UDS helps to mitigate {{CVE_ID}} by {{explanation}}"

The mitigation explanation should:
- Be exactly ONE sentence
- Identify the most relevant security control(s)
- Focus on the primary mitigation mechanism

The impact analysis should:
- Be 1 sentences describing potential consequences without UDS Core
- Cover attack scenarios, data risks, and potential blast radius
- Be specific to this CVE's attack vector and severity

Baseline Security Context:
{self.baseline_context}

Respond ONLY with valid JSON matching the SimpleCVEEnrichment schema. Do not include markdown \
formatting, code blocks, or any text outside the JSON object."""

    def _build_user_prompt(self, cve_id: str, cve_data: dict[str, Any]) -> str:
        """Build user prompt for CVE analysis.

        Args:
            cve_id: CVE identifier (e.g., CVE-2025-8869)
            cve_data: Vulnerability data from unified report

        Returns:
            User prompt for OpenRouter
        """
        severity = cve_data.get("severity", "UNKNOWN")
        description = cve_data.get("description", "No description available")

        # Extract CVSS 3.x scores if available
        cvss_scores = []
        if "cvss" in cve_data:
            cvss_data = cve_data["cvss"]
            if isinstance(cvss_data, list):
                cvss_scores = [
                    f"CVSS 3.x Base Score: {entry.get('metrics', {}).get('baseScore')}"
                    for entry in cvss_data
                    if entry.get("version", "").startswith("3") and entry.get("metrics", {}).get("baseScore")
                ]
        cvss_info = "\n" + "\n".join(cvss_scores) if cvss_scores else ""

        # Extract fix information if available
        fix_info = ""
        if "fix" in cve_data and "versions" in cve_data["fix"]:
            versions = cve_data["fix"]["versions"]
            if versions:
                fix_info = f"\nFixed in versions: {', '.join(versions)}"

        timestamp = datetime.now(UTC).isoformat()

        return f"""Analyze the following CVE in the context of UDS Core security controls:

CVE ID: {cve_id}
Severity: {severity}{cvss_info}
Description: {description}{fix_info}

Provide your analysis in JSON format with TWO key fields:

{{
  "cve_id": "{cve_id}",
  "mitigation_summary": "UDS helps to mitigate {cve_id} by [your single-sentence explanation here]",
  "impact_analysis": "[1 sentence explanation of potential impact without UDS Core controls]",
  "analysis_model": "{self.model}",
  "analysis_timestamp": "{timestamp}"
}}

Requirements for the mitigation_summary:
- MUST be exactly ONE sentence
- MUST start with "UDS helps to mitigate {cve_id} by"
- MUST identify the most relevant UDS Core security control(s)
- MUST be concise and specific
- Focus on NetworkPolicies, Pepr policies, or Istio service mesh controls

Requirements for the impact_analysis:
- MUST be 2 sentences in length
- Describe what could happen WITHOUT UDS Core controls in place
- Cover attack scenarios (e.g., remote code execution, privilege escalation)
- Describe potential data risks (e.g., exfiltration, tampering)
- Mention blast radius (e.g., lateral movement, cluster-wide compromise)
- Be specific to this CVE's severity and attack vector

Example:
{{
  "cve_id": "CVE-2024-12345",
  "mitigation_summary": "UDS helps to mitigate CVE-2024-12345 by enforcing non-root container execution \
through Pepr admission policies and blocking unauthorized external network access via default-deny NetworkPolicies.",
  "impact_analysis": "Without UDS Core controls, this critical vulnerability could allow an attacker to \
achieve remote code execution on the vulnerable container with root privileges. This could enable lateral \
movement across the cluster, exfiltration of sensitive data from connected services, and deployment of \
malicious workloads. The blast radius would extend beyond the compromised pod to potentially affect the entire \
cluster and connected infrastructure.",
  "analysis_model": "{self.model}",
  "analysis_timestamp": "{timestamp}"
}}
"""

    def _filter_vulnerabilities(
        self,
        vulnerabilities: list[dict[str, Any]],
        max_cves: int | None,
        severity_filter: list[str],
    ) -> tuple[list[tuple[str, dict[str, Any]]], int]:
        """Filter vulnerabilities by severity and max count.

        Args:
            vulnerabilities: List of vulnerability dictionaries
            max_cves: Maximum number of CVEs to collect (None = all)
            severity_filter: List of severity levels to include

        Returns:
            Tuple of (filtered CVEs list, count skipped by severity)
        """
        cves_to_enrich: list[tuple[str, dict[str, Any]]] = []
        skipped_by_severity = 0

        for vuln in vulnerabilities:
            if max_cves and len(cves_to_enrich) >= max_cves:
                logger.info("Reached max CVE limit", max_cves=max_cves, collected=len(cves_to_enrich))
                break

            cve_id = vuln.get("vulnerability_id")
            if not cve_id:
                logger.warning("Skipping vulnerability without ID", vuln=vuln.get("count"))
                continue

            cve_data = vuln.get("vulnerability", {})
            severity = cve_data.get("severity", "Unknown")

            if severity_filter and severity not in severity_filter:
                logger.debug(
                    "Skipping CVE due to severity filter",
                    cve_id=cve_id,
                    severity=severity,
                    allowed_severities=severity_filter,
                )
                skipped_by_severity += 1
                continue

            cves_to_enrich.append((cve_id, cve_data))

        return cves_to_enrich, skipped_by_severity

    def _enrich_single_cve(self, cve_id: str, cve_data: dict[str, Any]) -> tuple[str, SimpleCVEEnrichment | None]:
        """Enrich a single CVE using the OpenRouter Chat API.

        Args:
            cve_id: CVE identifier
            cve_data: Vulnerability data from unified report

        Returns:
            Tuple of (cve_id, enrichment or None if failed)
        """
        try:
            logger.debug("Enriching CVE", cve_id=cve_id)

            # Build the request parameters
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self._build_user_prompt(cve_id, cve_data)},
            ]

            # Build reasoning config if effort is specified
            reasoning = None
            if self.reasoning_effort:
                reasoning = Reasoning(effort=self.reasoning_effort)

            # Create chat request using OpenRouter SDK's chat.send() method
            response = self.client.chat.send(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_completion_tokens,
                seed=self.seed,
                metadata=self.metadata,
                reasoning=reasoning,
                stream=False,
            )

            # Extract content from response
            if not response.choices or not response.choices[0].message.content:
                logger.error("Empty response from OpenRouter", cve_id=cve_id)
                return cve_id, None

            content = response.choices[0].message.content

            # Parse the JSON response
            try:
                # Handle potential markdown code blocks in response
                if content.startswith("```"):
                    # Remove markdown code block wrapper
                    lines = content.split("\n")
                    content = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

                enrichment_data = json.loads(content)
                enrichment = SimpleCVEEnrichment(**enrichment_data)
                logger.debug("CVE enrichment successful", cve_id=cve_id)
                return cve_id, enrichment

            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(
                    "Failed to parse enrichment response",
                    cve_id=cve_id,
                    error=str(e),
                    content=content[:200] if content else "empty",
                )
                return cve_id, None

        except Exception as e:
            logger.error("Failed to enrich CVE", cve_id=cve_id, error=str(e))
            return cve_id, None

    def enrich_report(
        self,
        vulnerabilities: list[dict[str, Any]],
        max_cves: int | None = None,
        severity_filter: list[str] | None = None,
    ) -> dict[str, SimpleCVEEnrichment]:
        """Enrich multiple CVEs from a vulnerability report using OpenRouter API.

        This method coordinates the enrichment workflow:
        1. Filters vulnerabilities by severity
        2. Enriches each CVE concurrently using ThreadPoolExecutor
        3. Collects and returns successful enrichments

        Args:
            vulnerabilities: List of vulnerability dictionaries from unified report
            max_cves: Maximum number of CVEs to enrich (None = all)
            severity_filter: List of severity levels to enrich (e.g., ["Critical", "High"])
                If None, defaults to ["Critical", "High"]

        Returns:
            Dictionary mapping CVE IDs to SimpleCVEEnrichment objects

        Raises:
            EnrichmentError: If enrichment fails catastrophically
        """
        if severity_filter is None:
            severity_filter = ["Critical", "High"]

        # Step 1: Filter vulnerabilities
        cves_to_enrich, skipped_by_severity = self._filter_vulnerabilities(vulnerabilities, max_cves, severity_filter)

        if not cves_to_enrich:
            logger.info("No CVEs to enrich after filtering")
            return {}

        logger.info(
            "Starting CVE enrichment",
            total_vulnerabilities=len(vulnerabilities),
            cves_to_enrich=len(cves_to_enrich),
            skipped_by_severity=skipped_by_severity,
            severity_filter=severity_filter,
            max_workers=self.max_workers,
        )

        enrichments: dict[str, SimpleCVEEnrichment] = {}
        failed_count = 0

        # Step 2: Enrich CVEs concurrently
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all enrichment tasks
                future_to_cve = {
                    executor.submit(self._enrich_single_cve, cve_id, cve_data): cve_id
                    for cve_id, cve_data in cves_to_enrich
                }

                # Process completed tasks
                for future in as_completed(future_to_cve):
                    cve_id = future_to_cve[future]
                    try:
                        result_cve_id, enrichment = future.result()
                        if enrichment:
                            enrichments[result_cve_id] = enrichment
                        else:
                            failed_count += 1
                    except Exception as e:
                        logger.error("Enrichment task failed", cve_id=cve_id, error=str(e))
                        failed_count += 1

        except Exception as e:
            logger.error("CVE enrichment failed", error=str(e))
            raise EnrichmentError(f"CVE enrichment failed: {e}") from e

        logger.info(
            "CVE enrichment complete",
            total_vulnerabilities=len(vulnerabilities),
            cves_to_enrich=len(cves_to_enrich),
            successful_enrichments=len(enrichments),
            failed_enrichments=failed_count,
            skipped_by_severity=skipped_by_severity,
            severity_filter=severity_filter,
        )

        return enrichments


__all__ = ["OpenRouterEnricher"]
