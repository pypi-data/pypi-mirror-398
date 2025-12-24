"""Git provider detection and verification.

Auto-detects whether the repository is on Bitbucket or GitHub,
and verifies the appropriate tools are installed and authenticated.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum


class GitProvider(Enum):
    """Supported git providers."""

    BITBUCKET = "bitbucket"
    GITHUB = "github"
    UNKNOWN = "unknown"


@dataclass
class GitProviderStatus:
    """Status of git provider detection and tool readiness."""

    provider: GitProvider
    is_ready: bool
    tool: str  # "mcp-server-bitbucket" or "gh"
    error: str | None = None
    repo_info: dict | None = None  # Extracted repo info (owner, repo, etc.)


def detect_provider(cwd: str | None = None) -> GitProvider:
    """Detect git provider from remote URL.

    Args:
        cwd: Working directory to run git command in

    Returns:
        Detected GitProvider enum value
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        if result.returncode != 0:
            return GitProvider.UNKNOWN

        url = result.stdout.strip().lower()

        if "bitbucket.org" in url or "bitbucket.com" in url:
            return GitProvider.BITBUCKET
        elif "github.com" in url:
            return GitProvider.GITHUB

        return GitProvider.UNKNOWN
    except Exception:
        return GitProvider.UNKNOWN


def get_current_branch(cwd: str | None = None) -> str | None:
    """Get the current git branch.

    Args:
        cwd: Working directory

    Returns:
        Current branch name or None
    """
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        if result.returncode == 0:
            return result.stdout.strip() or None
        return None
    except Exception:
        return None


def get_default_branch(cwd: str | None = None) -> str | None:
    """Get the default branch from remote origin.

    Args:
        cwd: Working directory

    Returns:
        Default branch name (e.g., 'main', 'master', 'develop') or None
    """
    try:
        # Try to get from remote
        result = subprocess.run(
            ["git", "remote", "show", "origin"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "HEAD branch:" in line:
                    return line.split(":")[-1].strip()

        # Fallback: check common branch names
        for branch in ["main", "master", "develop"]:
            result = subprocess.run(
                ["git", "rev-parse", "--verify", f"origin/{branch}"],
                capture_output=True,
                text=True,
                cwd=cwd,
            )
            if result.returncode == 0:
                return branch

        return None
    except Exception:
        return None


def parse_remote_url(cwd: str | None = None) -> dict | None:
    """Parse git remote URL to extract owner and repo.

    Args:
        cwd: Working directory to run git command in

    Returns:
        Dict with 'owner' and 'repo' keys, or None if parsing fails
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        if result.returncode != 0:
            return None

        url = result.stdout.strip()

        # Handle SSH URLs: git@github.com:owner/repo.git
        if url.startswith("git@"):
            # git@github.com:owner/repo.git -> owner/repo
            parts = url.split(":")[-1]
            parts = parts.replace(".git", "")
            if "/" in parts:
                owner, repo = parts.split("/", 1)
                return {"owner": owner, "repo": repo}

        # Handle HTTPS URLs: https://github.com/owner/repo.git
        elif "://" in url:
            # Remove .git suffix
            url = url.replace(".git", "")
            # Split by / and get last two parts
            parts = url.split("/")
            if len(parts) >= 2:
                return {"owner": parts[-2], "repo": parts[-1]}

        return None
    except Exception:
        return None


def check_github_cli() -> tuple[bool, str | None]:
    """Check if gh CLI is installed and authenticated.

    Returns:
        Tuple of (is_ready, error_message)
    """
    # Check if installed
    if not shutil.which("gh"):
        return False, (
            "gh CLI not installed.\n"
            "Install with: brew install gh (macOS) or sudo apt install gh (Ubuntu)"
        )

    # Check if authenticated
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return False, ("gh CLI not authenticated.\nRun: gh auth login")

        return True, None
    except Exception as e:
        return False, f"Error checking gh auth status: {e}"


def check_bitbucket_mcp() -> tuple[bool, str | None]:
    """Check if Bitbucket MCP is configured.

    Returns:
        Tuple of (is_ready, error_message)
    """
    try:
        result = subprocess.run(
            ["claude", "mcp", "list"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return False, (
                "Could not check MCP configuration.\nEnsure Claude CLI is installed and working."
            )

        if "bitbucket" not in result.stdout.lower():
            return False, (
                "Bitbucket MCP not configured.\n\n"
                "Setup:\n"
                "  pipx install mcp-server-bitbucket\n"
                "  claude mcp add bitbucket -s user \\\n"
                "    -e BITBUCKET_WORKSPACE=your-workspace \\\n"
                "    -e BITBUCKET_EMAIL=your-email \\\n"
                "    -e BITBUCKET_API_TOKEN=your-token \\\n"
                "    -- mcp-server-bitbucket"
            )

        return True, None
    except FileNotFoundError:
        return False, ("Claude CLI not found.\nEnsure Claude Code is installed.")
    except Exception as e:
        return False, f"Error checking Bitbucket MCP: {e}"


def get_provider_status(cwd: str | None = None) -> GitProviderStatus:
    """Get full status of git provider and tools.

    Args:
        cwd: Working directory for git commands

    Returns:
        GitProviderStatus with provider info and readiness status
    """
    provider = detect_provider(cwd)
    repo_info = parse_remote_url(cwd)

    if provider == GitProvider.GITHUB:
        is_ready, error = check_github_cli()
        return GitProviderStatus(
            provider=provider,
            is_ready=is_ready,
            tool="gh",
            error=error,
            repo_info=repo_info,
        )

    elif provider == GitProvider.BITBUCKET:
        is_ready, error = check_bitbucket_mcp()
        return GitProviderStatus(
            provider=provider,
            is_ready=is_ready,
            tool="mcp-server-bitbucket",
            error=error,
            repo_info=repo_info,
        )

    return GitProviderStatus(
        provider=provider,
        is_ready=False,
        tool="",
        error="Unknown git provider. Only GitHub and Bitbucket are supported.",
        repo_info=repo_info,
    )


def get_pr_instructions(
    provider_status: GitProviderStatus,
    branch: str,
    title: str,
    description: str,
    dest_branch: str = "main",
    repo_slug: str | None = None,
) -> str:
    """Get provider-specific PR creation instructions for agents.

    Args:
        provider_status: Current provider status
        branch: Source branch name
        title: PR title
        description: PR description
        dest_branch: Destination branch
        repo_slug: Repository slug (for Bitbucket)

    Returns:
        Markdown instructions for creating a PR
    """
    if provider_status.provider == GitProvider.GITHUB:
        return f"""
## Creating the Pull Request

After committing your changes:

1. Push the branch:
   ```bash
   git push -u origin {branch}
   ```

2. Create PR using gh CLI:
   ```bash
   gh pr create --title "{title}" --body "{description}" --base {dest_branch}
   ```
"""

    elif provider_status.provider == GitProvider.BITBUCKET:
        slug = repo_slug or (
            provider_status.repo_info.get("repo") if provider_status.repo_info else "REPO_SLUG"
        )
        return f"""
## Creating the Pull Request

After committing your changes:

1. Push the branch:
   ```bash
   git push -u origin {branch}
   ```

2. Use the Bitbucket MCP tool `mcp_bitbucket_create_pull_request`:
   - repo_slug: {slug}
   - title: "{title}"
   - source_branch: "{branch}"
   - destination_branch: "{dest_branch}"
   - description: "{description}"
"""

    return """
## Creating the Pull Request

Push your branch and create the PR manually in the web interface:

```bash
git push -u origin <branch>
```
"""
