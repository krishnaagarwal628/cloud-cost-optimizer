from datetime import datetime, timedelta, timezone
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from src.utils import retry_on_throttling


class EC2Scanner:
    def __init__(self, session: boto3.Session, region_name: str = "us-east-1"):
        self.session = session
        self.region_name = region_name
        self.ec2_client = session.client("ec2", region_name=region_name)
        self.cloudwatch_client = session.client("cloudwatch", region_name=region_name)

    @retry_on_throttling(max_retries=3)
    def scan_stopped_instances(self) -> list:
        """Finds all EC2 instances in 'stopped' state."""
        findings = []
        try:
            response = self.ec2_client.describe_instances(
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
        except (ClientError, NoCredentialsError, PartialCredentialsError):
            print(f"[red]Error scanning stopped EC2 instances in {self.region_name}: Unable to locate AWS credentials.[/red]")
        return findings

    @retry_on_throttling(max_retries=3)
    def scan_low_cpu_instances(self, days: int = 14, threshold_percent: float = 5.0) -> list:
        """Scans running EC2 instances with sub-5% CPU utilization over the past 14 days via CloudWatch."""
        findings = []
        try:
            response = self.ec2_client.describe_instances(
                Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
            )
            
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=days)
            
            for reservation in response.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instance_id = instance.get("InstanceId")
                    instance_type = instance.get("InstanceType")
                    
                    metrics = self.cloudwatch_client.get_metric_statistics(
                        Namespace="AWS/EC2",
                        MetricName="CPUUtilization",
                        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,
                        Statistics=["Average"]
                    )
                    
                    datapoints = metrics.get("Datapoints", [])
                    if datapoints:
                        avg_cpu = sum(dp.get("Average", 0) for dp in datapoints) / len(datapoints)
                        
                        if avg_cpu < threshold_percent:
                            findings.append({
                                "resource_id": instance_id,
                                "resource_type": "EC2 Instance",
                                "state": f"idle (avg CPU: {avg_cpu:.1f}%)",
                                "instance_type": instance_type,
                                "region": self.region_name,
                                "recommendation": f"Instance has <{threshold_percent}% CPU utilization over {days} days. Consider downsizing or stopping."
                            })
        except (ClientError, NoCredentialsError, PartialCredentialsError):
            print(f"[red]Error fetching CloudWatch EC2 metrics in {self.region_name}: Unable to locate AWS credentials.[/red]")
        return findings

    @retry_on_throttling(max_retries=3)
    def scan_unattached_ebs(self) -> list:
        """Finds all EBS volumes with 'available' status (unattached)."""
        findings = []
        try:
            response = self.ec2_client.describe_volumes(
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
        except (ClientError, NoCredentialsError, PartialCredentialsError):
            print(f"[red]Error scanning EBS volumes in {self.region_name}: Unable to locate AWS credentials.[/red]")
        return findings

    @retry_on_throttling(max_retries=3)
    def scan_unused_eips(self) -> list:
        """Finds Elastic IPs not associated with any instance."""
        findings = []
        try:
            response = self.ec2_client.describe_addresses()
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
        except (ClientError, NoCredentialsError, PartialCredentialsError):
            print(f"[red]Error scanning Elastic IPs in {self.region_name}: Unable to locate AWS credentials.[/red]")
        return findings

    def run_all_scans(self) -> dict:
        """Executes all EC2/EBS/EIP cost audits including CloudWatch metrics."""
        return {
            "stopped_instances": self.scan_stopped_instances(),
            "low_cpu_instances": self.scan_low_cpu_instances(),
            "unattached_ebs": self.scan_unattached_ebs(),
            "unused_eips": self.scan_unused_eips()
        }