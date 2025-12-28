---
name: start-issue
description: Set up a GitHub issue for development with branch, worktree, and planning doc.
  Use when user says "start issue", "work on issue #X", "set up issue", or "begin issue".
---

# Start Issue Workflow

When the user wants to start working on a GitHub issue:

## Prerequisites

Ensure dossier-tools is installed:
```bash
pip install dossier-tools
```

If not installed, help the user install it first.

## Steps

1. Extract the issue number from their request
2. Run the setup workflow:
   ```bash
   dossier run imboard-ai/development/git/setup-issue-workflow
   ```
3. When prompted for issue number, provide the extracted number
4. Confirm successful setup with the user

## What This Creates

- A properly named branch (`feature/123-title` or `bug/123-title`)
- A git worktree for isolated development
- A `PLANNING.md` file to track implementation
