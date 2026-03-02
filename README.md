[![Patent Pending](https://img.shields.io/badge/Patent--Pending-orange.svg)](PATENT_JUSTIFICATION.md)
# ContractIQ: Autonomous Contract-Driven Quality Engineering

> **The "CEO of Quality" for the Modern SDLC.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-brightgreen.svg)](https://python.org)
[![MCP Protocol](https://img.shields.io/badge/MCP--Enabled-purple.svg)](https://modelcontextprotocol.io)
[![Patent Status](https://img.shields.io/badge/Patent%20Pending-TEMP%2FE--1%2F27374%2F2026--CHE-orange)](PATENT_DISCLOSURE.md)

> ⚠️ **PATENT PENDING** — Indian Patent Application No. **TEMP/E-1/27374/2026-CHE** filed by Vamsee Krishna Srirama. All novel methods, architectures, and systems described herein are protected under provisional patent. Unauthorized copying, reproduction, or commercialization of the patented innovations is prohibited.

---

## What is ContractIQ?

**ContractIQ** is a fully generic, spec-driven agentic test automation framework designed to test **UI applications** and **backend REST/GraphQL APIs** using a multi-layer AI agent architecture powered by the **Model Context Protocol (MCP)**.

Unlike traditional test automation tools tied to a proprietary platform, ContractIQ is:

- **Spec-driven** - Ingests OpenAPI 3.x, Postman collections, AsyncAPI, or custom YAML specs to auto-generate tests.
- **Platform-agnostic** - No vendor lock-in; runs on any CI/CD system (GitHub Actions, GitLab CI, Jenkins, Azure DevOps).
- **AI-first** - Uses a 3-layer multi-agent architecture to autonomously generate, execute, and heal tests.
- **Dual-mode** - Covers both UI (browser via Playwright) and Backend API (REST/GraphQL/gRPC) testing from the same framework.
- **Pluggable by design** - Every major capability is a feature flag. Turn on only what you need.

---

## Core Capabilities

| Feature | Description |
|---|---|
| GA-QE | Generative AI Quality Engineering - auto-generates test cases from specs |
| ACaC | Agent-as-a-Client - AI agent acts as API consumer to catch drift |
| MASAM | Multi-Agent Self-Adaptive Mesh - agents collaborate and self-heal |
| ZK-QP | Zero-Knowledge Quality Proofs - cryptographic test integrity attestation |
| RASUI | Risk-Adaptive Smart UI - dynamic risk scoring for UI test prioritization |
| Immutable Ledger | Optional blockchain-backed quality audit trail (flag-controlled) |

---

## Feature Flags (Pluggable Architecture)

ContractIQ uses a **flag-first design** - every feature module can be toggled independently via environment variables or `core/config.yaml`.

### Configuration File: `core/config.yaml`

```yaml
feature_flags:
  agent_swarm: true             # Multi-agent parallel execution
  adversarial_qe: true          # Adversarial/chaos testing agents
  zk_proofs: true               # Zero-Knowledge cryptographic quality proofs
  compliance_acac: true         # ACaC contract drift compliance checks
  synthetic_data: true          # Synthetic data generation for tests
  immutable_ledger: false       # Blockchain ledger (opt-in, production-grade)
  rasui_risk_scoring: true      # RASUI dynamic risk-based UI prioritization
  self_healing: true            # Auto-heal broken selectors and test flows
  mcp_gateway: true             # MCP protocol agent communication
```

### Environment Variable Overrides

All flags can be overridden at runtime via environment variables:

```bash
# Enable blockchain ledger
export CIQ_IMMUTABLE_LEDGER=true

# Disable adversarial testing
export CIQ_ADVERSARIAL_QE=false

# Enable/disable full agent swarm
export CIQ_AGENT_SWARM=true
```

### Flag Groups

| Group | Flags | Purpose |
|---|---|---|
| **Core QE** | agent_swarm, synthetic_data, self_healing | Base quality engineering |
| **AI/Crypto** | zk_proofs, adversarial_qe | Advanced AI + cryptographic integrity |
| **Compliance** | compliance_acac, mcp_gateway | Contract compliance + protocol |
| **Optional/Enterprise** | immutable_ledger, rasui_risk_scoring | Enterprise add-ons |

> **Blockchain Note**: `immutable_ledger` is **OFF by default**. Set `CIQ_IMMUTABLE_LEDGER=true` to activate the immutable blockchain-backed quality audit trail. This provides tamper-proof, append-only evidence for regulated industries (finance, healthcare, defense).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   ContractIQ Framework                      │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Orchestration Agent (MCP Gateway)                 │
│    ├── Intent Parser (NLP → Test Plan)                      │
│    ├── Agent Dispatcher (MASAM mesh)                        │
│    └── Quality Ledger Writer (ZK-QP + optional Blockchain)  │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Specialist Agents                                 │
│    ├── Contract Drift Agent (ACaC)                          │
│    ├── Adversarial Agent (chaos + mutation testing)         │
│    ├── RASUI Risk Scoring Agent (UI prioritization)         │
│    └── Synthetic Data Agent (privacy-safe test data)        │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Execution Agents                                  │
│    ├── Playwright UI Executor                               │
│    ├── REST/GraphQL API Executor                            │
│    └── Self-Healing Selector Agent                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
git clone https://github.com/srivamc/ContractIQ.git
cd ContractIQ
pip install -r requirements.txt

# Run with default flags (blockchain OFF)
python demo/app.py

# Run with blockchain ledger ON
CIQ_IMMUTABLE_LEDGER=true python demo/app.py

# Run unit tests
pytest tests/ -v
```

---

## Demo Endpoints

Once running at `http://localhost:8000`:

| Endpoint | Description |
|---|---|
| `GET /health` | Health check |
| `GET /users` | List synthetic users |
| `POST /users` | Create user (contract validated) |
| `GET /orders` | List synthetic orders |
| `GET /quality-proof` | ZK quality proof (requires ZK_PROOFS flag) |
| `GET /ledger` | Immutable ledger entries (requires IMMUTABLE_LEDGER flag) |
| `GET /drift-report` | Contract drift simulation report |

---

## Patent Status

> 🔒 **PATENT PENDING** — Provisional Application No. **TEMP/E-1/27374/2026-CHE**
> Filed: January 2026 | Indian Patent Office (Chennai) | Applicant: Vamsee Krishna Srirama

ContractIQ's core innovations are covered under a **Provisional Patent Application** filed with the **Indian Patent Office**. The patent is currently **under review**. All novel architectures, methods, and systems in this repository are protected.

**Patent Application Details:**
- **Application Number:** TEMP/E-1/27374/2026-CHE
- **Filing Office:** Indian Patent Office, Chennai
- **Applicant:** Vamsee Krishna Srirama
- **Status:** Provisional Patent Pending (Under Review)
- **Filing Year:** 2026

**Key patentable claims include:**
1. Multi-layer agentic quality orchestration via MCP protocol
2. Zero-Knowledge Quality Proofs (ZK-QP) for test integrity attestation
3. Adversarial Agent Swarm for autonomous chaos quality engineering
4. RASUI: Risk-Adaptive Scoring for UI test prioritization
5. Pluggable feature-flag architecture for modular quality frameworks
6. Optional immutable blockchain audit trail for regulated industries

> ⚠️ While this software is open source under Apache 2.0, the **novel methods and systems** described herein are protected under the above provisional patent application. You are free to use, study, and contribute to the codebase, but commercializing the patented innovations without a license is prohibited.

See [PATENT_DISCLOSURE.md](PATENT_DISCLOSURE.md) and [PATENT_SPECIFICATION.md](PATENT_SPECIFICATION.md) for full details.

---

## Author

**Vamsee Krishna Srirama**
Senior Director of Software Engineering | AI Quality Engineering Innovator

---

*ContractIQ - Making quality autonomous, provable, and pluggable.*
