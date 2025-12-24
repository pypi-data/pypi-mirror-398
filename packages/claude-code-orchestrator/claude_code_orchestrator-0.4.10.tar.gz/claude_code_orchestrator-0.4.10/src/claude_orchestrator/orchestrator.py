"""Orchestrator for running parallel Claude Code agents on multiple tasks.

Each task runs in its own git worktree with a dedicated agent instance.
Supports plan mode with manual or automatic approval, and creates PRs on completion.

Features:
- Inactivity timeout: Detects stuck agents and terminates them
- Retry with resume: Uses `claude --resume` to continue from where it left off
- Parallel execution: Run multiple agents simultaneously
"""

from __future__ import annotations

import asyncio
import json
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from claude_orchestrator.config import AgentConfig, Config
from claude_orchestrator.discovery import ProjectContext, discover_sync
from claude_orchestrator.git_provider import (
    GitProviderStatus,
    get_pr_instructions,
    get_provider_status,
)
from claude_orchestrator.task_generator import TaskConfig, TasksConfig


@dataclass
class AgentRunResult:
    """Result of a single agent execution attempt."""

    success: bool
    exit_code: int
    session_id: str | None = None  # For claude --resume
    timeout_type: str | None = None  # "inactivity" or "max_runtime"
    output_lines: int = 0
    duration_seconds: float = 0.0


@dataclass
class TaskResult:
    """Result of running a task."""

    task_id: str
    status: str  # "success", "failed", "skipped", "timeout"
    branch: str
    worktree_path: Path | None = None
    pr_url: str | None = None
    pr_id: int | None = None  # PR number/ID for use in review phase
    error: str | None = None
    attempts: int = 0
    session_id: str | None = None


def run_git(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a git command and return result.

    Args:
        args: Git command arguments
        cwd: Working directory

    Returns:
        CompletedProcess with result
    """
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def create_worktree(
    branch: str,
    worktree_dir: Path,
    base_branch: str = "main",
    repo_root: Path | None = None,
) -> Path:
    """Create a git worktree for the given branch.

    Args:
        branch: Branch name to create
        worktree_dir: Base directory for worktrees
        base_branch: Branch to base the new branch on
        repo_root: Root of the repository

    Returns:
        Path to the created worktree
    """
    if repo_root is None:
        repo_root = Path.cwd()

    worktree_path = worktree_dir / branch
    worktree_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing worktree if present
    if worktree_path.exists():
        run_git(["worktree", "remove", "--force", str(worktree_path)], cwd=repo_root)

    # Fetch latest from origin
    run_git(["fetch", "origin", base_branch], cwd=repo_root)

    # Create new worktree with new branch
    result = run_git(
        ["worktree", "add", "-b", branch, str(worktree_path), f"origin/{base_branch}"],
        cwd=repo_root,
    )
    if result.returncode != 0:
        # Branch might already exist, try without -b
        run_git(["branch", "-D", branch], cwd=repo_root)  # Delete local branch if exists
        result = run_git(
            ["worktree", "add", "-b", branch, str(worktree_path), f"origin/{base_branch}"],
            cwd=repo_root,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create worktree: {result.stderr}")

    # Copy .env to worktree if exists
    env_file = repo_root / ".env"
    if env_file.exists():
        shutil.copy(env_file, worktree_path / ".env")

    return worktree_path


def cleanup_worktree(branch: str, worktree_dir: Path, repo_root: Path | None = None) -> None:
    """Remove a git worktree.

    Args:
        branch: Branch name
        worktree_dir: Base directory for worktrees
        repo_root: Root of the repository
    """
    if repo_root is None:
        repo_root = Path.cwd()

    worktree_path = worktree_dir / branch
    if worktree_path.exists():
        run_git(["worktree", "remove", "--force", str(worktree_path)], cwd=repo_root)


def cleanup_all_worktrees(repo_root: Path | None = None, worktree_dir: str = "../worktrees") -> int:
    """Remove all orchestrator-created worktrees.

    Cleans up worktrees that match orchestrator naming patterns:
    - task-* (from run phase)
    - review-pr-* (from review phase)
    - feature/* (legacy)

    Args:
        repo_root: Root of the repository
        worktree_dir: Relative path to worktrees directory

    Returns:
        Number of worktrees cleaned up
    """
    if repo_root is None:
        repo_root = Path.cwd()

    # Determine worktree base path
    if worktree_dir.startswith("../"):
        worktree_base = repo_root.parent / worktree_dir[3:]
    elif worktree_dir.startswith("./"):
        worktree_base = repo_root / worktree_dir[2:]
    else:
        worktree_base = (
            Path(worktree_dir) if worktree_dir.startswith("/") else repo_root / worktree_dir
        )

    if not worktree_base.exists():
        return 0

    cleaned = 0
    # Get list of worktrees from git
    result = run_git(["worktree", "list", "--porcelain"], cwd=repo_root)
    if result.returncode != 0:
        return 0

    # Parse worktree list
    worktree_paths = []
    for line in result.stdout.split("\n"):
        if line.startswith("worktree "):
            path = Path(line.replace("worktree ", "").strip())
            # Only clean orchestrator worktrees (not the main repo)
            if path != repo_root and str(worktree_base) in str(path):
                worktree_paths.append(path)

    # Also check directory for any orphaned worktrees
    if worktree_base.exists():
        for item in worktree_base.iterdir():
            if item.is_dir() and item not in worktree_paths:
                worktree_paths.append(item)

    # Clean each worktree
    for wt_path in worktree_paths:
        try:
            run_git(["worktree", "remove", "--force", str(wt_path)], cwd=repo_root)
            cleaned += 1
        except Exception:
            # Try removing directory directly if git worktree remove fails
            try:
                shutil.rmtree(wt_path)
                cleaned += 1
            except Exception:
                pass

    # Prune worktree references
    run_git(["worktree", "prune"], cwd=repo_root)

    # Clean up empty directories in worktree base
    if worktree_base.exists():
        for item in worktree_base.iterdir():
            if item.is_dir():
                try:
                    # Check if directory is empty or only has .git file
                    contents = list(item.iterdir())
                    if not contents or (len(contents) == 1 and contents[0].name == ".git"):
                        shutil.rmtree(item)
                        cleaned += 1
                except Exception:
                    pass

    return cleaned


def build_agent_prompt(
    task: TaskConfig,
    provider_status: GitProviderStatus,
    project_context: ProjectContext | None = None,
    config: Config | None = None,
) -> str:
    """Build the prompt for a Claude Code agent.

    Args:
        task: Task configuration
        provider_status: Git provider status
        project_context: Discovered project context
        config: Project configuration

    Returns:
        Prompt string for the agent
    """
    # Files hint
    files_list = (
        "\n".join(f"- {f}" for f in task.files_hint)
        if task.files_hint
        else "- Determine based on task"
    )

    # Test section - use test_instructions if available, fallback to test_command
    if config and config.project.test_instructions:
        # Use detailed test instructions from config
        test_section = f"## Testing\n{config.project.test_instructions}"
    else:
        # Fallback to simple test command (config > task > manual)
        test_command = (
            (config.project.test_command if config else None)
            or task.test_command
            or "Manual verification - document steps in commit message"
        )
        test_section = f"""## Testing
Run tests before committing: {test_command}
Only commit if tests pass."""

    # Agent instructions path
    agent_instructions = ""
    if config and config.project.agent_instructions:
        agent_instructions = (
            f"\nRead the instructions in {config.project.agent_instructions} before starting.\n"
        )

    # Destination branch
    dest_branch = config.git.destination_branch if config else "main"
    repo_slug = config.git.repo_slug if config else None

    # PR instructions
    pr_instructions = get_pr_instructions(
        provider_status=provider_status,
        branch=task.branch,
        title=task.title,
        description=task.description[:200] + "..."
        if len(task.description) > 200
        else task.description,
        dest_branch=dest_branch,
        repo_slug=repo_slug,
    )

    return f"""{agent_instructions}
## Task: {task.title}

{task.description}

## Relevant Files
{files_list}

## Requirements
1. Implement the functionality described above
2. Follow project standards and conventions
3. Add tests if applicable
4. Only modify files within scope

{test_section}

## When Complete
Create a commit with a descriptive message following project conventions.

{pr_instructions}
"""


def build_claude_args(config: Config | None, auto_approve: bool = False) -> list[str]:
    """Build Claude CLI arguments from config.

    Args:
        config: Project configuration
        auto_approve: Whether to auto-approve agent plans

    Returns:
        List of CLI arguments
    """
    args = []

    if config and config.tools:
        tools = config.tools

        # Permission mode
        if tools.skip_permissions or auto_approve:
            args.append("--dangerously-skip-permissions")
        elif tools.permission_mode != "default":
            args.extend(["--permission-mode", tools.permission_mode])

        # Allowed tools - combine CLI tools with explicit allowed tools
        allowed = list(tools.allowed_tools)
        for cli_tool in tools.allowed_cli:
            # Convert CLI tool name to Bash pattern
            allowed.append(f"Bash({cli_tool}:*)")
        if allowed:
            args.extend(["--allowedTools"] + allowed)

        # Disallowed tools
        if tools.disallowed_tools:
            args.extend(["--disallowedTools"] + tools.disallowed_tools)

        # Additional directories
        for add_dir in tools.add_dirs:
            args.extend(["--add-dir", add_dir])

    elif auto_approve:
        args.append("--dangerously-skip-permissions")

    return args


def _extract_session_id(log_content: str) -> str | None:
    """Extract Claude session ID from log output for resume capability.

    Args:
        log_content: Content of the log file

    Returns:
        Session ID if found, None otherwise
    """
    # Claude outputs session ID in format: "Session ID: abc123-def456..."
    # or in JSON output format
    patterns = [
        r"Session ID[:\s]+([a-f0-9-]+)",
        r'"session_id"[:\s]+"([a-f0-9-]+)"',
        r"--resume\s+([a-f0-9-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, log_content, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def _format_json_event_for_log(event: dict) -> str:
    """Convert a stream-json event to human-readable log text.

    Args:
        event: Parsed JSON event from claude stream-json output

    Returns:
        Human-readable string for logging
    """
    event_type = event.get("type", "unknown")

    if event_type == "system" and event.get("subtype") == "init":
        session_id = event.get("session_id", "unknown")
        model = event.get("model", "unknown")
        return f"[INIT] Session: {session_id[:8]}... Model: {model}\n"

    elif event_type == "stream_event":
        # Handle streaming events - extract partial content
        inner_event = event.get("event", {})
        inner_type = inner_event.get("type", "")

        if inner_type == "content_block_delta":
            delta = inner_event.get("delta", {})
            delta_type = delta.get("type", "")

            if delta_type == "text_delta":
                # Streaming text output - return immediately for real-time display
                return delta.get("text", "")
            # Skip input_json_delta - tool input being built
            return ""

        elif inner_type == "content_block_stop":
            return "\n"

        elif inner_type == "message_stop":
            return "\n---\n"

        # Skip other stream events
        return ""

    elif event_type == "assistant":
        # Use assistant events for tool info (has complete input)
        msg = event.get("message", {})
        content = msg.get("content", [])
        lines = []
        if isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "tool_use":
                    tool_name = item.get("name", "unknown")
                    tool_input = item.get("input", {})
                    if isinstance(tool_input, dict):
                        if "command" in tool_input:
                            cmd = tool_input["command"]
                            if len(cmd) > 100:
                                cmd = cmd[:100] + "..."
                            lines.append(f"[TOOL] {tool_name}: {cmd}")
                        elif "file_path" in tool_input or "path" in tool_input:
                            path = tool_input.get("file_path") or tool_input.get("path", "")
                            lines.append(f"[TOOL] {tool_name}: {path}")
                        else:
                            lines.append(f"[TOOL] {tool_name}")
                    else:
                        lines.append(f"[TOOL] {tool_name}")
                # Skip text - already shown via stream_event
        return "\n".join(lines) + "\n" if lines else ""

    elif event_type == "user":
        # Tool result - check both locations where content might be
        result_text = ""
        tool_name = ""

        # First check tool_use_result.stdout (for Bash and similar tools)
        tool_result = event.get("tool_use_result", {})
        if tool_result and isinstance(tool_result, dict):
            result_text = tool_result.get("stdout", "")
            tool_name = tool_result.get("tool_name", "")

        # Also check message.content for MCP results
        if not result_text:
            content_list = event.get("message", {}).get("content", [])
            if isinstance(content_list, list):
                for item in content_list:
                    if not isinstance(item, dict):
                        continue
                    if item.get("type") == "tool_result":
                        content = item.get("content", "")
                        # Content can be string or list of objects
                        if isinstance(content, str) and content:
                            result_text = content
                            break
                        elif isinstance(content, list):
                            # Extract text from list of content objects
                            texts = []
                            for c in content:
                                if isinstance(c, dict) and c.get("type") == "text":
                                    texts.append(c.get("text", ""))
                                elif isinstance(c, str):
                                    texts.append(c)
                            if texts:
                                result_text = "\n".join(texts)
                                break

        # Format result with size info for large responses
        if result_text:
            result_len = len(result_text)
            if result_len > 1000:
                # For very large results (like PR diffs), show summary
                preview = result_text[:200].replace("\n", " ")
                tool_info = f" from {tool_name}" if tool_name else ""
                return f"[RESULT{tool_info}] ({result_len:,} chars) {preview}...\n"
            elif result_len > 500:
                result_text = result_text[:500] + f"... [{result_len} chars]"
            return f"[RESULT] {result_text}\n"
        return ""

    elif event_type == "result":
        result = event.get("result", "")
        if len(result) > 500:
            result = result[:500] + "..."
        duration = event.get("duration_ms", 0) / 1000
        return f"\n[COMPLETE] Duration: {duration:.1f}s\n{result}\n"

    return ""


async def _stream_and_monitor(
    process: asyncio.subprocess.Process,
    log_file: Path,
    agent_config: AgentConfig,
    task_id: str,
) -> AgentRunResult:
    """Stream subprocess JSON output to file while monitoring for timeouts.

    Processes stream-json format from claude CLI, extracting human-readable
    logs and detecting activity in real-time.

    Args:
        process: Running subprocess with stdout=PIPE (stream-json format)
        log_file: Path to write human-readable output
        agent_config: Agent timeout/retry configuration
        task_id: Task identifier for logging

    Returns:
        AgentRunResult with details about the run
    """
    start_time = time.time()
    last_activity_time = start_time
    last_bytes_time = start_time  # Track when we last received ANY bytes
    event_count = 0
    bytes_received = 0
    session_id: str | None = None
    line_buffer = b""
    process_done = asyncio.Event()

    async def read_and_process():
        """Read JSON lines from subprocess and convert to human-readable log."""
        nonlocal \
            last_activity_time, \
            last_bytes_time, \
            event_count, \
            session_id, \
            line_buffer, \
            bytes_received

        with open(log_file, "w") as f:
            while True:
                try:
                    # Check if process has ended
                    if process.returncode is not None:
                        # Process any remaining buffer
                        if line_buffer:
                            try:
                                event = json.loads(line_buffer.decode())
                                readable = _format_json_event_for_log(event)
                                if readable:
                                    f.write(readable)
                                    f.flush()
                            except (json.JSONDecodeError, UnicodeDecodeError):
                                f.write(line_buffer.decode(errors="replace") + "\n")
                                f.flush()
                        break

                    # Read chunks with short timeout to check process status frequently
                    chunk = await asyncio.wait_for(process.stdout.read(4096), timeout=1.0)
                    if not chunk:
                        # EOF - process finished
                        break

                    # Update activity times - receiving ANY bytes counts as activity
                    now = time.time()
                    last_bytes_time = now
                    bytes_received += len(chunk)

                    # Add to buffer and process complete lines
                    line_buffer += chunk
                    while b"\n" in line_buffer:
                        line, line_buffer = line_buffer.split(b"\n", 1)
                        # We got a complete JSON event - this is real activity
                        last_activity_time = now

                        try:
                            event = json.loads(line.decode())
                            event_count += 1

                            # Extract session_id from init event
                            if event.get("type") == "system" and event.get("subtype") == "init":
                                session_id = event.get("session_id")

                            # Convert to human-readable and write
                            readable = _format_json_event_for_log(event)
                            if readable:
                                f.write(readable)
                                f.flush()

                        except json.JSONDecodeError:
                            # Not valid JSON, write raw
                            f.write(line.decode(errors="replace") + "\n")
                            f.flush()

                except TimeoutError:
                    # Timeout on read - check if process is still running
                    if process.returncode is not None:
                        break
                    continue
                except Exception as e:
                    # Log unexpected errors
                    f.write(f"\n[ERROR] Stream read error: {e}\n")
                    f.flush()
                    break

        process_done.set()

    async def monitor_timeouts():
        """Monitor for inactivity and max runtime timeouts."""
        last_reported_minute = 0
        last_reported_bytes = 0

        while not process_done.is_set():
            await asyncio.sleep(5)

            # Check if process has terminated
            if process.returncode is not None:
                return None

            current_time = time.time()
            elapsed = current_time - start_time

            # Check max runtime
            if elapsed > agent_config.max_runtime:
                print(
                    f"[{task_id}] Max runtime ({agent_config.max_runtime}s) exceeded after {event_count} events, terminating..."
                )
                return "max_runtime"

            # For inactivity, we check both:
            # 1. Time since last complete JSON event (real activity)
            # 2. Time since we received ANY bytes (data still flowing)
            inactivity_duration = current_time - last_activity_time
            bytes_stalled_duration = current_time - last_bytes_time

            # If no bytes at all for inactivity_timeout, agent is truly stuck
            if bytes_stalled_duration > agent_config.inactivity_timeout:
                print(
                    f"[{task_id}] No data received for {int(bytes_stalled_duration)}s ({event_count} events, {bytes_received} bytes total), terminating..."
                )
                return "inactivity"

            # Log progress every minute, or when we're receiving data but no complete events
            current_minute = int(elapsed) // 60
            if current_minute > last_reported_minute or (
                bytes_received > last_reported_bytes + 10000  # Every 10KB
            ):
                last_reported_minute = current_minute
                last_reported_bytes = bytes_received

                # Show different message if we're receiving data but no complete events
                if bytes_received > 0 and inactivity_duration > 30:
                    print(
                        f"[{task_id}] Running {int(elapsed)}s: {event_count} events, {bytes_received} bytes (receiving large response...)"
                    )
                else:
                    print(
                        f"[{task_id}] Running {int(elapsed)}s: {event_count} events, {bytes_received} bytes"
                    )

        return None

    # Run reader and monitor concurrently
    reader_task = asyncio.create_task(read_and_process())
    monitor_task = asyncio.create_task(monitor_timeouts())

    done, pending = await asyncio.wait(
        [reader_task, monitor_task], return_when=asyncio.FIRST_COMPLETED
    )

    timeout_type = None

    if monitor_task in done:
        timeout_type = monitor_task.result()
        if timeout_type:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=10)
            except TimeoutError:
                process.kill()
                await process.wait()

            reader_task.cancel()
            try:
                await reader_task
            except asyncio.CancelledError:
                pass

    if reader_task in done:
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
        # Wait for process to fully terminate
        try:
            await asyncio.wait_for(process.wait(), timeout=5)
        except TimeoutError:
            pass

    for task in pending:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    elapsed = time.time() - start_time
    log_content = log_file.read_text() if log_file.exists() else ""

    # Final status log
    print(
        f"[{task_id}] Completed in {elapsed:.1f}s: {event_count} events, {bytes_received} bytes, exit={process.returncode}"
    )

    return AgentRunResult(
        success=process.returncode == 0 if timeout_type is None else False,
        exit_code=process.returncode or -1,
        session_id=session_id or _extract_session_id(log_content),
        timeout_type=timeout_type,
        output_lines=log_content.count("\n"),
        duration_seconds=elapsed,
    )


async def run_agent(
    task: TaskConfig,
    worktree_path: Path,
    provider_status: GitProviderStatus,
    project_context: ProjectContext | None = None,
    config: Config | None = None,
    auto_approve: bool = False,
    log_file: Path | None = None,
) -> AgentRunResult:
    """Run Claude Code agent for a task with activity monitoring.

    Args:
        task: Task configuration
        worktree_path: Path to the worktree
        provider_status: Git provider status
        project_context: Discovered project context
        config: Project configuration
        auto_approve: Whether to auto-approve the plan
        log_file: Path to write agent output

    Returns:
        AgentRunResult with success status and session info
    """
    prompt = build_agent_prompt(task, provider_status, project_context, config)
    agent_config = config.agent if config else AgentConfig()

    # Build claude command with tools/permissions config
    cmd = ["claude"]
    cmd.extend(build_claude_args(config, auto_approve))

    # Use stream-json for real-time monitoring in auto-approve mode
    if auto_approve:
        cmd.extend(
            [
                "--print",
                "--output-format",
                "stream-json",
                "--include-partial-messages",
                "--verbose",
                "-p",
                prompt,
            ]
        )
    else:
        cmd.extend(["--print", "--verbose", "-p", prompt])

    # Ensure log file exists for monitoring
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
    else:
        # Create temp log file for monitoring
        log_file = worktree_path / ".claude-agent.log"

    # Initialize empty log file
    log_file.write_text("")

    start_time = time.time()

    try:
        # Use PIPE to capture output and write to file ourselves
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=worktree_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            stdin=asyncio.subprocess.DEVNULL if auto_approve else None,
        )

        if not auto_approve:
            # Interactive mode - no monitoring, just wait and capture
            stdout, _ = await process.communicate()
            elapsed = time.time() - start_time

            # Write output to log file
            output_text = stdout.decode() if stdout else ""
            log_file.write_text(output_text)

            return AgentRunResult(
                success=process.returncode == 0,
                exit_code=process.returncode or 0,
                session_id=_extract_session_id(output_text),
                output_lines=output_text.count("\n"),
                duration_seconds=elapsed,
            )

        # Auto-approve mode with activity monitoring
        # Stream output to file while monitoring
        result = await _stream_and_monitor(process, log_file, agent_config, task.id)
        return result

    except Exception:
        elapsed = time.time() - start_time
        return AgentRunResult(
            success=False,
            exit_code=-1,
            timeout_type=None,
            duration_seconds=elapsed,
        )


async def run_agent_with_resume(
    task: TaskConfig,
    worktree_path: Path,
    provider_status: GitProviderStatus,
    session_id: str,
    config: Config | None = None,
    auto_approve: bool = False,
    log_file: Path | None = None,
) -> AgentRunResult:
    """Resume a Claude Code agent session.

    Args:
        task: Task configuration
        worktree_path: Path to the worktree
        provider_status: Git provider status
        session_id: Previous session ID to resume
        config: Project configuration
        auto_approve: Whether to auto-approve the plan
        log_file: Path to write agent output

    Returns:
        AgentRunResult with success status
    """
    agent_config = config.agent if config else AgentConfig()

    # Build resume command
    cmd = ["claude"]
    cmd.extend(build_claude_args(config, auto_approve))

    # Use stream-json for real-time monitoring in auto-approve mode
    if auto_approve:
        cmd.extend(
            [
                "--resume",
                session_id,
                "--print",
                "--output-format",
                "stream-json",
                "--include-partial-messages",
                "--verbose",
            ]
        )
    else:
        cmd.extend(["--resume", session_id, "--print", "--verbose"])

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        # Append retry marker to existing log
        with open(log_file, "a") as f:
            f.write(f"\n\n--- RETRY (resuming session {session_id}) ---\n\n")
    else:
        log_file = worktree_path / ".claude-agent.log"

    start_time = time.time()

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=worktree_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            stdin=asyncio.subprocess.DEVNULL if auto_approve else None,
        )

        if not auto_approve:
            stdout, _ = await process.communicate()
            elapsed = time.time() - start_time
            output_text = stdout.decode() if stdout else ""

            # Append to log file
            with open(log_file, "a") as f:
                f.write(output_text)

            return AgentRunResult(
                success=process.returncode == 0,
                exit_code=process.returncode or 0,
                session_id=session_id,
                output_lines=output_text.count("\n"),
                duration_seconds=elapsed,
            )

        # Auto-approve mode with stream monitoring
        result = await _stream_and_monitor(process, log_file, agent_config, task.id)
        # Preserve session ID for next retry
        if not result.session_id:
            result.session_id = session_id
        return result

    except Exception:
        elapsed = time.time() - start_time
        return AgentRunResult(
            success=False,
            exit_code=-1,
            session_id=session_id,
            duration_seconds=elapsed,
        )


def push_branch(branch: str, worktree_path: Path) -> bool:
    """Push branch to origin.

    Args:
        branch: Branch name
        worktree_path: Path to the worktree

    Returns:
        True if push succeeded
    """
    result = run_git(["push", "-u", "origin", branch], cwd=worktree_path)
    return result.returncode == 0


async def run_task(
    task: TaskConfig,
    config: Config,
    provider_status: GitProviderStatus,
    project_context: ProjectContext | None = None,
    auto_approve: bool = False,
    dry_run: bool = False,
    no_pr: bool = False,
    logs_dir: Path | None = None,
) -> TaskResult:
    """Run a single task end-to-end with retry support.

    Args:
        task: Task configuration
        config: Project configuration
        provider_status: Git provider status
        project_context: Discovered project context
        auto_approve: Whether to auto-approve agent plans
        dry_run: Show what would be done without executing
        no_pr: Skip PR creation
        logs_dir: Directory for log files

    Returns:
        TaskResult with status and details
    """
    repo_root = config.project_root or Path.cwd()
    worktree_dir = repo_root / config.worktree_dir
    worktree_path = None
    agent_config = config.agent

    try:
        # Create worktree
        print(f"\n[{task.id}] Creating worktree for branch: {task.branch}")
        if not dry_run:
            worktree_path = create_worktree(
                task.branch,
                worktree_dir,
                config.git.base_branch,
                repo_root,
            )
            print(f"[{task.id}] Worktree created at: {worktree_path}")

        # Prepare log file
        log_file = None
        if logs_dir:
            logs_dir.mkdir(parents=True, exist_ok=True)
            log_file = logs_dir / f"{task.id}.log"

        # Run agent
        print(f"[{task.id}] Running Claude Code agent...")
        if dry_run:
            print(f"[{task.id}] DRY RUN - Would run agent with prompt:")
            prompt = build_agent_prompt(task, provider_status, project_context, config)
            print(prompt[:500] + "...")
            return TaskResult(
                task_id=task.id,
                status="skipped",
                branch=task.branch,
                error="Dry run",
            )

        # Run agent with retry support
        attempt = 0
        max_attempts = agent_config.max_retries + 1
        session_id: str | None = None

        while attempt < max_attempts:
            attempt += 1

            if attempt > 1:
                print(f"[{task.id}] Retry {attempt - 1}/{agent_config.max_retries}...")
                await asyncio.sleep(agent_config.retry_delay)

            if session_id and agent_config.use_resume:
                # Resume previous session
                print(f"[{task.id}] Resuming session {session_id[:8]}...")
                result = await run_agent_with_resume(
                    task,
                    worktree_path,
                    provider_status,
                    session_id,
                    config,
                    auto_approve=auto_approve,
                    log_file=log_file,
                )
            else:
                # Fresh start
                result = await run_agent(
                    task,
                    worktree_path,
                    provider_status,
                    project_context,
                    config,
                    auto_approve=auto_approve,
                    log_file=log_file,
                )

            if result.success:
                print(f"[{task.id}] Agent completed successfully in {result.duration_seconds:.1f}s")
                break

            # Handle failure
            if result.timeout_type:
                print(
                    f"[{task.id}] Agent timed out ({result.timeout_type}) after {result.duration_seconds:.1f}s"
                )
                if result.session_id:
                    session_id = result.session_id
                    print(f"[{task.id}] Session ID captured for resume: {session_id[:8]}...")
            else:
                print(f"[{task.id}] Agent failed with exit code {result.exit_code}")
                # For non-timeout failures, still try to get session ID
                if result.session_id:
                    session_id = result.session_id

            if attempt >= max_attempts:
                error_msg = f"Agent failed after {attempt} attempt(s)"
                if result.timeout_type:
                    error_msg = (
                        f"Agent timed out ({result.timeout_type}) after {attempt} attempt(s)"
                    )

                return TaskResult(
                    task_id=task.id,
                    status="timeout" if result.timeout_type else "failed",
                    branch=task.branch,
                    worktree_path=worktree_path,
                    error=error_msg,
                    attempts=attempt,
                    session_id=session_id,
                )

        # Agent succeeded - push branch
        print(f"[{task.id}] Pushing branch to origin...")
        if not push_branch(task.branch, worktree_path):
            return TaskResult(
                task_id=task.id,
                status="failed",
                branch=task.branch,
                worktree_path=worktree_path,
                error="Failed to push branch",
                attempts=attempt,
                session_id=session_id,
            )

        # Note: PR creation is now handled by the agent using MCP or gh CLI
        return TaskResult(
            task_id=task.id,
            status="success",
            branch=task.branch,
            worktree_path=worktree_path,
            attempts=attempt,
            session_id=session_id,
        )

    except Exception as e:
        return TaskResult(
            task_id=task.id,
            status="failed",
            branch=task.branch,
            worktree_path=worktree_path,
            error=str(e),
        )


def save_state(results: list[TaskResult], state_file: Path) -> None:
    """Save execution state to file.

    Args:
        results: List of task results
        state_file: Path to state file
    """
    state = {
        "timestamp": datetime.now().isoformat(),
        "results": [
            {
                "task_id": r.task_id,
                "status": r.status,
                "branch": r.branch,
                "pr_url": r.pr_url,
                "pr_id": r.pr_id,
                "error": r.error,
                "attempts": r.attempts,
                "session_id": r.session_id,
            }
            for r in results
        ],
    }
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)


def print_summary(results: list[TaskResult]) -> None:
    """Print execution summary.

    Args:
        results: List of task results
    """
    print("\n" + "=" * 60)
    print("EXECUTION SUMMARY")
    print("=" * 60)

    for result in results:
        status_emoji = {
            "success": "✓",
            "failed": "✗",
            "skipped": "○",
            "timeout": "⏱",
        }.get(result.status, "?")
        print(f"\n{status_emoji} {result.task_id} ({result.branch})")
        print(f"  Status: {result.status}")
        if result.attempts > 1:
            print(f"  Attempts: {result.attempts}")
        if result.pr_url:
            print(f"  PR: {result.pr_url}")
        if result.error:
            print(f"  Error: {result.error}")
        if result.session_id and result.status in ("failed", "timeout"):
            print(f"  Session ID (for manual resume): {result.session_id}")

    success_count = sum(1 for r in results if r.status == "success")
    timeout_count = sum(1 for r in results if r.status == "timeout")
    failed_count = sum(1 for r in results if r.status == "failed")

    print(f"\n{success_count}/{len(results)} tasks completed successfully")
    if timeout_count:
        print(f"{timeout_count} task(s) timed out")
    if failed_count:
        print(f"{failed_count} task(s) failed")


async def run_tasks(
    tasks_config: TasksConfig,
    config: Config,
    task_ids: list[str] | None = None,
    auto_approve: bool = False,
    keep_worktrees: bool = False,
    dry_run: bool = False,
    no_pr: bool = False,
    sequential: bool = False,
) -> list[TaskResult]:
    """Run multiple tasks.

    Args:
        tasks_config: Tasks configuration
        config: Project configuration
        task_ids: Specific task IDs to run (None = all)
        auto_approve: Whether to auto-approve agent plans
        keep_worktrees: Don't cleanup worktrees after completion
        dry_run: Show what would be done without executing
        no_pr: Skip PR creation
        sequential: Run tasks sequentially instead of in parallel

    Returns:
        List of TaskResult objects
    """
    repo_root = config.project_root or Path.cwd()

    # Get provider status
    provider_status = get_provider_status(str(repo_root))

    if not provider_status.is_ready and not dry_run:
        print(f"Warning: Git provider not ready: {provider_status.error}")

    # Discover project context
    project_context = discover_sync(repo_root, use_claude=False)

    # Filter tasks
    tasks = tasks_config.tasks
    if task_ids:
        tasks = [t for t in tasks if t.id in task_ids]

    if not tasks:
        print("No tasks to run")
        return []

    print(f"Running {len(tasks)} task(s):")
    for task in tasks:
        print(f"  - {task.id}: {task.title}")

    # Prepare logs directory
    logs_dir = repo_root / ".claude-orchestrator" / "logs"

    # Run tasks
    results: list[TaskResult] = []

    if sequential:
        # Run sequentially
        for task in tasks:
            result = await run_task(
                task,
                config,
                provider_status,
                project_context,
                auto_approve,
                dry_run,
                no_pr,
                logs_dir,
            )
            results.append(result)
    else:
        # Run in parallel
        coros = [
            run_task(
                task,
                config,
                provider_status,
                project_context,
                auto_approve,
                dry_run,
                no_pr,
                logs_dir,
            )
            for task in tasks
        ]
        results = list(await asyncio.gather(*coros))

    # Cleanup worktrees
    if not keep_worktrees and not dry_run:
        worktree_dir = repo_root / config.worktree_dir
        print("\nCleaning up worktrees...")
        for task in tasks:
            cleanup_worktree(task.branch, worktree_dir, repo_root)

    # Save state
    state_file = repo_root / ".claude-orchestrator" / ".state.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    save_state(results, state_file)

    # Print summary
    print_summary(results)

    return results


def run_tasks_sync(
    tasks_config: TasksConfig,
    config: Config,
    task_ids: list[str] | None = None,
    auto_approve: bool = False,
    keep_worktrees: bool = False,
    dry_run: bool = False,
    no_pr: bool = False,
    sequential: bool = False,
) -> list[TaskResult]:
    """Synchronous wrapper for run_tasks.

    Args:
        tasks_config: Tasks configuration
        config: Project configuration
        task_ids: Specific task IDs to run (None = all)
        auto_approve: Whether to auto-approve agent plans
        keep_worktrees: Don't cleanup worktrees after completion
        dry_run: Show what would be done without executing
        no_pr: Skip PR creation
        sequential: Run tasks sequentially instead of in parallel

    Returns:
        List of TaskResult objects
    """
    return asyncio.run(
        run_tasks(
            tasks_config,
            config,
            task_ids,
            auto_approve,
            keep_worktrees,
            dry_run,
            no_pr,
            sequential,
        )
    )
