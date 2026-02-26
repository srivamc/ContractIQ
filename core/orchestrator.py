"""
ContractIQ Orchestrator
Main workflow controller for the 3-layer agentic pipeline.
Coordinates all agents from spec analysis through execution and reporting.
"""
from __future__ import annotations
import asyncio
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.table import Table
from loguru import logger

from core.context_manager import ContractIQContext

console = Console()

class ContractIQOrchestrator:
    """
    Main ContractIQ pipeline orchestrator.
    Executes the 3-layer agent workflow:
        Layer 0: Knowledge creation (SpecAnalyzerAgent)
        Layer 1: Core orchestration (9 sequential agents)
        Layer 2: Domain specialists (8 parallel agents)
    """

    def __init__(self, context: ContractIQContext) -> None:
        self.context = context
        self._phase_handlers = {
            "api": self._run_api_pipeline,
            "ui": self._run_ui_pipeline,
            "full": self._run_full_pipeline,
            "analyze": self._run_analyze_only,
            "validate": self._run_validate_only,
            "report": self._run_report_only,
        }

    async def run(self) -> int:
        """
        Execute the ContractIQ workflow for the configured mode.
        Returns exit code: 0 = success, 1 = failure, 2 = partial failure.
        """
        logger.info(f"Starting ContractIQ orchestrator | session={self.context.session_id} | mode={self.context.mode}")

        handler = self._phase_handlers.get(self.context.mode)
        if not handler:
            logger.error(f"Unknown mode: {self.context.mode}")
            return 1

        try:
            exit_code = await handler()
            self._print_summary(exit_code)
            self.context.save()
            return exit_code
        except Exception as e:
            logger.exception(f"Orchestrator failed: {e}")
            self.context.add_error("orchestrator", str(e))
            return 1

    # -------------------------------------------------------------------------
    # Pipeline variants
    # -------------------------------------------------------------------------

    async def _run_api_pipeline(self) -> int:
        """Full API testing pipeline: analyze -> generate -> validate -> execute -> report."""
        steps = [
            ("Layer 0: Spec Analysis", self._run_layer0),
            ("Layer 1: Scenario Generation", self._run_scenario_generation),
            ("Layer 1: Test Case Design", self._run_test_case_design),
            ("Layer 1: Test Data Generation", self._run_test_data_generation),
            ("Layer 2: API Specialists (parallel)", self._run_api_specialists),
        ]
        if not self.context.dry_run:
            steps += [
                ("Layer 1: Execution", self._run_execution),
                ("Layer 1: Healing", self._run_healing),
                ("Layer 1: Analysis", self._run_analysis),
                ("Layer 1: Documentation", self._run_documentation),
                ("Layer 1: Optimization", self._run_optimization),
                ("Reporting", self._run_reporting),
            ]
        return await self._execute_steps(steps)

    async def _run_ui_pipeline(self) -> int:
        """Full UI testing pipeline: analyze -> generate -> validate -> execute -> report."""
        steps = [
            ("Layer 0: Spec Analysis", self._run_layer0),
            ("Layer 1: Scenario Generation", self._run_scenario_generation),
            ("Layer 1: Test Case Design", self._run_test_case_design),
            ("Layer 2: UI Specialists (parallel)", self._run_ui_specialists),
        ]
        if not self.context.dry_run:
            steps += [
                ("Layer 1: Execution", self._run_execution),
                ("Layer 1: Healing", self._run_healing),
                ("Layer 1: Analysis", self._run_analysis),
                ("Reporting", self._run_reporting),
            ]
        return await self._execute_steps(steps)

    async def _run_full_pipeline(self) -> int:
        """Combined API + UI pipeline with all domain specialists."""
        steps = [
            ("Layer 0: Spec Analysis", self._run_layer0),
            ("Layer 1: Scenario Generation", self._run_scenario_generation),
            ("Layer 1: Test Case Design", self._run_test_case_design),
            ("Layer 1: Test Data Generation", self._run_test_data_generation),
            ("Layer 2: All Specialists (parallel)", self._run_all_specialists),
        ]
        if not self.context.dry_run:
            steps += [
                ("Layer 1: Execution", self._run_execution),
                ("Layer 1: Healing", self._run_healing),
                ("Layer 1: Analysis", self._run_analysis),
                ("Layer 1: Documentation", self._run_documentation),
                ("Layer 1: Optimization", self._run_optimization),
                ("Reporting", self._run_reporting),
            ]
        return await self._execute_steps(steps)

    async def _run_analyze_only(self) -> int:
        """Spec analysis only - no test generation or execution."""
        return await self._execute_steps([
            ("Layer 0: Spec Analysis", self._run_layer0),
        ])

    async def _run_validate_only(self) -> int:
        """Validate existing test files - no execution."""
        return await self._execute_steps([
            ("Layer 0: Spec Analysis", self._run_layer0),
            ("Validation", self._run_validation),
        ])

    async def _run_report_only(self) -> int:
        """Generate reports from existing results."""
        return await self._execute_steps([
            ("Reporting", self._run_reporting),
        ])

    # -------------------------------------------------------------------------
    # Step executors
    # -------------------------------------------------------------------------

    async def _execute_steps(self, steps: List[tuple]) -> int:
        """Execute a sequence of pipeline steps with progress display."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=False
        ) as progress:
            for step_name, step_func in steps:
                task = progress.add_task(f"[cyan]{step_name}[/cyan]", total=None)
                try:
                    await step_func()
                    progress.update(task, description=f"[green]\u2713 {step_name}[/green]")
                    self.context.mark_phase_complete(step_name)
                except Exception as e:
                    progress.update(task, description=f"[red]\u2717 {step_name}: {e}[/red]")
                    self.context.add_error(step_name, str(e))
                    logger.error(f"Step failed: {step_name} - {e}")
                    if self._is_critical_step(step_name):
                        return 1
        return 0 if not self.context.has_errors else 2

    def _is_critical_step(self, step_name: str) -> bool:
        """Determine if failure of this step should halt the pipeline."""
        critical = ["Layer 0", "Spec Analysis"]
        return any(c in step_name for c in critical)

    # -------------------------------------------------------------------------
    # Individual step implementations
    # -------------------------------------------------------------------------

    async def _run_layer0(self) -> None:
        """Run the SpecAnalyzerAgent to build the knowledge base."""
        from agents.layer0.spec_analyzer_agent import SpecAnalyzerAgent
        agent = SpecAnalyzerAgent(self.context)
        await agent.run()

    async def _run_scenario_generation(self) -> None:
        from agents.layer1.scenario_generator_agent import ScenarioGeneratorAgent
        agent = ScenarioGeneratorAgent(self.context)
        await agent.run()

    async def _run_test_case_design(self) -> None:
        from agents.layer1.test_case_designer_agent import TestCaseDesignerAgent
        agent = TestCaseDesignerAgent(self.context)
        await agent.run()

    async def _run_test_data_generation(self) -> None:
        from agents.layer1.test_data_generator_agent import TestDataGeneratorAgent
        agent = TestDataGeneratorAgent(self.context)
        await agent.run()

    async def _run_execution(self) -> None:
        from agents.layer1.execution_agent import ExecutionAgent
        agent = ExecutionAgent(self.context)
        await agent.run()

    async def _run_healing(self) -> None:
        if self.context.healing_enabled:
            from agents.layer1.healing_agent import HealingAgent
            agent = HealingAgent(self.context)
            await agent.run()

    async def _run_analysis(self) -> None:
        from agents.layer1.analysis_agent import AnalysisAgent
        agent = AnalysisAgent(self.context)
        await agent.run()

    async def _run_documentation(self) -> None:
        from agents.layer1.documentation_agent import DocumentationAgent
        agent = DocumentationAgent(self.context)
        await agent.run()

    async def _run_optimization(self) -> None:
        from agents.layer1.optimization_agent import OptimizationAgent
        agent = OptimizationAgent(self.context)
        await agent.run()

    async def _run_api_specialists(self) -> None:
        """Run API-relevant Layer 2 specialists in parallel."""
        from agents.layer2.api_testing_specialist import APITestingSpecialist
        from agents.layer2.security_testing_specialist import SecurityTestingSpecialist
        from agents.layer2.performance_testing_specialist import PerformanceTestingSpecialist
        from agents.layer2.code_review_specialist import CodeReviewSpecialist
        specialists = [
            APITestingSpecialist(self.context),
            SecurityTestingSpecialist(self.context),
            PerformanceTestingSpecialist(self.context),
            CodeReviewSpecialist(self.context),
        ]
        await asyncio.gather(*[s.run() for s in specialists], return_exceptions=True)

    async def _run_ui_specialists(self) -> None:
        """Run UI-relevant Layer 2 specialists in parallel."""
        from agents.layer2.api_testing_specialist import APITestingSpecialist
        specialists = [
            APITestingSpecialist(self.context),
        ]
        await asyncio.gather(*[s.run() for s in specialists], return_exceptions=True)

    async def _run_all_specialists(self) -> None:
        """Run all Layer 2 specialists in parallel."""
        await asyncio.gather(
            self._run_api_specialists(),
            self._run_ui_specialists(),
            return_exceptions=True
        )

    async def _run_validation(self) -> None:
        """Validate existing test assets."""
        from core.spec_parser import SpecParser
        parser = SpecParser(self.context)
        await parser.validate()

    async def _run_reporting(self) -> None:
        """Generate test reports."""
        from core.reporter import ContractIQReporter
        reporter = ContractIQReporter(self.context.output_dir)
        await reporter.generate()

    # -------------------------------------------------------------------------
    # Summary display
    # -------------------------------------------------------------------------

    def _print_summary(self, exit_code: int) -> None:
        """Print execution summary to console."""
        summary = self.context.get_summary()
        table = Table(title="ContractIQ Execution Summary", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="dim", width=30)
        table.add_column("Value", justify="right")

        table.add_row("Session ID", summary["session_id"][:8] + "...")
        table.add_row("Mode", summary["mode"].upper())
        table.add_row("Spec Type", summary.get("spec_type") or "N/A")
        table.add_row("Endpoints Discovered", str(summary["endpoints_discovered"]))
        table.add_row("Test Scenarios", str(summary["test_scenarios"]))
        table.add_row("Test Cases Generated", str(summary["test_cases"]))
        table.add_row("Phases Completed", str(len(summary["completed_phases"])))
        table.add_row("Errors", f"[red]{summary['errors']}[/red]" if summary["errors"] else "[green]0[/green]")
        table.add_row("Warnings", str(summary["warnings"]))

        status_map = {0: "[bold green]SUCCESS[/bold green]", 1: "[bold red]FAILED[/bold red]", 2: "[bold yellow]PARTIAL[/bold yellow]"}
        table.add_row("Exit Status", status_map.get(exit_code, str(exit_code)))
        console.print(table)
