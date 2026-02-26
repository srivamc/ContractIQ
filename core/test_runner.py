"""
SPECTRA Test Runner
Parallel test execution engine supporting API and UI tests.
Handles concurrent execution with configurable thread pools.
"""

from __future__ import annotations

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from loguru import logger

from core.context_manager import SPECTRAContext


class TestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestMode(str, Enum):
    API = "api"
    UI = "ui"
    MIXED = "mixed"


@dataclass
class TestCase:
    """Represents a single executable test case."""
    id: str
    name: str
    description: str
    mode: TestMode
    endpoint: Optional[str] = None
    method: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Any] = None
    expected_status: int = 200
    expected_schema: Optional[Dict] = None
    ui_steps: List[Dict] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    priority: int = 5
    timeout: int = 30
    retry_count: int = 0
    status: TestStatus = TestStatus.PENDING
    result: Optional[Dict] = None
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class TestSuite:
    """Collection of test cases to execute."""
    id: str
    name: str
    description: str
    test_cases: List[TestCase] = field(default_factory=list)
    mode: TestMode = TestMode.MIXED
    parallel: bool = True
    max_workers: int = 20
    timeout: int = 300


@dataclass
class ExecutionResult:
    """Result of a test suite execution."""
    suite_id: str
    suite_name: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration_ms: float = 0.0
    test_results: List[TestCase] = field(default_factory=list)
    coverage_percent: float = 0.0
    timestamp: str = ""


class SPECTRATestRunner:
    """Parallel test execution engine for SPECTRA framework."""

    def __init__(self, context: SPECTRAContext, max_workers: int = 100):
        self.context = context
        self.max_workers = max_workers
        self._api_client = None
        self._ui_driver = None
        self._before_hooks: List[Callable] = []
        self._after_hooks: List[Callable] = []
        self._on_test_complete: Optional[Callable] = None

    def register_before_hook(self, hook: Callable) -> None:
        """Register a hook to run before each test."""
        self._before_hooks.append(hook)

    def register_after_hook(self, hook: Callable) -> None:
        """Register a hook to run after each test."""
        self._after_hooks.append(hook)

    def on_test_complete(self, callback: Callable) -> None:
        """Register callback for test completion events."""
        self._on_test_complete = callback

    async def run_suite(self, suite: TestSuite) -> ExecutionResult:
        """Execute a full test suite with parallel workers."""
        logger.info(f"Starting suite: {suite.name} ({len(suite.test_cases)} tests)")
        start_time = time.time()

        result = ExecutionResult(
            suite_id=suite.id,
            suite_name=suite.name,
            total=len(suite.test_cases),
            timestamp=str(int(start_time))
        )

        # Sort by priority (lower number = higher priority)
        sorted_tests = sorted(suite.test_cases, key=lambda t: t.priority)

        if suite.parallel:
            completed = await self._run_parallel(sorted_tests, suite.max_workers)
        else:
            completed = await self._run_sequential(sorted_tests)

        for tc in completed:
            result.test_results.append(tc)
            if tc.status == TestStatus.PASSED:
                result.passed += 1
            elif tc.status == TestStatus.FAILED:
                result.failed += 1
            elif tc.status == TestStatus.SKIPPED:
                result.skipped += 1
            else:
                result.errors += 1

        result.duration_ms = (time.time() - start_time) * 1000
        result.coverage_percent = (result.passed / result.total * 100) if result.total > 0 else 0.0

        logger.info(
            f"Suite complete: {result.passed}/{result.total} passed "
            f"({result.coverage_percent:.1f}%) in {result.duration_ms:.0f}ms"
        )
        return result

    async def _run_parallel(self, tests: List[TestCase], max_workers: int) -> List[TestCase]:
        """Execute tests in parallel using thread pool."""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=min(max_workers, self.max_workers)) as executor:
            futures = {
                executor.submit(self._run_single_sync, tc): tc
                for tc in tests
            }
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    tc = futures[future]
                    tc.status = TestStatus.ERROR
                    tc.error = str(e)
        return tests

    async def _run_sequential(self, tests: List[TestCase]) -> List[TestCase]:
        """Execute tests one at a time."""
        for tc in tests:
            await self._run_single(tc)
        return tests

    def _run_single_sync(self, tc: TestCase) -> None:
        """Synchronous wrapper for async test execution."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._run_single(tc))
        finally:
            loop.close()

    async def _run_single(self, tc: TestCase) -> None:
        """Execute a single test case."""
        tc.status = TestStatus.RUNNING
        start = time.time()

        # Run before hooks
        for hook in self._before_hooks:
            await hook(tc)

        try:
            if tc.mode == TestMode.API:
                await self._execute_api_test(tc)
            elif tc.mode == TestMode.UI:
                await self._execute_ui_test(tc)
            else:
                await self._execute_mixed_test(tc)
        except asyncio.TimeoutError:
            tc.status = TestStatus.ERROR
            tc.error = f"Test timed out after {tc.timeout}s"
        except Exception as e:
            if tc.retry_count > 0:
                tc.retry_count -= 1
                logger.warning(f"Retrying test {tc.id}: {e}")
                await self._run_single(tc)
                return
            tc.status = TestStatus.FAILED
            tc.error = str(e)
        finally:
            tc.duration_ms = (time.time() - start) * 1000

        # Run after hooks
        for hook in self._after_hooks:
            await hook(tc)

        if self._on_test_complete:
            await self._on_test_complete(tc)

        logger.debug(f"Test {tc.id}: {tc.status.value} ({tc.duration_ms:.0f}ms)")

    async def _execute_api_test(self, tc: TestCase) -> None:
        """Execute an API test case using httpx."""
        import httpx

        base_url = self.context.target_url or ""
        url = f"{base_url}{tc.endpoint}"

        async with httpx.AsyncClient(timeout=tc.timeout) as client:
            method = tc.method.upper() if tc.method else "GET"
            response = await client.request(
                method=method,
                url=url,
                params=tc.params,
                headers={**self.context.default_headers, **tc.headers},
                json=tc.body
            )

        # Validate status
        if response.status_code != tc.expected_status:
            tc.status = TestStatus.FAILED
            tc.error = f"Expected {tc.expected_status}, got {response.status_code}"
            tc.result = {"status_code": response.status_code, "body": response.text[:500]}
            return

        # Validate schema if provided
        if tc.expected_schema:
            from jsonschema import validate, ValidationError
            try:
                validate(instance=response.json(), schema=tc.expected_schema)
            except ValidationError as e:
                tc.status = TestStatus.FAILED
                tc.error = f"Schema validation failed: {e.message}"
                return

        tc.status = TestStatus.PASSED
        tc.result = {
            "status_code": response.status_code,
            "response_time_ms": response.elapsed.total_seconds() * 1000,
            "body_preview": response.text[:200]
        }

    async def _execute_ui_test(self, tc: TestCase) -> None:
        """Execute a UI test case using Playwright."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                for step in tc.ui_steps:
                    action = step.get("action", "")
                    selector = step.get("selector", "")
                    value = step.get("value", "")

                    if action == "navigate":
                        await page.goto(value or self.context.target_url)
                    elif action == "click":
                        await page.click(selector)
                    elif action == "fill":
                        await page.fill(selector, value)
                    elif action == "assert_text":
                        text = await page.text_content(selector)
                        assert value in text, f"Expected '{value}' in '{text}'"
                    elif action == "assert_visible":
                        assert await page.is_visible(selector), f"Element not visible: {selector}"
                    elif action == "screenshot":
                        await page.screenshot(path=f"/tmp/spectra_{tc.id}.png")

                tc.status = TestStatus.PASSED
                tc.result = {"steps_completed": len(tc.ui_steps)}
            except Exception as e:
                tc.status = TestStatus.FAILED
                tc.error = str(e)
            finally:
                await browser.close()

    async def _execute_mixed_test(self, tc: TestCase) -> None:
        """Execute a test that involves both API and UI steps."""
        # For mixed tests, run API portion first then UI
        if tc.endpoint:
            await self._execute_api_test(tc)
        if tc.ui_steps and tc.status != TestStatus.FAILED:
            await self._execute_ui_test(tc)

    def create_test_from_endpoint(self, endpoint: Dict[str, Any]) -> TestCase:
        """Create a TestCase from a parsed endpoint definition."""
        import uuid
        return TestCase(
            id=str(uuid.uuid4())[:8],
            name=f"{endpoint.get('method', 'GET')} {endpoint.get('path', '/')}",
            description=endpoint.get('summary', ''),
            mode=TestMode.API,
            endpoint=endpoint.get('path'),
            method=endpoint.get('method', 'GET'),
            params=[p for p in endpoint.get('parameters', []) if p.get('in') == 'query'],
            expected_status=int(list(endpoint.get('responses', {200: {}}).keys())[0]),
            tags=endpoint.get('tags', [])
        )
