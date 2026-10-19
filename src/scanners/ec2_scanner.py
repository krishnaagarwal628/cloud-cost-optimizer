import boto3
from botocore.exceptions import ClientError
from src.utils import retry_on_throttling
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError


class EC2Scanner:
    def __init__(self, session: boto3.Session, region_name: str = "us-east-1"):
        self.session = session
        self.region_name = region_name
        self.client = session.client("ec2", region_name=region_name)

    @retry_on_throttling(max_retries=3)
    def scan_stopped_instances(self) -> list:
        """Finds all EC2 instances in 'stopped' state."""
        findings = []
        try:
            response = self.client.describe_instances(
                Filters=[{"Name": "instance-state-name", "Values": ["stopped"]}]
            )
            for reservation in response.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    findings.append({
                        "resource_id": instance.get("InstanceId"),
                        "resource_type": "EC2 Instance",
                        "state": "stopped",
                        "instance_type": instance.get("InstanceType"),
                        "region": self.region_name,
                        "recommendation": "Consider terminating or downsizing stopped instance if not needed."
                    })
        except (ClientError, NoCredentialsError, PartialCredentialsError) as e:
            print(f"[red]Error scanning stopped EC2 instances in {self.region_name}: Unable to locate AWS credentials.[/red]")
        return findings

    @retry_on_throttling(max_retries=3)
    def scan_unattached_ebs(self) -> list:
        """Finds all EBS volumes with 'available' status (unattached)."""
        findings = []
        try:
            response = self.client.describe_volumes(
                Filters=[{"Name": "status", "Values": ["available"]}]
            )
            for volume in response.get("Volumes", []):
                findings.append({
                    "resource_id": volume.get("VolumeId"),
                    "resource_type": "EBS Volume",
                    "state": "unattached",
                    "size_gb": volume.get("Size"),
                    "volume_type": volume.get("VolumeType"),
                    "region": self.region_name,
                    "recommendation": "Delete unattached EBS volume or create snapshot before removal."
                })
        except (ClientError, NoCredentialsError, PartialCredentialsError) as e:
            print(f"[red]Error scanning EBS volumes in {self.region_name}: Unable to locate AWS credentials.[/red]")
        return findings

    @retry_on_throttling(max_retries=3)
    def scan_unused_eips(self) -> list:
        """Finds Elastic IPs not associated with any instance."""
        findings = []
        try:
            response = self.client.describe_addresses()
            for address in response.get("Addresses", []):
                if "InstanceId" not in address and "NetworkInterfaceId" not in address:
                    findings.append({
                        "resource_id": address.get("AllocationId", address.get("PublicIp")),
                        "public_ip": address.get("PublicIp"),
                        "resource_type": "Elastic IP",
                        "state": "unassociated",
                        "region": self.region_name,
                        "recommendation": "Release unassociated Elastic IP to avoid hourly charge."
                    })
        except (ClientError, NoCredentialsError, PartialCredentialsError) as e:
            print(f"[red]Error scanning Elastic IPs in {self.region_name}: Unable to locate AWS credentials.[/red]")
        return findings
        

    def run_all_scans(self) -> dict:
        """Executes all EC2/EBS/EIP cost audits."""
        return {
            "stopped_instances": self.scan_stopped_instances(),
            "unattached_ebs": self.scan_unattached_ebs(),
            "unused_eips": self.scan_unused_eips()
        }