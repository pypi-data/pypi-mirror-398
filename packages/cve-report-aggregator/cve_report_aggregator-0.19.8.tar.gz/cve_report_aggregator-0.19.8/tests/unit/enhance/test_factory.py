"""Tests for the enhance factory module."""

from typing import Any
from unittest.mock import Mock, patch

import pytest

from cve_report_aggregator.core.models import EnrichmentConfig
from cve_report_aggregator.enhance.base import Enricher
from cve_report_aggregator.enhance.exceptions import ConfigurationError
from cve_report_aggregator.enhance.factory import (
    EnricherFactory,
    _providers,
    create_enricher,
    get_available_providers,
    register_provider,
    unregister_provider,
)
from cve_report_aggregator.enhance.models import SimpleCVEEnrichment


class DummyEnricher:
    """Dummy enricher for testing factory registration."""

    def __init__(
        self,
        api_key: str,
        model: str,
        reasoning_effort: str = "medium",
        verbosity: str = "medium",
        max_completion_tokens: int | None = None,
        seed: int | None = None,
        metadata: dict[str, str] | None = None,
        max_workers: int = 5,
    ):
        self._api_key = api_key
        self._model = model
        self.reasoning_effort = reasoning_effort
        self.verbosity = verbosity
        self.max_completion_tokens = max_completion_tokens
        self.seed = seed
        self.metadata = metadata
        self.max_workers = max_workers

    @property
    def model(self) -> str:
        return self._model

    def enrich_report(
        self,
        vulnerabilities: list[dict[str, Any]],
        max_cves: int | None = None,
        severity_filter: list[str] | None = None,
    ) -> dict[str, SimpleCVEEnrichment]:
        return {}


class TestRegisterProvider:
    """Tests for provider registration functions."""

    def test_register_provider(self):
        """Test registering a new provider."""
        # Ensure provider doesn't exist before registration
        if "dummy" in _providers:
            unregister_provider("dummy")

        register_provider("dummy", DummyEnricher)
        assert "dummy" in _providers
        assert _providers["dummy"] is DummyEnricher

        # Cleanup
        unregister_provider("dummy")

    def test_unregister_provider(self):
        """Test unregistering a provider."""
        register_provider("to_remove", DummyEnricher)
        assert "to_remove" in _providers

        unregister_provider("to_remove")
        assert "to_remove" not in _providers

    def test_unregister_nonexistent_provider(self):
        """Test unregistering a non-existent provider (should not raise)."""
        unregister_provider("nonexistent_provider")  # Should not raise

    def test_get_available_providers(self):
        """Test getting list of available providers."""
        providers = get_available_providers()

        # Default providers should be registered
        assert "openrouter" in providers
        assert isinstance(providers, list)


class TestCreateEnricher:
    """Tests for the create_enricher function."""

    def test_create_enricher_with_valid_config(self):
        """Test creating enricher with valid configuration."""
        # Register a dummy provider for testing, using a valid provider name
        # that's already allowed by the config validation
        original_provider = _providers.get("openrouter")
        register_provider("openrouter", DummyEnricher)

        config = EnrichmentConfig(
            enabled=True,
            provider="openrouter",
            api_key="test-api-key",
            model="x-ai/test-model",
        )

        enricher = create_enricher(config)

        assert isinstance(enricher, DummyEnricher)
        assert enricher.model == "x-ai/test-model"

        # Restore original provider
        if original_provider:
            register_provider("openrouter", original_provider)

    def test_create_enricher_unknown_provider(self):
        """Test that unknown provider raises ConfigurationError."""
        # Temporarily unregister a provider to test unknown provider handling
        original_provider = _providers.get("openrouter")
        unregister_provider("openrouter")

        config = EnrichmentConfig(
            enabled=True,
            provider="openrouter",
            api_key="test-key",
            model="x-ai/test-model",
        )

        try:
            with pytest.raises(ConfigurationError, match="Unknown enrichment provider"):
                create_enricher(config)
        finally:
            # Restore original provider
            if original_provider:
                register_provider("openrouter", original_provider)

    def test_create_enricher_missing_api_key(self):
        """Test that missing API key raises ConfigurationError."""
        original_provider = _providers.get("openrouter")
        register_provider("openrouter", DummyEnricher)

        config = EnrichmentConfig(
            enabled=True,
            provider="openrouter",
            api_key=None,
            model="x-ai/test-model",
        )

        try:
            with pytest.raises(ConfigurationError, match="API key required"):
                create_enricher(config)
        finally:
            if original_provider:
                register_provider("openrouter", original_provider)

    def test_create_enricher_passes_all_config_options(self):
        """Test that all configuration options are passed to enricher."""
        original_provider = _providers.get("openrouter")
        register_provider("openrouter", DummyEnricher)

        config = EnrichmentConfig(
            enabled=True,
            provider="openrouter",
            api_key="test-key",
            model="x-ai/custom-model",
            reasoning_effort="high",
            verbosity="low",
            max_completion_tokens=2048,
            seed=42,
            metadata={"key": "value"},
            max_workers=10,
        )

        try:
            enricher = create_enricher(config)

            assert enricher.model == "x-ai/custom-model"
            # Cast to DummyEnricher to check provider-specific attributes
            assert isinstance(enricher, DummyEnricher)
            assert enricher.reasoning_effort == "high"
            assert enricher.verbosity == "low"
            assert enricher.max_completion_tokens == 2048
            assert enricher.seed == 42
            assert enricher.metadata == {"key": "value"}
            assert enricher.max_workers == 10
        finally:
            if original_provider:
                register_provider("openrouter", original_provider)

    def test_create_enricher_openrouter_provider(self):
        """Test creating OpenRouter enricher (mocked)."""
        with patch("cve_report_aggregator.enhance.providers.openrouter.OpenRouter") as mock_openrouter:
            mock_client = Mock()
            mock_model = Mock()
            mock_model.id = "x-ai/grok-code-fast-1"
            mock_models_response = Mock()
            mock_models_response.data = [mock_model]
            mock_client.models.list.return_value = mock_models_response
            mock_openrouter.return_value = mock_client

            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.read_text", return_value="# Baseline context"):
                    config = EnrichmentConfig(
                        enabled=True,
                        provider="openrouter",
                        api_key="test-key",
                        model="x-ai/grok-code-fast-1",
                    )

                    enricher = create_enricher(config)
                    assert isinstance(enricher, Enricher)


class TestEnricherFactory:
    """Tests for the EnricherFactory class (class-based interface)."""

    def test_factory_register(self):
        """Test factory class registration method."""
        if "factory_test" in _providers:
            EnricherFactory.unregister("factory_test")

        EnricherFactory.register("factory_test", DummyEnricher)
        assert "factory_test" in _providers

        EnricherFactory.unregister("factory_test")

    def test_factory_unregister(self):
        """Test factory class unregistration method."""
        EnricherFactory.register("to_remove_factory", DummyEnricher)
        EnricherFactory.unregister("to_remove_factory")
        assert "to_remove_factory" not in _providers

    def test_factory_available_providers(self):
        """Test factory class available_providers method."""
        providers = EnricherFactory.available_providers()
        assert "openrouter" in providers
        assert isinstance(providers, list)

    def test_factory_create(self):
        """Test factory class create method."""
        original_provider = _providers.get("openrouter")
        EnricherFactory.register("openrouter", DummyEnricher)

        config = EnrichmentConfig(
            enabled=True,
            provider="openrouter",
            api_key="test-key",
            model="x-ai/test-model",
        )

        try:
            enricher = EnricherFactory.create(config)
            assert isinstance(enricher, DummyEnricher)
        finally:
            if original_provider:
                EnricherFactory.register("openrouter", original_provider)

    def test_factory_create_error_handling(self):
        """Test factory class error handling."""
        # Temporarily unregister providers to test error handling
        original_provider = _providers.get("openrouter")
        EnricherFactory.unregister("openrouter")

        config = EnrichmentConfig(
            enabled=True,
            provider="openrouter",
            api_key="test-key",
            model="x-ai/test-model",
        )

        try:
            with pytest.raises(ConfigurationError):
                EnricherFactory.create(config)
        finally:
            if original_provider:
                EnricherFactory.register("openrouter", original_provider)
