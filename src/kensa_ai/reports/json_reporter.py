"""
JSON report generator for Kensa-AI.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class JSONReporter:
    """
    Generate machine-readable JSON reports.
    """
    
    def __init__(self, pretty: bool = True, include_evidence: bool = True):
        """
        Initialize the JSON reporter.
        
        Args:
            pretty: Use pretty formatting with indentation
            include_evidence: Include full evidence data in report
        """
        self.pretty = pretty
        self.include_evidence = include_evidence
    
    def generate(self, results: dict[str, Any], output_path: Path) -> Path:
        """
        Generate JSON report from test results.
        
        Args:
            results: Test results dictionary
            output_path: Path to write the report
            
        Returns:
            Path to generated report
        """
        # Prepare report data
        report = self._prepare_report(results)
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            if self.pretty:
                json.dump(report, f, indent=2, default=str)
            else:
                json.dump(report, f, default=str)
        
        return output_path
    
    def _prepare_report(self, results: dict[str, Any]) -> dict[str, Any]:
        """Prepare the report data structure."""
        report = {
            "meta": {
                "tool": "Kensa-AI",
                "version": "0.1.0",
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "report_format_version": "1.0",
            },
            "run_id": results.get("run_id"),
            "timestamp": results.get("timestamp"),
            "duration_seconds": results.get("duration_seconds"),
            "target": results.get("target"),
            "summary": results.get("summary"),
        }
        
        # Include test results
        if self.include_evidence:
            report["results"] = results.get("results", [])
            report["evidence"] = results.get("evidence")
        else:
            # Exclude response text and detailed evidence
            report["results"] = [
                {
                    "test": r.get("test"),
                    "status": r.get("status"),
                    "result": {
                        "passed": r.get("result", {}).get("passed"),
                        "confidence": r.get("result", {}).get("confidence"),
                    } if r.get("result") else None,
                }
                for r in results.get("results", [])
            ]
        
        # Include configuration (sanitized)
        config = results.get("config", {})
        report["config"] = {
            "test_pack": config.get("tests", {}).get("pack"),
            "categories": config.get("tests", {}).get("categories"),
            "fail_on": config.get("execution", {}).get("fail_on"),
        }
        
        return report
    
    def to_string(self, results: dict[str, Any]) -> str:
        """
        Generate JSON report as string.
        
        Args:
            results: Test results dictionary
            
        Returns:
            JSON string
        """
        report = self._prepare_report(results)
        if self.pretty:
            return json.dumps(report, indent=2, default=str)
        return json.dumps(report, default=str)
