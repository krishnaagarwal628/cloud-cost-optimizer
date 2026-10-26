import typer
from rich import print
from src.auth import get_aws_session, verify_aws_credentials
from src.utils import get_available_aws_regions
from src.scanners.ec2_scanner import EC2Scanner
from rich import print
from rich.table import Table
from src.scanners.s3_scanner import S3Scanner

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
def scan(
    profile: str = typer.Option(None, "--profile", "-p", help="AWS profile name"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="AWS region")
):
    """Scan EC2 instances, EBS volumes, Elastic IPs, and S3 buckets for cost optimization."""
    print(f"[bold yellow]Starting Resource Audit (EC2 & S3) in region: {region}...[/bold yellow]")
    
    session = get_aws_session(profile_name=profile, region_name=region)
    
    # Run EC2 Scans
    ec2_scanner = EC2Scanner(session=session, region_name=region)
    ec2_results = ec2_scanner.run_all_scans()
    
    # Run S3 Scans
    s3_scanner = S3Scanner(session=session)
    s3_results = s3_scanner.run_all_scans()
    
    # Combine Findings
    all_findings = (
        ec2_results["stopped_instances"] + 
        ec2_results["unattached_ebs"] + 
        ec2_results["unused_eips"] +
        s3_results["empty_buckets"] +
        s3_results["missing_lifecycle"]
    )
    
    table = Table(title=f"Cloud Resource Audit Findings ({region})", show_header=True, header_style="bold magenta")
    table.add_column("Type", style="cyan", width=18)
    table.add_column("Resource ID / IP", style="bold white", width=25)
    table.add_column("State", style="red", width=20)
    table.add_column("Recommendation", style="yellow")

    if all_findings:
        for item in all_findings:
            res_id = item.get("resource_id") or item.get("public_ip", "N/A")
            table.add_row(
                item.get("resource_type", "Unknown"),
                res_id,
                item.get("state", "N/A"),
                item.get("recommendation", "N/A")
            )
        print(table)
    else:
        print(table)
        print("\n[bold green]✓ No idle or underutilized cloud resources detected![/bold green]")

@app.command()
def regions(
    profile: str = typer.Option(None, "--profile", "-p", help="AWS profile name")
):
    """List all available AWS regions for the configured account."""
    print("[yellow]Fetching available AWS regions...[/yellow]")
    session = get_aws_session(profile_name=profile)
    region_list = get_available_aws_regions(session)
    print(f"[bold green]✓ Active AWS Regions ({len(region_list)}):[/bold green]")
    print(region_list)
    
if __name__ == "__main__":
    app()