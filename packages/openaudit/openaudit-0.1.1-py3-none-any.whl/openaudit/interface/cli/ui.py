from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.live import Live
from rich.panel import Panel
from rich.markdown import Markdown
from typing import Generator, Optional
import time

class UI:
    """
    Centralized UI handler using Rich.
    """
    console = Console()

    @staticmethod
    def print(text: str, style: str = None):
        UI.console.print(text, style=style)

    @staticmethod
    def header(title: str):
        UI.console.rule(f"[bold blue]{title}[/bold blue]")

    @staticmethod
    def success(message: str):
        UI.console.print(f"[bold green]✓[/bold green] {message}")

    @staticmethod
    def error(message: str):
        UI.console.print(f"[bold red]✗[/bold red] {message}")

    @staticmethod
    def warning(message: str):
        UI.console.print(f"[bold yellow]![/bold yellow] {message}")

    @staticmethod
    def create_progress():
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=UI.console
        )

    @staticmethod
    def stream_markdown(content_generator: Generator[str, None, None], title: str = "Analysis"):
        """
        Streams markdown content nicely.
        """
        with Live(console=UI.console, refresh_per_second=10) as live:
            accumulated_text = ""
            for chunk in content_generator:
                accumulated_text += chunk
                markdown = Markdown(accumulated_text)
                panel = Panel(markdown, title=title, border_style="blue")
                live.update(panel)
            
            # Final render
            markdown = Markdown(accumulated_text)
            panel = Panel(markdown, title=title, border_style="green")
            live.update(panel)
        return accumulated_text
