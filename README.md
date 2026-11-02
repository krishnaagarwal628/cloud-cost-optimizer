# Cloud Cost Optimizer CLI ☁️💰

A modular Python CLI tool to audit AWS infrastructure, detect idle resource waste using CloudWatch metrics, generate multi-format reports, and execute safe tag-protected remediations.

---

## 📅 4-Week Development Roadmap & Daily Logs

### **Week 1: Core CLI & EC2/EBS Scanner Setup**
* **Day 1:** Project directory structure (`src/`, `tests/`) setup and `requirements.txt` environment configuration (`boto3`, `typer`, `rich`).
* **Day 2:** `src/cli.py` base setup using `typer` for standard CLI commands (`scan`, `clean`).
* **Day 3:** AWS authentication wrapper in `src/utils.py` to handle `boto3.Session` profiles and regions.
* **Day 4:** `EC2Scanner` implementation (`src/scanners/ec2_scanner.py`) to detect stopped EC2 instances.
* **Day 5:** EBS scanner addition inside `EC2Scanner` to target unattached EBS volumes (`available` state).
* **Day 6:** Elastic IP (EIP) scanner logic for unassociated public IP addresses.
* **Day 7:** Basic `rich` table integration in CLI output to render initial audit findings.

---

### **Week 2: S3 & RDS Idle Resource Detection**
* **Day 8:** `S3Scanner` implementation (`src/scanners/s3_scanner.py`) to detect empty S3 buckets.
* **Day 9:** S3 lifecycle policy verification to identify buckets missing expiration/transition rules.
* **Day 10:** `RDSScanner` implementation (`src/scanners/rds_scanner.py`) for stopped/idle database instances.
* **Day 11:** RDS manual snapshot scanner to surface old, unattached database backups.

---

### **Week 3: CloudWatch Metrics, Cost Estimator & Multi-Region Audit**
* **Day 12:** Monthly cost estimation module (`src/cost_estimator.py`) mapping AWS resource pricing models.
* **Day 13:** Base JSON export implementation in `src/exporter.py` (`--output report.json`).
* **Day 14:** CSV exporter functionality addition (`--output report.csv`).
* **Day 15:** CloudWatch metrics engine integration (`scan_low_cpu_instances`) for 14-day sub-5% CPU instance profiling.
* **Day 16:** Unit test suite creation in `tests/test_scanners.py` using `unittest.mock`.
* **Day 17:** Parallel multi-region scanner orchestrator (`src/scanners/multi_region.py`) via `ThreadPoolExecutor`.
* **Day 18:** CLI integration for `--all-regions` (`-a`) flag for concurrent cross-region scanning.

---

### **Week 4: Safety Controls, Remediation Engine & HTML Exporter**
* **Day 19:** `RemediationEngine` creation (`src/remediation.py`) with tag exclusion rules (`Protection=true`, `DoNotDelete=true`).
* **Day 20:** Safety `--dry-run` CLI flag integration and unit tests in `tests/test_remediation.py` (4/4 tests passed).
* **Day 21:** Stylized HTML Dashboard Exporter implementation (`--output report.html`) and final project documentation.

---

## 🚀 CLI Commands Quick Reference

```powershell
# Single region audit
python -m src.cli scan --region us-east-1

# Parallel multi-region audit
python -m src.cli scan --all-regions

# HTML Dashboard export
python -m src.cli scan --output report.html

# Dry-run safety simulation
python -m src.cli clean --dry-run