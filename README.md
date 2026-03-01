[![Patent Pending](https://img.shields.io/badge/Patent--Pending-orange.svg)](PATENT_JUSTIFICATION.md)
# ContractIQ: Autonomous Contract-Driven Quality Engineering

> **The "CEO of Quality" for the Modern SDLC.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-brightgreen.svg)](https://python.org)
[![MCP Protocol](https://img.shields.io/badge/MCP--Enabled-purple.svg)](https://modelcontextprotocol.io)

---

## What is ContractIQ?

**ContractIQ** is a fully generic, spec-driven agentic test automation framework designed to test **UI applications** and **backend REST/GraphQL APIs** using a multi-layer AI agent architecture powered by the **Model Context Protocol (MCP)**.

Unlike traditional test automation tools tied to a proprietary platform, ContractIQ is:

- **Spec-driven** – Ingests OpenAPI 3.x, Postman collections, AsyncAPI, or custom YAML specs to auto-generate tests.
- **Platform-agnostic** – No vendor lock-in; runs on any CI/CD system (GitHub Actions, GitLab CI, Jenkins, Azure DevOps).
- **AI-first** – Uses a 3-layer multi-agent architecture to autonomously generate, execute, and heal tests.
- **Dual-mode** – Covers both UI (browser via Playwright) and Backend API (REST/GraphQL/gRPC) testing from the same framework.
- **Zero-migration** – Works alongside existing test suites; does not break existing tests.

## 🚀 Revolutionary Features

ContractIQ introduces industry-first autonomous capabilities:

- **Generative Adversarial Quality Engineering (GA-QE)**: A "Breaker vs. Fixer" multi-agent loop that evolves attack vectors to violate contracts and proactively fixes them.
- **Autonomous Compliance-as-Contract (ACaC)**: Translates regulatory text (GDPR, HIPAA, SOC2) into machine-testable quality contracts.
- **Dynamic Contract Synthesis**: Observes legacy systems to synthesize missing specifications into a baseline "Inferred Truth."
- **Shift-Right Telemetry Evolution**: Agents that re-prioritize testing strategies based on real-time production failure patterns and user behavior.
- **Zero-Knowledge Quality Proofs (ZK-QP)**: Verify contract compliance without exposing internal application logic or source code.

## 3-Layer Agent Architecture

### Layer 0: Strategic (Management)
- **Test Orchestrator Agent**: The "Project Manager" that assigns tasks to specialist agents.
- **Analysis Agent**: Provides autonomous root cause analysis and executive risk reporting.

### Layer 1: Specialist (Execution)
- **API Testing Specialist**: Autonomous REST/GraphQL validation.
- **Security Testing Specialist**: OWASP Top 10 automated scanning during functional flows.
- **Performance Testing Specialist**: Validates SLAs, latency, and throughput.
- **Code Review Specialist**: Intelligent PR analysis for testability and contract drift.

### Layer 2: Foundation (Core Skills)
- **Spec Analyzer Agent**: Ingests and enforces the "Contract-as-Truth."
- **Discovery Agent**: Identifies "Shadow APIs" not present in documentation.
- **Healing Agent**: Predictive self-healing that generates proactive refactoring PRs.

## Model Context Protocol (MCP) Integration

ContractIQ is **MCP-Native**. This allows our agents to:
- **Persist Memory**: Context travels across test sessions.
- **Connect Silos**: Functional agents share state with Security agents in real-time.
- **Deep Visibility**: Agents access server logs and infra state to verify "why" a contract failed.

## Getting Started

### 1. Installation
```bash
pip install contractiq
```

### 2. Configure MCP
Create a `.mcp.json` in your project root to enable cross-session intelligence.

### 3. Run Your First Validation
```bash
python run_contractiq.py --spec https://api.yoursite.com/openapi.json
```

## Strategic Roadmap

- **Phase 1 (Q1 2025):** Foundation – 3-Layer Architecture & MCP Support (Current).
- **Phase 2 (Q2 2025):** Zero-Touch Discovery – Autonomous spec crawling and Shadow API detection.
- **Phase 3 (Q3 2025):** GA-QE Launch – Implementing the Adversarial Breaker-Fixer loop.
- **Phase 4 (Q4 2025):** Enterprise Scale – Swarm orchestration for 1000+ parallel agents.

## License

ContractIQ is open-source software licensed under the [Apache 2.0 License](LICENSE).

---
“ContractIQ: Where the Spec meets the Speed of AI.”
