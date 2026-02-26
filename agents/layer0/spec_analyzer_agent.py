"""
ContractIQ Layer 0 - Spec Analyzer Agent
Knowledge Engine agent that parses all spec formats and builds reusable knowledge base.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from loguru import logger

from core.context_manager import ContractIQContext
from core.spec_parser import ContractIQSpecParser, SpecType


class SpecAnalyzerAgent:
    """Layer 0 Agent - Analyzes specs and builds knowledge base for downstream agents."""

    def __init__(self, context: ContractIQContext):
        self.context = context
        self.parser = ContractIQSpecParser(context)
        self.knowledge_base: Dict[str, Any] = {
            "endpoints": [],
            "schemas": {},
            "auth_flows": [],
            "ui_components": [],
            "metadata": {}
        }

    async def analyze_spec(self, spec_path: str, spec_type: Optional[SpecType] = None) -> Dict[str, Any]:
        """Main entry point - analyze spec and build knowledge base."""
        logger.info(f"Analyzing spec: {spec_path}")

        # Parse the spec
        await self.parser.parse()

        # Extract knowledge
        await self._extract_endpoints()
        await self._extract_schemas()
        await self._extract_auth_flows()
        await self._extract_ui_components()
        self._extract_metadata()

        # Persist knowledge to context
        await self._persist_knowledge()

        logger.success(
            f"Analysis complete: {len(self.knowledge_base['endpoints'])} endpoints, "
            f"{len(self.knowledge_base['schemas'])} schemas, "
            f"{len(self.knowledge_base['auth_flows'])} auth flows"
        )
        return self.knowledge_base

    async def _extract_endpoints(self) -> None:
        """Extract all API endpoints from parsed context."""
        for endpoint in self.context.endpoints:
            self.knowledge_base["endpoints"].append(endpoint)
        logger.debug(f"Extracted {len(self.knowledge_base['endpoints'])} endpoints")

    async def _extract_schemas(self) -> None:
        """Extract all data schemas from parsed context."""
        self.knowledge_base["schemas"].update(self.context.schemas)
        logger.debug(f"Extracted {len(self.knowledge_base['schemas'])} schemas")

    async def _extract_auth_flows(self) -> None:
        """Extract authentication and security requirements."""
        for auth_flow in self.context.auth_flows:
            self.knowledge_base["auth_flows"].append(auth_flow)
        logger.debug(f"Extracted {len(self.knowledge_base['auth_flows'])} auth flows")

    async def _extract_ui_components(self) -> None:
        """Extract UI component tree from Playwright traces/HAR."""
        for component in self.context.ui_components:
            self.knowledge_base["ui_components"].append(component)
        logger.debug(f"Extracted {len(self.knowledge_base['ui_components'])} UI components")

    def _extract_metadata(self) -> None:
        """Extract spec metadata (version, title, etc.)."""
        self.knowledge_base["metadata"] = {
            "spec_type": self.context.spec_type,
            "spec_version": self.context.spec_version,
            "target_url": self.context.target_url,
            "project_name": self.context.project_name,
        }

    async def _persist_knowledge(self) -> None:
        """Persist knowledge base to context for cross-agent use."""
        self.context.knowledge_base = self.knowledge_base
        logger.debug("Knowledge base persisted to context")

    def get_endpoint_coverage(self) -> Dict[str, bool]:
        """Return which endpoints have test coverage."""
        return {f"{e['method']} {e['path']}": False for e in self.knowledge_base["endpoints"]}

    def get_critical_endpoints(self) -> List[Dict[str, Any]]:
        """Identify critical endpoints that require priority testing."""
        critical_tags = ["auth", "payment", "user", "critical", "important"]
        critical = []
        for endpoint in self.knowledge_base["endpoints"]:
            if any(tag.lower() in critical_tags for tag in endpoint.get("tags", [])):
                critical.append(endpoint)
            # POST/PUT/DELETE are higher priority than GET
            if endpoint["method"] in ["POST", "PUT", "DELETE", "PATCH"]:
                critical.append(endpoint)
        return critical

    def suggest_test_scenarios(self) -> List[str]:
        """Suggest high-value test scenarios based on spec analysis."""
        scenarios = []
        # Suggest scenarios based on endpoints
        for endpoint in self.knowledge_base["endpoints"]:
            method = endpoint["method"]
            path = endpoint["path"]
            scenarios.append(f"Happy path: {method} {path} returns expected schema")

            # Auth scenarios
            if endpoint.get("security"):
                scenarios.append(f"Auth test: {method} {path} requires authentication")
                scenarios.append(f"Negative: {method} {path} fails without valid token")

            # Input validation
            if endpoint.get("parameters"):
                scenarios.append(f"Validation: {method} {path} validates required parameters")

            # Error handling
            if "404" in endpoint.get("responses", {}):
                scenarios.append(f"Error: {method} {path} returns 404 for invalid resource")

        return scenarios[:50]  # Limit to top 50
