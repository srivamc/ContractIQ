"""
ACAC Agent - Agent-as-a-Client Contract Drift Detection
Patent Pending: TEMP/E-1/27374/2026-CHE
Copyright (c) 2026 Vamsee Krishna Srirama

Patented innovation: LLM-powered semantic contract drift detection beyond schema validation.
"""
from __future__ import annotations
import json
import os
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    logger.warning("openai not installed. LLM semantic analysis disabled.")


@dataclass
class ContractVersion:
    version_id: str
    timestamp: str
    spec_hash: str
    openapi_spec: Dict[str, Any]


@dataclass
class DriftDetection:
    field_path: str
    change_type: str  # added, removed, type_changed, enum_changed
    old_value: Any
    new_value: Any
    breaking: bool
    risk_score: int  # 0-100
    description: str


@dataclass
class DriftReport:
    session_id: str
    baseline_version: str
    current_version: str
    total_drifts: int
    breaking_drifts: int
    non_breaking_drifts: int
    overall_risk_score: int
    detections: List[DriftDetection]
    timestamp_utc: str
    llm_analysis: Optional[str] = None
    patent_ref: str = "TEMP/E-1/27374/2026-CHE"

    def to_dict(self) -> Dict:
        return asdict(self)


class ACACAgent:
    """
    PATENTED: Agent-as-a-Client (ACaC) for Contract Drift Detection
    Application: TEMP/E-1/27374/2026-CHE

    Uses LLM to detect semantic contract drift beyond simple schema validation:
    - Breaking vs non-breaking changes
    - Semantic meaning analysis
    - Risk scoring for each drift
    - Context-aware recommendations
    """

    def __init__(self, llm_provider: str = "openai", api_key: Optional[str] = None):
        self.llm_provider = llm_provider
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._contract_store: Dict[str, ContractVersion] = {}
        if llm_provider == "openai" and HAS_OPENAI and self._api_key:
            openai.api_key = self._api_key
            self._llm_enabled = True
        else:
            self._llm_enabled = False
            logger.warning("LLM not configured. Semantic analysis limited.")

    def _hash_spec(self, spec: Dict[str, Any]) -> str:
        """Generate SHA-256 hash of OpenAPI spec for versioning."""
        canonical = json.dumps(spec, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def store_baseline(self, spec: Dict[str, Any], version_id: Optional[str] = None) -> str:
        """Store a baseline contract version."""
        vid = version_id or f"v_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        contract = ContractVersion(
            version_id=vid,
            timestamp=datetime.now(timezone.utc).isoformat(),
            spec_hash=self._hash_spec(spec),
            openapi_spec=spec
        )
        self._contract_store[vid] = contract
        logger.info(f"Stored baseline contract: {vid} | hash={contract.spec_hash}")
        return vid

    def _detect_schema_drifts(self, baseline: Dict, current: Dict, path="") -> List[DriftDetection]:
        """Rule-based schema drift detection (non-LLM fallback)."""
        drifts = []
        # Detect added fields
        for key in current.keys():
            if key not in baseline:
                drifts.append(DriftDetection(
                    field_path=f"{path}.{key}",
                    change_type="added",
                    old_value=None,
                    new_value=current[key],
                    breaking=False,
                    risk_score=20,
                    description=f"New field added: {key}"
                ))
        # Detect removed fields
        for key in baseline.keys():
            if key not in current:
                drifts.append(DriftDetection(
                    field_path=f"{path}.{key}",
                    change_type="removed",
                    old_value=baseline[key],
                    new_value=None,
                    breaking=True,
                    risk_score=90,
                    description=f"Field removed (BREAKING): {key}"
                ))
        # Detect type changes
        for key in baseline.keys():
            if key in current:
                if isinstance(baseline[key], dict) and isinstance(current[key], dict):
                    drifts.extend(self._detect_schema_drifts(baseline[key], current[key], f"{path}.{key}"))
                elif type(baseline[key]) != type(current[key]):
                    drifts.append(DriftDetection(
                        field_path=f"{path}.{key}",
                        change_type="type_changed",
                        old_value=type(baseline[key]).__name__,
                        new_value=type(current[key]).__name__,
                        breaking=True,
                        risk_score=85,
                        description=f"Type changed (BREAKING): {key}"
                    ))
        return drifts

    def _llm_semantic_analysis(self, baseline_spec: Dict, current_spec: Dict, schema_drifts: List[DriftDetection]) -> Tuple[List[DriftDetection], str]:
        """PATENTED: LLM-powered semantic drift analysis."""
        if not self._llm_enabled or not schema_drifts:
            return schema_drifts, "LLM analysis not available"

        drift_summary = "\n".join([f"- {d.change_type}: {d.field_path} (risk={d.risk_score})" for d in schema_drifts])
        prompt = f"""You are an API contract analysis expert. Analyze these detected schema drifts between baseline and current OpenAPI specs:

Baseline spec (summary): {len(baseline_spec.get('paths', {}))} endpoints
Current spec (summary): {len(current_spec.get('paths', {}))} endpoints

Detected drifts:
{drift_summary}

For each drift, assess:
1. Is it truly breaking or can consumers adapt?
2. What's the business impact (low/medium/high)?
3. Risk score justification (0-100)
4. Recommended action

Return JSON array:
[
  {{
    "field_path": "...",
    "breaking": true/false,
    "risk_score": 0-100,
    "impact": "low/medium/high",
    "recommendation": "..."
  }}
]

Return ONLY valid JSON."""

        try:
            if HAS_OPENAI:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=1500
                )
                content = response.choices[0].message.content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                llm_analysis = json.loads(content.strip())
                # Update drifts with LLM insights
                for i, drift in enumerate(schema_drifts):
                    for analysis in llm_analysis:
                        if analysis["field_path"] == drift.field_path:
                            drift.breaking = analysis["breaking"]
                            drift.risk_score = analysis["risk_score"]
                            drift.description += f" | Impact: {analysis['impact']} | {analysis['recommendation']}"
                logger.success("LLM semantic analysis complete")
                return schema_drifts, "LLM-enhanced analysis"
        except Exception as e:
            logger.error(f"LLM semantic analysis failed: {e}")
        return schema_drifts, "Fallback to rule-based analysis"

    def detect_drift(self, baseline_version_id: str, current_spec: Dict[str, Any]) -> DriftReport:
        """PATENTED: Detect contract drift between baseline and current spec."""
        if baseline_version_id not in self._contract_store:
            raise ValueError(f"Baseline version {baseline_version_id} not found")

        baseline = self._contract_store[baseline_version_id]
        session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        logger.info(f"Detecting drift | baseline={baseline_version_id} | session={session_id}")

        # Step 1: Rule-based schema drift detection
        baseline_paths = baseline.openapi_spec.get("paths", {})
        current_paths = current_spec.get("paths", {})
        drifts = self._detect_schema_drifts(baseline_paths, current_paths, "paths")

        # Step 2: LLM semantic analysis
        drifts, llm_summary = self._llm_semantic_analysis(baseline.openapi_spec, current_spec, drifts)

        # Step 3: Generate report
        breaking = sum(1 for d in drifts if d.breaking)
        non_breaking = len(drifts) - breaking
        overall_risk = int(sum(d.risk_score for d in drifts) / len(drifts)) if drifts else 0

        report = DriftReport(
            session_id=session_id,
            baseline_version=baseline_version_id,
            current_version=self._hash_spec(current_spec),
            total_drifts=len(drifts),
            breaking_drifts=breaking,
            non_breaking_drifts=non_breaking,
            overall_risk_score=overall_risk,
            detections=drifts,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            llm_analysis=llm_summary
        )
        logger.success(f"Drift detection complete | total={len(drifts)} | breaking={breaking} | risk={overall_risk}")
        return report

    def continuous_monitoring(self, baseline_version_id: str, live_api_spec_url: str) -> DriftReport:
        """Continuously monitor live API for contract drift."""
        import requests
        try:
            response = requests.get(live_api_spec_url, timeout=10)
            response.raise_for_status()
            current_spec = response.json()
            return self.detect_drift(baseline_version_id, current_spec)
        except Exception as e:
            logger.error(f"Failed to fetch live spec: {e}")
            raise


def detect_contract_drift(baseline_spec: Dict, current_spec: Dict, use_llm: bool = True) -> DriftReport:
    """Convenience function for one-shot drift detection."""
    agent = ACACAgent() if use_llm else ACACAgent(llm_provider="none")
    baseline_id = agent.store_baseline(baseline_spec, "baseline_v1")
    return agent.detect_drift(baseline_id, current_spec)
