"""Claude Orchestrator - Run parallel Claude Code agents on multiple tasks."""

__version__ = "0.4.8"

from claude_orchestrator.config import Config, ReviewConfig, load_config
from claude_orchestrator.git_provider import GitProvider, GitProviderStatus, get_provider_status
from claude_orchestrator.mcp_registry import AuthType, MCPDefinition, MCP_REGISTRY
from claude_orchestrator.reviewer import PRInfo, ReviewResult, review_prs_sync

__all__ = [
    "__version__",
    "Config",
    "ReviewConfig",
    "load_config",
    "GitProvider",
    "GitProviderStatus",
    "get_provider_status",
    "AuthType",
    "MCPDefinition",
    "MCP_REGISTRY",
    "PRInfo",
    "ReviewResult",
    "review_prs_sync",
]

