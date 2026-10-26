import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from src.utils import retry_on_throttling


class RDSScanner:
    def __init__(self, session: boto3.Session, region_name: str = "us-east-1"):
        self.session = session
        self.region_name = region_name
        self.client = session.client("rds", region_name=region_name)

    @retry_on_throttling(max_retries=3)
    def scan_stopped_db_instances(self) -> list:
        """Finds RDS DB instances that are in 'stopped' state."""
        findings = []
        try:
            response = self.client.describe_db_instances()
            for instance in response.get("DBInstances", []):
                status = instance.get("DBInstanceStatus")
                if status in ["stopped", "stopping"]:
                    findings.append({
                        "resource_id": instance.get("DBInstanceIdentifier"),
                        "resource_type": "RDS Instance",
                        "state": status,
                        "region": self.region_name,
                        "recommendation": "Consider deleting or taking a final snapshot if stopped instance is no longer needed."
                    })
        except (ClientError, NoCredentialsError, PartialCredentialsError):
            print(f"[red]Error scanning RDS instances in {self.region_name}: Unable to locate AWS credentials.[/red]")
        return findings

    @retry_on_throttling(max_retries=3)
    def scan_manual_snapshots(self) -> list:
        """Finds manual RDS snapshots that might be orphaned or old."""
        findings = []
        try:
            response = self.client.describe_db_snapshots(SnapshotType="manual")
            for snapshot in response.get("DBSnapshots", []):
                findings.append({
                    "resource_id": snapshot.get("DBSnapshotIdentifier"),
                    "resource_type": "RDS Snapshot",
                    "state": "manual-snapshot",
                    "region": self.region_name,
                    "recommendation": "Review manual DB snapshot for retention or export to S3 to lower storage costs."
                })
        except (ClientError, NoCredentialsError, PartialCredentialsError):
            print(f"[red]Error scanning RDS snapshots in {self.region_name}: Unable to locate AWS credentials.[/red]")
        return findings

    def run_all_scans(self) -> dict:
        """Executes all RDS cost audits."""
        return {
            "stopped_instances": self.scan_stopped_db_instances(),
            "manual_snapshots": self.scan_manual_snapshots()
        }