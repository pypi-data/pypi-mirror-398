#!/usr/bin/env python3
"""
Unified CLI for Claude Agent Framework.

Provides a single entry point for all architectures and observability tools.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import webbrowser
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Import architectures to trigger registration
import claude_agent_framework.architectures  # noqa: F401
from claude_agent_framework.core.registry import get_architecture_info
from claude_agent_framework.core.session import AgentSession


def print_architectures() -> None:
    """Print available architectures."""
    print("\nAvailable Architectures:")
    print("=" * 50)

    for name, info in get_architecture_info().items():
        print(f"\n  {name}")
        print(f"    {info['description']}")

    print()


async def run_architecture(
    arch_name: str,
    query: str | None = None,
    model: str = "haiku",
    interactive: bool = False,
    verbose: bool = False,
    business_template: str | None = None,
    template_vars: dict | None = None,
) -> None:
    """
    Run the specified architecture using create_session() internally.

    Args:
        arch_name: Name of the architecture
        query: Single query (None for interactive mode)
        model: Model to use
        interactive: Force interactive mode
        verbose: Enable verbose logging
        business_template: Business template name
        template_vars: Template variables for prompt customization
    """
    from claude_agent_framework import create_session
    from claude_agent_framework.session import InitializationError

    # If no query provided and using business template, try to get default query
    if not query and business_template and not interactive:
        from claude_agent_framework.business_templates import get_template_default_query

        default_query = get_template_default_query(business_template, template_vars)
        if default_query:
            query = default_query
            print(f"Using default query from template: {query}")

    try:
        # Use create_session() to create session
        session = create_session(
            architecture=arch_name,  # type: ignore[arg-type]
            model=model,  # type: ignore[arg-type]
            verbose=verbose,
            business_template=business_template,
            template_vars=template_vars,
        )
    except InitializationError as e:
        print(f"Error: {e}")
        if "Unknown architecture" in str(e):
            print_architectures()
        return

    try:
        if query and not interactive:
            # Single query mode
            await _execute_query(session, query)
        else:
            # Interactive mode
            await _interactive_loop(session, arch_name)

    except KeyboardInterrupt:
        print("\n\nSession interrupted by user.")

    finally:
        await session.teardown()
        if session.session_dir:
            print(f"\nSession saved to: {session.session_dir}")


async def _execute_query(session: AgentSession, query: str) -> None:
    """Execute a single query."""
    print(f"\nExecuting with {session.architecture.name} architecture...")
    print("-" * 50)

    async for msg in session.run(query):
        # Message processing is handled by session
        pass

    print("-" * 50)
    print("Done.")


async def _interactive_loop(session: AgentSession, arch_name: str) -> None:
    """Run interactive loop."""
    print("\n" + "=" * 50)
    print(f"Claude Agent Framework - {arch_name} Architecture")
    print("=" * 50)
    print(f"\nUsing: {session.architecture.description}")
    print("\nType your query or 'quit' to exit.")

    while True:
        try:
            user_input = input("\n> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            await _execute_query(session, user_input)

        except EOFError:
            print("\nGoodbye!")
            break


def cmd_metrics(args: argparse.Namespace) -> None:
    """Display session metrics."""
    session_file = Path(args.session_file)

    if not session_file.exists():
        print(f"Error: Session file not found: {session_file}")
        return

    try:
        with session_file.open() as f:
            data = json.load(f)

        print("\n" + "=" * 60)
        print("SESSION METRICS")
        print("=" * 60)

        summary = data.get("summary", {})
        print(f"\nSession ID: {summary.get('session_id', 'N/A')}")
        print(f"Total Events: {summary.get('total_events', 0)}")

        print("\nEvent Counts:")
        for event_type, count in summary.get("event_counts", {}).items():
            print(f"  {event_type}: {count}")

        print("\nLog Levels:")
        for level, count in summary.get("level_counts", {}).items():
            print(f"  {level}: {count}")

        print("=" * 60)

    except json.JSONDecodeError:
        print(f"Error: Invalid JSON file: {session_file}")
    except Exception as e:
        print(f"Error reading session file: {e}")


def cmd_view(args: argparse.Namespace) -> None:
    """Open interactive session viewer in browser."""
    session_file = Path(args.session_file)

    if not session_file.exists():
        print(f"Error: Session file not found: {session_file}")
        return

    try:
        # Import here to avoid dependency issues if jinja2 not installed
        from claude_agent_framework.observability import SessionVisualizer

        # Load events from JSON
        visualizer = SessionVisualizer()
        visualizer.load_from_json(session_file)

        # Generate dashboard
        output_file = Path(args.output) if args.output else session_file.parent / "dashboard.html"
        html = visualizer.generate_dashboard(output_file)

        print(f"\nDashboard generated: {output_file}")

        # Open in browser if requested
        if not args.no_browser:
            print("Opening in browser...")
            webbrowser.open(f"file://{output_file.absolute()}")

    except ImportError:
        print("Error: Observability features require jinja2.")
        print("Install with: pip install 'claude-agent-framework[observability]'")
    except Exception as e:
        print(f"Error generating dashboard: {e}")


def cmd_report(args: argparse.Namespace) -> None:
    """Generate HTML reports."""
    session_file = Path(args.session_file)

    if not session_file.exists():
        print(f"Error: Session file not found: {session_file}")
        return

    try:
        # Import here to avoid dependency issues if jinja2 not installed
        from claude_agent_framework.observability import SessionVisualizer

        # Load events from JSON
        visualizer = SessionVisualizer()
        visualizer.load_from_json(session_file)

        # Generate full report
        output_dir = Path(args.output) if args.output else session_file.parent / "report"
        files = visualizer.generate_full_report(output_dir)

        print(f"\nReport generated: {output_dir}")
        print("\nGenerated files:")
        for report_type, file_path in files.items():
            print(f"  {report_type}: {file_path}")

        # Open dashboard in browser if requested
        if not args.no_browser and "dashboard" in files:
            print("\nOpening dashboard in browser...")
            webbrowser.open(f"file://{files['dashboard'].absolute()}")

    except ImportError:
        print("Error: Observability features require jinja2.")
        print("Install with: pip install 'claude-agent-framework[observability]'")
    except Exception as e:
        print(f"Error generating report: {e}")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Claude Agent Framework - Multi-Architecture Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Default command (run architecture) - for backward compatibility
    run_parser = subparsers.add_parser(
        "run",
        help="Run an architecture",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available architectures
  claude-agent run --list

  # Run research architecture with query
  claude-agent run --arch research -q "研究AI市场趋势"

  # Run pipeline architecture interactively
  claude-agent run --arch pipeline -i

  # Run with business template
  claude-agent run --arch research -bt competitive_intelligence \\
    -tv company_name="TechCorp" -tv industry="Cloud Computing"

  # Run debate architecture with tech decision template
  claude-agent run --arch debate -bt tech_decision \\
    -tv decision_topic="Database Selection" -q "Should we use PostgreSQL or MongoDB?"
""",
    )
    run_parser.add_argument(
        "--arch",
        "-a",
        type=str,
        default="research",
        help="Architecture to use (default: research)",
    )
    run_parser.add_argument(
        "-q",
        "--query",
        type=str,
        help="Single query mode: execute query and exit",
    )
    run_parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Force interactive mode",
    )
    run_parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="haiku",
        choices=["haiku", "sonnet", "opus"],
        help="Model to use (default: haiku)",
    )
    run_parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List available architectures",
    )
    run_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    run_parser.add_argument(
        "-bt",
        "--business-template",
        type=str,
        help="Business template to use (e.g., competitive_intelligence, pr_code_review)",
    )
    run_parser.add_argument(
        "-tv",
        "--template-var",
        action="append",
        metavar="KEY=VALUE",
        help="Template variable in key=value format (can be used multiple times)",
    )

    # Metrics command
    metrics_parser = subparsers.add_parser(
        "metrics",
        help="Display session metrics",
        description="Display metrics for a completed session",
    )
    metrics_parser.add_argument(
        "session_file",
        type=str,
        help="Path to session events JSON file",
    )

    # View command
    view_parser = subparsers.add_parser(
        "view",
        help="Open interactive session viewer",
        description="Generate and open interactive HTML dashboard for session analysis",
    )
    view_parser.add_argument(
        "session_file",
        type=str,
        help="Path to session events JSON file",
    )
    view_parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output HTML file path (default: session_dir/dashboard.html)",
    )
    view_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open browser automatically",
    )

    # Report command
    report_parser = subparsers.add_parser(
        "report",
        help="Generate HTML reports",
        description="Generate comprehensive HTML reports for session analysis",
    )
    report_parser.add_argument(
        "session_file",
        type=str,
        help="Path to session events JSON file",
    )
    report_parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output directory (default: session_dir/report)",
    )
    report_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open browser automatically",
    )

    # Also add top-level options for backward compatibility (when no subcommand)
    parser.add_argument(
        "--arch",
        "-a",
        type=str,
        default="research",
        help=argparse.SUPPRESS,  # Hide from help (use subcommand instead)
    )
    parser.add_argument(
        "-q",
        "--query",
        type=str,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="haiku",
        choices=["haiku", "sonnet", "opus"],
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-bt",
        "--business-template",
        type=str,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-tv",
        "--template-var",
        action="append",
        metavar="KEY=VALUE",
        help=argparse.SUPPRESS,
    )

    args = parser.parse_args()

    # Set log level
    if hasattr(args, "verbose") and args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Route to appropriate command
    if args.command == "metrics":
        cmd_metrics(args)
    elif args.command == "view":
        cmd_view(args)
    elif args.command == "report":
        cmd_report(args)
    elif args.command == "run" or args.command is None:
        # Run architecture (backward compatibility when no subcommand)
        if args.list:
            print_architectures()
        else:
            # Parse template variables from key=value format
            template_vars = None
            if hasattr(args, "template_var") and args.template_var:
                template_vars = {}
                for var in args.template_var:
                    if "=" in var:
                        key, value = var.split("=", 1)
                        template_vars[key.strip()] = value.strip()
                    else:
                        print(f"Warning: Invalid template variable format: {var} (expected key=value)")

            asyncio.run(
                run_architecture(
                    arch_name=args.arch,
                    query=args.query,
                    model=args.model,
                    interactive=args.interactive,
                    verbose=args.verbose if hasattr(args, "verbose") else False,
                    business_template=getattr(args, "business_template", None),
                    template_vars=template_vars,
                )
            )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
