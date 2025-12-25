"""JSON utility functions for loading and validating report files.

This module provides centralized JSON loading with standardized error handling
to eliminate code duplication across the application.
"""

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from .exceptions import ReportLoadError
from .logging import get_logger

logger = get_logger(__name__)


def load_json_report(path: Path) -> dict[str, Any]:
    """Load and validate JSON report file with standardized error handling.

    This function provides consistent JSON loading behavior across the application,
    with proper error handling and logging for common failure scenarios.

    Args:
        path: Path to JSON file to load

    Returns:
        Parsed JSON data as dictionary

    Raises:
        ReportLoadError: If file cannot be read or contains invalid JSON

    Examples:
        >>> from pathlib import Path
        >>> data = load_json_report(Path("report.json"))
        >>> print(data.keys())
        dict_keys(['matches', 'source', 'descriptor'])

        >>> # With error handling
        >>> try:
        ...     data = load_json_report(Path("invalid.json"))
        ... except ReportLoadError as e:
        ...     print(f"Failed to load: {e}")
    """
    try:
        with open(path) as f:
            data = json.load(f)
            # Type narrowing: ensure we got a dictionary
            if not isinstance(data, dict):
                raise ReportLoadError(str(path), f"Expected JSON object (dict), got {type(data).__name__}")
            return data
    except JSONDecodeError as e:
        logger.error("Invalid JSON in report file", file=str(path), error=str(e))
        raise ReportLoadError(str(path), f"Invalid JSON: {e}") from e
    except OSError as e:
        logger.error("Failed to read report file", file=str(path), error=str(e))
        raise ReportLoadError(str(path), f"File read error: {e}") from e
    except Exception as e:
        logger.error("Unexpected error loading report", file=str(path), error=str(e))
        raise ReportLoadError(str(path), f"Unexpected error: {e}") from e


__all__ = ["load_json_report"]
