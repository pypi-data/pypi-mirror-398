"""Archive utilities for bundling output artifacts."""

import tarfile
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import AppContext


def create_tarball(
    tarball_path: Path,
    output_files: list[Path],
    context: AppContext,
) -> Path:
    """Create a compressed tarball of all artifacts.

    Creates a gzip-compressed tarball containing all generated artifacts
    including SBOM files (from zarf package inspect sbom), JSON reports,
    CSV exports, and executive summaries. The tarball is created in the
    archive directory (/home/cve-aggregator/archive) for easy Docker
    volume mounting with a single mount point.

    Args:
        tarball_path: Full path where tarball should be created
            (e.g., /home/cve-aggregator/archive/artifacts.tar.gz)
        output_files: List of file paths to include in tarball (SBOMs + outputs)
        context: Application context with logger

    Returns:
        Path to the created tarball

    Raises:
        RuntimeError: If tarball creation fails

    Example:
        >>> from pathlib import Path
        >>> input_dir = Path("/home/cve-aggregator/output/reports")
        >>> output_dir = Path("/home/cve-aggregator/output")
        >>> files = [
        ...     # SBOM files from zarf package inspect sbom
        ...     input_dir / "component-sbom.json",
        ...     # Output files from aggregation
        ...     output_dir / "package-1.0.0.json",
        ...     output_dir / "package-1.0.0.csv",
        ...     output_dir / "executive-summary-20250101.json"
        ... ]
        >>> tarball_path = Path("/home/cve-aggregator/archive/artifacts.tar.gz")
        >>> created_path = create_tarball(tarball_path, files, context)
        >>> print(created_path)
        /home/cve-aggregator/archive/artifacts.tar.gz
    """
    logger = context.get_logger(__name__)

    try:
        # Ensure parent directory exists
        tarball_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Creating tarball",
            tarball=str(tarball_path),
            file_count=len(output_files),
        )

        # Create tarball with gzip compression
        with tarfile.open(tarball_path, "w:gz") as tar:
            for file_path in output_files:
                # Add file with just the filename (no directory structure)
                tar.add(file_path, arcname=file_path.name)

                logger.debug(
                    "Added file to tarball",
                    file=file_path.name,
                )

        logger.info(
            "Tarball created successfully",
            tarball=str(tarball_path),
            size_bytes=tarball_path.stat().st_size,
        )

        return tarball_path

    except Exception as e:
        logger.error(
            "Failed to create tarball",
            error=str(e),
            tarball=str(tarball_path),
        )
        raise RuntimeError(f"Tarball creation failed: {e}") from e


__all__ = ["create_tarball"]
