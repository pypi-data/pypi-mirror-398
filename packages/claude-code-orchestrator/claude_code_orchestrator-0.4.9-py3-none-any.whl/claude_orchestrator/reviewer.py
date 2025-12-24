"""PR review functionality for claude-orchestrator.

Provides tools for fetching PRs, building review prompts, and running
reviewer agents that test and fix PRs before merge.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from claude_orchestrator.config import Config
from claude_orchestrator.git_provider import GitProvider, GitProviderStatus, get_provider_status
from claude_orchestrator.orchestrator import (
    AgentRunResult,
    _extract_session_id,
    _stream_and_monitor,
    build_claude_args,
    run_git,
)


@dataclass
class PRInfo:
    """Information about a pull request."""

    id: int
    title: str
    source_branch: str
    destination_branch: str
    url: str
    author: str | None = None
    state: str = "OPEN"
    description: str | None = None


def fetch_open_prs_github(repo_root: Path) -> list[PRInfo]:
    """Fetch open PRs from GitHub using gh CLI.

    Args:
        repo_root: Root directory of the repository

    Returns:
        List of PRInfo objects for open PRs
    """
    try:
        result = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--state",
                "open",
                "--json",
                "number,title,headRefName,baseRefName,url,author,body",
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return []

        prs = json.loads(result.stdout)
        return [
            PRInfo(
                id=pr["number"],
                title=pr["title"],
                source_branch=pr["headRefName"],
                destination_branch=pr["baseRefName"],
                url=pr["url"],
                author=pr.get("author", {}).get("login"),
                description=pr.get("body"),
            )
            for pr in prs
        ]
    except Exception:
        return []


def fetch_pr_by_id_github(repo_root: Path, pr_id: int) -> PRInfo | None:
    """Fetch a specific PR from GitHub using gh CLI.

    Args:
        repo_root: Root directory of the repository
        pr_id: PR number to fetch

    Returns:
        PRInfo if found, None otherwise
    """
    try:
        result = subprocess.run(
            [
                "gh",
                "pr",
                "view",
                str(pr_id),
                "--json",
                "number,title,headRefName,baseRefName,url,author,body,state",
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None

        pr = json.loads(result.stdout)
        return PRInfo(
            id=pr["number"],
            title=pr["title"],
            source_branch=pr["headRefName"],
            destination_branch=pr["baseRefName"],
            url=pr["url"],
            author=pr.get("author", {}).get("login"),
            state=pr.get("state", "OPEN"),
            description=pr.get("body"),
        )
    except Exception:
        return None


def fetch_open_prs_bitbucket(repo_slug: str) -> list[PRInfo]:
    """Fetch open PRs from Bitbucket using the REST API.

    Uses environment variables for authentication:
    - BITBUCKET_WORKSPACE: Bitbucket workspace
    - BITBUCKET_EMAIL: User email for auth
    - BITBUCKET_API_TOKEN: App password or API token

    Args:
        repo_slug: Bitbucket repository slug

    Returns:
        List of PRInfo objects for open PRs
    """
    import os

    try:
        import httpx
    except ImportError:
        # Fallback message if httpx not installed
        return []

    workspace = os.getenv("BITBUCKET_WORKSPACE")
    email = os.getenv("BITBUCKET_EMAIL")
    token = os.getenv("BITBUCKET_API_TOKEN")

    if not all([workspace, email, token]):
        return []

    try:
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/pullrequests?state=OPEN"

        with httpx.Client(auth=(email, token), timeout=30) as client:
            response = client.get(url)
            if response.status_code != 200:
                return []
            data = response.json()

        prs = []
        for pr in data.get("values", []):
            prs.append(
                PRInfo(
                    id=pr["id"],
                    title=pr["title"],
                    source_branch=pr["source"]["branch"]["name"],
                    destination_branch=pr["destination"]["branch"]["name"],
                    url=pr["links"]["html"]["href"],
                    author=pr.get("author", {}).get("display_name"),
                    description=pr.get("description"),
                )
            )
        return prs

    except (json.JSONDecodeError, KeyError, httpx.HTTPError):
        return []


def fetch_pr_by_id_bitbucket(repo_slug: str, pr_id: int) -> PRInfo | None:
    """Fetch a specific PR from Bitbucket using the REST API.

    Args:
        repo_slug: Bitbucket repository slug
        pr_id: PR ID to fetch

    Returns:
        PRInfo if found, None otherwise
    """
    import os

    try:
        import httpx
    except ImportError:
        return None

    workspace = os.getenv("BITBUCKET_WORKSPACE")
    email = os.getenv("BITBUCKET_EMAIL")
    token = os.getenv("BITBUCKET_API_TOKEN")

    if not all([workspace, email, token]):
        return None

    try:
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}"

        with httpx.Client(auth=(email, token), timeout=30) as client:
            response = client.get(url)
            if response.status_code != 200:
                return None
            pr = response.json()

        return PRInfo(
            id=pr["id"],
            title=pr["title"],
            source_branch=pr["source"]["branch"]["name"],
            destination_branch=pr["destination"]["branch"]["name"],
            url=pr["links"]["html"]["href"],
            author=pr.get("author", {}).get("display_name"),
            state=pr.get("state", "OPEN"),
            description=pr.get("description"),
        )

    except (json.JSONDecodeError, KeyError, httpx.HTTPError):
        return None


def fetch_open_prs(
    provider_status: GitProviderStatus,
    repo_root: Path,
    repo_slug: str | None = None,
) -> list[PRInfo]:
    """Fetch open PRs based on git provider.

    Args:
        provider_status: Git provider status
        repo_root: Root directory of the repository
        repo_slug: Bitbucket repository slug (required for Bitbucket)

    Returns:
        List of PRInfo objects for open PRs
    """
    if provider_status.provider == GitProvider.GITHUB:
        return fetch_open_prs_github(repo_root)
    elif provider_status.provider == GitProvider.BITBUCKET:
        # For Bitbucket, we'll use MCP - return empty for now
        # The CLI will handle this through agent interaction
        return fetch_open_prs_bitbucket(repo_slug or "")
    return []


def fetch_pr_by_id(
    provider_status: GitProviderStatus,
    repo_root: Path,
    pr_id: int,
    repo_slug: str | None = None,
) -> PRInfo | None:
    """Fetch a specific PR by ID.

    Args:
        provider_status: Git provider status
        repo_root: Root directory of the repository
        pr_id: PR number/ID to fetch
        repo_slug: Bitbucket repository slug (required for Bitbucket)

    Returns:
        PRInfo if found, None otherwise
    """
    if provider_status.provider == GitProvider.GITHUB:
        return fetch_pr_by_id_github(repo_root, pr_id)
    elif provider_status.provider == GitProvider.BITBUCKET:
        return fetch_pr_by_id_bitbucket(repo_slug or "", pr_id)
    return None


def build_reviewer_prompt(
    pr: PRInfo,
    config: Config,
    automerge: bool = False,
) -> str:
    """Build the prompt for a PR reviewer agent.

    Args:
        pr: Pull request information
        config: Project configuration
        automerge: Whether to automerge after successful review

    Returns:
        Prompt string for the reviewer agent
    """
    # Test section - use test_instructions if available
    if config.project.test_instructions:
        test_section = f"""## Testing (MANDATORY)

**You MUST run this exact test command:**
```bash
{config.project.test_instructions}
```

⚠️ DO NOT approve the PR without running this specific test command.
Include the test output in your review comment."""
    elif config.project.test_command:
        test_section = f"""## Testing (MANDATORY)

**Run this test command:**
```bash
{config.project.test_command}
```
All tests must pass before approving."""
    else:
        test_section = """## Testing
Run any available tests to verify the changes work correctly.
Check for regressions and ensure all tests pass."""

    # Merge instructions
    if automerge:
        merge_instructions = """## After Successful Review
If all tests pass and code looks good:
1. Approve the PR
2. Merge the PR (squash merge preferred)
3. Report the merge status"""
    else:
        merge_instructions = """## After Review
1. Add a review comment summarizing your findings
2. If issues found: fix them, commit, and push
3. If all looks good: Approve the PR for human merge"""

    # Agent instructions
    agent_instructions = ""
    if config.project.agent_instructions:
        agent_instructions = (
            f"\nRead the instructions in {config.project.agent_instructions} before starting.\n"
        )

    return f"""{agent_instructions}
## PR Review: {pr.title}

**PR:** {pr.url}
**Branch:** {pr.source_branch} -> {pr.destination_branch}
**Author:** {pr.author or "Unknown"}

{f"**Description:**{chr(10)}{pr.description}" if pr.description else ""}

## Your Task

You are already on the PR branch `{pr.source_branch}` in an isolated worktree.

1. **Review the code changes:**
   - Check for correctness and potential bugs
   - Verify code follows project conventions
   - Look for missing error handling
   - Check for security issues

2. **Run tests** (see Testing section below)

3. **If issues found:**
   - Fix the issues
   - Commit with message: `fix: <description>`
   - Push the changes

4. **Add review comment** with your findings

{test_section}

{merge_instructions}
"""


def get_merge_instructions_github(pr_id: int) -> str:
    """Get GitHub CLI merge instructions."""
    return f"""To merge the PR:
```bash
gh pr merge {pr_id} --squash
```"""


def get_merge_instructions_bitbucket(repo_slug: str, pr_id: int) -> str:
    """Get Bitbucket MCP merge instructions."""
    return f"""To merge the PR, use the MCP tool:
- Tool: mcp_bitbucket_merge_pull_request
- repo_slug: {repo_slug}
- pr_id: {pr_id}
- merge_strategy: squash"""


async def run_reviewer_agent(
    pr: PRInfo,
    repo_root: Path,
    provider_status: GitProviderStatus,
    config: Config,
    automerge: bool = False,
    auto_approve: bool = False,
    log_file: Path | None = None,
) -> AgentRunResult:
    """Run a Claude Code agent to review a PR.

    Creates an isolated worktree for the PR branch to avoid conflicts
    with the main repository.

    Args:
        pr: Pull request to review
        repo_root: Root directory of the repository
        provider_status: Git provider status
        config: Project configuration
        automerge: Whether to automerge after successful review
        auto_approve: Whether to auto-approve agent plans
        log_file: Path to write agent output

    Returns:
        AgentRunResult with success status
    """
    import time

    # Create worktree for the PR branch
    worktree_dir = config.worktree_dir
    if worktree_dir.startswith("../"):
        worktree_base = repo_root.parent / worktree_dir[3:]
    elif worktree_dir.startswith("./"):
        worktree_base = repo_root / worktree_dir[2:]
    else:
        worktree_base = (
            Path(worktree_dir) if worktree_dir.startswith("/") else repo_root / worktree_dir
        )
    worktree_branch = f"review-pr-{pr.id}"

    # Fetch the PR branch first
    run_git(["fetch", "origin", pr.source_branch], cwd=repo_root)

    # Create worktree from the PR source branch
    worktree_path = worktree_base / worktree_branch
    worktree_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing worktree if present
    if worktree_path.exists():
        run_git(["worktree", "remove", "--force", str(worktree_path)], cwd=repo_root)

    # Create worktree tracking the remote PR branch
    result = run_git(
        ["worktree", "add", str(worktree_path), f"origin/{pr.source_branch}"],
        cwd=repo_root,
    )
    if result.returncode != 0:
        return AgentRunResult(
            success=False,
            exit_code=result.returncode,
            duration_seconds=0,
        )

    # Checkout the branch (worktree is in detached HEAD from origin/branch)
    run_git(["checkout", "-B", pr.source_branch, f"origin/{pr.source_branch}"], cwd=worktree_path)
    run_git(["branch", "--set-upstream-to", f"origin/{pr.source_branch}"], cwd=worktree_path)

    prompt = build_reviewer_prompt(pr, config, automerge)

    # Use review-specific tools config if available, otherwise use main tools
    tools_config = config.review.tools if config.review.tools else config.tools
    agent_config = config.agent

    # Build claude command
    cmd = ["claude"]

    # Build args using a temporary config with review tools
    temp_config = Config(tools=tools_config)
    cmd.extend(build_claude_args(temp_config, auto_approve))

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

    # Ensure log file exists (in main repo, not worktree)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
    else:
        log_file = repo_root / ".claude-orchestrator" / "logs" / f"review-pr-{pr.id}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

    log_file.write_text("")

    start_time = time.time()

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=worktree_path,  # Run in worktree
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            stdin=asyncio.subprocess.DEVNULL if auto_approve else None,
        )

        if not auto_approve:
            # Interactive mode
            stdout, _ = await process.communicate()
            elapsed = time.time() - start_time
            output_text = stdout.decode() if stdout else ""
            log_file.write_text(output_text)

            result = AgentRunResult(
                success=process.returncode == 0,
                exit_code=process.returncode or 0,
                session_id=_extract_session_id(output_text),
                output_lines=output_text.count("\n"),
                duration_seconds=elapsed,
            )
        else:
            # Auto-approve mode with monitoring
            result = await _stream_and_monitor(
                process, log_file, agent_config, f"review-pr-{pr.id}"
            )

        return result

    except Exception:
        elapsed = time.time() - start_time
        return AgentRunResult(
            success=False,
            exit_code=-1,
            duration_seconds=elapsed,
        )
    finally:
        # Cleanup worktree after review
        try:
            run_git(["worktree", "remove", "--force", str(worktree_path)], cwd=repo_root)
        except Exception:
            pass  # Best effort cleanup


@dataclass
class ReviewResult:
    """Result of a PR review."""

    pr_id: int
    pr_url: str
    status: str  # "approved", "changes_requested", "merged", "failed"
    review_comment: str | None = None
    error: str | None = None
    session_id: str | None = None


async def review_pr(
    pr: PRInfo,
    repo_root: Path,
    config: Config,
    automerge: bool = False,
    auto_approve: bool = False,
) -> ReviewResult:
    """Review a single PR end-to-end.

    Args:
        pr: Pull request to review
        repo_root: Root directory of the repository
        config: Project configuration
        automerge: Whether to automerge after successful review
        auto_approve: Whether to auto-approve agent plans

    Returns:
        ReviewResult with status and details
    """
    provider_status = get_provider_status(str(repo_root))

    logs_dir = repo_root / ".claude-orchestrator" / "logs"
    log_file = logs_dir / f"review-pr-{pr.id}.log"

    try:
        result = await run_reviewer_agent(
            pr=pr,
            repo_root=repo_root,
            provider_status=provider_status,
            config=config,
            automerge=automerge,
            auto_approve=auto_approve,
            log_file=log_file,
        )

        if result.success:
            status = "merged" if automerge else "approved"
            return ReviewResult(
                pr_id=pr.id,
                pr_url=pr.url,
                status=status,
                session_id=result.session_id,
            )
        else:
            return ReviewResult(
                pr_id=pr.id,
                pr_url=pr.url,
                status="failed",
                error=f"Agent failed with exit code {result.exit_code}",
                session_id=result.session_id,
            )

    except Exception as e:
        return ReviewResult(
            pr_id=pr.id,
            pr_url=pr.url,
            status="failed",
            error=str(e),
        )


async def review_prs(
    prs: list[PRInfo],
    repo_root: Path,
    config: Config,
    automerge: bool = False,
    auto_approve: bool = False,
    sequential: bool = True,
) -> list[ReviewResult]:
    """Review multiple PRs.

    Args:
        prs: List of PRs to review
        repo_root: Root directory of the repository
        config: Project configuration
        automerge: Whether to automerge after successful review
        auto_approve: Whether to auto-approve agent plans
        sequential: Run reviews sequentially (default True for safety)

    Returns:
        List of ReviewResult objects
    """
    if sequential:
        results = []
        for pr in prs:
            result = await review_pr(pr, repo_root, config, automerge, auto_approve)
            results.append(result)
        return results
    else:
        # Parallel review (use with caution)
        coros = [review_pr(pr, repo_root, config, automerge, auto_approve) for pr in prs]
        return list(await asyncio.gather(*coros))


def review_prs_sync(
    prs: list[PRInfo],
    repo_root: Path,
    config: Config,
    automerge: bool = False,
    auto_approve: bool = False,
    sequential: bool = True,
) -> list[ReviewResult]:
    """Synchronous wrapper for review_prs.

    Args:
        prs: List of PRs to review
        repo_root: Root directory of the repository
        config: Project configuration
        automerge: Whether to automerge after successful review
        auto_approve: Whether to auto-approve agent plans
        sequential: Run reviews sequentially

    Returns:
        List of ReviewResult objects
    """
    return asyncio.run(review_prs(prs, repo_root, config, automerge, auto_approve, sequential))


def load_prs_from_state(state_file: Path) -> list[PRInfo]:
    """Load PR information from a previous run state file.

    Args:
        state_file: Path to the state file (.state.json)

    Returns:
        List of PRInfo objects from successful tasks
    """
    if not state_file.exists():
        return []

    try:
        with open(state_file) as f:
            state = json.load(f)

        prs = []
        for result in state.get("results", []):
            if result.get("status") == "success" and result.get("pr_id"):
                prs.append(
                    PRInfo(
                        id=result["pr_id"],
                        title=result.get("task_id", f"PR #{result['pr_id']}"),
                        source_branch=result.get("branch", ""),
                        destination_branch="",  # Will be fetched
                        url=result.get("pr_url", ""),
                    )
                )
        return prs
    except Exception:
        return []
