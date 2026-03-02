"""
GA-QE Agent - Generative AI Quality Engineering
Patent Pending: TEMP/E-1/27374/2026-CHE
Copyright (c) 2026 Vamsee Krishna Srirama

Patented innovation: Complete autonomous loop Spec→Test→Execute→Report using LLM orchestration.
"""
from __future__ import annotations
import json
import os
import requests
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from loguru import logger

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    logger.warning("openai package not installed. LLM features will be limited.")


@dataclass
class GeneratedTestCase:
    test_id: str
    endpoint: str
    method: str
    description: str
    request_body: Optional[Dict] = None
    expected_status: int = 200
    test_type: str = "positive"  # positive, negative, boundary


@dataclass
class TestExecutionResult:
    test_id: str
    endpoint: str
    method: str
    passed: bool
    actual_status: int
    expected_status: int
    duration_ms: float
    error_message: Optional[str] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class GAQEReport:
    session_id: str
    total_tests: int
    passed: int
    failed: int
    pass_rate: float
    execution_time_ms: float
    test_results: List[TestExecutionResult]
    timestamp_utc: str
    spec_source: str
    patent_ref: str = "TEMP/E-1/27374/2026-CHE"

    def to_dict(self) -> Dict:
        return asdict(self)


class GAQEAgent:
    """
    PATENTED: Generative AI Quality Engineering Agent
    Application: TEMP/E-1/27374/2026-CHE

    Autonomous loop:
    1. Parse OpenAPI/AsyncAPI spec
    2. Generate tests via LLM
    3. Execute HTTP requests
    4. Report with structured results
    """

    def __init__(self, llm_provider: str = "openai", api_key: Optional[str] = None):
        self.llm_provider = llm_provider
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if llm_provider == "openai" and HAS_OPENAI and self._api_key:
            openai.api_key = self._api_key
            self._llm_enabled = True
        else:
            self._llm_enabled = False
            logger.warning("LLM not configured. Using fallback test generation.")

    def parse_openapi_spec(self, spec: Dict[str, Any]) -> List[Dict]:
        """Extract endpoints from OpenAPI 3.x spec."""
        endpoints = []
        paths = spec.get("paths", {})
        base_url = spec.get("servers", [{}])[0].get("url", "http://localhost:8000")
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.lower() in ["get", "post", "put", "delete", "patch"]:
                    endpoints.append({
                        "path": path,
                        "method": method.upper(),
                        "summary": details.get("summary", ""),
                        "description": details.get("description", ""),
                        "request_body": details.get("requestBody", {}),
                        "responses": details.get("responses", {}),
                        "base_url": base_url
                    })
        logger.info(f"Parsed {len(endpoints)} endpoints from OpenAPI spec")
        return endpoints

    def generate_tests_llm(self, endpoints: List[Dict]) -> List[GeneratedTestCase]:
        """PATENTED: LLM-powered test case generation."""
        if not self._llm_enabled:
            return self._generate_tests_fallback(endpoints)

        prompt = f"""You are a quality engineering AI. Generate comprehensive test cases for these API endpoints:

{json.dumps(endpoints, indent=2)}

For each endpoint, generate:
1. Positive test (happy path with valid data)
2. Negative test (invalid data, missing fields)
3. Boundary test (edge cases)

Return JSON array with format:
[
  {{
    "endpoint": "/path",
    "method": "GET",
    "description": "Test description",
    "request_body": {{...}} or null,
    "expected_status": 200,
    "test_type": "positive|negative|boundary"
  }}
]

Return ONLY valid JSON, no explanations."""

        try:
            if HAS_OPENAI:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2000
                )
                content = response.choices[0].message.content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                test_data = json.loads(content.strip())
                tests = [
                    GeneratedTestCase(
                        test_id=str(uuid.uuid4())[:8],
                        endpoint=t["endpoint"],
                        method=t["method"],
                        description=t["description"],
                        request_body=t.get("request_body"),
                        expected_status=t.get("expected_status", 200),
                        test_type=t.get("test_type", "positive")
                    )
                    for t in test_data
                ]
                logger.success(f"Generated {len(tests)} tests via LLM")
                return tests
        except Exception as e:
            logger.error(f"LLM test generation failed: {e}. Using fallback.")
        return self._generate_tests_fallback(endpoints)

    def _generate_tests_fallback(self, endpoints: List[Dict]) -> List[GeneratedTestCase]:
        """Fallback: rule-based test generation."""
        tests = []
        for ep in endpoints:
            # Positive test
            tests.append(GeneratedTestCase(
                test_id=str(uuid.uuid4())[:8],
                endpoint=ep["path"],
                method=ep["method"],
                description=f"Positive: {ep['method']} {ep['path']}",
                request_body=None if ep["method"] == "GET" else {},
                expected_status=200,
                test_type="positive"
            ))
            # Negative test (expect 400/404)
            if ep["method"] != "GET":
                tests.append(GeneratedTestCase(
                    test_id=str(uuid.uuid4())[:8],
                    endpoint=ep["path"],
                    method=ep["method"],
                    description=f"Negative: {ep['method']} {ep['path']} with invalid data",
                    request_body={"invalid_field": "bad_value"},
                    expected_status=400,
                    test_type="negative"
                ))
        logger.info(f"Generated {len(tests)} tests via fallback")
        return tests

    def execute_tests(self, tests: List[GeneratedTestCase], base_url: str) -> List[TestExecutionResult]:
        """PATENTED: Execute generated tests against live API."""
        results = []
        for test in tests:
            url = base_url.rstrip("/") + test.endpoint
            start_time = datetime.now()
            try:
                if test.method == "GET":
                    response = requests.get(url, timeout=10)
                elif test.method == "POST":
                    response = requests.post(url, json=test.request_body, timeout=10)
                elif test.method == "PUT":
                    response = requests.put(url, json=test.request_body, timeout=10)
                elif test.method == "DELETE":
                    response = requests.delete(url, timeout=10)
                else:
                    response = requests.request(test.method, url, json=test.request_body, timeout=10)

                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                passed = (response.status_code == test.expected_status)
                results.append(TestExecutionResult(
                    test_id=test.test_id,
                    endpoint=test.endpoint,
                    method=test.method,
                    passed=passed,
                    actual_status=response.status_code,
                    expected_status=test.expected_status,
                    duration_ms=duration_ms
                ))
                logger.info(f"Test {test.test_id}: {'PASS' if passed else 'FAIL'} | {test.method} {test.endpoint}")
            except Exception as e:
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                results.append(TestExecutionResult(
                    test_id=test.test_id,
                    endpoint=test.endpoint,
                    method=test.method,
                    passed=False,
                    actual_status=0,
                    expected_status=test.expected_status,
                    duration_ms=duration_ms,
                    error_message=str(e)
                ))
                logger.error(f"Test {test.test_id}: ERROR | {str(e)}")
        return results

    def generate_report(self, results: List[TestExecutionResult], session_id: str, spec_source: str) -> GAQEReport:
        """PATENTED: Generate structured quality report."""
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        pass_rate = round((passed / total * 100), 2) if total > 0 else 0.0
        total_time = sum(r.duration_ms for r in results)
        report = GAQEReport(
            session_id=session_id,
            total_tests=total,
            passed=passed,
            failed=failed,
            pass_rate=pass_rate,
            execution_time_ms=total_time,
            test_results=results,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            spec_source=spec_source
        )
        logger.success(f"GA-QE Report: {passed}/{total} passed ({pass_rate}%)")
        return report

    def run_full_loop(self, openapi_spec: Dict[str, Any], base_url: Optional[str] = None) -> GAQEReport:
        """
        PATENTED METHOD: Complete GA-QE loop.
        Spec → Parse → Generate Tests (LLM) → Execute → Report
        """
        session_id = str(uuid.uuid4())
        logger.info(f"Starting GA-QE loop | session={session_id}")
        # Step 1: Parse spec
        endpoints = self.parse_openapi_spec(openapi_spec)
        # Step 2: Generate tests via LLM
        tests = self.generate_tests_llm(endpoints)
        # Step 3: Execute tests
        if base_url is None:
            base_url = openapi_spec.get("servers", [{}])[0].get("url", "http://localhost:8000")
        results = self.execute_tests(tests, base_url)
        # Step 4: Generate report
        report = self.generate_report(results, session_id, "openapi_spec")
        logger.success(f"GA-QE loop complete | session={session_id}")
        return report


def run_gaqe_from_spec_file(spec_path: str, base_url: Optional[str] = None) -> GAQEReport:
    """Convenience function: run GA-QE from OpenAPI file path."""
    with open(spec_path, "r") as f:
        spec = json.load(f) if spec_path.endswith(".json") else {}
    agent = GAQEAgent()
    return agent.run_full_loop(spec, base_url)
