"""
SPECTRA Layer 1 - Test Case Designer Agent
Designs executable test cases from scenarios.
"""

from __future__ import annotations
from typing import Any, Dict, List
from loguru import logger
from core.context_manager import SPECTRAContext
from core.test_runner import TestCase, TestMode
import uuid


class TestCaseDesignerAgent:
    """Layer 1 Agent - Designs executable test cases from scenarios."""

    def __init__(self, context: SPECTRAContext):
        self.context = context

    async def design_tests(self, scenarios: List[Dict[str, Any]]) -> List[TestCase]:
        """Design executable test cases from scenarios."""
        logger.info("🎨 Test case design started")

        test_cases = []
        for scenario in scenarios:
            tc = self._create_test_case(scenario)
            test_cases.append(tc)

        logger.success(f"✅ Designed {len(test_cases)} test cases")
        return test_cases

    def _create_test_case(self, scenario: Dict[str, Any]) -> TestCase:
        endpoint = scenario.get("endpoint", {})
        return TestCase(
            id=str(uuid.uuid4())[:8],
            name=scenario.get("name", ""),
            description=endpoint.get("description", ""),
            mode=TestMode.API,
            endpoint=endpoint.get("path"),
            method=endpoint.get("method"),
            expected_status=scenario.get("expected_status", 200),
            tags=[scenario.get("type", "")] + endpoint.get("tags", [])
        )
