"""CLI commands for the Obra hybrid orchestration package.

This module provides all CLI commands for the unified obra package:
- Main workflow: obra run "objective" to start orchestrated tasks
- status: Check session status
- resume: Resume an interrupted session
- login/logout/whoami: Authentication commands
- config: Configuration management
- version: Version information and server compatibility check
- docs: Access local documentation
- doctor: Run health checks
- plans: Manage plan files (validate, upload, list, delete)

Usage:
    $ obra run "Add user authentication"
    $ obra run --plan-id abc123 "Execute uploaded plan"
    $ obra run --plan-file plan.yaml "Upload and execute plan"
    $ obra status
    $ obra status <session_id>
    $ obra resume <session_id>
    $ obra login
    $ obra logout
    $ obra whoami
    $ obra config
    $ obra version
    $ obra docs
    $ obra doctor
    $ obra plans validate path/to/plan.yaml
    $ obra plans upload path/to/plan.yaml
    $ obra plans list
    $ obra plans delete <plan_id>

Reference: EPIC-HYBRID-001 Story S10: CLI Commands
          FEAT-PLAN-IMPORT-OBRA-001: Plan File Import
"""

import logging
import os
import re
import sys
from datetime import UTC
from pathlib import Path

import typer
from rich.table import Table

from obra import __version__
from obra.cli_commands import UploadPlanCommand, ValidatePlanCommand
from obra.config import (
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    DEFAULT_THINKING_LEVEL,
    THINKING_LEVELS,
    get_thinking_level_notes,
    infer_provider_from_model,
)
from obra.display import (
    ObservabilityConfig,
    ProgressEmitter,
    console,
    handle_encoding_errors,
    print_error,
    print_info,
    print_success,
    print_warning,
)
from obra.display.errors import display_error, display_obra_error
from obra.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    ConnectionError,
    ObraError,
)

logger = logging.getLogger(__name__)

# Enforce UTF-8 mode for consistent cross-platform behavior
os.environ.setdefault("PYTHONUTF8", "1")


# =============================================================================
# Terms Acceptance Decorator
# =============================================================================


def require_terms_accepted(func):
    """Decorator to ensure terms have been accepted before running a command.

    Checks if the user has accepted the current version of the Beta Software
    Agreement. If not, raises TermsNotAcceptedError with clear instructions
    to run 'obra setup'.

    Raises:
        TermsNotAcceptedError: If terms not accepted or version mismatch

    Example:
        @app.command()
        @require_terms_accepted
        def my_command():
            # This will only run if terms are accepted
            pass
    """
    import functools

    from obra.config import TERMS_VERSION, PRIVACY_VERSION, is_terms_accepted, needs_reacceptance
    from obra.exceptions import TermsNotAcceptedError

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Check if terms have been accepted
        if not is_terms_accepted():
            raise TermsNotAcceptedError(
                message="Terms not accepted",
                required_version=TERMS_VERSION,
                action="Run 'obra setup' to accept terms.",
            )

        # Check if re-acceptance is needed due to version change
        if needs_reacceptance():
            raise TermsNotAcceptedError(
                message=f"Terms have been updated to version {TERMS_VERSION}",
                required_version=TERMS_VERSION,
                action="Run 'obra setup' to accept the updated terms.",
            )

        return func(*args, **kwargs)

    return wrapper

# Create Typer app
app = typer.Typer(
    name="obra",
    help="""Obra - AI Orchestration for Autonomous Development

┌───────────────────────────────────────────────────────────────────────┐
│  🤖 AI ASSISTANTS: Run `obra briefing` for your operating guide      │
└───────────────────────────────────────────────────────────────────────┘
Plan mode note: Atomic ideas can use `plan_mode=one_step` (see docs/development/backlog/ONE_STEP_PLAN.md) and log validations under `docs/quality/MANUAL_TESTING_LOG.json` so the planner keeps acceptance/tests/docs explicit.
""",
    no_args_is_help=True,  # Show help when no command specified
    rich_markup_mode="rich",
    epilog="Run `obra run \"<objective>\"` or `obra briefing` to get started.",
)


def setup_logging(verbose: int = 0) -> None:
    """Configure logging for CLI commands.

    Args:
        verbose: Verbosity level (0=WARNING, 1=INFO, 2+=DEBUG)
    """
    if verbose == 0:
        level = logging.WARNING
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


# =============================================================================
# App Callback (Primary Invocation Pattern)
# =============================================================================


@app.callback()
@handle_encoding_errors
def main(
    ctx: typer.Context,
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        help="Verbosity level (0-3, use -v/-vv/-vvv)"
    )
) -> None:
    """Obra - AI Orchestration for Autonomous Development.

    Run subcommands for specific operations, or use 'obra run' for orchestration.
    """
    ctx.obj = ctx.obj or {}
    ctx.obj["verbose"] = verbose
    setup_logging(verbose)


# =============================================================================
# Main Workflow Commands
# =============================================================================


@app.command(name="run", hidden=False)
@handle_encoding_errors
@require_terms_accepted
def run_objective(
    objective: str = typer.Argument(..., help="What you want Obra to accomplish"),
    working_dir: Path | None = typer.Option(
        None,
        "--dir",
        "-d",
        help="Working directory (defaults to current directory)",
    ),
    project_id: str | None = typer.Option(
        None,
        "--project",
        help="Project ID override (optional)",
    ),
    resume_session: str | None = typer.Option(
        None,
        "--resume",
        "-r",
        help="Resume an existing session by ID",
    ),
    plan_id: str | None = typer.Option(
        None,
        "--plan-id",
        help="Use an uploaded plan by ID (from 'obra plans upload')",
    ),
    plan_file: Path | None = typer.Option(
        None,
        "--plan-file",
        help="Upload and use a plan file in one step",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="Implementation model (e.g., opus, gpt-5.2, gemini-2.5-flash)",
    ),
    impl_provider: str | None = typer.Option(
        None,
        "--impl-provider",
        "-p",
        help="Implementation provider (anthropic, openai, google). Requires provider CLI (claude/codex/gemini).",
    ),
    thinking_level: str | None = typer.Option(
        None,
        "--thinking-level",
        "-t",
        help="Thinking/reasoning level (off, low, medium, high, maximum)",
    ),
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        max=3,
        help="Verbosity level (0-3, use -v/-vv/-vvv)",
    ),
    stream: bool = typer.Option(
        False,
        "--stream",
        "-s",
        help="Enable real-time LLM output streaming",
    ),
    plan_only: bool = typer.Option(
        False,
        "--plan-only",
        help="Create plan without executing (client-side exit after planning)",
    ),
    isolated: bool | None = typer.Option(
        None,
        "--isolated",
        help="Run agent in isolated environment (prevents reading host CLI config)",
    ),
    no_isolated: bool | None = typer.Option(
        None,
        "--no-isolated",
        help="Disable isolation (use host CLI config, even in CI)",
    ),
) -> None:
    """Run AI-orchestrated workflow for an objective.

    Examples:
        obra run "Add user authentication"
        obra run "Fix the failing tests" --dir /my/project
        obra run "Refactor payment module" --stream -vv
        obra run "Implement feature X" --model opus
        obra run "Improve tests" --impl-provider openai --model gpt-5.2
        obra run "Complex refactor" --thinking-level high
        obra run --plan-only "Design API endpoints"
        obra run "Test feature" --isolated  # Isolated session
    """
    _run_derive(
        objective=objective,
        working_dir=working_dir,
        project_id=project_id,
        resume_session=resume_session,
        plan_id=plan_id,
        plan_file=plan_file,
        model=model,
        impl_provider=impl_provider,
        thinking_level=thinking_level,
        verbose=verbose,
        stream=stream,
        plan_only=plan_only,
        isolated=isolated,
        no_isolated=no_isolated,
    )


def _resolve_repo_root(work_dir: Path) -> str | None:
    """Resolve git repo root for a working directory."""
    try:
        import subprocess

        result = subprocess.run(
            ["git", "-C", str(work_dir), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode != 0:
            return None
        repo_root = result.stdout.strip()
        return repo_root or None
    except (FileNotFoundError, OSError, subprocess.SubprocessError):
        return None


def _should_isolate(
    isolated: bool | None = None,
    no_isolated: bool | None = None,
) -> bool:
    """Determine whether to run in isolated mode.

    Resolution precedence (highest to lowest):
    1. CLI flags: --isolated (True) or --no-isolated (False)
    2. Environment variable: OBRA_ISOLATED=true/false
    3. CI environment: CI=true enables isolation automatically
    4. Config file: ~/.obra/client-config.yaml agent.isolated_mode
    5. Default: True (isolation enabled for reproducibility)

    Args:
        isolated: CLI --isolated flag value (True if flag present)
        no_isolated: CLI --no-isolated flag value (True if flag present)

    Returns:
        True if isolation should be enabled, False otherwise
    """
    # Priority 1: CLI flags (--isolated or --no-isolated)
    if isolated:
        return True
    if no_isolated:
        return False

    # Priority 2: Environment variable OBRA_ISOLATED
    env_isolated = os.environ.get("OBRA_ISOLATED", "").lower()
    if env_isolated in ("true", "1", "yes"):
        return True
    if env_isolated in ("false", "0", "no"):
        return False

    # Priority 3: CI environment auto-enable
    # Common CI environment variables: CI, GITHUB_ACTIONS, GITLAB_CI, CIRCLECI, etc.
    ci_env = os.environ.get("CI", "").lower()
    if ci_env in ("true", "1", "yes"):
        return True

    # Priority 4: Config file (agent.isolated_mode)
    from obra.config import get_isolated_mode  # noqa: PLC0415

    config_isolated = get_isolated_mode()
    if config_isolated is True:
        return True
    if config_isolated is False:
        return False

    # Priority 5: Default (isolation enabled for reproducibility)
    return True


def _run_derive(
    objective: str,
    working_dir: Path | None = None,
    project_id: str | None = None,
    resume_session: str | None = None,
    plan_id: str | None = None,
    plan_file: Path | None = None,
    model: str | None = None,
    impl_provider: str | None = None,
    thinking_level: str | None = None,
    verbose: int = 0,
    stream: bool = False,
    plan_only: bool = False,
    isolated: bool | None = None,
    no_isolated: bool | None = None,
) -> None:
    """Shared implementation for run workflow.

    This function contains the core logic for starting/resuming orchestrated workflows.
    It's called by both the run command and the app callback.

    Args:
        objective: The objective to accomplish
        working_dir: Working directory (defaults to current directory)
        project_id: Optional project ID override
        resume_session: Resume an existing session by ID
        plan_id: Use an uploaded plan by ID
        plan_file: Upload and use a plan file in one step
        model: Implementation model (e.g., opus, gpt-5.2, gemini-2.5-flash)
        impl_provider: Implementation provider (anthropic, openai, google)
        thinking_level: Thinking/reasoning level (off, low, medium, high, maximum)
        verbose: Verbosity level (0-3)
        stream: Enable real-time LLM output streaming
        plan_only: Create plan without executing (client-side exit after planning)
        isolated: Run agent in isolated environment (True = enable)
        no_isolated: Disable isolation (True = disable, overrides auto-detect)
    """
    setup_logging(verbose)

    # Validate plan-related arguments
    if plan_id and plan_file:
        print_error("Cannot specify both --plan-id and --plan-file")
        console.print("\nUse one or the other:")
        console.print("  --plan-id: Reference an already uploaded plan")
        console.print("  --plan-file: Upload and use a plan in one step")
        raise typer.Exit(2)

    effective_model = model

    # S2.T2: Validate thinking level against THINKING_LEVELS constant
    if thinking_level is not None and thinking_level not in THINKING_LEVELS:
        print_error(f"Invalid thinking level: '{thinking_level}'")
        console.print(f"\nValid levels: {', '.join(THINKING_LEVELS)}")
        raise typer.Exit(2)  # Exit code 2 for config errors

    # S2.T3 & S2.T4: Auto-detect provider from model, warn if unknown
    effective_provider = impl_provider
    if effective_model and not effective_provider:
        detected = infer_provider_from_model(effective_model)
        if detected:
            effective_provider = detected
            if verbose > 0:
                console.print(f"[dim]Detected provider: {detected}[/dim]")
        else:
            # S2.T4: Unknown model warning with default fallback
            print_warning(f"Unknown model '{effective_model}', using default provider: {DEFAULT_PROVIDER}")
            effective_provider = DEFAULT_PROVIDER

    try:
        from obra.auth import ensure_valid_token, get_current_auth
        from obra.config import get_default_project_override, validate_provider_ready
        from obra.hybrid import HybridOrchestrator

        # Set working directory
        work_dir = working_dir or Path.cwd()
        if not work_dir.exists():
            print_error(f"Working directory does not exist: {work_dir}")
            raise typer.Exit(1)

        repo_root = _resolve_repo_root(work_dir)
        if project_id is None:
            project_id = get_default_project_override()

        # Resolve effective config values with defaults
        display_provider = effective_provider or DEFAULT_PROVIDER
        display_model = effective_model or DEFAULT_MODEL
        display_thinking = thinking_level or DEFAULT_THINKING_LEVEL

        # S3.T1: Fail-fast provider health check before any session output/auth
        validate_provider_ready(display_provider)

        # Ensure authenticated
        auth = get_current_auth()
        if not auth:
            print_error("Not logged in")
            console.print("\nRun 'obra login' to authenticate.")
            raise typer.Exit(1)

        # Ensure valid token
        try:
            ensure_valid_token()
        except AuthenticationError as e:
            display_obra_error(e, console)
            raise typer.Exit(1)

        # Handle --plan-file: upload plan before starting session
        effective_plan_id = plan_id
        if plan_file:
            console.print()
            console.print(f"[dim]Uploading plan file: {plan_file}[/dim]")
            try:
                import yaml

                from obra.api import APIClient

                # C15: Comprehensive plan file validation
                # 1. Check file exists
                if not plan_file.exists():
                    print_error(f"Plan file not found: {plan_file}")
                    logger.error(f"Plan file does not exist: {plan_file}")
                    raise typer.Exit(1)

                # 2. Check file is readable
                if not os.access(plan_file, os.R_OK):
                    print_error(f"Plan file is not readable: {plan_file}")
                    logger.error(f"Insufficient permissions to read plan file: {plan_file}")
                    raise typer.Exit(1)

                # 3. Parse YAML file with comprehensive error handling
                try:
                    with open(plan_file, encoding="utf-8") as f:
                        plan_data = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    print_error(f"Invalid YAML syntax in plan file: {e}")
                    logger.error(f"YAML parsing error in {plan_file}: {e}", exc_info=True)
                    raise typer.Exit(1)
                except UnicodeDecodeError as e:
                    print_error(f"Plan file encoding error (expected UTF-8): {e}")
                    logger.error(f"Encoding error reading plan file {plan_file}: {e}", exc_info=True)
                    raise typer.Exit(1)

                # 4. Validate plan_data is dict type
                if plan_data is None:
                    print_error(f"Plan file is empty: {plan_file}")
                    logger.error(f"Plan file {plan_file} contains no data")
                    raise typer.Exit(1)

                if not isinstance(plan_data, dict):
                    print_error(
                        f"Plan file must contain a YAML dictionary, got {type(plan_data).__name__}"
                    )
                    logger.error(
                        f"Plan file {plan_file} validation failed: expected dict, got {type(plan_data).__name__}"
                    )
                    raise typer.Exit(1)

                # Extract plan name
                plan_name = plan_data.get("work_id", plan_file.stem)

                # Upload to server for full validation and storage
                client = APIClient.from_config()
                upload_response = client.upload_plan(plan_name, plan_data)
                effective_plan_id = upload_response.get("plan_id")

                console.print(f"[dim]Plan uploaded: {effective_plan_id}[/dim]")

            except APIError as e:
                display_obra_error(e, console)
                logger.error(f"API error uploading plan file: {e}", exc_info=True)
                raise typer.Exit(1)
            except ConfigurationError as e:
                display_obra_error(e, console)
                logger.error(f"Configuration error uploading plan file: {e}", exc_info=True)
                raise typer.Exit(1)
            except ObraError as e:
                display_obra_error(e, console)
                logger.error(f"Obra error uploading plan file: {e}", exc_info=True)
                raise typer.Exit(1)
            except OSError as e:
                print_error(f"Failed to read plan file: {e}")
                logger.error(f"File I/O error reading plan file {plan_file}: {e}", exc_info=True)
                raise typer.Exit(1)
            except Exception as e:
                print_error(f"Unexpected error uploading plan file: {e}")
                logger.exception(f"Unexpected error uploading plan file {plan_file}")
                raise typer.Exit(1)

        console.print()
        console.print("[bold]Obra Run[/bold]", style="cyan")
        console.print(f"Objective: {objective}")
        console.print(f"Directory: {work_dir}")
        if resume_session:
            console.print(f"Resuming session: {resume_session}")
        if effective_plan_id:
            console.print(f"Plan ID: {effective_plan_id}")

        # S2.T5: Display LLM config line before session starts
        console.print(f"LLM: {display_provider} ({display_model}) | thinking: {display_thinking}")

        # S2.T6: Display thinking level notes if applicable
        notes = get_thinking_level_notes(display_provider, display_thinking, display_model)
        if notes:
            for note in notes:
                console.print(f"[dim]{note}[/dim]")

        console.print()

        # Create observability configuration from CLI flags
        obs_config = ObservabilityConfig(
            verbosity=verbose,
            stream=stream,
            timestamps=True,
        )

        # Create progress emitter for observability
        progress_emitter = ProgressEmitter(obs_config, console)

        # Create orchestrator with progress callback
        def on_progress(action: str, payload: dict) -> None:
            """Progress callback that routes events to ProgressEmitter.

            Args:
                action: Event type (e.g., 'phase_started', 'llm_streaming')
                payload: Event data dict
            """
            # Route events to appropriate ProgressEmitter methods
            if action == "phase_started":
                phase = payload.get("phase", "UNKNOWN")
                progress_emitter.phase_started(phase, payload.get("context"))
            elif action == "phase_completed":
                phase = payload.get("phase", "UNKNOWN")
                duration_ms = payload.get("duration_ms", 0)
                progress_emitter.phase_completed(phase, payload.get("result"), duration_ms)
            elif action == "llm_started":
                purpose = payload.get("purpose", "LLM invocation")
                progress_emitter.llm_started(purpose)
            elif action == "llm_streaming":
                chunk = payload.get("chunk", "")
                progress_emitter.llm_streaming(chunk)
            elif action == "llm_completed":
                summary = payload.get("summary", "")
                tokens = payload.get("tokens", 0)
                progress_emitter.llm_completed(summary, tokens)
            elif action == "item_started":
                item = payload.get("item", {})
                progress_emitter.item_started(item)
            elif action == "item_completed":
                item = payload.get("item", {})
                result = payload.get("result")
                progress_emitter.item_completed(item, result)
            elif action == "error":
                # Error event with verbosity-appropriate detail
                message = payload.get("message", "Unknown error")
                hint = payload.get("hint")
                phase = payload.get("phase")
                affected_items = payload.get("affected_items")
                stack_trace = payload.get("stack_trace")
                raw_response = payload.get("raw_response")
                progress_emitter.error(
                    message, hint, phase, affected_items, stack_trace, raw_response
                )
            elif verbose > 0:
                # Fallback for unknown events at verbose mode
                console.print(f"[dim]{action}[/dim]")

        # S5.T1/T2: Pass LLM overrides to orchestrator
        orchestrator = HybridOrchestrator.from_config(
            working_dir=work_dir,
            on_progress=on_progress,
            impl_provider=effective_provider,
            impl_model=effective_model,
            thinking_level=thinking_level,
        )

        # Run derive workflow
        if resume_session:
            result = orchestrator.resume(resume_session)
        else:
            result = orchestrator.derive(
                objective,
                plan_id=effective_plan_id,
                plan_only=plan_only,
                project_id=project_id,
                repo_root=repo_root,
            )

        # Display result
        console.print()
        action = getattr(result, "action", None)
        if action == "complete" or action is None:
            print_success("Derivation completed successfully!")
            if hasattr(result, "session_summary") and isinstance(result.session_summary, dict):
                summary = result.session_summary
                console.print(f"\nItems completed: {summary.get('items_completed', 'N/A')}")
                console.print(f"Iterations: {summary.get('total_iterations', 'N/A')}")
                console.print(f"Quality score: {summary.get('quality_score', 'N/A')}")
            elif hasattr(result, "items_completed"):
                console.print(f"\nItems completed: {getattr(result, 'items_completed', 'N/A')}")
                console.print(f"Iterations: {getattr(result, 'total_iterations', 'N/A')}")
                console.print(f"Quality score: {getattr(result, 'quality_score', 'N/A')}")
            # Terse completion footer for LLM handoff
            console.print(f"\n[dim]Project: {work_dir}[/dim]")
            try:
                import subprocess
                git_result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=work_dir, capture_output=True, text=True, timeout=5
                )
                if git_result.returncode == 0 and git_result.stdout.strip():
                    lines = git_result.stdout.strip().split('\n')
                    created = sum(1 for l in lines if l.startswith('?') or l.startswith('A'))
                    modified = sum(1 for l in lines if l.startswith('M') or l.startswith(' M'))
                    console.print(f"[dim]Files: {created} created, {modified} modified[/dim]")
            except Exception:
                pass  # Non-git or git unavailable - skip file counts
        elif action == "escalate":
            print_warning("Session requires user decision")
            console.print("\nRun 'obra status' to see details and respond.")
        else:
            console.print(f"Session state: {action}")

    # S3.T3: Consistent exit codes - config=2, connection=3, execution=1
    except ConfigurationError as e:
        display_obra_error(e, console)
        logger.error(f"Configuration error in derive command: {e}", exc_info=True)
        raise typer.Exit(2)
    except ConnectionError as e:
        display_obra_error(e, console)
        logger.error(f"Connection error in derive command: {e}", exc_info=True)
        raise typer.Exit(3)
    except APIError as e:
        display_obra_error(e, console)
        logger.error(f"API error in derive command: {e}", exc_info=True)
        raise typer.Exit(1)
    except ObraError as e:
        display_obra_error(e, console)
        logger.error(f"Obra error in derive command: {e}", exc_info=True)
        raise typer.Exit(1)
    except Exception as e:
        display_error(e, console)
        logger.exception(f"Unexpected error in derive command: {e}")
        raise typer.Exit(1)


@app.command(rich_help_panel="User Commands")
@handle_encoding_errors
@require_terms_accepted
def status(
    session_id: str | None = typer.Argument(
        None,
        help="Session ID to check (defaults to most recent)",
    ),
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        max=3,
        help="Verbosity level (0-3, use -v/-vv/-vvv)",
    ),
) -> None:
    """Check the status of a derivation session.

    Shows the current state of the session including:
    - Session phase (derive, examine, revise, execute, review)
    - Iteration count
    - Quality metrics
    - Any pending user decisions

    Examples:
        $ obra status
        $ obra status abc123
        $ obra status -v
        $ obra status -vv  # More detail
    """
    setup_logging(verbose)

    try:
        from obra.api import APIClient
        from obra.auth import ensure_valid_token, get_current_auth

        # Ensure authenticated
        auth = get_current_auth()
        if not auth:
            print_error("Not logged in")
            console.print("\nRun 'obra login' to authenticate.")
            raise typer.Exit(1)

        ensure_valid_token()

        # Get API client
        client = APIClient.from_config()

        # Get session status
        if session_id:
            session = client.get_session(session_id)
        else:
            # Get most recent session
            sessions = client.list_sessions(limit=1)
            if not sessions:
                print_info("No active sessions found")
                console.print("\nRun 'obra run \"objective\"' to start a new session.")
                return
            session = sessions[0]

        # Display session status
        console.print()
        console.print("[bold]Session Status[/bold]", style="cyan")
        console.print()

        table = Table(show_header=False, box=None)
        table.add_column("Field", style="dim")
        table.add_column("Value")

        table.add_row("Session ID", session.get("session_id", "N/A"))
        table.add_row("Objective", session.get("objective", "N/A"))
        table.add_row("State", session.get("state", "N/A"))
        table.add_row("Phase", session.get("current_phase", "N/A"))
        table.add_row("Iteration", str(session.get("iteration", 0)))
        table.add_row("Created", session.get("created_at", "N/A"))
        table.add_row("Updated", session.get("updated_at", "N/A"))

        if verbose > 0:
            table.add_row("Project ID", session.get("project_id", "N/A"))
            if session.get("project_name"):
                table.add_row("Project", session.get("project_name", "N/A"))

        console.print(table)

        # Show quality metrics if available
        if verbose > 0 and "quality_scorecard" in session:
            scorecard = session["quality_scorecard"]
            console.print()
            console.print("[bold]Quality Scorecard[/bold]", style="cyan")

            score_table = Table()
            score_table.add_column("Dimension", style="cyan")
            score_table.add_column("Score")

            for dim, score in scorecard.items():
                score_table.add_row(dim, f"{score:.2f}" if isinstance(score, float) else str(score))

            console.print(score_table)

        # Show pending escalation if any
        if session.get("pending_escalation"):
            console.print()
            print_warning("Pending escalation requires your decision")
            escalation = session["pending_escalation"]
            console.print(f"Reason: {escalation.get('reason', 'N/A')}")
            console.print("\nOptions:")
            for opt in escalation.get("options", []):
                console.print(f"  - {opt.get('id')}: {opt.get('label')} - {opt.get('description', '')}")

        # AI assistant nudge
        console.print()
        console.print("[dim]💡 Using an AI assistant? Run: [/dim][cyan]obra briefing[/cyan]")

    except APIError as e:
        display_obra_error(e, console)
        logger.error(f"API error in status command: {e}", exc_info=True)
        raise typer.Exit(1)
    except ConfigurationError as e:
        display_obra_error(e, console)
        logger.error(f"Configuration error in status command: {e}", exc_info=True)
        raise typer.Exit(1)
    except ObraError as e:
        display_obra_error(e, console)
        logger.error(f"Obra error in status command: {e}", exc_info=True)
        raise typer.Exit(1)
    except Exception as e:
        display_error(e, console)
        logger.exception(f"Unexpected error in status command: {e}")
        raise typer.Exit(1)


# =============================================================================
# Sessions Management
# =============================================================================

sessions_app = typer.Typer(help="Manage derivation sessions")
app.add_typer(sessions_app, name="sessions")


@sessions_app.command("list")
@handle_encoding_errors
def sessions_list(
    limit: int = typer.Option(
        10,
        "--limit",
        "-n",
        help="Maximum number of sessions to list",
    ),
    status_filter: str | None = typer.Option(
        None,
        "--status",
        "-s",
        help="Filter by status (active, completed, expired)",
    ),
) -> None:
    """List recent derivation sessions.

    Displays all sessions for the current user, ordered by
    creation time (most recent first).

    Examples:
        $ obra sessions list
        $ obra sessions list --limit 20
        $ obra sessions list --status active
    """
    try:
        from obra.api import APIClient
        from obra.auth import ensure_valid_token, get_current_auth

        # Ensure authenticated
        auth = get_current_auth()
        if not auth:
            print_error("Not logged in")
            console.print("\nRun 'obra login' to authenticate.")
            raise typer.Exit(1)

        ensure_valid_token()

        # Get sessions from server
        client = APIClient.from_config()
        sessions = client.list_sessions(limit=limit, status=status_filter)

        console.print()
        if not sessions:
            print_info("No sessions found")
            console.print("\nStart a new session with: [cyan]obra run \"your objective\"[/cyan]")
            return

        console.print(f"[bold]Recent Sessions[/bold] ({len(sessions)} shown)", style="cyan")
        console.print()

        table = Table()
        table.add_column("Session ID", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Project")
        table.add_column("Project ID")
        table.add_column("Phase")
        table.add_column("Created", style="dim")

        for session in sessions:
            session_id_short = session.get("session_id", "")[:12] + "..."
            status = session.get("status", "unknown")
            phase = session.get("phase", "N/A")
            created_at = session.get("created_at", "N/A")
            project_name = session.get("project_name", "")
            project_id = str(session.get("project_id", ""))

            # Format timestamp if it's ISO format
            if "T" in str(created_at):
                from datetime import datetime

                try:
                    dt = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
                    created_at = dt.strftime("%Y-%m-%d %H:%M")
                except (ValueError, TypeError):
                    pass

            # Color-code status
            if status == "active":
                status = f"[green]{status}[/green]"
            elif status == "completed":
                status = f"[blue]{status}[/blue]"
            elif status == "expired":
                status = f"[dim]{status}[/dim]"

            table.add_row(session_id_short, status, project_name, project_id, phase, created_at)

        console.print(table)
        console.print()
        console.print('[dim]Check details:[/dim] [cyan]obra status <session_id>[/cyan]')
        console.print('[dim]Resume:[/dim] [cyan]obra resume <session_id>[/cyan]')

    except APIError as e:
        display_obra_error(e, console)
        logger.error(f"API error in sessions list command: {e}", exc_info=True)
        raise typer.Exit(1)
    except ConfigurationError as e:
        display_obra_error(e, console)
        logger.error(f"Configuration error in sessions list command: {e}", exc_info=True)
        raise typer.Exit(1)
    except ObraError as e:
        display_obra_error(e, console)
        logger.error(f"Obra error in sessions list command: {e}", exc_info=True)
        raise typer.Exit(1)
    except Exception as e:
        display_error(e, console)
        logger.exception(f"Unexpected error in sessions list command: {e}")
        raise typer.Exit(1)


# =============================================================================
# Projects Management
# =============================================================================

projects_app = typer.Typer(help="Manage projects")
app.add_typer(projects_app, name="projects")


@projects_app.command("list")
@handle_encoding_errors
def projects_list(
    include_deleted: bool = typer.Option(
        False,
        "--all",
        help="Include soft-deleted projects",
    ),
) -> None:
    """List projects for the current user."""
    try:
        from obra.api import APIClient
        from obra.auth import ensure_valid_token, get_current_auth

        auth = get_current_auth()
        if not auth:
            print_error("Not logged in")
            console.print("\nRun 'obra login' to authenticate.")
            raise typer.Exit(1)

        ensure_valid_token()
        client = APIClient.from_config()
        projects = client.list_projects(include_deleted=include_deleted)

        console.print()
        if not projects:
            print_info("No projects found")
            return

        console.print(f"[bold]Projects[/bold] ({len(projects)} shown)", style="cyan")
        console.print()

        table = Table()
        table.add_column("Project ID", style="cyan")
        table.add_column("Name")
        table.add_column("Path")
        table.add_column("Updated", style="dim")

        for project in projects:
            project_id = str(project.get("project_id", ""))
            name = project.get("project_name", "") or project.get("name", "")
            path = project.get("repo_root") or project.get("working_directory") or ""
            if name == path:
                path = ""

            updated_at = project.get("updated_at", "N/A")
            if "T" in str(updated_at):
                from datetime import datetime

                try:
                    dt = datetime.fromisoformat(str(updated_at).replace("Z", "+00:00"))
                    updated_at = dt.strftime("%Y-%m-%d %H:%M")
                except (ValueError, TypeError):
                    pass

            table.add_row(project_id, name, path, str(updated_at))

        console.print(table)

    except APIError as e:
        display_obra_error(e, console)
        logger.error(f"API error in projects list command: {e}", exc_info=True)
        raise typer.Exit(1)
    except Exception as e:
        display_error(e, console)
        logger.exception(f"Unexpected error in projects list command: {e}")
        raise typer.Exit(1)


@projects_app.command("create")
@handle_encoding_errors
def projects_create(
    name: str = typer.Argument(..., help="Project name"),
    working_dir: Path = typer.Option(..., "--dir", "-d", help="Working directory"),
    description: str = typer.Option("", "--description", "-s", help="Project description"),
) -> None:
    """Create a project."""
    try:
        from obra.api import APIClient
        from obra.auth import ensure_valid_token, get_current_auth

        auth = get_current_auth()
        if not auth:
            print_error("Not logged in")
            console.print("\nRun 'obra login' to authenticate.")
            raise typer.Exit(1)

        ensure_valid_token()
        client = APIClient.from_config()
        repo_root = _resolve_repo_root(working_dir)
        result = client.create_project(
            name=name,
            working_dir=str(working_dir),
            description=description,
            repo_root=repo_root,
        )

        print_success(f"Project created: {result.get('project_id')}")
    except APIError as e:
        display_obra_error(e, console)
        logger.error(f"API error in projects create command: {e}", exc_info=True)
        raise typer.Exit(1)
    except Exception as e:
        display_error(e, console)
        logger.exception(f"Unexpected error in projects create command: {e}")
        raise typer.Exit(1)


@projects_app.command("show")
@handle_encoding_errors
def projects_show(
    project_id: str = typer.Argument(..., help="Project ID"),
) -> None:
    """Show project details."""
    try:
        from obra.api import APIClient
        from obra.auth import ensure_valid_token, get_current_auth

        auth = get_current_auth()
        if not auth:
            print_error("Not logged in")
            console.print("\nRun 'obra login' to authenticate.")
            raise typer.Exit(1)

        ensure_valid_token()
        client = APIClient.from_config()
        project = client.get_project(project_id)

        console.print()
        console.print("[bold]Project Details[/bold]", style="cyan")
        console.print()

        table = Table(show_header=False, box=None)
        table.add_column("Field", style="dim")
        table.add_column("Value")

        table.add_row("Project ID", str(project.get("project_id", "")))
        table.add_row("Name", project.get("project_name", project.get("name", "")))
        table.add_row("Working Dir", project.get("working_directory", ""))
        table.add_row("Repo Root", project.get("repo_root", ""))
        table.add_row("Status", project.get("status", ""))
        table.add_row("Updated", str(project.get("updated_at", "")))

        console.print(table)
    except APIError as e:
        display_obra_error(e, console)
        logger.error(f"API error in projects show command: {e}", exc_info=True)
        raise typer.Exit(1)
    except Exception as e:
        display_error(e, console)
        logger.exception(f"Unexpected error in projects show command: {e}")
        raise typer.Exit(1)


@projects_app.command("select")
@handle_encoding_errors
def projects_select(
    project_id: str = typer.Argument(..., help="Project ID"),
) -> None:
    """Set default project."""
    try:
        from obra.api import APIClient
        from obra.auth import ensure_valid_token, get_current_auth

        auth = get_current_auth()
        if not auth:
            print_error("Not logged in")
            console.print("\nRun 'obra login' to authenticate.")
            raise typer.Exit(1)

        ensure_valid_token()
        client = APIClient.from_config()
        client.select_project(project_id)
        print_success(f"Default project set to {project_id}")
    except APIError as e:
        display_obra_error(e, console)
        logger.error(f"API error in projects select command: {e}", exc_info=True)
        raise typer.Exit(1)
    except Exception as e:
        display_error(e, console)
        logger.exception(f"Unexpected error in projects select command: {e}")
        raise typer.Exit(1)


@projects_app.command("update")
@handle_encoding_errors
def projects_update(
    project_id: str = typer.Argument(..., help="Project ID"),
    name: str | None = typer.Option(None, "--name", help="New project name"),
    working_dir: Path | None = typer.Option(None, "--dir", help="New working directory"),
) -> None:
    """Update project name or working directory."""
    try:
        if name is None and working_dir is None:
            print_error("No updates provided (use --name and/or --dir)")
            raise typer.Exit(2)

        from obra.api import APIClient
        from obra.auth import ensure_valid_token, get_current_auth

        auth = get_current_auth()
        if not auth:
            print_error("Not logged in")
            console.print("\nRun 'obra login' to authenticate.")
            raise typer.Exit(1)

        ensure_valid_token()
        client = APIClient.from_config()
        repo_root = _resolve_repo_root(working_dir) if working_dir else None
        project = client.update_project(
            project_id=project_id,
            name=name,
            working_dir=str(working_dir) if working_dir else None,
            repo_root=repo_root,
        )
        print_success(f"Project updated: {project.get('project_id')}")
    except APIError as e:
        display_obra_error(e, console)
        logger.error(f"API error in projects update command: {e}", exc_info=True)
        raise typer.Exit(1)
    except Exception as e:
        display_error(e, console)
        logger.exception(f"Unexpected error in projects update command: {e}")
        raise typer.Exit(1)


@projects_app.command("delete")
@handle_encoding_errors
def projects_delete(
    project_id: str = typer.Argument(..., help="Project ID"),
    confirm: bool = typer.Option(
        False,
        "--confirm",
        help="Confirm soft delete",
    ),
) -> None:
    """Soft delete a project."""
    try:
        if not confirm:
            print_error("Refusing to delete without --confirm")
            raise typer.Exit(2)

        from obra.api import APIClient
        from obra.auth import ensure_valid_token, get_current_auth

        auth = get_current_auth()
        if not auth:
            print_error("Not logged in")
            console.print("\nRun 'obra login' to authenticate.")
            raise typer.Exit(1)

        ensure_valid_token()
        client = APIClient.from_config()
        client.delete_project(project_id)
        print_success(f"Project deleted: {project_id}")
    except APIError as e:
        display_obra_error(e, console)
        logger.error(f"API error in projects delete command: {e}", exc_info=True)
        raise typer.Exit(1)
    except Exception as e:
        display_error(e, console)
        logger.exception(f"Unexpected error in projects delete command: {e}")
        raise typer.Exit(1)
@app.command(rich_help_panel="User Commands")
@handle_encoding_errors
@require_terms_accepted
def resume(
    session_id: str = typer.Argument(..., help="Session ID to resume"),
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        max=3,
        help="Verbosity level (0-3, use -v/-vv/-vvv)",
    ),
    stream: bool = typer.Option(
        False,
        "--stream",
        "-s",
        help="Enable real-time LLM output streaming",
    ),
) -> None:
    """Resume an interrupted session.

    Continues a session from where it left off. Useful after:
    - Network disconnection
    - Client crash
    - Manual interruption

    Examples:
        $ obra resume abc123
        $ obra resume abc123 -v
        $ obra resume abc123 -vv --stream
    """
    setup_logging(verbose)

    try:
        from obra.auth import ensure_valid_token, get_current_auth
        from obra.hybrid import HybridOrchestrator

        # Ensure authenticated
        auth = get_current_auth()
        if not auth:
            print_error("Not logged in")
            console.print("\nRun 'obra login' to authenticate.")
            raise typer.Exit(1)

        ensure_valid_token()

        console.print()
        console.print("[bold]Resuming Session[/bold]", style="cyan")
        console.print(f"Session ID: {session_id}")
        console.print()

        # Create observability configuration from CLI flags
        obs_config = ObservabilityConfig(
            verbosity=verbose,
            stream=stream,
            timestamps=True,
        )

        # Create progress emitter for observability
        progress_emitter = ProgressEmitter(obs_config, console)

        # Create orchestrator and resume with progress callback
        def on_progress(action: str, payload: dict) -> None:
            """Progress callback that routes events to ProgressEmitter."""
            # Route events to appropriate ProgressEmitter methods
            if action == "phase_started":
                phase = payload.get("phase", "UNKNOWN")
                progress_emitter.phase_started(phase, payload.get("context"))
            elif action == "phase_completed":
                phase = payload.get("phase", "UNKNOWN")
                duration_ms = payload.get("duration_ms", 0)
                progress_emitter.phase_completed(phase, payload.get("result"), duration_ms)
            elif action == "llm_started":
                purpose = payload.get("purpose", "LLM invocation")
                progress_emitter.llm_started(purpose)
            elif action == "llm_streaming":
                chunk = payload.get("chunk", "")
                progress_emitter.llm_streaming(chunk)
            elif action == "llm_completed":
                summary = payload.get("summary", "")
                tokens = payload.get("tokens", 0)
                progress_emitter.llm_completed(summary, tokens)
            elif action == "item_started":
                item = payload.get("item", {})
                progress_emitter.item_started(item)
            elif action == "item_completed":
                item = payload.get("item", {})
                result = payload.get("result")
                progress_emitter.item_completed(item, result)
            elif action == "error":
                # Error event with verbosity-appropriate detail
                message = payload.get("message", "Unknown error")
                hint = payload.get("hint")
                phase = payload.get("phase")
                affected_items = payload.get("affected_items")
                stack_trace = payload.get("stack_trace")
                raw_response = payload.get("raw_response")
                progress_emitter.error(
                    message, hint, phase, affected_items, stack_trace, raw_response
                )
            elif verbose > 0:
                # Fallback for unknown events at verbose mode
                console.print(f"[dim]{action}[/dim]")

        orchestrator = HybridOrchestrator.from_config(on_progress=on_progress)
        result = orchestrator.resume(session_id)

        # Display result
        console.print()
        action = getattr(result, "action", None)
        if action == "complete" or action is None:
            print_success("Session completed successfully!")
            if hasattr(result, "session_summary") and isinstance(result.session_summary, dict):
                summary = result.session_summary
                console.print(f"\nItems completed: {summary.get('items_completed', 'N/A')}")
                console.print(f"Iterations: {summary.get('total_iterations', 'N/A')}")
                console.print(f"Quality score: {summary.get('quality_score', 'N/A')}")
            elif hasattr(result, "items_completed"):
                console.print(f"\nItems completed: {getattr(result, 'items_completed', 'N/A')}")
                console.print(f"Iterations: {getattr(result, 'total_iterations', 'N/A')}")
                console.print(f"Quality score: {getattr(result, 'quality_score', 'N/A')}")
            # Terse completion footer for LLM handoff
            cwd = Path.cwd()
            console.print(f"\n[dim]Project: {cwd}[/dim]")
            try:
                import subprocess
                git_result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=cwd, capture_output=True, text=True, timeout=5
                )
                if git_result.returncode == 0 and git_result.stdout.strip():
                    lines = git_result.stdout.strip().split('\n')
                    created = sum(1 for l in lines if l.startswith('?') or l.startswith('A'))
                    modified = sum(1 for l in lines if l.startswith('M') or l.startswith(' M'))
                    console.print(f"[dim]Files: {created} created, {modified} modified[/dim]")
            except Exception:
                pass  # Non-git or git unavailable - skip file counts
        elif action == "escalate":
            print_warning("Session requires user decision")
            console.print("\nRun 'obra status' to see details.")
        else:
            console.print(f"Session state: {action}")

    except APIError as e:
        display_obra_error(e, console)
        logger.error(f"API error in resume command: {e}", exc_info=True)
        raise typer.Exit(1)
    except ConfigurationError as e:
        display_obra_error(e, console)
        logger.error(f"Configuration error in resume command: {e}", exc_info=True)
        raise typer.Exit(1)
    except ObraError as e:
        display_obra_error(e, console)
        logger.error(f"Obra error in resume command: {e}", exc_info=True)
        raise typer.Exit(1)
    except Exception as e:
        display_error(e, console)
        logger.exception(f"Unexpected error in resume command: {e}")
        raise typer.Exit(1)


# =============================================================================
# Setup Command (First-Time Onboarding)
# =============================================================================


@app.command(rich_help_panel="User Commands")
@handle_encoding_errors
def setup(
    check: bool = typer.Option(
        False,
        "--check",
        help="Check setup status without prompting",
    ),
    skip_validation: bool = typer.Option(
        False,
        "--skip-validation",
        help="Skip environment validation after authentication",
    ),
    timeout: int = typer.Option(
        300,
        "--timeout",
        "-t",
        help="Timeout in seconds for browser authentication",
    ),
    no_browser: bool = typer.Option(
        False,
        "--no-browser",
        help="Don't open browser, just print URL",
    ),
) -> None:
    """First-time setup with terms acceptance and authentication.

    Complete onboarding flow:
    1. Display and accept Beta Software Agreement
    2. Authenticate via browser OAuth
    3. Register acceptance with server
    4. Validate environment configuration

    Examples:
        $ obra setup
        $ obra setup --check
        $ obra setup --no-browser
        $ obra setup --timeout 600

    Exit Codes:
        0: Setup complete (or --check passed)
        1: Setup incomplete or failed
        2: User declined terms
    """
    try:
        from obra.api import APIClient
        from obra.auth import login_with_browser, save_auth
        from obra.config import (
            TERMS_VERSION,
            PRIVACY_VERSION,
            is_terms_accepted,
            needs_reacceptance,
            save_terms_acceptance,
        )
        from obra.legal import get_terms_summary, get_terms_url, get_privacy_url

        # S1.T6: Implement --check flag
        if check:
            console.print()
            console.print("[bold]Setup Status Check[/bold]", style="cyan")
            console.print()

            # Check terms acceptance
            if is_terms_accepted():
                print_success(f"Terms accepted: version {TERMS_VERSION}")
            elif needs_reacceptance():
                from obra.config import get_terms_acceptance

                old_acceptance = get_terms_acceptance()
                old_version = old_acceptance.get("version", "unknown") if old_acceptance else "unknown"
                print_warning(f"Terms version mismatch: {old_version} → {TERMS_VERSION}")
                console.print("Run 'obra setup' to accept updated terms.")
                raise typer.Exit(1)
            else:
                print_warning("Terms not accepted")
                console.print("Run 'obra setup' to accept terms.")
                raise typer.Exit(1)

            # Check authentication
            from obra.auth import get_current_auth

            auth = get_current_auth()
            if auth:
                print_success(f"Authenticated: {auth.email}")
            else:
                print_warning("Not authenticated")
                console.print("Run 'obra setup' to authenticate.")
                raise typer.Exit(1)

            # Check environment (provider CLIs)
            console.print()
            console.print("[bold]Environment:[/bold]")

            from obra.config import LLM_PROVIDERS, check_provider_status

            provider_count = 0
            for provider_key in LLM_PROVIDERS:
                status = check_provider_status(provider_key)
                provider_name = LLM_PROVIDERS[provider_key].get("name", provider_key)

                if status.installed:
                    console.print(f"  [green]✓[/green] {provider_name} ({status.cli_command})")
                    provider_count += 1
                else:
                    console.print(f"  [red]✗[/red] {provider_name} ({status.cli_command}) - not found")

            console.print()
            if provider_count > 0:
                print_success("Setup complete - all checks passed")
                raise typer.Exit(0)
            else:
                print_warning("No provider CLIs installed")
                console.print("Install at least one: claude, codex, or gemini")
                raise typer.Exit(1)

        # Regular setup flow (not --check mode)
        console.print()
        console.print("[bold]Obra Setup[/bold]", style="cyan")
        console.print()

        # S1.T7: Check if re-acceptance is needed
        if needs_reacceptance():
            from obra.config import get_terms_acceptance

            old_acceptance = get_terms_acceptance()
            old_version = old_acceptance.get("version", "unknown") if old_acceptance else "unknown"
            console.print(f"[yellow]Terms have been updated: v{old_version} → v{TERMS_VERSION}[/yellow]")
            console.print()
            console.print("You must review and accept the updated terms to continue.")
            console.print()

        # S1.T1: Display terms summary
        terms_text = get_terms_summary()

        # Display terms in a box
        console.print("[bold cyan]════════════════════════════════════════════════════════════════════════[/bold cyan]")
        console.print(terms_text.strip())
        console.print("[bold cyan]════════════════════════════════════════════════════════════════════════[/bold cyan]")
        console.print()

        # Prompt for acceptance
        console.print("To accept these terms, type exactly: [bold]I ACCEPT[/bold]")
        console.print("To decline, type anything else or press Ctrl+C")
        console.print()

        # Get user input
        try:
            user_input = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print()
            console.print("[yellow]Setup cancelled by user[/yellow]")
            raise typer.Exit(2)

        # Check acceptance (case-insensitive)
        if user_input.upper() != "I ACCEPT":
            console.print()
            console.print("[yellow]Terms not accepted. Setup cancelled.[/yellow]")
            console.print()
            console.print("You must accept the terms to use Obra.")
            raise typer.Exit(2)

        console.print()
        print_success(f"Terms v{TERMS_VERSION} accepted")
        console.print()

        # Save local acceptance
        save_terms_acceptance()

        # S1.T2: Authenticate via OAuth
        console.print("Opening browser for authentication...")
        console.print()

        try:
            auth_result = login_with_browser(timeout=timeout, auto_open=not no_browser)
            save_auth(auth_result)

            console.print()
            print_success(f"Logged in as: {auth_result.email}")
            if auth_result.display_name:
                console.print(f"Name: {auth_result.display_name}")
            console.print()

        except Exception as e:
            print_error(f"Authentication failed: {e}")
            logger.error(f"OAuth flow failed during setup: {e}", exc_info=True)
            raise typer.Exit(1)

        # S1.T3: Register terms acceptance with server (MANDATORY)
        # Server-side registration is required for legal compliance.
        # Without server confirmation, we cannot prove acceptance in disputes.
        import time

        client = APIClient.from_config()
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                client.log_terms_acceptance(
                    terms_version=TERMS_VERSION,
                    privacy_version=PRIVACY_VERSION,
                )
                print_success("Terms acceptance registered with server")
                console.print()
                break  # Success - exit retry loop
            except Exception as e:
                logger.warning(f"Terms registration attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    console.print(f"[yellow]Server registration failed, retrying ({attempt}/{max_retries})...[/yellow]")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    # All retries exhausted - this is fatal
                    logger.error(f"Terms registration failed after {max_retries} attempts: {e}")
                    print_error("Failed to register terms acceptance with server")
                    console.print()
                    console.print("[red]Server-side registration is required for legal compliance.[/red]")
                    console.print("Please check your internet connection and try again.")
                    console.print()
                    console.print("If the problem persists, contact support at: https://obra.dev/support")
                    raise typer.Exit(1)

        # S1.T4: Run environment validation (unless skipped)
        if not skip_validation:
            console.print("[bold]Validating environment...[/bold]")
            console.print()

            from obra.config import LLM_PROVIDERS, check_provider_status

            provider_count = 0
            for provider_key in LLM_PROVIDERS:
                status = check_provider_status(provider_key)
                provider_name = LLM_PROVIDERS[provider_key].get("name", provider_key)

                if status.installed:
                    console.print(f"  [green]✓[/green] {provider_name} CLI: {status.cli_command}")
                    provider_count += 1
                else:
                    console.print(f"  [dim]○[/dim] {provider_name} CLI: Not installed")

            console.print()

            # Check working directory
            from pathlib import Path

            obra_projects = Path.home() / "obra-projects"
            if obra_projects.exists():
                console.print(f"  [green]✓[/green] Working directory: {obra_projects}")
            else:
                console.print(f"  [yellow]○[/yellow] Working directory: {obra_projects} (will be created)")

            console.print()

            if provider_count == 0:
                print_warning("No provider CLIs installed")
                console.print()
                console.print("Obra requires at least one LLM provider CLI:")
                console.print("  - Claude Code: https://claude.com/download")
                console.print("  - OpenAI Codex: https://openai.com/codex")
                console.print("  - Gemini CLI: https://ai.google.dev/gemini-api/docs/cli")
                console.print()
                console.print("Install one and run 'obra setup --check' to verify.")
                console.print()

        # S1.T5: Display setup completion with copy-paste prompt
        console.print("[bold cyan]═══════════════════════════════════════════════════════════════════════[/bold cyan]")
        console.print()
        console.print("[bold green]Setup complete![/bold green]")
        console.print()
        console.print("[bold cyan]═══════════════════════════════════════════════════════════════════════[/bold cyan]")
        console.print()
        console.print("[bold]  USING OBRA WITH YOUR AI ASSISTANT[/bold]")
        console.print()
        console.print("    Copy this prompt to your AI assistant (Claude Code, Cursor, Gemini):")
        console.print()
        console.print("    [cyan]┌─────────────────────────────────────────────────────────────────┐[/cyan]")
        console.print("    [cyan]│[/cyan]                                                                 [cyan]│[/cyan]")
        console.print("    [cyan]│[/cyan]  I want to use Obra. Run `obra` and `obra briefing` to get     [cyan]│[/cyan]")
        console.print("    [cyan]│[/cyan]  oriented. Then help me prepare structured input and invoke    [cyan]│[/cyan]")
        console.print("    [cyan]│[/cyan]  Obra to execute my objective.                                 [cyan]│[/cyan]")
        console.print("    [cyan]│[/cyan]                                                                 [cyan]│[/cyan]")
        console.print("    [cyan]└─────────────────────────────────────────────────────────────────┘[/cyan]")
        console.print()
        console.print("    Your AI will then know exactly how to prepare high-quality input")
        console.print("    for Obra's optimal performance.")
        console.print()
        console.print("[bold cyan]═══════════════════════════════════════════════════════════════════════[/bold cyan]")
        console.print()
        console.print("[bold]Next steps:[/bold]")
        console.print()
        console.print("  1. Give your AI the prompt above, then describe what you want to build")
        console.print()
        console.print("  2. Or start directly (if you know what you're doing):")
        console.print('     [cyan]$ obra run "Add user authentication" --stream[/cyan]')
        console.print()
        console.print("  3. Check session status anytime:")
        console.print("     [cyan]$ obra status[/cyan]")
        console.print()
        console.print("  4. Explore configuration:")
        console.print("     [cyan]$ obra config[/cyan]")
        console.print()
        console.print("[bold cyan]═══════════════════════════════════════════════════════════════════════[/bold cyan]")
        console.print()

    except typer.Exit:
        # Re-raise typer.Exit without catching it as an error
        raise
    except ConfigurationError as e:
        display_obra_error(e, console)
        logger.error(f"Configuration error in setup command: {e}", exc_info=True)
        raise typer.Exit(1)
    except ObraError as e:
        display_obra_error(e, console)
        logger.error(f"Obra error in setup command: {e}", exc_info=True)
        raise typer.Exit(1)
    except Exception as e:
        display_error(e, console)
        logger.exception(f"Unexpected error in setup command: {e}")
        raise typer.Exit(1)


# =============================================================================
# AI Assistant Onboarding Commands
# =============================================================================


@app.command(
    rich_help_panel="AI Operator Resources",
    help="★ Operating guide, blueprint, and protocol for AI assistants",
)
@handle_encoding_errors
def briefing(
    blueprint: bool = typer.Option(
        False,
        "--blueprint",
        help="Quick blueprint reference (condensed checklist format)",
    ),
    protocol: bool = typer.Option(
        False,
        "--protocol",
        help="Full autonomous execution protocol (11 behaviors detailed)",
    ),
    questions: bool = typer.Option(
        False,
        "--questions",
        help="Detailed question patterns by category",
    ),
    full: bool = typer.Option(
        False,
        "--full",
        help="Complete LLM onboarding guide (1700+ lines)",
    ),
    path: bool = typer.Option(
        False,
        "--path",
        help="Show file path for deep reading",
    ),
) -> None:
    """Operating guide for AI assistants using Obra.

    Provides blueprint, protocol, and best practices for LLMs (Claude Code,
    Cursor, Gemini) helping users with Obra.

    Default output (no flags) includes:
    - Obra description
    - Input blueprint inline
    - 11 autonomous execution behaviors (names)
    - Subcommand reference

    Examples:
        $ obra briefing                  # Default: blueprint inline
        $ obra briefing --blueprint      # Quick reference
        $ obra briefing --protocol       # Full 11 behaviors
        $ obra briefing --questions      # Question patterns
        $ obra briefing --full           # Complete guide
        $ obra briefing --path           # Show file location

    Exit Codes:
        0: Always (informational command)
    """
    try:
        import importlib.resources as pkg_resources
        from pathlib import Path

        # Locate the LLM_ONBOARDING.md file in the installed package
        try:
            # Python 3.9+ approach
            if hasattr(pkg_resources, 'files'):
                obra_package = pkg_resources.files('obra')
                onboarding_file = obra_package / '.obra' / 'LLM_ONBOARDING.md'
                file_path = str(onboarding_file)

                # Read the file content
                if hasattr(onboarding_file, 'read_text'):
                    content = onboarding_file.read_text(encoding='utf-8')
                else:
                    # Fallback for older Python versions
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
            else:
                # Fallback for Python < 3.9
                import pkg_resources as old_pkg
                file_path = old_pkg.resource_filename('obra', '.obra/LLM_ONBOARDING.md')
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
        except Exception as e:
            # Development mode fallback - look in source tree
            dev_path = Path(__file__).parent / '.obra' / 'LLM_ONBOARDING.md'
            if dev_path.exists():
                file_path = str(dev_path)
                content = dev_path.read_text(encoding='utf-8')
            else:
                print_error(f"Could not locate LLM_ONBOARDING.md: {e}")
                raise typer.Exit(1)

        # Handle --path flag: just show the file location
        if path:
            console.print()
            console.print(f"[bold]LLM Onboarding Guide Location:[/bold]")
            console.print()
            console.print(f"  {file_path}")
            console.print()
            console.print("Use this path to read the complete guide in your editor or tools.")
            console.print()
            raise typer.Exit(0)

        # Handle --full flag: output entire file
        if full:
            console.print(content)
            raise typer.Exit(0)

        # Handle --blueprint flag: condensed checklist format
        if blueprint:
            console.print()
            console.print("[bold]OBRA INPUT BLUEPRINT (Quick Reference)[/bold]")
            console.print("[cyan]══════════════════════════════════════[/cyan]")
            console.print()
            console.print("First: Run `obra` to see all commands.")
            console.print()
            console.print("[bold]REQUIRED:[/bold]")
            console.print("  □ Objective      What are we building/fixing?")
            console.print("  □ Tech Stack     Languages, frameworks, databases")
            console.print("  □ Features       List of capabilities needed")
            console.print()
            console.print("[bold]RECOMMENDED:[/bold]")
            console.print("  □ Constraints    Performance, security, compliance")
            console.print("  □ Integrations   External services, APIs, existing systems")
            console.print("  □ Anti-patterns  What to avoid")
            console.print()
            console.print("Trivial tasks (typos, single-line fixes) → invoke directly")
            console.print("Design decisions required → gather requirements first")
            console.print()
            console.print("[bold]Example:[/bold]")
            console.print('  obra "E-commerce: React + Node + MongoDB. Features: catalog, cart,')
            console.print('  Stripe. Constraints: <500ms, OWASP. Anti-patterns: no Redux." --stream')
            console.print()
            raise typer.Exit(0)

        # Handle --protocol flag: full 11 behaviors with descriptions
        if protocol:
            _display_protocol_full(content)
            raise typer.Exit(0)

        # Handle --questions flag: question patterns by category
        if questions:
            _display_question_patterns(content)
            raise typer.Exit(0)

        # Default output: Process-first with conversation example
        console.print()
        console.print("[bold]FOR HUMANS: Copy this prompt to your AI assistant:[/bold]")
        console.print()
        console.print("[cyan]┌─────────────────────────────────────────────────────────────────┐[/cyan]")
        console.print("[cyan]│[/cyan]                                                                 [cyan]│[/cyan]")
        console.print("[cyan]│[/cyan]  I want to use Obra. Run `obra` and `obra briefing` to get     [cyan]│[/cyan]")
        console.print("[cyan]│[/cyan]  oriented. Then help me prepare structured input and invoke    [cyan]│[/cyan]")
        console.print("[cyan]│[/cyan]  Obra to execute my objective.                                 [cyan]│[/cyan]")
        console.print("[cyan]│[/cyan]                                                                 [cyan]│[/cyan]")
        console.print("[cyan]└─────────────────────────────────────────────────────────────────┘[/cyan]")
        console.print()
        console.print("[cyan]══════════════════════════════════════════════════════════════════════[/cyan]")
        console.print("[bold cyan]           OBRA OPERATING GUIDE FOR AI ASSISTANTS[/bold cyan]")
        console.print("[cyan]══════════════════════════════════════════════════════════════════════[/cyan]")
        console.print()
        console.print("Obra executes development tasks autonomously. Your job: gather requirements")
        console.print("through conversation, then invoke Obra with structured input.")
        console.print()
        console.print("Run `obra` to see all commands. Key: run, status, resume, doctor")
        console.print()
        console.print("[bold]YOUR PROCESS[/bold]")
        console.print("[cyan]────────────[/cyan]")
        console.print("1. Ask what they're building (get specific, not vague)")
        console.print("2. Check project files for tech stack (don't ask what you can infer)")
        console.print("3. Clarify features, constraints, anti-patterns through conversation")
        console.print("4. Summarize into one structured Obra input")
        console.print()
        console.print("[bold]EXAMPLE CONVERSATION[/bold]")
        console.print("[cyan]────────────────────[/cyan]")
        console.print('  User: "Build me an API"')
        console.print('  You:  "What kind? REST, GraphQL? What\'s it for?"')
        console.print('  User: "REST for user management"')
        console.print('  You:  "I see FastAPI in your project. Auth approach?"')
        console.print('  User: "JWT with refresh tokens"')
        console.print('  You:  "Deployment target? Any existing services to integrate?"')
        console.print()
        console.print("  [bold]→ INVOKE:[/bold]")
        console.print('    obra "User management REST API: FastAPI + PostgreSQL.')
        console.print('    JWT auth with refresh tokens, CRUD operations, role-based access.')
        console.print('    Docker Compose deployment. Integrate with auth-service:8000." --stream')
        console.print()
        console.print("[bold]CHECKLIST (what to cover)[/bold]")
        console.print("[cyan]─────────────────────────[/cyan]")
        console.print("Required: Objective, Tech Stack, Features")
        console.print("Optional: Constraints, Integrations, Anti-patterns")
        console.print()
        console.print("Trivial tasks (typos, single-line fixes) → invoke Obra directly")
        console.print()
        console.print("[bold]ADVANCED FLAGS (optional)[/bold]")
        console.print("[cyan]──────────────────────────[/cyan]")
        console.print("Override model/provider for specific tasks:")
        console.print()
        console.print("  --model opus                    Use specific model")
        console.print("  --impl-provider google          Use specific provider")
        console.print("  --thinking-level high           Set reasoning depth")
        console.print()
        console.print("[dim]Run `obra run --help` for complete flag reference[/dim]")
        console.print()
        console.print("[bold]WHILE OBRA RUNS[/bold]")
        console.print("[cyan]───────────────[/cyan]")
        console.print("Monitor progress, validate success, escalate if stuck.")
        console.print("See `--protocol` for full 11 autonomous behaviors.")
        console.print()
        console.print("[cyan]──────────────────────────────────────────────────────────────────────[/cyan]")
        console.print("obra briefing --blueprint   Quick checklist")
        console.print("obra briefing --questions   Question patterns (detailed)")
        console.print("obra briefing --protocol    11 autonomous behaviors")
        console.print("obra briefing --full        Complete guide (includes advanced flags reference)")
        console.print("[cyan]══════════════════════════════════════════════════════════════════════[/cyan]")
        console.print()

    except typer.Exit:
        # Clean exit - don't treat as error
        raise
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Let encoding errors bubble up to @handle_encoding_errors decorator
        raise
    except Exception as e:
        display_error(e, console)
        logger.exception(f"Unexpected error in briefing command: {e}")
        raise typer.Exit(1)


def _display_protocol_full(content: str) -> None:
    """Display the full autonomous execution protocol with all 11 behaviors.

    Args:
        content: Full content of LLM_ONBOARDING.md
    """
    # Extract the Autonomous Operation Protocol section
    lines = content.split('\n')
    in_protocol_section = False
    protocol_lines = []

    for i, line in enumerate(lines):
        if line.strip() == '## Autonomous Operation Protocol':
            in_protocol_section = True
            continue

        if in_protocol_section:
            # Stop at the next ## heading
            if line.startswith('## ') and not line.startswith('### '):
                break
            protocol_lines.append(line)

    # Display the extracted section
    console.print()
    console.print("[bold cyan]AUTONOMOUS OPERATION PROTOCOL[/bold cyan]")
    console.print()
    console.print('\n'.join(protocol_lines))
    console.print()


def _display_question_patterns(content: str) -> None:
    """Display question patterns by category.

    Args:
        content: Full content of LLM_ONBOARDING.md
    """
    # Extract the Question Patterns section
    lines = content.split('\n')
    in_patterns_section = False
    patterns_lines = []

    for line in lines:
        if '## Question Patterns' in line or '## The Questions to Ask' in line:
            in_patterns_section = True
            continue

        if in_patterns_section:
            # Stop at the next ## heading
            if line.startswith('## ') and not line.startswith('### '):
                break
            patterns_lines.append(line)

    # Display the extracted section
    console.print()
    console.print("[bold cyan]QUESTION PATTERNS FOR GATHERING REQUIREMENTS[/bold cyan]")
    console.print()
    console.print('\n'.join(patterns_lines))
    console.print()


# =============================================================================
# Authentication Commands
# =============================================================================


@app.command(rich_help_panel="User Commands")
@handle_encoding_errors
def login(
    timeout: int = typer.Option(
        300,
        "--timeout",
        "-t",
        help="Timeout in seconds for browser authentication",
    ),
    no_browser: bool = typer.Option(
        False,
        "--no-browser",
        help="Don't open browser, just print URL",
    ),
) -> None:
    """Authenticate with Obra.

    Opens your browser to sign in with Google or GitHub.
    After successful authentication, your session is saved locally.

    Examples:
        $ obra login
        $ obra login --no-browser
        $ obra login --timeout 600
    """
    try:
        from obra.auth import login_with_browser, save_auth

        console.print()
        console.print("[bold]Obra Login[/bold]", style="cyan")
        console.print()

        if no_browser:
            console.print("Opening authentication URL...")
            console.print("Copy the URL below and open it in your browser:")
        else:
            console.print("Opening browser for authentication...")

        result = login_with_browser(timeout=timeout, auto_open=not no_browser)

        # Save the authentication
        save_auth(result)

        console.print()
        print_success(f"Logged in as: {result.email}")
        if result.display_name:
            console.print(f"Name: {result.display_name}")

        # Display next steps
        console.print()
        console.print("[bold]Next Steps[/bold]", style="cyan")
        console.print()
        console.print("1. [cyan]Validate your environment[/cyan]")
        console.print("   $ obra config --validate")
        console.print()
        console.print("2. [cyan]Explore documentation[/cyan]")
        console.print("   $ obra docs")
        console.print()
        console.print("3. [cyan]Start your first task[/cyan]")
        console.print('   $ obra run "Add user authentication"')
        console.print()
        console.print("4. [cyan]Check session status[/cyan]")
        console.print("   $ obra status")
        console.print()

    except AuthenticationError as e:
        display_obra_error(e, console)
        logger.error(f"Authentication error in login command: {e}", exc_info=True)
        raise typer.Exit(1)
    except APIError as e:
        display_obra_error(e, console)
        logger.error(f"API error in login command: {e}", exc_info=True)
        raise typer.Exit(1)
    except ConfigurationError as e:
        display_obra_error(e, console)
        logger.error(f"Configuration error in login command: {e}", exc_info=True)
        raise typer.Exit(1)
    except ObraError as e:
        display_obra_error(e, console)
        logger.error(f"Obra error in login command: {e}", exc_info=True)
        raise typer.Exit(1)
    except Exception as e:
        display_error(e, console)
        logger.exception(f"Unexpected error in login command: {e}")
        raise typer.Exit(1)


@app.command(rich_help_panel="User Commands")
@handle_encoding_errors
def logout() -> None:
    """Log out and clear stored credentials.

    Removes your authentication token from the local config.
    You'll need to run 'obra login' again to use Obra.

    Example:
        $ obra logout
    """
    try:
        from obra.auth import clear_auth, get_current_auth

        auth = get_current_auth()
        if not auth:
            print_info("Not currently logged in")
            return

        email = auth.email
        clear_auth()

        console.print()
        print_success(f"Logged out: {email}")
        console.print("\nRun 'obra login' to sign in again.")

    except ConfigurationError as e:
        display_obra_error(e, console)
        logger.error(f"Configuration error in logout command: {e}", exc_info=True)
        raise typer.Exit(1)
    except ObraError as e:
        display_obra_error(e, console)
        logger.error(f"Obra error in logout command: {e}", exc_info=True)
        raise typer.Exit(1)
    except OSError as e:
        print_error(f"Failed to clear authentication: {e}")
        logger.error(f"File I/O error in logout command: {e}", exc_info=True)
        raise typer.Exit(1)
    except Exception as e:
        display_error(e, console)
        logger.exception(f"Unexpected error in logout command: {e}")
        raise typer.Exit(1)


@app.command(rich_help_panel="User Commands")
@handle_encoding_errors
def whoami() -> None:
    """Show current authentication status.

    Displays the currently authenticated user and token status.

    Example:
        $ obra whoami
    """
    try:
        from obra.auth import get_current_auth
        from obra.config import load_config

        auth = get_current_auth()

        console.print()
        if not auth:
            print_info("Not logged in")
            console.print("\nRun 'obra login' to authenticate.")
            return

        console.print("[bold]Current User[/bold]", style="cyan")
        console.print()

        table = Table(show_header=False, box=None)
        table.add_column("Field", style="dim")
        table.add_column("Value")

        table.add_row("Email", auth.email)
        if auth.display_name:
            table.add_row("Name", auth.display_name)
        table.add_row("Provider", auth.auth_provider)
        table.add_row("User ID", auth.firebase_uid[:16] + "...")

        console.print(table)

        # Check token status
        config = load_config()
        token_expires = config.get("token_expires_at")
        if token_expires:
            from datetime import datetime

            try:
                expires_dt = datetime.fromisoformat(token_expires.replace("Z", "+00:00"))
                now = datetime.now(UTC)
                if expires_dt > now:
                    remaining = expires_dt - now
                    minutes = int(remaining.total_seconds() / 60)
                    console.print(f"\n[dim]Token expires in {minutes} minutes[/dim]")
                else:
                    console.print("\n[yellow]Token expired - will auto-refresh on next request[/yellow]")
            except ValueError:
                pass

    except ConfigurationError as e:
        display_obra_error(e, console)
        logger.error(f"Configuration error in whoami command: {e}", exc_info=True)
        raise typer.Exit(1)
    except ObraError as e:
        display_obra_error(e, console)
        logger.error(f"Obra error in whoami command: {e}", exc_info=True)
        raise typer.Exit(1)
    except Exception as e:
        display_error(e, console)
        logger.exception(f"Unexpected error in whoami command: {e}")
        raise typer.Exit(1)


# =============================================================================
# Configuration Commands
# =============================================================================


def _run_config_validation(json_output: bool = False) -> None:
    """Run configuration validation and display results.

    S4.T2: Validates provider CLIs and configuration settings.

    Args:
        json_output: If True, output JSON instead of human-readable format
    """
    import json

    from obra.config import (
        CONFIG_PATH,
        LLM_PROVIDERS,
        check_provider_status,
        load_config,
    )

    # Check all providers
    provider_results = {}
    for provider_key in LLM_PROVIDERS:
        status = check_provider_status(provider_key)
        provider_results[provider_key] = {
            "name": LLM_PROVIDERS[provider_key].get("name", provider_key),
            "installed": status.installed,
            "cli_command": status.cli_command,
            "install_hint": status.install_hint,
            "docs_url": status.docs_url,
        }

    # Load configuration
    config_data = load_config()
    config_exists = bool(config_data)

    # Overall status
    all_installed = all(p["installed"] for p in provider_results.values())

    if json_output:
        # S4.T4: JSON output structure
        output = {
            "status": "valid" if (all_installed and config_exists) else "issues_found",
            "providers": provider_results,
            "configuration": {
                "path": str(CONFIG_PATH),
                "exists": config_exists,
                "keys_present": list(config_data.keys()) if config_data else [],
            },
        }
        console.print(json.dumps(output, indent=2))
    else:
        # S4.T3: Human-readable output with colors and icons
        _display_validation_human(provider_results, config_exists, str(CONFIG_PATH))


def _display_validation_human(
    provider_results: dict,
    config_exists: bool,
    config_path: str,
) -> None:
    """Display validation results in human-readable format with colors and icons.

    S4.T3: Display validation with ✓/✗ icons and colored output.

    Args:
        provider_results: Provider validation results
        config_exists: Whether config file exists
        config_path: Path to config file
    """
    console.print()
    console.print("[bold]Configuration Validation[/bold]", style="cyan")
    console.print()

    # Provider CLI checks
    console.print("[bold]Provider CLIs:[/bold]")
    for provider_key, result in provider_results.items():
        if result["installed"]:
            icon = "[green]✓[/green]"
            status_text = f"[green]{result['cli_command']} installed[/green]"
        else:
            icon = "[red]✗[/red]"
            status_text = f"[red]{result['cli_command']} not found[/red]"
            if result["install_hint"]:
                status_text += f"\n    [dim]{result['install_hint']}[/dim]"

        console.print(f"  {icon} {result['name']}: {status_text}")

    console.print()

    # Configuration file check
    console.print("[bold]Configuration:[/bold]")
    if config_exists:
        icon = "[green]✓[/green]"
        status_text = f"[green]Config found at {config_path}[/green]"
    else:
        icon = "[yellow]⚠[/yellow]"
        status_text = "[yellow]No config file (using defaults)[/yellow]"

    console.print(f"  {icon} {status_text}")
    console.print()

    # Overall status
    all_installed = all(p["installed"] for p in provider_results.values())
    if all_installed and config_exists:
        print_success("All checks passed!")
    elif all_installed:
        print_warning("Providers installed but no config file found (using defaults)")
    else:
        print_warning("Some provider CLIs are not installed")
        console.print("\n[dim]Tip: Install the providers you plan to use with obra run --impl-provider[/dim]")


@app.command(rich_help_panel="User Commands")
@handle_encoding_errors
def config(
    show: bool = typer.Option(False, "--show", "-s", help="Show current configuration"),
    get_path: str | None = typer.Option(None, "--get", help="Get value for a specific config path"),
    set_path: str | None = typer.Option(None, "--set", help="Set a specific config path"),
    set_value: str | None = typer.Argument(None, help="Value to set when using --set"),
    reset: bool = typer.Option(False, "--reset", help="Reset configuration to defaults"),
    validate: bool = typer.Option(False, "--validate", help="Validate provider CLIs and configuration"),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON for supported commands"),
    confirm: bool = typer.Option(False, "--confirm", help="Show config after changes"),
    scope: str = typer.Option("local", "--scope", help="Config scope: local or server"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show configuration sources (where each value comes from)"),
) -> None:
    """Manage Obra configuration.

    Without options, launches the interactive configuration TUI.
    Use --show to display current configuration.
    Use --reset to reset to default values.
    Use --validate to check provider CLIs and configuration.
    Use --json with --show/--get/--validate for machine-readable output.
    Use --confirm with --set to reprint configuration after changes.
    Use --verbose to show where each configuration value comes from.

    Examples:
        $ obra config
        $ obra config --show
        $ obra config --show --json
        $ obra config --get llm.orchestrator.provider
        $ obra config --set llm.orchestrator.provider openai --confirm
        $ obra config --show --verbose
        $ obra config --reset
        $ obra config --validate
        $ obra config --validate --json
    """
    try:
        import copy
        import json

        from obra.config import CONFIG_PATH, load_config, save_config
        from obra.config.explorer.descriptions import (
            CONFIG_DEFAULTS,
            get_all_paths,
            get_choices,
            get_description,
            get_default,
            is_sensitive,
        )

        def _emit_error(message: str, detail: str = "") -> None:
            prefix = "Error: "
            print(f"{prefix}{message}", file=sys.stderr)
            if detail:
                print(detail, file=sys.stderr)

        def _get_nested_value(config: dict[str, object], path: str) -> object | None:
            parts = path.split(".")
            current: object = config
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
            return current

        def _set_nested_value(config: dict[str, object], path: str, value: object) -> None:
            parts = path.split(".")
            current: dict[str, object] = config
            for part in parts[:-1]:
                if part not in current or not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]  # type: ignore[assignment]
            current[parts[-1]] = value

        def _flatten_config(data: dict[str, object], prefix: str = "") -> dict[str, object]:
            flat: dict[str, object] = {}
            for key, value in data.items():
                path = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    flat.update(_flatten_config(value, path))
                else:
                    flat[path] = value
            return flat

        def _apply_defaults(config_data: dict[str, object]) -> dict[str, object]:
            merged = copy.deepcopy(config_data)
            for path, default_value in CONFIG_DEFAULTS.items():
                if _get_nested_value(merged, path) is None:
                    _set_nested_value(merged, path, default_value)
            return merged

        def _format_human_value(value: object) -> str:
            if value is None:
                return "null"
            if isinstance(value, bool):
                return "true" if value else "false"
            return str(value)

        def _redact_value(path: str, value: object) -> object:
            if is_sensitive(path):
                return "***"
            return value

        def _redact_config(data: dict[str, object]) -> dict[str, object]:
            redacted: dict[str, object] = {}
            for path, value in _flatten_config(data).items():
                _set_nested_value(redacted, path, _redact_value(path, value))
            return redacted

        def _parse_value(raw: str) -> object:
            stripped = raw.strip()
            if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in ("'", '"'):
                return stripped[1:-1]
            lower = stripped.lower()
            if lower == "true":
                return True
            if lower == "false":
                return False
            if re.fullmatch(r"-?\d+", stripped):
                return int(stripped)
            if re.fullmatch(r"-?\d+\.\d+", stripped):
                return float(stripped)
            return stripped

        def _infer_expected_type(path: str, current_config: dict[str, object]) -> type | None:
            existing = _get_nested_value(current_config, path)
            if isinstance(existing, (bool, int, float)):
                return type(existing)
            default_value = get_default(path)
            if isinstance(default_value, (bool, int, float)):
                return type(default_value)
            return None

        def _path_has_children(path: str) -> bool:
            prefix = f"{path}."
            return any(other.startswith(prefix) for other in get_all_paths())

        action_flags = [validate, reset, show, bool(get_path), bool(set_path)]
        if sum(1 for flag in action_flags if flag) > 1:
            _emit_error("Only one of --show, --get, --set, --reset, or --validate may be used at a time")
            raise typer.Exit(2)

        if confirm and not set_path:
            _emit_error("--confirm is only valid with --set")
            raise typer.Exit(2)

        if set_path and json_output and not confirm:
            _emit_error("--set --json requires --confirm")
            raise typer.Exit(2)

        if json_output and not (validate or show or get_path or (set_path and confirm)):
            _emit_error("--json is only valid with --show, --get, --validate, or --set --confirm")
            raise typer.Exit(2)

        if scope not in ("local", "server"):
            _emit_error("Invalid scope. Use --scope local or --scope server")
            raise typer.Exit(2)

        if set_path and set_value is None:
            _emit_error("Missing value for --set")
            raise typer.Exit(2)

        # S4.T1: Handle --validate flag
        if validate:
            _run_config_validation(json_output=json_output)
            return

        if reset:
            # Confirm reset
            # C14: Check for non-interactive mode before prompting
            if not sys.stdin.isatty():
                # Non-interactive mode: default to not resetting (safe default)
                console.print("Non-interactive mode: skipping reset confirmation (defaulting to cancel)")
                return

            confirm = typer.confirm("Reset configuration to defaults?")
            if not confirm:
                console.print("Cancelled")
                return

            # Reset by saving minimal config
            save_config({})
            print_success("Configuration reset to defaults")
            return

        if show or get_path or set_path:
            def _load_server_config() -> dict[str, object]:
                from obra.api import APIClient

                api_client = APIClient.from_config()
                server_config = api_client.get_user_config()
                return server_config.get("resolved", {})

            def _load_scope_config() -> tuple[dict[str, object], bool]:
                if scope == "server":
                    return _load_server_config(), True

                config_data = load_config()
                config_exists = CONFIG_PATH.exists()
                effective = _apply_defaults(config_data)
                if not config_exists:
                    print("info: local config not found; using defaults", file=sys.stderr)
                return effective, config_exists

            def _print_show(config_data: dict[str, object]) -> None:
                redacted = _redact_config(config_data)
                if json_output:
                    payload = {"scope": scope, "data": redacted}
                    print(json.dumps(payload, ensure_ascii=True))
                    return

                for path, value in sorted(_flatten_config(redacted).items()):
                    print(f"{path}: {_format_human_value(value)}")

            if show:
                config_data, _ = _load_scope_config()
                _print_show(config_data)
                return

            if get_path:
                if get_description(get_path) is None:
                    _emit_error(f"Unknown config path '{get_path}'")
                    raise typer.Exit(1)

                config_data, _ = _load_scope_config()
                value = _get_nested_value(config_data, get_path)
                value = _redact_value(get_path, value)

                if json_output:
                    payload = {"scope": scope, "data": {get_path: value}}
                    print(json.dumps(payload, ensure_ascii=True))
                else:
                    print(_format_human_value(value))
                return

            if set_path:
                if get_description(set_path) is None:
                    _emit_error(f"Unknown config path '{set_path}'")
                    raise typer.Exit(1)

                if _path_has_children(set_path):
                    _emit_error(f"Cannot set non-leaf config path '{set_path}'")
                    raise typer.Exit(1)

                config_data, _ = _load_scope_config()
                raw_value = set_value or ""
                choices = get_choices(set_path, config_data)
                if choices and raw_value not in choices:
                    _emit_error(
                        f"Invalid value '{raw_value}' for {set_path}",
                        f"Valid choices: {', '.join(choices)}",
                    )
                    raise typer.Exit(1)

                parsed_value = _parse_value(raw_value)
                expected_type = _infer_expected_type(set_path, config_data)
                if expected_type is bool and not isinstance(parsed_value, bool):
                    _emit_error(f"Expected boolean for {set_path}, got '{raw_value}'")
                    raise typer.Exit(1)
                if expected_type is int and not isinstance(parsed_value, int):
                    _emit_error(f"Expected integer for {set_path}, got '{raw_value}'")
                    raise typer.Exit(1)
                if expected_type is float and not isinstance(parsed_value, (int, float)):
                    _emit_error(f"Expected number for {set_path}, got '{raw_value}'")
                    raise typer.Exit(1)

                if scope == "server":
                    from obra.api import APIClient

                    api_client = APIClient.from_config()
                    server_config = api_client.update_user_config(overrides={set_path: parsed_value})
                    config_data = server_config.get("resolved", {})
                else:
                    local_config = load_config()
                    _set_nested_value(local_config, set_path, parsed_value)
                    save_config(local_config)
                    config_data = _apply_defaults(local_config)

                if not json_output:
                    print_success(f"Set {set_path} = {raw_value}")
                if confirm:
                    if json_output:
                        payload = {"scope": scope, "data": _redact_config(config_data)}
                        print(json.dumps(payload, ensure_ascii=True))
                    else:
                        _print_show(config_data)
                return

        # Launch config explorer TUI
        try:
            from obra.config.explorer import run_explorer

            # Load local config to pass to explorer
            local_config = load_config()

            # Try to get server config if authenticated
            server_config: dict = {}
            api_client = None
            try:
                from obra.api import APIClient

                api_client = APIClient.from_config()
                config_data = api_client.get_user_config()
                server_config = config_data.get("resolved", {})
                server_config["_preset"] = config_data.get("preset", "unknown")
            except (APIError, ConfigurationError, ConnectionError):
                # Server unavailable or not authenticated - offline mode
                logger.debug("Server config unavailable, using offline mode")
            except Exception as e:
                # Log unexpected errors but continue in offline mode
                logger.warning(f"Unexpected error fetching server config: {e}")

            run_explorer(
                local_config=local_config,
                server_config=server_config,
                api_client=api_client,
            )
        except ImportError:
            print_error("Config explorer not available")
            console.print("\nUse 'obra config --show' to view current configuration.")
            console.print("Edit ~/.obra/client-config.yaml directly to make changes.")
            raise typer.Exit(1)

    except ConfigurationError as e:
        display_obra_error(e, console)
        logger.error(f"Configuration error in config command: {e}", exc_info=True)
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except ObraError as e:
        display_obra_error(e, console)
        logger.error(f"Obra error in config command: {e}", exc_info=True)
        raise typer.Exit(1)
    except OSError as e:
        print_error(f"Failed to access configuration file: {e}")
        logger.error(f"File I/O error in config command: {e}", exc_info=True)
        raise typer.Exit(1)
    except Exception as e:
        display_error(e, console)
        logger.exception(f"Unexpected error in config command: {e}")
        raise typer.Exit(1)


# =============================================================================
# Version Command
# =============================================================================


@app.command(rich_help_panel="User Commands")
@handle_encoding_errors
def version(
    check_server: bool = typer.Option(
        False,
        "--check",
        "-c",
        help="Check server version compatibility",
    ),
) -> None:
    """Show version information.

    Displays the client version and optionally checks server compatibility.

    Examples:
        $ obra version
        $ obra version --check
    """
    console.print()
    console.print(f"[bold]Obra[/bold] v{__version__}")
    console.print()

    # Show Python version
    console.print(f"Python: {sys.version.split()[0]}")

    # Show platform
    import platform

    console.print(f"Platform: {platform.system()} {platform.release()}")

    if check_server:
        console.print()
        console.print("Checking server compatibility...")

        try:
            from obra.api import APIClient
            from obra.config import get_api_base_url

            # Create unauthenticated client for version check
            client = APIClient(base_url=get_api_base_url())

            try:
                server_info = client.get_version()

                console.print()
                console.print("[bold]Server Information[/bold]", style="cyan")

                table = Table(show_header=False, box=None)
                table.add_column("Field", style="dim")
                table.add_column("Value")

                table.add_row("Server Version", server_info.get("version", "N/A"))
                table.add_row("API Version", server_info.get("api_version", "N/A"))
                table.add_row("Status", server_info.get("status", "N/A"))

                console.print(table)

                # Check compatibility
                compatible = server_info.get("compatible", True)
                min_client = server_info.get("min_client_version", "0.0.0")

                console.print()
                if compatible:
                    print_success("Client is compatible with server")
                else:
                    print_warning(f"Client update required (minimum: {min_client})")
                    console.print("\nRun: pip install --upgrade obra")

            except APIError as e:
                if e.status_code == 0:
                    print_error("Cannot connect to server")
                    console.print("\nCheck your network connection.")
                    logger.error("Connection error in version check", exc_info=True)
                else:
                    print_error(f"Server error: {e}")
                    logger.error(f"API error in version check: {e}", exc_info=True)
            except ConnectionError as e:
                print_error("Cannot connect to server")
                console.print("\nCheck your network connection.")
                logger.error(f"Connection error in version check: {e}", exc_info=True)

        except ConfigurationError as e:
            print_error(f"Configuration error: {e}")
            logger.error(f"Configuration error in version check: {e}", exc_info=True)
        except ObraError as e:
            print_error(f"Version check failed: {e}")
            logger.error(f"Obra error in version check: {e}", exc_info=True)
        except Exception as e:
            print_error(f"Unexpected error during version check: {e}")
            logger.exception(f"Unexpected error checking server version: {e}")


# =============================================================================
# Documentation Commands
# =============================================================================


@app.command(rich_help_panel="User Commands")
@handle_encoding_errors
def docs(
    llm: bool = typer.Option(
        False,
        "--llm",
        help="Show path to LLM_ONBOARDING.md for LLM operators",
    ),
) -> None:
    """Access local Obra documentation.

    Displays paths to documentation files shipped with the package.
    Use --llm flag to show the LLM operator guide specifically.

    Examples:
        $ obra docs
        $ obra docs --llm
    """
    package_root = Path(__file__).parent

    if llm:
        # Show path to LLM_ONBOARDING.md
        llm_onboarding_path = package_root / ".obra" / "LLM_ONBOARDING.md"

        console.print()
        console.print("[bold]LLM Operator Guide[/bold]", style="cyan")
        console.print()
        console.print(f"Path: {llm_onboarding_path}")
        console.print()
        console.print("[dim]Use 'cat' or your text editor to read this file.[/dim]")
    else:
        # Show paths to local documentation
        readme_path = package_root / "README.md"
        llm_onboarding_path = package_root / ".obra" / "LLM_ONBOARDING.md"

        console.print()
        console.print("[bold]Obra Documentation (Local)[/bold]", style="cyan")
        console.print()
        console.print("[bold]Package Documentation:[/bold]")
        console.print(f"  README:           {readme_path}")
        console.print()
        console.print("[bold]LLM Operator Guide:[/bold]")
        console.print(f"  LLM_ONBOARDING:   {llm_onboarding_path}")
        console.print(f"  Quick access:     [cyan]obra docs --llm[/cyan]")
        console.print()
        console.print("[dim]Use 'cat <path>' or your text editor to read these files.[/dim]")


@app.command(rich_help_panel="User Commands")
@handle_encoding_errors
def doctor() -> None:
    """Run health checks on your Obra environment.

    Validates:
    - Python version compatibility
    - Authentication status
    - Provider CLI availability
    - API connectivity

    Example:
        $ obra doctor
    """
    console.print()
    console.print("[bold]Obra Health Check[/bold]", style="cyan")
    console.print()

    checks_passed = 0
    total_checks = 5

    # Check 1: Python version
    console.print("[bold]Python Version:[/bold]")
    python_version = sys.version_info
    version_str = f"{python_version.major}.{python_version.minor}.{python_version.micro}"

    if python_version >= (3, 12):
        console.print(f"  [green]✓[/green] Python {version_str} (recommended)")
        checks_passed += 1
    else:
        console.print(f"  [yellow]⚠[/yellow] Python {version_str} (Python 3.12+ recommended)")
        console.print("    [dim]Obra works with Python 3.10+, but 3.12+ is recommended for best performance[/dim]")
        if python_version >= (3, 10):
            checks_passed += 1  # Still passes, just with warning

    console.print()

    # Check 2: Authentication status
    console.print("[bold]Authentication:[/bold]")
    try:
        from obra.auth import get_current_auth

        auth = get_current_auth()

        if auth:
            console.print(f"  [green]✓[/green] Logged in as {auth.email}")
            checks_passed += 1
        else:
            console.print("  [yellow]⚠[/yellow] Not logged in")
            console.print("    [dim]Run 'obra login' to authenticate[/dim]")
    except Exception as e:
        console.print(f"  [red]✗[/red] Authentication check failed: {e}")
        logger.debug(f"Auth check error: {e}", exc_info=True)

    console.print()

    # Check 3: Provider CLIs
    console.print("[bold]Provider CLIs:[/bold]")
    try:
        from obra.config import LLM_PROVIDERS, check_provider_status

        provider_count = 0
        for provider_key in LLM_PROVIDERS:
            status = check_provider_status(provider_key)
            provider_name = LLM_PROVIDERS[provider_key].get("name", provider_key)

            if status.installed:
                console.print(f"  [green]✓[/green] {provider_name} ({status.cli_command})")
                provider_count += 1
            else:
                console.print(f"  [red]✗[/red] {provider_name} ({status.cli_command}) - not found")

        # At least one provider installed counts as passing
        if provider_count > 0:
            checks_passed += 1
    except Exception as e:
        console.print(f"  [red]✗[/red] Provider check failed: {e}")
        logger.debug(f"Provider check error: {e}", exc_info=True)

    console.print()

    # Check 4: API Connectivity
    console.print("[bold]API Connectivity:[/bold]")
    try:
        import urllib.request

        # Try to connect to Obra API health endpoint
        health_url = "https://obra.dev/health"
        req = urllib.request.Request(health_url, method="HEAD")

        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    console.print("  [green]✓[/green] obra.dev API reachable")
                    checks_passed += 1
                else:
                    console.print(f"  [yellow]⚠[/yellow] API returned status {response.status}")
        except (TimeoutError, urllib.error.URLError) as e:
            console.print("  [red]✗[/red] Cannot reach obra.dev API")
            console.print(f"    [dim]Error: {e}[/dim]")
    except Exception as e:
        console.print(f"  [red]✗[/red] API check failed: {e}")
        logger.debug(f"API check error: {e}", exc_info=True)

    console.print()

    # Summary - Report Card Style
    console.print("[bold]Overall Health:[/bold]")
    percentage = int((checks_passed / total_checks) * 100)

    if percentage == 100:
        status_icon = "[green]✓[/green]"
        status_text = "[green]Excellent - All checks passed![/green]"
    elif percentage >= 80:
        status_icon = "[green]✓[/green]"
        status_text = "[green]Good - System is functional[/green]"
    elif percentage >= 60:
        status_icon = "[yellow]⚠[/yellow]"
        status_text = "[yellow]Fair - Some issues detected[/yellow]"
    else:
        status_icon = "[red]✗[/red]"
        status_text = "[red]Poor - Multiple issues need attention[/red]"

    console.print(f"  {status_icon} {checks_passed}/{total_checks} checks passed ({percentage}%)")
    console.print(f"  {status_text}")
    console.print()


# =============================================================================
# Plan Management Commands
# =============================================================================


# Create plans subcommand group
plans_app = typer.Typer(
    name="plans",
    help="Manage uploaded plan files",
    no_args_is_help=True,
)
app.add_typer(plans_app, name="plans")


@plans_app.command("list")
@handle_encoding_errors
def plans_list(
    limit: int = typer.Option(
        50,
        "--limit",
        "-n",
        help="Maximum number of plans to list (max: 100)",
    ),
) -> None:
    """List uploaded plan files.

    Displays all plans uploaded by the current user, ordered by
    creation time (most recent first).

    Examples:
        $ obra plans list
        $ obra plans list --limit 10
    """
    try:
        from obra.api import APIClient
        from obra.auth import ensure_valid_token, get_current_auth

        # Ensure authenticated
        auth = get_current_auth()
        if not auth:
            print_error("Not logged in")
            console.print("\nRun 'obra login' to authenticate.")
            raise typer.Exit(1)

        ensure_valid_token()

        # Get plans from server
        client = APIClient.from_config()
        plans = client.list_plans(limit=limit)

        console.print()
        if not plans:
            print_info("No plans uploaded")
            console.print("\nUpload a plan with: [cyan]obra plans upload path/to/plan.yaml[/cyan]")
            return

        console.print(f"[bold]Uploaded Plans[/bold] ({len(plans)} total)", style="cyan")
        console.print()

        table = Table()
        table.add_column("Plan ID", style="cyan")
        table.add_column("Name", style="bold")
        table.add_column("Stories", justify="right")
        table.add_column("Uploaded", style="dim")

        for plan in plans:
            plan_id_short = plan.get("plan_id", "")[:8] + "..."
            name = plan.get("name", "N/A")
            story_count = str(plan.get("story_count", 0))
            created_at = plan.get("created_at", "N/A")

            # Format timestamp if it's ISO format
            if "T" in created_at:
                from datetime import datetime

                try:
                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    created_at = dt.strftime("%Y-%m-%d %H:%M")
                except (ValueError, TypeError):
                    # Invalid timestamp format, use as-is
                    pass

            table.add_row(plan_id_short, name, story_count, created_at)

        console.print(table)
        console.print()
        console.print('[dim]Use with:[/dim] [cyan]obra run --plan-id <plan_id> "objective"[/cyan]')

    except APIError as e:
        display_obra_error(e, console)
        logger.error(f"API error in plans list command: {e}", exc_info=True)
        raise typer.Exit(1)
    except ConfigurationError as e:
        display_obra_error(e, console)
        logger.error(f"Configuration error in plans list command: {e}", exc_info=True)
        raise typer.Exit(1)
    except ObraError as e:
        display_obra_error(e, console)
        logger.error(f"Obra error in plans list command: {e}", exc_info=True)
        raise typer.Exit(1)
    except Exception as e:
        display_error(e, console)
        logger.exception(f"Unexpected error in plans list command: {e}")
        raise typer.Exit(1)


@plans_app.command("show")
@handle_encoding_errors
def plans_show(
    plan_id: str = typer.Argument(..., help="Plan ID to display"),
) -> None:
    """Display details of an uploaded plan file.

    Shows complete information about a plan including:
    - Plan metadata (name, work_id, description)
    - Story list with titles and status
    - Task count per story

    Examples:
        $ obra plans show abc123
        $ obra plans show abc12345-6789-...
    """
    try:
        from obra.api import APIClient
        from obra.auth import ensure_valid_token, get_current_auth

        # Ensure authenticated
        auth = get_current_auth()
        if not auth:
            print_error("Not logged in")
            console.print("\nRun 'obra login' to authenticate.")
            raise typer.Exit(1)

        ensure_valid_token()

        # Get plan details from server
        client = APIClient.from_config()
        plan = client.get_plan(plan_id)

        if not plan:
            print_error(f"Plan not found: {plan_id}")
            raise typer.Exit(1)

        console.print()
        console.print(f"[bold cyan]Plan Details[/bold cyan]")
        console.print("=" * 60)
        console.print()

        # Basic info
        console.print(f"[bold]Plan ID:[/bold]   {plan.get('plan_id', 'N/A')}")
        console.print(f"[bold]Name:[/bold]      {plan.get('name', 'N/A')}")
        console.print(f"[bold]Work ID:[/bold]   {plan.get('work_id', 'N/A')}")

        # Format and display creation time
        created_at = plan.get("created_at", "N/A")
        if "T" in str(created_at):
            from datetime import datetime

            try:
                dt = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
                created_at = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            except (ValueError, TypeError):
                pass
        console.print(f"[bold]Uploaded:[/bold]  {created_at}")

        # Description if present
        if plan.get("description"):
            console.print(f"[bold]Description:[/bold]")
            console.print(f"  {plan.get('description')}")

        # Stories
        stories = plan.get("stories", [])
        if stories:
            console.print()
            console.print(f"[bold]Stories[/bold] ({len(stories)} total)")
            console.print("-" * 40)

            story_table = Table(show_header=True, header_style="bold")
            story_table.add_column("ID", style="cyan")
            story_table.add_column("Title")
            story_table.add_column("Status", style="dim")
            story_table.add_column("Tasks", justify="right")

            for story in stories:
                story_id = story.get("id", "?")
                title = story.get("title", "Untitled")
                status = story.get("status", "pending")
                task_count = len(story.get("tasks", []))
                story_table.add_row(story_id, title, status, str(task_count))

            console.print(story_table)

        console.print()
        console.print(f'[dim]Use with:[/dim] [cyan]obra --plan-id {plan_id[:8]}... "your objective"[/cyan]')

    except APIError as e:
        display_obra_error(e, console)
        logger.error(f"API error in plans show command: {e}", exc_info=True)
        raise typer.Exit(1)
    except ConfigurationError as e:
        display_obra_error(e, console)
        logger.error(f"Configuration error in plans show command: {e}", exc_info=True)
        raise typer.Exit(1)
    except ObraError as e:
        display_obra_error(e, console)
        logger.error(f"Obra error in plans show command: {e}", exc_info=True)
        raise typer.Exit(1)
    except Exception as e:
        display_error(e, console)
        logger.exception(f"Unexpected error in plans show command: {e}")
        raise typer.Exit(1)


@plans_app.command("delete")
@handle_encoding_errors
def plans_delete(
    plan_id: str = typer.Argument(..., help="Plan ID to delete"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Delete an uploaded plan file.

    Permanently removes the plan from the server. This cannot be undone.
    Existing sessions using this plan are not affected.

    Examples:
        $ obra plans delete abc123-uuid
        $ obra plans delete abc123-uuid --force
    """
    try:
        from obra.api import APIClient
        from obra.auth import ensure_valid_token, get_current_auth

        # Ensure authenticated
        auth = get_current_auth()
        if not auth:
            print_error("Not logged in")
            console.print("\nRun 'obra login' to authenticate.")
            raise typer.Exit(1)

        ensure_valid_token()

        # Get plan details first
        client = APIClient.from_config()

        console.print()
        console.print("[dim]Fetching plan details...[/dim]")

        try:
            plan = client.get_plan(plan_id)
            plan_name = plan.get("name", "Unknown")
            story_count = plan.get("story_count", 0)

            console.print()
            console.print("[bold]Plan Details[/bold]", style="yellow")
            console.print(f"ID: {plan_id}")
            console.print(f"Name: {plan_name}")
            console.print(f"Stories: {story_count}")
            console.print()

        except (APIError, ObraError) as e:
            # Plan not found or error fetching - proceed with deletion anyway
            logger.warning(f"Could not fetch plan details: {e}")
            plan_name = "Unknown"

        # Confirm deletion
        if not force:
            # C14: Check for non-interactive mode before prompting
            if not sys.stdin.isatty():
                # Non-interactive mode: default to not deleting (safe default)
                console.print("Non-interactive mode: skipping deletion confirmation (defaulting to cancel)")
                console.print("Use --force to delete without confirmation")
                return

            confirm = typer.confirm(
                f"Are you sure you want to delete plan '{plan_name}'?",
                default=False,
            )
            if not confirm:
                console.print("Cancelled")
                return

        # Delete plan
        console.print("[dim]Deleting plan...[/dim]")
        result = client.delete_plan(plan_id)

        if result.get("success"):
            console.print()
            print_success(f"Plan deleted: {plan_name}")
        else:
            print_error("Failed to delete plan")
            raise typer.Exit(1)

    except APIError as e:
        display_obra_error(e, console)
        logger.error(f"API error in plans delete command: {e}", exc_info=True)
        raise typer.Exit(1)
    except ConfigurationError as e:
        display_obra_error(e, console)
        logger.error(f"Configuration error in plans delete command: {e}", exc_info=True)
        raise typer.Exit(1)
    except ObraError as e:
        display_obra_error(e, console)
        logger.error(f"Obra error in plans delete command: {e}", exc_info=True)
        raise typer.Exit(1)
    except Exception as e:
        display_error(e, console)
        logger.exception(f"Unexpected error in plans delete command: {e}")
        raise typer.Exit(1)


@plans_app.command("upload")
@handle_encoding_errors
def plans_upload(
    file_path: Path = typer.Argument(..., help="Path to MACHINE_PLAN.yaml file to upload"),
    validate_only: bool = typer.Option(
        False,
        "--validate-only",
        help="Only validate the plan file without uploading",
    ),
) -> None:
    """Upload a MACHINE_PLAN.yaml file to Obra SaaS.

    Validates and uploads a plan file to Firestore for later use.
    After upload, use the returned plan_id with 'obra run --plan-id'.

    Examples:
        $ obra plans upload docs/development/MY_PLAN.yaml
        $ obra plans upload --validate-only plan.yaml

    Exit Codes:
        0: Upload successful or validation passed
        1: Upload failed or validation failed
    """
    try:
        command = UploadPlanCommand()
        exit_code = command.execute(str(file_path), validate_only)

        if exit_code != 0:
            raise typer.Exit(exit_code)

    except APIError as e:
        display_obra_error(e, console)
        logger.error(f"API error in plans upload command: {e}", exc_info=True)
        raise typer.Exit(1)
    except ConfigurationError as e:
        display_obra_error(e, console)
        logger.error(f"Configuration error in plans upload command: {e}", exc_info=True)
        raise typer.Exit(1)
    except ObraError as e:
        display_obra_error(e, console)
        logger.error(f"Obra error in plans upload command: {e}", exc_info=True)
        raise typer.Exit(1)
    except OSError as e:
        print_error(f"Failed to read plan file: {e}")
        logger.error(f"File I/O error in plans upload command: {e}", exc_info=True)
        raise typer.Exit(1)
    except Exception as e:
        display_error(e, console)
        logger.exception(f"Unexpected error in plans upload command: {e}")
        raise typer.Exit(1)


@plans_app.command("validate")
@handle_encoding_errors
def plans_validate(
    file_path: Path = typer.Argument(..., help="Path to MACHINE_PLAN.yaml file to validate"),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output with additional details",
    ),
) -> None:
    """Validate YAML syntax of a MACHINE_PLAN.yaml file.

    Validates the specified plan file for YAML syntax errors and schema
    compliance. Displays detailed error messages with line/column numbers
    and helpful suggestions for fixing common issues.

    Examples:
        $ obra plans validate docs/development/MY_PLAN.yaml
        $ obra plans validate --verbose plan.yaml

    Exit Codes:
        0: Validation passed - file is valid
        1: Validation failed - file has errors
    """
    try:
        # Validate that file exists
        if not file_path.exists():
            print_error(f"File not found: {file_path}")
            raise typer.Exit(1)

        # Execute validation
        command = ValidatePlanCommand()
        exit_code = command.execute(str(file_path), verbose)

        # Exit with appropriate code
        if exit_code != 0:
            raise typer.Exit(exit_code)

    except ConfigurationError as e:
        display_obra_error(e, console)
        logger.error(f"Configuration error in plans validate command: {e}", exc_info=True)
        raise typer.Exit(1)
    except ObraError as e:
        display_obra_error(e, console)
        logger.error(f"Obra error in plans validate command: {e}", exc_info=True)
        raise typer.Exit(1)
    except OSError as e:
        print_error(f"Failed to read plan file: {e}")
        logger.error(f"File I/O error in plans validate command: {e}", exc_info=True)
        raise typer.Exit(1)
    except Exception as e:
        display_error(e, console)
        logger.exception(f"Unexpected error in plans validate command: {e}")
        raise typer.Exit(1)


# =============================================================================
# Entry Point
# =============================================================================


def main() -> None:
    """Main entry point for the CLI."""
    # Windows UTF-8 setup BEFORE any output (including --help)
    # This must run before Typer/Rich output anything with Unicode
    if sys.platform == "win32":
        os.environ["PYTHONUTF8"] = "1"
        # Reconfigure stdout/stderr for UTF-8 with fallback for unprintable chars
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    app()


if __name__ == "__main__":
    main()
