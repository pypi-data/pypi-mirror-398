"""
Governance Scanner CLI

Command-line tool for scanning and validating governance policies.
"""

import json
from enum import Enum
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(
    name="tork",
    help="Tork Governance CLI - Universal governance tools for AI agents",
)
console = Console()


class OutputFormat(str, Enum):
    text = "text"
    json = "json"
    sarif = "sarif"


SEVERITY_COLORS = {
    "critical": "red bold",
    "high": "red",
    "medium": "yellow",
    "low": "blue",
    "info": "dim",
}


@app.command()
def scan(
    path: Path = typer.Argument(
        ...,
        help="Path to file or directory to scan",
    ),
    output: OutputFormat = typer.Option(
        OutputFormat.text,
        "--output",
        "-o",
        help="Output format (text/json/sarif)",
    ),
    severity: str = typer.Option(
        "info",
        "--severity",
        "-s",
        help="Minimum severity to report (critical/high/medium/low/info)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """Scan MCP configurations for security vulnerabilities."""
    from tork.scanner import MCPScanner, ScanSeverity, ScanResult
    
    console.print(Panel.fit(
        "[bold blue]Tork MCP Security Scanner[/bold blue]",
        border_style="blue",
    ))
    
    if not path.exists():
        console.print(f"[red]Error: Path does not exist: {path}[/red]")
        raise typer.Exit(1)
    
    try:
        min_severity = ScanSeverity(severity.lower())
    except ValueError:
        console.print(f"[red]Error: Invalid severity: {severity}[/red]")
        console.print("Valid options: critical, high, medium, low, info")
        raise typer.Exit(1)
    
    scanner = MCPScanner()
    
    if path.is_file():
        findings = scanner.scan_file(str(path))
        result = ScanResult(
            findings=findings,
            files_scanned=1,
            scan_duration=0.0,
        )
        result.compute_summary()
    else:
        result = scanner.scan_directory(str(path))
    
    # Filter by severity
    severity_order = ["critical", "high", "medium", "low", "info"]
    min_index = severity_order.index(min_severity.value)
    valid_severities = set(severity_order[:min_index + 1])
    
    filtered_findings = [
        f for f in result.findings
        if f.severity.value in valid_severities
    ]
    
    if output == OutputFormat.json:
        _output_json(result, filtered_findings)
    elif output == OutputFormat.sarif:
        _output_sarif(result, filtered_findings)
    else:
        _output_text(result, filtered_findings, verbose)
    
    # Exit with code 1 if critical or high findings
    has_critical_high = any(
        f.severity.value in ("critical", "high")
        for f in filtered_findings
    )
    
    if has_critical_high:
        raise typer.Exit(1)


def _output_text(result, findings: list, verbose: bool) -> None:
    """Output findings in text format with rich formatting."""
    console.print(f"\n[dim]Files scanned: {result.files_scanned}[/dim]")
    console.print(f"[dim]Scan duration: {result.scan_duration:.2f}s[/dim]\n")
    
    if not findings:
        console.print("[green]No security issues found![/green]")
        return
    
    # Group findings by file
    by_file: dict[str, list] = {}
    for finding in findings:
        if finding.file_path not in by_file:
            by_file[finding.file_path] = []
        by_file[finding.file_path].append(finding)
    
    for file_path, file_findings in by_file.items():
        console.print(f"\n[bold]{file_path}[/bold]")
        
        for finding in file_findings:
            color = SEVERITY_COLORS.get(finding.severity.value, "white")
            line_info = f" (line {finding.line_number})" if finding.line_number else ""
            
            console.print(f"  [{color}][{finding.severity.value.upper()}][/{color}] {finding.rule_id}: {finding.title}{line_info}")
            
            if verbose:
                console.print(f"    [dim]{finding.description}[/dim]")
                console.print(f"    [cyan]Recommendation: {finding.recommendation}[/cyan]")
    
    # Summary table
    console.print("\n")
    table = Table(title="Summary", show_header=True)
    table.add_column("Severity", style="bold")
    table.add_column("Count", justify="right")
    
    for sev in ["critical", "high", "medium", "low", "info"]:
        count = result.summary.get(sev, 0)
        if count > 0:
            color = SEVERITY_COLORS.get(sev, "white")
            table.add_row(f"[{color}]{sev.upper()}[/{color}]", str(count))
    
    console.print(table)
    console.print(f"\n[bold]Total findings: {len(findings)}[/bold]")


def _output_json(result, findings: list) -> None:
    """Output findings in JSON format."""
    output = {
        "files_scanned": result.files_scanned,
        "scan_duration": result.scan_duration,
        "summary": result.summary,
        "findings": [
            {
                "rule_id": f.rule_id,
                "severity": f.severity.value,
                "title": f.title,
                "description": f.description,
                "file_path": f.file_path,
                "line_number": f.line_number,
                "recommendation": f.recommendation,
            }
            for f in findings
        ],
    }
    console.print_json(json.dumps(output, indent=2))


def _output_sarif(result, findings: list) -> None:
    """Output findings in SARIF format."""
    rules = {}
    results = []
    
    for finding in findings:
        if finding.rule_id not in rules:
            rules[finding.rule_id] = {
                "id": finding.rule_id,
                "name": finding.title,
                "shortDescription": {"text": finding.title},
                "fullDescription": {"text": finding.description},
                "help": {"text": finding.recommendation},
                "defaultConfiguration": {
                    "level": _severity_to_sarif_level(finding.severity.value)
                },
            }
        
        result_entry = {
            "ruleId": finding.rule_id,
            "level": _severity_to_sarif_level(finding.severity.value),
            "message": {"text": finding.description},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": finding.file_path},
                    }
                }
            ],
        }
        
        if finding.line_number:
            result_entry["locations"][0]["physicalLocation"]["region"] = {
                "startLine": finding.line_number
            }
        
        results.append(result_entry)
    
    sarif = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Tork MCP Scanner",
                        "version": "0.1.0",
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
            }
        ],
    }
    
    console.print_json(json.dumps(sarif, indent=2))


def _severity_to_sarif_level(severity: str) -> str:
    """Convert severity to SARIF level."""
    mapping = {
        "critical": "error",
        "high": "error",
        "medium": "warning",
        "low": "note",
        "info": "note",
    }
    return mapping.get(severity, "warning")


@app.command()
def policy(
    policy_path: Path = typer.Option(
        ...,
        "--policy",
        "-p",
        help="Path to policy file or directory",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """Validate governance policies."""
    console.print("[bold blue]Tork Policy Validator[/bold blue]")
    console.print(f"Validating policies at: {policy_path}")
    
    if not policy_path.exists():
        console.print(f"[red]Error: Path does not exist: {policy_path}[/red]")
        raise typer.Exit(1)
    
    from tork.compliance import PolicyValidator
    
    validator = PolicyValidator()
    count = validator.load_policies(policy_path)
    
    console.print(f"[green]Loaded {count} policies[/green]")
    
    if verbose:
        table = Table(title="Policy Summary")
        table.add_column("Policy", style="cyan")
        table.add_column("Status", style="green")
        table.add_row("Governance policies", f"{count} loaded")
        console.print(table)


@app.command()
def version() -> None:
    """Display version information."""
    from tork import __version__
    console.print(f"Tork Governance SDK v{__version__}")


@app.command()
def init(
    output: Path = typer.Option(
        Path("./policies"),
        "--output",
        "-o",
        help="Output directory for policy templates",
    ),
) -> None:
    """Initialize a new policy directory with templates."""
    output.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]Created policy directory: {output}[/green]")
    console.print("Add your YAML policy files to this directory.")


if __name__ == "__main__":
    app()
