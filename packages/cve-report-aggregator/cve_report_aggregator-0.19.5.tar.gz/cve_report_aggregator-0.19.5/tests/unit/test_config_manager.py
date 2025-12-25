"""Unit tests for global configuration manager.

This module tests the global configuration management functionality including:
- Setting and getting global configuration
- Thread safety
- Configuration context managers for testing
- Error handling for uninitialized configuration
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from cve_report_aggregator.core.config import (
    ConfigurationError,
    config_context,
    get_current_config,
    is_config_initialized,
    reset_config,
    set_config,
)
from cve_report_aggregator.core.models import AggregatorConfig


@pytest.fixture(autouse=True)
def reset_global_config():
    """Ensure clean config state before each test.

    This fixture automatically resets the global configuration before and after
    each test to prevent test pollution.
    """
    reset_config()
    yield
    reset_config()


class TestConfigManagerBasics:
    """Test basic configuration manager functionality."""

    def test_set_and_get_config(self, tmp_path: Path) -> None:
        """Test setting and retrieving global configuration."""
        # Create required directories for validation FIRST
        (tmp_path / "reports").mkdir()

        # Create test config
        test_config = AggregatorConfig(
            input_dir=tmp_path / "reports",
            output_file=tmp_path / "output.json",
            log_level="DEBUG",
        )

        # Set global config
        set_config(test_config)

        # Retrieve and verify
        retrieved_config = get_current_config()
        assert retrieved_config.log_level == "DEBUG"
        assert retrieved_config.input_dir == tmp_path / "reports"
        assert retrieved_config.scanner == "grype"  # default value

    def test_get_config_before_init_raises_error(self) -> None:
        """Test that accessing config before initialization raises error."""
        with pytest.raises(ConfigurationError) as exc_info:
            get_current_config()

        assert "not initialized" in str(exc_info.value)
        assert "set_config()" in str(exc_info.value)

    def test_is_config_initialized(self, tmp_path: Path) -> None:
        """Test checking if configuration is initialized."""
        # Initially not initialized
        assert is_config_initialized() is False

        # Create and set config
        (tmp_path / "reports").mkdir()
        test_config = AggregatorConfig(
            input_dir=tmp_path / "reports",
            output_file=tmp_path / "output.json",
        )
        set_config(test_config)

        # Now initialized
        assert is_config_initialized() is True

        # Reset
        reset_config()
        assert is_config_initialized() is False

    def test_config_override(self, tmp_path: Path) -> None:
        """Test that setting config multiple times overrides previous value."""
        (tmp_path / "reports1").mkdir()
        (tmp_path / "reports2").mkdir()

        # Set initial config
        config1 = AggregatorConfig(
            input_dir=tmp_path / "reports1",
            output_file=tmp_path / "output1.json",
            log_level="INFO",
        )
        set_config(config1)

        # Override with new config
        config2 = AggregatorConfig(
            input_dir=tmp_path / "reports2",
            output_file=tmp_path / "output2.json",
            log_level="DEBUG",
        )
        set_config(config2)

        # Verify latest config is active
        current = get_current_config()
        assert current.log_level == "DEBUG"
        assert current.input_dir == tmp_path / "reports2"


class TestConfigContext:
    """Test configuration context manager for testing."""

    def test_config_context_basic(self, tmp_path: Path) -> None:
        """Test basic context manager usage."""
        (tmp_path / "reports").mkdir()
        test_config = AggregatorConfig(
            input_dir=tmp_path / "reports",
            output_file=tmp_path / "output.json",
            log_level="DEBUG",
        )

        # Use context manager
        with config_context(test_config):
            config = get_current_config()
            assert config.log_level == "DEBUG"
            assert config.input_dir == tmp_path / "reports"

        # Config should be reset after context
        assert is_config_initialized() is False

    def test_config_context_restores_previous(self, tmp_path: Path) -> None:
        """Test that context manager restores previous configuration."""
        (tmp_path / "reports1").mkdir()
        (tmp_path / "reports2").mkdir()

        # Set initial global config
        original_config = AggregatorConfig(
            input_dir=tmp_path / "reports1",
            output_file=tmp_path / "output1.json",
            log_level="INFO",
        )
        set_config(original_config)

        # Use temporary config in context
        temp_config = AggregatorConfig(
            input_dir=tmp_path / "reports2",
            output_file=tmp_path / "output2.json",
            log_level="DEBUG",
        )

        with config_context(temp_config):
            assert get_current_config().log_level == "DEBUG"
            assert get_current_config().input_dir == tmp_path / "reports2"

        # Original config should be restored
        assert get_current_config().log_level == "INFO"
        assert get_current_config().input_dir == tmp_path / "reports1"

    def test_config_context_nested(self, tmp_path: Path) -> None:
        """Test nested context managers."""
        (tmp_path / "reports1").mkdir()
        (tmp_path / "reports2").mkdir()
        (tmp_path / "reports3").mkdir()

        config1 = AggregatorConfig(
            input_dir=tmp_path / "reports1",
            output_file=tmp_path / "output1.json",
            scanner="grype",
        )
        config2 = AggregatorConfig(
            input_dir=tmp_path / "reports2",
            output_file=tmp_path / "output2.json",
            scanner="trivy",
        )
        config3 = AggregatorConfig(
            input_dir=tmp_path / "reports3",
            output_file=tmp_path / "output3.json",
            scanner="grype",
        )

        with config_context(config1):
            assert get_current_config().scanner == "grype"
            assert get_current_config().input_dir == tmp_path / "reports1"

            with config_context(config2):
                assert get_current_config().scanner == "trivy"
                assert get_current_config().input_dir == tmp_path / "reports2"

                with config_context(config3):
                    assert get_current_config().scanner == "grype"
                    assert get_current_config().input_dir == tmp_path / "reports3"

                # Back to config2
                assert get_current_config().scanner == "trivy"
                assert get_current_config().input_dir == tmp_path / "reports2"

            # Back to config1
            assert get_current_config().scanner == "grype"
            assert get_current_config().input_dir == tmp_path / "reports1"

        # Back to no config
        assert is_config_initialized() is False


class TestThreadSafety:
    """Test thread safety of global configuration manager."""

    def test_concurrent_access(self, tmp_path: Path) -> None:
        """Test concurrent access from multiple threads."""
        (tmp_path / "reports").mkdir()
        test_config = AggregatorConfig(
            input_dir=tmp_path / "reports",
            output_file=tmp_path / "output.json",
            log_level="DEBUG",
        )
        set_config(test_config)

        # Results collector
        results: list[bool] = []
        errors: list[Exception] = []

        def access_config() -> None:
            """Access config from thread."""
            try:
                config = get_current_config()
                results.append(config.log_level == "DEBUG")
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = [threading.Thread(target=access_config) for _ in range(10)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify all threads got correct config
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        assert all(results), "All threads should have gotten correct config"

    def test_concurrent_set_and_get(self, tmp_path: Path) -> None:
        """Test concurrent set and get operations."""
        (tmp_path / "reports1").mkdir()
        (tmp_path / "reports2").mkdir()

        config1 = AggregatorConfig(
            input_dir=tmp_path / "reports1",
            output_file=tmp_path / "output1.json",
            log_level="INFO",
        )
        config2 = AggregatorConfig(
            input_dir=tmp_path / "reports2",
            output_file=tmp_path / "output2.json",
            log_level="DEBUG",
        )

        def set_config_repeatedly(config: AggregatorConfig, count: int) -> None:
            """Set config multiple times."""
            for _ in range(count):
                set_config(config)

        # Create threads that set different configs
        thread1 = threading.Thread(target=set_config_repeatedly, args=(config1, 50))
        thread2 = threading.Thread(target=set_config_repeatedly, args=(config2, 50))

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        # Final config should be valid (either config1 or config2)
        final_config = get_current_config()
        assert final_config.log_level in ("DEBUG", "INFO")
        assert final_config.input_dir in (tmp_path / "reports1", tmp_path / "reports2")


class TestConfigurationIntegration:
    """Test integration with executor module."""

    def test_executor_uses_global_config(self, tmp_path: Path) -> None:
        """Test that executor can use global configuration."""
        from cve_report_aggregator.core.executor import ExecutorManager

        # Set up global config
        (tmp_path / "reports").mkdir()
        test_config = AggregatorConfig(
            input_dir=tmp_path / "reports",
            output_file=tmp_path / "output.json",
            log_level="DEBUG",
        )
        set_config(test_config)

        # Execute command using global config
        output, error = ExecutorManager.execute_with_global_config(["echo", "test"])

        assert error is None
        assert "test" in output

    def test_executor_without_global_config(self) -> None:
        """Test that executor works without global config initialized."""
        from cve_report_aggregator.core.executor import ExecutorManager

        # Don't initialize global config
        assert is_config_initialized() is False

        # Should still work (graceful degradation)
        output, error = ExecutorManager.execute_with_global_config(["echo", "test"])

        assert error is None
        assert "test" in output

    def test_executor_with_explicit_config(self, tmp_path: Path) -> None:
        """Test executor with explicitly passed config."""
        from cve_report_aggregator.core.executor import ExecutorManager

        (tmp_path / "reports").mkdir()
        test_config = AggregatorConfig(
            input_dir=tmp_path / "reports",
            output_file=tmp_path / "output.json",
            log_level="DEBUG",
        )

        # Use config explicitly (don't set as global)
        output, error = ExecutorManager.execute(
            ["echo", "test"],
            config=test_config,
        )

        assert error is None
        assert "test" in output


class TestConfigurationPatterns:
    """Test recommended configuration usage patterns."""

    def test_application_startup_pattern(self, tmp_path: Path) -> None:
        """Test recommended pattern for application startup."""
        from cve_report_aggregator.core.config import get_config

        # Simulate application startup
        (tmp_path / "reports").mkdir()

        # 1. Load configuration from all sources
        app_config = get_config(
            cli_args={
                "input_dir": tmp_path / "reports",
                "output_file": tmp_path / "output.json",
                "log_level": "DEBUG",
            }
        )

        # 2. Set as global configuration
        set_config(app_config)

        # 3. Now any module can access it
        assert is_config_initialized() is True
        assert get_current_config().log_level == "DEBUG"

    def test_testing_pattern(self, tmp_path: Path) -> None:
        """Test recommended pattern for testing."""
        # Create test config
        (tmp_path / "reports").mkdir()
        test_config = AggregatorConfig(
            input_dir=tmp_path / "reports",
            output_file=tmp_path / "output.json",
            log_level="DEBUG",
            scanner="trivy",
        )

        # Use context manager for isolated test
        with config_context(test_config):
            # Test code that needs config
            config = get_current_config()
            assert config.scanner == "trivy"
            assert config.log_level == "DEBUG"

        # Config is automatically cleaned up
        assert is_config_initialized() is False

    def test_module_access_pattern(self, tmp_path: Path) -> None:
        """Test recommended pattern for module access to config."""
        from cve_report_aggregator.core.config import is_config_initialized

        # Set up config
        (tmp_path / "reports").mkdir()
        test_config = AggregatorConfig(
            input_dir=tmp_path / "reports",
            output_file=tmp_path / "output.json",
            log_level="DEBUG",
        )
        set_config(test_config)

        # Module pattern: check if initialized before accessing
        if is_config_initialized():
            config = get_current_config()
            assert config.log_level == "DEBUG"
        else:
            pytest.fail("Config should be initialized")
