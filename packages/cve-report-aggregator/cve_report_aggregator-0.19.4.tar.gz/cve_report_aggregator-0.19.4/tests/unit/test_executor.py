"""Tests for the ExecutorManager command execution with retry logic."""

import subprocess
from unittest.mock import MagicMock

import pytest

from cve_report_aggregator.core.executor import ExecutorManager


class TestIsRetryableError:
    """Tests for _is_retryable_error classification."""

    def test_file_not_found_not_retryable(self):
        """FileNotFoundError should not be retried."""
        error = FileNotFoundError("Command not found")
        assert ExecutorManager._is_retryable_error(error) is False

    def test_timeout_expired_is_retryable(self):
        """TimeoutExpired should be retried."""
        error = subprocess.TimeoutExpired(cmd=["test"], timeout=30)
        assert ExecutorManager._is_retryable_error(error) is True

    @pytest.mark.parametrize(
        "exit_code",
        [124, 125, 126, 7, 28, 35, 52, 56, 137, 143],
    )
    def test_retryable_exit_codes(self, exit_code):
        """Specific exit codes should be retried."""
        error = subprocess.CalledProcessError(
            returncode=exit_code,
            cmd=["test"],
            stderr="",
            output="",
        )
        assert ExecutorManager._is_retryable_error(error) is True

    def test_non_retryable_exit_code(self):
        """Exit code 1 (generic failure) should not be retried without transient indicators."""
        error = subprocess.CalledProcessError(
            returncode=1,
            cmd=["test"],
            stderr="invalid argument",
            output="",
        )
        assert ExecutorManager._is_retryable_error(error) is False

    @pytest.mark.parametrize(
        "error_message",
        [
            "connection refused",
            "connection reset by peer",
            "connection timeout",
            "temporary failure in name resolution",
            "service unavailable",
            "too many requests",
            "rate limit exceeded",
            "socket error",
            "network error occurred",
            "dns resolution failed",
            "no route to host",
            "host unreachable",
            "broken pipe",
            "connection aborted",
            "ssl error occurred",
            "ssl: certificate verify failed",
            "tls handshake failed",
            "registry unavailable",
            "manifest unknown",
            "unexpected eof",
            "out of memory",
        ],
    )
    def test_transient_error_messages_are_retryable(self, error_message):
        """Error messages indicating transient failures should be retried."""
        error = subprocess.CalledProcessError(
            returncode=1,
            cmd=["test"],
            stderr=error_message,
            output="",
        )
        assert ExecutorManager._is_retryable_error(error) is True

    def test_oserror_with_retryable_errno(self):
        """OSError with retryable errno should be retried."""
        error = OSError(11, "Resource temporarily unavailable")  # EAGAIN
        assert ExecutorManager._is_retryable_error(error) is True

    def test_oserror_with_non_retryable_errno(self):
        """OSError with non-retryable errno should not be retried."""
        error = OSError(2, "No such file or directory")  # ENOENT
        assert ExecutorManager._is_retryable_error(error) is False

    def test_unknown_exception_not_retryable(self):
        """Unknown exception types should not be retried by default."""
        error = ValueError("Unknown error")
        assert ExecutorManager._is_retryable_error(error) is False


class TestCalculateBackoffDelay:
    """Tests for exponential backoff delay calculation."""

    def test_first_attempt_returns_initial_delay_approximately(self):
        """First attempt (0) should return approximately the initial delay."""
        delay = ExecutorManager._calculate_backoff_delay(
            attempt=0,
            initial_delay=1.0,
            max_delay=30.0,
            backoff_multiplier=2.0,
            jitter_factor=0.0,  # No jitter for deterministic test
        )
        assert delay == 1.0

    def test_exponential_increase(self):
        """Delay should increase exponentially with attempts."""
        delays = []
        for attempt in range(4):
            delay = ExecutorManager._calculate_backoff_delay(
                attempt=attempt,
                initial_delay=1.0,
                max_delay=100.0,
                backoff_multiplier=2.0,
                jitter_factor=0.0,
            )
            delays.append(delay)

        # Should be: 1, 2, 4, 8
        assert delays == [1.0, 2.0, 4.0, 8.0]

    def test_max_delay_cap(self):
        """Delay should be capped at max_delay."""
        delay = ExecutorManager._calculate_backoff_delay(
            attempt=10,  # Would be 1024 without cap
            initial_delay=1.0,
            max_delay=30.0,
            backoff_multiplier=2.0,
            jitter_factor=0.0,
        )
        assert delay == 30.0

    def test_jitter_adds_variation(self):
        """Jitter should add some variation to the delay."""
        delays = set()
        for _ in range(20):
            delay = ExecutorManager._calculate_backoff_delay(
                attempt=1,
                initial_delay=10.0,
                max_delay=100.0,
                backoff_multiplier=2.0,
                jitter_factor=0.1,  # 10% jitter
            )
            delays.add(round(delay, 2))

        # With jitter, we should get some variation
        # Base delay would be 20.0, jitter of ±10% means 18-22 range
        assert len(delays) > 1  # Should have variation
        for d in delays:
            assert 18.0 <= d <= 22.0  # Within jitter range

    def test_never_returns_negative(self):
        """Delay should never be negative even with large negative jitter."""
        delay = ExecutorManager._calculate_backoff_delay(
            attempt=0,
            initial_delay=0.1,
            max_delay=30.0,
            backoff_multiplier=2.0,
            jitter_factor=0.5,  # 50% jitter could theoretically go negative
        )
        assert delay >= 0.0


class TestExecute:
    """Tests for the execute method with retry logic."""

    def test_successful_execution(self, monkeypatch):
        """Successful command should return output and no error."""
        mock_result = MagicMock()
        mock_result.stdout = "success output"
        mock_result.stderr = ""
        mock_result.returncode = 0

        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: mock_result)

        output, error = ExecutorManager.execute(["echo", "hello"], max_retries=0)

        assert output == "success output"
        assert error is None

    def test_command_not_found_no_retry(self, monkeypatch):
        """FileNotFoundError should not be retried."""
        call_count = 0

        def mock_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise FileNotFoundError("Command not found")

        monkeypatch.setattr(subprocess, "run", mock_run)

        output, error = ExecutorManager.execute(["nonexistent"], max_retries=3)

        assert call_count == 1  # Only one attempt, no retries
        assert isinstance(error, FileNotFoundError)

    def test_retryable_error_retries(self, monkeypatch):
        """Retryable errors should be retried up to max_retries."""
        call_count = 0

        def mock_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise subprocess.CalledProcessError(
                returncode=124,  # Timeout - retryable
                cmd=args[0],
                stderr="timeout",
                output="",
            )

        monkeypatch.setattr(subprocess, "run", mock_run)

        output, error = ExecutorManager.execute(
            ["timeout_cmd"],
            max_retries=2,
            initial_delay=0.01,  # Fast for testing
        )

        assert call_count == 3  # Initial + 2 retries
        assert isinstance(error, subprocess.CalledProcessError)

    def test_success_after_retry(self, monkeypatch):
        """Command should succeed after transient failures."""
        call_count = 0

        def mock_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise subprocess.CalledProcessError(
                    returncode=124,  # Timeout - retryable
                    cmd=args[0],
                    stderr="timeout",
                    output="",
                )
            # Third attempt succeeds
            result = MagicMock()
            result.stdout = "success after retries"
            result.stderr = ""
            result.returncode = 0
            return result

        monkeypatch.setattr(subprocess, "run", mock_run)

        output, error = ExecutorManager.execute(
            ["flaky_cmd"],
            max_retries=3,
            initial_delay=0.01,
        )

        assert call_count == 3
        assert output == "success after retries"
        assert error is None

    def test_non_retryable_error_fails_immediately(self, monkeypatch):
        """Non-retryable errors should fail without retrying."""
        call_count = 0

        def mock_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise subprocess.CalledProcessError(
                returncode=1,
                cmd=args[0],
                stderr="invalid argument",  # Not a transient error
                output="",
            )

        monkeypatch.setattr(subprocess, "run", mock_run)

        output, error = ExecutorManager.execute(
            ["bad_args"],
            max_retries=3,
            initial_delay=0.01,
        )

        assert call_count == 1  # No retries for non-transient errors
        assert isinstance(error, subprocess.CalledProcessError)

    def test_timeout_expired_is_retried(self, monkeypatch):
        """TimeoutExpired should be retried."""
        call_count = 0

        def mock_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise subprocess.TimeoutExpired(cmd=args[0], timeout=30)
            result = MagicMock()
            result.stdout = "success"
            result.stderr = ""
            return result

        monkeypatch.setattr(subprocess, "run", mock_run)

        output, error = ExecutorManager.execute(
            ["slow_cmd"],
            max_retries=3,
            initial_delay=0.01,
        )

        assert call_count == 2
        assert output == "success"
        assert error is None

    def test_working_directory_from_config(self, monkeypatch, tmp_path):
        """Working directory should be set from config if not explicitly provided."""
        from cve_report_aggregator.core.models import AggregatorConfig

        captured_cwd = None

        def mock_run(*args, **kwargs):
            nonlocal captured_cwd
            captured_cwd = kwargs.get("cwd")
            result = MagicMock()
            result.stdout = "ok"
            result.stderr = ""
            return result

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Create a config with input_dir
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        config = AggregatorConfig(
            input_dir=reports_dir,
            output_file=tmp_path / "output.json",
        )

        ExecutorManager.execute(["test"], config=config)

        # Should use input_dir's parent as working directory
        assert captured_cwd == str(tmp_path)

    def test_explicit_cwd_overrides_config(self, monkeypatch, tmp_path):
        """Explicit cwd parameter should override config."""
        from cve_report_aggregator.core.models import AggregatorConfig

        captured_cwd = None

        def mock_run(*args, **kwargs):
            nonlocal captured_cwd
            captured_cwd = kwargs.get("cwd")
            result = MagicMock()
            result.stdout = "ok"
            result.stderr = ""
            return result

        monkeypatch.setattr(subprocess, "run", mock_run)

        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        config = AggregatorConfig(
            input_dir=reports_dir,
            output_file=tmp_path / "output.json",
        )

        explicit_dir = tmp_path / "explicit"
        explicit_dir.mkdir()

        ExecutorManager.execute(["test"], cwd=explicit_dir, config=config)

        assert captured_cwd == str(explicit_dir)


class TestExecuteWithGlobalConfig:
    """Tests for execute_with_global_config method."""

    def test_uses_global_config_when_available(self, monkeypatch, tmp_path):
        """Should use global config when initialized."""
        from cve_report_aggregator.core.config import reset_config, set_config
        from cve_report_aggregator.core.models import AggregatorConfig

        mock_result = MagicMock()
        mock_result.stdout = "output"
        mock_result.stderr = ""
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: mock_result)

        # Initialize global config
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        config = AggregatorConfig(
            input_dir=reports_dir,
            output_file=tmp_path / "output.json",
            log_level="DEBUG",
        )
        set_config(config)

        try:
            output, error = ExecutorManager.execute_with_global_config(["test"])
            assert output == "output"
            assert error is None
        finally:
            reset_config()

    def test_works_without_global_config(self, monkeypatch):
        """Should work even when global config is not initialized."""
        from cve_report_aggregator.core.config import reset_config

        mock_result = MagicMock()
        mock_result.stdout = "output"
        mock_result.stderr = ""
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: mock_result)

        reset_config()  # Ensure no global config

        output, error = ExecutorManager.execute_with_global_config(["test"])
        assert output == "output"
        assert error is None


class TestCreateTempDirectory:
    """Tests for create_temp_directory method."""

    def test_creates_temp_directory(self, monkeypatch):
        """Should create and return temp directory path."""
        mock_result = MagicMock()
        mock_result.stdout = "/tmp/test-dir-abc123\n"
        mock_result.stderr = ""
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: mock_result)

        temp_dir, error = ExecutorManager.create_temp_directory()

        assert error is None
        assert str(temp_dir) == "/tmp/test-dir-abc123"

    def test_handles_mktemp_failure(self, monkeypatch):
        """Should handle mktemp command failure."""

        def mock_run(*args, **kwargs):
            raise subprocess.CalledProcessError(
                returncode=1,
                cmd=["mktemp", "-d"],
                stderr="mktemp failed",
                output="",
            )

        monkeypatch.setattr(subprocess, "run", mock_run)

        temp_dir, error = ExecutorManager.create_temp_directory()

        assert error is not None
        assert isinstance(error, subprocess.CalledProcessError)
