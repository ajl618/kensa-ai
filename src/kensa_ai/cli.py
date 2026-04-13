"""
Command-line interface for Kensa-AI.
"""

import asyncio
import json
import sys
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from kensa_ai import __version__
from kensa_ai.connectors import get_connector
from kensa_ai.core.config import Config
from kensa_ai.core.runner import Runner
from kensa_ai.test_packs import TEST_PACKS, load_test_pack

console = Console()


def _parse_csv(value: str | None) -> list[str] | None:
    """Parse comma-separated CLI input into a normalized list."""
    if value is None:
        return None

    values = [item.strip() for item in value.split(",") if item.strip()]
    return values or None


def _apply_tag_filters(
    tests: list[dict],
    include_tags: list[str] | None,
    exclude_tags: list[str] | None,
) -> list[dict]:
    """Filter serialized tests by include/exclude tag rules."""
    filtered = tests

    if include_tags:
        include = {tag.lower() for tag in include_tags}
        filtered = [
            test for test in filtered if any(tag.lower() in include for tag in test.get("tags", []))
        ]

    if exclude_tags:
        exclude = {tag.lower() for tag in exclude_tags}
        filtered = [
            test
            for test in filtered
            if not any(tag.lower() in exclude for tag in test.get("tags", []))
        ]

    return filtered


def _apply_severity_filters(
    tests: list[dict],
    severities: list[str] | None,
) -> list[dict]:
    """Filter serialized tests by severity values."""
    if not severities:
        return tests

    allowed = {severity.lower() for severity in severities}
    return [test for test in tests if str(test.get("severity", "")).lower() in allowed]


def compare_reports_data(current: dict, baseline: dict) -> dict:
    """Compare two report payloads and return regression summary."""
    current_summary = current.get("summary", {})
    baseline_summary = baseline.get("summary", {})

    severity_order = ["critical", "high", "medium", "low"]
    current_by_severity = current_summary.get("by_severity", {})
    baseline_by_severity = baseline_summary.get("by_severity", {})

    severity_delta = {
        severity: int(current_by_severity.get(severity, 0)) - int(baseline_by_severity.get(severity, 0))
        for severity in severity_order
    }

    regressions = {severity: delta for severity, delta in severity_delta.items() if delta > 0}

    return {
        "baseline_run_id": baseline.get("run_id"),
        "current_run_id": current.get("run_id"),
        "score_delta": float(current_summary.get("score", 0.0))
        - float(baseline_summary.get("score", 0.0)),
        "failed_delta": int(current_summary.get("failed", 0))
        - int(baseline_summary.get("failed", 0)),
        "errors_delta": int(current_summary.get("errors", 0))
        - int(baseline_summary.get("errors", 0)),
        "severity_delta": severity_delta,
        "regressions": regressions,
        "has_regression": len(regressions) > 0,
    }


def extract_failed_test_names(report_data: dict) -> list[str]:
    """Extract failed/error test names from a report payload."""
    names = []
    for item in report_data.get("results", []):
        status = item.get("status")
        if status in {"failed", "error"}:
            test_name = item.get("test", {}).get("name")
            if test_name:
                names.append(str(test_name))
    return names


def build_history_context(report_data: dict) -> tuple[dict[str, dict], dict[str, float]]:
    """Build per-test outcomes and per-category failure rates from a previous report."""
    outcomes: dict[str, dict] = {}

    for item in report_data.get("results", []):
        test = item.get("test", {})
        test_name = test.get("name")
        if not test_name:
            continue

        result = item.get("result") or {}
        outcomes[str(test_name)] = {
            "status": item.get("status"),
            "confidence": float(result.get("confidence", 0.0) or 0.0),
            "execution_time_ms": float(result.get("execution_time_ms", 0.0) or 0.0),
            "category": test.get("category"),
            "severity": test.get("severity"),
        }

    rates: dict[str, float] = {}
    by_category = report_data.get("summary", {}).get("by_category", {})
    for category, stats in by_category.items():
        passed = int(stats.get("passed", 0))
        failed = int(stats.get("failed", 0))
        errors = int(stats.get("error", 0))
        total = passed + failed + errors
        if total > 0:
            rates[str(category)] = failed / total

    return outcomes, rates


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
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to configuration file",
)
@click.option(
    "--target", "-t", type=str, default="openai", help="Target connector type"
)
@click.option("--pack", "-p", type=str, default="basic_security", help="Test pack to run")
@click.option(
    "--categories", type=str, default=None, help="Comma-separated list of test categories"
)
@click.option("--tags", type=str, default=None, help="Comma-separated test tags to include")
@click.option(
    "--exclude-tags", type=str, default=None, help="Comma-separated test tags to exclude"
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("reports"),
    help="Output directory for reports",
)
@click.option(
    "--format",
    "-f",
    type=str,
    default="json,html",
    help="Output formats (json, html, csv, or comma-separated)",
)
@click.option(
    "--severities",
    type=str,
    default=None,
    help="Comma-separated severities to include (critical,high,medium,low,info)",
)
@click.option(
    "--evidence-mode/--no-evidence-mode",
    default=False,
    help="Enable evidence mode for audit trails",
)
@click.option(
    "--fail-on",
    type=click.Choice(["critical", "high", "medium", "low", "none"]),
    default="critical",
    help="Fail with exit code 1 if issues at this severity or above are found",
)
@click.option(
    "--fail-on-error/--ignore-errors",
    default=True,
    help="Fail with exit code 1 when technical execution errors occur",
)
@click.option(
    "--parallel",
    type=click.IntRange(min=1),
    default=1,
    help="Number of tests to execute concurrently",
)
@click.option(
    "--max-failures",
    type=click.IntRange(min=1),
    default=None,
    help="Stop execution early after this many failed tests",
)
@click.option(
    "--planner-mode",
    type=click.Choice(["off", "risk_per_second"]),
    default="off",
    help="Execution planner strategy (off or risk_per_second)",
)
@click.option(
    "--time-budget-seconds",
    type=float,
    default=None,
    help="Maximum execution budget in seconds for planner-based selection",
)
@click.option(
    "--smart-priority/--no-smart-priority",
    default=False,
    help="Use severity + historical report context to prioritize test execution",
)
@click.option(
    "--max-per-category",
    type=click.IntRange(min=1),
    default=50,
    help="Maximum number of tests to load per category",
)
@click.option(
    "--max-tests",
    type=click.IntRange(min=1),
    default=None,
    help="Maximum total number of tests to execute after filtering",
)
@click.option(
    "--randomize/--no-randomize",
    default=False,
    help="Randomize test order before execution",
)
@click.option(
    "--seed",
    type=int,
    default=None,
    help="Optional random seed for reproducible test order",
)
@click.option(
    "--baseline-report",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Optional baseline JSON report to compare against",
)
@click.option(
    "--focus-failures-from",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Use failed/error tests from a baseline JSON report for smart focus",
)
@click.option(
    "--history-report",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Historical JSON report used for smart-priority scoring",
)
@click.option(
    "--focus-mode",
    type=click.Choice(["off", "prioritize", "only"]),
    default="off",
    help="How to apply focus list: off, prioritize, or only",
)
@click.option(
    "--fail-on-regression/--ignore-regression",
    default=True,
    help="Fail with exit code 1 when baseline comparison detects regression",
)
@click.option("--verbose", "-v", is_flag=True, default=False, help="Enable verbose output")
@click.option(
    "--dry-run", is_flag=True, default=False, help="Show what would be tested without executing"
)
@click.version_option(version=__version__)
@click.pass_context
def main(
    ctx: click.Context,
    config: Path | None,
    target: str,
    pack: str,
    categories: str | None,
    tags: str | None,
    exclude_tags: str | None,
    severities: str | None,
    output: Path,
    format: str,
    evidence_mode: bool,
    fail_on: str,
    fail_on_error: bool,
    parallel: int,
    max_failures: int | None,
    planner_mode: str,
    time_budget_seconds: float | None,
    smart_priority: bool,
    max_per_category: int,
    max_tests: int | None,
    randomize: bool,
    seed: int | None,
    baseline_report: Path | None,
    focus_failures_from: Path | None,
    history_report: Path | None,
    focus_mode: str,
    fail_on_regression: bool,
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
    category_list = _parse_csv(categories)
    include_tags = _parse_csv(tags)
    exclude_tag_list = _parse_csv(exclude_tags)
    severity_list = _parse_csv(severities)

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
    cfg.tags = include_tags
    cfg.exclude_tags = exclude_tag_list
    cfg.severities = severity_list
    cfg.output_dir = output
    cfg.output_formats = output_formats
    cfg.evidence_mode = evidence_mode
    cfg.fail_on = fail_on
    cfg.fail_on_error = fail_on_error
    cfg.parallel = parallel
    cfg.max_failures = max_failures
    cfg.planner_mode = planner_mode
    cfg.time_budget_seconds = time_budget_seconds
    cfg.smart_priority = smart_priority
    cfg.max_tests_per_category = max_per_category
    cfg.max_tests = max_tests
    cfg.randomize = randomize
    cfg.seed = seed
    cfg.focus_mode = focus_mode
    cfg.verbose = verbose

    if focus_failures_from is not None:
        with open(focus_failures_from) as f:
            focus_data = json.load(f)
        cfg.focus_failed_test_names = extract_failed_test_names(focus_data)

        if not cfg.focus_failed_test_names and focus_mode == "only":
            raise click.BadParameter(
                "focus-mode 'only' requires at least one failed/error test in focus-failures-from report"
            )

        if not cfg.focus_failed_test_names and focus_mode == "prioritize":
            console.print(
                "[yellow]No failed/error tests found in focus report; disabling focus mode.[/yellow]"
            )
            cfg.focus_mode = "off"

    if history_report is not None:
        with open(history_report) as f:
            history_data = json.load(f)
        outcomes, rates = build_history_context(history_data)
        cfg.history_test_outcomes = outcomes
        cfg.history_category_failure_rates = rates

    if dry_run:
        preview_runner = Runner(cfg)
        test_count = asyncio.run(preview_runner.load_test_pack())
        by_category: dict[str, int] = {}
        for test in preview_runner.tests:
            by_category[test.category] = by_category.get(test.category, 0) + 1

        console.print("\n[yellow]DRY RUN MODE[/yellow]\n")
        console.print(f"Target: {target}")
        console.print(f"Test Pack: {pack}")
        console.print(f"Categories: {category_list or 'all'}")
        console.print(f"Include tags: {include_tags or 'none'}")
        console.print(f"Exclude tags: {exclude_tag_list or 'none'}")
        console.print(f"Severities: {severity_list or 'all'}")
        console.print(f"Output: {output}")
        console.print(f"Evidence Mode: {evidence_mode}")
        console.print(f"Fail on execution errors: {fail_on_error}")
        console.print(f"Parallel workers: {parallel}")
        console.print(f"Max failures before stop: {max_failures or 'disabled'}")
        console.print(f"Planner mode: {planner_mode}")
        console.print(f"Time budget (seconds): {time_budget_seconds or 'disabled'}")
        console.print(f"Smart priority: {smart_priority}")
        console.print(f"Max tests per category: {max_per_category}")
        console.print(f"Max total tests: {max_tests or 'unlimited'}")
        console.print(f"Randomize order: {randomize}")
        console.print(f"Random seed: {seed if seed is not None else 'none'}")
        console.print(f"Focus mode: {focus_mode}")
        console.print(
            "Focused tests from baseline: "
            f"{len(cfg.focus_failed_test_names or []) if focus_failures_from is not None else 0}"
        )
        console.print(
            "Historical signals loaded: "
            f"{len(cfg.history_test_outcomes or {}) if history_report is not None else 0} tests"
        )
        console.print(f"Planned tests: {test_count}")

        if by_category:
            console.print("\nCategory distribution:")
            for category, count in sorted(by_category.items()):
                console.print(f"  - {category}: {count}")

        return 0

    # Run tests
    try:
        result = asyncio.run(
            run_tests(
                cfg,
                verbose,
                baseline_report=baseline_report,
                fail_on_regression=fail_on_regression,
            )
        )
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


async def run_tests(
    config: Config,
    verbose: bool,
    baseline_report: Path | None = None,
    fail_on_regression: bool = True,
) -> int:
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
    exit_code = determine_exit_code(results, config.fail_on, config.fail_on_error)

    if baseline_report is not None:
        with open(baseline_report) as f:
            baseline_data = json.load(f)

        comparison = compare_reports_data(results, baseline_data)
        print_comparison(comparison)

        if fail_on_regression and comparison["has_regression"]:
            exit_code = 1

    return exit_code


def print_comparison(comparison: dict) -> None:
    """Print baseline comparison result."""
    console.print("\n")
    console.print(Panel("[bold]Baseline Comparison[/bold]", style="magenta"))
    console.print(f"  Score delta: {comparison['score_delta']:+.2%}")
    console.print(f"  Failed tests delta: {comparison['failed_delta']:+d}")
    console.print(f"  Execution errors delta: {comparison['errors_delta']:+d}")

    sev_delta = comparison.get("severity_delta", {})
    if sev_delta:
        console.print("  Severity deltas:")
        for severity in ["critical", "high", "medium", "low"]:
            delta = int(sev_delta.get(severity, 0))
            if delta != 0:
                console.print(f"    {severity.upper()}: {delta:+d}")

    if comparison.get("has_regression"):
        console.print("  [red]Regression detected[/red]")
    else:
        console.print("  [green]No severity regression detected[/green]")


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
                    "low": "blue",
                }.get(sev, "white")
                console.print(f"    [{color}]{sev.upper()}: {count}[/{color}]")
    console.print()


def determine_exit_code(results: dict, fail_on: str, fail_on_error: bool = True) -> int:
    """Determine exit code based on results and fail_on threshold."""
    summary = results.get("summary", {})

    if fail_on_error and summary.get("errors", 0) > 0:
        return 1

    if fail_on == "none":
        return 0

    severity_order = ["critical", "high", "medium", "low"]
    threshold_index = severity_order.index(fail_on)

    severities = summary.get("by_severity", {})

    for i, sev in enumerate(severity_order):
        if i <= threshold_index and severities.get(sev, 0) > 0:
            return 1

    return 0


@main.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Optional config file",
)
@click.option("--target", "-t", type=str, default=None, help="Target connector type")
@click.option("--base-url", type=str, default=None, help="Override target base URL")
@click.option("--model", type=str, default=None, help="Override model name")
def validate_target(config: Path | None, target: str | None, base_url: str | None, model: str | None) -> None:
    """Validate target configuration and connectivity."""

    async def _validate() -> bool:
        cfg = Config.from_file(config) if config else Config.default()

        if target:
            cfg.target_type = target
            cfg.target.type = target
        if base_url:
            cfg.target.base_url = base_url
        if model:
            cfg.target.model = model

        console.print(f"Validating target type: [cyan]{cfg.target_type}[/cyan]")
        console.print(f"Base URL: {cfg.target.base_url}")
        console.print(f"Model: {cfg.target.model}")

        connector = get_connector(cfg.target_type, cfg.target)
        try:
            is_valid = await connector.validate()
        finally:
            await connector.close()

        if not is_valid:
            raise ConnectionError("Target did not pass validation checks")

        return True

    try:
        asyncio.run(_validate())
        console.print("[green]Target validation passed[/green]")
    except Exception as e:
        console.print(f"[red]Target validation failed:[/red] {e}")
        raise click.exceptions.Exit(1) from e


@main.command()
@click.option("--pack", "-p", type=str, default=None, help="Pack to inspect in detail")
@click.option(
    "--categories", type=str, default=None, help="Comma-separated categories to include"
)
@click.option("--tags", type=str, default=None, help="Comma-separated tags to include")
@click.option("--exclude-tags", type=str, default=None, help="Comma-separated tags to exclude")
@click.option(
    "--severities",
    type=str,
    default=None,
    help="Comma-separated severities to include (critical,high,medium,low,info)",
)
@click.option("--max-per-category", type=click.IntRange(min=1), default=50)
@click.option("--max-tests", type=click.IntRange(min=1), default=None)
@click.option("--limit", type=click.IntRange(min=1), default=25, help="Rows to display")
@click.option("--json-output", is_flag=True, default=False, help="Print machine-readable JSON")
def list_tests(
    pack: str | None,
    categories: str | None,
    tags: str | None,
    exclude_tags: str | None,
    severities: str | None,
    max_per_category: int,
    max_tests: int | None,
    limit: int,
    json_output: bool,
) -> None:
    """List available test packs or inspect concrete tests with filters."""
    if pack is None:
        table = Table(title="Available Test Packs", box=box.SIMPLE_HEAD)
        table.add_column("Pack", style="cyan")
        table.add_column("Description")

        descriptions = {
            "basic_security": "Quick security checks for CI/CD",
            "full_security": "Comprehensive security test suite",
            "ci_quick": "Fast checks for pull requests",
            "prompt_injection": "Prompt injection attack tests",
            "jailbreak": "Jailbreak attempt tests",
            "data_leakage": "Data leakage and exfiltration tests",
            "toxicity": "Toxicity and harmful content tests",
            "hallucination": "Hallucination and grounding tests",
        }

        for name in sorted(TEST_PACKS.keys()):
            table.add_row(name, descriptions.get(name, "Custom pack"))

        console.print(table)
        console.print("\nUse [cyan]kensa-ai list-tests --pack <name>[/cyan] for detailed test listing.")
        return

    category_list = _parse_csv(categories)
    include_tags = _parse_csv(tags)
    exclude_tag_list = _parse_csv(exclude_tags)
    severity_list = _parse_csv(severities)

    tests = load_test_pack(
        pack_name=pack,
        categories=category_list,
        max_per_category=max_per_category,
    )

    serialized_tests = [test.to_dict() for test in tests if test.enabled]
    serialized_tests = _apply_tag_filters(serialized_tests, include_tags, exclude_tag_list)
    serialized_tests = _apply_severity_filters(serialized_tests, severity_list)

    if max_tests is not None:
        serialized_tests = serialized_tests[:max_tests]

    if json_output:
        payload = {
            "pack": pack,
            "count": len(serialized_tests),
            "filters": {
                "categories": category_list,
                "tags": include_tags,
                "exclude_tags": exclude_tag_list,
                "severities": severity_list,
                "max_per_category": max_per_category,
                "max_tests": max_tests,
            },
            "tests": serialized_tests,
        }
        console.print(json.dumps(payload, indent=2))
        return

    category_counts: dict[str, int] = {}
    for test in serialized_tests:
        category = test.get("category", "general")
        category_counts[category] = category_counts.get(category, 0) + 1

    console.print(f"\n[bold]Pack:[/bold] {pack}")
    console.print(f"[bold]Matching tests:[/bold] {len(serialized_tests)}")
    if category_counts:
        summary = ", ".join(
            f"{category}={count}" for category, count in sorted(category_counts.items())
        )
        console.print(f"[bold]By category:[/bold] {summary}")

    table = Table(title="Test Preview", box=box.SIMPLE_HEAD)
    table.add_column("Name", style="cyan", overflow="fold")
    table.add_column("Category")
    table.add_column("Severity")
    table.add_column("Tags", overflow="fold")

    for test in serialized_tests[:limit]:
        table.add_row(
            test.get("name", ""),
            test.get("category", ""),
            test.get("severity", ""),
            ", ".join(test.get("tags", [])) or "-",
        )

    console.print(table)

    if len(serialized_tests) > limit:
        console.print(f"Showing first {limit} tests. Increase --limit to view more.")


@main.command()
@click.argument("report_path", type=click.Path(exists=True, path_type=Path))
def show_report(report_path: Path) -> None:
    """Display a previously generated report."""
    import json

    with open(report_path) as f:
        report = json.load(f)

    print_summary(report)


@main.command()
@click.argument("current_report", type=click.Path(exists=True, path_type=Path))
@click.argument("baseline_report", type=click.Path(exists=True, path_type=Path))
@click.option("--json-output", is_flag=True, default=False, help="Print machine-readable JSON")
def compare_reports(current_report: Path, baseline_report: Path, json_output: bool) -> None:
    """Compare a current JSON report against a baseline report."""
    with open(current_report) as f:
        current_data = json.load(f)
    with open(baseline_report) as f:
        baseline_data = json.load(f)

    comparison = compare_reports_data(current_data, baseline_data)

    if json_output:
        console.print(json.dumps(comparison, indent=2))
        return

    print_comparison(comparison)


if __name__ == "__main__":
    sys.exit(main())
