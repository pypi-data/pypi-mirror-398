import typer
import os
from pathlib import Path
from openaudit.core.domain import ScanContext, Severity, Confidence
from openaudit.core.rules_engine import RulesEngine
from openaudit.core.ignore_manager import IgnoreManager
import time
from openaudit.features.secrets.scanner import SecretScanner
from openaudit.features.config.scanner import ConfigScanner
from openaudit.reporters.console import ConsoleReporter
from openaudit.reporters.json_reporter import JSONReporter
from typing import Optional
from enum import Enum
from openaudit.ai.ethics import ConsentManager
from openaudit.features.architecture.scanner import ArchitectureScanner
from openaudit.features.architecture.agent import ArchitectureAgent
from openaudit.ai.models import PromptContext
from openaudit.features.secrets.context import SecretContextExtractor
from openaudit.features.secrets.agent import SecretConfidenceAgent
from openaudit.features.secrets.agent import SecretConfidenceAgent
from openaudit.ai.ethics import Redactor
from openaudit.core.domain import Finding
from openaudit.features.dataflow.scanner import DataFlowScanner
from openaudit.features.dataflow.agent import CrossFileAgent
from openaudit.features.threat_model.agent import ThreatModelingAgent
from openaudit.features.explain.agent import ExplainAgent


class OutputFormat(str, Enum):
    RICH = "rich"
    JSON = "json"

def scan_command(
    target: str = typer.Argument(".", help="Target directory to scan"),
    rules_path: Optional[str] = typer.Option(None, help="Path to rules file or directory"),
    format: OutputFormat = typer.Option(OutputFormat.RICH, case_sensitive=False, help="Output format"),
    output: Optional[str] = typer.Option(None, help="Output file path (for JSON)"),
    ci: bool = typer.Option(False, help="Run in CI mode (no progress bar, exit code 1 on failure)"),
    fail_on: Severity = typer.Option(Severity.HIGH, help="Severity threshold to fail the scan"),
    ai: bool = typer.Option(False, help="Enable AI-powered advisory agents (requires consent)")
):
    """
    Scan the target directory for security issues.
    """
    # 1. Setup Context
    target_path = Path(target).absolute()
    if not target_path.exists():
        typer.echo(f"Error: Target path {target} does not exist.")
        raise typer.Exit(code=1)

    # 1.1 Check AI Consent
    if ai:
        if not ConsentManager.has_consented():
            if ci:
                typer.echo("Error: CI mode requires explicit AI consent. Run 'openaudit consent --grant' locally first or set environment variable.")
                raise typer.Exit(code=1)
            
            # Interactive prompt
            confirm = typer.confirm("AI features require sending anonymized code snippets to an LLM. Do you consent?", default=False)
            if confirm:
                ConsentManager.grant_consent()
                typer.echo("Consent granted.")
            else:
                typer.echo("Consent denied. Disabling AI features.")
                ai = False

    # 1. Setup Context & Ignore Manager
    ignore_manager = IgnoreManager(root_path=target_path)
    context = ScanContext(target_path=str(target_path), ignore_manager=ignore_manager)
    
    # 2. Load Rules
    if rules_path is None:
        # Default to bundled rules
        import openaudit
        package_dir = Path(openaudit.__file__).parent
        rules_path = str(package_dir / "rules")
        if not Path(rules_path).exists():
            # Fallback for dev environment if not installed as package
            rules_path = "rules"

    engine = RulesEngine(rules_path)
    rules = engine.load_rules()
    
    if not rules:
        typer.echo("Warning: No rules loaded.")

    # 3. Initialize Scanners
    scanners = [
        SecretScanner(rules=rules),
        ConfigScanner(rules=rules)
    ]

    # 4. Run Scan
    all_findings = []
    
    start_time = time.time()
    if ci:
        # No progress bar in CI mode
        for scanner in scanners:
            all_findings.extend(scanner.scan(context))
    else:
        from openaudit.interface.cli.ui import UI
        with UI.create_progress() as progress:
            scan_task = progress.add_task("[green]Scanning...", total=len(scanners))
            for scanner in scanners:
                all_findings.extend(scanner.scan(context))
                progress.update(scan_task, advance=1)
                
    # 4.1 Run AI Agents if enabled
    if ai:
        from openaudit.interface.cli.ui import UI
        
        UI.header("AI Analysis")
        
        # Architecture Agent
        with UI.console.status("[bold blue]Analyzing Architecture...[/bold blue]"):
            arch_scanner = ArchitectureScanner()
            structure = arch_scanner.scan(context)
            
            arch_agent = ArchitectureAgent()
            result = arch_agent.run_on_structure(structure)
            
            if result and result.is_advisory:
                ai_finding = Finding(
                    rule_id=f"AI-{arch_agent.name.upper()}",
                    description=f"{result.analysis} Suggested: {result.suggestion}",
                    file_path="PROJECT_ROOT",
                    line_number=0,
                    secret_hash="",
                    severity=result.severity,
                    confidence=result.confidence,
                    category="architecture",
                    remediation=result.suggestion or "Review architecture.",
                    is_ai_generated=True
                )
                all_findings.append(ai_finding)

        # Cross-File Agent
        with UI.console.status("[bold purple]Analyzing Data Flow...[/bold purple]"):
            df_scanner = DataFlowScanner()
            df_graph = df_scanner.scan(context, structure)
            
            cross_agent = CrossFileAgent()
            df_results = cross_agent.run_on_graph(df_graph)
            
            for res in df_results:
                 if res.is_advisory:
                    df_finding = Finding(
                        rule_id=f"AI-{cross_agent.name.upper()}",
                        description=f"{res.analysis} Suggested: {res.suggestion}",
                        file_path="PROJECT_ROOT",
                        line_number=0,
                        secret_hash="",
                        severity=res.severity,
                        confidence=res.confidence,
                        category="architecture",
                        remediation=res.suggestion or "Secure data flow.",
                        is_ai_generated=True
                    )
                    all_findings.append(df_finding)
        
        # Threat Modeling Agent
        with UI.console.status("[bold red]Modeling Threats...[/bold red]"):
            threat_agent = ThreatModelingAgent()
            tm_results = threat_agent.run_on_structure(structure)
            for res in tm_results:
                 if res.is_advisory:
                    tm_finding = Finding(
                        rule_id=f"AI-THREAT-{res.analysis.split(':')[0]}", # Crude ID generation
                        description=f"{res.analysis} {res.suggestion}",
                        file_path="PROJECT_ROOT",
                        line_number=0,
                        secret_hash="",
                        severity=res.severity,
                        confidence=res.confidence,
                        category="architecture",
                        remediation=res.suggestion or "Mitigate threat.",
                        is_ai_generated=True
                    )
                    all_findings.append(tm_finding)

        # Secret Confidence Agent
        secret_findings = [f for f in all_findings if f.category == "secret"]
        if secret_findings:
            with UI.create_progress() as progress:
                secret_task = progress.add_task("[cyan]Verifying Secrets with AI...", total=len(secret_findings))
                secret_agent = SecretConfidenceAgent()
                
                for finding in secret_findings:
                    # Extract context
                    code_context = SecretContextExtractor.get_context(finding.file_path, finding.line_number)
                    if not code_context:
                        progress.update(secret_task, advance=1)
                        continue
                    
                    # Redact
                    redacted_context = Redactor.redact(code_context)
                    
                    # Analyze
                    ctx = PromptContext(
                        file_path=finding.file_path,
                        code_snippet=redacted_context,
                        line_number=finding.line_number
                    )
                    
                    ai_result = secret_agent.run(ctx)
                    
                    if ai_result:
                        # Enrich Finding
                        finding.description += f" [AI: {ai_result.analysis}]"
                        finding.is_ai_generated = True # Tag enriched findings too
                        
                        # If agent is very confident it's a false positive (test), downgrade
                        if ai_result.confidence == Confidence.LOW and ai_result.severity == Severity.LOW:
                            finding.confidence = Confidence.LOW
                            finding.severity = Severity.LOW
                            finding.description = f"[ADVISORY] {finding.description}"
                    
                    progress.update(secret_task, advance=1)

    duration = time.time() - start_time

    # 5. Report
    if format == OutputFormat.JSON:
        reporter = JSONReporter(output_path=output)
    else:
         # Note: ConsoleReporter currently prints to stdout only
        reporter = ConsoleReporter()
        
    reporter.report(all_findings)
    if not format == OutputFormat.JSON:
        typer.echo(f"Scan Duration: {duration:.2f}s")

    # 6. Exit Logic
    if ci or fail_on:
        max_severity = Severity.LOW
        failed = False
        for f in all_findings:
            if f.severity >= fail_on:
                failed = True
                break
        
        if failed:
            if not format == OutputFormat.JSON:
                 typer.echo(f"Failure: Found issues with severity >= {fail_on.value}")
            raise typer.Exit(code=1)

def explain_command(
    path: str = typer.Argument(..., help="Path to the file to explain"),
    ai: bool = typer.Option(True, help="Enable AI features (implied true for this command)")
):
    """
    Explain the code in a specific file using AI.
    """
    from openaudit.interface.cli.ui import UI
    
    target_path = Path(path).absolute()
    if not target_path.exists() or not target_path.is_file():
         UI.error(f"Error: path {path} does not exist or is not a file.")
         raise typer.Exit(code=1)
         
    # Check Consent
    if not ConsentManager.has_consented():
        confirm = typer.confirm("This feature sends code to an AI. Do you consent?", default=False)
        if confirm:
            ConsentManager.grant_consent()
        else:
            UI.warning("Consent refused. Exiting.")
            raise typer.Exit(code=1)
            
    # Read Content
    content = target_path.read_text(encoding="utf-8", errors="ignore")
    
    # Redact
    redacted_content = Redactor.redact(content)
    
    # Run Agent
    agent = ExplainAgent()
    context = PromptContext(code_snippet=redacted_content, file_path=str(target_path))
    
    # Stream Output
    UI.stream_markdown(agent.stream(context), title=f"Analysis for {target_path.name}")


# Config Commands
config_app = typer.Typer(help="Manage OpenAuditKit configuration.")

@config_app.command("set-key")
def set_key(key: str = typer.Argument(..., help="OpenAI API Key")):
    """
    Set the OpenAI API key in the configuration file.
    """
    from openaudit.core.config import ConfigManager
    manager = ConfigManager()
    manager.set_api_key(key)
    typer.echo(f"API key saved to {manager.config_path}")

@config_app.command("show")
def show_config():
    """
    Show current configuration path and status.
    """
    from openaudit.core.config import ConfigManager
    manager = ConfigManager()
    key = manager.get_api_key()
    status = "Set" if key else "Not Set"
    typer.echo(f"Config File: {manager.config_path}")
    typer.echo(f"API Key Status: {status}")
        