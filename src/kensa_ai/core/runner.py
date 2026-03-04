"""
Main test runner for Kensa-AI.
"""

import asyncio
import hashlib
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from kensa_ai.connectors import BaseConnector, get_connector
from kensa_ai.core.config import Config
from kensa_ai.core.test_case import Severity, TestCase, TestEvidence, TestResult, TestStatus
from kensa_ai.reports import HTMLReporter, JSONReporter
from kensa_ai.test_packs import load_test_pack

logger = structlog.get_logger()


class Runner:
    """
    Main test runner that orchestrates test execution.

    Responsibilities:
    - Load configuration
    - Initialize connectors
    - Load and filter test packs
    - Execute tests
    - Collect evidence
    - Generate reports
    """

    def __init__(self, config: Config):
        self.config = config
        self.run_id = str(uuid.uuid4())
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None

        self.connector: BaseConnector | None = None
        self.tests: list[TestCase] = []
        self.results: dict[str, Any] = {}

        self._logger = logger.bind(run_id=self.run_id)

    async def initialize(self) -> None:
        """Initialize the runner and connector."""
        self._logger.info("Initializing runner", target_type=self.config.target_type)

        # Initialize connector
        self.connector = get_connector(
            connector_type=self.config.target_type,
            config=self.config.target,
        )

        # Validate connectivity
        await self.connector.validate()

        # Create output directory
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        self._logger.info("Runner initialized successfully")

    async def load_test_pack(self) -> int:
        """
        Load tests from the configured test pack.

        Returns:
            Number of tests loaded.
        """
        self._logger.info(
            "Loading test pack",
            pack=self.config.test_pack,
            categories=self.config.categories,
        )

        # Load tests from pack
        self.tests = load_test_pack(
            pack_name=self.config.test_pack,
            categories=self.config.categories,
            max_per_category=self.config.max_tests_per_category,
        )

        # Filter enabled tests
        self.tests = [t for t in self.tests if t.enabled]

        # Randomize if configured
        if self.config.randomize:
            import random
            if self.config.seed is not None:
                random.seed(self.config.seed)
            random.shuffle(self.tests)

        self._logger.info("Test pack loaded", test_count=len(self.tests))

        return len(self.tests)

    async def run(self) -> dict[str, Any]:
        """
        Execute all loaded tests.

        Returns:
            Dictionary with test results and summary.
        """
        self.start_time = datetime.now(timezone.utc)
        self._logger.info("Starting test run", test_count=len(self.tests))

        results = []

        for i, test in enumerate(self.tests, 1):
            self._logger.debug(
                "Running test",
                test_num=i,
                total=len(self.tests),
                test_name=test.name,
                category=test.category,
            )

            try:
                result = await self._execute_test(test)
                results.append({
                    "test": test.to_dict(),
                    "result": result.to_dict(),
                    "status": TestStatus.PASSED.value if result.passed else TestStatus.FAILED.value,
                })
            except Exception as e:
                self._logger.error("Test execution error", test_name=test.name, error=str(e))
                results.append({
                    "test": test.to_dict(),
                    "result": None,
                    "status": TestStatus.ERROR.value,
                    "error": str(e),
                })

            # Rate limiting
            if self.config.target.rate_limit > 0:
                await asyncio.sleep(1.0 / self.config.target.rate_limit)

        self.end_time = datetime.now(timezone.utc)

        # Build results summary
        self.results = self._build_results(results)

        return self.results

    async def _execute_test(self, test: TestCase) -> TestResult:
        """Execute a single test case."""
        test.pre_execute()

        # Generate prompt
        prompt = test.generate_prompt()
        system_prompt = test.get_system_prompt() or self.config.target.system_prompt

        # Record evidence
        start_time = time.perf_counter()

        # Send to target
        response = await self.connector.send_prompt(
            prompt=prompt,
            system_prompt=system_prompt,
        )

        execution_time = (time.perf_counter() - start_time) * 1000

        # Evaluate response
        result = test.evaluate(response)
        result.response_text = response
        result.response_hash = hashlib.sha256(response.encode()).hexdigest()
        result.execution_time_ms = execution_time

        # Collect evidence if enabled
        if self.config.evidence_mode:
            test.evidence = TestEvidence(
                request_hash=hashlib.sha256(prompt.encode()).hexdigest(),
                response_hash=result.response_hash,
                prompt_text=prompt if self.config.evidence.include_request_response else "",
                response_text=response if self.config.evidence.include_request_response else "",
                config_snapshot={
                    "target": self.config.target.name,
                    "model": self.config.target.model,
                },
            )

        test.result = result
        test.post_execute(response)

        return result

    def _build_results(self, results: list[dict]) -> dict[str, Any]:
        """Build the results summary."""
        total = len(results)
        passed = sum(1 for r in results if r["status"] == TestStatus.PASSED.value)
        failed = sum(1 for r in results if r["status"] == TestStatus.FAILED.value)
        errors = sum(1 for r in results if r["status"] == TestStatus.ERROR.value)

        # Count by severity
        by_severity = {sev.value: 0 for sev in Severity}
        by_category = {}

        for r in results:
            if r["status"] == TestStatus.FAILED.value:
                severity = r["test"].get("severity", "medium")
                by_severity[severity] = by_severity.get(severity, 0) + 1

            category = r["test"].get("category", "general")
            if category not in by_category:
                by_category[category] = {"passed": 0, "failed": 0, "error": 0}

            if r["status"] == TestStatus.PASSED.value:
                by_category[category]["passed"] += 1
            elif r["status"] == TestStatus.FAILED.value:
                by_category[category]["failed"] += 1
            else:
                by_category[category]["error"] += 1

        # Calculate score
        score = passed / total if total > 0 else 0.0

        return {
            "run_id": self.run_id,
            "timestamp": self.start_time.isoformat() if self.start_time else None,
            "duration_seconds": (
                (self.end_time - self.start_time).total_seconds()
                if self.start_time and self.end_time else 0
            ),
            "target": {
                "name": self.config.target.name,
                "type": self.config.target.type,
                "model": self.config.target.model,
            },
            "config": self.config.to_dict(),
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "score": score,
                "by_severity": by_severity,
                "by_category": by_category,
            },
            "results": results,
            "evidence": {
                "enabled": self.config.evidence_mode,
                "hash_algorithm": self.config.evidence.hash_algorithm,
            } if self.config.evidence_mode else None,
        }

    async def generate_reports(self) -> list[Path]:
        """Generate reports in configured formats."""
        generated = []

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"redteam_report_{timestamp}"

        if "json" in self.config.output_formats:
            json_path = self.config.output_dir / f"{base_name}.json"
            reporter = JSONReporter()
            reporter.generate(self.results, json_path)
            generated.append(json_path)
            self._logger.info("Generated JSON report", path=str(json_path))

        if "html" in self.config.output_formats:
            html_path = self.config.output_dir / f"{base_name}.html"
            reporter = HTMLReporter()
            reporter.generate(self.results, html_path)
            generated.append(html_path)
            self._logger.info("Generated HTML report", path=str(html_path))

        return generated
