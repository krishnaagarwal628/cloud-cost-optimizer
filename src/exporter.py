import csv
import json
from pathlib import Path
from rich import print


class ReportExporter:
    @staticmethod
    def export_to_json(findings: list, file_path: str) -> None:
        """Exports audit findings to a formatted JSON file."""
        try:
            path = Path(file_path)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(findings, f, indent=4)
            print(f"[bold green]✓ Report successfully saved to JSON:[bold green] [cyan]{path.resolve()}[/cyan]")
        except Exception as e:
            print(f"[bold red]✗ Failed to export JSON report:[bold red] {e}")

    @staticmethod
    def export_to_csv(findings: list, file_path: str) -> None:
        """Exports audit findings to a CSV spreadsheet file."""
        if not findings:
            print("[yellow]No findings to export to CSV.[/yellow]")
            return

        try:
            path = Path(file_path)
            fieldnames = [
                "resource_type",
                "resource_id",
                "state",
                "estimated_monthly_waste",
                "region",
                "recommendation"
            ]

            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                for item in findings:
                    row = item.copy()
                    if "resource_id" not in row and "public_ip" in row:
                        row["resource_id"] = row["public_ip"]
                    writer.writerow(row)

            print(f"[bold green]✓ Report successfully saved to CSV:[bold green] [cyan]{path.resolve()}[/cyan]")
        except Exception as e:
            print(f"[bold red]✗ Failed to export CSV report:[bold red] {e}")