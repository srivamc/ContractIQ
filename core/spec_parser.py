"""
ContractIQ Spec Parser
Universal specification parser supporting multiple spec formats.
Supports: OpenAPI 3.x, Swagger 2.0, Postman Collection v2.1, AsyncAPI, GraphQL, Playwright HAR
"""
from __future__ import annotations
import json
import yaml
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from enum import Enum
from loguru import logger

from core.context_manager import ContractIQContext


class SpecType(str, Enum):
    OPENAPI = "openapi"
    SWAGGER = "swagger"
    POSTMAN = "postman"
    ASYNCAPI = "asyncapi"
    GRAPHQL = "graphql"
    PLAYWRIGHT_HAR = "playwright-har"
    PLAYWRIGHT_TRACE = "playwright-trace"
    CUSTOM_YAML = "custom-yaml"
    UNKNOWN = "unknown"


class ContractIQSpecParser:
    """
    Universal spec parser that auto-detects format and extracts:
    - API endpoints with methods, paths, parameters, request/response schemas
    - Authentication flows (OAuth2, API Key, Basic, Bearer)
    - Data schemas and models
    - UI component trees (from Playwright traces/HAR)
    """

    def __init__(self, context: ContractIQContext) -> None:
        self.context = context
        self.raw_spec: Optional[Dict] = None
        self.spec_type: SpecType = SpecType.UNKNOWN

    async def parse(self) -> None:
        """
        Parse the spec file and populate context with extracted information.
        """
        if not self.context.spec_path:
            raise ValueError("No spec path provided in context")

        spec_path = Path(self.context.spec_path)
        logger.info(f"Parsing spec: {spec_path}")

        # Load raw spec
        self.raw_spec = self._load_spec(spec_path)

        # Detect format
        self.spec_type = self._detect_spec_type(spec_path, self.raw_spec)
        self.context.spec_type = self.spec_type.value
        logger.info(f"Detected spec type: {self.spec_type.value}")

        # Parse based on type
        parsers = {
            SpecType.OPENAPI: self._parse_openapi,
            SpecType.SWAGGER: self._parse_openapi,  # Same parser, handles both
            SpecType.POSTMAN: self._parse_postman,
            SpecType.ASYNCAPI: self._parse_asyncapi,
            SpecType.GRAPHQL: self._parse_graphql,
            SpecType.PLAYWRIGHT_HAR: self._parse_playwright_har,
        }

        parser_fn = parsers.get(self.spec_type)
        if parser_fn:
            await parser_fn()
        else:
            logger.warning(f"No specialized parser for {self.spec_type}. Using generic YAML parser.")
            await self._parse_generic()

        logger.info(
            f"Spec parsing complete: {len(self.context.endpoints)} endpoints, "
            f"{len(self.context.schemas)} schemas, {len(self.context.auth_flows)} auth flows"
        )

    async def validate(self) -> Dict[str, Any]:
        """
        Validate spec structure and report issues.
        Returns a validation report.
        """
        await self.parse()
        report = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "endpoints_found": len(self.context.endpoints),
            "schemas_found": len(self.context.schemas),
            "auth_flows_found": len(self.context.auth_flows),
        }
        if not self.context.endpoints:
            report["warnings"].append("No endpoints found in spec")
        if not self.context.schemas:
            report["warnings"].append("No schemas found in spec")
        return report

    def _load_spec(self, path: Path) -> Dict[str, Any]:
        """Load spec from YAML or JSON file."""
        content = path.read_text(encoding="utf-8")
        if path.suffix in (".yaml", ".yml"):
            return yaml.safe_load(content)
        elif path.suffix == ".json":
            return json.loads(content)
        else:
            # Try YAML first, then JSON
            try:
                return yaml.safe_load(content)
            except Exception:
                return json.loads(content)

    def _detect_spec_type(self, path: Path, spec: Dict) -> SpecType:
        """Auto-detect spec format from file content."""
        if not spec:
            return SpecType.UNKNOWN

        # OpenAPI 3.x
        if "openapi" in spec and spec["openapi"].startswith("3."):
            self.context.spec_version = spec["openapi"]
            return SpecType.OPENAPI

        # Swagger 2.0
        if "swagger" in spec and spec["swagger"].startswith("2."):
            self.context.spec_version = spec["swagger"]
            return SpecType.SWAGGER

        # Postman Collection
        if "info" in spec and "_postman_id" in spec.get("info", {}):
            return SpecType.POSTMAN
        if "collection" in spec:
            return SpecType.POSTMAN

        # AsyncAPI
        if "asyncapi" in spec:
            self.context.spec_version = spec["asyncapi"]
            return SpecType.ASYNCAPI

        # GraphQL introspection
        if "__schema" in spec or ("data" in spec and "__schema" in spec.get("data", {})):
            return SpecType.GRAPHQL

        # Playwright HAR
        if path.suffix == ".har" or ("log" in spec and "entries" in spec.get("log", {})):
            return SpecType.PLAYWRIGHT_HAR

        return SpecType.CUSTOM_YAML

    async def _parse_openapi(self) -> None:
        """Parse OpenAPI 3.x or Swagger 2.0 spec."""
        spec = self.raw_spec
        base_url = self.context.target_url

        # Extract server base URL if not provided
        if not base_url:
            servers = spec.get("servers", [])
            if servers:
                base_url = servers[0].get("url", "")
                self.context.target_url = base_url

        # Extract paths/endpoints
        paths = spec.get("paths", {})
        for path, path_item in paths.items():
            http_methods = ["get", "post", "put", "patch", "delete", "head", "options"]
            for method in http_methods:
                operation = path_item.get(method)
                if not operation:
                    continue
                endpoint = {
                    "path": path,
                    "method": method.upper(),
                    "operation_id": operation.get("operationId", f"{method}_{path.replace('/', '_')}"),
                    "summary": operation.get("summary", ""),
                    "description": operation.get("description", ""),
                    "tags": operation.get("tags", []),
                    "parameters": operation.get("parameters", []),
                    "request_body": operation.get("requestBody"),
                    "responses": operation.get("responses", {}),
                    "security": operation.get("security"),
                    "deprecated": operation.get("deprecated", False),
                }
                self.context.endpoints.append(endpoint)

        # Extract components/schemas
        components = spec.get("components", spec.get("definitions", {}))
        schemas = components.get("schemas", {}) if isinstance(components, dict) else {}
        self.context.schemas.update(schemas)

        # Extract security schemes
        security_schemes = components.get("securitySchemes", {}) if isinstance(components, dict) else {}
        for name, scheme in security_schemes.items():
            self.context.auth_flows.append({
                "name": name,
                "type": scheme.get("type"),
                "scheme": scheme.get("scheme"),
                "flows": scheme.get("flows"),
                "in": scheme.get("in"),
            })

    async def _parse_postman(self) -> None:
        """Parse Postman Collection v2.1."""
        collection = self.raw_spec.get("collection", self.raw_spec)
        items = collection.get("item", [])
        self._extract_postman_items(items)

    def _extract_postman_items(self, items: List, parent_tag: str = "") -> None:
        """Recursively extract Postman requests."""
        for item in items:
            if "item" in item:  # Folder - recurse
                self._extract_postman_items(item["item"], item.get("name", parent_tag))
            elif "request" in item:
                req = item["request"]
                url = req.get("url", {})
                path = "/" + "/".join(url.get("path", []))
                endpoint = {
                    "path": path,
                    "method": req.get("method", "GET").upper(),
                    "operation_id": item.get("name", path),
                    "summary": item.get("name", ""),
                    "description": item.get("description", ""),
                    "tags": [parent_tag] if parent_tag else [],
                    "parameters": url.get("query", []),
                    "request_body": req.get("body"),
                    "responses": {},
                }
                self.context.endpoints.append(endpoint)

    async def _parse_asyncapi(self) -> None:
        """Parse AsyncAPI 2.x spec."""
        spec = self.raw_spec
        channels = spec.get("channels", {})
        for channel, channel_item in channels.items():
            for operation_type in ["subscribe", "publish"]:
                op = channel_item.get(operation_type)
                if op:
                    endpoint = {
                        "path": channel,
                        "method": operation_type.upper(),
                        "operation_id": op.get("operationId", f"{operation_type}_{channel}"),
                        "summary": op.get("summary", ""),
                        "description": op.get("description", ""),
                        "tags": op.get("tags", []),
                        "message": op.get("message"),
                    }
                    self.context.endpoints.append(endpoint)

    async def _parse_graphql(self) -> None:
        """Parse GraphQL introspection result."""
        schema = self.raw_spec.get("data", self.raw_spec).get("__schema", {})
        query_type = schema.get("queryType", {}).get("name")
        mutation_type = schema.get("mutationType", {}).get("name")
        types = {t["name"]: t for t in schema.get("types", []) if not t["name"].startswith("__")}

        for operation_type, type_name in [("query", query_type), ("mutation", mutation_type)]:
            if not type_name or type_name not in types:
                continue
            for field in types[type_name].get("fields", []):
                endpoint = {
                    "path": f"/{operation_type}/{field['name']}",
                    "method": operation_type.upper(),
                    "operation_id": field["name"],
                    "summary": field.get("description", ""),
                    "args": field.get("args", []),
                    "return_type": field.get("type"),
                }
                self.context.endpoints.append(endpoint)

    async def _parse_playwright_har(self) -> None:
        """Parse Playwright HAR trace file to extract API calls and UI interactions."""
        entries = self.raw_spec.get("log", {}).get("entries", [])
        for entry in entries:
            request = entry.get("request", {})
            response = entry.get("response", {})
            url = request.get("url", "")
            from urllib.parse import urlparse
            parsed = urlparse(url)
            endpoint = {
                "path": parsed.path,
                "method": request.get("method", "GET").upper(),
                "operation_id": f"{request.get('method', 'GET')}_{parsed.path.replace('/', '_')}",
                "summary": f"HAR captured: {url[:80]}",
                "parameters": request.get("queryString", []),
                "request_body": request.get("postData"),
                "responses": {str(response.get("status", 200)): {"description": response.get("statusText", "")}},
            }
            self.context.endpoints.append(endpoint)

    async def _parse_generic(self) -> None:
        """Generic YAML/JSON parser - extract what we can."""
        spec = self.raw_spec
        logger.warning("Using generic parser - spec format not recognized")
        # Try to extract any endpoint-like structures
        if "paths" in spec:
            await self._parse_openapi()
        elif "item" in spec or "collection" in spec:
            await self._parse_postman()
