# What we are building
Read the docs: Project_Blueprint.md
(Note keep this updated as the project plan evolves)

## Issue Tracking with bd (beads)
IMPORTANT: This project uses bd (beads) for ALL issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods.

## Environment & Dependencies
- We manage dependencies with **uv** and the checked-in `pyproject.toml` + `uv.lock`.
- Do **not** reintroduce `requirements.txt` or use `pip -r`; use `uv sync` instead.
- Standard workflow:
  1. Create env: `uv venv` (uses .venv by default)
  2. Activate: `source .venv/bin/activate` (or `.\.venv\Scripts\activate` on Windows)
  3. Install: `uv sync`
  4. Run tools via `uv run <command>` when you need isolation (e.g., `uv run pytest`).
- When running scripts locally, always activate the project venv (`source .venv/bin/activate`) or use `uv run ...` so dependencies are available and no unexpected downloads occur.

### Why bd?

- Dependency-aware: Track blockers and relationships between issues
- Git-friendly: Auto-syncs to JSONL for version control
- Agent-optimized: JSON output, ready work detection, discovered-from links
- Prevents duplicate tracking systems and confusion

### Quick Start

Check for ready work:
```
bd ready --json
```

Create new issues:
```
bd create "Issue title" -t bug|feature|task -p 0-4 --json
bd create "Issue title" -p 1 --deps discovered-from:bd-123 --json
```

Claim and update:
```
bd update bd-42 --status in_progress --json
bd update bd-42 --priority 1 --json
```

Complete work:
```
bd close bd-42 --reason "Completed" --json
```

### Issue Types

- `bug` - Something broken
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `epic` - Large feature with subtasks
- `chore` - Maintenance (dependencies, tooling)

### Priorities

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (default, nice-to-have)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

### Workflow for AI Agents

1. Check ready work: `bd ready` shows unblocked issues
2. Claim your task: `bd update <id> --status in_progress`
3. Work on it: Implement, test, document
4. Discover new work? Create linked issue:
   - `bd create "Found bug" -p 1 --deps discovered-from:<parent-id>`
5. Complete: `bd close <id> --reason "Done"`
6. Commit together: Always commit the `.beads/issues.jsonl` file together with the code changes so issue state stays in sync with code state

### Auto-Sync

bd automatically syncs with git:
- Exports to `.beads/issues.jsonl` after changes (5s debounce)
- Imports from JSONL when newer (e.g., after `git pull`)
- No manual export/import needed!
