"""
Main test runner for Kensa-AI.
"""

import asyncio
import hashlib
import time
import uuid
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from kensa_ai.connectors import BaseConnector, get_connector
from kensa_ai.core.config import Config
from kensa_ai.core.test_case import Severity, TestCase, TestEvidence, TestResult, TestStatus
from kensa_ai.reports import CSVReporter, HTMLReporter, JSONReporter
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
        self._rate_limit_lock = asyncio.Lock()
        self._last_request_ts = 0.0

        self._logger = logger.bind(run_id=self.run_id)

    async def initialize(self) -> None:
        """Initialize the runner and connector."""
        self.config.validate()
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

        # Filter by include tags (match any).
        if self.config.tags:
            include_tags = {tag.lower() for tag in self.config.tags}
            self.tests = [
                test
                for test in self.tests
                if any(tag.lower() in include_tags for tag in test.tags)
            ]

        # Exclude tests containing any excluded tag.
        if self.config.exclude_tags:
            exclude_tags = {tag.lower() for tag in self.config.exclude_tags}
            self.tests = [
                test
                for test in self.tests
                if not any(tag.lower() in exclude_tags for tag in test.tags)
            ]

        # Filter by severity values.
        if self.config.severities:
            allowed = {severity.lower() for severity in self.config.severities}
            self.tests = [test for test in self.tests if test.severity.value.lower() in allowed]

        # Apply baseline-guided focus strategy.
        focus_set: set[str] | None = None
        if self.config.focus_mode != "off" and self.config.focus_failed_test_names:
            focus_set = {name.strip().lower() for name in self.config.focus_failed_test_names}
            if self.config.focus_mode == "only":
                self.tests = [test for test in self.tests if test.name.strip().lower() in focus_set]

        # Smart priority ordering uses severity + history to surface high-value tests first.
        if self.config.smart_priority:
            if self.config.focus_mode == "prioritize" and focus_set is not None:
                self.tests.sort(
                    key=lambda test: (
                        test.name.strip().lower() not in focus_set,
                        -self._priority_score(test),
                    )
                )
            else:
                self.tests.sort(key=lambda test: -self._priority_score(test))
        elif self.config.focus_mode == "prioritize" and focus_set is not None:
            self.tests.sort(key=lambda test: test.name.strip().lower() not in focus_set)

        # Randomize if configured
        if self.config.randomize and not self.config.smart_priority:
            import random

            if self.config.seed is not None:
                random.seed(self.config.seed)
            random.shuffle(self.tests)
        elif self.config.randomize and self.config.smart_priority:
            self._logger.info("Ignoring randomize because smart_priority is enabled")

        # Budget planner: select best risk-per-second subset under time budget.
        if (
            self.config.planner_mode == "risk_per_second"
            and self.config.time_budget_seconds is not None
        ):
            original_count = len(self.tests)
            self.tests = self._apply_budget_planner(self.tests, self.config.time_budget_seconds)
            self._logger.info(
                "Applied budget planner",
                planner_mode=self.config.planner_mode,
                time_budget_seconds=self.config.time_budget_seconds,
                selected_tests=len(self.tests),
                original_tests=original_count,
            )

        # Apply optional global test cap after filtering and randomization.
        if self.config.max_tests is not None:
            self.tests = self.tests[: self.config.max_tests]

        self._logger.info("Test pack loaded", test_count=len(self.tests))

        return len(self.tests)

    def _priority_score(self, test: TestCase) -> float:
        """Calculate smart execution priority score for a test."""
        severity_weight = {
            "critical": 4.0,
            "high": 3.0,
            "medium": 2.0,
            "low": 1.0,
            "info": 0.5,
        }
        score = severity_weight.get(test.severity.value.lower(), 1.0)

        history_rates = self.config.history_category_failure_rates or {}
        score += float(history_rates.get(test.category, 0.0)) * 3.0

        outcomes = self.config.history_test_outcomes or {}
        history = outcomes.get(test.name)
        if history:
            status = str(history.get("status", ""))
            confidence = float(history.get("confidence", 0.0) or 0.0)
            if status == "failed":
                score += 4.0 + min(confidence, 1.0)
            elif status == "error":
                score += 2.5
            elif status == "passed":
                score -= 0.5

        risky_tags = {
            "exfil",
            "secret",
            "api-key",
            "system-prompt",
            "doxxing",
            "dan",
            "admin",
            "encoding",
        }
        score += 0.35 * sum(1 for tag in test.tags if tag.lower() in risky_tags)

        return score

    def _estimate_runtime_ms(self, test: TestCase) -> float:
        """Estimate runtime for a test from history, with severity fallback."""
        outcomes = self.config.history_test_outcomes or {}
        history = outcomes.get(test.name, {})
        historical_ms = float(history.get("execution_time_ms", 0.0) or 0.0)
        if historical_ms > 0:
            return max(historical_ms, 50.0)

        fallback_ms = {
            "critical": 1800.0,
            "high": 1500.0,
            "medium": 1200.0,
            "low": 900.0,
            "info": 700.0,
        }
        return fallback_ms.get(test.severity.value.lower(), 1200.0)

    def _apply_budget_planner(self, tests: list[TestCase], budget_seconds: float) -> list[TestCase]:
        """Select tests maximizing risk-per-second within a time budget."""
        budget_ms = budget_seconds * 1000.0
        if budget_ms <= 0:
            return tests

        candidates: list[tuple[float, float, int, TestCase]] = []
        for index, test in enumerate(tests):
            score = self._priority_score(test)
            runtime_ms = self._estimate_runtime_ms(test)
            efficiency = score / max(runtime_ms, 1.0)
            candidates.append((efficiency, score, index, test))

        # High efficiency first, then higher raw score, then stable original order.
        candidates.sort(key=lambda item: (-item[0], -item[1], item[2]))

        selected: list[TestCase] = []
        used_ms = 0.0
        for _, _, _, test in candidates:
            runtime_ms = self._estimate_runtime_ms(test)
            if used_ms + runtime_ms <= budget_ms:
                selected.append(test)
                used_ms += runtime_ms

        # Ensure at least one test is run when a budget is set but too tight.
        if not selected and tests:
            selected.append(max(tests, key=self._priority_score))

        # Keep final execution order by priority score.
        selected.sort(key=lambda test: -self._priority_score(test))
        return selected

    async def run(self) -> dict[str, Any]:
        """
        Execute all loaded tests.

        Returns:
            Dictionary with test results and summary.
        """
        self.start_time = datetime.now(timezone.utc)
        self._logger.info("Starting test run", test_count=len(self.tests))

        parallelism = max(1, self.config.parallel)
        total = len(self.tests)
        max_failures = self.config.max_failures
        failed_count = 0
        stopped_early = False

        if parallelism == 1:
            indexed_results: list[tuple[int, dict[str, Any]]] = []
            for i, test in enumerate(self.tests, 1):
                item = await self._run_test_with_capture(i, test, total)
                indexed_results.append(item)
                if item[1]["status"] == TestStatus.FAILED.value:
                    failed_count += 1
                    if max_failures is not None and failed_count >= max_failures:
                        stopped_early = True
                        break
        else:
            self._logger.info("Running tests in parallel", parallelism=parallelism)
            semaphore = asyncio.Semaphore(parallelism)

            async def _run_with_semaphore(
                index: int, test_case: TestCase
            ) -> tuple[int, dict[str, Any]]:
                async with semaphore:
                    return await self._run_test_with_capture(index, test_case, total)

            tasks = [
                asyncio.create_task(_run_with_semaphore(i, test))
                for i, test in enumerate(self.tests, 1)
            ]

            indexed_results = []
            for completed_task in asyncio.as_completed(tasks):
                result = await completed_task
                indexed_results.append(result)

                if result[1]["status"] == TestStatus.FAILED.value:
                    failed_count += 1
                    if max_failures is not None and failed_count >= max_failures:
                        stopped_early = True
                        for task in tasks:
                            if not task.done():
                                task.cancel()
                        for task in tasks:
                            with suppress(asyncio.CancelledError):
                                await task
                        break

        indexed_results.sort(key=lambda item: item[0])
        results = [result for _, result in indexed_results]

        self.end_time = datetime.now(timezone.utc)

        # Build results summary
        self.results = self._build_results(results)
        if stopped_early:
            self.results["stopped_early"] = True
            self.results["stop_reason"] = f"max_failures_reached:{max_failures}"

        return self.results

    async def _run_test_with_capture(
        self, index: int, test: TestCase, total: int
    ) -> tuple[int, dict[str, Any]]:
        """Execute one test and normalize success/error result payloads."""
        self._logger.debug(
            "Running test",
            test_num=index,
            total=total,
            test_name=test.name,
            category=test.category,
        )

        try:
            result = await self._execute_test(test)
            return (
                index,
                {
                    "test": test.to_dict(),
                    "result": result.to_dict(),
                    "status": TestStatus.PASSED.value if result.passed else TestStatus.FAILED.value,
                },
            )
        except Exception as e:
            self._logger.error("Test execution error", test_name=test.name, error=str(e))
            return (
                index,
                {
                    "test": test.to_dict(),
                    "result": None,
                    "status": TestStatus.ERROR.value,
                    "error": str(e),
                },
            )

    async def _execute_test(self, test: TestCase) -> TestResult:
        """Execute a single test case."""
        test.pre_execute()

        # Generate prompt
        prompt = test.generate_prompt()
        system_prompt = test.get_system_prompt() or self.config.target.system_prompt

        # Record evidence
        start_time = time.perf_counter()

        await self._apply_rate_limit()

        # Send to target
        assert self.connector is not None, "Runner not initialized. Call initialize() first."
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

    async def _apply_rate_limit(self) -> None:
        """Apply a global inter-request delay to respect configured request rate."""
        if self.config.target.rate_limit <= 0:
            return

        min_interval = 1.0 / self.config.target.rate_limit

        async with self._rate_limit_lock:
            now = time.perf_counter()
            elapsed = now - self._last_request_ts

            if self._last_request_ts > 0 and elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)

            self._last_request_ts = time.perf_counter()

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
                if self.start_time and self.end_time
                else 0
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
            "evidence": (
                {
                    "enabled": self.config.evidence_mode,
                    "hash_algorithm": self.config.evidence.hash_algorithm,
                }
                if self.config.evidence_mode
                else None
            ),
        }

    async def generate_reports(self) -> list[Path]:
        """Generate reports in configured formats."""
        generated = []

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"redteam_report_{timestamp}"

        if "json" in self.config.output_formats:
            json_path = self.config.output_dir / f"{base_name}.json"
            json_reporter = JSONReporter()
            json_reporter.generate(self.results, json_path)
            generated.append(json_path)
            self._logger.info("Generated JSON report", path=str(json_path))

        if "html" in self.config.output_formats:
            html_path = self.config.output_dir / f"{base_name}.html"
            html_reporter = HTMLReporter()
            html_reporter.generate(self.results, html_path)
            generated.append(html_path)
            self._logger.info("Generated HTML report", path=str(html_path))

        if "csv" in self.config.output_formats:
            csv_path = self.config.output_dir / f"{base_name}.csv"
            csv_reporter = CSVReporter()
            csv_reporter.generate(self.results, csv_path)
            generated.append(csv_path)
            self._logger.info("Generated CSV report", path=str(csv_path))

        return generated
