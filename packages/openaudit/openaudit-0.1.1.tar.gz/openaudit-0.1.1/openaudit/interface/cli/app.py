import typer
from .commands import scan_command, explain_command, config_app

app = typer.Typer(
    name="OpenAuditKit",
    help="CLI tool for security auditing",
    add_completion=False
)

@app.callback()
def main_callback():
    """
    OpenAuditKit CLI
    """
    pass

app.command(name="scan")(scan_command)
app.command(name="explain")(explain_command)
app.add_typer(config_app, name="config")

