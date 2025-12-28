"""Abstract base classes and protocols for CVE enrichment providers.

This module defines the contracts that all enricher implementations must follow,
enabling a pluggable architecture where different AI providers can be used
interchangeably.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from .models import SimpleCVEEnrichment


@runtime_checkable
class Enricher(Protocol):
    """Protocol defining the contract for CVE enrichers.

    All enricher implementations must support this interface to be
    used interchangeably by the orchestrator. Using Protocol allows
    for structural subtyping (duck typing) rather than nominal subtyping.

    Example:
        >>> class MyEnricher:
        ...     @property`
        ...     def model(self) -> str:
        ...         return "my-model"
        ...
        ...     def enrich_report(
        ...         self,
        ...         vulnerabilities: list[dict[str, Any]],
        ...         max_cves: int | None = None,
        ...         severity_filter: list[str] | None = None,
        ...     ) -> dict[str, SimpleCVEEnrichment]:
        ...         return {}
        >>> isinstance(MyEnricher(), Enricher)
        True
    """

    @property
    def model(self) -> str:
        """Return the model identifier being used for enrichment.

        Returns:
            Model identifier string (e.g., "x-ai/grok-code-fast-1", "gpt-4o")
        """
        ...

    def enrich_report(
        self,
        vulnerabilities: list[dict[str, Any]],
        max_cves: int | None = None,
        severity_filter: list[str] | None = None,
    ) -> dict[str, SimpleCVEEnrichment]:
        """Enrich multiple CVEs from a vulnerability report.

        This is the primary method for enriching CVE data with AI-generated
        security context and mitigation strategies.

        Args:
            vulnerabilities: List of vulnerability dictionaries from unified report.
                Each dictionary should contain:
                - vulnerability_id: CVE identifier (e.g., "CVE-2024-12345")
                - vulnerability: Dict with severity, description, cvss, etc.
            max_cves: Maximum number of CVEs to enrich. If None, enriches all
                CVEs matching the severity filter.
            severity_filter: List of severity levels to include (e.g., ["Critical", "High"]).
                CVEs not matching these severities are skipped.

        Returns:
            Dictionary mapping CVE IDs to SimpleCVEEnrichment objects containing:
            - mitigation_summary: How UDS Core mitigates this CVE
            - impact_analysis: Potential impact without UDS Core controls
            - analysis_model: Model used for analysis
            - analysis_timestamp: When analysis was performed

        Raises:
            EnrichmentError: If enrichment fails due to API errors, timeouts, etc.
        """
        ...


class BaseEnricher(ABC):
    """Abstract base class for CVE enrichers with shared functionality.

    Provides common infrastructure like baseline context loading and
    prompt building while delegating provider-specific logic to subclasses.
    Extend this class to create new enricher implementations.

    Attributes:
        baseline_context: Loaded UDS Core security context documentation
        system_prompt: Built system prompt including baseline context

    Example:
        >>> class MyEnricher(BaseEnricher):
        ...     def __init__(self, api_key: str, model: str, **kwargs):
        ...         super().__init__(model=model)
        ...         self._api_key = api_key
        ...
        ...     def _build_system_prompt(self) -> str:
        ...         return f"Context: {self.baseline_context[:100]}..."
        ...
        ...     def enrich_report(self, vulnerabilities, **kwargs):
        ...         # Implementation here
        ...         return {}
    """

    def __init__(
        self,
        model: str,
        baseline_context_path: Path | None = None,
    ) -> None:
        """Initialize base enricher with model and baseline context.

        Args:
            model: AI model identifier to use for enrichment
            baseline_context_path: Optional path to custom baseline context file.
                If None, uses the default baseline_security_context.md from package.

        Raises:
            FileNotFoundError: If baseline context file not found
        """
        self._model = model
        self.baseline_context = self._load_baseline_context(baseline_context_path)
        self.system_prompt = self._build_system_prompt()

    @property
    def model(self) -> str:
        """Return the model identifier being used.

        Returns:
            Model identifier string
        """
        return self._model

    def _load_baseline_context(self, path: Path | None = None) -> str:
        """Load baseline security context from markdown file.

        The baseline context provides UDS Core security control documentation
        that informs the AI's analysis of CVE mitigations.

        Args:
            path: Optional custom path to baseline context file.
                If None, uses default baseline_security_context.md from package.

        Returns:
            Baseline security context as string

        Raises:
            FileNotFoundError: If baseline context file not found
        """
        if path is None:
            # Use default baseline context from package
            path = Path(__file__).parent / "baseline_security_context.md"

        if not path.exists():
            raise FileNotFoundError(f"Baseline context file not found: {path}")

        return path.read_text()

    @abstractmethod
    def _build_system_prompt(self) -> str:
        """Build system prompt with baseline security context.

        Subclasses must implement this to create a provider-specific
        system prompt that instructs the AI on how to analyze CVEs.

        Returns:
            Complete system prompt string including baseline context
        """
        ...

    @abstractmethod
    def enrich_report(
        self,
        vulnerabilities: list[dict[str, Any]],
        max_cves: int | None = None,
        severity_filter: list[str] | None = None,
    ) -> dict[str, SimpleCVEEnrichment]:
        """Enrich multiple CVEs from a vulnerability report.

        Subclasses must implement the actual enrichment logic using
        their specific AI provider.

        Args:
            vulnerabilities: List of vulnerability dictionaries
            max_cves: Maximum number of CVEs to enrich (None = all)
            severity_filter: List of severity levels to enrich

        Returns:
            Dictionary mapping CVE IDs to SimpleCVEEnrichment objects
        """
        ...


__all__ = [
    "Enricher",
    "BaseEnricher",
]
