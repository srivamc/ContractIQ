"""
SPECTRA Layer 0 - Spec Analyzer Agent
Knowledge Engine agent that parses all spec formats and builds reusable knowledge base.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from loguru import logger

from core.context_manager import SPECTRAContext
from core.spec_parser import SPECTRASpecParser, SpecType


class SpecAnalyzerAgent:
    """Layer 0 Agent - Analyzes specs and builds knowledge base for downstream agents."""

    def __init__(self, context: SPECTRAContext):
        self.context = context
        self.parser = SPECTRASpecParser(context)
        self.knowledge_base: Dict[str, Any] = {
            "endpoints": [],
            "schemas": {},
            "auth_flows": [],
            "ui_components": [],
            "metadata": {}
        }

    async def analyze_spec(self, spec_path: str, spec_type: Optional[SpecType] = None) -> Dict[str, Any]:
        """Main entry point - analyze spec and build knowledge base."""
        logger.info(f"🔍 Analyzing spec: {spec_path}")

        # Parse the spec
        parsed = await self.parser.parse_spec(spec_path, spec_type)

        # Extract knowledge
        await self._extract_endpoints(parsed)
        await self._extract_schemas(parsed)
        await self._extract_auth_flows(parsed)
        await self._extract_ui_components(parsed)
        self._extract_metadata(parsed)

        # Persist knowledge to MCP Memory
        await self._persist_knowledge()

        logger.success(
            f"✅ Analysis complete: {len(self.knowledge_base['endpoints'])} endpoints, "
            f"{len(self.knowledge_base['schemas'])} schemas, "
            f"{len(self.knowledge_base['auth_flows'])} auth flows"
        )

        return self.knowledge_base

    async def _extract_endpoints(self, parsed: Dict[str, Any]) -> None:
        """Extract all API endpoints from spec."""
        spec_type = parsed.get("spec_type")

        if spec_type in [SpecType.OPENAPI, SpecType.SWAGGER]:
            paths = parsed.get("raw_spec", {}).get("paths", {})
            for path, methods in paths.items():
                for method, details in methods.items():
                    if isinstance(details, dict):
                        endpoint = {
                            "path": path,
                            "method": method.upper(),
                            "operation_id": details.get("operationId", f"{method}_{path.replace('/', '_')}"),
                            "summary": details.get("summary", ""),
                            "description": details.get("description", ""),
                            "parameters": details.get("parameters", []),
                            "request_body": details.get("requestBody", {}),
                            "responses": details.get("responses", {}),
                            "tags": details.get("tags", []),
                            "security": details.get("security", [])
                        }
                        self.knowledge_base["endpoints"].append(endpoint)

        elif spec_type == SpecType.POSTMAN:
            for item in parsed.get("endpoints", []):
                self.knowledge_base["endpoints"].append(item)

        logger.debug(f"Extracted {len(self.knowledge_base['endpoints'])} endpoints")

    async def _extract_schemas(self, parsed: Dict[str, Any]) -> None:
        """Extract all data schemas from spec."""
        spec_type = parsed.get("spec_type")

        if spec_type in [SpecType.OPENAPI, SpecType.SWAGGER]:
            components = parsed.get("raw_spec", {}).get("components", {})
            schemas = components.get("schemas", {})

            for name, schema_def in schemas.items():
                self.knowledge_base["schemas"][name] = schema_def

        elif spec_type == SpecType.GRAPHQL:
            # Extract GraphQL types as schemas
            spec_data = parsed.get("raw_spec", {})
            if "__schema" in spec_data:
                for type_def in spec_data["__schema"].get("types", []):
                    self.knowledge_base["schemas"][type_def["name"]] = type_def

        logger.debug(f"Extracted {len(self.knowledge_base['schemas'])} schemas")

    async def _extract_auth_flows(self, parsed: Dict[str, Any]) -> None:
        """Extract authentication and security requirements."""
        spec_type = parsed.get("spec_type")

        if spec_type in [SpecType.OPENAPI, SpecType.SWAGGER]:
            components = parsed.get("raw_spec", {}).get("components", {})
            security_schemes = components.get("securitySchemes", {})

            for name, scheme in security_schemes.items():
                auth_flow = {
                    "name": name,
                    "type": scheme.get("type", ""),
                    "scheme": scheme.get("scheme", ""),
                    "bearer_format": scheme.get("bearerFormat", ""),
                    "in": scheme.get("in", ""),
                    "flows": scheme.get("flows", {})
                }
                self.knowledge_base["auth_flows"].append(auth_flow)

        logger.debug(f"Extracted {len(self.knowledge_base['auth_flows'])} auth flows")

    async def _extract_ui_components(self, parsed: Dict[str, Any]) -> None:
        """Extract UI component tree from Playwright traces/HAR."""
        spec_type = parsed.get("spec_type")

        if spec_type in [SpecType.PLAYWRIGHT_HAR, SpecType.PLAYWRIGHT_TRACE]:
            entries = parsed.get("raw_spec", {}).get("log", {}).get("entries", [])

            for entry in entries:
                request = entry.get("request", {})
                ui_component = {
                    "url": request.get("url", ""),
                    "method": request.get("method", ""),
                    "headers": {h["name"]: h["value"] for h in request.get("headers", [])},
                    "query_params": request.get("queryString", []),
                    "response_status": entry.get("response", {}).get("status", 0)
                }
                self.knowledge_base["ui_components"].append(ui_component)

        logger.debug(f"Extracted {len(self.knowledge_base['ui_components'])} UI components")

    def _extract_metadata(self, parsed: Dict[str, Any]) -> None:
        """Extract spec metadata (version, title, etc.)."""
        spec_type = parsed.get("spec_type")
        raw_spec = parsed.get("raw_spec", {})

        if spec_type in [SpecType.OPENAPI, SpecType.SWAGGER]:
            info = raw_spec.get("info", {})
            self.knowledge_base["metadata"] = {
                "title": info.get("title", ""),
                "version": info.get("version", ""),
                "description": info.get("description", ""),
                "base_url": raw_spec.get("servers", [{}])[0].get("url", ""),
                "spec_type": spec_type.value
            }

    async def _persist_knowledge(self) -> None:
        """Persist knowledge base to MCP Memory for cross-session use."""
        # This would integrate with memory-keeper MCP server
        self.context.set("knowledge_base", self.knowledge_base)
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
