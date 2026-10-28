from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3
from rich import print

from src.scanners.ec2_scanner import EC2Scanner
from src.scanners.rds_scanner import RDSScanner
from src.scanners.s3_scanner import S3Scanner
from src.utils import get_available_aws_regions


class MultiRegionScanner:
    def __init__(self, session: boto3.Session):
        self.session = session

    def _scan_single_region(self, region: str) -> list:
        """Runs EC2, S3, and RDS scans for a single specified AWS region."""
        findings = []
        try:
            # EC2 & CloudWatch Scans
            ec2_scanner = EC2Scanner(session=self.session, region_name=region)
            ec2_res = ec2_scanner.run_all_scans()
            findings.extend(
                ec2_res["stopped_instances"] +
                ec2_res["low_cpu_instances"] +
                ec2_res["unattached_ebs"] +
                ec2_res["unused_eips"]
            )

            # RDS Scans
            rds_scanner = RDSScanner(session=self.session, region_name=region)
            rds_res = rds_scanner.run_all_scans()
            findings.extend(
                rds_res["stopped_instances"] +
                rds_res["manual_snapshots"]
            )
        except Exception:
            pass
        return findings

    def scan_all_regions(self, max_workers: int = 10) -> list:
        """Scans all active AWS regions in parallel using thread pools."""
        regions = get_available_aws_regions(self.session)
        print(f"[bold yellow]Initiating Parallel Multi-Region Audit across {len(regions)} regions...[/bold yellow]")

        all_findings = []

        # Global S3 Audit (S3 is a global service)
        try:
            s3_scanner = S3Scanner(session=self.session)
            s3_res = s3_scanner.run_all_scans()
            all_findings.extend(s3_res["empty_buckets"] + s3_res["missing_lifecycle"])
        except Exception:
            pass

        # Regional Audits in Parallel Threads
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_region = {
                executor.submit(self._scan_single_region, region): region for region in regions
            }
            for future in as_completed(future_to_region):
                region_findings = future.result()
                if region_findings:
                    all_findings.extend(region_findings)

        return all_findings
    