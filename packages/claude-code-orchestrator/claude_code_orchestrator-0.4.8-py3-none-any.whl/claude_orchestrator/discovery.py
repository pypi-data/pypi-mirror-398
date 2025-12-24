"""Project discovery via Claude Code analysis.

Automatically analyzes project structure, conventions, and key files
using Claude to generate dynamic context for task execution.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path

from claude_orchestrator.git_provider import GitProvider, detect_provider


@dataclass
class ProjectContext:
    """Discovered project context."""

    project_name: str
    key_files: list[str] = field(default_factory=list)
    test_command: str | None = None
    conventions: str = ""
    tech_stack: list[str] = field(default_factory=list)
    git_provider: GitProvider = GitProvider.UNKNOWN
    has_claude_md: bool = False
    has_readme: bool = False


DISCOVERY_PROMPT = """\
Analyze this project and return ONLY a JSON object (no markdown, no explanation) with:

{{
  "project_name": "name of the project",
  "key_files": ["list", "of", "important", "files"],
  "test_command": "command to run tests or null",
  "conventions": "brief description of code style and conventions",
  "tech_stack": ["python", "flask", "etc"]
}}

Instructions:
1. Read CLAUDE.md if it exists for project context
2. Read README.md for project overview
3. Explore the directory structure
4. Identify the main source files, config files, and test files
5. Determine the testing framework and command

Return ONLY the JSON object, nothing else.
"""


def get_project_files(project_root: Path) -> dict[str, bool]:
    """Check for common project files.

    Args:
        project_root: Root directory of the project

    Returns:
        Dict of filename -> exists
    """
    files_to_check = [
        "CLAUDE.md",
        "README.md",
        "pyproject.toml",
        "package.json",
        "Cargo.toml",
        "go.mod",
        "requirements.txt",
        "setup.py",
        ".claude/AGENT_INSTRUCTIONS.md",
    ]

    return {f: (project_root / f).exists() for f in files_to_check}


def infer_tech_stack(project_files: dict[str, bool]) -> list[str]:
    """Infer technology stack from project files.

    Args:
        project_files: Dict of filename -> exists

    Returns:
        List of detected technologies
    """
    stack = []

    if project_files.get("pyproject.toml") or project_files.get("requirements.txt"):
        stack.append("python")
    if project_files.get("package.json"):
        stack.append("javascript")
    if project_files.get("Cargo.toml"):
        stack.append("rust")
    if project_files.get("go.mod"):
        stack.append("go")

    return stack


def infer_test_command(project_files: dict[str, bool], project_root: Path) -> str | None:
    """Infer test command from project files.

    Args:
        project_files: Dict of filename -> exists
        project_root: Root directory of the project

    Returns:
        Inferred test command or None
    """
    if project_files.get("pyproject.toml"):
        # Check if pytest is configured
        pyproject = project_root / "pyproject.toml"
        content = pyproject.read_text()
        if "pytest" in content:
            return "pytest tests/"
        if "poetry" in content:
            return "poetry run pytest tests/"

    if project_files.get("package.json"):
        return "npm test"

    if project_files.get("Cargo.toml"):
        return "cargo test"

    if project_files.get("go.mod"):
        return "go test ./..."

    return None


def quick_discover(project_root: Path) -> ProjectContext:
    """Quick project discovery without using Claude.

    Uses file system analysis to infer project context.

    Args:
        project_root: Root directory of the project

    Returns:
        ProjectContext with inferred information
    """
    project_files = get_project_files(project_root)
    tech_stack = infer_tech_stack(project_files)
    test_command = infer_test_command(project_files, project_root)
    git_provider = detect_provider(str(project_root))

    # Find key files
    key_files = []
    for pattern in ["src/**/*.py", "src/**/*.ts", "src/**/*.js", "lib/**/*.py", "*.py"]:
        key_files.extend([str(p.relative_to(project_root)) for p in project_root.glob(pattern)])

    # Limit to first 10 key files
    key_files = key_files[:10]

    return ProjectContext(
        project_name=project_root.name,
        key_files=key_files,
        test_command=test_command,
        conventions="",
        tech_stack=tech_stack,
        git_provider=git_provider,
        has_claude_md=project_files.get("CLAUDE.md", False),
        has_readme=project_files.get("README.md", False),
    )


async def discover_with_claude(project_root: Path) -> ProjectContext:
    """Discover project context using Claude Code.

    Runs Claude in print mode to analyze the project.

    Args:
        project_root: Root directory of the project

    Returns:
        ProjectContext with discovered information
    """
    # First do quick discovery for fallback
    quick_context = quick_discover(project_root)

    try:
        cmd = [
            "claude",
            "--print",
            "-p",
            DISCOVERY_PROMPT,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=project_root,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=60,  # 60 second timeout
        )

        if process.returncode != 0:
            # Fall back to quick discovery
            return quick_context

        output = stdout.decode().strip()

        # Try to extract JSON from output
        json_str = output

        # Handle markdown code blocks
        if "```json" in output:
            start = output.find("```json") + 7
            end = output.find("```", start)
            json_str = output[start:end].strip()
        elif "```" in output:
            start = output.find("```") + 3
            end = output.find("```", start)
            json_str = output[start:end].strip()

        # Find JSON object boundaries
        if "{" in json_str:
            start = json_str.find("{")
            # Find matching closing brace
            depth = 0
            for i, char in enumerate(json_str[start:], start):
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        json_str = json_str[start : i + 1]
                        break

        data = json.loads(json_str)

        return ProjectContext(
            project_name=data.get("project_name", quick_context.project_name),
            key_files=data.get("key_files", quick_context.key_files),
            test_command=data.get("test_command", quick_context.test_command),
            conventions=data.get("conventions", ""),
            tech_stack=data.get("tech_stack", quick_context.tech_stack),
            git_provider=quick_context.git_provider,
            has_claude_md=quick_context.has_claude_md,
            has_readme=quick_context.has_readme,
        )

    except TimeoutError:
        return quick_context
    except json.JSONDecodeError:
        return quick_context
    except Exception:
        return quick_context


def discover_sync(project_root: Path, use_claude: bool = True) -> ProjectContext:
    """Synchronous wrapper for project discovery.

    Args:
        project_root: Root directory of the project
        use_claude: Whether to use Claude for discovery

    Returns:
        ProjectContext with discovered information
    """
    if not use_claude:
        return quick_discover(project_root)

    return asyncio.run(discover_with_claude(project_root))
