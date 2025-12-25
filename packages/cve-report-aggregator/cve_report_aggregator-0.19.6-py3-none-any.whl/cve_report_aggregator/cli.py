"""Command-line interface for CVE Report Aggregator."""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import rich_click as click
from pydantic import ValidationError
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from . import __version__
from .context import AppContext
from .core.config import AggregatorConfig, get_config, set_config
from .core.models import ScannerType
from .core.orchestrator import AggregationResult, run_aggregation
from .core.validation import MissingToolError, validate_configuration, validate_scanner_tools
from .utils import ASCII_LOGO, check_command_exists, get_scanner_version

# =============================================================================
# CLI Argument Processing
# =============================================================================


@dataclass
class CLIArguments:
    """Structured CLI arguments for configuration building.

    Attributes:
        input_dir: Input directory containing scan report files
        output_file: Output file path for unified report
        output_dir: Output directory for all artifacts
        local_only: Only scan local Zarf packages
        scanner: Scanner type (grype, trivy, both)
        log_level: Logging level
        mode: Aggregation mode
        max_workers: Maximum concurrent workers
        archive_dir: Directory for tarball archive
        enrich_config: CVE enrichment configuration
    """

    input_dir: Path | None = None
    output_file: Path | None = None
    output_dir: Path | None = None
    local_only: bool | None = None
    scanner: str | None = None
    log_level: str | None = None
    mode: str | None = None
    max_workers: int | None = None
    archive_dir: Path | None = None
    enrich_config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for config loading, excluding None values."""
        result: dict[str, Any] = {}
        if self.input_dir is not None:
            result["input_dir"] = self.input_dir
        if self.output_file is not None:
            result["output_file"] = self.output_file
        if self.output_dir is not None:
            result["output_dir"] = self.output_dir
        if self.local_only is not None:
            result["local_only"] = self.local_only
        if self.scanner is not None:
            result["scanner"] = self.scanner
        if self.log_level is not None:
            result["log_level"] = self.log_level
        if self.mode is not None:
            result["mode"] = self.mode
        if self.max_workers is not None:
            result["max_workers"] = self.max_workers
        if self.archive_dir is not None:
            result["archive_dir"] = self.archive_dir
        if self.enrich_config:
            result["enrich"] = self.enrich_config
        return result


def _build_enrich_config(
    enrich_cves: bool | None,
    openai_api_key: str | None,
    openai_model: str | None,
    enrich_severity_filter: tuple[str, ...] | None,
) -> dict[str, Any]:
    """Build enrichment configuration from CLI args.

    Args:
        enrich_cves: Whether to enable CVE enrichment
        openai_api_key: OpenAI API key
        openai_model: OpenAI model to use
        enrich_severity_filter: Severity levels to enrich

    Returns:
        Dictionary of enrichment configuration options
    """
    config: dict[str, Any] = {}
    if enrich_cves is not None:
        config["enabled"] = enrich_cves
    if openai_api_key is not None:
        config["api_key"] = openai_api_key
    if openai_model is not None:
        config["model"] = openai_model
    if enrich_severity_filter is not None and len(enrich_severity_filter) > 0:
        config["severities"] = list(enrich_severity_filter)
    return config


def parse_cli_arguments(
    input_dir: Path | None,
    output_file: Path | None,
    output_dir: Path | None,
    local_only: bool | None,
    scanner: str | None,
    log_level: str | None,
    mode: str | None,
    max_workers: int | None,
    archive_dir: Path | None,
    enrich_cves: bool | None,
    openai_api_key: str | None,
    openai_model: str | None,
    enrich_severity_filter: tuple[str, ...] | None,
) -> CLIArguments:
    """Parse and structure CLI arguments.

    Consolidates all CLI argument processing into a single function,
    reducing complexity in the main function.

    Args:
        input_dir: Input directory containing scan report files
        output_file: Output file path for unified report
        output_dir: Output directory for all artifacts
        local_only: Only scan local Zarf packages
        scanner: Scanner type
        log_level: Logging level
        mode: Aggregation mode
        max_workers: Maximum concurrent workers
        archive_dir: Directory for tarball archive
        enrich_cves: Enable CVE enrichment
        openai_api_key: OpenAI API key
        openai_model: OpenAI model
        enrich_severity_filter: Severity levels to enrich

    Returns:
        CLIArguments dataclass with structured arguments
    """
    enrich_config = _build_enrich_config(
        enrich_cves,
        openai_api_key,
        openai_model,
        enrich_severity_filter,
    )

    return CLIArguments(
        input_dir=input_dir,
        output_file=output_file,
        output_dir=output_dir,
        local_only=local_only,
        scanner=scanner,
        log_level=log_level.upper() if log_level else None,
        mode=mode,
        max_workers=max_workers,
        archive_dir=archive_dir,
        enrich_config=enrich_config,
    )


# =============================================================================
# Configuration Loading
# =============================================================================


def _display_pydantic_validation_errors(console: Console, error: ValidationError) -> None:
    """Display Pydantic validation errors in user-friendly format.

    Args:
        console: Rich console for output
        error: Pydantic ValidationError
    """
    console.print("[red]Error:[/red] Configuration validation failed:", style="bold red")
    for err in error.errors():
        field_path = " -> ".join(str(loc) for loc in err["loc"])
        message = err["msg"]
        console.print(f"  [yellow]{field_path}:[/yellow] {message}", style="dim")


def load_and_validate_config(
    cli_args: CLIArguments,
    config_file_path: Path | None,
    console: Console,
) -> AggregatorConfig:
    """Load configuration with comprehensive error handling.

    Args:
        cli_args: Parsed CLI arguments
        config_file_path: Optional path to YAML config file
        console: Rich console for error output

    Returns:
        Validated AggregatorConfig

    Note:
        Exits with code 1 on validation or loading errors
    """
    try:
        return get_config(cli_args=cli_args.to_dict(), config_file_path=config_file_path)
    except ValidationError as e:
        _display_pydantic_validation_errors(console, e)
        sys.exit(1)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        sys.exit(1)


# =============================================================================
# Environment Validation
# =============================================================================


def _determine_effective_scanner(config: AggregatorConfig) -> ScannerType:
    """Determine which scanner to use based on mode.

    Args:
        config: Application configuration

    Returns:
        Effective scanner type
    """
    if config.mode == "grype-only":
        return "grype"
    elif config.mode == "trivy-only":
        return "trivy"
    return config.scanner


def _warn_if_uds_missing(console: Console) -> None:
    """Warn if UDS CLI is not available.

    Args:
        console: Rich console for warning output
    """
    if not check_command_exists("uds"):
        console.print(
            "[yellow]Warning:[/yellow] 'uds' command not found. Local package scanning will be skipped.\n"
            "To enable local package scanning, install UDS CLI: https://github.com/defenseunicorns/uds-cli",
            style="dim",
        )


def validate_environment(
    context: AppContext,
    console: Console,
) -> tuple[ScannerType, str]:
    """Validate tools and configuration, return effective scanner.

    Args:
        context: Application context
        console: Rich console for error output

    Returns:
        Tuple of (effective_scanner, scanner_version)

    Note:
        Exits with code 1 on validation errors
    """
    config = context.config

    # Determine effective scanner
    effective_scanner = _determine_effective_scanner(config)

    # Validate required tools
    try:
        validate_scanner_tools(context)
        validate_configuration(context)
    except MissingToolError as e:
        display_validation_error(e)
        sys.exit(1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        sys.exit(1)

    # Warn if UDS CLI is missing (optional)
    _warn_if_uds_missing(console)

    # Get scanner version
    scanner_version = get_scanner_version(effective_scanner)

    return effective_scanner, scanner_version


# =============================================================================
# Workflow Execution
# =============================================================================


def execute_aggregation_workflow(
    context: AppContext,
    console: Console,
    is_debug: bool,
) -> AggregationResult:
    """Execute the main aggregation workflow with progress tracking.

    Args:
        context: Application context
        console: Rich console for output
        is_debug: Whether debug mode is enabled

    Returns:
        AggregationResult with output files and statistics

    Note:
        Exits with code 1 on errors
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Acquiring SBOM files...", total=None)
            result = run_aggregation(context)
            progress.update(task, completed=True)

        if is_debug:
            console.print("\n[green]✓[/green] Aggregation completed successfully\n")

        return result

    except (ValueError, RuntimeError) as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        sys.exit(1)
    except Exception as e:
        console.print(
            f"[red]Error:[/red] Unexpected error during aggregation: {e}",
            style="bold red",
        )
        if is_debug:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)


# =============================================================================
# Output Categorization
# =============================================================================


@dataclass
class CategorizedOutputFiles:
    """Categorized output files from aggregation.

    Attributes:
        unified_json: List of unified JSON report files
        unified_csv: List of unified CSV report files
        executive_summaries: List of executive summary files
    """

    unified_json: list[Path] = field(default_factory=list)
    unified_csv: list[Path] = field(default_factory=list)
    executive_summaries: list[Path] = field(default_factory=list)


def categorize_output_files(output_files: list[Path]) -> CategorizedOutputFiles:
    """Categorize output files by type.

    Args:
        output_files: List of all output file paths

    Returns:
        CategorizedOutputFiles with files grouped by type
    """
    return CategorizedOutputFiles(
        unified_json=[f for f in output_files if f.suffix == ".json" and not f.name.startswith("executive-summary")],
        unified_csv=[f for f in output_files if f.suffix == ".csv"],
        executive_summaries=[f for f in output_files if f.name.startswith("executive-summary")],
    )


# Configure rich-click for beautiful help output
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "bold yellow"
click.rich_click.ERRORS_SUGGESTION = "Try running the '--help' flag for more information."
click.rich_click.ERRORS_EPILOGUE = ""
click.rich_click.SHOW_METAVARS_COLUMN = False
click.rich_click.APPEND_METAVARS_HELP = True
click.rich_click.OPTION_GROUPS = {
    "cve-report-aggregator": [
        {
            "name": "Configuration",
            "options": ["--config"],
        },
        {
            "name": "Input/Output Options",
            "options": ["--input-dir", "--output-file", "--output-dir", "--local-only"],
        },
        {
            "name": "Scanner Configuration",
            "options": ["--scanner", "--mode", "--max-workers"],
        },
        {
            "name": "CVE Enrichment Options",
            "options": [
                "--enrich-cves",
                "--openai-api-key",
                "--openai-model",
                "--batch-size",
                "--max-cves-to-enrich",
                "--enrich-severity-filter",
            ],
        },
        {
            "name": "Display Options",
            "options": ["--log-level"],
        },
    ],
}

# Initialize Rich console
console = Console()


def display_logo() -> None:
    """Display the ASCII logo."""
    try:
        console.print(ASCII_LOGO, style="cyan")
    except Exception:
        # Silently fall back if logo can't be displayed
        console.print("[bold cyan]🔒 CVE Report Aggregator[/bold cyan]")


def display_header(mode: str, scanner: str, scanner_version: str) -> None:
    """Display application header with configuration details.

    Args:
        mode: Aggregation mode
        scanner: Scanner type
        scanner_version: Scanner version string
    """
    header_text = (
        f"[bold cyan]🔒 Vulnerability Report Aggregator[/bold cyan]\n"
        f"[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]\n"
        f"[bold]Mode:[/bold] [magenta]{mode}[/magenta]\n"
        f"[bold]Scanner:[/bold] [yellow]{scanner.title()}[/yellow] [dim]v{scanner_version}[/dim]"
    )
    console.print()
    console.print(
        Panel(
            header_text,
            box=box.DOUBLE,
            border_style="bold cyan",
            padding=(1, 2),
        )
    )
    console.print()


def display_debug_config(app_config: Any) -> None:
    """Display configuration settings in debug mode.

    Args:
        app_config: Application configuration object
    """
    console.print()
    console.print(
        Panel(
            Pretty(app_config, expand_all=True),
            title="[bold cyan]Configuration Settings[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
    )
    console.print()


def display_critical_locals(local_vars: dict[str, Any]) -> None:
    """Display local variables in critical mode.

    Args:
        local_vars: Dictionary of local variables
    """
    console.print()
    console.print(
        Panel(
            Pretty(local_vars, expand_all=True),
            title="[bold red]Local Variables (CRITICAL)[/bold red]",
            border_style="red",
            padding=(1, 2),
        )
    )
    console.print()


def display_validation_error(error: MissingToolError) -> None:
    """Display validation error message.

    Args:
        error: MissingToolError with details
    """
    console.print(
        f"[red]Error:[/red] {error}",
        style="bold red",
    )


def display_success_summary(
    unified_json: list[Path],
    unified_csv: list[Path],
    executive_summaries: list[Path],
    tarball_path: Path | None = None,
) -> None:
    """Display success message with output files.

    Args:
        unified_json: List of unified JSON report files
        unified_csv: List of unified CSV report files
        executive_summaries: List of executive summary files
        tarball_path: Optional path to created tarball
    """
    console.print()

    if len(unified_json) == 1 and len(executive_summaries) == 1:
        # Single package - show all files
        message = "[bold green]Success![/bold green] Reports created:\n"
        message += f"  • Unified Report (JSON): [cyan]{unified_json[0].name}[/cyan]\n"
        if unified_csv:
            message += f"  • Unified Report (CSV): [cyan]{unified_csv[0].name}[/cyan]\n"
        message += f"  • Executive Summary: [cyan]{executive_summaries[0].name}[/cyan]"
        if tarball_path:
            message += f"\n  • Tarball Archive: [cyan]{tarball_path}[/cyan]"

        console.print(
            Panel(
                message,
                box=box.ROUNDED,
                border_style="green",
                padding=(0, 2),
            )
        )
    else:
        # Multiple packages - show all unified reports + single executive summary
        json_list = "\n".join([f"    • [cyan]{f.name}[/cyan]" for f in unified_json])
        csv_list = "\n".join([f"    • [cyan]{f.name}[/cyan]" for f in unified_csv])

        message = "[bold green]Success![/bold green] Created reports:\n\n"
        message += f"  [bold]Unified Reports (JSON):[/bold] ({len(unified_json)} packages)\n{json_list}\n\n"

        if unified_csv:
            message += f"  [bold]Unified Reports (CSV):[/bold] ({len(unified_csv)} packages)\n{csv_list}\n\n"

        if executive_summaries:
            message += f"  [bold]Executive Summary:[/bold]\n    • [cyan]{executive_summaries[0].name}[/cyan]"

        if tarball_path:
            message += f"\n\n  [bold]Tarball Archive:[/bold]\n    • [cyan]{tarball_path}[/cyan]"

        console.print(
            Panel(
                message,
                box=box.ROUNDED,
                border_style="green",
                padding=(0, 2),
            )
        )
    console.print()


def display_statistics(
    mode_value: str,
    effective_scanner: str,
    packages_scanned: int,
    unique_images: set[str],
    total_occurrences: int,
    unique_vulnerabilities: int,
    severity_breakdown: dict[str, int],
    enrichment_stats: dict[str, Any] | None = None,
) -> None:
    """Display summary statistics and severity breakdown.

    Args:
        mode_value: Aggregation mode
        effective_scanner: Scanner type
        packages_scanned: Number of packages scanned
        unique_images: Set of unique images
        total_occurrences: Total vulnerability occurrences
        unique_vulnerabilities: Number of unique vulnerabilities
        severity_breakdown: Count by severity level
        enrichment_stats: Optional enrichment statistics
    """
    # Create summary table
    table = Table(
        title="[bold cyan]📊 Executive Summary[/bold cyan]",
        box=box.DOUBLE_EDGE,
        show_header=True,
        header_style="bold magenta",
        border_style="cyan",
        title_style="bold cyan",
        padding=(0, 1),
    )
    table.add_column("Metric", style="bold cyan", no_wrap=True, width=25)
    table.add_column("Value", justify="right", style="bold yellow", width=20)

    table.add_row("Mode", f"[magenta]{mode_value}[/magenta]")
    table.add_row("Scanner", f"[yellow]{effective_scanner.title()}[/yellow]")
    table.add_row("Packages Scanned", f"[bold]{packages_scanned}[/bold]")
    table.add_row("Images Scanned", f"[bold]{len(unique_images)}[/bold]")
    table.add_row("Total Occurrences", f"[bold]{total_occurrences}[/bold]")
    table.add_row("Unique Vulnerabilities", f"[bold green]{unique_vulnerabilities}[/bold green]")

    # Add enrichment statistics if enabled
    if enrichment_stats:
        table.add_row("", "")  # Empty separator
        table.add_row("CVE Enrichment", "[bold cyan]Enabled[/bold cyan]")
        table.add_row("Enrichment Model", f"[dim]{enrichment_stats['model']}[/dim]")
        enriched_display = (
            f"[bold green]{enrichment_stats['total_enriched']}[/bold green] / "
            f"{enrichment_stats['total_eligible']} ({enrichment_stats['percentage']:.1f}%)"
        )
        table.add_row("CVEs Enriched", enriched_display)

    console.print(table)
    console.print()

    # Create severity breakdown table
    severity_table = Table(
        title="[bold cyan]⚠️  Severity Breakdown[/bold cyan]",
        box=box.HEAVY_EDGE,
        show_header=True,
        header_style="bold magenta",
        border_style="cyan",
        title_style="bold cyan",
        padding=(0, 1),
    )
    severity_table.add_column("Severity", style="bold", no_wrap=True, width=15)
    severity_table.add_column("Count", justify="right", width=10)
    severity_table.add_column("Bar", width=30)

    # Color-code severity levels with icons
    severity_config: dict[str, dict[str, str]] = {
        "Critical": {"color": "bold red", "icon": "🔴"},
        "High": {"color": "red", "icon": "🟠"},
        "Medium": {"color": "yellow", "icon": "🟡"},
        "Low": {"color": "blue", "icon": "🔵"},
        "Negligible": {"color": "dim", "icon": "⚪"},
        "Unknown": {"color": "dim", "icon": "❓"},
    }

    # Calculate max count for bar chart
    max_count = max(severity_breakdown.values()) if severity_breakdown.values() else 1

    severity_order = ["Critical", "High", "Medium", "Low", "Negligible", "Unknown"]
    for severity in severity_order:
        count = severity_breakdown.get(severity, 0)
        config_item = severity_config.get(severity, {"color": "white", "icon": "⚫"})
        color = config_item["color"]
        icon = config_item["icon"]

        # Create bar chart
        bar_length = int((count / max_count) * 20) if max_count > 0 and count > 0 else 0
        bar = "█" * bar_length

        severity_table.add_row(
            f"{icon} [{color}]{severity}[/{color}]",
            f"[{color}]{count}[/{color}]",
            f"[{color}]{bar}[/{color}]",
        )

    console.print(severity_table)
    console.print()


@click.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    epilog="[link=https://github.com/mkm29/cve-report-aggregator]https://github.com/mkm29/cve-report-aggregator[/link]",
)
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to YAML configuration file.",
    show_default=False,
)
@click.option(
    "-i",
    "--input-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Input directory containing scan report files.",
    show_default=True,
)
@click.option(
    "-o",
    "--output-file",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Output file path for the unified report.",
    show_default=True,
)
@click.option(
    "-d",
    "--output-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Output directory for all artifacts (JSON, CSV, summaries, tarball). Default: ~/output",
    show_default=True,
)
@click.option(
    "--local-only",
    is_flag=True,
    default=None,
    help="Only scan local Zarf packages (skip remote downloads).",
)
@click.option(
    "-s",
    "--scanner",
    type=click.Choice(["grype", "trivy", "both"], case_sensitive=False),
    default=None,
    help="[yellow]grype[/yellow], [yellow]trivy[/yellow], or [yellow]both[/yellow] vulnerability scanners.",
    show_default=True,
)
@click.option(
    "-l",
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False),
    default=None,
    help="Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    show_default=True,
)
@click.option(
    "-m",
    "--mode",
    type=click.Choice(
        ["highest-score", "first-occurrence", "grype-only", "trivy-only"],
        case_sensitive=False,
    ),
    default=None,
    help=(
        "[cyan]highest-score[/cyan]: Select highest CVSS 3.x score. "
        "[cyan]first-occurrence[/cyan]: Use first found. "
        "[cyan]grype-only[/cyan]: Grype scanner only. "
        "[cyan]trivy-only[/cyan]: Trivy scanner only."
    ),
    show_default=True,
)
@click.option(
    "--max-workers",
    type=int,
    default=None,
    help="Maximum number of concurrent workers for parallel scanning (default: auto-detect based on CPU count).",
    show_default=False,
)
@click.option(
    "--archive-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Directory for tarball archive output. Creates artifacts.tar.gz containing all outputs.",
    show_default=False,
)
@click.option(
    "--enrich-cves",
    is_flag=True,
    default=None,
    help="Enable CVE enrichment with OpenAI security context analysis.",
)
@click.option(
    "--openai-api-key",
    type=str,
    default=None,
    help="OpenAI API key (defaults to OPENAI_API_KEY env var).",
    show_default=False,
)
@click.option(
    "--openai-model",
    type=str,
    default=None,
    help="OpenAI model to use for enrichment (e.g., gpt-5-nano, gpt-4o).",
    show_default=True,
)
@click.option(
    "--batch-size",
    type=int,
    default=None,
    help="Number of CVEs to process per batch (1-100, default: 10).",
    show_default=True,
)
@click.option(
    "--max-cves-to-enrich",
    type=int,
    default=None,
    help="Maximum number of CVEs to enrich (None = all CVEs).",
    show_default=False,
)
@click.option(
    "--enrich-severity-filter",
    type=str,
    multiple=True,
    default=None,
    help=(
        "Severity levels to enrich (e.g., Critical, High). Default: Critical,High. "
        "Use multiple times for multiple severities."
    ),
    show_default=False,
)
@click.version_option(
    version=f"{__version__}",
    prog_name="CVE Report Aggregator",
    message=f"{__version__}",
)
def main(
    config: Path | None,
    input_dir: Path | None,
    output_file: Path | None,
    output_dir: Path | None,
    local_only: bool | None,
    scanner: str | None,
    log_level: str | None,
    mode: str | None,
    max_workers: int | None,
    archive_dir: Path | None,
    enrich_cves: bool | None,
    openai_api_key: str | None,
    openai_model: str | None,
    batch_size: int | None,
    max_cves_to_enrich: int | None,
    enrich_severity_filter: tuple[str, ...] | None,
) -> None:
    """[bold cyan]CVE Report Aggregator[/bold cyan]

    Aggregate and deduplicate vulnerability scan reports from Grype, Trivy, or both.

    Processes vulnerability scan reports from a directory, deduplicates vulnerabilities by CVE ID,
    and generates a unified JSON report with [magenta]CVSS 3.x scoring[/magenta] and occurrence tracking.

    [bold]Configuration Priority:[/bold]
      1. CLI arguments (highest)
      2. YAML config file (--config)
      3. Environment variables (CVE_AGGREGATOR_*)
      4. Default values (lowest)

    [bold]Examples:[/bold]

      [dim]# Aggregate Grype reports with highest CVSS scores[/dim]
      [cyan]$ cve-report-aggregator -i ./reports -o unified.json[/cyan]

      [dim]# Use configuration file[/dim]
      [cyan]$ cve-report-aggregator --config ./config.yaml[/cyan]

      [dim]# Use Trivy scanner with debug logging[/dim]
      [cyan]$ cve-report-aggregator -s trivy --log-level DEBUG[/cyan]

      [dim]# Run both Grype and Trivy scanners[/dim]
      [cyan]$ cve-report-aggregator -s both[/cyan]

      [dim]# Only scan local Zarf packages (skip remote downloads)[/dim]
      [cyan]$ cve-report-aggregator --local-only[/cyan]

      [dim]# Enrich CVEs with OpenAI (defaults to Critical and High severity only)[/dim]
      [cyan]$ export OPENAI_API_KEY=sk-...[/cyan]
      [cyan]$ cve-report-aggregator --enrich-cves[/cyan]

      [dim]# Enrich only top 10 CVEs with custom model[/dim]
      [cyan]$ cve-report-aggregator --enrich-cves --max-cves-to-enrich 10 --openai-model gpt-4o[/cyan]

      [dim]# Enrich all severity levels (not just Critical and High)[/dim]
      [cyan]$ cve-report-aggregator --enrich-cves --enrich-severity-filter Critical[/cyan]
      [cyan]  --enrich-severity-filter High --enrich-severity-filter Medium[/cyan]

      [dim]# First-occurrence mode (fastest)[/dim]
      [cyan]$ cve-report-aggregator -m first-occurrence[/cyan]
    """
    # Parse CLI arguments into structured format
    cli_args = parse_cli_arguments(
        input_dir=input_dir,
        output_file=output_file,
        output_dir=output_dir,
        local_only=local_only,
        scanner=scanner,
        log_level=log_level,
        mode=mode,
        max_workers=max_workers,
        archive_dir=archive_dir,
        enrich_cves=enrich_cves,
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        enrich_severity_filter=enrich_severity_filter,
    )

    # Load and validate configuration
    app_config = load_and_validate_config(cli_args, config, console)
    set_config(app_config)

    # Create application context
    context = AppContext(app_config)

    # Validate environment and tools
    effective_scanner, scanner_version = validate_environment(context, console)

    # Display header and configuration
    display_header(app_config.mode, effective_scanner, scanner_version)
    if app_config.log_level == "DEBUG":
        display_debug_config(app_config)
    elif app_config.log_level == "CRITICAL":
        display_critical_locals(locals())

    # Validate output file extension
    if app_config.output_file.suffix.lower() != ".json":
        console.print(
            f"[yellow]Warning:[/yellow] Output file does not have .json extension: {app_config.output_file}",
            style="dim",
        )

    # Execute aggregation workflow
    is_debug = app_config.log_level == "DEBUG"
    result = execute_aggregation_workflow(context, console, is_debug)

    # Categorize output files
    categorized = categorize_output_files(result.output_files)

    # Display success summary
    display_success_summary(
        categorized.unified_json,
        categorized.unified_csv,
        categorized.executive_summaries,
        result.tarball_path,
    )

    # Display statistics
    display_statistics(
        mode_value=app_config.mode,
        effective_scanner=effective_scanner,
        packages_scanned=result.packages_scanned,
        unique_images=result.unique_images,
        total_occurrences=result.total_occurrences,
        unique_vulnerabilities=result.unique_vulnerabilities,
        severity_breakdown=result.severity_breakdown,
        enrichment_stats=result.enrichment_stats,
    )


if __name__ == "__main__":
    main()
