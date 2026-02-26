"""
SPECTRA Context Manager
Manages session-level and global context for the SPECTRA agent pipeline.
Provides shared state between all agents across the 3-layer architecture.
"""

from __future__ import annotations
import uuid
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path
from loguru import logger


@dataclass
class SPECTRAContext:
    """
    Primary context object shared across all SPECTRA agents.
    Encapsulates configuration, runtime state, and knowledge artifacts.
    """
    # Configuration
    spec_path: Optional[str] = None
    target_url: Optional[str] = None
    environment: str = "development"
    mode: str = "api"  # api | ui | full | analyze | validate
    parallel_workers: int = 4
    max_tests: int = 0  # 0 = unlimited
    scenarios: str = "all"
    healing_enabled: bool = True
    report_format: str = "html"
    ai_model: str = "claude-sonnet-4-5"
    output_dir: str = "./reports"
    dry_run: bool = False

    # Session tracking
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    project_name: str = "spectra-project"

    # Spec analysis results (populated by Layer 0)
    spec_type: Optional[str] = None  # openapi | postman | asyncapi | graphql | playwright-har
    spec_version: Optional[str] = None
    endpoints: List[Dict] = field(default_factory=list)
    schemas: Dict[str, Any] = field(default_factory=dict)
    auth_flows: List[Dict] = field(default_factory=list)
    ui_components: List[Dict] = field(default_factory=list)
    knowledge_base: Dict[str, Any] = field(default_factory=dict)

    # Test generation artifacts (populated by Layer 1)
    test_scenarios: List[Dict] = field(default_factory=list)
    test_cases: List[Dict] = field(default_factory=list)
    test_data: Dict[str, Any] = field(default_factory=dict)
    reusable_components: List[Dict] = field(default_factory=list)

    # Execution results (populated by execution agents)
    execution_results: List[Dict] = field(default_factory=list)
    healed_tests: List[Dict] = field(default_factory=list)
    coverage_report: Dict[str, Any] = field(default_factory=dict)
    documentation: Dict[str, Any] = field(default_factory=dict)

    # Error tracking
    errors: List[Dict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Agent state tracking
    agent_states: Dict[str, str] = field(default_factory=dict)  # agent_name -> status
    completed_phases: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize context to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize context to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)

    def save(self, path: Optional[str] = None) -> str:
        """Persist context to disk."""
        save_path = path or f"{self.output_dir}/context_{self.session_id}.json"
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w") as f:
            f.write(self.to_json())
        logger.debug(f"Context saved to {save_path}")
        return save_path

    def add_error(self, agent: str, message: str, details: Optional[Dict] = None) -> None:
        """Record an error from an agent."""
        self.errors.append({
            "agent": agent,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        })

    def add_warning(self, message: str) -> None:
        """Record a warning."""
        self.warnings.append(message)

    def set_agent_state(self, agent: str, state: str) -> None:
        """Update agent state (running | completed | failed | skipped)."""
        self.agent_states[agent] = state
        logger.debug(f"Agent '{agent}' state -> {state}")

    def mark_phase_complete(self, phase: str) -> None:
        """Mark a pipeline phase as complete."""
        if phase not in self.completed_phases:
            self.completed_phases.append(phase)

    @property
    def has_errors(self) -> bool:
        """Check if any errors occurred."""
        return len(self.errors) > 0

    @property
    def test_count(self) -> int:
        """Total number of test cases."""
        return len(self.test_cases)

    @property
    def endpoint_count(self) -> int:
        """Total number of discovered endpoints."""
        return len(self.endpoints)

    def get_summary(self) -> Dict[str, Any]:
        """Return a summary of the current context state."""
        return {
            "session_id": self.session_id,
            "project": self.project_name,
            "mode": self.mode,
            "spec_type": self.spec_type,
            "target_url": self.target_url,
            "environment": self.environment,
            "endpoints_discovered": self.endpoint_count,
            "test_scenarios": len(self.test_scenarios),
            "test_cases": self.test_count,
            "completed_phases": self.completed_phases,
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "dry_run": self.dry_run
        }


class GlobalContext:
    """
    Singleton global context for platform-wide read-only configuration.
    Loaded once at startup from environment variables and config files.
    """
    _instance: Optional[GlobalContext] = None
    _config: Dict[str, Any] = {}

    def __new__(cls) -> GlobalContext:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, config_path: Optional[str] = None) -> None:
        """Load global configuration from file and environment."""
        import os

        # Defaults
        self._config = {
            "platform": "spectra",
            "version": "1.0.0",
            "ai_provider": os.getenv("SPECTRA_AI_PROVIDER", "anthropic"),
            "ai_model": os.getenv("SPECTRA_AI_MODEL", "claude-sonnet-4-5"),
            "mcp_server_url": os.getenv("SPECTRA_MCP_URL", "http://localhost:8765"),
            "memory_db_path": os.getenv("MEMORY_DB_PATH", ".spectra/memory.db"),
            "playwright_headless": os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true",
            "log_level": os.getenv("SPECTRA_LOG_LEVEL", "INFO"),
            "max_healing_attempts": int(os.getenv("SPECTRA_MAX_HEALING_ATTEMPTS", "5")),
            "request_timeout_seconds": int(os.getenv("SPECTRA_REQUEST_TIMEOUT", "30")),
        }

        # Load from config file if provided
        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                file_config = json.load(f)
                self._config.update(file_config)

        logger.debug(f"GlobalContext loaded with {len(self._config)} settings")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self._config[key]


# Convenience accessor
def get_global_context() -> GlobalContext:
    """Get or create the singleton global context."""
    ctx = GlobalContext()
    if not ctx._config:
        ctx.load()
    return ctx
