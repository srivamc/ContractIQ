"""
ContractIQ - Agentic Property-Based Testing
============================================
Property-based testing for agent behaviour using Hypothesis.
Tests invariants, contracts and emergent agent properties across
all 3-layer agent architecture (Layer0 / Layer1 / Layer2).
"""

from __future__ import annotations

import asyncio
import pytest
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, invariant

# ---------------------------------------------------------------------------
# Shared Hypothesis strategies for ContractIQ domain objects
# ---------------------------------------------------------------------------

http_method = st.sampled_from(["GET", "POST", "PUT", "PATCH", "DELETE"])

path_segment = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters="-_"),
    min_size=1,
    max_size=20,
)

api_path = st.builds(
    lambda segments: "/" + "/".join(segments),
    st.lists(path_segment, min_size=1, max_size=4),
)

endpoint_strategy = st.fixed_dictionaries({
    "method": http_method,
    "path": api_path,
    "tags": st.lists(st.sampled_from(["auth", "payment", "user", "admin", "public"]), max_size=3),
    "security": st.booleans(),
    "parameters": st.lists(
        st.fixed_dictionaries({"name": path_segment, "in": st.sampled_from(["query", "path", "header"])}),
        max_size=5,
    ),
    "responses": st.dictionaries(
        st.sampled_from(["200", "400", "401", "403", "404", "500"]),
        st.just({}),
        max_size=4,
    ),
})

knowledge_base_strategy = st.fixed_dictionaries({
    "endpoints": st.lists(endpoint_strategy, min_size=0, max_size=20),
    "schemas": st.dictionaries(path_segment, st.just({}), max_size=10),
    "auth_flows": st.lists(st.sampled_from(["oauth2", "apikey", "basic", "bearer"]), max_size=3),
    "ui_components": st.lists(path_segment, max_size=10),
    "metadata": st.fixed_dictionaries({
        "spec_type": st.sampled_from(["openapi", "asyncapi", "graphql", "postman"]),
        "spec_version": st.sampled_from(["3.0", "3.1", "2.0"]),
        "target_url": st.just("https://api.example.com"),
        "project_name": path_segment,
    }),
})


# ---------------------------------------------------------------------------
# Helper: build minimal mock context from knowledge_base dict
# ---------------------------------------------------------------------------

def build_mock_context(kb: Dict[str, Any]) -> MagicMock:
    ctx = MagicMock()
    ctx.endpoints = kb["endpoints"]
    ctx.schemas = kb["schemas"]
    ctx.auth_flows = kb["auth_flows"]
    ctx.ui_components = kb["ui_components"]
    ctx.spec_type = kb["metadata"]["spec_type"]
    ctx.spec_version = kb["metadata"]["spec_version"]
    ctx.target_url = kb["metadata"]["target_url"]
    ctx.project_name = kb["metadata"]["project_name"]
    ctx.knowledge_base = {}
    return ctx


# ---------------------------------------------------------------------------
# Property: SpecAnalyzerAgent
# ---------------------------------------------------------------------------

class TestSpecAnalyzerAgentProperties:
    """Property-based tests for Layer 0 - SpecAnalyzerAgent."""

    @given(kb=knowledge_base_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_endpoint_coverage_keys_match_endpoints(self, kb: Dict[str, Any]):
        """Property: get_endpoint_coverage() keys always match endpoint count."""
        from agents.layer0.spec_analyzer_agent import SpecAnalyzerAgent

        ctx = build_mock_context(kb)
        agent = SpecAnalyzerAgent.__new__(SpecAnalyzerAgent)
        agent.context = ctx
        agent.knowledge_base = kb

        coverage = agent.get_endpoint_coverage()

        assert len(coverage) == len(kb["endpoints"]), (
            "Coverage dict length must equal endpoint count"
        )
        for key in coverage:
            assert isinstance(key, str), "Coverage key must be string"
            assert coverage[key] is False, "Initial coverage must be False for all endpoints"

    @given(kb=knowledge_base_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_critical_endpoints_subset_of_all_endpoints(self, kb: Dict[str, Any]):
        """Property: critical endpoints must always be a subset of all endpoints."""
        from agents.layer0.spec_analyzer_agent import SpecAnalyzerAgent

        ctx = build_mock_context(kb)
        agent = SpecAnalyzerAgent.__new__(SpecAnalyzerAgent)
        agent.context = ctx
        agent.knowledge_base = kb

        critical = agent.get_critical_endpoints()
        all_endpoints = kb["endpoints"]

        # Every critical endpoint must appear in the full list
        for ep in critical:
            assert ep in all_endpoints, "Critical endpoint not found in full endpoint list"

    @given(kb=knowledge_base_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_scenario_suggestions_bounded(self, kb: Dict[str, Any]):
        """Property: suggested scenarios capped at 50."""
        from agents.layer0.spec_analyzer_agent import SpecAnalyzerAgent

        ctx = build_mock_context(kb)
        agent = SpecAnalyzerAgent.__new__(SpecAnalyzerAgent)
        agent.context = ctx
        agent.knowledge_base = kb

        scenarios = agent.suggest_test_scenarios()

        assert len(scenarios) <= 50, "Scenarios must be capped at 50"
        assert all(isinstance(s, str) for s in scenarios), "All scenarios must be strings"


# ---------------------------------------------------------------------------
# Property: Agent Output Determinism
# ---------------------------------------------------------------------------

class TestAgentDeterminism:
    """Property: same input must always yield same output (no hidden state)."""

    @given(kb=knowledge_base_strategy)
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_coverage_is_deterministic(self, kb: Dict[str, Any]):
        """Given the same knowledge base, endpoint coverage must be identical on two calls."""
        from agents.layer0.spec_analyzer_agent import SpecAnalyzerAgent

        ctx = build_mock_context(kb)
        agent = SpecAnalyzerAgent.__new__(SpecAnalyzerAgent)
        agent.context = ctx
        agent.knowledge_base = kb

        result_a = agent.get_endpoint_coverage()
        result_b = agent.get_endpoint_coverage()

        assert result_a == result_b, "Endpoint coverage must be deterministic"


# ---------------------------------------------------------------------------
# Property: Agent Context Isolation
# ---------------------------------------------------------------------------

class TestAgentContextIsolation:
    """Property: agents must not mutate shared context in unexpected ways."""

    @given(kb=knowledge_base_strategy)
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_suggest_scenarios_does_not_mutate_knowledge_base(self, kb: Dict[str, Any]):
        """Calling suggest_test_scenarios must not mutate the knowledge base."""
        from agents.layer0.spec_analyzer_agent import SpecAnalyzerAgent
        import copy

        ctx = build_mock_context(kb)
        agent = SpecAnalyzerAgent.__new__(SpecAnalyzerAgent)
        agent.context = ctx
        agent.knowledge_base = copy.deepcopy(kb)
        kb_before = copy.deepcopy(agent.knowledge_base)

        agent.suggest_test_scenarios()

        assert agent.knowledge_base == kb_before, "suggest_test_scenarios must not mutate knowledge_base"


# ---------------------------------------------------------------------------
# Stateful Property Test: Agent Lifecycle Machine
# ---------------------------------------------------------------------------

class AgentLifecycleMachine(RuleBasedStateMachine):
    """
    Stateful property test that models the lifecycle of a SpecAnalyzerAgent.
    Verifies invariants hold across arbitrary sequences of operations.
    """

    def __init__(self):
        super().__init__()
        from agents.layer0.spec_analyzer_agent import SpecAnalyzerAgent
        self.AgentClass = SpecAnalyzerAgent
        self.agent = None
        self.current_kb = {
            "endpoints": [],
            "schemas": {},
            "auth_flows": [],
            "ui_components": [],
            "metadata": {
                "spec_type": "openapi",
                "spec_version": "3.0",
                "target_url": "https://api.example.com",
                "project_name": "test",
            },
        }

    @initialize(kb=knowledge_base_strategy)
    def create_agent(self, kb):
        ctx = build_mock_context(kb)
        self.agent = self.AgentClass.__new__(self.AgentClass)
        self.agent.context = ctx
        self.agent.knowledge_base = kb
        self.current_kb = kb

    @rule(endpoint=endpoint_strategy)
    def add_endpoint(self, endpoint):
        self.agent.knowledge_base["endpoints"].append(endpoint)
        self.current_kb = self.agent.knowledge_base

    @invariant()
    def coverage_count_matches_endpoints(self):
        if self.agent is None:
            return
        coverage = self.agent.get_endpoint_coverage()
        assert len(coverage) == len(self.agent.knowledge_base["endpoints"])

    @invariant()
    def scenarios_never_exceed_cap(self):
        if self.agent is None:
            return
        scenarios = self.agent.suggest_test_scenarios()
        assert len(scenarios) <= 50


TestAgentLifecycle = AgentLifecycleMachine.TestCase


# ---------------------------------------------------------------------------
# Async property tests for analyze_spec pipeline
# ---------------------------------------------------------------------------

class TestAsyncAgentProperties:
    """Property-based tests for async agent pipeline."""

    @given(kb=knowledge_base_strategy)
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_analyze_spec_populates_all_knowledge_base_keys(self, kb: Dict[str, Any]):
        """After analyze_spec, the returned dict must contain all 5 required keys."""
        from agents.layer0.spec_analyzer_agent import SpecAnalyzerAgent

        async def _run():
            ctx = build_mock_context(kb)
            ctx.endpoints = kb["endpoints"]
            ctx.schemas = kb["schemas"]
            ctx.auth_flows = kb["auth_flows"]
            ctx.ui_components = kb["ui_components"]

            agent = SpecAnalyzerAgent.__new__(SpecAnalyzerAgent)
            agent.context = ctx
            agent.knowledge_base = {
                "endpoints": [],
                "schemas": {},
                "auth_flows": [],
                "ui_components": [],
                "metadata": {},
            }

            # Mock the parser to avoid actual file I/O
            mock_parser = AsyncMock()
            mock_parser.parse = AsyncMock()
            agent.parser = mock_parser

            result = await agent.analyze_spec("mock_spec.yaml")
            return result

        result = asyncio.get_event_loop().run_until_complete(_run())
        required_keys = {"endpoints", "schemas", "auth_flows", "ui_components", "metadata"}
        assert required_keys.issubset(set(result.keys())), (
            f"Missing keys in knowledge base: {required_keys - set(result.keys())}"
        )
