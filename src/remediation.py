import boto3
from botocore.exceptions import ClientError
from rich import print


class RemediationEngine:
    def __init__(self, session: boto3.Session, region_name: str = "us-east-1", dry_run: bool = True):
        self.session = session
        self.region_name = region_name
        self.dry_run = dry_run
        self.ec2_client = session.client("ec2", region_name=region_name)

    def is_resource_protected(self, tags: list) -> bool:
        """Checks if resource contains protection tags (e.g., Protection=true, DoNotDelete=true)."""
        if not tags:
            return False
        
        protected_keys = ["protection", "donotdelete", "do_not_delete", "keepalive"]
        for tag in tags:
            key = str(tag.get("Key", "")).strip().lower()
            val = str(tag.get("Value", "")).strip().lower()
            if key in protected_keys and val in ["true", "yes", "1"]:
                return True
        return False

    def stop_ec2_instance(self, instance_id: str) -> bool:
        """Stops an active EC2 instance with protection check and dry-run mode."""
        try:
            # Tag verification
            instance_info = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            tags = instance_info["Reservations"][0]["Instances"][0].get("Tags", [])
            
            if self.is_resource_protected(tags):
                print(f"[bold yellow]🔒 Skipped protected instance:[bold yellow] {instance_id}")
                return False

            if self.dry_run:
                print(f"[cyan][DRY-RUN] Would stop EC2 instance:[cyan] [bold white]{instance_id}[/bold white]")
                return True

            self.ec2_client.stop_instances(InstanceIds=[instance_id])
            print(f"[bold green]✓ Stopped EC2 instance:[bold green] {instance_id}")
            return True
        except ClientError as e:
            print(f"[bold red]✗ Failed to stop instance {instance_id}:[bold red] {e}")
            return False

    def delete_unattached_ebs(self, volume_id: str) -> bool:
        """Deletes an unattached EBS volume with protection check and dry-run mode."""
        try:
            vol_info = self.ec2_client.describe_volumes(VolumeIds=[volume_id])
            tags = vol_info["Volumes"][0].get("Tags", [])
            
            if self.is_resource_protected(tags):
                print(f"[bold yellow]🔒 Skipped protected EBS volume:[bold yellow] {volume_id}")
                return False

            if self.dry_run:
                print(f"[cyan][DRY-RUN] Would delete unattached EBS volume:[cyan] [bold white]{volume_id}[/bold white]")
                return True

            self.ec2_client.delete_volume(VolumeId=volume_id)
            print(f"[bold green]✓ Deleted EBS volume:[bold green] {volume_id}")
            return True
        except ClientError as e:
            print(f"[bold red]✗ Failed to delete volume {volume_id}:[bold red] {e}")
            return False

    def release_unused_eip(self, allocation_id: str) -> bool:
        """Releases an unassociated Elastic IP address with dry-run mode."""
        try:
            if self.dry_run:
                print(f"[cyan][DRY-RUN] Would release Elastic IP:[cyan] [bold white]{allocation_id}[/bold white]")
                return True

            self.ec2_client.release_address(AllocationId=allocation_id)
            print(f"[bold green]✓ Released Elastic IP:[bold green] {allocation_id}")
            return True
        except ClientError as e:
            print(f"[bold red]✗ Failed to release Elastic IP {allocation_id}:[bold red] {e}")
            return False