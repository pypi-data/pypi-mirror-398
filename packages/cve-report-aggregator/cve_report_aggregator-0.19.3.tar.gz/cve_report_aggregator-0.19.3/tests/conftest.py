"""Pytest configuration and fixtures for test isolation.

This module provides test fixtures that ensure tests run in isolation
from the project's local configuration files (.cve-aggregator.yaml).
"""

import os

import pytest


@pytest.fixture(autouse=True)
def isolate_test_environment(tmp_path, monkeypatch):
    """Isolate each test by changing to a temporary directory.

    This fixture automatically runs for all tests and ensures:
    1. Tests run in a clean temporary directory
    2. Local .cve-aggregator.yaml files don't interfere with test expectations
    3. Working directory is restored after each test
    4. Environment variables are cleared

    Args:
        tmp_path: Pytest fixture providing a temporary directory
        monkeypatch: Pytest fixture for modifying environment

    Yields:
        Path: The temporary directory where the test will run
    """
    # Save original working directory
    original_cwd = os.getcwd()

    # Change to temporary directory for test isolation
    # This ensures YAML config file discovery looks in temp dir, not project root
    os.chdir(tmp_path)

    # Clear any CVE_AGGREGATOR_ environment variables that might interfere
    env_vars_to_clear = [key for key in os.environ if key.startswith("CVE_AGGREGATOR_")]
    for env_var in env_vars_to_clear:
        monkeypatch.delenv(env_var, raising=False)

    try:
        yield tmp_path
    finally:
        # Restore original working directory
        os.chdir(original_cwd)
