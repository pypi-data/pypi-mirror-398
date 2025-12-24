"""CLI for claude-orchestrator.

Provides commands for initializing projects, generating tasks, and running agents.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from claude_orchestrator import __version__
from claude_orchestrator.config import (
    GLOBAL_CONFIG_FILE,
    Config,
    GitConfig,
    config_exists,
    load_config,
    load_global_config,
    save_config,
    save_global_config,
)
from claude_orchestrator.discovery import discover_sync
from claude_orchestrator.git_provider import (
    GitProvider,
    get_default_branch,
    get_provider_status,
)
from claude_orchestrator.mcp_registry import AuthType, get_mcp_status
from claude_orchestrator.orchestrator import cleanup_all_worktrees, run_tasks_sync
from claude_orchestrator.reviewer import (
    PRInfo,
    ReviewResult,
    fetch_open_prs,
    fetch_pr_by_id,
    load_prs_from_state,
    review_prs_sync,
)
from claude_orchestrator.task_generator import (
    generate_tasks_sync,
    load_tasks_config,
    save_tasks_config,
)

app = typer.Typer(
    name="claude-orchestrator",
    help="Orchestrator for running parallel Claude Code agents on multiple tasks.",
    no_args_is_help=True,
)
console = Console()


def validate_and_prompt_config(config: Config, project_dir: Path) -> Config:
    """Validate config and prompt for missing required values.

    Shows auto-detected values and prompts for any that couldn't be detected.
    Only prompts if values are missing or auto-detected defaults need confirmation.

    Args:
        config: Loaded configuration
        project_dir: Project directory

    Returns:
        Updated config with user-provided values
    """
    needs_save = False

    # Check repo_slug (required for Bitbucket)
    provider_status = get_provider_status(str(project_dir))
    if provider_status.provider == GitProvider.BITBUCKET and not config.git.repo_slug:
        console.print("[yellow]⚠ Could not auto-detect repo_slug from git remote[/yellow]")
        config.git.repo_slug = typer.prompt("Enter Bitbucket repository slug")
        needs_save = True

    # Show summary of config (no prompting if already configured)
    console.print("\n[bold]Configuration:[/bold]")
    console.print(f"  repo_slug: [cyan]{config.git.repo_slug}[/cyan]")
    console.print(f"  base_branch: [cyan]{config.git.base_branch}[/cyan]")
    console.print(f"  destination_branch: [cyan]{config.git.destination_branch}[/cyan]")
    console.print()

    # Save if modified
    if needs_save:
        save_config(config, project_dir)
        console.print("[green]✓ Configuration saved[/green]\n")

    return config


def version_callback(value: bool):
    if value:
        console.print(f"claude-orchestrator version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
):
    """Claude Orchestrator - Run parallel Claude Code agents on multiple tasks."""
    pass


@app.command()
def doctor(
    project_dir: Path = typer.Option(
        Path.cwd(),
        "--project-dir",
        "-d",
        help="Project directory to check.",
    ),
    mcps: str | None = typer.Option(
        None,
        "--mcps",
        "-m",
        help="Comma-separated list of MCPs to check (default: from config or common ones).",
    ),
):
    """Check prerequisites and configuration status.

    Verifies git provider, CLI tools, and MCP configurations.
    """
    console.print("\n[bold]Claude Orchestrator Doctor[/bold]\n")

    # Check git provider
    console.print("[bold]Git Provider[/bold]")
    provider_status = get_provider_status(str(project_dir))

    if provider_status.provider == GitProvider.GITHUB:
        provider_name = "GitHub"
        tool_name = "gh CLI"
    elif provider_status.provider == GitProvider.BITBUCKET:
        provider_name = "Bitbucket"
        tool_name = "mcp-server-bitbucket"
    else:
        provider_name = "Unknown"
        tool_name = "N/A"

    if provider_status.is_ready:
        console.print(f"  [green]✓[/green] Provider: {provider_name}")
        console.print(f"  [green]✓[/green] Tool: {tool_name} (ready)")
    else:
        console.print(f"  [yellow]![/yellow] Provider: {provider_name}")
        if provider_status.error:
            console.print(f"  [red]✗[/red] {provider_status.error}")

    # Check config
    console.print("\n[bold]Configuration[/bold]")
    if config_exists(project_dir):
        console.print("  [green]✓[/green] .claude-orchestrator.yaml exists")
        config = load_config(project_dir)
    else:
        console.print(
            "  [yellow]○[/yellow] .claude-orchestrator.yaml not found (will use defaults)"
        )
        config = Config()

    # Check MCPs
    console.print("\n[bold]MCPs[/bold]")

    # Determine which MCPs to check
    mcp_list = []
    if mcps:
        mcp_list = [m.strip() for m in mcps.split(",")]
    elif config.mcps.enabled:
        mcp_list = config.mcps.enabled
    # Only check git provider MCP if needed (Bitbucket needs MCP, GitHub uses gh CLI)
    # Don't show all MCPs by default - only what's configured or explicitly requested

    # Check git provider MCP status (only for Bitbucket)
    if provider_status.provider == GitProvider.BITBUCKET:
        status = get_mcp_status("bitbucket")
        if status.is_ready:
            console.print("  [green]✓[/green] bitbucket: ready")
        elif status.is_configured:
            console.print("  [green]✓[/green] bitbucket: configured")
        else:
            console.print("  [red]✗[/red] bitbucket: not configured")
            if status.setup_instructions:
                console.print(f"      Setup:\n{status.setup_instructions}")
    elif provider_status.provider == GitProvider.GITHUB:
        console.print("  [dim]○[/dim] Using gh CLI for GitHub (no MCP needed)")

    # Get status of explicitly enabled MCPs from config
    for mcp_name in mcp_list:
        if mcp_name == "bitbucket":
            continue  # Already handled above

        status = get_mcp_status(mcp_name)

        if status.is_ready:
            console.print(f"  [green]✓[/green] {mcp_name}: ready")
        elif status.is_configured:
            if status.auth_type == AuthType.OAUTH_BROWSER:
                console.print(
                    f"  [yellow]○[/yellow] {mcp_name}: configured (may need browser auth)"
                )
            else:
                console.print(f"  [yellow]![/yellow] {mcp_name}: {status.message}")
        else:
            console.print(f"  [red]✗[/red] {mcp_name}: not configured")
            if status.setup_instructions:
                console.print(f"      Setup:\n{status.setup_instructions}")

    if not mcp_list and provider_status.provider != GitProvider.BITBUCKET:
        console.print("  [dim]○[/dim] No additional MCPs configured")

    console.print()


@app.command()
def init(
    project_dir: Path = typer.Option(
        Path.cwd(),
        "--project-dir",
        "-d",
        help="Project directory to initialize.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing configuration.",
    ),
    use_claude: bool = typer.Option(
        True,
        "--use-claude/--no-claude",
        help="Use Claude for project discovery.",
    ),
):
    """Initialize project configuration.

    Discovers project structure and creates .claude-orchestrator.yaml.
    """
    if config_exists(project_dir) and not force:
        console.print("[yellow]Configuration already exists. Use --force to overwrite.[/yellow]")
        raise typer.Exit(1)

    console.print("[bold]Initializing Claude Orchestrator[/bold]\n")

    # Detect git provider
    console.print("Detecting git provider...")
    provider_status = get_provider_status(str(project_dir))

    provider_name = {
        GitProvider.GITHUB: "github",
        GitProvider.BITBUCKET: "bitbucket",
    }.get(provider_status.provider, "auto")

    console.print(f"  Provider: {provider_name}")

    # Detect default branch
    console.print("Detecting default branch...")
    default_branch = get_default_branch(str(project_dir)) or "main"
    console.print(f"  Default branch: {default_branch}")

    # Discover project
    console.print("\nAnalyzing project structure...")
    context = discover_sync(project_dir, use_claude=use_claude)

    console.print(f"  Project: {context.project_name}")
    console.print(f"  Tech stack: {', '.join(context.tech_stack)}")
    console.print(f"  Test command: {context.test_command or 'Not detected'}")
    console.print(f"  Key files: {len(context.key_files)} found")

    # Create config
    config = Config(
        project_root=project_dir,
        git=GitConfig(
            provider=provider_name,
            base_branch=default_branch,
            destination_branch=default_branch,
            repo_slug=provider_status.repo_info.get("repo") if provider_status.repo_info else None,
        ),
    )

    # Add project context
    config.project.key_files = context.key_files[:10]
    config.project.test_command = context.test_command

    # Check for agent instructions
    if (project_dir / ".claude" / "AGENT_INSTRUCTIONS.md").exists():
        config.project.agent_instructions = ".claude/AGENT_INSTRUCTIONS.md"

    # Save config
    save_config(config, project_dir)
    console.print("\n[green]✓[/green] Created .claude-orchestrator.yaml")

    # Show next steps
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Review and customize .claude-orchestrator.yaml")
    console.print("  2. Create a todo.md with tasks")
    console.print("  3. Run: claude-orchestrator generate --from-todo todo.md")
    console.print("  4. Run: claude-orchestrator run")


@app.command()
def generate(
    from_todo: Path = typer.Option(
        ...,
        "--from-todo",
        "-t",
        help="Path to todo.md file.",
    ),
    output: Path = typer.Option(
        Path("task_config.yaml"),
        "--output",
        "-o",
        help="Output path for task configuration.",
    ),
    use_sdk: bool = typer.Option(
        True,
        "--use-sdk/--no-sdk",
        help="Use Anthropic SDK with structured outputs (requires ANTHROPIC_API_KEY).",
    ),
    project_dir: Path = typer.Option(
        Path.cwd(),
        "--project-dir",
        "-d",
        help="Project directory.",
    ),
):
    """Generate task configuration from a todo file.

    Uses Claude to analyze the todo file and generate task_config.yaml.

    By default, uses Anthropic SDK with structured outputs if ANTHROPIC_API_KEY
    is set. Falls back to Claude CLI otherwise.
    """
    import os

    if not from_todo.exists():
        console.print(f"[red]Error: Todo file not found: {from_todo}[/red]")
        raise typer.Exit(1)

    console.print("[bold]Generating task configuration[/bold]\n")
    console.print(f"  Input: {from_todo}")
    console.print(f"  Output: {output}")

    # Check SDK availability
    if use_sdk and os.getenv("ANTHROPIC_API_KEY"):
        console.print("  [dim]Method: Anthropic SDK (structured outputs)[/dim]")
    else:
        console.print("  [dim]Method: Claude CLI[/dim]")

    # Load config
    config = load_config(project_dir)

    # Discover project
    console.print("\nAnalyzing project...")
    context = discover_sync(project_dir, use_claude=False)

    # Generate tasks
    console.print("Generating tasks with Claude...")
    tasks_config = generate_tasks_sync(from_todo, context, config, use_sdk=use_sdk)

    if not tasks_config or not tasks_config.tasks:
        console.print("[red]Error: Failed to generate tasks[/red]")
        raise typer.Exit(1)

    # Save tasks
    save_tasks_config(tasks_config, output)

    console.print(f"\n[green]✓[/green] Generated {len(tasks_config.tasks)} task(s):")
    for task in tasks_config.tasks:
        console.print(f"  - {task.id}: {task.title}")

    console.print(f"\n[bold]Next step:[/bold] claude-orchestrator run --config {output}")


@app.command()
def run(
    config_file: Path = typer.Option(
        Path("task_config.yaml"),
        "--config",
        "-c",
        help="Path to task configuration file.",
    ),
    from_todo: Path | None = typer.Option(
        None,
        "--from-todo",
        "-t",
        help="Generate tasks from todo file before running.",
    ),
    execute: bool = typer.Option(
        False,
        "--execute",
        "-e",
        help="Execute tasks after generating (requires --from-todo).",
    ),
    yolo: bool = typer.Option(
        False,
        "--yolo",
        help="YOLO mode: generate, execute, and create PRs without stopping.",
    ),
    with_review: bool = typer.Option(
        False,
        "--with-review",
        help="Run PR review phase after task execution.",
    ),
    tasks: str | None = typer.Option(
        None,
        "--tasks",
        help="Comma-separated task IDs to run (default: all).",
    ),
    auto_approve: bool = typer.Option(
        False,
        "--auto-approve",
        "-y",
        help="Automatically approve all agent plans.",
    ),
    keep_worktrees: bool = typer.Option(
        False,
        "--keep-worktrees",
        help="Don't cleanup worktrees after completion.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Show what would be done without executing.",
    ),
    no_pr: bool = typer.Option(
        False,
        "--no-pr",
        help="Skip PR creation instructions in prompts.",
    ),
    sequential: bool = typer.Option(
        False,
        "--sequential",
        "-s",
        help="Run tasks sequentially instead of in parallel.",
    ),
    project_dir: Path = typer.Option(
        Path.cwd(),
        "--project-dir",
        "-d",
        help="Project directory.",
    ),
):
    """Run tasks using Claude Code agents.

    Each task runs in its own git worktree with a dedicated agent.

    Workflow modes:
      - Default: Generate tasks, stop for review
      - --execute: Generate and execute, stop before PRs
      - --yolo: Generate, execute, and create PRs without stopping
      - --with-review: Execute + run PR review phase afterwards
    """
    # Load project config early for workflow settings
    config = load_config(project_dir)

    # Validate and prompt for missing config (unless dry-run)
    if not dry_run:
        config = validate_and_prompt_config(config, project_dir)

    # YOLO mode overrides everything
    if yolo:
        execute = True
        auto_approve = config.workflow.auto_approve or auto_approve
        if not no_pr:
            no_pr = not config.workflow.auto_pr
    else:
        # Apply workflow config defaults
        auto_approve = auto_approve or config.workflow.auto_approve
        if config.workflow.mode == "yolo":
            execute = True
            if not no_pr:
                no_pr = not config.workflow.auto_pr

    # Handle --from-todo
    if from_todo:
        if not from_todo.exists():
            console.print(f"[red]Error: Todo file not found: {from_todo}[/red]")
            raise typer.Exit(1)

        console.print("[bold]Generating tasks from todo...[/bold]\n")

        # Discover project
        context = discover_sync(project_dir, use_claude=False)

        # Generate tasks
        tasks_config = generate_tasks_sync(from_todo, context, config)

        if not tasks_config or not tasks_config.tasks:
            console.print("[red]Error: Failed to generate tasks[/red]")
            raise typer.Exit(1)

        # Save tasks
        save_tasks_config(tasks_config, config_file)

        console.print(f"[green]✓[/green] Generated {len(tasks_config.tasks)} task(s)")

        # Check if we should stop after generate (unless yolo or execute)
        should_stop = config.workflow.stop_after_generate and not execute and not yolo
        if should_stop:
            console.print(f"\n[dim]Review {config_file} and run: claude-orchestrator run[/dim]")
            console.print("[dim]Or use --execute or --yolo to continue automatically[/dim]")
            raise typer.Exit()

        console.print("\n" + "=" * 60)
        console.print("Proceeding to execute tasks...")
        console.print("=" * 60)

    # Load task config
    tasks_config = load_tasks_config(config_file)

    if not tasks_config:
        console.print(f"[red]Error: Could not load task config: {config_file}[/red]")
        raise typer.Exit(1)

    if not tasks_config.tasks:
        console.print("[yellow]No tasks to run[/yellow]")
        raise typer.Exit()

    # Parse task IDs
    task_ids = [t.strip() for t in tasks.split(",")] if tasks else None

    # Run tasks
    console.print(f"\n[bold]Running {len(tasks_config.tasks)} task(s)[/bold]\n")

    results = run_tasks_sync(
        tasks_config=tasks_config,
        config=config,
        task_ids=task_ids,
        auto_approve=auto_approve,
        keep_worktrees=keep_worktrees,
        dry_run=dry_run,
        no_pr=no_pr,
        sequential=sequential,
    )

    # Check for failures
    failed = sum(1 for r in results if r.status == "failed")
    successful = [r for r in results if r.status == "success"]

    # Handle --with-review flag
    if with_review and successful and not dry_run:
        console.print("\n" + "=" * 60)
        console.print("[bold]PR REVIEW PHASE[/bold]")
        console.print("=" * 60 + "\n")

        # Load PRs from successful results
        state_file = project_dir / ".claude-orchestrator" / ".state.json"
        prs_to_review = load_prs_from_state(state_file)

        if prs_to_review:
            # Fetch full PR info
            provider_status = get_provider_status(str(project_dir))
            full_prs = []
            for pr in prs_to_review:
                full_pr = fetch_pr_by_id(
                    provider_status,
                    project_dir,
                    pr.id,
                    config.git.repo_slug,
                )
                if full_pr:
                    full_prs.append(full_pr)

            if full_prs:
                console.print(f"Reviewing {len(full_prs)} PR(s)...")
                review_results = review_prs_sync(
                    prs=full_prs,
                    repo_root=project_dir,
                    config=config,
                    automerge=config.review.automerge,
                    auto_approve=auto_approve,
                    sequential=True,
                )
                _print_review_summary(review_results)

                review_failed = sum(1 for r in review_results if r.status == "failed")
                failed += review_failed
            else:
                console.print("[yellow]Could not fetch PR details for review[/yellow]")
        else:
            console.print("[yellow]No PRs found from task execution[/yellow]")

    # Exit with appropriate code
    raise typer.Exit(1 if failed > 0 else 0)


@app.command()
def yolo(
    from_todo: Path = typer.Argument(
        ...,
        help="Path to todo.md file.",
    ),
    config_file: Path = typer.Option(
        Path("task_config.yaml"),
        "--config",
        "-c",
        help="Path to task configuration file.",
    ),
    tasks: str | None = typer.Option(
        None,
        "--tasks",
        help="Comma-separated task IDs to run (default: all).",
    ),
    sequential: bool = typer.Option(
        False,
        "--sequential",
        "-s",
        help="Run tasks sequentially instead of in parallel.",
    ),
    project_dir: Path = typer.Option(
        Path.cwd(),
        "--project-dir",
        "-d",
        help="Project directory.",
    ),
):
    """YOLO mode: Generate tasks, execute, and create PRs without stopping.

    This is a shortcut for:
        claude-orchestrator run --from-todo TODO.md --yolo

    Example:
        claude-orchestrator yolo TODO.md
    """
    # Load config
    config = load_config(project_dir)

    if not from_todo.exists():
        console.print(f"[red]Error: Todo file not found: {from_todo}[/red]")
        raise typer.Exit(1)

    console.print("[bold yellow]🚀 YOLO MODE[/bold yellow]")
    console.print("[dim]Generating → Executing → Creating PRs (no stops)[/dim]\n")

    # Generate tasks
    console.print("[bold]Step 1: Generating tasks...[/bold]")
    context = discover_sync(project_dir, use_claude=False)
    tasks_config = generate_tasks_sync(from_todo, context, config)

    if not tasks_config or not tasks_config.tasks:
        console.print("[red]Error: Failed to generate tasks[/red]")
        raise typer.Exit(1)

    save_tasks_config(tasks_config, config_file)
    console.print(f"[green]✓[/green] Generated {len(tasks_config.tasks)} task(s)\n")

    # Execute tasks
    console.print("[bold]Step 2: Executing tasks...[/bold]")
    task_ids = [t.strip() for t in tasks.split(",")] if tasks else None

    results = run_tasks_sync(
        tasks_config=tasks_config,
        config=config,
        task_ids=task_ids,
        auto_approve=config.workflow.auto_approve,
        keep_worktrees=False,
        dry_run=False,
        no_pr=not config.workflow.auto_pr,
        sequential=sequential,
    )

    # Summary
    console.print("\n[bold]Summary[/bold]")
    succeeded = sum(1 for r in results if r.status == "success")
    failed = sum(1 for r in results if r.status == "failed")
    console.print(f"  [green]✓[/green] Succeeded: {succeeded}")
    if failed > 0:
        console.print(f"  [red]✗[/red] Failed: {failed}")

    raise typer.Exit(1 if failed > 0 else 0)


@app.command()
def config(
    key: str = typer.Argument(
        None,
        help="Configuration key (e.g., git.base_branch, git.repo_slug)",
    ),
    value: str = typer.Argument(
        None,
        help="Value to set",
    ),
    list_all: bool = typer.Option(
        False,
        "--list",
        "-l",
        help="List all configuration values.",
    ),
    is_global: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Use global configuration (~/.config/claude-orchestrator/config.yaml).",
    ),
    project_dir: Path = typer.Option(
        Path.cwd(),
        "--project-dir",
        "-d",
        help="Project directory.",
    ),
):
    """Get or set configuration values.

    Similar to 'git config' or 'gh config'.

    Configuration priority (higher overrides lower):
      1. Project config (.claude-orchestrator.yaml)
      2. Global config (~/.config/claude-orchestrator/config.yaml)
      3. Default values

    Examples:
        claude-orchestrator config --list
        claude-orchestrator config git.base_branch
        claude-orchestrator config git.base_branch develop
        claude-orchestrator config --global git.base_branch develop
    """
    if is_global:
        # Handle global config
        global_data = load_global_config()

        if list_all:
            console.print(f"\n[bold]Global Configuration[/bold] ({GLOBAL_CONFIG_FILE})\n")
            if not global_data:
                console.print("  [dim](no global config set)[/dim]")
            else:
                _print_nested_config(global_data, "  ")
            console.print()
            return

        if key is None:
            console.print("Usage: claude-orchestrator config --global [KEY] [VALUE]")
            console.print("       claude-orchestrator config --global --list")
            return

        # Get value from global config
        if value is None:
            val = _get_nested_value(global_data, key)
            console.print(val if val is not None else "")
            return

        # Set value in global config
        _set_nested_value(global_data, key, value)
        save_global_config(global_data)
        console.print(f"[green]✓[/green] Set global {key} = {value}")
        return

    # Handle project config
    cfg = load_config(project_dir)

    if list_all:
        console.print("\n[bold]Configuration[/bold] (merged: global + project)\n")
        console.print("[dim]# Git[/dim]")
        console.print(f"  git.provider: {cfg.git.provider}")
        console.print(f"  git.base_branch: {cfg.git.base_branch}")
        console.print(f"  git.destination_branch: {cfg.git.destination_branch}")
        console.print(f"  git.repo_slug: {cfg.git.repo_slug or '(auto)'}")
        console.print(f"  worktree_dir: {cfg.worktree_dir}")
        console.print("[dim]# Workflow[/dim]")
        console.print(f"  workflow.mode: {cfg.workflow.mode}")
        console.print(f"  workflow.stop_after_generate: {cfg.workflow.stop_after_generate}")
        console.print(f"  workflow.auto_approve: {cfg.workflow.auto_approve}")
        console.print(f"  workflow.auto_pr: {cfg.workflow.auto_pr}")
        console.print("[dim]# Tools & Permissions[/dim]")
        console.print(f"  tools.permission_mode: {cfg.tools.permission_mode}")
        if cfg.tools.allowed_cli:
            console.print(f"  tools.allowed_cli: {', '.join(cfg.tools.allowed_cli)}")
        if cfg.tools.allowed_tools:
            console.print(f"  tools.allowed_tools: {', '.join(cfg.tools.allowed_tools)}")
        if cfg.tools.disallowed_tools:
            console.print(f"  tools.disallowed_tools: {', '.join(cfg.tools.disallowed_tools)}")
        if cfg.tools.skip_permissions:
            console.print(f"  tools.skip_permissions: {cfg.tools.skip_permissions}")
        if cfg.mcps.enabled:
            console.print("[dim]# MCPs[/dim]")
            console.print(f"  mcps.enabled: {', '.join(cfg.mcps.enabled)}")
        if cfg.project.test_command or cfg.project.test_instructions:
            console.print("[dim]# Project[/dim]")
            if cfg.project.test_command:
                console.print(f"  project.test_command: {cfg.project.test_command}")
            if cfg.project.test_instructions:
                preview = cfg.project.test_instructions[:50].replace("\n", " ")
                console.print(f"  project.test_instructions: {preview}...")
        console.print("[dim]# Review[/dim]")
        console.print(f"  review.automerge: {cfg.review.automerge}")
        console.print(f"  review.test_before_merge: {cfg.review.test_before_merge}")
        console.print("[dim]# Agent Timeouts & Retry[/dim]")
        console.print(f"  agent.inactivity_timeout: {cfg.agent.inactivity_timeout}")
        console.print(f"  agent.max_runtime: {cfg.agent.max_runtime}")
        console.print(f"  agent.max_retries: {cfg.agent.max_retries}")
        console.print(f"  agent.use_resume: {cfg.agent.use_resume}")
        console.print(f"  agent.retry_delay: {cfg.agent.retry_delay}")
        console.print()
        return

    if key is None:
        console.print("Usage: claude-orchestrator config [KEY] [VALUE]")
        console.print("       claude-orchestrator config --list")
        console.print("       claude-orchestrator config --global [KEY] [VALUE]")
        return

    # Get value
    if value is None:
        if key == "git.provider":
            console.print(cfg.git.provider)
        elif key == "git.base_branch":
            console.print(cfg.git.base_branch)
        elif key == "git.destination_branch":
            console.print(cfg.git.destination_branch)
        elif key == "git.repo_slug":
            console.print(cfg.git.repo_slug or "")
        elif key == "worktree_dir":
            console.print(cfg.worktree_dir)
        elif key == "project.test_command":
            console.print(cfg.project.test_command or "")
        elif key == "project.test_instructions":
            console.print(cfg.project.test_instructions or "")
        elif key == "review.automerge":
            console.print(str(cfg.review.automerge).lower())
        elif key == "review.test_before_merge":
            console.print(str(cfg.review.test_before_merge).lower())
        elif key == "review.require_all_tests_pass":
            console.print(str(cfg.review.require_all_tests_pass).lower())
        elif key == "workflow.mode":
            console.print(cfg.workflow.mode)
        elif key == "workflow.stop_after_generate":
            console.print(str(cfg.workflow.stop_after_generate).lower())
        elif key == "workflow.auto_approve":
            console.print(str(cfg.workflow.auto_approve).lower())
        elif key == "workflow.auto_pr":
            console.print(str(cfg.workflow.auto_pr).lower())
        elif key == "tools.permission_mode":
            console.print(cfg.tools.permission_mode)
        elif key == "tools.allowed_cli":
            console.print(",".join(cfg.tools.allowed_cli) if cfg.tools.allowed_cli else "")
        elif key == "tools.allowed_tools":
            console.print(",".join(cfg.tools.allowed_tools) if cfg.tools.allowed_tools else "")
        elif key == "tools.disallowed_tools":
            console.print(
                ",".join(cfg.tools.disallowed_tools) if cfg.tools.disallowed_tools else ""
            )
        elif key == "tools.skip_permissions":
            console.print(str(cfg.tools.skip_permissions).lower())
        elif key == "agent.inactivity_timeout":
            console.print(cfg.agent.inactivity_timeout)
        elif key == "agent.max_runtime":
            console.print(cfg.agent.max_runtime)
        elif key == "agent.max_retries":
            console.print(cfg.agent.max_retries)
        elif key == "agent.use_resume":
            console.print(str(cfg.agent.use_resume).lower())
        elif key == "agent.retry_delay":
            console.print(cfg.agent.retry_delay)
        else:
            console.print(f"[red]Unknown key: {key}[/red]")
        return

    # Set value
    if key == "git.provider":
        cfg.git.provider = value
    elif key == "git.base_branch":
        cfg.git.base_branch = value
    elif key == "git.destination_branch":
        cfg.git.destination_branch = value
    elif key == "git.repo_slug":
        cfg.git.repo_slug = value
    elif key == "worktree_dir":
        cfg.worktree_dir = value
    elif key == "project.test_command":
        cfg.project.test_command = value
    elif key == "project.test_instructions":
        # Allow multiline - read from file if starts with @
        if value.startswith("@"):
            filepath = Path(value[1:])
            if filepath.exists():
                cfg.project.test_instructions = filepath.read_text()
            else:
                console.print(f"[red]File not found: {filepath}[/red]")
                raise typer.Exit(1)
        else:
            cfg.project.test_instructions = value
    elif key == "review.automerge":
        cfg.review.automerge = value.lower() in ("true", "1", "yes")
    elif key == "review.test_before_merge":
        cfg.review.test_before_merge = value.lower() in ("true", "1", "yes")
    elif key == "review.require_all_tests_pass":
        cfg.review.require_all_tests_pass = value.lower() in ("true", "1", "yes")
    elif key.startswith("mcps.enabled"):
        cfg.mcps.enabled = [v.strip() for v in value.split(",")]
    elif key == "workflow.mode":
        if value not in ("review", "yolo"):
            console.print(f"[red]Invalid mode: {value}. Use 'review' or 'yolo'[/red]")
            raise typer.Exit(1)
        cfg.workflow.mode = value
    elif key == "workflow.stop_after_generate":
        cfg.workflow.stop_after_generate = value.lower() in ("true", "1", "yes")
    elif key == "workflow.auto_approve":
        cfg.workflow.auto_approve = value.lower() in ("true", "1", "yes")
    elif key == "workflow.auto_pr":
        cfg.workflow.auto_pr = value.lower() in ("true", "1", "yes")
    elif key == "tools.permission_mode":
        valid_modes = ("default", "acceptEdits", "plan", "dontAsk", "bypassPermissions")
        if value not in valid_modes:
            console.print(f"[red]Invalid mode: {value}. Use one of: {', '.join(valid_modes)}[/red]")
            raise typer.Exit(1)
        cfg.tools.permission_mode = value
    elif key == "tools.allowed_cli":
        cfg.tools.allowed_cli = [v.strip() for v in value.split(",") if v.strip()]
    elif key == "tools.allowed_tools":
        cfg.tools.allowed_tools = [v.strip() for v in value.split(",") if v.strip()]
    elif key == "tools.disallowed_tools":
        cfg.tools.disallowed_tools = [v.strip() for v in value.split(",") if v.strip()]
    elif key == "tools.skip_permissions":
        cfg.tools.skip_permissions = value.lower() in ("true", "1", "yes")
    elif key == "agent.inactivity_timeout":
        try:
            cfg.agent.inactivity_timeout = int(value)
        except ValueError:
            console.print(f"[red]Invalid value: {value}. Must be an integer (seconds)[/red]")
            raise typer.Exit(1)
    elif key == "agent.max_runtime":
        try:
            cfg.agent.max_runtime = int(value)
        except ValueError:
            console.print(f"[red]Invalid value: {value}. Must be an integer (seconds)[/red]")
            raise typer.Exit(1)
    elif key == "agent.max_retries":
        try:
            cfg.agent.max_retries = int(value)
        except ValueError:
            console.print(f"[red]Invalid value: {value}. Must be an integer[/red]")
            raise typer.Exit(1)
    elif key == "agent.use_resume":
        cfg.agent.use_resume = value.lower() in ("true", "1", "yes")
    elif key == "agent.retry_delay":
        try:
            cfg.agent.retry_delay = int(value)
        except ValueError:
            console.print(f"[red]Invalid value: {value}. Must be an integer (seconds)[/red]")
            raise typer.Exit(1)
    else:
        console.print(f"[red]Unknown key: {key}[/red]")
        raise typer.Exit(1)

    save_config(cfg, project_dir)
    console.print(f"[green]✓[/green] Set {key} = {value}")


def _get_nested_value(data: dict, key: str):
    """Get a nested value from a dictionary using dot notation."""
    parts = key.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _set_nested_value(data: dict, key: str, value: str):
    """Set a nested value in a dictionary using dot notation."""
    parts = key.split(".")
    current = data
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]

    # Handle comma-separated values for lists
    if parts[-1] == "enabled":
        current[parts[-1]] = [v.strip() for v in value.split(",")]
    else:
        current[parts[-1]] = value


def _print_nested_config(data: dict, prefix: str = ""):
    """Print nested configuration dictionary."""
    for key, value in data.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                console.print(f"{prefix}{key}.{subkey}: {subvalue}")


@app.command()
def status(
    project_dir: Path = typer.Option(
        Path.cwd(),
        "--project-dir",
        "-d",
        help="Project directory.",
    ),
):
    """Show status of previous run.

    Displays results from the last execution.
    """
    import json

    state_file = project_dir / ".claude-orchestrator" / ".state.json"

    if not state_file.exists():
        console.print("[yellow]No previous run found[/yellow]")
        raise typer.Exit()

    with open(state_file) as f:
        state = json.load(f)

    console.print(f"\n[bold]Last Run: {state.get('timestamp', 'Unknown')}[/bold]\n")

    # Create table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Task")
    table.add_column("Status")
    table.add_column("Branch")
    table.add_column("Notes")

    for result in state.get("results", []):
        status = result.get("status", "unknown")
        status_style = {
            "success": "[green]✓ success[/green]",
            "failed": "[red]✗ failed[/red]",
            "skipped": "[yellow]○ skipped[/yellow]",
        }.get(status, status)

        notes = result.get("pr_url") or result.get("error") or ""

        table.add_row(
            result.get("task_id", ""),
            status_style,
            result.get("branch", ""),
            notes[:50] + "..." if len(notes) > 50 else notes,
        )

    console.print(table)


def _select_prs_interactive(prs: list[PRInfo]) -> list[PRInfo]:
    """Interactive PR selector using Rich.

    Args:
        prs: List of available PRs

    Returns:
        List of selected PRs
    """
    from rich.prompt import Prompt

    if not prs:
        console.print("[yellow]No open PRs found[/yellow]")
        return []

    console.print("\n[bold]Available Pull Requests:[/bold]\n")

    # Display PRs in a table
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim")
    table.add_column("ID")
    table.add_column("Title")
    table.add_column("Branch")
    table.add_column("Author")

    for i, pr in enumerate(prs, 1):
        table.add_row(
            str(i),
            str(pr.id),
            pr.title[:50] + "..." if len(pr.title) > 50 else pr.title,
            pr.source_branch,
            pr.author or "Unknown",
        )

    console.print(table)
    console.print()

    # Get selection
    selection = Prompt.ask(
        "Select PRs to review (comma-separated numbers, 'all', or 'q' to quit)",
        default="all",
    )

    if selection.lower() == "q":
        return []

    if selection.lower() == "all":
        return prs

    # Parse selection
    try:
        indices = [int(x.strip()) - 1 for x in selection.split(",")]
        selected = [prs[i] for i in indices if 0 <= i < len(prs)]
        return selected
    except (ValueError, IndexError):
        console.print("[red]Invalid selection[/red]")
        return []


def _print_review_summary(results: list[ReviewResult]) -> None:
    """Print review summary.

    Args:
        results: List of review results
    """
    console.print("\n" + "=" * 60)
    console.print("[bold]REVIEW SUMMARY[/bold]")
    console.print("=" * 60)

    for result in results:
        status_emoji = {
            "approved": "[green]✓[/green]",
            "merged": "[green]✓✓[/green]",
            "changes_requested": "[yellow]![/yellow]",
            "failed": "[red]✗[/red]",
        }.get(result.status, "?")

        console.print(f"\n{status_emoji} PR #{result.pr_id}")
        console.print(f"  Status: {result.status}")
        console.print(f"  URL: {result.pr_url}")
        if result.error:
            console.print(f"  Error: {result.error}")
        if result.session_id and result.status == "failed":
            console.print(f"  Session ID (for manual resume): {result.session_id}")

    approved = sum(1 for r in results if r.status in ("approved", "merged"))
    failed = sum(1 for r in results if r.status == "failed")

    console.print(f"\n{approved}/{len(results)} PRs reviewed successfully")
    if failed > 0:
        console.print(f"[red]{failed} PR(s) failed review[/red]")


@app.command()
def cleanup(
    project_dir: Path = typer.Option(
        Path.cwd(),
        "--project-dir",
        "-d",
        help="Project directory.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force cleanup without confirmation.",
    ),
):
    """Clean up all orchestrator worktrees.

    Removes all worktrees created by the orchestrator:
    - task-* worktrees from run phase
    - review-pr-* worktrees from review phase
    - Any orphaned worktrees in the worktrees directory

    Also prunes stale worktree references from git.

    Examples:
        claude-orchestrator cleanup           # Interactive confirmation
        claude-orchestrator cleanup --force   # No confirmation
    """
    config = load_config(project_dir)
    worktree_dir = config.worktree_dir

    # Determine worktree base path for display
    if worktree_dir.startswith("../"):
        worktree_base = project_dir.parent / worktree_dir[3:]
    elif worktree_dir.startswith("./"):
        worktree_base = project_dir / worktree_dir[2:]
    else:
        worktree_base = (
            Path(worktree_dir) if worktree_dir.startswith("/") else project_dir / worktree_dir
        )

    console.print("\n[bold]Cleanup Worktrees[/bold]")
    console.print(f"Directory: {worktree_base}\n")

    if not worktree_base.exists():
        console.print("[dim]No worktrees directory found.[/dim]")
        return

    # List existing worktrees
    if worktree_base.exists():
        items = list(worktree_base.iterdir())
        if items:
            console.print("Found worktrees:")
            for item in items:
                if item.is_dir():
                    console.print(f"  - {item.name}")
        else:
            console.print("[dim]No worktrees to clean up.[/dim]")
            return

    if not force:
        if not typer.confirm("\nRemove all worktrees?"):
            console.print("[dim]Cancelled.[/dim]")
            return

    cleaned = cleanup_all_worktrees(project_dir, worktree_dir)
    console.print(f"\n[green]✓[/green] Cleaned up {cleaned} worktree(s)")


@app.command()
def review(
    pr_id: int | None = typer.Option(
        None,
        "--pr",
        "-p",
        help="Review a specific PR by ID.",
    ),
    from_run: bool = typer.Option(
        False,
        "--from-run",
        "-r",
        help="Review PRs from the last run (uses .state.json).",
    ),
    automerge: bool = typer.Option(
        False,
        "--automerge",
        "-m",
        help="Automatically merge PRs after successful review.",
    ),
    auto_approve: bool = typer.Option(
        False,
        "--auto-approve",
        "-y",
        help="Automatically approve all agent plans.",
    ),
    sequential: bool = typer.Option(
        True,
        "--sequential/--parallel",
        help="Run reviews sequentially (default) or in parallel.",
    ),
    project_dir: Path = typer.Option(
        Path.cwd(),
        "--project-dir",
        "-d",
        help="Project directory.",
    ),
):
    """Review and test pull requests using Claude Code agents.

    Modes:
      - Interactive (default): List open PRs and select which to review
      - --pr ID: Review a specific PR by ID
      - --from-run: Review PRs created in the last orchestrator run

    The review agent will:
      1. Checkout the PR branch
      2. Review code changes
      3. Run tests (using project.test_instructions if configured)
      4. Fix issues if found
      5. Approve or request changes

    Examples:
        claude-orchestrator review              # Interactive selection
        claude-orchestrator review --pr 42     # Review PR #42
        claude-orchestrator review --from-run  # Review PRs from last run
        claude-orchestrator review --automerge # Auto-merge after review
    """
    config = load_config(project_dir)

    # Validate and prompt for missing config
    config = validate_and_prompt_config(config, project_dir)

    provider_status = get_provider_status(str(project_dir))

    if not provider_status.is_ready:
        console.print(f"[red]Error: Git provider not ready: {provider_status.error}[/red]")
        raise typer.Exit(1)

    # Apply config defaults
    automerge = automerge or config.review.automerge
    auto_approve = auto_approve or config.workflow.auto_approve

    prs_to_review: list[PRInfo] = []

    # Mode 1: Specific PR
    if pr_id is not None:
        console.print(f"[bold]Fetching PR #{pr_id}...[/bold]")
        pr = fetch_pr_by_id(
            provider_status,
            project_dir,
            pr_id,
            config.git.repo_slug,
        )
        if not pr:
            console.print(f"[red]Error: PR #{pr_id} not found[/red]")
            raise typer.Exit(1)
        prs_to_review = [pr]

    # Mode 2: From last run
    elif from_run:
        console.print("[bold]Loading PRs from last run...[/bold]")
        state_file = project_dir / ".claude-orchestrator" / ".state.json"
        prs_to_review = load_prs_from_state(state_file)
        if not prs_to_review:
            console.print("[yellow]No PRs found from last run[/yellow]")
            raise typer.Exit()

        # Fetch full PR info
        full_prs = []
        for pr in prs_to_review:
            full_pr = fetch_pr_by_id(
                provider_status,
                project_dir,
                pr.id,
                config.git.repo_slug,
            )
            if full_pr:
                full_prs.append(full_pr)
        prs_to_review = full_prs

    # Mode 3: Interactive selection
    else:
        console.print("[bold]Fetching open PRs...[/bold]")
        all_prs = fetch_open_prs(
            provider_status,
            project_dir,
            config.git.repo_slug,
        )
        prs_to_review = _select_prs_interactive(all_prs)

    if not prs_to_review:
        console.print("[yellow]No PRs selected for review[/yellow]")
        raise typer.Exit()

    # Confirm review
    console.print(f"\n[bold]Reviewing {len(prs_to_review)} PR(s):[/bold]")
    for pr in prs_to_review:
        console.print(f"  - #{pr.id}: {pr.title}")

    if automerge:
        console.print(
            "\n[yellow]⚠ Automerge enabled - PRs will be merged after successful review[/yellow]"
        )

    # Run reviews
    console.print("\n[bold]Starting review...[/bold]\n")
    results = review_prs_sync(
        prs=prs_to_review,
        repo_root=project_dir,
        config=config,
        automerge=automerge,
        auto_approve=auto_approve,
        sequential=sequential,
    )

    # Print summary
    _print_review_summary(results)

    # Exit code
    failed = sum(1 for r in results if r.status == "failed")
    raise typer.Exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    app()
