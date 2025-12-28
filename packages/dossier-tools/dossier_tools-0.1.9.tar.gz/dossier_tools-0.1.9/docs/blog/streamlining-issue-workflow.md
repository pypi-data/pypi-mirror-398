# Streamlining Your Issue Workflow with Skills and Dossiers

You pick up a new issue. Before writing a single line of code, you're:

- Tab-switching to GitHub to grab the issue title
- Deciding if it's `bug/` or `feature/` (what were the labels again?)
- Mentally slugifying "Add user preferences page" → "add-user-preferences-page"
- Remembering where worktrees go in this repo (`../`? `.worktrees/`? next to `main/`?)
- Running `git branch`, `git worktree add`
- Creating yet another `PLANNING.md` from scratch

This takes 5-10 minutes. You do it multiple times a day. And everyone on your team does it slightly differently.

**What if you could just say: "start working on issue 123"?**

---

## Quick Start

### Prerequisites

- [Claude Code](https://claude.ai/code) CLI installed
- [GitHub CLI](https://cli.github.com/) (`gh`) installed and authenticated

### Installation

1. Install dossier-tools:
   ```bash
   pip install dossier-tools
   ```

2. Install the skill:
   ```bash
   dossier install-skill imboard-ai/skills/start-issue
   ```

3. **Start a new Claude Code session** (required for skill discovery)

4. Say:
   > "start working on issue 123"

That's it. Branch created, worktree set up, `PLANNING.md` ready.

---

## What Gets Created

When you say "start working on issue 123", the workflow:

1. **Fetches issue details** from GitHub (title, labels, body)
2. **Creates a branch** with proper naming: `feature/123-add-user-preferences` or `bug/123-fix-login`
3. **Sets up a worktree** in the right location for your project
4. **Generates `PLANNING.md`** with issue context and checklist

```
Issue workflow setup complete!

Issue:      #123 - Add user preferences page
Type:       feature
Branch:     feature/123-add-user-preferences
Worktree:   ../feature-123/
Planning:   ../feature-123/PLANNING.md

Next steps:
1. cd ../feature-123/
2. Review PLANNING.md
3. Start coding!
```

---

## The Full Loop

This is just the beginning. With both start and finish workflows installed:

| Phase | Command | What Happens |
|-------|---------|--------------|
| **Start** | "start working on issue 123" | Branch, worktree, PLANNING.md |
| **Work** | *(you write code)* | |
| **Finish** | "finish issue" | Security checks, cleanup, PR creation |

The tedious parts are automated. The creative parts stay with you.

→ See [Finishing What You Started](./finishing-what-you-started.md) for the finish-issue skill.

---

## "Can't I Just Ask Claude Directly?"

Yes, you could say: *"Create a branch for issue 123 with a planning doc"* and Claude would do it.

So why use dossier-tools?

| Just Prompting | With Skills + Dossiers |
|----------------|------------------------|
| Works for you, right now | Works for your whole team, every time |
| Your conventions, in your head | Conventions codified and versioned |
| Prompt varies each time | Same workflow, reproducible |
| Can't share or discover | Registry of workflows to browse |
| No audit trail | Checksums and signatures for trust |

**For solo devs:** Skills save you from remembering your own conventions.

**For teams:** Everyone uses the same branch naming, worktree locations, and planning templates—without tribal knowledge or "please read the wiki" onboarding.

---

## What If Something Goes Wrong?

### GitHub CLI not authenticated?
The workflow will detect this and prompt you to run `gh auth login` first.

### Branch already exists?
You'll be asked whether to check it out, create a new one, or abort.

### Worktree location unclear?
The workflow checks your repo's documentation, existing worktrees, and asks you if it's still unsure.

### Issue doesn't exist?
Clear error message with the issue number that wasn't found.

---

## How It Works

### What `install-skill` Does

When you run:
```bash
dossier install-skill imboard-ai/skills/start-issue
```

It:
1. Fetches the skill from the dossier registry
2. Creates `~/.claude/skills/start-issue/SKILL.md`
3. Claude Code auto-discovers skills in this directory on next session start

> **Note:** After installing a skill, start a new Claude Code session for it to be discovered.

### The Skill + Dossier Pattern

Two components work together:

| Component | What it does | Where it lives |
|-----------|--------------|----------------|
| **Skill** | Natural language trigger | `~/.claude/skills/` (local) |
| **Dossier** | Workflow logic | Registry (shared, versioned) |

- **Skill**: Teaches Claude to respond to "start issue", "work on issue #X", etc.
- **Dossier**: Contains the actual steps—fetch issue, create branch, set up worktree, generate planning doc

The skill triggers the dossier:
```bash
dossier run imboard-ai/development/git/setup-issue-workflow
```

### Why This Pattern?

- **Update once, everyone gets it**: Change the dossier, all installed skills use the new version
- **Team standardization**: Same conventions without tribal knowledge
- **Discoverable**: Browse workflows others have built with `dossier list`
- **Trustworthy**: Checksums verify content, signatures verify authors

---

## Under the Hood

### The Skill File

<details>
<summary><strong>View installed SKILL.md</strong></summary>

```yaml
---
name: start-issue
description: Set up a GitHub issue for development with branch, worktree, and planning doc.
  Use when user says "start issue", "work on issue #X", "set up issue", or "begin issue".
---

# Start Issue Workflow

When the user wants to start working on a GitHub issue:

## Steps

1. Extract the issue number from their request
2. Run the setup workflow:
   ```bash
   dossier run imboard-ai/development/git/setup-issue-workflow
   ```
3. Confirm successful setup with the user

## What This Creates

- A properly named branch (`feature/123-title` or `bug/123-title`)
- A git worktree for isolated development
- A `PLANNING.md` file to track implementation
```

</details>

### The Dossier

You can inspect the workflow dossier:

```bash
# View metadata
dossier get imboard-ai/development/git/setup-issue-workflow

# Download locally
dossier pull imboard-ai/development/git/setup-issue-workflow
```

<details>
<summary><strong>View full dossier content</strong></summary>

```yaml
---
name: setup-issue-workflow
title: Setup Issue Workflow
version: 1.0.0
objective: Create a workflow for GitHub issues that fetches issue details, creates
  appropriately named branches, sets up git worktrees, and generates PLANNING.md
---

# Setup Issue Workflow

## Prerequisites

- Git is installed and configured
- GitHub CLI (gh) is installed and authenticated
- You are in a git repository with GitHub as a remote

## Steps

### 1. Get Issue Number
Prompt the user for the GitHub issue number if not already provided.

### 2. Fetch Issue Details
```bash
gh issue view <ISSUE_NUMBER> --json title,labels,body,assignees
```

### 3. Determine Branch Type
- If "bug" label present: Use `bug/` prefix
- If "feature" label present: Use `feature/` prefix
- If unclear: Prompt user to choose

### 4. Create Branch Name
- Slugify the title (lowercase, hyphens, no special chars)
- Format: `{type}/{issue-number}-{slugified-title}`
- Example: `feature/123-add-user-preferences`

### 5. Discover Worktree Location
Check documentation, existing worktrees, or prompt user.

### 6. Create Branch and Worktree
```bash
git branch <branch-name>
git worktree add <worktree-path> <branch-name>
```

### 7. Generate PLANNING.md
Create planning file with issue context and implementation checklist.
```

</details>

---

## Customizing for Your Team

The default workflow is a starting point. To customize:

1. **Pull the dossier locally**:
   ```bash
   dossier pull imboard-ai/development/git/setup-issue-workflow
   ```

2. **Modify it** for your conventions (branch naming, worktree location, planning template)

3. **Publish your version**:
   ```bash
   dossier publish my-workflow.ds.md --namespace yourteam/workflows
   ```

Now your whole team uses the same conventions—without remembering or documenting them.

---

## Summary

| Before | After |
|--------|-------|
| 5-10 minutes of manual setup | One natural language command |
| Inconsistent naming across team | Same conventions every time |
| Context switching to GitHub | Automated fetching |
| Creating PLANNING.md from scratch | Generated with issue details |
| Onboarding: "read the wiki" | Onboarding: `dossier install-skill` |

---

## Next Steps

- **Finish the loop**: Install the [finish-issue](./finishing-what-you-started.md) skill for pre-PR checks
- **Create your own**: `dossier new`

### Explore More Workflows

Run `dossier list` to see what's available. Some examples:

| Dossier | What it does |
|---------|--------------|
| `imboard-ai/development/release/release-notes-generator` | Generate release notes from commits |
| `imboard-ai/development/security/dependency-vulnerability-report` | Scan dependencies for vulnerabilities |
| `imboard-ai/development/testing/test-coverage-gap-analysis` | Find untested code paths |
| `imboard-ai/development/ops/runbook-generator` | Create ops runbooks from code |

---

## Links

- [dossier-tools on GitHub](https://github.com/liberioai/dossier-tools)
- [start-issue Skill](https://github.com/liberioai/dossier-tools/tree/main/examples/skills/start-issue/SKILL.md)
- [Claude Code](https://claude.ai/code)
- [GitHub CLI](https://cli.github.com/)
