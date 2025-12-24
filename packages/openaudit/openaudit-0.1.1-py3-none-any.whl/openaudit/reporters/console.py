from typing import List
from rich.console import Console
from rich.table import Table
from openaudit.core.domain import Finding
from .base import Reporter

class ConsoleReporter(Reporter):
    def report(self, findings: List[Finding]):
        console = Console()
        
        if not findings:
            console.print("[green]No issues found![/green]")
            return

        table = Table(title=f"Scan Results - {len(findings)} Issues Found")
        table.add_column("Severity", style="bold")
        table.add_column("Confidence")
        table.add_column("Category")
        table.add_column("Rule ID")
        table.add_column("Location")
        table.add_column("Secret (Masked)")

        for f in findings:
            color = "red" if f.severity == "critical" else "yellow" if f.severity == "high" else "blue"
            conf_color = "green" if f.confidence == "high" else "yellow" if f.confidence == "medium" else "dim"
            location = f"{f.file_path}:{f.line_number}"
            table.add_row(
                f"[{color}]{f.severity.value.upper()}[/{color}]",
                f"[{conf_color}]{f.confidence.value.upper()}[/{conf_color}]",
                f.category.upper(),
                f.rule_id,
                location,
                f.secret_hash
            )

        console.print(table)
        console.print("\nLegend: [red]CRITICAL/HIGH[/red] - Immediate action required | [blue]LOW/MEDIUM[/blue] - Warning/Info")
