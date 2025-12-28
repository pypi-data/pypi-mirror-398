"""Factory for creating enricher instances based on configuration.

This module implements the Factory pattern for creating enricher instances,
allowing the application to instantiate the appropriate enricher based on
configuration without depending on specific implementations.
"""

from ..core.logging import get_logger
from ..core.models import EnrichmentConfig
from .base import Enricher
from .exceptions import ConfigurationError

logger = get_logger(__name__)

# Registry of provider implementations
_providers: dict[str, type] = {}


def register_provider(name: str, provider_class: type) -> None:
    """Register a provider implementation.

    This function adds a provider to the registry, making it available
    for instantiation via the create_enricher function.

    Args:
        name: Provider name (e.g., 'openrouter', 'openai', 'mock')
        provider_class: Class implementing the Enricher protocol

    Example:
        >>> from my_module import MyCustomEnricher
        >>> register_provider("custom", MyCustomEnricher)
    """
    _providers[name] = provider_class
    logger.debug("Registered enrichment provider", provider=name)


def unregister_provider(name: str) -> None:
    """Unregister a provider implementation.

    Primarily useful for testing to clean up registered providers.

    Args:
        name: Provider name to unregister
    """
    if name in _providers:
        del _providers[name]
        logger.debug("Unregistered enrichment provider", provider=name)


def get_available_providers() -> list[str]:
    """Return list of registered provider names.

    Returns:
        List of provider name strings
    """
    return list(_providers.keys())


def create_enricher(config: EnrichmentConfig) -> Enricher:
    """Create an enricher instance based on configuration.

    This is the primary factory function for creating enricher instances.
    It looks up the appropriate provider class from the registry and
    instantiates it with the provided configuration.

    Args:
        config: Enrichment configuration containing provider, model,
            API key, and other settings.

    Returns:
        Configured enricher instance implementing the Enricher protocol

    Raises:
        ConfigurationError: If provider is not registered or config is invalid

    Example:
        >>> from cve_report_aggregator.core.models import EnrichmentConfig
        >>> config = EnrichmentConfig(
        ...     enabled=True,
        ...     provider="openrouter",
        ...     api_key="sk-...",
        ...     model="x-ai/grok-code-fast-1",
        ... )
        >>> enricher = create_enricher(config)
        >>> isinstance(enricher, Enricher)
        True
    """
    provider = config.provider

    if provider not in _providers:
        available = get_available_providers()
        raise ConfigurationError(
            f"Unknown enrichment provider: '{provider}'. Available providers: {available}",
            field="provider",
            value=provider,
        )

    if not config.api_key:
        raise ConfigurationError(
            f"API key required for provider '{provider}'. "
            "Set OPENROUTER_API_KEY environment variable or provide apiKey in configuration.",
            field="api_key",
        )

    provider_class = _providers[provider]

    logger.info(
        "Creating enricher",
        provider=provider,
        model=config.model,
    )

    return provider_class(
        api_key=config.api_key,
        model=config.model,
        reasoning_effort=config.reasoning_effort,
        verbosity=config.verbosity,
        max_completion_tokens=config.max_completion_tokens,
        seed=config.seed,
        metadata=config.metadata,
        max_workers=config.max_workers,
    )


class EnricherFactory:
    """Factory class for creating enricher instances.

    This class provides a class-based interface to the factory functions,
    which may be useful for dependency injection or when you need to
    pass the factory as an object.

    This is an alternative to the module-level functions and maintains
    the same functionality.

    Example:
        >>> factory = EnricherFactory()
        >>> enricher = factory.create(config)
    """

    @staticmethod
    def register(name: str, provider_class: type) -> None:
        """Register a provider implementation.

        Args:
            name: Provider name
            provider_class: Enricher class to instantiate
        """
        register_provider(name, provider_class)

    @staticmethod
    def unregister(name: str) -> None:
        """Unregister a provider implementation.

        Args:
            name: Provider name to unregister
        """
        unregister_provider(name)

    @staticmethod
    def available_providers() -> list[str]:
        """Return list of registered provider names."""
        return get_available_providers()

    @staticmethod
    def create(config: EnrichmentConfig) -> Enricher:
        """Create an enricher instance based on configuration.

        Args:
            config: Enrichment configuration

        Returns:
            Configured enricher instance

        Raises:
            ConfigurationError: If provider is not registered or config is invalid
        """
        return create_enricher(config)


def _register_default_providers() -> None:
    """Register default enricher providers.

    Called during module initialization to register built-in providers.
    This is a private function and should not be called directly.
    """
    # Import here to avoid circular imports
    from .providers.openrouter import OpenRouterEnricher

    register_provider("openrouter", OpenRouterEnricher)

    logger.debug("Registered default enrichment providers")


# Auto-register default providers on module import
_register_default_providers()


__all__ = [
    "EnricherFactory",
    "create_enricher",
    "register_provider",
    "unregister_provider",
    "get_available_providers",
]
