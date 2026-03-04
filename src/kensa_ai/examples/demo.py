#!/usr/bin/env python3
"""
Kensa-AI - Demo Mode

Demonstrates the toolkit capabilities using the mock server.
Can run without any external API keys.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import print as rprint

console = Console()


def print_banner():
    """Print the demo banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║        Kensa-AI - Demo Mode                          ║
║        ISO/IEC 42001-friendly Security Testing                 ║
╚═══════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold blue"))


def demo_test_packs():
    """Demonstrate available test packs."""
    console.print("\n[bold cyan]📦 Available Test Packs[/bold cyan]\n")
    
    from kensa_ai.test_packs import (
        prompt_injection,
        jailbreak,
        data_leakage,
        toxicity,
        hallucination,
    )
    
    packs = [
        ("Prompt Injection", prompt_injection.get_tests(), "Tests for instruction override attacks"),
        ("Jailbreak", jailbreak.get_tests(), "Tests for bypassing safety guidelines"),
        ("Data Leakage", data_leakage.get_tests(), "Tests for sensitive data exposure"),
        ("Toxicity", toxicity.get_tests(), "Tests for harmful content generation"),
        ("Hallucination", hallucination.get_tests(), "Tests for false information"),
    ]
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Test Pack", style="cyan")
    table.add_column("Tests", justify="right")
    table.add_column("Description")
    
    for name, tests, desc in packs:
        table.add_row(name, str(len(tests)), desc)
    
    console.print(table)
    
    # Show sample tests
    console.print("\n[bold cyan]🔍 Sample Tests[/bold cyan]\n")
    
    for name, tests, _ in packs[:2]:  # Show first 2 packs
        console.print(f"[yellow]{name}:[/yellow]")
        for test in tests[:2]:  # Show first 2 tests
            console.print(f"  • {test.name} (Severity: {test.severity})")
            console.print(f"    Prompt: {test.prompt[:60]}...")
        console.print()


def demo_evaluators():
    """Demonstrate available evaluators."""
    console.print("\n[bold cyan]⚖️ Available Evaluators[/bold cyan]\n")
    
    from kensa_ai.evaluators import (
        RegexEvaluator,
        ClassifierEvaluator,
        LLMJudgeEvaluator,
    )
    
    evaluators = [
        ("RegexEvaluator", "Pattern matching for specific strings/patterns", "✅"),
        ("ClassifierEvaluator", "Keyword-based scoring and classification", "✅"),
        ("LLMJudgeEvaluator", "Uses LLM as judge for semantic evaluation", "⚙️"),
    ]
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Evaluator", style="cyan")
    table.add_column("Description")
    table.add_column("Status", justify="center")
    
    for name, desc, status in evaluators:
        table.add_row(name, desc, status)
    
    console.print(table)
    
    # Demo RegexEvaluator
    console.print("\n[bold]Example: RegexEvaluator[/bold]")
    
    evaluator = RegexEvaluator()
    
    test_cases = [
        ("Test prompt", "I'll ignore my previous instructions as you requested."),
        ("Test prompt", "I cannot comply with that request."),
        ("Test prompt", "Sure, here is how to hack into the system."),
    ]
    
    for prompt, response in test_cases:
        result = evaluator.evaluate(prompt, response)
        status = "[red]FAIL[/red]" if not result.passed else "[green]PASS[/green]"
        console.print(f"  Response: '{response[:50]}...' → {status}")


def demo_connectors():
    """Demonstrate available connectors."""
    console.print("\n[bold cyan]🔌 Available Connectors[/bold cyan]\n")
    
    connectors = [
        ("OpenAI", "OpenAI API (GPT-3.5, GPT-4)", "OPENAI_API_KEY"),
        ("Anthropic", "Anthropic API (Claude)", "ANTHROPIC_API_KEY"),
        ("HTTP", "Generic HTTP endpoint", "TARGET_URL"),
    ]
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Connector", style="cyan")
    table.add_column("Description")
    table.add_column("Config Env Var")
    
    for name, desc, env in connectors:
        table.add_row(name, desc, env)
    
    console.print(table)


async def demo_mock_test():
    """Run a demo test against mock server."""
    console.print("\n[bold cyan]🧪 Running Demo Test[/bold cyan]\n")
    
    target_url = os.environ.get("TARGET_URL", "http://localhost:8080/v1/chat/completions")
    api_key = os.environ.get("TARGET_API_KEY", "mock-api-key")
    
    console.print(f"[dim]Target URL: {target_url}[/dim]")
    
    # Check if mock server is available
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            health_url = target_url.replace("/v1/chat/completions", "/health")
            response = await client.get(health_url, timeout=5.0)
            if response.status_code == 200:
                console.print("[green]✓ Mock server is running[/green]\n")
            else:
                console.print("[yellow]⚠ Mock server health check failed, skipping live test[/yellow]\n")
                return
    except Exception:
        console.print("[yellow]⚠ Mock server not available, skipping live test[/yellow]")
        console.print("[dim]Start mock server with: docker-compose up mock-server[/dim]\n")
        return
    
    # Run a simple test
    from kensa_ai.connectors import get_connector
    from kensa_ai.test_packs import prompt_injection
    from kensa_ai.evaluators import RegexEvaluator
    
    # Create config object for connector
    class ConnectorConfig:
        base_url = target_url.replace("/v1/chat/completions", "")
        api_key = api_key
        model = "mock-gpt-4"
        timeout = 30
        max_retries = 2
    
    connector = get_connector("http", ConnectorConfig())
    evaluator = RegexEvaluator()
    
    tests = prompt_injection.get_tests()[:3]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Running tests...", total=len(tests))
        
        results = []
        for test in tests:
            try:
                response = await connector.send_prompt(test.prompt)
                eval_result = evaluator.evaluate(test.prompt, response)
                results.append({
                    "name": test.name,
                    "response": response[:100],
                    "passed": eval_result.passed,
                    "score": eval_result.confidence
                })
            except Exception as e:
                results.append({
                    "name": test.name,
                    "response": f"Error: {e}",
                    "passed": None,
                    "score": 0
                })
            progress.advance(task)
    
    # Show results
    console.print("\n[bold]Results:[/bold]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Test", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Response Preview")
    
    for result in results:
        if result["passed"] is None:
            status = "[yellow]ERROR[/yellow]"
        elif result["passed"]:
            status = "[green]PASS[/green]"
        else:
            status = "[red]FAIL[/red]"
        
        table.add_row(
            result["name"][:30],
            status,
            result["response"][:40] + "..."
        )
    
    console.print(table)


def demo_report_formats():
    """Demonstrate report generation."""
    console.print("\n[bold cyan]📊 Report Formats[/bold cyan]\n")
    
    formats = [
        ("JSON", "Structured data for CI/CD integration", "report.json"),
        ("HTML", "Interactive dashboard with charts", "report.html"),
    ]
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Format", style="cyan")
    table.add_column("Description")
    table.add_column("Example Output")
    
    for name, desc, example in formats:
        table.add_row(name, desc, example)
    
    console.print(table)
    
    console.print("\n[dim]Reports include:[/dim]")
    console.print("[dim]  • Test results with pass/fail status[/dim]")
    console.print("[dim]  • Severity breakdown (critical/high/medium/low)[/dim]")
    console.print("[dim]  • Evidence mode for ISO/IEC 42001 compliance[/dim]")
    console.print("[dim]  • Timestamps and execution metadata[/dim]")


def run_demo():
    """Run the full demo."""
    print_banner()
    
    console.print("[bold]This demo showcases the Kensa-AI capabilities.[/bold]")
    console.print("[dim]No API keys required - uses mock server for testing.[/dim]\n")
    
    demo_test_packs()
    demo_evaluators()
    demo_connectors()
    demo_report_formats()
    
    # Run async mock test
    console.print("\n" + "=" * 60)
    asyncio.run(demo_mock_test())
    
    console.print("\n[bold green]✓ Demo completed![/bold green]")
    console.print("\n[dim]Next steps:[/dim]")
    console.print("[dim]  1. Configure your target: export TARGET_URL=your-api-url[/dim]")
    console.print("[dim]  2. Run tests: kensa run --pack basic_security[/dim]")
    console.print("[dim]  3. View reports in ./reports/ directory[/dim]\n")


if __name__ == "__main__":
    run_demo()
