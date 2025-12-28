# Finishing What You Started: The Other Side of the Workflow

*This is the companion post to [Streamlining Your Issue Workflow](./streamlining-issue-workflow.md). That one covers starting an issue. This one covers finishing it.*

---

You've written the code. Tests pass (locally). Time to create a PR.

Then you remember:

- Did I remove those `console.log` statements?
- Is my branch up to date with main?
- Was there a `TODO` I left somewhere?
- Did I accidentally commit that `.env` file?
- What should the PR description even say?

You rush through it. The PR goes up. Then the review comes back:

> "Please remove the debug statements on line 42 and 87."
> "There's a hardcoded path to your home directory in the config."
> "Can you rebase? There are conflicts with main."

---

## I've Been on Both Sides

As a developer, I was *that person*. The one who forgot to remove `print()` statements. Who committed files with my local machine paths. Who pushed a branch that was 47 commits behind main.

My team lead would catch these in review. Every. Single. Time.

Then I became a team lead. And suddenly I understood the frustration—not because developers were careless, but because there was no system. Everyone was doing the same mental checklist (or not), and things slipped through.

The options were:
1. Chase developers about the same issues repeatedly
2. Add more "please remember to..." items to the PR template
3. Accept that some things would always slip through

None of these felt right.

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
   dossier install-skill imboard-ai/skills/finish-issue
   ```

3. **Start a new Claude Code session** (required for skill discovery)

4. Say:
   > "finish issue"

   Or: "ready for PR", "prepare for review", "create PR"

That's it. Checks run, issues flagged, PR created.

> **Note:** Works on any feature branch—you don't need to use [start-issue](./streamlining-issue-workflow.md) first.

---

## "Can't I Just Ask Claude Directly?"

Yes, you could say: *"Check my code for debug statements and create a PR"* and Claude would try.

But here's what you'd miss:

| Just Prompting | With finish-issue |
|----------------|-------------------|
| You remember what to check | Comprehensive checklist runs every time |
| Easy to skip steps when rushed | Same rigor whether it's 5pm Friday or Tuesday morning |
| Secrets might slip through | Pattern-based secret detection blocks dangerous commits |
| Generic PR description | Context-aware description with reviewer suggestions |
| No team consistency | Everyone runs the same pre-PR checks |

**The real value:** This workflow catches things you wouldn't think to ask about—secrets patterns, files that should be gitignored, user-specific paths that break for others.

It's a pre-commit hook with intelligence.

---

## What It Checks

### Git Preparation
- Fetch latest from origin
- Rebase onto main (or warn about conflicts)
- Review commit history

### Security & Hygiene
- **Secrets**: API keys (`AKIA...`), tokens (`ghp_...`), private keys, hardcoded passwords
- **Gitignore candidates**: `.env`, `node_modules/`, `__pycache__/`, `.DS_Store`
- **User-specific paths**: `/Users/yourname/...`, `/home/yourname/...`
- **Large binary files**: Catches accidental commits of build artifacts

### Code Cleanup
- Debug statements (`console.log`, `print()`, `debugger`, `pdb.set_trace()`)
- Commented-out code blocks
- Unresolved `TODO`/`FIXME`/`HACK` comments
- Unused imports

### Project Checks
- Run linter (auto-detected from your project)
- Run formatter
- Run type checker
- Sync lockfiles if needed

### Tests
- Run test suite
- Flag skipped tests (`.skip`, `@pytest.mark.skip`)

### Context-Aware Review Suggestions

The workflow analyzes what you changed and suggests who should review:

| Changes Detected | Suggested Review |
|-----------------|------------------|
| Auth, login, session, JWT | Security review |
| Database, queries, migrations | Performance/DB review |
| New dependencies | Security + license review |
| Payment, billing, Stripe | Compliance review |
| Dockerfile, CI/CD, Terraform | Ops review |

---

## The Interaction Model

Unlike a static linter, this workflow *asks you* what to do.

```
═══════════════════════════════════════════════════════════
  Phase 2: Security & Hygiene
═══════════════════════════════════════════════════════════

Found 3 potential issues:

  ⚠️  console.log in src/api/users.ts:42
      > console.log("user data:", userData)

  ⚠️  console.log in src/api/users.ts:87
      > console.log("response:", res)

  ⚠️  Hardcoded path in tests/config.json:15
      > "dataPath": "/Users/john/testdata"

┌─────────────────────────────────────┐
│  How would you like to proceed?     │
├─────────────────────────────────────┤
│  1. Fix automatically               │
│  2. Skip and continue               │
│  3. View details                    │
│  4. Abort workflow                  │
└─────────────────────────────────────┘
```

You decide. Some `console.log` statements are intentional (logging). Some hardcoded paths are test fixtures. The workflow doesn't assume—it asks.

**For critical issues like secrets, it blocks:**

```
🚨 BLOCKED: Possible secret detected

  File: src/config.ts:23
  > const API_KEY = "sk_live_abc123..."

  This looks like a Stripe API key. Committing secrets
  to git is a security risk.

  Options:
  1. Remove this line (use environment variable instead)
  2. This is a test/fake key (mark as reviewed)
  3. Abort and fix manually
```

You can't accidentally push an API key.

---

## What If Something Goes Wrong?

### Tests fail?
You're shown the failure summary and asked: fix now, skip (noted in PR), or abort.

### Merge conflicts during rebase?
The workflow stops and shows which files conflict. Resolve them, then continue.

### Linter not detected?
You're prompted to enter your lint command, or skip.

### Secret detected but it's a false positive?
You can mark it as reviewed and continue. The PR will note it was manually reviewed.

### GitHub CLI not authenticated?
Detected early—you'll be prompted to run `gh auth login`.

---

## How It Works

### What `install-skill` Does

When you run:
```bash
dossier install-skill imboard-ai/skills/finish-issue
```

It:
1. Fetches the skill from the dossier registry
2. Creates `~/.claude/skills/finish-issue/SKILL.md`
3. Claude Code auto-discovers skills in this directory on next session start

> **Note:** After installing a skill, start a new Claude Code session for it to be discovered.

### The Skill + Dossier Pattern

| Component | What it does | Where it lives |
|-----------|--------------|----------------|
| **Skill** | Triggers on "finish issue", "ready for PR", etc. | `~/.claude/skills/` (local) |
| **Dossier** | The actual checklist and logic | Registry (shared, versioned) |

The skill triggers the dossier:
```bash
dossier run imboard-ai/development/git/finish-issue-workflow
```

---

## Under the Hood

### The Skill File

<details>
<summary><strong>View installed SKILL.md</strong></summary>

```yaml
---
name: finish-issue
description: Prepare a GitHub issue branch for PR with quality checks, cleanup, and review recommendations.
  Use when user says "finish issue", "ready for PR", "prepare for review", "submit PR",
  "create PR", "finalize issue", or "wrap up".
---

# Finish Issue Workflow

When the user wants to finalize their work on a GitHub issue and prepare a PR:

## Steps

1. Verify we're on a feature/bug branch (not main/master)
2. Run the finish workflow:
   ```bash
   dossier run imboard-ai/development/git/finish-issue-workflow
   ```
3. Respond to prompts for each check category
4. Confirm successful PR creation with the user
```

</details>

### The Dossier

You can inspect the workflow dossier:

```bash
# View metadata
dossier get imboard-ai/development/git/finish-issue-workflow

# Download locally
dossier pull imboard-ai/development/git/finish-issue-workflow
```

<details>
<summary><strong>View full dossier content</strong></summary>

```yaml
---
name: finish-issue-workflow
title: Finish Issue Workflow
version: 1.0.0
status: stable
objective: Comprehensive pre-PR workflow with security scans, code cleanup, quality checks,
  and context-aware review recommendations
risk_level: medium
risk_factors:
  - modifies_files
  - executes_external_code
---

# Finish Issue Workflow

## Phase 1: Git Preparation
- Verify not on main/master (block if so)
- Fetch & rebase onto main
- Show conflicts if any (block until resolved)

## Phase 2: Security & Hygiene
Scan for:
- Secrets: AKIA*, ghp_*, private keys, hardcoded passwords
- Gitignore candidates: .env, node_modules/, __pycache__/
- User-specific paths: /Users/<name>/, /home/<name>/
- Large files (>1MB)

## Phase 3: Code Cleanup
Detect and offer to remove:
- Debug statements (console.log, print, debugger)
- Commented-out code blocks
- Unresolved TODOs/FIXMEs
- Unused imports

## Phase 4: Project Checks
Auto-detect and run:
- Linter (from package.json, Makefile, pyproject.toml)
- Formatter
- Type checker
- Lockfile sync

## Phase 5: Tests
- Run test suite
- Flag skipped tests

## Phase 6: Context-Aware Review Recommendations
Based on files changed, suggest:
- Security review (auth/login/JWT changes)
- DB review (schema/migration changes)
- Ops review (Dockerfile/CI changes)

## Phase 7: Create PR
- Generate description from PLANNING.md + commits
- Link to issue
- Include review recommendations
- Size warning if >500 lines
- Push and create via gh
```

</details>

---

## Customizing for Your Team

The default workflow is a starting point. Your team might:

- Have stricter rules (block on *any* debug statement)
- Have different lint/test commands
- Want additional checks (coverage thresholds, changelog updates)
- Use different PR templates

To customize:

1. **Pull the dossier locally**:
   ```bash
   dossier pull imboard-ai/development/git/finish-issue-workflow
   ```

2. **Modify it** for your conventions

3. **Publish your version**:
   ```bash
   dossier publish my-workflow.ds.md --namespace yourteam/workflows
   ```

Now your whole team runs the same pre-PR checks—no more "please remember to..." comments in reviews.

---

## The Full Loop

With both workflows installed:

| Phase | Command | What Happens |
|-------|---------|--------------|
| Start | "start working on issue 123" | Branch, worktree, PLANNING.md |
| Work | *(you write code)* | |
| Finish | "finish issue" | Checks, cleanup, PR creation |

The tedious parts are automated. The creative parts stay with you.

---

## Share Your Workflows

If you build a workflow that works for your team, consider sharing it:

```bash
dossier publish my-workflow.ds.md --namespace yourorg/workflows
```

Others can install it:

```bash
dossier install-skill yourorg/workflows/my-workflow
```

Browse what's available:

```bash
dossier list
```

### Example Workflows

| Dossier | What it does |
|---------|--------------|
| `imboard-ai/development/release/release-notes-generator` | Generate release notes from commits |
| `imboard-ai/development/security/dependency-vulnerability-report` | Scan dependencies for vulnerabilities |
| `imboard-ai/development/testing/test-coverage-gap-analysis` | Find untested code paths |
| `imboard-ai/development/ops/runbook-generator` | Create ops runbooks from code |

The goal isn't one workflow for everyone. It's making it easy to share what works.

---

## Links

- [The Start Issue Blog Post](./streamlining-issue-workflow.md)
- [finish-issue Skill](https://github.com/liberioai/dossier-tools/tree/main/examples/skills/finish-issue/SKILL.md)
- [finish-issue Dossier](https://github.com/liberioai/dossier-tools/tree/main/examples/dossiers/finish-issue-workflow.ds.md)
- [dossier-tools on GitHub](https://github.com/liberioai/dossier-tools)
- [Claude Code](https://claude.ai/code)
