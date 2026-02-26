#!/usr/bin/env python3
"""
SPECTRA - Spec-driven, Platform-agnostic, Extensible, Cloud-ready Test Runner with Agentic AI
Main entry point for the SPECTRA agentic QE framework.

Usage:
    python run_spectra.py --mode api --spec ./specs/sample-openapi.yaml
    python run_spectra.py --mode ui --target https://myapp.example.com --spec ./specs/sample-ui-spec.yaml
    python run_spectra.py --mode full --spec ./specs/sample-openapi.yaml --target https://myapp.example.com
"""

import sys
import os
import asyncio
import argparse
from pathlib import Path
from typing import Optional
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

console = Console()


SPECTRA_BANNER = """
 ____  ____  _____ ____ _____ ____      _    
/ ___||  _ \| ____/ ___|_   _|  _ \    / \   
\___ \| |_) |  _|| |     | | | |_) |  / _ \  
 ___) |  __/| |__| |___  | | |  _ <  / ___ \ 
|____/|_|   |_____\____| |_| |_| \_\/_/   \_\
                                               
Spec-driven | Platform-agnostic | Extensible | Cloud-ready | Agentic AI
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="SPECTRA - Agentic QE Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run API tests from OpenAPI spec
  python run_spectra.py --mode api --spec ./specs/openapi.yaml --target https://api.example.com

  # Run UI tests with Playwright
  python run_spectra.py --mode ui --target https://myapp.example.com --spec ./specs/ui-spec.yaml

  # Full suite (API + UI)
  python run_spectra.py --mode full --spec ./specs/openapi.yaml --target https://myapp.example.com

  # Analyze spec only (no execution)
  python run_spectra.py --mode analyze --spec ./specs/openapi.yaml

  # Validate generated tests
  python run_spectra.py --mode validate --spec ./specs/openapi.yaml
        """
    )

    parser.add_argument(
        "--mode",
        choices=["api", "ui", "full", "analyze", "validate", "report"],
        required=True,
        help="Execution mode: api | ui | full | analyze | validate | report"
    )
    parser.add_argument(
        "--spec",
        type=Path,
        help="Path to spec file (OpenAPI YAML/JSON, Postman collection, AsyncAPI, GraphQL introspection)"
    )
    parser.add_argument(
        "--target",
        type=str,
        help="Target base URL for tests (e.g. https://api.example.com)"
    )
    parser.add_argument(
        "--env",
        default="development",
        choices=["development", "staging", "production"],
        help="Target environment"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./reports"),
        help="Output directory for reports"
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=4,
        help="Number of parallel worker threads (default: 4)"
    )
    parser.add_argument(
        "--max-tests",
        type=int,
        default=0,
        help="Maximum number of tests to generate (0 = unlimited)"
    )
    parser.add_argument(
        "--scenarios",
        type=str,
        default="all",
        help="Comma-separated list of test scenarios to run (or 'all')"
    )
    parser.add_argument(
        "--heal",
        action="store_true",
        default=True,
        help="Enable self-healing mode (default: True)"
    )
    parser.add_argument(
        "--no-heal",
        action="store_false",
        dest="heal",
        help="Disable self-healing mode"
    )
    parser.add_argument(
        "--report-format",
        choices=["allure", "html", "json", "all"],
        default="html",
        help="Report format (default: html)"
    )
    parser.add_argument(
        "--ai-model",
        default="claude-sonnet-4-5",
        help="AI model for agent orchestration (default: claude-sonnet-4-5)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze and generate tests without executing them"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    """Validate argument combinations."""
    if args.mode in ["api", "ui", "full", "analyze"] and not args.spec:
        # Check for spec in environment
        env_spec = os.environ.get("SPECTRA_SPEC_PATH")
        if not env_spec:
            console.print("[red]ERROR: --spec is required for mode '{args.mode}' or set SPECTRA_SPEC_PATH env var[/red]")
            sys.exit(1)
        args.spec = Path(env_spec)

    if args.spec and not args.spec.exists():
        console.print(f"[red]ERROR: Spec file not found: {args.spec}[/red]")
        sys.exit(1)

    if args.mode in ["api", "ui", "full"] and not args.target:
        env_target = os.environ.get("SPECTRA_TARGET_URL")
        if not env_target:
            console.print("[yellow]WARNING: --target URL not specified. Tests may use spec-defined server URLs.[/yellow]")
        else:
            args.target = env_target


async def run_spectra(args: argparse.Namespace) -> int:
    """
    Main SPECTRA workflow runner.
    Orchestrates the 3-layer agent pipeline.
    """
    from core.orchestrator import SPECTRAOrchestrator
    from core.context_manager import SPECTRAContext

    # Initialize context
    context = SPECTRAContext(
        spec_path=str(args.spec) if args.spec else None,
        target_url=args.target,
        environment=args.env,
        mode=args.mode,
        parallel_workers=args.parallel,
        max_tests=args.max_tests,
        scenarios=args.scenarios,
        healing_enabled=args.heal,
        report_format=args.report_format,
        ai_model=args.ai_model,
        output_dir=str(args.output),
        dry_run=args.dry_run
    )

    # Initialize orchestrator
    orchestrator = SPECTRAOrchestrator(context)

    console.print(Panel(
        f"[bold green]Mode:[/bold green] {args.mode.upper()}\n"
        f"[bold green]Spec:[/bold green] {args.spec or 'N/A'}\n"
        f"[bold green]Target:[/bold green] {args.target or 'From spec'}\n"
        f"[bold green]Environment:[/bold green] {args.env}\n"
        f"[bold green]AI Model:[/bold green] {args.ai_model}\n"
        f"[bold green]Parallel Workers:[/bold green] {args.parallel}\n"
        f"[bold green]Self-Healing:[/bold green] {'Enabled' if args.heal else 'Disabled'}",
        title="[bold cyan]SPECTRA Configuration[/bold cyan]",
        border_style="cyan"
    ))

    try:
        exit_code = await orchestrator.run()
        return exit_code
    except KeyboardInterrupt:
        console.print("\n[yellow]Execution interrupted by user.[/yellow]")
        return 130
    except Exception as e:
        console.print(f"[red]FATAL ERROR: {e}[/red]")
        logger.exception("Fatal error during SPECTRA execution")
        return 1


def main() -> None:
    """Entry point."""
    # Print banner
    console.print(Text(SPECTRA_BANNER, style="bold cyan"))

    # Parse and validate args
    args = parse_args()
    validate_args(args)

    # Configure logging
    log_level = "DEBUG" if args.verbose else "INFO"
    logger.remove()
    logger.add(sys.stderr, level=log_level, format="{time:HH:mm:ss} | {level} | {message}")
    logger.add(
        "logs/spectra_{time:YYYYMMDD}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG"
    )

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

    # Run the async workflow
    exit_code = asyncio.run(run_spectra(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
