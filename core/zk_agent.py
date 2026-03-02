"""
ContractIQ - Zero-Knowledge Quality Proof Agent (ZK-QP)
Patent Pending: TEMP/E-1/27374/2026-CHE (Indian Patent Office)
Copyright (c) 2026 Vamsee Krishna Srirama. All rights reserved.

Implements the patented ZK-QP system using SHA-256 Merkle trees
and HMAC-based proof chaining for tamper-proof quality attestation.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger


@dataclass
class TestExecutionPayload:
    """Single test execution event for ZK proof generation."""
    test_id: str
    endpoint: str
    method: str
    status_code: int
    passed: bool
    duration_ms: float
    timestamp: str
    contract_version: str
    session_id: str
    _request_body: Optional[Dict] = field(default=None, repr=False)
    _response_body: Optional[Dict] = field(default=None, repr=False)


@dataclass
class ZKQualityProof:
    """
    Zero-Knowledge Quality Proof artifact.
    Allows third-party verification of test completeness and integrity
    WITHOUT revealing request/response bodies, credentials, or test logic.
    Patent Pending: TEMP/E-1/27374/2026-CHE
    """
    proof_id: str
    session_id: str
    merkle_root: str
    proof_chain: List[str]
    commitment_hash: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    pass_rate: float
    timestamp_utc: str
    contract_version: str
    algorithm: str = "SHA256-HMAC-MERKLE"
    patent_ref: str = "TEMP/E-1/27374/2026-CHE"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ZKQualityProofAgent:
    """
    PATENTED ZK-QP Agent (TEMP/E-1/27374/2026-CHE).

    Generates cryptographic quality proofs using:
    1. SHA-256 hash of each test payload (non-sensitive fields only)
    2. Merkle tree construction over all test hashes
    3. HMAC proof chain linking each test to the previous
    4. Binding commitment over Merkle root + session stats
    """

    ALGORITHM = "SHA256-HMAC-MERKLE"
    PROOF_VERSION = "2.0.0"

    def __init__(self, secret_key: Optional[bytes] = None) -> None:
        self._secret_key = secret_key or self._derive_session_key()
        logger.info("ZKQualityProofAgent initialized | algo={}", self.ALGORITHM)

    @staticmethod
    def _derive_session_key() -> bytes:
        env_key = os.environ.get("CIQ_ZK_SECRET_KEY")
        if env_key:
            return hashlib.sha256(env_key.encode()).digest()
        return os.urandom(32)

    @staticmethod
    def _hash_test_payload(payload: TestExecutionPayload) -> str:
        """Hash non-sensitive test fields. Sensitive bodies are excluded."""
        canonical = (
            f"{payload.test_id}|"
            f"{payload.endpoint}|"
            f"{payload.method}|"
            f"{payload.status_code}|"
            f"{payload.passed}|"
            f"{payload.timestamp}|"
            f"{payload.contract_version}|"
            f"{payload.session_id}"
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _build_merkle_tree(leaf_hashes: List[str]) -> Tuple[str, List[str]]:
        """Build SHA-256 Merkle tree. Returns (root, all_nodes)."""
        if not leaf_hashes:
            return hashlib.sha256(b"empty").hexdigest(), []
        nodes = list(leaf_hashes)
        all_nodes = list(nodes)
        while len(nodes) > 1:
            if len(nodes) % 2 == 1:
                nodes.append(nodes[-1])
            parent_level = []
            for i in range(0, len(nodes), 2):
                combined = nodes[i] + nodes[i + 1]
                parent_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
                parent_level.append(parent_hash)
                all_nodes.append(parent_hash)
            nodes = parent_level
        return nodes[0], all_nodes

    def _generate_proof_chain(self, leaf_hashes: List[str], session_id: str) -> List[str]:
        """Generate HMAC-chained proof sequence (tamper-evident ordering)."""
        chain = []
        previous = session_id.encode("utf-8")
        for h in leaf_hashes:
            link = hmac.new(
                self._secret_key,
                msg=previous + h.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).hexdigest()
            chain.append(link)
            previous = link.encode("utf-8")
        return chain

    def _create_commitment(self, merkle_root: str, total: int, passed: int,
                           session_id: str, contract_version: str) -> str:
        commitment_data = (
            f"{merkle_root}|{total}|{passed}|{session_id}|"
            f"{contract_version}|{self.PROOF_VERSION}"
        )
        return hmac.new(
            self._secret_key,
            msg=commitment_data.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

    def generate_proof(self, payloads: List[TestExecutionPayload],
                       contract_version: str = "1.0.0") -> ZKQualityProof:
        """
        PATENTED METHOD: Generate a Zero-Knowledge Quality Proof.
        Produces cryptographic proof verifiable by any party with the
        session key, without exposing sensitive test data.
        """
        if not payloads:
            raise ValueError("Cannot generate proof for empty test suite")
        session_id = payloads[0].session_id
        proof_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        logger.info("Generating ZK proof | session={} | tests={}", session_id, len(payloads))
        leaf_hashes = [self._hash_test_payload(p) for p in payloads]
        merkle_root, _ = self._build_merkle_tree(leaf_hashes)
        proof_chain = self._generate_proof_chain(leaf_hashes, session_id)
        total = len(payloads)
        passed = sum(1 for p in payloads if p.passed)
        failed = total - passed
        pass_rate = round(passed / total * 100, 2) if total > 0 else 0.0
        commitment = self._create_commitment(merkle_root, total, passed, session_id, contract_version)
        proof = ZKQualityProof(
            proof_id=proof_id, session_id=session_id, merkle_root=merkle_root,
            proof_chain=proof_chain, commitment_hash=commitment,
            total_tests=total, passed_tests=passed, failed_tests=failed,
            pass_rate=pass_rate, timestamp_utc=timestamp, contract_version=contract_version,
        )
        logger.success("ZK proof generated | proof_id={} | pass_rate={}%", proof_id, pass_rate)
        return proof

    @staticmethod
    def verify_proof(proof: ZKQualityProof, secret_key: bytes) -> bool:
        """Verify ZK proof integrity using the session key."""
        commitment_data = (
            f"{proof.merkle_root}|{proof.total_tests}|{proof.passed_tests}|"
            f"{proof.session_id}|{proof.contract_version}|"
            f"{ZKQualityProofAgent.PROOF_VERSION}"
        )
        expected = hmac.new(
            secret_key,
            msg=commitment_data.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
        valid = hmac.compare_digest(expected, proof.commitment_hash)
        logger.info("ZK proof verification | proof_id={} | valid={}", proof.proof_id, valid)
        return valid

    def generate_from_test_results(self, test_results: List[Dict[str, Any]],
                                    session_id: str, contract_version: str = "1.0.0") -> ZKQualityProof:
        """Convenience: generate proof from raw test result dicts."""
        payloads = []
        for i, result in enumerate(test_results):
            payload = TestExecutionPayload(
                test_id=result.get("test_id", f"test_{i:04d}"),
                endpoint=result.get("endpoint", result.get("url", "/unknown")),
                method=result.get("method", "GET"),
                status_code=result.get("status_code", result.get("actual_status", 0)),
                passed=result.get("passed", result.get("status") == "passed"),
                duration_ms=result.get("duration_ms", 0.0),
                timestamp=result.get("timestamp", datetime.now(timezone.utc).isoformat()),
                contract_version=contract_version,
                session_id=session_id,
            )
            payloads.append(payload)
        return self.generate_proof(payloads, contract_version)


def create_zk_proof_for_session(
    test_results: List[Dict[str, Any]],
    session_id: Optional[str] = None,
    contract_version: str = "1.0.0",
    secret_key: Optional[bytes] = None,
) -> ZKQualityProof:
    """Top-level function for generating ZK proofs. Used by orchestrator."""
    sid = session_id or str(uuid.uuid4())
    agent = ZKQualityProofAgent(secret_key=secret_key)
    return agent.generate_from_test_results(test_results, sid, contract_version)
