"""Comprehensive tests for AppContext class."""

from pathlib import Path

import pytest

from cve_report_aggregator.context import AppContext
from cve_report_aggregator.core.models import AggregatorConfig


@pytest.fixture
def base_config(tmp_path: Path) -> AggregatorConfig:
    """Create a base configuration for testing.

    Args:
        tmp_path: Pytest temporary directory

    Returns:
        AggregatorConfig instance
    """
    input_dir = tmp_path / "reports"
    input_dir.mkdir()
    return AggregatorConfig(
        input_dir=input_dir,
        output_file=tmp_path / "output.json",
        scanner="grype",
        mode="highest-score",
        log_level="INFO",
    )


class TestAppContextInitialization:
    """Tests for AppContext initialization."""

    def test_init_basic(self, base_config: AggregatorConfig):
        """Test basic context initialization."""
        context = AppContext(base_config)

        assert context.config == base_config
        assert context.error_handler is not None
        assert context.config.log_level == "INFO"

    def test_init_with_debug_logging(self, tmp_path: Path):
        """Test context initialization with DEBUG logging."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()
        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
            log_level="DEBUG",
        )
        context = AppContext(config)

        assert context.config.log_level == "DEBUG"

    def test_error_handler_not_singleton(self, base_config: AggregatorConfig):
        """Test that error handler is not a singleton (each context gets its own)."""
        context1 = AppContext(base_config)
        context2 = AppContext(base_config)

        # Different error handler instances
        assert context1.error_handler is not context2.error_handler


class TestGetLogger:
    """Tests for get_logger method."""

    def test_get_logger_default(self, base_config: AggregatorConfig):
        """Test getting logger with default parameters."""
        context = AppContext(base_config)

        logger = context.get_logger()

        assert logger is not None
        # Logger should be callable
        logger.info("Test message")

    def test_get_logger_with_name(self, base_config: AggregatorConfig):
        """Test getting logger with module name."""
        context = AppContext(base_config)

        logger = context.get_logger(__name__)

        assert logger is not None
        logger.info("Test message with name")

    def test_get_logger_with_context(self, base_config: AggregatorConfig):
        """Test getting logger with bound context."""
        context = AppContext(base_config)

        logger = context.get_logger(__name__, package="test-package", version="1.0.0")

        assert logger is not None
        # Bound context should be included in logs
        logger.info("Test message with context")

    def test_get_logger_multiple_calls(self, base_config: AggregatorConfig):
        """Test multiple logger retrievals."""
        context = AppContext(base_config)

        logger1 = context.get_logger("module1")
        logger2 = context.get_logger("module2")
        logger3 = context.get_logger("module1")

        # All loggers should be valid
        assert logger1 is not None
        assert logger2 is not None
        assert logger3 is not None


class TestWithConfig:
    """Tests for with_config method."""

    def test_with_config_single_update(self, base_config: AggregatorConfig):
        """Test updating single configuration field."""
        original_context = AppContext(base_config)

        # Update log level
        debug_context = original_context.with_config(log_level="DEBUG")

        # Original context unchanged
        assert original_context.config.log_level == "INFO"
        # New context has updated value
        assert debug_context.config.log_level == "DEBUG"
        # Other fields remain the same
        assert debug_context.config.scanner == base_config.scanner
        assert debug_context.config.mode == base_config.mode

    def test_with_config_multiple_updates(self, base_config: AggregatorConfig):
        """Test updating multiple configuration fields."""
        original_context = AppContext(base_config)

        # Update multiple fields
        new_context = original_context.with_config(
            log_level="DEBUG",
            scanner="trivy",
            mode="first-occurrence",
        )

        # Original unchanged
        assert original_context.config.log_level == "INFO"
        assert original_context.config.scanner == "grype"
        assert original_context.config.mode == "highest-score"

        # New context has updates
        assert new_context.config.log_level == "DEBUG"
        assert new_context.config.scanner == "trivy"
        assert new_context.config.mode == "first-occurrence"

    def test_with_config_invalid_field(self, base_config: AggregatorConfig):
        """Test that invalid fields are silently ignored."""
        original_context = AppContext(base_config)

        # Try to update non-existent field
        new_context = original_context.with_config(nonexistent_field="value")

        # Should create new context without error
        assert new_context is not None
        assert new_context.config == original_context.config

    def test_with_config_deep_copy(self, base_config: AggregatorConfig):
        """Test that with_config creates a deep copy."""
        original_context = AppContext(base_config)

        # Create new context
        new_context = original_context.with_config(log_level="DEBUG")

        # Modify original config (shouldn't affect new context)
        original_context.config.log_level = "CRITICAL"

        # New context should still have DEBUG
        assert new_context.config.log_level == "DEBUG"

    def test_with_config_preserves_complex_fields(self, tmp_path: Path):
        """Test that complex configuration fields are properly copied."""
        from cve_report_aggregator.core.models import PackageConfig

        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
            download_remote_packages=True,
            registry="registry.example.com",
            organization="test-org",
            packages=[
                PackageConfig(name="pkg1", version="1.0.0", architecture="amd64"),
                PackageConfig(name="pkg2", version="2.0.0", architecture="arm64"),
            ],
        )

        original_context = AppContext(config)
        new_context = original_context.with_config(log_level="DEBUG")

        # Complex fields should be preserved
        assert new_context.config.download_remote_packages is True
        assert new_context.config.registry == "registry.example.com"
        assert new_context.config.organization == "test-org"
        assert len(new_context.config.packages) == 2
        assert new_context.config.packages[0].name == "pkg1"

    def test_with_config_chain_updates(self, base_config: AggregatorConfig):
        """Test chaining multiple with_config calls."""
        original_context = AppContext(base_config)

        # Chain multiple updates
        final_context = (
            original_context.with_config(log_level="DEBUG")
            .with_config(scanner="trivy")
            .with_config(mode="first-occurrence")
        )

        # Original unchanged
        assert original_context.config.log_level == "INFO"
        assert original_context.config.scanner == "grype"
        assert original_context.config.mode == "highest-score"

        # Final context has all updates
        assert final_context.config.log_level == "DEBUG"
        assert final_context.config.scanner == "trivy"
        assert final_context.config.mode == "first-occurrence"

    def test_with_config_empty_updates(self, base_config: AggregatorConfig):
        """Test with_config with no updates."""
        original_context = AppContext(base_config)

        # No updates
        new_context = original_context.with_config()

        # Should create new context with same config
        assert new_context is not original_context
        assert new_context.config.log_level == original_context.config.log_level
        assert new_context.config.scanner == original_context.config.scanner


class TestContextIntegration:
    """Integration tests for AppContext."""

    def test_context_used_across_modules(self, tmp_path: Path):
        """Test that context can be passed to different modules."""
        input_dir = tmp_path / "reports"
        input_dir.mkdir()

        config = AggregatorConfig(
            input_dir=input_dir,
            output_file=tmp_path / "output.json",
            log_level="DEBUG",
        )
        context = AppContext(config)

        # Get loggers from different modules
        logger1 = context.get_logger("module1")
        logger2 = context.get_logger("module2")

        # Both loggers should work
        logger1.info("Message from module1")
        logger2.info("Message from module2")

        # Error handler should be accessible
        assert context.error_handler is not None

    def test_context_config_immutability(self, base_config: AggregatorConfig):
        """Test that original config is not mutated by with_config."""
        context = AppContext(base_config)
        original_log_level = context.config.log_level

        # Create multiple derived contexts
        debug_ctx = context.with_config(log_level="DEBUG")
        warning_ctx = context.with_config(log_level="WARNING")
        critical_ctx = context.with_config(log_level="CRITICAL")

        # Original context unchanged
        assert context.config.log_level == original_log_level

        # Each derived context has correct value
        assert debug_ctx.config.log_level == "DEBUG"
        assert warning_ctx.config.log_level == "WARNING"
        assert critical_ctx.config.log_level == "CRITICAL"
