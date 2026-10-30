import typer
from rich import print
from rich.table import Table

from src.auth import get_aws_session, verify_aws_credentials
from src.utils import get_available_aws_regions
from src.scanners.ec2_scanner import EC2Scanner
from src.scanners.s3_scanner import S3Scanner
from src.scanners.rds_scanner import RDSScanner
from src.cost_estimator import CostEstimator
from src.exporter import ReportExporter
from src.scanners.multi_region import MultiRegionScanner
from src.remediation import RemediationEngine


app = typer.Typer(
    name="cloud-cost-optimizer",
    help="AWS Cloud Cost Optimization CLI Tool",
    add_completion=False
)


@app.command()
def version():
    """Show tool version."""
    print("[bold cyan]Cloud Cost Optimizer v0.1.0[/bold cyan]")


@app.command()
def auth_check(
    profile: str = typer.Option(None, "--profile", "-p", help="AWS profile name")
):
    """Verify AWS authentication credentials."""
    print("[yellow]Verifying AWS Credentials...[/yellow]")
    session = get_aws_session(profile_name=profile)
    result = verify_aws_credentials(session)

    if result.get("status") == "success":
        print(f"[bold green]✓ AWS Authentication Successful![/bold green]")
        print(f"Account ID: [cyan]{result.get('account')}[/cyan]")
        print(f"User / ARN: [cyan]{result.get('arn')}[/cyan]")
    else:
        print(f"[bold red]✗ Authentication Failed:[/bold red] {result.get('message')}")


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


@app.command()
def scan(
    profile: str = typer.Option(None, "--profile", "-p", help="AWS profile name"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="AWS region"),
    all_regions: bool = typer.Option(False, "--all-regions", "-a", help="Scan all active AWS regions in parallel"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path (.json or .csv)")
):
    """Scan AWS resources (EC2, CloudWatch, S3, RDS), estimate waste, and export reports."""
    session = get_aws_session(profile_name=profile, region_name=region)
    
    if all_regions:
        raw_findings = MultiRegionScanner(session=session).scan_all_regions()
    else:
        print(f"[bold yellow]Starting Complete Resource Audit in region: {region}...[/bold yellow]")
        ec2_results = EC2Scanner(session=session, region_name=region).run_all_scans()
        s3_results = S3Scanner(session=session).run_all_scans()
        rds_results = RDSScanner(session=session, region_name=region).run_all_scans()
        
        raw_findings = (
            ec2_results["stopped_instances"] + 
            ec2_results["low_cpu_instances"] +
            ec2_results["unattached_ebs"] + 
            ec2_results["unused_eips"] +
            s3_results["empty_buckets"] +
            s3_results["missing_lifecycle"] +
            rds_results["stopped_instances"] +
            rds_results["manual_snapshots"]
        )
    
    # Calculate Cost Estimates & Enrich Findings
    all_findings, total_savings = CostEstimator.calculate_total_savings(raw_findings)
    
    # Build Table Display
    title = "Multi-Region Audit Findings" if all_regions else f"Cloud Resource Audit Findings ({region})"
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Type", style="cyan", width=16)
    table.add_column("Resource ID / IP", style="bold white", width=22)
    table.add_column("State", style="red", width=18)
    table.add_column("Est. Waste", style="bold green", width=12)
    table.add_column("Recommendation", style="yellow")

    if all_findings:
        for item in all_findings:
            res_id = item.get("resource_id") or item.get("public_ip", "N/A")
            table.add_row(
                item.get("resource_type", "Unknown"),
                res_id,
                item.get("state", "N/A"),
                item.get("estimated_monthly_waste", "$0.00"),
                item.get("recommendation", "N/A")
            )
        print(table)
        print(f"\n[bold green]💰 Total Estimated Monthly Savings: ${total_savings:.2f}/month[/bold green]")
    else:
        print(table)
        print("\n[bold green]✓ No idle or underutilized cloud resources detected![/bold green]")

    # Export Report if --output (-o) flag is passed
    if output:
        if output.endswith(".json"):
            ReportExporter.export_to_json(all_findings, output)
        elif output.endswith(".csv"):
            ReportExporter.export_to_csv(all_findings, output)
        else:
            print("[bold red]✗ Unsupported file format. Please use .json or .csv extension.[/bold red]")


@app.command()
def clean(
    profile: str = typer.Option(None, "--profile", "-p", help="AWS profile name"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="AWS region"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run", help="Run in dry-run mode without modifying resources"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip interactive confirmation prompts")
):
    """Clean up detected idle and underutilized AWS resources safely."""
    mode_str = "[bold cyan]DRY-RUN MODE[/bold cyan]" if dry_run else "[bold red]LIVE REMEDIATION MODE[/bold red]"
    print(f"Starting Resource Remediation in {region} ({mode_str})...")

    session = get_aws_session(profile_name=profile, region_name=region)
    remediator = RemediationEngine(session=session, region_name=region, dry_run=dry_run)

    # Fetch current findings
    ec2_scanner = EC2Scanner(session=session, region_name=region)
    ec2_results = ec2_scanner.run_all_scans()

    stopped_instances = ec2_results["stopped_instances"]
    unattached_ebs = ec2_results["unattached_ebs"]
    unused_eips = ec2_results["unused_eips"]

    total_targets = len(stopped_instances) + len(unattached_ebs) + len(unused_eips)
    if total_targets == 0:
        print("[bold green]✓ No cleanup actions needed. All resources active/in-use.[/bold green]")
        return

    # User confirmation check for live execution
    if not dry_run and not confirm:
        sure = typer.confirm(f"Are you sure you want to modify/delete {total_targets} resources in {region}?")
        if not sure:
            print("[yellow]Remediation cancelled by user.[/yellow]")
            return

    # Execute Remediation Steps
    for inst in stopped_instances:
        remediator.stop_ec2_instance(inst["resource_id"])

    for ebs in unattached_ebs:
        remediator.delete_unattached_ebs(ebs["resource_id"])

    for eip in unused_eips:
        remediator.release_unused_eip(eip["resource_id"])
if __name__ == "__main__":
    app()