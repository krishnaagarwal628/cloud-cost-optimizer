import typer
from rich import print

# Typer app initialize kar rahe hain
app = typer.Typer(
    help="Cloud Infrastructure Auditor & Cost Optimizer CLI",
    add_completion=False
)

@app.command()
def version():
    """Display the current CLI version."""
    print("[bold cyan]Cloud Cost Optimizer CLI v0.1.0[/bold cyan]")

@app.command()
def scan():
    """Scan cloud resources (Placeholder for Week 2)."""
    print("[yellow]Scan command triggered. Scanner logic will be added in Week 2.[/yellow]")

if __name__ == "__main__":
    app()
    