import csv
import json
from datetime import datetime
from rich import print


class ReportExporter:
    @staticmethod
    def export_to_json(findings: list, filepath: str):
        """Exports audit findings to a JSON file."""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(findings, f, indent=4)
            print(f"[bold green]✓ Report successfully exported to JSON:[bold green] {filepath}")
        except Exception as e:
            print(f"[bold red]✗ Failed to export JSON report:[bold red] {e}")

    @staticmethod
    def export_to_csv(findings: list, filepath: str):
        """Exports audit findings to a CSV file."""
        if not findings:
            print("[yellow]No findings to export to CSV.[/yellow]")
            return

        try:
            fieldnames = ["resource_id", "resource_type", "state", "region", "estimated_monthly_waste", "recommendation"]
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(findings)
            print(f"[bold green]✓ Report successfully exported to CSV:[bold green] {filepath}")
        except Exception as e:
            print(f"[bold red]✗ Failed to export CSV report:[bold red] {e}")

    @staticmethod
    def export_to_html(findings: list, total_savings: float, filepath: str):
        """Exports audit findings to a stylized HTML dashboard report."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        rows_html = ""
        if findings:
            for item in findings:
                res_id = item.get("resource_id") or item.get("public_ip", "N/A")
                rows_html += f"""
                <tr>
                    <td><span class="badge">{item.get('resource_type', 'N/A')}</span></td>
                    <td class="res-id">{res_id}</td>
                    <td class="state">{item.get('state', 'N/A')}</td>
                    <td class="region">{item.get('region', 'global')}</td>
                    <td class="cost">{item.get('estimated_monthly_waste', '$0.00')}</td>
                    <td>{item.get('recommendation', 'N/A')}</td>
                </tr>
                """
        else:
            rows_html = '<tr><td colspan="6" style="text-align:center;">No idle cloud resources detected!</td></tr>'

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AWS Cloud Cost Audit Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 40px; }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #334155; padding-bottom: 20px; margin-bottom: 30px; }}
        h1 {{ margin: 0; font-size: 28px; color: #38bdf8; }}
        .timestamp {{ color: #94a3b8; font-size: 14px; }}
        .summary-card {{ background-color: #1e293b; border-radius: 12px; padding: 24px; margin-bottom: 30px; border: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }}
        .summary-title {{ font-size: 14px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }}
        .summary-amount {{ font-size: 36px; font-weight: bold; color: #4ade80; margin-top: 8px; }}
        table {{ width: 100%; border-collapse: collapse; background-color: #1e293b; border-radius: 12px; overflow: hidden; border: 1px solid #334155; }}
        th {{ background-color: #0f172a; text-align: left; padding: 16px; color: #cbd5e1; font-weight: 600; font-size: 14px; text-transform: uppercase; }}
        td {{ padding: 16px; border-top: 1px solid #334155; font-size: 14px; }}
        tr:hover {{ background-color: #334155; }}
        .badge {{ background-color: #0284c7; color: white; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; }}
        .res-id {{ font-family: monospace; color: #f43f5e; font-weight: bold; }}
        .cost {{ color: #4ade80; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>AWS Cloud Cost Optimization Audit</h1>
                <div class="timestamp">Generated on: {now_str}</div>
            </div>
        </div>
        <div class="summary-card">
            <div>
                <div class="summary-title">Total Potential Monthly Waste</div>
                <div class="summary-amount">${total_savings:.2f} / month</div>
            </div>
            <div>
                <span class="badge" style="padding: 10px 16px; font-size: 14px;">Resources Scanned: {len(findings)}</span>
            </div>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Type</th>
                    <th>Resource ID</th>
                    <th>State</th>
                    <th>Region</th>
                    <th>Est. Monthly Waste</th>
                    <th>Recommendation</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"[bold green]✓ Report successfully exported to HTML Dashboard:[bold green] {filepath}")
        except Exception as e:
            print(f"[bold red]✗ Failed to export HTML report:[bold red] {e}")