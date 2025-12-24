"""Configuration handling for claude-orchestrator.

Handles loading, saving, and validating configuration:
- Global: ~/.config/claude-orchestrator/config.yaml
- Project: .claude-orchestrator.yaml
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from claude_orchestrator.git_provider import (
    get_current_branch,
    get_default_branch,
    parse_remote_url,
)
from claude_orchestrator.mcp_registry import AuthType, register_custom_mcp

CONFIG_FILENAME = ".claude-orchestrator.yaml"
GLOBAL_CONFIG_DIR = Path.home() / ".config" / "claude-orchestrator"
GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / "config.yaml"


@dataclass
class GitConfig:
    """Git-related configuration."""

    provider: str = "auto"  # "auto", "bitbucket", "github"
    base_branch: str = "main"
    destination_branch: str = "main"
    repo_slug: str | None = None  # Required for Bitbucket
    owner: str | None = None  # For GitHub
    repo: str | None = None  # For GitHub


@dataclass
class AgentConfig:
    """Agent execution configuration."""

    # Inactivity timeout in seconds (no output = agent is stuck)
    # Default: 300s (5 minutes)
    inactivity_timeout: int = 300

    # Total timeout for an agent task in seconds
    # Default: 3600s (1 hour)
    max_runtime: int = 3600

    # Number of retry attempts on timeout or failure
    max_retries: int = 2

    # Whether to use claude --resume for retries (preserves session state)
    use_resume: bool = True

    # Delay between retries in seconds
    retry_delay: int = 5


@dataclass
class WorkflowConfig:
    """Workflow mode configuration."""

    # Execution mode: "review" (stop after each step), "yolo" (run everything)
    mode: str = "review"

    # Fine-grained stop points (only apply in "review" mode)
    stop_after_generate: bool = True  # Stop after generating tasks
    stop_after_run: bool = False  # Stop after running tasks (before PRs)

    # Auto-approve agent actions (dangerous but fast)
    auto_approve: bool = False

    # Create PRs automatically
    auto_pr: bool = True


@dataclass
class ToolsConfig:
    """Tools and permissions configuration for Claude Code agents."""

    # Permission mode: default, acceptEdits, plan, dontAsk, bypassPermissions
    permission_mode: str = "default"

    # Allowed CLI tools (e.g., ["gh", "az", "aws", "docker"])
    # These get added to --allowedTools as Bash patterns
    allowed_cli: list[str] = field(default_factory=list)

    # Explicitly allowed tools (e.g., ["Bash(git:*)", "Edit", "Read"])
    allowed_tools: list[str] = field(default_factory=list)

    # Explicitly disallowed tools (e.g., ["Bash(rm:*)"])
    disallowed_tools: list[str] = field(default_factory=list)

    # Additional directories to allow access
    add_dirs: list[str] = field(default_factory=list)

    # Dangerously skip all permissions (only for sandboxed environments)
    skip_permissions: bool = False


@dataclass
class MCPConfig:
    """MCP-related configuration."""

    enabled: list[str] = field(default_factory=list)
    custom: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ReviewConfig:
    """PR review phase configuration."""

    # Automatically merge PRs after successful review
    automerge: bool = False

    # Run tests before approving/merging
    test_before_merge: bool = True

    # Require all tests to pass before merge
    require_all_tests_pass: bool = True

    # Inherit tools config from main tools section (if None, uses same tools)
    tools: ToolsConfig | None = None


@dataclass
class ProjectConfig:
    """Project context configuration."""

    key_files: list[str] = field(default_factory=list)
    test_command: str | None = None
    # Detailed testing instructions in markdown format
    # When provided, overrides test_command in agent prompts
    test_instructions: str | None = None
    agent_instructions: str | None = None


@dataclass
class Config:
    """Main configuration for claude-orchestrator."""

    git: GitConfig = field(default_factory=GitConfig)
    worktree_dir: str = "../worktrees"
    mcps: MCPConfig = field(default_factory=MCPConfig)
    project: ProjectConfig = field(default_factory=ProjectConfig)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    review: ReviewConfig = field(default_factory=ReviewConfig)

    # Runtime settings (not persisted)
    project_root: Path | None = None


def _merge_configs(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two configuration dictionaries.

    Args:
        base: Base configuration (lower priority)
        override: Override configuration (higher priority)

    Returns:
        Merged configuration dictionary
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value
    return result


def load_global_config() -> dict[str, Any]:
    """Load global configuration from ~/.config/claude-orchestrator/config.yaml.

    Returns:
        Dictionary with global configuration values
    """
    if not GLOBAL_CONFIG_FILE.exists():
        return {}

    try:
        with open(GLOBAL_CONFIG_FILE) as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def save_global_config(data: dict[str, Any]) -> None:
    """Save global configuration.

    Args:
        data: Configuration dictionary to save
    """
    GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(GLOBAL_CONFIG_FILE, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def load_config(project_root: Path | None = None) -> Config:
    """Load configuration from .claude-orchestrator.yaml with global fallbacks.

    Configuration is loaded in this order (later overrides earlier):
    1. Default values
    2. Global config (~/.config/claude-orchestrator/config.yaml)
    3. Project config (.claude-orchestrator.yaml)

    Args:
        project_root: Root directory of the project. If None, uses current directory.

    Returns:
        Config object with loaded or default values
    """
    if project_root is None:
        project_root = Path.cwd()

    config_path = project_root / CONFIG_FILENAME
    config = Config(project_root=project_root)

    # Load global config first
    global_data = load_global_config()

    # Load project config
    project_data: dict[str, Any] = {}
    if config_path.exists():
        try:
            with open(config_path) as f:
                project_data = yaml.safe_load(f) or {}
        except Exception:
            pass

    # Merge: global -> project (project overrides global)
    data = _merge_configs(global_data, project_data)

    if not data:
        return config

    # Parse git config
    if "git" in data:
        git_data = data["git"]
        config.git = GitConfig(
            provider=git_data.get("provider", "auto"),
            base_branch=git_data.get("base_branch", "main"),
            destination_branch=git_data.get("destination_branch", "main"),
            repo_slug=git_data.get("repo_slug"),
            owner=git_data.get("owner"),
            repo=git_data.get("repo"),
        )

    # Auto-detect repo_slug and owner/repo from git remote if not configured
    if not config.git.repo_slug or not config.git.owner:
        repo_info = parse_remote_url(str(project_root))
        if repo_info:
            if not config.git.repo_slug:
                config.git.repo_slug = repo_info.get("repo")
            if not config.git.owner:
                config.git.owner = repo_info.get("owner")
            if not config.git.repo:
                config.git.repo = repo_info.get("repo")

    # Auto-detect base_branch: prefer current branch if it's a main/develop branch,
    # otherwise check for develop, then fallback to remote default
    if config.git.base_branch == "main":
        current = get_current_branch(str(project_root))
        # Use current branch if it's a base branch (main, master, develop, dev)
        base_branch_names = {"main", "master", "develop", "dev", "development"}
        if current and current in base_branch_names:
            config.git.base_branch = current
            config.git.destination_branch = current
        else:
            # Check if 'develop' branch exists (common workflow)
            import subprocess

            result = subprocess.run(
                ["git", "rev-parse", "--verify", "origin/develop"],
                capture_output=True,
                cwd=str(project_root),
            )
            if result.returncode == 0:
                config.git.base_branch = "develop"
                config.git.destination_branch = "develop"
            else:
                # Fallback to remote default branch
                detected_branch = get_default_branch(str(project_root))
                if detected_branch:
                    config.git.base_branch = detected_branch
                    config.git.destination_branch = detected_branch

    # Ensure destination_branch matches base_branch if not explicitly set
    if config.git.destination_branch == "main" and config.git.base_branch != "main":
        config.git.destination_branch = config.git.base_branch

    # Parse worktree_dir
    if "worktree_dir" in data:
        config.worktree_dir = data["worktree_dir"]

    # Parse MCP config
    if "mcps" in data:
        mcps_data = data["mcps"]
        config.mcps = MCPConfig(
            enabled=mcps_data.get("enabled", []),
            custom=mcps_data.get("custom", []),
        )

        # Register custom MCPs
        for custom_mcp in config.mcps.custom:
            register_custom_mcp(
                name=custom_mcp.get("name", ""),
                package=custom_mcp.get("package", ""),
                auth_type=AuthType(custom_mcp.get("auth_type", "env_vars")),
                env_vars=custom_mcp.get("env_vars", []),
                setup_instructions=custom_mcp.get("setup_instructions", ""),
            )

    # Parse project config
    if "project" in data:
        project_data = data["project"]
        config.project = ProjectConfig(
            key_files=project_data.get("key_files", []),
            test_command=project_data.get("test_command"),
            test_instructions=project_data.get("test_instructions"),
            agent_instructions=project_data.get("agent_instructions"),
        )

    # Parse workflow config
    if "workflow" in data:
        workflow_data = data["workflow"]
        config.workflow = WorkflowConfig(
            mode=workflow_data.get("mode", "review"),
            stop_after_generate=workflow_data.get("stop_after_generate", True),
            stop_after_run=workflow_data.get("stop_after_run", False),
            auto_approve=workflow_data.get("auto_approve", False),
            auto_pr=workflow_data.get("auto_pr", True),
        )

    # Parse tools config
    if "tools" in data:
        tools_data = data["tools"]
        config.tools = ToolsConfig(
            permission_mode=tools_data.get("permission_mode", "default"),
            allowed_cli=tools_data.get("allowed_cli", []),
            allowed_tools=tools_data.get("allowed_tools", []),
            disallowed_tools=tools_data.get("disallowed_tools", []),
            add_dirs=tools_data.get("add_dirs", []),
            skip_permissions=tools_data.get("skip_permissions", False),
        )

    # Parse agent config
    if "agent" in data:
        agent_data = data["agent"]
        config.agent = AgentConfig(
            inactivity_timeout=agent_data.get("inactivity_timeout", 300),
            max_runtime=agent_data.get("max_runtime", 3600),
            max_retries=agent_data.get("max_retries", 2),
            use_resume=agent_data.get("use_resume", True),
            retry_delay=agent_data.get("retry_delay", 5),
        )

    # Parse review config
    if "review" in data:
        review_data = data["review"]
        review_tools = None
        if "tools" in review_data and review_data["tools"]:
            tools_data = review_data["tools"]
            review_tools = ToolsConfig(
                permission_mode=tools_data.get("permission_mode", "default"),
                allowed_cli=tools_data.get("allowed_cli", []),
                allowed_tools=tools_data.get("allowed_tools", []),
                disallowed_tools=tools_data.get("disallowed_tools", []),
                add_dirs=tools_data.get("add_dirs", []),
                skip_permissions=tools_data.get("skip_permissions", False),
            )
        config.review = ReviewConfig(
            automerge=review_data.get("automerge", False),
            test_before_merge=review_data.get("test_before_merge", True),
            require_all_tests_pass=review_data.get("require_all_tests_pass", True),
            tools=review_tools,
        )

    return config


def save_config(config: Config, project_root: Path | None = None) -> None:
    """Save configuration to .claude-orchestrator.yaml.

    Args:
        config: Configuration to save
        project_root: Root directory of the project. If None, uses config.project_root or cwd.
    """
    if project_root is None:
        project_root = config.project_root or Path.cwd()

    config_path = project_root / CONFIG_FILENAME

    data: dict[str, Any] = {}

    # Git config
    git_data: dict[str, Any] = {
        "provider": config.git.provider,
        "base_branch": config.git.base_branch,
        "destination_branch": config.git.destination_branch,
    }
    if config.git.repo_slug:
        git_data["repo_slug"] = config.git.repo_slug
    if config.git.owner:
        git_data["owner"] = config.git.owner
    if config.git.repo:
        git_data["repo"] = config.git.repo
    data["git"] = git_data

    # Worktree dir
    data["worktree_dir"] = config.worktree_dir

    # MCPs config
    if config.mcps.enabled or config.mcps.custom:
        mcps_data: dict[str, Any] = {}
        if config.mcps.enabled:
            mcps_data["enabled"] = config.mcps.enabled
        if config.mcps.custom:
            mcps_data["custom"] = config.mcps.custom
        data["mcps"] = mcps_data

    # Project config
    if (
        config.project.key_files
        or config.project.test_command
        or config.project.test_instructions
        or config.project.agent_instructions
    ):
        project_data: dict[str, Any] = {}
        if config.project.key_files:
            project_data["key_files"] = config.project.key_files
        if config.project.test_command:
            project_data["test_command"] = config.project.test_command
        if config.project.test_instructions:
            project_data["test_instructions"] = config.project.test_instructions
        if config.project.agent_instructions:
            project_data["agent_instructions"] = config.project.agent_instructions
        data["project"] = project_data

    # Workflow config (only save non-default values)
    workflow_data: dict[str, Any] = {}
    if config.workflow.mode != "review":
        workflow_data["mode"] = config.workflow.mode
    if not config.workflow.stop_after_generate:
        workflow_data["stop_after_generate"] = config.workflow.stop_after_generate
    if config.workflow.stop_after_run:
        workflow_data["stop_after_run"] = config.workflow.stop_after_run
    if config.workflow.auto_approve:
        workflow_data["auto_approve"] = config.workflow.auto_approve
    if not config.workflow.auto_pr:
        workflow_data["auto_pr"] = config.workflow.auto_pr
    if workflow_data:
        data["workflow"] = workflow_data

    # Tools config (only save non-default values)
    tools_data: dict[str, Any] = {}
    if config.tools.permission_mode != "default":
        tools_data["permission_mode"] = config.tools.permission_mode
    if config.tools.allowed_cli:
        tools_data["allowed_cli"] = config.tools.allowed_cli
    if config.tools.allowed_tools:
        tools_data["allowed_tools"] = config.tools.allowed_tools
    if config.tools.disallowed_tools:
        tools_data["disallowed_tools"] = config.tools.disallowed_tools
    if config.tools.add_dirs:
        tools_data["add_dirs"] = config.tools.add_dirs
    if config.tools.skip_permissions:
        tools_data["skip_permissions"] = config.tools.skip_permissions
    if tools_data:
        data["tools"] = tools_data

    # Agent config (only save non-default values)
    agent_data: dict[str, Any] = {}
    if config.agent.inactivity_timeout != 300:
        agent_data["inactivity_timeout"] = config.agent.inactivity_timeout
    if config.agent.max_runtime != 3600:
        agent_data["max_runtime"] = config.agent.max_runtime
    if config.agent.max_retries != 2:
        agent_data["max_retries"] = config.agent.max_retries
    if not config.agent.use_resume:
        agent_data["use_resume"] = config.agent.use_resume
    if config.agent.retry_delay != 5:
        agent_data["retry_delay"] = config.agent.retry_delay
    if agent_data:
        data["agent"] = agent_data

    # Review config (only save non-default values)
    review_data: dict[str, Any] = {}
    if config.review.automerge:
        review_data["automerge"] = config.review.automerge
    if not config.review.test_before_merge:
        review_data["test_before_merge"] = config.review.test_before_merge
    if not config.review.require_all_tests_pass:
        review_data["require_all_tests_pass"] = config.review.require_all_tests_pass
    if config.review.tools:
        # Save review-specific tools config
        review_tools_data: dict[str, Any] = {}
        if config.review.tools.permission_mode != "default":
            review_tools_data["permission_mode"] = config.review.tools.permission_mode
        if config.review.tools.allowed_cli:
            review_tools_data["allowed_cli"] = config.review.tools.allowed_cli
        if config.review.tools.allowed_tools:
            review_tools_data["allowed_tools"] = config.review.tools.allowed_tools
        if config.review.tools.disallowed_tools:
            review_tools_data["disallowed_tools"] = config.review.tools.disallowed_tools
        if config.review.tools.add_dirs:
            review_tools_data["add_dirs"] = config.review.tools.add_dirs
        if config.review.tools.skip_permissions:
            review_tools_data["skip_permissions"] = config.review.tools.skip_permissions
        if review_tools_data:
            review_data["tools"] = review_tools_data
    if review_data:
        data["review"] = review_data

    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def config_exists(project_root: Path | None = None) -> bool:
    """Check if configuration file exists.

    Args:
        project_root: Root directory of the project. If None, uses current directory.

    Returns:
        True if config file exists
    """
    if project_root is None:
        project_root = Path.cwd()

    return (project_root / CONFIG_FILENAME).exists()
