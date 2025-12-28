"""Mock enricher for testing purposes.

This module provides a MockEnricher class that returns predictable results
for testing without making actual API calls.
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..base import BaseEnricher
from ..models import SimpleCVEEnrichment


class MockEnricher(BaseEnricher):
    """Mock enricher that returns predictable results for testing.

    This enricher does not make any API calls and returns deterministic
    results based on the input vulnerabilities. Useful for:
    - Unit testing
    - Integration testing without API costs
    - Development and debugging

    Attributes:
        enrichment_calls: List of all calls made to enrich_report for inspection

    Example:
        >>> enricher = MockEnricher(api_key="test-key")
        >>> result = enricher.enrich_report([
        ...     {"vulnerability_id": "CVE-2024-12345", "vulnerability": {"severity": "Critical"}}
        ... ])
        >>> assert "CVE-2024-12345" in result
        >>> assert enricher.enrichment_calls[0]["vulnerabilities"][0]["vulnerability_id"] == "CVE-2024-12345"
    """

    def __init__(
        self,
        api_key: str = "mock-api-key",
        model: str = "mock-model",
        reasoning_effort: str = "medium",
        verbosity: str = "medium",
        max_completion_tokens: int | None = None,
        seed: int | None = None,
        metadata: dict[str, str] | None = None,
        baseline_context_path: Path | None = None,
        max_workers: int = 5,
        **kwargs: Any,
    ) -> None:
        """Initialize mock enricher.

        All parameters mirror OpenRouterEnricher for compatibility,
        but most are ignored for mock operation.

        Args:
            api_key: Mock API key (not used)
            model: Model identifier to report in enrichments
            reasoning_effort: Ignored for mock
            verbosity: Ignored for mock
            max_completion_tokens: Ignored for mock
            seed: Ignored for mock
            metadata: Ignored for mock
            baseline_context_path: Path to baseline context (uses mock if not found)
            max_workers: Ignored for mock
            **kwargs: Additional arguments ignored
        """
        self._model = model
        self.reasoning_effort = reasoning_effort
        self.verbosity = verbosity
        self.max_completion_tokens = max_completion_tokens
        self.seed = seed
        self.metadata = metadata
        self.max_workers = max_workers

        # Track calls for test assertions
        self.enrichment_calls: list[dict[str, Any]] = []

        # Try to load baseline context, use mock if not available
        try:
            self.baseline_context = self._load_baseline_context(baseline_context_path)
        except FileNotFoundError:
            self.baseline_context = "Mock baseline security context for testing."

        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build mock system prompt.

        Returns:
            Mock system prompt for testing
        """
        return f"""Mock system prompt for testing.

Baseline Context (truncated):
{self.baseline_context[:200]}...

This is a mock enricher and does not make actual API calls."""

    def enrich_report(
        self,
        vulnerabilities: list[dict[str, Any]],
        max_cves: int | None = None,
        severity_filter: list[str] | None = None,
    ) -> dict[str, SimpleCVEEnrichment]:
        """Return mock enrichments for testing.

        Generates predictable enrichment data for each vulnerability
        that passes the severity filter.

        Args:
            vulnerabilities: List of vulnerability dictionaries
            max_cves: Maximum number of CVEs to enrich (None = all)
            severity_filter: List of severity levels to include.
                Defaults to ["Critical", "High"] if None.

        Returns:
            Dictionary mapping CVE IDs to SimpleCVEEnrichment objects
        """
        # Track the call for test assertions
        self.enrichment_calls.append(
            {
                "vulnerabilities": vulnerabilities,
                "max_cves": max_cves,
                "severity_filter": severity_filter,
            }
        )

        if severity_filter is None:
            severity_filter = ["Critical", "High"]

        enrichments: dict[str, SimpleCVEEnrichment] = {}

        for vuln in vulnerabilities:
            cve_id = vuln.get("vulnerability_id")
            if not cve_id:
                continue

            severity = vuln.get("vulnerability", {}).get("severity", "Unknown")
            if severity_filter and severity not in severity_filter:
                continue

            if max_cves and len(enrichments) >= max_cves:
                break

            # Generate deterministic mock enrichment
            enrichments[cve_id] = SimpleCVEEnrichment(
                cve_id=cve_id,
                mitigation_summary=(
                    f"UDS helps to mitigate {cve_id} by enforcing NetworkPolicies that restrict "
                    f"network access and Pepr admission policies that prevent insecure configurations."
                ),
                impact_analysis=(
                    f"Without UDS Core controls, {cve_id} could allow attackers to exploit this "
                    f"{severity.lower()} severity vulnerability. The blast radius could extend to "
                    f"other workloads in the cluster through lateral movement."
                ),
                analysis_model=self._model,
                analysis_timestamp=datetime.now(UTC).isoformat(),
            )

        return enrichments

    def reset_calls(self) -> None:
        """Reset the enrichment calls history.

        Useful for clearing state between tests.
        """
        self.enrichment_calls = []


__all__ = ["MockEnricher"]
