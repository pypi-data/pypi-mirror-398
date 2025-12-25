"""Core scanner tool functions for Grype, Trivy, and Syft.

This module contains low-level scanner execution functions that are used by
both scanner.py and pipeline.py. It's separated to avoid circular imports.
"""

import subprocess
from pathlib import Path

from rich.console import Console

from ..core.exceptions import ScannerExecutionError, ScannerNotFoundError

console = Console()


def convert_to_cyclonedx(grype_report: Path, output_dir: Path, verbose: bool = False) -> Path:
    """Convert Grype report to CycloneDX format using Syft.

    Args:
        grype_report: Path to the Grype JSON report.
        output_dir: Directory to store the converted file.
        verbose: Whether to print conversion details.

    Returns:
        Path to the converted CycloneDX JSON file.
    """
    cdx_file: Path = output_dir / f"{grype_report.stem}.cdx.json"

    if verbose:
        console.print(
            f"[cyan]Converting[/cyan] {grype_report.name} to CycloneDX...",
            style="dim",
        )

    try:
        result: subprocess.CompletedProcess[str] = subprocess.run(
            ["syft", "convert", str(grype_report), "-o", "cyclonedx-json"],
            check=True,
            capture_output=True,
            text=True,
        )
        cdx_file.write_text(result.stdout)

        if verbose:
            console.print(f"  [green]✓[/green] Created: {cdx_file.name}", style="dim")

        return cdx_file
    except subprocess.CalledProcessError as e:
        error_msg = f"Converting {grype_report.name} to CycloneDX: {e.stderr}"
        console.print(f"[red]Error[/red] {error_msg}", style="bold red")
        raise ScannerExecutionError(
            "syft", ["syft", "convert", str(grype_report), "-o", "cyclonedx-json"], e.stderr
        ) from e
    except FileNotFoundError as e:
        console.print(
            "[red]Error:[/red] 'syft' command not found. Please install syft to use Trivy scanning.",
            style="bold red",
        )
        raise ScannerNotFoundError("syft") from e


def scan_sbom_with_grype(sbom_file: Path, output_dir: Path, verbose: bool = False) -> Path:
    """Scan SBOM file with Grype.

    Args:
        sbom_file: Path to the Syft SBOM JSON file.
        output_dir: Directory to store the Grype report.
        verbose: Whether to print scanning details.

    Returns:
        Path to the Grype JSON report.
    """
    grype_report: Path = output_dir / f"{sbom_file.stem}.grype.json"

    if verbose:
        console.print(f"[cyan]Scanning[/cyan] {sbom_file.name} with Grype...", style="dim")

    try:
        result: subprocess.CompletedProcess[str] = subprocess.run(
            ["grype", f"sbom:{sbom_file}", "-o", "json"],
            check=True,
            capture_output=True,
            text=True,
        )
        grype_report.write_text(result.stdout)

        if verbose:
            console.print(f"  [green]✓[/green] Created: {grype_report.name}", style="dim")

        return grype_report
    except subprocess.CalledProcessError as e:
        error_msg = f"Scanning {sbom_file.name} with Grype"
        console.print(f"[red]Error[/red] {error_msg}: {e.stderr}", style="bold red")
        raise ScannerExecutionError("grype", ["grype", f"sbom:{sbom_file}", "-o", "json"], e.stderr) from e
    except FileNotFoundError as e:
        console.print(
            "[red]Error:[/red] 'grype' command not found. Please install Grype.",
            style="bold red",
        )
        raise ScannerNotFoundError("grype") from e


def scan_with_trivy(cdx_file: Path, output_dir: Path, verbose: bool = False) -> Path:
    """Scan CycloneDX SBOM with Trivy.

    Trivy exit codes:
    - 0: No vulnerabilities found
    - 1: Vulnerabilities found (NOT an error - this is expected!)
    - 2+: Error occurred

    Args:
        cdx_file: Path to the CycloneDX JSON file.
        output_dir: Directory to store the Trivy report.
        verbose: Whether to print scanning details.

    Returns:
        Path to the Trivy JSON report.
    """
    trivy_report: Path = output_dir / f"{cdx_file.stem.replace('.cdx', '')}.trivy.json"

    if verbose:
        console.print(f"[cyan]Scanning[/cyan] {cdx_file.name} with Trivy...", style="dim")

    try:
        # Don't use check=True because exit code 1 means vulnerabilities found (success)
        result = subprocess.run(
            ["trivy", "sbom", str(cdx_file), "-f", "json", "-o", str(trivy_report)],
            capture_output=True,
            text=True,
        )

        # Exit code 0 or 1 are both success (1 = vulnerabilities found)
        if result.returncode in (0, 1):
            if verbose:
                console.print(f"  [green]✓[/green] Created: {trivy_report.name}", style="dim")
            return trivy_report

        # Exit code 2+ is an actual error
        error_msg = f"Scanning {cdx_file.name} with Trivy"
        stderr_output = result.stderr or "No error details available"
        console.print(f"[red]Error[/red] {error_msg}: {stderr_output}", style="bold red")
        raise ScannerExecutionError(
            "trivy",
            ["trivy", "sbom", str(cdx_file), "-f", "json", "-o", str(trivy_report)],
            stderr_output,
        )
    except FileNotFoundError as e:
        console.print(
            "[red]Error:[/red] 'trivy' command not found. Please install Trivy.",
            style="bold red",
        )
        raise ScannerNotFoundError("trivy") from e
