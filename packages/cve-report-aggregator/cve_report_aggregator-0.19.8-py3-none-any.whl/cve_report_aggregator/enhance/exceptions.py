"""Exceptions for the enhance module.

This module defines a hierarchy of exceptions specific to CVE enrichment,
enabling fine-grained error handling and clear error messages.
"""


class EnrichmentError(Exception):
    """Base exception for all enrichment-related errors.

    This is the parent class for all exceptions in the enhance module.
    Catching this exception will catch all enrichment-related errors.

    Example:
        >>> try:
        ...     enricher.enrich_report(vulnerabilities)
        ... except EnrichmentError as e:
        ...     logger.error(f"Enrichment failed: {e}")
    """

    pass


class ProviderError(EnrichmentError):
    """Error communicating with AI provider.

    Raised when there are network issues, API errors, or unexpected
    responses from the AI provider (e.g., OpenRouter, OpenAI).

    Attributes:
        provider: Name of the provider that failed
        status_code: HTTP status code if applicable
        response: Raw response content if available
    """

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        status_code: int | None = None,
        response: str | None = None,
    ) -> None:
        """Initialize provider error with details.

        Args:
            message: Human-readable error message
            provider: Name of the provider (e.g., "openrouter")
            status_code: HTTP status code if applicable
            response: Raw response content for debugging
        """
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code
        self.response = response


class ModelValidationError(EnrichmentError):
    """Invalid or unavailable model specified.

    Raised when the requested AI model is not available from the
    provider or the model name format is invalid.

    Attributes:
        model: The model that was requested
        available_models: List of available models if known
    """

    def __init__(
        self,
        message: str,
        model: str | None = None,
        available_models: list[str] | None = None,
    ) -> None:
        """Initialize model validation error with details.

        Args:
            message: Human-readable error message
            model: The model that was requested
            available_models: List of available models for reference
        """
        super().__init__(message)
        self.model = model
        self.available_models = available_models or []


class BatchTimeoutError(EnrichmentError):
    """Batch processing exceeded timeout.

    Raised when a batch enrichment job takes longer than the
    configured timeout period to complete.

    Attributes:
        batch_id: ID of the batch job that timed out
        elapsed_seconds: How long the job ran before timeout
        timeout_seconds: The configured timeout limit
    """

    def __init__(
        self,
        message: str,
        batch_id: str | None = None,
        elapsed_seconds: float | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        """Initialize batch timeout error with details.

        Args:
            message: Human-readable error message
            batch_id: ID of the batch job
            elapsed_seconds: Time elapsed before timeout
            timeout_seconds: Configured timeout limit
        """
        super().__init__(message)
        self.batch_id = batch_id
        self.elapsed_seconds = elapsed_seconds
        self.timeout_seconds = timeout_seconds


class ConfigurationError(EnrichmentError):
    """Invalid enrichment configuration.

    Raised when the enrichment configuration is invalid, such as
    missing API keys, invalid provider names, or incompatible options.

    Attributes:
        field: Configuration field that caused the error
        value: The invalid value that was provided
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: str | None = None,
    ) -> None:
        """Initialize configuration error with details.

        Args:
            message: Human-readable error message
            field: Configuration field name
            value: The invalid value
        """
        super().__init__(message)
        self.field = field
        self.value = value


class ParseError(EnrichmentError):
    """Error parsing AI response content.

    Raised when the AI provider returns a response that cannot be
    parsed as expected (e.g., invalid JSON, missing fields).

    Attributes:
        content: The content that failed to parse
        expected_format: Description of expected format
    """

    def __init__(
        self,
        message: str,
        content: str | None = None,
        expected_format: str | None = None,
    ) -> None:
        """Initialize parse error with details.

        Args:
            message: Human-readable error message
            content: The content that failed to parse (truncated if long)
            expected_format: Description of what was expected
        """
        super().__init__(message)
        # Truncate content for logging
        self.content = content[:500] if content and len(content) > 500 else content
        self.expected_format = expected_format


__all__ = [
    "EnrichmentError",
    "ProviderError",
    "ModelValidationError",
    "BatchTimeoutError",
    "ConfigurationError",
    "ParseError",
]
