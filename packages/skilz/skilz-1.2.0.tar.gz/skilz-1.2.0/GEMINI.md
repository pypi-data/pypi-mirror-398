# GEMINI.md

## Project Overview

**Skilz** is a universal package manager for AI skills. It allows users to install, manage, and share skills (agents and tools) across various AI coding assistants (like Claude Code, OpenCode, Gemini, etc.). It functions similarly to `npm` or `pip` but for AI capabilities, ensuring reproducible installations via Git SHA pinning and manifest tracking.

### Key Technologies
*   **Language:** Python 3.10+
*   **Build System:** Hatchling (via `pyproject.toml`) / Poetry
*   **CLI Framework:** `argparse`
*   **Dependencies:** `PyYAML`
*   **Dev Tools:** `pytest` (testing), `ruff` (linting/formatting), `mypy` (type checking), `Taskfile` (automation)

## Building and Running

The project uses a `Taskfile.yml` to automate common development tasks.

### Prerequisites
*   Python 3.10 or higher
*   `pip`
*   (Optional) [Task](https://taskfile.dev) for running predefined tasks.

### Key Commands

| Action | Command (Manual) | Command (Task) |
| :--- | :--- | :--- |
| **Install Dev Deps** | `pip install -e ".[dev]"` | `task install` |
| **Run CLI** | `python -m skilz [command]` | `task run -- [command]` |
| **Run Tests** | `pytest tests/ -v` | `task test` |
| **Run Coverage** | `pytest tests/ --cov=skilz` | `task coverage` |
| **Lint Code** | `ruff check src/ tests/` | `task lint` |
| **Format Code** | `ruff format src/ tests/` | `task format` |
| **Type Check** | `mypy src/skilz` | `task typecheck` |
| **Build Package** | `python -m build` | `task build` |

### Running the CLI
To run the CLI from the source without installing it globally:
```bash
python -m skilz --help
python -m skilz install <skill-id> --dry-run
```

## Development Conventions

### Code Style
*   **Formatting:** The project uses `ruff` for code formatting. Run `task format` before committing.
*   **Type Hints:** Static typing is enforced using `mypy`. All new code must be fully typed.
*   **Linting:** `ruff` is used for linting. Ensure `task check` passes.
*   **Line Length:** 100 characters.

### Testing
*   **Framework:** `pytest` is used for all testing.
*   **Coverage:** The project maintains a high test coverage (target > 80%).
*   **Structure:** Tests are located in the `tests/` directory and mirror the `src/` structure (e.g., `tests/test_installer.py` tests `src/skilz/installer.py`).
*   **Mocking:** `unittest.mock` is heavily used to mock filesystem operations (`pathlib.Path`), network calls, and git operations to ensure tests are fast and reliable.

### Architecture
*   **Entry Point:** `src/skilz/cli.py` handles argument parsing and sub-command dispatch.
*   **Commands:** Individual command logic is encapsulated in `src/skilz/commands/` (e.g., `install_cmd.py`, `list_cmd.py`).
*   **Core Logic:**
    *   `installer.py`: Handles the core installation flow (validating, copying, creating manifests).
    *   `git_ops.py`: Wraps git operations (clone, fetch, checkout).
    *   `registry.py`: Resolves skill IDs to git locations.
    *   `manifest.py`: Manages the `.skilz-manifest.yaml` file for installed skills.
*   **Agents:** The system is agent-agnostic but supports agent-specific configurations (e.g., install paths) defined in `src/skilz/agents.py`.

### Git Workflow
*   **Commit Messages:** Follow Conventional Commits (e.g., `feat:`, `fix:`, `test:`, `docs:`).
*   **Branches:** Feature branches are typically used for development.

## Directory Structure
*   `src/skilz/`: Main package source code.
*   `tests/`: Unit and integration tests.
*   `docs/`: User manuals and documentation.
*   `.skilz/`: Default local configuration/registry (if present).
*   `Taskfile.yml`: Task runner configuration.
*   `pyproject.toml`: Python project configuration.

<skills_system priority="1">

## Available Skills

<!-- SKILLS_TABLE_START -->
<usage>
When users ask you to perform tasks, check if any of the available skills
below can help complete the task more effectively.

How to use skills:
- Invoke: Bash("skilz read <skill-name>")
- The skill content will load with detailed instructions
- Base directory provided in output for resolving bundled resources

Usage notes:
- Only use skills listed in <available_skills> below
- Do not invoke a skill that is already loaded in your context
</usage>

<available_skills>

<skill>
<name>design-doc-mermaid</name>
<description>Create Mermaid diagrams for any purpose - activity diagrams, deployment diagrams, architecture diagrams, or complete design documents. This skill uses a hierarchical structure with specialized guides loaded on-demand based on user intent. Supports code-to-diagram generation, Unicode semantic symbols, and Python utilities for diagram extraction and image conversion.</description>
<location>.skilz/skills/design-doc-mermaid/SKILL.md</location>
</skill>

<skill>
<name>my-skill</name>
<description>Skill: local/my-skill</description>
<location>/var/folders/tm/chrvt43s3rbdld20ghw1qtc40000gn/T/tmpiqczuocw/.claude/skills/my-skill/SKILL.md</location>
</skill>

<skill>
<name>sdd</name>
<description>Guide users through GitHub Spec-Kit for executable spec-driven development (greenfield/brownfield workflows with feature tracking).</description>
<location>.skilz/skills/sdd/SKILL.md</location>
</skill>

<skill>
<name>test-skill</name>
<description>Skill: test/skill</description>
<location>/var/folders/tm/chrvt43s3rbdld20ghw1qtc40000gn/T/tmp0gh6u29y/.claude/skills/test-skill/SKILL.md</location>
</skill>

</available_skills>
<!-- SKILLS_TABLE_END -->

</skills_system>
