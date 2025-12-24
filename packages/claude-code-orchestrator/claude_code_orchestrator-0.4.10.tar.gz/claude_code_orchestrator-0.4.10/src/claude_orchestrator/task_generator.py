"""Task generation from todo files using Claude.

Parses todo.md files and generates task configurations for parallel execution.
Supports structured outputs via Anthropic SDK when available.
"""

from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from claude_orchestrator.config import Config
from claude_orchestrator.discovery import ProjectContext

# Check if Anthropic SDK is available
try:
    import anthropic

    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


# Pydantic models for structured outputs
class TaskSchema(BaseModel):
    """Schema for a single task."""

    id: str = Field(description="Short, unique, kebab-case identifier (e.g., 'add-swagger-link')")
    branch: str = Field(
        description="Branch name with feature/ prefix (e.g., 'feature/add-swagger-link')"
    )
    title: str = Field(
        description="Conventional commit title (e.g., 'feat: add swagger link to docs')"
    )
    description: str = Field(
        description="Detailed description with requirements and implementation hints"
    )
    files_hint: list[str] = Field(
        default_factory=list, description="List of files likely to be modified"
    )
    test_command: str | None = Field(
        default=None, description="pytest command or null for UI-only changes"
    )


class TasksConfigSchema(BaseModel):
    """Schema for all tasks configuration."""

    tasks: list[TaskSchema] = Field(description="List of tasks to generate")


# Dataclasses for internal use
@dataclass
class TaskConfig:
    """Configuration for a single task."""

    id: str
    branch: str
    title: str
    description: str
    files_hint: list[str] = field(default_factory=list)
    test_command: str | None = None


@dataclass
class TasksConfig:
    """Configuration for all tasks."""

    settings: dict = field(default_factory=dict)
    tasks: list[TaskConfig] = field(default_factory=list)


def _extract_yaml_from_output(output: str) -> str | None:
    """Extract YAML content from Claude output.

    Handles various output formats:
    - Bare YAML
    - YAML in ```yaml``` fences
    - YAML with preamble text

    Args:
        output: Raw output from Claude

    Returns:
        Extracted YAML string or None
    """
    # First, try to extract from markdown fences
    # Match ```yaml or ``` followed by content
    fence_patterns = [
        re.compile(r"```yaml\n(.*?)```", re.DOTALL),
        re.compile(r"```yml\n(.*?)```", re.DOTALL),
        re.compile(r"```\n(.*?)```", re.DOTALL),
    ]

    for pattern in fence_patterns:
        matches = pattern.findall(output)
        for match in matches:
            # Check if this looks like valid task config
            if "settings:" in match and "tasks:" in match or "tasks:" in match:
                return match.strip()

    # No fenced block found, try to extract by finding YAML markers
    # Look for settings: at the start of a line
    if "\nsettings:" in output or output.startswith("settings:"):
        idx = output.find("settings:")
        yaml_str = output[idx:]
        # Remove any trailing non-YAML content
        return yaml_str.strip()

    # Look for tasks: at the start of a line
    if "\ntasks:" in output or output.startswith("tasks:"):
        idx = output.find("tasks:")
        yaml_str = output[idx:]
        return yaml_str.strip()

    return None


def build_generation_prompt(
    todo_content: str,
    project_context: ProjectContext | None = None,
    config: Config | None = None,
) -> str:
    """Build the prompt for task generation.

    Args:
        todo_content: Content of the todo file
        project_context: Discovered project context
        config: Project configuration

    Returns:
        Prompt string for Claude
    """
    # Build project context section
    context_section = ""
    if project_context:
        context_section = f"""
## Project Context
Project: {project_context.project_name}
Tech Stack: {", ".join(project_context.tech_stack)}
Test Command: {project_context.test_command or "Not configured"}

Key Files:
{chr(10).join(f"- {f}" for f in project_context.key_files[:10])}

Conventions: {project_context.conventions or "Follow existing patterns"}
"""

    # Get settings from config
    base_branch = "main"
    dest_branch = "main"
    repo_slug = "REPO_SLUG"

    if config:
        base_branch = config.git.base_branch
        dest_branch = config.git.destination_branch
        repo_slug = config.git.repo_slug or "REPO_SLUG"

    return f"""Read the following todo list and generate a task_config.yaml for the parallel-tasks orchestrator.

## Todo List
{todo_content}

{context_section}

## Output Requirements

Generate a YAML configuration with this exact structure:

```yaml
settings:
  base_branch: {base_branch}
  destination_branch: {dest_branch}
  worktree_dir: ../worktrees
  repo_slug: {repo_slug}
  auto_cleanup: true

tasks:
  - id: <short-kebab-case-id>
    branch: feature/<descriptive-branch-name>
    title: "feat: <concise title>"
    description: |
      <Detailed description of what needs to be done>

      Requirements:
      - <Specific requirement 1>
      - <Specific requirement 2>

      Implementation hints:
      - <Helpful hint about how to implement>
    files_hint:
      - <file1.py>
      - <file2.html>
    test_command: "<pytest command or null>"
```

## Guidelines for Each Task

1. **id**: Short, unique, kebab-case (e.g., "add-swagger-link")
2. **branch**: Use feature/ prefix with descriptive name
3. **title**: Follow conventional commits (feat:, fix:, refactor:, etc.)
4. **description**:
   - Be specific about what to implement
   - List concrete requirements
   - Include implementation hints when helpful
   - Reference existing patterns in the codebase
5. **files_hint**: List the most likely files to modify
6. **test_command**: pytest command or null for UI-only changes

## Important
- Output ONLY the YAML content, no markdown fences or explanations
- Make descriptions detailed enough that another Claude agent can implement without ambiguity
- Consider dependencies between tasks (if any)

Generate the task_config.yaml now:
"""


def _build_settings(config: Config | None) -> dict:
    """Build settings dict from config.

    Args:
        config: Project configuration

    Returns:
        Settings dictionary
    """
    settings = {
        "worktree_dir": "../worktrees",
        "auto_cleanup": True,
    }
    if config:
        settings["base_branch"] = config.git.base_branch
        settings["destination_branch"] = config.git.destination_branch
        if config.git.repo_slug:
            settings["repo_slug"] = config.git.repo_slug
    return settings


async def _generate_with_sdk(
    todo_content: str,
    project_context: ProjectContext | None = None,
    config: Config | None = None,
) -> TasksConfig | None:
    """Generate tasks using Anthropic SDK with structured outputs.

    Args:
        todo_content: Content of the todo file
        project_context: Discovered project context
        config: Project configuration

    Returns:
        TasksConfig or None if generation fails
    """
    if not HAS_ANTHROPIC:
        return None

    # Build a simpler prompt for structured outputs (no YAML format needed)
    context_section = ""
    if project_context:
        context_section = f"""
Project: {project_context.project_name}
Tech Stack: {", ".join(project_context.tech_stack)}
Test Command: {project_context.test_command or "Not configured"}
Key Files: {", ".join(project_context.key_files[:10])}
"""

    prompt = f"""Analyze this todo list and generate tasks for parallel Claude Code agents.

## Todo List
{todo_content}

{context_section}

## Guidelines
- id: Short, kebab-case (e.g., "add-swagger-link")
- branch: feature/ prefix (e.g., "feature/add-swagger-link")
- title: Conventional commits (feat:, fix:, refactor:, etc.)
- description: Be specific with requirements and implementation hints
- files_hint: List likely files to modify
- test_command: pytest command or null for UI-only changes

Only include tasks that are NOT already marked as done/completed."""

    try:
        client = anthropic.Anthropic()

        # Use structured outputs
        response = client.beta.messages.parse(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
            betas=["structured-outputs-2025-11-13"],
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            output_format=TasksConfigSchema,
        )

        parsed = response.parsed_output
        if not parsed or not parsed.tasks:
            return None

        # Convert to TaskConfig dataclasses
        tasks = [
            TaskConfig(
                id=task.id,
                branch=task.branch,
                title=task.title,
                description=task.description,
                files_hint=task.files_hint or [],
                test_command=task.test_command,
            )
            for task in parsed.tasks
        ]

        return TasksConfig(
            settings=_build_settings(config),
            tasks=tasks,
        )

    except Exception:
        return None


async def _generate_with_cli(
    todo_path: Path,
    todo_content: str,
    project_context: ProjectContext | None = None,
    config: Config | None = None,
) -> TasksConfig | None:
    """Generate tasks using Claude CLI (fallback method).

    Args:
        todo_path: Path to the todo file
        todo_content: Content of the todo file
        project_context: Discovered project context
        config: Project configuration

    Returns:
        TasksConfig or None if generation fails
    """
    prompt = build_generation_prompt(todo_content, project_context, config)
    project_root = todo_path.parent

    cmd = [
        "claude",
        "--print",
        "-p",
        prompt,
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=project_root,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=300,  # 5 minute timeout for complex prompts
        )

        if process.returncode != 0:
            return None

        output = stdout.decode().strip()

        yaml_str = _extract_yaml_from_output(output)
        if not yaml_str:
            return None

        # Parse YAML
        try:
            data = yaml.safe_load(yaml_str)
        except yaml.YAMLError:
            return None

        if not data or "tasks" not in data:
            return None

        # Convert to TasksConfig
        tasks = []
        for task_data in data.get("tasks", []):
            tasks.append(
                TaskConfig(
                    id=task_data.get("id", ""),
                    branch=task_data.get("branch", ""),
                    title=task_data.get("title", ""),
                    description=task_data.get("description", ""),
                    files_hint=task_data.get("files_hint", []),
                    test_command=task_data.get("test_command"),
                )
            )

        return TasksConfig(
            settings=_build_settings(config),
            tasks=tasks,
        )

    except TimeoutError:
        return None
    except yaml.YAMLError:
        return None
    except Exception:
        return None


async def generate_tasks_with_claude(
    todo_path: Path,
    project_context: ProjectContext | None = None,
    config: Config | None = None,
    use_sdk: bool = True,
) -> TasksConfig | None:
    """Generate task configuration from a todo file using Claude.

    Uses Anthropic SDK with structured outputs if available,
    falls back to Claude CLI otherwise.

    Args:
        todo_path: Path to the todo file
        project_context: Discovered project context
        config: Project configuration
        use_sdk: Whether to try using the SDK first (default: True)

    Returns:
        TasksConfig or None if generation fails
    """
    if not todo_path.exists():
        return None

    todo_content = todo_path.read_text()

    # Try SDK with structured outputs first (if available and enabled)
    if use_sdk and HAS_ANTHROPIC and os.getenv("ANTHROPIC_API_KEY"):
        result = await _generate_with_sdk(todo_content, project_context, config)
        if result:
            return result

    # Fallback to CLI
    return await _generate_with_cli(todo_path, todo_content, project_context, config)


def generate_tasks_sync(
    todo_path: Path,
    project_context: ProjectContext | None = None,
    config: Config | None = None,
    use_sdk: bool = True,
) -> TasksConfig | None:
    """Synchronous wrapper for task generation.

    Args:
        todo_path: Path to the todo file
        project_context: Discovered project context
        config: Project configuration
        use_sdk: Whether to try using the SDK first (default: True)

    Returns:
        TasksConfig or None if generation fails
    """
    return asyncio.run(generate_tasks_with_claude(todo_path, project_context, config, use_sdk))


def save_tasks_config(tasks_config: TasksConfig, output_path: Path) -> None:
    """Save tasks configuration to a YAML file.

    Args:
        tasks_config: Tasks configuration to save
        output_path: Path to save the YAML file
    """
    data = {
        "settings": tasks_config.settings,
        "tasks": [
            {
                "id": task.id,
                "branch": task.branch,
                "title": task.title,
                "description": task.description,
                "files_hint": task.files_hint,
                "test_command": task.test_command,
            }
            for task in tasks_config.tasks
        ],
    }

    with open(output_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def load_tasks_config(config_path: Path) -> TasksConfig | None:
    """Load tasks configuration from a YAML file.

    Args:
        config_path: Path to the YAML file

    Returns:
        TasksConfig or None if loading fails
    """
    if not config_path.exists():
        return None

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)

        if not data or "tasks" not in data:
            return None

        tasks = []
        for task_data in data.get("tasks", []):
            tasks.append(
                TaskConfig(
                    id=task_data.get("id", ""),
                    branch=task_data.get("branch", ""),
                    title=task_data.get("title", ""),
                    description=task_data.get("description", ""),
                    files_hint=task_data.get("files_hint", []),
                    test_command=task_data.get("test_command"),
                )
            )

        return TasksConfig(
            settings=data.get("settings", {}),
            tasks=tasks,
        )

    except Exception:
        return None
