import typer
from rich import print
from src.auth import get_aws_session, verify_aws_credentials

app = typer.Typer(
    help="Cloud Infrastructure Auditor & Cost Optimizer CLI",
    add_completion=False
)

@app.command()
def version():
    """Display the current CLI version."""
    print("[bold cyan]Cloud Cost Optimizer CLI v0.1.0[/bold cyan]")

@app.command()
def auth_check(
    profile: str = typer.Option(None, "--profile", "-p", help="AWS profile name"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="AWS region")
):
    """Verify AWS credentials and display current account information."""
    print(f"[yellow]Verifying AWS authentication (Region: {region})...[/yellow]")
    
    session = get_aws_session(profile_name=profile, region_name=region)
    auth_result = verify_aws_credentials(session)
    
    if auth_result["status"]:
        print("[bold green]✓ AWS Authentication Successful![/bold green]")
        print(f"[bold white]Account ID:[/bold white] {auth_result['account_id']}")
        print(f"[bold white]Identity ARN:[/bold white] {auth_result['arn']}")
    else:
        print("[bold red]✗ AWS Authentication Failed![/bold red]")
        print(f"[red]Error:[/red] {auth_result['error']}")

@app.command()
def scan():
    """Scan cloud resources (Placeholder for Week 2)."""
    print("[yellow]Scan command triggered. Scanner logic will be added in Week 2.[/yellow]")

if __name__ == "__main__":
    app()