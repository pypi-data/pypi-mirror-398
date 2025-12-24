"""Extensible MCP registry with authentication types.

Manages MCP definitions, checks configuration status, and provides
setup instructions for various MCPs.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from enum import Enum


class AuthType(Enum):
    """Authentication types for MCPs."""

    ENV_VARS = "env_vars"  # Simple env vars (BITBUCKET_TOKEN, DATABASE_URL)
    OAUTH_BROWSER = "oauth_browser"  # Requires browser auth flow
    PRE_CONFIGURED = "pre_configured"  # No auth needed, just check if running


@dataclass
class MCPDefinition:
    """Definition of an MCP with its configuration requirements."""

    name: str
    package: str  # PyPI or npm package name
    auth_type: AuthType
    env_vars: list[str] = field(default_factory=list)  # Required env vars for ENV_VARS type
    check_command: str | None = None  # Command to check if ready
    setup_instructions: str = ""
    is_npm: bool = False  # True if this is an npm package


# Built-in MCP registry
MCP_REGISTRY: dict[str, MCPDefinition] = {
    "bitbucket": MCPDefinition(
        name="bitbucket",
        package="mcp-server-bitbucket",
        auth_type=AuthType.ENV_VARS,
        env_vars=["BITBUCKET_WORKSPACE", "BITBUCKET_EMAIL", "BITBUCKET_API_TOKEN"],
        setup_instructions="""\
pipx install mcp-server-bitbucket
claude mcp add bitbucket -s user \\
  -e BITBUCKET_WORKSPACE=your-workspace \\
  -e BITBUCKET_EMAIL=your-email \\
  -e BITBUCKET_API_TOKEN=your-token \\
  -- mcp-server-bitbucket
""",
    ),
    "atlassian": MCPDefinition(
        name="atlassian",
        package="mcp-server-atlassian",
        auth_type=AuthType.OAUTH_BROWSER,
        setup_instructions="""\
pipx install mcp-server-atlassian
claude mcp add atlassian -s user -- mcp-server-atlassian
# First run will open browser for OAuth authentication
""",
    ),
    "linear": MCPDefinition(
        name="linear",
        package="mcp-server-linear",
        auth_type=AuthType.OAUTH_BROWSER,
        setup_instructions="""\
pipx install mcp-server-linear
claude mcp add linear -s user -- mcp-server-linear
# First run will open browser for OAuth authentication
""",
    ),
    "postgres": MCPDefinition(
        name="postgres",
        package="mcp-server-postgres",
        auth_type=AuthType.ENV_VARS,
        env_vars=["DATABASE_URL"],
        setup_instructions="""\
pipx install mcp-server-postgres
claude mcp add postgres -s user \\
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \\
  -- mcp-server-postgres
""",
    ),
    "chrome": MCPDefinition(
        name="chrome",
        package="@anthropic/mcp-server-chrome",
        auth_type=AuthType.PRE_CONFIGURED,
        check_command="pgrep -x 'Google Chrome' || pgrep -x 'chrome'",
        is_npm=True,
        setup_instructions="""\
npm install -g @anthropic/mcp-server-chrome
claude mcp add chrome -s user -- npx @anthropic/mcp-server-chrome
# Ensure Google Chrome is running before using
""",
    ),
    "filesystem": MCPDefinition(
        name="filesystem",
        package="@modelcontextprotocol/server-filesystem",
        auth_type=AuthType.PRE_CONFIGURED,
        is_npm=True,
        setup_instructions="""\
npm install -g @modelcontextprotocol/server-filesystem
claude mcp add filesystem -s user -- npx @modelcontextprotocol/server-filesystem /path/to/allowed/dir
""",
    ),
}


def check_mcp_configured(name: str) -> bool:
    """Check if an MCP is configured in Claude.

    Args:
        name: MCP name to check

    Returns:
        True if the MCP is configured
    """
    try:
        result = subprocess.run(
            ["claude", "mcp", "list"],
            capture_output=True,
            text=True,
        )
        return name.lower() in result.stdout.lower()
    except Exception:
        return False


def check_env_vars(env_vars: list[str]) -> tuple[bool, list[str]]:
    """Check if required environment variables are set.

    Args:
        env_vars: List of required environment variable names

    Returns:
        Tuple of (all_set, missing_vars)
    """
    missing = [var for var in env_vars if not os.environ.get(var)]
    return len(missing) == 0, missing


def check_prerequisite_command(command: str) -> bool:
    """Run a check command to verify prerequisites.

    Args:
        command: Shell command to run

    Returns:
        True if command succeeds (exit code 0)
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
        )
        return result.returncode == 0
    except Exception:
        return False


@dataclass
class MCPStatus:
    """Status of an MCP."""

    name: str
    is_configured: bool
    is_ready: bool
    auth_type: AuthType
    message: str | None = None
    setup_instructions: str | None = None


def get_mcp_status(name: str) -> MCPStatus:
    """Get status of an MCP and setup instructions if needed.

    Args:
        name: MCP name to check

    Returns:
        MCPStatus with configuration and readiness info
    """
    if name not in MCP_REGISTRY:
        return MCPStatus(
            name=name,
            is_configured=False,
            is_ready=False,
            auth_type=AuthType.ENV_VARS,
            message=f"Unknown MCP: {name}. Available: {list(MCP_REGISTRY.keys())}",
        )

    definition = MCP_REGISTRY[name]
    is_configured = check_mcp_configured(name)

    if not is_configured:
        return MCPStatus(
            name=name,
            is_configured=False,
            is_ready=False,
            auth_type=definition.auth_type,
            message=f"MCP '{name}' not configured.",
            setup_instructions=definition.setup_instructions,
        )

    # For OAuth MCPs, we can't easily check auth status - assume configured = ready
    if definition.auth_type == AuthType.OAUTH_BROWSER:
        return MCPStatus(
            name=name,
            is_configured=True,
            is_ready=True,
            auth_type=definition.auth_type,
            message=f"MCP '{name}' configured. First run may require browser auth.",
        )

    # For ENV_VARS type, check if env vars are set
    if definition.auth_type == AuthType.ENV_VARS and definition.env_vars:
        all_set, missing = check_env_vars(definition.env_vars)
        if not all_set:
            return MCPStatus(
                name=name,
                is_configured=True,
                is_ready=False,
                auth_type=definition.auth_type,
                message=f"MCP '{name}' configured but missing env vars: {missing}",
            )

    # For pre-configured, run check command if provided
    if definition.auth_type == AuthType.PRE_CONFIGURED and definition.check_command:
        if not check_prerequisite_command(definition.check_command):
            return MCPStatus(
                name=name,
                is_configured=True,
                is_ready=False,
                auth_type=definition.auth_type,
                message=f"MCP '{name}' configured but prerequisite not met.",
            )

    return MCPStatus(
        name=name,
        is_configured=True,
        is_ready=True,
        auth_type=definition.auth_type,
        message=f"MCP '{name}' ready.",
    )


def register_custom_mcp(
    name: str,
    package: str,
    auth_type: AuthType,
    env_vars: list[str] | None = None,
    check_command: str | None = None,
    setup_instructions: str = "",
    is_npm: bool = False,
) -> None:
    """Register a custom MCP definition.

    Args:
        name: MCP name
        package: PyPI or npm package name
        auth_type: Authentication type
        env_vars: Required environment variables
        check_command: Command to check prerequisites
        setup_instructions: Setup instructions for users
        is_npm: True if this is an npm package
    """
    MCP_REGISTRY[name] = MCPDefinition(
        name=name,
        package=package,
        auth_type=auth_type,
        env_vars=env_vars or [],
        check_command=check_command,
        setup_instructions=setup_instructions,
        is_npm=is_npm,
    )


def get_all_mcp_statuses(names: list[str] | None = None) -> list[MCPStatus]:
    """Get status of multiple MCPs.

    Args:
        names: List of MCP names to check. If None, checks all registered MCPs.

    Returns:
        List of MCPStatus objects
    """
    if names is None:
        names = list(MCP_REGISTRY.keys())

    return [get_mcp_status(name) for name in names]
