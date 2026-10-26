import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from src.utils import retry_on_throttling


class S3Scanner:
    def __init__(self, session: boto3.Session):
        self.session = session
        self.client = session.client("s3")

    @retry_on_throttling(max_retries=3)
    def scan_empty_buckets(self) -> list:
        """Finds S3 buckets with no objects."""
        findings = []
        try:
            response = self.client.list_buckets()
            for bucket in response.get("Buckets", []):
                bucket_name = bucket.get("Name")
                try:
                    objects = self.client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
                    if objects.get("KeyCount", 0) == 0:
                        findings.append({
                            "resource_id": bucket_name,
                            "resource_type": "S3 Bucket",
                            "state": "empty",
                            "recommendation": "Consider deleting empty bucket if no longer required."
                        })
                except ClientError:
                    continue
        except (ClientError, NoCredentialsError, PartialCredentialsError) as e:
            print(f"[red]Error scanning S3 empty buckets: Unable to locate AWS credentials or permission denied.[/red]")
        return findings

    @retry_on_throttling(max_retries=3)
    def scan_missing_lifecycle_policies(self) -> list:
        """Finds buckets without lifecycle transition/expiration configuration."""
        findings = []
        try:
            response = self.client.list_buckets()
            for bucket in response.get("Buckets", []):
                bucket_name = bucket.get("Name")
                try:
                    self.client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "")
                    if error_code == "NoSuchLifecycleConfiguration":
                        findings.append({
                            "resource_id": bucket_name,
                            "resource_type": "S3 Bucket",
                            "state": "no-lifecycle-rule",
                            "recommendation": "Configure lifecycle policy to transition old data to Glacier or delete."
                        })
        except (ClientError, NoCredentialsError, PartialCredentialsError) as e:
            print(f"[red]Error scanning S3 lifecycle policies: Unable to locate AWS credentials.[/red]")
        return findings

    def run_all_scans(self) -> dict:
        """Executes all S3 cost audits."""
        return {
            "empty_buckets": self.scan_empty_buckets(),
            "missing_lifecycle": self.scan_missing_lifecycle_policies()
        }