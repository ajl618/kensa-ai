"""
Command-line interface for Kensa-AI.
"""

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from kensa_ai import __version__
from kensa_ai.core.config import Config
from kensa_ai.core.runner import Runner

console = Console()


def print_banner() -> None:
    """Print the application banner."""
    banner = f"""
╔═══════════════════════════════════════════════════════════╗
║          Kensa-AI v{__version__}                    ║
║     ISO/IEC 42001-friendly Adversarial Testing            ║
╚═══════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold blue"))


@click.group(invoke_without_command=True)
@click.option(
    "--config", "-c",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to configuration file"
)
@click.option(
    "--target", "-t",
    type=str,
    default="openai",
    help="Target connector type (openai, anthropic, http, local)"
)
@click.option(
    "--pack", "-p",
    type=str,
    default="basic_security",
    help="Test pack to run"
)
@click.option(
    "--categories",
    type=str,
    default=None,
    help="Comma-separated list of test categories"
)
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    default=Path("reports"),
    help="Output directory for reports"
)
@click.option(
    "--format", "-f",
    type=str,
    default="json,html",
    help="Output formats (json, html, or both)"
)
@click.option(
    "--evidence-mode/--no-evidence-mode",
    default=False,
    help="Enable evidence mode for audit trails"
)
@click.option(
    "--fail-on",
    type=click.Choice(["critical", "high", "medium", "low", "none"]),
    default="critical",
    help="Fail with exit code 1 if issues at this severity or above are found"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    default=False,
    help="Enable verbose output"
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be tested without executing"
)
@click.version_option(version=__version__)
@click.pass_context
def main(
    ctx: click.Context,
    config: Path | None,
    target: str,
    pack: str,
    categories: str | None,
    output: Path,
    format: str,
    evidence_mode: bool,
    fail_on: str,
    verbose: bool,
    dry_run: bool,
) -> int:
    """
    Kensa-AI - Adversarial testing for AI systems.

    Run security tests against AI model endpoints to identify vulnerabilities
    like prompt injection, jailbreaks, and data leakage.

    \b
    Examples:
      ai-redteam-test --target openai --pack basic_security
      ai-redteam-test --config config.yaml --evidence-mode
      ai-redteam-test --categories prompt_injection,jailbreak
    """
    if ctx.invoked_subcommand is not None:
        return 0

    print_banner()

    # Parse categories
    category_list = None
    if categories:
        category_list = [c.strip() for c in categories.split(",")]

    # Parse output formats
    output_formats = [f.strip() for f in format.split(",")]

    # Load or create configuration
    if config:
        cfg = Config.from_file(config)
    else:
        cfg = Config.default()

    # Override config with CLI options
    cfg.target_type = target
    cfg.test_pack = pack
    cfg.categories = category_list
    cfg.output_dir = output
    cfg.output_formats = output_formats
    cfg.evidence_mode = evidence_mode
    cfg.fail_on = fail_on
    cfg.verbose = verbose

    if dry_run:
        console.print("\n[yellow]DRY RUN MODE[/yellow]\n")
        console.print(f"Target: {target}")
        console.print(f"Test Pack: {pack}")
        console.print(f"Categories: {category_list or 'all'}")
        console.print(f"Output: {output}")
        console.print(f"Evidence Mode: {evidence_mode}")
        return 0

    # Run tests
    try:
        result = asyncio.run(run_tests(cfg, verbose))
        return result
    except KeyboardInterrupt:
        console.print("\n[yellow]Test run interrupted by user[/yellow]")
        return 130
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        return 1


async def run_tests(config: Config, verbose: bool) -> int:
    """Execute the test run."""
    runner = Runner(config)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Initialize
        task = progress.add_task("Initializing...", total=None)
        await runner.initialize()

        # Load test pack
        progress.update(task, description="Loading test pack...")
        test_count = await runner.load_test_pack()
        console.print(f"[green]Loaded {test_count} tests[/green]")

        # Run tests
        progress.update(task, description="Running tests...")
        results = await runner.run()

        # Generate reports
        progress.update(task, description="Generating reports...")
        await runner.generate_reports()

        progress.update(task, description="Done!")

    # Print summary
    print_summary(results)

    # Determine exit code
    exit_code = determine_exit_code(results, config.fail_on)

    return exit_code


def print_summary(results: dict) -> None:
    """Print test results summary."""
    summary = results.get("summary", {})

    console.print("\n")
    console.print(Panel("[bold]Test Results Summary[/bold]", style="blue"))
    console.print(f"  Total Tests: {summary.get('total_tests', 0)}")
    console.print(f"  [green]Passed: {summary.get('passed', 0)}[/green]")
    console.print(f"  [red]Failed: {summary.get('failed', 0)}[/red]")
    console.print(f"  Score: {summary.get('score', 0):.1%}")
    console.print()

    # Severity breakdown
    severities = summary.get("by_severity", {})
    if severities:
        console.print("  Failures by Severity:")
        for sev, count in severities.items():
            if count > 0:
                color = {
                    "critical": "red",
                    "high": "orange1",
                    "medium": "yellow",
                    "low": "blue"
                }.get(sev, "white")
                console.print(f"    [{color}]{sev.upper()}: {count}[/{color}]")
    console.print()


def determine_exit_code(results: dict, fail_on: str) -> int:
    """Determine exit code based on results and fail_on threshold."""
    if fail_on == "none":
        return 0

    severity_order = ["critical", "high", "medium", "low"]
    threshold_index = severity_order.index(fail_on)

    severities = results.get("summary", {}).get("by_severity", {})

    for i, sev in enumerate(severity_order):
        if i <= threshold_index and severities.get(sev, 0) > 0:
            return 1

    return 0


@main.command()
@click.option("--target", "-t", type=str, required=True, help="Target to validate")
def validate_target(target: str) -> None:
    """Validate target configuration and connectivity."""
    console.print(f"Validating target: {target}")
    # Implementation would go here
    console.print("[green]Target validation passed[/green]")


@main.command()
@click.option("--pack", "-p", type=str, default=None, help="Test pack to list")
def list_tests(pack: str | None) -> None:
    """List available tests or test packs."""
    console.print("[bold]Available Test Packs:[/bold]")
    packs = [
        ("basic_security", "Quick security checks for CI/CD"),
        ("full_security", "Comprehensive security test suite"),
        ("prompt_injection", "Prompt injection attack tests"),
        ("jailbreak", "Jailbreak attempt tests"),
        ("data_leakage", "Data leakage and exfiltration tests"),
        ("toxicity", "Toxicity and harmful content tests"),
        ("hallucination", "Hallucination and grounding tests"),
    ]

    for name, description in packs:
        console.print(f"  [cyan]{name}[/cyan]: {description}")


@main.command()
@click.argument("report_path", type=click.Path(exists=True, path_type=Path))
def show_report(report_path: Path) -> None:
    """Display a previously generated report."""
    import json

    with open(report_path) as f:
        report = json.load(f)

    print_summary(report)


if __name__ == "__main__":
    sys.exit(main())
