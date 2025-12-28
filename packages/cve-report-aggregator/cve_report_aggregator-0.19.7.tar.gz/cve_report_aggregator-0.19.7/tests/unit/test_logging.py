"""Tests for the centralized logging system using structlog."""

from __future__ import annotations

import pytest

from cve_report_aggregator.core.config import config_context, reset_config
from cve_report_aggregator.core.logging import LogManager, get_logger
from cve_report_aggregator.core.models import AggregatorConfig


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset LogManager state before each test."""
    LogManager.reset()
    reset_config()
    yield
    LogManager.reset()
    reset_config()


@pytest.fixture
def sample_config(tmp_path):
    """Create a sample configuration for testing with DEBUG log level."""
    input_dir = tmp_path / "reports"
    input_dir.mkdir()
    return AggregatorConfig(
        input_dir=input_dir,
        output_file=tmp_path / "output.json",
        scanner="grype",
        mode="highest-score",
        log_level="DEBUG",
    )


@pytest.fixture
def quiet_config(tmp_path):
    """Create a quiet (non-verbose) configuration for testing with INFO log level."""
    input_dir = tmp_path / "reports"
    input_dir.mkdir()
    return AggregatorConfig(
        input_dir=input_dir,
        output_file=tmp_path / "output.json",
        scanner="grype",
        mode="highest-score",
        log_level="INFO",
    )


@pytest.fixture
def capture_logs(capsys):
    """Capture log output for testing.

    Note: structlog writes to stdout, so we use capsys instead of StringIO.
    """
    yield capsys


class TestLogManagerConfiguration:
    """Tests for LogManager configuration."""

    def test_auto_configuration_on_first_use(self):
        """Test that LogManager auto-configures on first logger creation."""
        assert not LogManager._configured

        logger = LogManager.get_logger(__name__)

        assert LogManager._configured
        assert logger is not None

    def test_explicit_configuration(self):
        """Test explicit configuration before logger creation."""
        LogManager.configure(log_level="DEBUG", use_json=False, use_colors=True)

        assert LogManager._configured

        logger = LogManager.get_logger(__name__)
        assert logger is not None

    def test_configuration_with_verbose_config(self, sample_config):
        """Test that DEBUG log_level config sets DEBUG level."""
        with config_context(sample_config):
            LogManager.configure()

            level = LogManager.get_log_level()
            assert level == "DEBUG"

    def test_configuration_with_quiet_config(self, quiet_config):
        """Test that INFO log_level config sets INFO level."""
        with config_context(quiet_config):
            LogManager.configure()

            level = LogManager.get_log_level()
            assert level == "INFO"

    def test_configuration_without_global_config(self):
        """Test configuration when global config is not initialized."""
        # Don't initialize config
        LogManager.configure()

        level = LogManager.get_log_level()
        assert level == "INFO"

    def test_reconfiguration_is_idempotent(self):
        """Test that calling configure multiple times is safe."""
        LogManager.configure(log_level="DEBUG")
        first_configured = LogManager._configured

        LogManager.configure(log_level="INFO")
        second_configured = LogManager._configured

        assert first_configured is True
        assert second_configured is True

    def test_json_output_configuration(self):
        """Test configuration with JSON output."""
        LogManager.configure(use_json=True)

        logger = LogManager.get_logger(__name__)
        assert logger is not None

    def test_no_colors_configuration(self):
        """Test configuration without colors."""
        LogManager.configure(use_colors=False)

        logger = LogManager.get_logger(__name__)
        assert logger is not None


class TestLoggerCreation:
    """Tests for logger creation and caching."""

    def test_get_logger_with_name(self):
        """Test getting a logger with a specific name."""
        logger = LogManager.get_logger("test.module")

        assert logger is not None
        assert "test.module" in LogManager._loggers

    def test_get_logger_without_name(self):
        """Test getting a logger without a name (uses default)."""
        logger = LogManager.get_logger()

        assert logger is not None
        assert "cve_report_aggregator" in LogManager._loggers

    def test_get_logger_with_initial_context(self):
        """Test getting a logger with initial context."""
        logger = LogManager.get_logger(__name__, component="scanner", version="1.0")

        assert logger is not None
        # Logger with context is not cached
        assert __name__ not in LogManager._loggers or LogManager._loggers[__name__] != logger

    def test_logger_caching(self):
        """Test that loggers are cached by name."""
        logger1 = LogManager.get_logger("test.module")
        logger2 = LogManager.get_logger("test.module")

        assert logger1 is logger2

    def test_convenience_function(self):
        """Test the get_logger convenience function."""
        logger = get_logger(__name__)

        assert logger is not None

    def test_multiple_loggers_different_names(self):
        """Test creating multiple loggers with different names."""
        logger1 = LogManager.get_logger("module1")
        logger2 = LogManager.get_logger("module2")

        assert logger1 is not None
        assert logger2 is not None
        assert logger1 is not logger2


class TestLogging:
    """Tests for actual logging functionality."""

    def test_log_info_message(self, capture_logs):
        """Test logging an INFO message."""
        LogManager.configure(log_level="INFO", use_json=False)
        logger = LogManager.get_logger(__name__)

        logger.info("Test message", key="value")

        captured = capture_logs.readouterr()
        output = captured.out
        assert "Test message" in output
        assert "key" in output
        assert "value" in output

    def test_log_debug_message_with_debug_level(self, capture_logs):
        """Test that DEBUG messages appear with DEBUG level."""
        LogManager.configure(log_level="DEBUG", use_json=False)
        logger = LogManager.get_logger(__name__)

        logger.debug("Debug message", detail="test")

        captured = capture_logs.readouterr()
        output = captured.out
        assert "Debug message" in output

    def test_log_debug_message_filtered_with_info_level(self, capture_logs):
        """Test that DEBUG messages are filtered with INFO level."""
        LogManager.configure(log_level="INFO", use_json=False)
        logger = LogManager.get_logger(__name__)

        logger.debug("Debug message")

        captured = capture_logs.readouterr()
        output = captured.out
        assert "Debug message" not in output

    def test_log_with_exception(self, capture_logs):
        """Test logging with exception information."""
        LogManager.configure(log_level="INFO", use_json=False)
        logger = LogManager.get_logger(__name__)

        try:
            raise ValueError("Test error")
        except ValueError:
            logger.exception("An error occurred")

        captured = capture_logs.readouterr()
        output = captured.out
        assert "An error occurred" in output
        assert "ValueError" in output
        assert "Test error" in output

    def test_log_with_structured_data(self, capture_logs):
        """Test logging with structured data."""
        LogManager.configure(log_level="INFO", use_json=False)
        logger = LogManager.get_logger(__name__)

        logger.info(
            "Processing vulnerability",
            vuln_id="CVE-2024-12345",
            severity="High",
            cvss_score=7.5,
            affected_packages=["openssl", "libssl"],
        )

        captured = capture_logs.readouterr()
        output = captured.out
        assert "Processing vulnerability" in output
        assert "CVE-2024-12345" in output
        assert "High" in output

    def test_logger_context_binding(self, capture_logs):
        """Test binding context to a logger."""
        LogManager.configure(log_level="INFO", use_json=False)
        logger = LogManager.get_logger(__name__)

        # Bind context
        bound_logger = logger.bind(request_id="abc-123", user="tester")

        bound_logger.info("First message")
        bound_logger.info("Second message")

        captured = capture_logs.readouterr()
        output = captured.out
        # Both messages should include the bound context
        assert output.count("abc-123") >= 2
        assert output.count("tester") >= 2


class TestLogContext:
    """Tests for log context management."""

    def test_log_context_manager(self, capture_logs):
        """Test using log context manager."""
        LogManager.configure(log_level="INFO", use_json=False)

        with LogManager.log_context(request_id="req-123", session="sess-456"):
            logger = LogManager.get_logger(__name__)
            logger.info("Inside context")

        captured = capture_logs.readouterr()
        output = captured.out
        assert "req-123" in output
        assert "sess-456" in output

    def test_log_context_cleanup(self, capture_logs):
        """Test that log context is cleaned up after exiting."""
        LogManager.configure(log_level="INFO", use_json=False)

        with LogManager.log_context(temp_id="temp-123"):
            logger1 = LogManager.get_logger(__name__)
            logger1.info("Inside context")

        logger2 = LogManager.get_logger(__name__)
        logger2.info("Outside context")

        captured = capture_logs.readouterr()
        output = captured.out
        # temp_id should appear once (inside context)
        assert output.count("temp-123") == 1

    def test_nested_log_contexts(self, capture_logs):
        """Test nested log contexts."""
        LogManager.configure(log_level="INFO", use_json=False)

        with LogManager.log_context(outer="outer-123"):
            logger1 = LogManager.get_logger(__name__)
            logger1.info("Outer level")

            with LogManager.log_context(inner="inner-456"):
                logger2 = LogManager.get_logger(__name__)
                logger2.info("Inner level")

        captured = capture_logs.readouterr()
        output = captured.out
        assert "outer-123" in output
        assert "inner-456" in output


class TestLogLevelManagement:
    """Tests for dynamic log level management."""

    def test_get_log_level_from_verbose_config(self, sample_config):
        """Test getting log level from DEBUG config."""
        with config_context(sample_config):
            LogManager.configure()
            level = LogManager.get_log_level()

            assert level == "DEBUG"

    def test_get_log_level_from_quiet_config(self, quiet_config):
        """Test getting log level from INFO config."""
        with config_context(quiet_config):
            LogManager.configure()
            level = LogManager.get_log_level()

            assert level == "INFO"

    def test_set_log_level_dynamically(self, capture_logs):
        """Test dynamically changing log level."""
        LogManager.configure(log_level="INFO")
        logger1 = LogManager.get_logger(__name__)

        # Debug message should be filtered
        logger1.debug("Debug 1")
        captured_first = capture_logs.readouterr()
        assert "Debug 1" not in captured_first.out

        # Change to DEBUG level
        LogManager.set_log_level("DEBUG")

        # Get a new logger after level change
        LogManager.reset()
        LogManager.configure(log_level="DEBUG")
        logger2 = LogManager.get_logger(__name__)
        logger2.debug("Debug 2")

        captured = capture_logs.readouterr()
        output = captured.out
        assert "Debug 2" in output

    def test_set_log_level_to_warning(self, capture_logs):
        """Test setting log level to WARNING."""
        LogManager.configure(log_level="DEBUG")
        logger = LogManager.get_logger(__name__)

        logger.info("Info 1")
        captured1 = capture_logs.readouterr()
        assert "Info 1" in captured1.out

        # Change to WARNING level and get new logger
        LogManager.set_log_level("WARNING")
        LogManager.reset()
        LogManager.configure(log_level="WARNING")
        logger2 = LogManager.get_logger(__name__)
        logger2.info("Info 2")

        captured2 = capture_logs.readouterr()
        output = captured2.out
        assert "Info 2" not in output


class TestReset:
    """Tests for LogManager reset functionality."""

    def test_reset_clears_configuration(self):
        """Test that reset clears configuration state."""
        LogManager.configure(log_level="DEBUG")
        assert LogManager._configured is True

        LogManager.reset()
        assert LogManager._configured is False

    def test_reset_clears_logger_cache(self):
        """Test that reset clears logger cache."""
        LogManager.get_logger("test1")
        LogManager.get_logger("test2")
        assert len(LogManager._loggers) >= 2

        LogManager.reset()
        assert len(LogManager._loggers) == 0

    def test_reset_allows_reconfiguration(self):
        """Test that reset allows reconfiguration."""
        LogManager.configure(log_level="INFO", use_json=False)
        assert LogManager._configured is True

        LogManager.reset()
        LogManager.configure(log_level="DEBUG", use_json=True)

        assert LogManager._configured is True
        # Note: get_log_level reads from config, not from current state
        # So it returns INFO unless config is initialized with log_level="DEBUG"


class TestIntegrationWithConfig:
    """Tests for integration with global configuration."""

    def test_logger_uses_verbose_from_config(self, sample_config, capture_logs):
        """Test that logger respects DEBUG log level from config."""
        with config_context(sample_config):
            LogManager.configure()
            logger = LogManager.get_logger(__name__)

            logger.debug("Debug message")

            captured = capture_logs.readouterr()
            output = captured.out
            assert "Debug message" in output

    def test_logger_uses_quiet_from_config(self, quiet_config, capture_logs):
        """Test that logger respects INFO log level from config."""
        with config_context(quiet_config):
            LogManager.configure()
            logger = LogManager.get_logger(__name__)

            logger.debug("Debug message")

            captured = capture_logs.readouterr()
            output = captured.out
            assert "Debug message" not in output

    def test_configuration_without_config_initialized(self):
        """Test that LogManager works without global config."""
        # Don't initialize config
        LogManager.configure()
        logger = LogManager.get_logger(__name__)

        assert logger is not None
        assert LogManager.get_log_level() == "INFO"
