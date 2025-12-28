# Use Case: Start Issue Workflow

## The Task

Every time a developer starts work on a GitHub issue, they need to:
1. Fetch issue details from GitHub
2. Create a properly named branch (`feature/123-issue-title` or `bug/123-issue-title`)
3. Set up a git worktree for isolated development
4. Generate a `PLANNING.md` file to track implementation

**Frequency**: Multiple times per day
**Current friction**: Must remember and type `dossier run imboard-ai/development/git/setup-issue-workflow`

---

## Proposed Solution: Skill + Dossier

### The Skill (Trigger)

**Location**: `~/.claude/skills/start-issue/SKILL.md` (user-level, works across all projects)

```yaml
---
name: start-issue
description: Set up a GitHub issue for development. Use when user says
  "start issue", "work on issue #X", "set up issue", or "begin issue".
---

# Start Issue

When the user wants to start working on a GitHub issue:

1. Extract the issue number from their request
2. Run: `dossier run imboard-ai/development/git/setup-issue-workflow`
3. Provide the issue number when prompted
```

### The Dossier (Engine)

**Location**: Registry at `imboard-ai/development/git/setup-issue-workflow`

Already exists - handles all the complex logic:
- GitHub API calls
- Branch naming conventions
- Worktree creation
- PLANNING.md generation

---

## User Experience

**Before** (dossier only):
```
$ dossier run imboard-ai/development/git/setup-issue-workflow
? GitHub issue number: 123
...
```

**After** (skill + dossier):
```
User: "start working on issue 123"

Claude: [auto-triggers skill → runs dossier]

        Done! Created:
        - Branch: feature/123-add-dark-mode
        - Worktree: ../feature-123
        - Planning: ../feature-123/PLANNING.md
```

---

## Why Both?

| Skill provides | Dossier provides |
|----------------|------------------|
| Natural language trigger | Versioned workflow |
| Zero-friction invocation | Registry discovery |
| Auto-detection from context | Team sharing |
| | Signed/trusted execution |

**Result**: Frictionless UX + organizational infrastructure
