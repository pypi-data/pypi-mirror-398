# Multi-Agent CLI Support Plan for Skilz

## Overview

Extend skilz-cli to support 10 AI agent CLIs following the [agentskills.io](http://agentskills.io/) open standard, with universal skills directory, config file sync, and Progressive Disclosure Architecture.

## User Requirements Summary

- **All 10 agents**: Claude, OpenCode, Copilot, Gemini, Aider, Cursor, Windsurf, Qwen, Codex, + universal
- **Config file**: `~/.config/skilz/config.json` to configure agent detection files
- **Home-level agents**: Claude, OpenCode, Codex (support `~/.agent/skills/`)
- **Project-level agents**: All others edit their respective config files (AGENTS.md, GEMINI.md, etc.)
- **Default mode**: Symlink for all agents EXCEPT Claude (copy for Claude)
- **Read format**: Header + Content format for `skilz read` command

---

## Architecture

### Agent Registry (`~/.config/skilz/config.json`)

```json
{
  "default_skills_dir": "~/.claude/skills",
  "agents": {
    "claude": {
      "display_name": "Claude Code",
      "home_dir": "~/.claude/skills",
      "project_dir": ".claude/skills",
      "config_files": ["CLAUDE.md"],
      "supports_home": true,
      "default_mode": "copy",
      "native_skill_support": "all"
    },
    "opencode": {
      "display_name": "OpenCode CLI",
      "home_dir": "~/.config/opencode/skills",
      "project_dir": ".skilz/skills",
      "config_files": ["AGENTS.md"],
      "supports_home": true,
      "default_mode": "copy",
      "native_skill_support": "home"
    },
    "codex": {
      "display_name": "OpenAI Codex",
      "home_dir": "~/.codex/skills",
      "project_dir": ".codex/skills",
      "config_files": ["AGENTS.md"],
      "supports_home": true,
      "default_mode": "copy",
      "invocation": "$skill-name or /skills",
      "native_skill_support": "all"
    },
    "gemini": {
      "display_name": "Gemini CLI",
      "project_dir": ".skilz/skills",
      "config_files": ["GEMINI.md"],
      "supports_home": false,
      "default_mode": "symlink",
      "native_skill_support": "none"
    },
    "copilot": {
      "display_name": "GitHub Copilot",
      "project_dir": ".github/copilot/skills",
      "config_files": [".github/copilot-instructions.md"],
      "supports_home": false,
      "default_mode": "symlink",
      "native_skill_support": "none"
    },
    "aider": {
      "display_name": "Aider",
      "project_dir": ".skills/skills",
      "config_files": ["CONVENTIONS.md"],
      "supports_home": false,
      "default_mode": "symlink",
      "native_skill_support": "none"
    },
    "cursor": {
      "display_name": "Cursor",
      "project_dir": ".skills/skills",
      "config_files": [".cursor/rules/RULES.md", ".cursor/rules/RULE.md"],
      "uses_folder_rules": true,
      "supports_home": false,
      "default_mode": "symlink",
      "native_skill_support": "none"
    },
    "windsurf": {
      "display_name": "Windsurf",
      "project_dir": ".skills/skills",
      "config_files": [],
      "supports_home": false,
      "default_mode": "symlink",
      "native_skill_support": "none"
    },
    "qwen": {
      "display_name": "Qwen CLI",
      "project_dir": ".skills/skills",
      "config_files": ["QWEN.md", "CONTEXT.md"],
      "supports_home": false,
      "default_mode": "symlink",
      "native_skill_support": "none"
    },
    "crush": {
      "display_name": "Crush",
      "project_dir": ".skills/skills",
      "config_files": [],
      "supports_home": false,
      "default_mode": "symlink",
      "native_skill_support": "none"
    },
    "kimi": {
      "display_name": "Kimi CLI",
      "project_dir": ".skills/skills",
      "config_files": [],
      "supports_home": false,
      "default_mode": "symlink",
      "native_skill_support": "none"
    },
    "plandex": {
      "display_name": "Plandex",
      "project_dir": ".skills/skills",
      "config_files": [],
      "supports_home": false,
      "default_mode": "symlink",
      "native_skill_support": "none"
    },
    "zed": {
      "display_name": "Zed AI",
      "project_dir": ".skills/skills",
      "config_files": [],
      "supports_home": false,
      "default_mode": "symlink",
      "native_skill_support": "none"
    },
    "universal": {
      "display_name": "Universal (Skilz)",
      "home_dir": "~/.skilz/skills",
      "project_dir": ".skilz/skills",
      "config_files": [],
      "supports_home": true,
      "default_mode": "copy"
    }
  }
}
```

### Agent Configuration Fields

**display_name**

Human-readable name for the agent shown in CLI output and help text. Example: "Claude Code", "GitHub Copilot"

**home_dir**

Path to user-level skills directory in the home folder (e.g., `~/.claude/skills`). Only applicable for agents that support home-level installation. Set to `null` or omit for project-only agents.

**project_dir**

Path to project-level skills directory relative to the project root (e.g., `.claude/skills`, `.github/copilot/skills`). All agents must have a project directory.

**config_files**

Array of configuration file names where skill metadata should be synced (e.g., `["AGENTS.md", "GEMINI.md"]`). These files receive XML skill listings during `skilz sync`. Empty array means no config file sync.

**supports_home**

Boolean indicating whether the agent supports user-level (~/) skill installation. Currently only `true` for Claude, OpenCode, Codex, and Universal.

**default_mode**

Installation mode used when no explicit flag is provided. Either `"copy"` (duplicate files) or `"symlink"` (create symbolic links). Claude defaults to copy for compatibility; most others use symlink.

**uses_folder_rules**

Boolean indicating whether the agent uses folder-based rule files (like Cursor's `.cursor/rules/` structure) instead of or in addition to single config files. Optional field, defaults to `false`.

**invocation**

Optional string describing how skills are invoked within the agent's CLI/interface. Example: `"$skill-name or /skills"` for Codex. Used for documentation purposes.

**native_skill_support**

Level of native skill support: `"all"` (full support at home and project level), `"home"` (only home-level native support), or `"none"` (requires skilz-cli for skill management). If they support "none" this means that we have to edit the first config file we find in the **`config_files`**.

### Install Examples

To install in a Gemini-managed project, you would run this command in the project directory:

```bash
skilz install anthropics/pdf --project --agent gemini
```

Based on the above configuration, this would create a dir in the gemini project dir `./.skilz/skills` and create symbolic links to the default install skill folder `default_skills_dir`. Since `GEMINI.md` is listed as the config file, the skills markdown would get added to `GEMINI.md` for this skill. If you add another skill to this project, it will add another symbolic link and update the XML for skills in `GEMINI.md`.

To install in a Gemini-managed project with all skills from a directory, you would run this command in the project directory:

```bash
skilz install -f ~/.claude/skills/* --project --agent gemini
```

Based on the above configuration, this would create a dir in the gemini project dir `./.skilz/skills` and create symbolic links to each of the skills in this directory. Since `GEMINI.md` is listed as the config file, the skills markdown would get added to `GEMINI.md` for every skill in that directory. You can also specify a single skill directory from the filesystem.

To install in a Gemini-managed project with a skill from a GitHub repo, you would run this command in the project directory:

```bash
skilz install -g https://github.com/lackeyjb/playwright-skill/tree/main/skills/playwright-skill \
  --project --agent gemini
```

Based on the above configuration, this would create a dir in the gemini project dir `./.skilz/skills`, install from the corresponding git repo at the correct branch, and then submit this skill to the skilz marketplace web application. Since `GEMINI.md` is listed as the config file, the skills markdown would get added to `GEMINI.md` for the skill you want to install.

This works the same way as the last, and would even work with non-github links:

```bash
skilz install -g git@github.com:lackeyjb/playwright-skill.git \
  --path playwright-skill/SKILL.md \
  --project --agent gemini
```

### Directory Search Priority

```
1. ./.skilz/skills/       <- Project universal (HIGHEST)
2. ~/.skilz/skills/       <- Global universal
3. ./<agent>/skills/      <- Project agent-specific
4. ~/<agent>/skills/      <- User agent-specific (LOWEST)
```

---

## Implementation Phases

### Phase 1: Agent Registry System

**Goal**: Replace hardcoded agent definitions with configurable registry.

**New Files**:
- `src/skilz/agent_registry.py` - Agent configuration dataclasses and registry loader

**Modify**:
- `src/skilz/agents.py` - Delegate to registry, maintain backward compatibility
- `src/skilz/cli.py` - Dynamic `--agent` choices from registry
- `src/skilz/config.py` - Add registry loading from `~/.config/skilz/config.json`

**Key Code**:
```python
# src/skilz/agent_registry.py
@dataclass(frozen=True)
class AgentConfig:
    name: str
    display_name: str
    home_dir: Path | None
    project_dir: Path
    config_files: tuple[str, ...]
    supports_home: bool = False
    uses_folder_rules: bool = False
    default_mode: Literal["copy", "symlink"] = "symlink"
    native_skill_support: Literal["all", "home", "none"] = "none"

AgentType = Literal["claude", "opencode", "codex", "gemini", "copilot",
                    "aider", "cursor", "windsurf", "qwen", "crush", "kimi",
                    "plandex", "zed", "universal",
                    "other1", "other2", "other3", "other4", "other5",
                    "other6", "other7", "other8", "other9"]
```

### Phase 2: Universal Skills Directory

**Goal**: Add `.skilz/skills/` as universal directory with symlink/copy support.

**New Files**:
- `src/skilz/link_ops.py` - Symlink creation, validation, broken link handling

**Modify**:
- `src/skilz/installer.py` - Add `--universal`, `--copy`, `--symlink`, `-f`, `-g` flags
- `src/skilz/scanner.py` - Scan all directories with priority resolution
- `src/skilz/manifest.py` - Add `install_mode`, `canonical_path` fields
- `src/skilz/commands/install_cmd.py` - Pass new flags

**CLI Changes**:
```bash
skilz install anthropics/pdf                    # Claude to ~/.claude/skills
skilz install anthropics/pdf --agent claude     # Claude to ~/.claude/skills
skilz install anthropics/pdf --agent universal  # To ~/.skilz/skills
skilz install anthropics/pdf --agent opencode   # To ~/.config/opencode/skills
skilz install anthropics/pdf --global           # To ~/.skilz/skills/
skilz install -f ~/.claude/skills/*             # Install from filesystem
skilz install -g https://github.com/user/repo   # Install from git URL
```

### Phase 3: SKILL.md Frontmatter Parsing

**Goal**: Parse name/description from SKILL.md for config file sync.

**New Files**:
- `src/skilz/frontmatter.py` - YAML frontmatter extraction using strictyaml

**Key Code**:
```python
# src/skilz/frontmatter.py
@dataclass
class SkillMetadata:
    name: str
    description: str
    raw_frontmatter: str

def parse_frontmatter(content: str) -> SkillMetadata:
    # Uses strictyaml for parsing
```

### Phase 4: `skilz read` Command

**Goal**: Output skill content with base directory for agent consumption.

**New Files**:
- `src/skilz/commands/read_cmd.py`

**Modify**:
- `src/skilz/cli.py` - Add `read` subparser

**Output Format**:
```
Reading: pdf
Base directory: /Users/me/.claude/skills/pdf

---
name: pdf
description: Comprehensive PDF manipulation toolkit...
---

[Full SKILL.md content]
```

### Phase 5: `skilz sync` Command

**Goal**: Update agent config files (AGENTS.md, GEMINI.md, etc.) with skill metadata.

This is done automatically as part of the install. But if you want to refresh the metadata you can. We will only add/refresh the skills that are already added to the project.

**New Files**:
- `src/skilz/commands/sync_cmd.py`
- `src/skilz/config_sync.py` - Config file parsing and XML generation

**Modify**:
- `src/skilz/cli.py` - Add `sync` subparser

**Generated XML**:
```xml
<skills_system priority="1">
<usage>
When a skill is relevant, invoke with: skilz read <name>
</usage>
<available_skills>
  <skill>
    <name>pdf</name>
    <description>PDF manipulation toolkit...</description>
    <location>project</location>
  </skill>
</available_skills>
</skills_system>
```

### Phase 6: `skilz validate` Command

**Goal**: Validate skills following agentskills.io spec.

**New Files**:
- `src/skilz/commands/validate_cmd.py`
- `src/skilz/validator.py` - Port validation logic from skills-ref

**Validation Rules**:
- SKILL.md exists with valid YAML frontmatter
- Required fields: name, description
- Name: lowercase, letters/digits/hyphens, max 64 chars
- Description: max 1024 chars
- Name matches directory name
- Only allowed fields in frontmatter

### Phase 7: `skilz manage` Command

**Goal**: Interactive skill management TUI.

**New Files**:
- `src/skilz/commands/manage_cmd.py`

**Features**:
- List installed/available skills
- Install/remove interactively
- Configure per-agent installation
- This is a basic terminal interface so we do not bloat the command line tool

---

## Files to Create

| File | Purpose |
|------|---------|
| `src/skilz/agent_registry.py` | Agent configuration registry |
| `src/skilz/link_ops.py` | Symlink/copy operations |
| `src/skilz/frontmatter.py` | SKILL.md parsing (using strictyaml) |
| `src/skilz/validator.py` | Skill validation (port from skills-ref) |
| `src/skilz/config_sync.py` | Config file XML generation |
| `src/skilz/commands/read_cmd.py` | Read command |
| `src/skilz/commands/sync_cmd.py` | Sync command |
| `src/skilz/commands/validate_cmd.py` | Validate command |
| `src/skilz/commands/manage_cmd.py` | Manage command |

## Files to Modify

| File | Changes |
|------|---------|
| `src/skilz/agents.py` | Delegate to registry, add universal paths |
| `src/skilz/cli.py` | Add 4 new subparsers, dynamic agent choices |
| `src/skilz/config.py` | Load agent registry from config file |
| `src/skilz/installer.py` | Add universal/copy/symlink modes, -f and -g flags |
| `src/skilz/scanner.py` | Multi-directory priority scanning |
| `src/skilz/manifest.py` | Add install_mode, canonical_path fields |
| `src/skilz/commands/install_cmd.py` | Pass new flags |
| `src/skilz/commands/list_cmd.py` | Show symlink status |
| `src/skilz/commands/remove_cmd.py` | Handle symlink removal |
| `src/skilz/commands/update_cmd.py` | Handle symlink updates |

## Test Files to Create

| File | Purpose |
|------|---------|
| `tests/test_agent_registry.py` | Agent registry tests |
| `tests/test_link_ops.py` | Symlink operations tests |
| `tests/test_frontmatter.py` | Frontmatter parsing tests |
| `tests/test_validator.py` | Validation logic tests (port from skills-ref) |
| `tests/test_config_sync.py` | Config sync tests |
| `tests/test_read_cmd.py` | Read command tests |
| `tests/test_sync_cmd.py` | Sync command tests |
| `tests/test_validate_cmd.py` | Validate command tests |

---

## CLI Summary After Implementation

```
skilz [command] [options]

Commands:
  install <skill-id>     Install skills (--universal, --copy, --symlink, --global, -f, -g)
  list                   List installed skills with status
  update                 Update skills to registry versions
  remove <name>          Remove a skill
  read <name>            Load skill content to stdout (for agents)
  sync                   Update AGENTS.md, GEMINI.md, etc. with skill metadata
  validate <name>        Validate skill against agentskills.io spec
  manage                 Interactive skill management
  config                 Show/modify configuration

Global Options:
  --agent {claude,opencode,codex,gemini,copilot,aider,cursor,windsurf,qwen,crush,kimi,plandex,zed,universal}
  --project              Use project-level instead of user-level
  -y, --yes-all          Skip confirmation prompts
  -v, --verbose          Verbose output
```

---

## Key Design Decisions

1. **Symlink default for agents without native support** - Agents with `native_skill_support: "none"` use symlinks
2. **Copy default for native-supporting agents** - Claude, OpenCode, Codex use copy for compatibility
3. **Config-driven agent registry** - Users can customize detection markers and paths
4. **agentskills.io compatible** - Following the open standard for portability
5. **Progressive disclosure** - Metadata in config files, full content via `skilz read`
6. **Backward compatible** - Existing Claude/OpenCode installs continue working
7. **Project-level focus for most agents** - Only Claude/OpenCode/Codex support home installs
8. **Automatic sync on install** - Config files updated automatically during installation

---

## Agent-Specific Differences

| Feature | Claude Code | OpenAI Codex | Others |
|---------|-------------|--------------|--------|
| **Skill Invocation** | Model-invoked only (implicit) | `$skill-name` or `/skills` | Varies |
| **Home Location** | `~/.claude/skills/` | `~/.codex/skills/` | Project-only |
| **Project Location** | `.claude/skills/` | `.codex/skills/` | Agent-specific |
| **Config File** | `CLAUDE.md` | `AGENTS.md` | See registry |
| **allowed-tools** | Supported | Experimental | Varies |
| **Native Skill Support** | all | all | none (requires config sync) |

### Codex Search Order (from agent-skill-converter)
1. `$CWD/.codex/skills` (repo working dir)
2. `$CWD/../.codex/skills` (parent)
3. `$REPO_ROOT/.codex/skills` (repo root)
4. `$CODEX_HOME/skills` (~/.codex/skills)
5. `/etc/codex/skills` (admin)
6. System bundled

### Universal Directory Unifies All
With `.skilz/skills/`, skills work across all agents:
- Symlinks from `.claude/skills/` → `.skilz/skills/`
- Symlinks from `.codex/skills/` → `.skilz/skills/`
- One source, all agents see it

## Dependencies

**New dependency**:
- `strictyaml>=1.7.3` - For SKILL.md frontmatter parsing (used by agentskills.io reference)

**Existing**:
- `pathlib` for paths
- `json` for config files
- `html` for XML escaping
- Existing CLI infrastructure (argparse)

---

## Reference Implementation: skills-ref (agentskills.io)

The official reference library provides patterns to follow:

### Validation Rules (from `validator.py`)
```python
MAX_SKILL_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_COMPATIBILITY_LENGTH = 500

ALLOWED_FIELDS = {
    "name",           # Required
    "description",    # Required
    "license",        # Optional
    "allowed-tools",  # Optional (experimental)
    "metadata",       # Optional dict
    "compatibility",  # Optional
}
```

### Name Validation
- Lowercase only
- Letters, digits, hyphens only
- No leading/trailing hyphens
- No consecutive hyphens
- NFKC Unicode normalization for i18n support
- Must match directory name

### SkillProperties Model (from `models.py`)
```python
@dataclass
class SkillProperties:
    name: str
    description: str
    license: Optional[str] = None
    compatibility: Optional[str] = None
    allowed_tools: Optional[str] = None
    metadata: dict[str, str] = field(default_factory=dict)
```

### XML Prompt Format (from `prompt.py`)
```xml
<available_skills>
<skill>
<name>
pdf-reader
</name>
<description>
Read and extract text from PDF files
</description>
<location>
/path/to/pdf-reader/SKILL.md
</location>
</skill>
</available_skills>
```

### CLI Commands (from `cli.py`)
The reference provides these commands we should mirror:
- `skills-ref validate path/to/skill` - Validate a skill
- `skills-ref read-properties path/to/skill` - Output JSON properties
- `skills-ref to-prompt path/to/skill-a path/to/skill-b` - Generate XML

**Our equivalents**:
- `skilz validate <skill-name>` - Validate installed skill
- `skilz read <skill-name>` - Read skill (Header+Content format)
- `skilz sync` - Generate XML for all config files

---

## Spec Reference

- agentskills.io standard: https://agentskills.io/home
- skills-ref reference library: https://github.com/anthropics/skills-ref
- Progressive Disclosure Architecture from user spec
- AGENTS.md support table from user spec
