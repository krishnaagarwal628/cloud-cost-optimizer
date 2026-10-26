class CostEstimator:
    # Standard AWS monthly rates (in USD)
    EBS_GB_MONTHLY = 0.10          # $0.10 per GB/month for EBS
    EIP_MONTHLY = 3.60             # $0.005/hr * 720 hrs = $3.60/month per unused EIP
    RDS_STORAGE_GB_MONTHLY = 0.115 # $0.115 per GB/month for RDS allocated storage
    S3_EMPTY_BUCKET_MONTHLY = 0.50  # Estimated minimal management overhead

    @classmethod
    def estimate_item_waste(cls, item: dict) -> float:
        """Estimates monthly waste cost in USD for a single resource item."""
        res_type = item.get("resource_type", "")
        state = item.get("state", "")

        if res_type == "EBS Volume" and state == "unattached":
            size = item.get("size_gb", 20)  # Default 20GB fallback if not fetched
            return round(size * cls.EBS_GB_MONTHLY, 2)

        elif res_type == "Elastic IP" and state == "unassociated":
            return cls.EIP_MONTHLY

        elif res_type == "EC2 Instance" and state == "stopped":
            # Stopped instances don't pay for vCPU, but pay for attached root EBS volumes (~30GB avg)
            return round(30 * cls.EBS_GB_MONTHLY, 2)

        elif res_type == "RDS Instance" and state in ["stopped", "stopping"]:
            # Stopped RDS pays for allocated storage (~100GB avg estimate)
            return round(100 * cls.RDS_STORAGE_GB_MONTHLY, 2)

        elif res_type == "S3 Bucket" and state == "empty":
            return cls.S3_EMPTY_BUCKET_MONTHLY

        return 0.0

    @classmethod
    def calculate_total_savings(cls, all_findings: list) -> tuple[list, float]:
        """Calculates waste cost for every finding and sums up total potential monthly savings."""
        total_savings = 0.0
        enriched_findings = []

        for item in all_findings:
            monthly_waste = cls.estimate_item_waste(item)
            item["estimated_monthly_waste"] = f"${monthly_waste:.2f}"
            total_savings += monthly_waste
            enriched_findings.append(item)

        return enriched_findings, round(total_savings, 2)