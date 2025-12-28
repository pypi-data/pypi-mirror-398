"""CVE enrichment module for adding security context and mitigation strategies using AI providers.

This module provides a pluggable architecture for enriching CVE data with AI-generated
security context and mitigation strategies. It supports multiple AI providers through
a factory pattern, enabling easy extension and testing.

Quick Start:
    >>> from cve_report_aggregator.enhance import create_enricher
    >>> from cve_report_aggregator.core.models import EnrichmentConfig
    >>>
    >>> config = EnrichmentConfig(
    ...     enabled=True,
    ...     provider="openrouter",
    ...     api_key="sk-or-v1-...",
    ...     model="x-ai/grok-code-fast-1",
    ... )
    >>> enricher = create_enricher(config)
    >>> enrichments = enricher.enrich_report(vulnerabilities)

Architecture:
    - Enricher (Protocol): Defines the contract for all enrichers
    - BaseEnricher (ABC): Provides shared functionality for enrichers
    - EnricherFactory: Creates enricher instances based on configuration
    - Providers: Concrete implementations (OpenRouterEnricher, MockEnricher)

Providers:
    - openrouter: Uses OpenRouter Batch API for CVE enrichment (production)
    - mock: Returns predictable results for testing (not registered by default)
"""

# Abstract base classes and protocols
from .base import BaseEnricher, Enricher

# Exceptions
from .exceptions import (
    BatchTimeoutError,
    ConfigurationError,
    EnrichmentError,
    ModelValidationError,
    ParseError,
    ProviderError,
)

# Factory for creating enrichers
from .factory import EnricherFactory, create_enricher, get_available_providers, register_provider, unregister_provider

# Data models
from .models import (
    CVEEnrichment,
    MitigationStrategy,
    NetworkPolicyAnalysis,
    PeprPolicyAnalysis,
    SecurityContextAnalysis,
    SeverityLevel,
    SimpleCVEEnrichment,
)

# Concrete providers (for direct instantiation if needed)
from .providers.mock import MockEnricher
from .providers.openrouter import OpenRouterEnricher

__all__ = [
    # Protocol and base class
    "Enricher",
    "BaseEnricher",
    # Factory
    "EnricherFactory",
    "create_enricher",
    "register_provider",
    "unregister_provider",
    "get_available_providers",
    # Exceptions
    "EnrichmentError",
    "ProviderError",
    "ModelValidationError",
    "BatchTimeoutError",
    "ConfigurationError",
    "ParseError",
    # Data models
    "CVEEnrichment",
    "MitigationStrategy",
    "NetworkPolicyAnalysis",
    "PeprPolicyAnalysis",
    "SecurityContextAnalysis",
    "SeverityLevel",
    "SimpleCVEEnrichment",
    # Providers
    "OpenRouterEnricher",
    "MockEnricher",
]
