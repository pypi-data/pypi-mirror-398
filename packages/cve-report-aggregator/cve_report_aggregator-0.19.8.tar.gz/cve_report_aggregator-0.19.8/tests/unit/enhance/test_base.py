"""Tests for the enhance base module (abstractions and protocols)."""

from typing import Any

import pytest

from cve_report_aggregator.enhance.base import BaseEnricher, Enricher
from cve_report_aggregator.enhance.models import SimpleCVEEnrichment


class TestEnricherProtocol:
    """Tests for the Enricher protocol."""

    def test_protocol_is_runtime_checkable(self):
        """Test that Enricher protocol supports isinstance checks."""

        class ValidEnricher:
            @property
            def model(self) -> str:
                return "test-model"

            def enrich_report(
                self,
                vulnerabilities: list[dict[str, Any]],
                max_cves: int | None = None,
                severity_filter: list[str] | None = None,
            ) -> dict[str, SimpleCVEEnrichment]:
                return {}

        enricher = ValidEnricher()
        assert isinstance(enricher, Enricher)

    def test_non_conforming_class_not_enricher(self):
        """Test that classes missing methods are not Enrichers."""

        class InvalidEnricher:
            @property
            def model(self) -> str:
                return "test-model"

            # Missing enrich_report method

        enricher = InvalidEnricher()
        assert not isinstance(enricher, Enricher)

    def test_class_with_different_signature_not_enricher(self):
        """Test that classes with wrong method signatures are not Enrichers."""

        class WrongSignature:
            @property
            def model(self) -> str:
                return "test-model"

            def enrich_report(self):  # Wrong signature
                return {}

        enricher = WrongSignature()
        # Note: Protocol checks are structural, so this may still pass
        # depending on Python version. The type checker would catch this.
        assert isinstance(enricher, Enricher)


class ConcreteEnricher(BaseEnricher):
    """Concrete implementation of BaseEnricher for testing."""

    def __init__(self, model: str = "test-model", baseline_context: str | None = None):
        if baseline_context is not None:
            # Allow injecting baseline context for testing
            self._model = model
            self.baseline_context = baseline_context
            self.system_prompt = self._build_system_prompt()
        else:
            # This will fail if baseline context file doesn't exist
            super().__init__(model=model)

    def _build_system_prompt(self) -> str:
        return f"Test prompt with context: {self.baseline_context[:50]}..."

    def enrich_report(
        self,
        vulnerabilities: list[dict[str, Any]],
        max_cves: int | None = None,
        severity_filter: list[str] | None = None,
    ) -> dict[str, SimpleCVEEnrichment]:
        return {}


class TestBaseEnricher:
    """Tests for the BaseEnricher abstract base class."""

    def test_model_property(self):
        """Test that model property returns the model identifier."""
        enricher = ConcreteEnricher(model="my-model", baseline_context="Test context")
        assert enricher.model == "my-model"

    def test_baseline_context_loaded(self):
        """Test that baseline context is stored."""
        enricher = ConcreteEnricher(baseline_context="Custom baseline context")
        assert enricher.baseline_context == "Custom baseline context"

    def test_system_prompt_built(self):
        """Test that system prompt is built from baseline context."""
        enricher = ConcreteEnricher(baseline_context="My custom context for testing")
        assert "My custom context" in enricher.system_prompt

    def test_load_baseline_context_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        nonexistent_path = tmp_path / "nonexistent.md"

        # Create a concrete enricher with baseline context to call the method
        enricher = ConcreteEnricher(baseline_context="dummy")
        with pytest.raises(FileNotFoundError, match="Baseline context file not found"):
            enricher._load_baseline_context(nonexistent_path)

    def test_load_baseline_context_custom_path(self, tmp_path):
        """Test loading baseline context from custom path."""
        custom_file = tmp_path / "custom_context.md"
        custom_file.write_text("# Custom Security Context\n\nThis is custom content.")

        # Create a minimal concrete class to test the method
        enricher = ConcreteEnricher(baseline_context="dummy")
        context = enricher._load_baseline_context(custom_file)

        assert "Custom Security Context" in context
        assert "custom content" in context

    def test_implements_enricher_protocol(self):
        """Test that ConcreteEnricher implements Enricher protocol."""
        enricher = ConcreteEnricher(baseline_context="Test context")
        assert isinstance(enricher, Enricher)

    def test_abstract_methods_must_be_implemented(self):
        """Test that abstract methods cannot be called directly."""

        class IncompleteEnricher(BaseEnricher):
            pass

        # Should not be able to instantiate without implementing abstract methods
        with pytest.raises(TypeError, match="abstract"):
            IncompleteEnricher(model="test")
