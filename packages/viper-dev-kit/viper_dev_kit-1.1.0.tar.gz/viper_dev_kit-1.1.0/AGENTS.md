# AGENTS.md - Universal Agent Instructions

> **Template Version**: 1.0.0
> **Last Updated**: 2025-12
> **Compatibility**: Claude Code, OpenAI Codex, Gemini CLI, Google Antigravity, Cursor, GitHub Copilot
>
> This file follows the [AGENTS.md open standard](https://agents.md).
> It provides universal instructions for all AI coding agents.

## Project Context

This project uses the **ai-dev-kit** template for consistent AI-assisted development
across multiple tools and IDEs. For project-specific overrides, create an `AGENTS.local.md` file.

## Core Principles

### Architecture-First Development

- Always understand the full architecture before making changes
- Create implementation plans before writing code
- Define interfaces and contracts before implementations
- Consider how changes affect the broader system

### Code Quality Standards

- Write clean, readable, self-documenting code
- Prefer explicit over implicit
- Use clear, descriptive names for variables, functions, and classes
- Keep functions focused and small (single responsibility)
- Document complex logic with comments explaining "why" not "what"
- Handle errors gracefully with meaningful messages
- Include appropriate logging for debugging

### TOON Format Standards

- **Tabular Arrays**: Do NOT use commas inside quoted strings in TOON tabular arrays (e.g., `items[2]{col1,col2}`). The parser treats them as delimiters. Use semicolons or pipes instead.
- **Indentation**: maintain consistent 2-space indentation.

### Formatting

- Use consistent indentation (project-specific: see local config)
- Keep line length reasonable (80-120 characters)
- Use blank lines to separate logical sections
- Group related imports together

## Testing

- Write tests for new functionality
- Run existing tests before committing: check `package.json`, `Makefile`, or project docs
- Aim for meaningful coverage, not 100% coverage
- Test edge cases and error conditions

## Python Environment (UV)

This project uses **[UV](https://docs.astral.sh/uv/)** as the Python package and environment manager.

**Key commands**:

```bash
uv run script.py           # Run script with project dependencies
uv add package             # Add a dependency
uv sync                    # Sync environment with pyproject.toml
uv pip install package     # Install package (pip compatibility)
```

**Important**: Never use `pip install` directly. Always use `uv add` or `uv pip install` to ensure proper dependency tracking.

## Git Conventions

### Commit Messages

Format: `type(scope): description`

Types:

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Formatting, no code change
- `refactor` - Code restructuring
- `test` - Adding/updating tests
- `chore` - Maintenance tasks

### Branching

- `main` / `master` - Production-ready code
- `develop` - Integration branch (if used)
- `feature/*` - New features
- `fix/*` - Bug fixes
- `docs/*` - Documentation updates

## Security

- Never commit secrets, API keys, or credentials
- Use environment variables for sensitive configuration
- Validate and sanitize all inputs
- Follow principle of least privilege

## Project Structure

```
ai-docs/            # AI-consumable documentation
specs/              # Project specifications
dev-tools/          # Development tooling and scripts (source repo)
.claude/            # Claude Code configuration
├── settings.json   # Project settings
└── run-logs/       # Execution logs
```

> **Note**: The `.ai-kit/` directory structure is deprecated as of v1.0.0.
> The ai-dev-kit plugin is now installed via Claude Code's plugin system.
> See `docs/MAINTAINER.md` for migration details.

## Documentation

### AI-Consumable Docs

This project maintains AI-optimized documentation in `ai-docs/`:

- `frameworks/` - Framework-specific guidance
- `libraries/` - Library usage patterns
- `patterns/` - Architectural patterns
- `standards/` - Coding standards

### External Documentation Protocol

**Core principle**: Never work with an external library without loading its documentation first.

**Find documentation**:

```
/ai-dev-kit:docs-find [query]
```

**Navigate manually**:

```
@ai-docs/libraries/_index.toon          # See all libraries
@ai-docs/libraries/{lib}/_index.toon    # Library overview
```

**Update documentation**:

```
/ai-dev-kit:docs-update [source]   # Refresh existing
/ai-dev-kit:docs-add [url] [name]  # Add new source
```

## Working with Specifications

Check `specs/` for:

- Feature specifications
- API contracts
- Architecture decisions
- Design documents

When implementing features, always reference the relevant spec first.

## Development Workflows

### Starting a New Feature

1. Review relevant specs in `specs/`
2. Check `ai-docs/` for framework/library guidance
3. Create a plan before implementation
4. Implement in small, testable increments
5. Write tests as you go

### Parallel Development (Worktrees)

When working on multiple features simultaneously:

1. Use git worktrees to isolate work
2. Define clear file ownership per worktree
3. Avoid overlapping file modifications
4. Merge frequently to catch conflicts early

## Commands Available

> **Command Namespace**: All commands use the `/ai-dev-kit:` prefix (e.g., `/ai-dev-kit:plan`).
> See `docs/WORKFLOWS.md` for full usage examples.

### Planning

- `/ai-dev-kit:plan` - Create an architecture-first implementation plan
- `/ai-dev-kit:plan-phase` - Plan a specific development phase
- `/ai-dev-kit:plan-roadmap` - Create phased implementation roadmap
- `/ai-dev-kit:explore-architecture` - Analyze codebase and build C4 diagrams
- `/ai-dev-kit:visualize-roadmap` - Visualize roadmap diagrams
- `/ai-dev-kit:parallel` - Set up parallel development with worktrees

### Execution

- `/ai-dev-kit:execute-lane` - Execute a swim lane in worktree
- `/ai-dev-kit:execute-phase` - Execute all lanes in a phase

### Documentation

- `/ai-dev-kit:docs-find [query]` - Search documentation indexes
- `/ai-dev-kit:docs-update [source]` - Refresh documentation
- `/ai-dev-kit:docs-add [url] [name]` - Add new documentation source
- `/ai-dev-kit:docs-check` - Check for documentation updates (dry-run)
- `/ai-dev-kit:toon-validate` - Validate TOON files

### Multi-Agent Orchestration

- `/ai-dev-kit:delegate [agent] [task]` - Delegate task to specific agent
- `/ai-dev-kit:route [task]` - Intelligent task routing
- `/ai-dev-kit:cost-status` - Show usage across all providers
- `/ai-dev-kit:provider-check` - Check provider CLI availability

### Kit Management

- `/ai-dev-kit:setup` - Configure brownfield project
- `/ai-dev-kit:init` - Scaffold greenfield project
- `/ai-dev-kit:validate` - Verify plugin installation
- `/ai-dev-kit:kit-pull` - Pull template updates
- `/ai-dev-kit:kit-push` - Push template improvements
- `/ai-dev-kit:kit-diff` - Show template divergence
- `/ai-dev-kit:kit-update` - Update plugin from source
- `/ai-dev-kit:kit-doctor` - Validate kit installation

### Onboarding

- `/ai-dev-kit:quickstart-codebase` - Unified brownfield onboarding
- `/ai-dev-kit:prime` - Prime context with essential docs

## Multi-Agent Environment

This project operates in a multi-agent environment where tasks can be delegated
to the most appropriate AI provider based on task characteristics.

### Operating Model

| Platform | Role | Usage |
|----------|------|-------|
| **Antigravity** | Visual command center, collaboration hub | Visualization, manual intervention |
| **Claude Code** | Orchestrating brain, agentic interface | Task routing, delegation, SDK automation |
| **OpenAI (Codex)** | Delegate for sandboxed execution | Sandboxed tasks, coding |
| **Gemini** | Delegate for large context, multimodal | Large files, images, web search |
| **Cursor** | Delegate for quick IDE edits | Fast, targeted changes |

### Agent Priority Matrix (December 2025)

| Task Type | Priority 1 | Priority 2 | Priority 3 |
|-----------|------------|------------|------------|
| Complex reasoning | Claude (Opus 4.5) | OpenAI (GPT-5.2) | Gemini (3 Pro) |
| Sandboxed execution | OpenAI (GPT-5.2-Codex) | Cursor (Composer) | Claude (Opus 4.5) |
| Large context (>100k) | Gemini (3 Pro) | Claude (Opus 4.5) | OpenAI (GPT-5.2) |
| Multimodal (images/video) | Gemini (3 Pro) | Claude (Opus 4.5) | OpenAI (GPT-5.2) |
| Quick codegen | Claude (Haiku 4.5) | Gemini (3 Flash) | OpenAI (GPT-5.2-Codex-Mini) |
| Extended reasoning | OpenAI (GPT-5.2) | Gemini (3 Pro) | Claude (Opus 4.5) |
| Web search/grounding | Gemini (3 Pro) | OpenAI (GPT-5.2) | Claude (Opus 4.5) |

### Tool Discovery

Orchestration tools are available in `.claude/ai-dev-kit/dev-tools/orchestration/`:

```bash
# Check provider status
.claude/ai-dev-kit/dev-tools/orchestration/monitoring/cost-status.sh

# Route task to best agent
.claude/ai-dev-kit/dev-tools/orchestration/routing/route-task.py "your task"

# Direct provider execution
.claude/ai-dev-kit/dev-tools/orchestration/providers/claude-code/spawn.sh "task"
.claude/ai-dev-kit/dev-tools/orchestration/providers/codex/execute.sh "task"
.claude/ai-dev-kit/dev-tools/orchestration/providers/gemini/query.sh "task"
.claude/ai-dev-kit/dev-tools/orchestration/providers/cursor/agent.sh "task"
```

## Additional Context

For project-specific instructions, check:

- `AGENTS.local.md` - Project-specific agent instructions
- `.cursor/rules/` - Cursor specific rules
- `.agent/rules/` - Antigravity specific rules

---

**Note**: This file follows the [AGENTS.md open standard](https://agents.md).
CLAUDE.md and GEMINI.md are symlinks to this file for tool compatibility.
