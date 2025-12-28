"""Enricher provider implementations.

This package contains concrete implementations of the Enricher protocol
for different AI providers.

Available Providers:
    - OpenRouterEnricher: Uses OpenRouter API for CVE enrichment
    - MockEnricher: Returns predictable results for testing
"""

from .mock import MockEnricher
from .openrouter import OpenRouterEnricher

__all__ = [
    "OpenRouterEnricher",
    "MockEnricher",
]
