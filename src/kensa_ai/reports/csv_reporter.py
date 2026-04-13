"""
CSV report generator for Kensa-AI.
"""

import csv
from pathlib import Path
from typing import Any


class CSVReporter:
    """
    Generate tabular CSV reports for spreadsheet and BI workflows.
    """

    def generate(self, results: dict[str, Any], output_path: Path) -> Path:
        """
        Generate CSV report from test results.

        Args:
            results: Test results dictionary
            output_path: Path to write the report

        Returns:
            Path to generated report
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "run_id",
            "timestamp",
            "status",
            "test_id",
            "test_name",
            "category",
            "severity",
            "tags",
            "confidence",
            "execution_time_ms",
            "response_hash",
            "error",
            "matched_patterns",
            "risk_indicators",
        ]

        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for item in results.get("results", []):
                test = item.get("test", {})
                result = item.get("result") or {}

                writer.writerow(
                    {
                        "run_id": results.get("run_id", ""),
                        "timestamp": results.get("timestamp", ""),
                        "status": item.get("status", ""),
                        "test_id": test.get("id", ""),
                        "test_name": test.get("name", ""),
                        "category": test.get("category", ""),
                        "severity": test.get("severity", ""),
                        "tags": ",".join(test.get("tags", [])),
                        "confidence": result.get("confidence", ""),
                        "execution_time_ms": result.get("execution_time_ms", ""),
                        "response_hash": result.get("response_hash", ""),
                        "error": item.get("error", ""),
                        "matched_patterns": ",".join(result.get("matched_patterns", [])),
                        "risk_indicators": ",".join(result.get("risk_indicators", [])),
                    }
                )

        return output_path
