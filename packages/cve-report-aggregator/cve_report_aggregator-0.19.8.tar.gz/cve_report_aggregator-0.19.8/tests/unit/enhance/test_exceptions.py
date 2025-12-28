"""Tests for the enhance exceptions module."""

import pytest

from cve_report_aggregator.enhance.exceptions import (
    BatchTimeoutError,
    ConfigurationError,
    EnrichmentError,
    ModelValidationError,
    ParseError,
    ProviderError,
)


class TestEnrichmentError:
    """Tests for base EnrichmentError."""

    def test_is_exception(self):
        """Test that EnrichmentError is an Exception."""
        assert issubclass(EnrichmentError, Exception)

    def test_message_preserved(self):
        """Test that error message is preserved."""
        error = EnrichmentError("Test error message")
        assert str(error) == "Test error message"

    def test_can_be_raised_and_caught(self):
        """Test that EnrichmentError can be raised and caught."""
        with pytest.raises(EnrichmentError):
            raise EnrichmentError("Test")


class TestProviderError:
    """Tests for ProviderError."""

    def test_inherits_from_enrichment_error(self):
        """Test that ProviderError inherits from EnrichmentError."""
        assert issubclass(ProviderError, EnrichmentError)

    def test_basic_initialization(self):
        """Test basic initialization with just message."""
        error = ProviderError("Connection failed")
        assert str(error) == "Connection failed"
        assert error.provider is None
        assert error.status_code is None
        assert error.response is None

    def test_full_initialization(self):
        """Test initialization with all attributes."""
        error = ProviderError(
            "API error occurred",
            provider="openrouter",
            status_code=429,
            response='{"error": "rate_limit"}',
        )
        assert error.provider == "openrouter"
        assert error.status_code == 429
        assert error.response == '{"error": "rate_limit"}'

    def test_can_be_caught_as_enrichment_error(self):
        """Test that ProviderError can be caught as EnrichmentError."""
        with pytest.raises(EnrichmentError):
            raise ProviderError("Test")


class TestModelValidationError:
    """Tests for ModelValidationError."""

    def test_inherits_from_enrichment_error(self):
        """Test that ModelValidationError inherits from EnrichmentError."""
        assert issubclass(ModelValidationError, EnrichmentError)

    def test_basic_initialization(self):
        """Test basic initialization with just message."""
        error = ModelValidationError("Model not found")
        assert str(error) == "Model not found"
        assert error.model is None
        assert error.available_models == []

    def test_full_initialization(self):
        """Test initialization with all attributes."""
        error = ModelValidationError(
            "Model 'gpt-99' is not available",
            model="gpt-99",
            available_models=["gpt-4", "gpt-3.5-turbo", "claude-3"],
        )
        assert error.model == "gpt-99"
        assert "gpt-4" in error.available_models
        assert len(error.available_models) == 3


class TestBatchTimeoutError:
    """Tests for BatchTimeoutError."""

    def test_inherits_from_enrichment_error(self):
        """Test that BatchTimeoutError inherits from EnrichmentError."""
        assert issubclass(BatchTimeoutError, EnrichmentError)

    def test_basic_initialization(self):
        """Test basic initialization with just message."""
        error = BatchTimeoutError("Batch timed out")
        assert str(error) == "Batch timed out"
        assert error.batch_id is None
        assert error.elapsed_seconds is None
        assert error.timeout_seconds is None

    def test_full_initialization(self):
        """Test initialization with all attributes."""
        error = BatchTimeoutError(
            "Batch exceeded 24 hour timeout",
            batch_id="batch-abc123",
            elapsed_seconds=86401.5,
            timeout_seconds=86400.0,
        )
        assert error.batch_id == "batch-abc123"
        assert error.elapsed_seconds == 86401.5
        assert error.timeout_seconds == 86400.0


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_inherits_from_enrichment_error(self):
        """Test that ConfigurationError inherits from EnrichmentError."""
        assert issubclass(ConfigurationError, EnrichmentError)

    def test_basic_initialization(self):
        """Test basic initialization with just message."""
        error = ConfigurationError("Invalid configuration")
        assert str(error) == "Invalid configuration"
        assert error.field is None
        assert error.value is None

    def test_full_initialization(self):
        """Test initialization with all attributes."""
        error = ConfigurationError(
            "Invalid provider specified",
            field="provider",
            value="invalid_provider",
        )
        assert error.field == "provider"
        assert error.value == "invalid_provider"


class TestParseError:
    """Tests for ParseError."""

    def test_inherits_from_enrichment_error(self):
        """Test that ParseError inherits from EnrichmentError."""
        assert issubclass(ParseError, EnrichmentError)

    def test_basic_initialization(self):
        """Test basic initialization with just message."""
        error = ParseError("Invalid JSON response")
        assert str(error) == "Invalid JSON response"
        assert error.content is None
        assert error.expected_format is None

    def test_full_initialization(self):
        """Test initialization with all attributes."""
        error = ParseError(
            "Failed to parse response as JSON",
            content="Not valid JSON at all",
            expected_format="SimpleCVEEnrichment JSON",
        )
        assert error.content == "Not valid JSON at all"
        assert error.expected_format == "SimpleCVEEnrichment JSON"

    def test_content_truncation(self):
        """Test that long content is truncated to 500 characters."""
        long_content = "x" * 1000
        error = ParseError("Parse failed", content=long_content)
        assert error.content is not None
        assert len(error.content) == 500
        assert error.content == "x" * 500

    def test_short_content_not_truncated(self):
        """Test that short content is not truncated."""
        short_content = "Short content"
        error = ParseError("Parse failed", content=short_content)
        assert error.content == short_content
        assert len(error.content) == len(short_content)


class TestExceptionHierarchy:
    """Tests for exception hierarchy and catching behavior."""

    def test_all_exceptions_inherit_from_enrichment_error(self):
        """Test that all exceptions inherit from EnrichmentError."""
        exceptions = [
            ProviderError,
            ModelValidationError,
            BatchTimeoutError,
            ConfigurationError,
            ParseError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, EnrichmentError), f"{exc_class.__name__} should inherit from EnrichmentError"

    def test_catch_all_with_enrichment_error(self):
        """Test that all specific exceptions can be caught with EnrichmentError."""
        exceptions = [
            ProviderError("test"),
            ModelValidationError("test"),
            BatchTimeoutError("test"),
            ConfigurationError("test"),
            ParseError("test"),
        ]

        for exc in exceptions:
            with pytest.raises(EnrichmentError):
                raise exc

    def test_specific_exceptions_distinguishable(self):
        """Test that specific exceptions can be distinguished."""

        def raise_provider_error():
            raise ProviderError("Provider issue")

        def raise_config_error():
            raise ConfigurationError("Config issue")

        # Catch specific exception
        with pytest.raises(ProviderError):
            raise_provider_error()

        # Different exception should not match
        with pytest.raises(ConfigurationError):
            raise_config_error()

        # Provider error should not be caught as ConfigurationError
        try:
            raise_provider_error()
        except ConfigurationError:
            pytest.fail("ProviderError should not be caught as ConfigurationError")
        except ProviderError:
            pass  # Expected
