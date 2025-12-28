---
schema_version: "1.0.0"
name: finish-issue-workflow
title: Finish Issue Workflow
version: "1.0.0"
status: stable
objective: Comprehensive pre-PR workflow that performs git preparation, security scans, code cleanup, quality checks, testing, and creates a properly formatted pull request with context-aware review recommendations.
authors:
  - name: Dossier Community
checksum:
  algorithm: sha256
  hash: 7350b31435ddb166d3c5c4a7bdd39140ad7ab6e00287a6bb83faf2ef1c2a12eb
risk_level: medium
risk_factors:
  - modifies_files
  - executes_external_code
  - network_access
requires_approval: true
category:
  - development
  - git
tags:
  - finish-issue
  - pull-request
  - code-review
  - quality-checks
estimated_duration:
  min_minutes: 5
  max_minutes: 30
---

# Finish Issue Workflow

Prepare a GitHub issue branch for pull request with comprehensive quality checks, security scans, code cleanup, and automated PR creation.

## Interaction Model

This workflow follows a **consultative approach**:

1. **Issues Found**: Ask user how to proceed (fix, skip, or abort)
2. **Blocking Decisions**: Make autonomous decisions with clear reasoning
3. **Command Detection**: Auto-detect project commands, fallback to prompting user

For each issue category, present options:
```
Found [N] issues in [category]:
  - [issue description]

Options:
1. Fix automatically
2. Skip and continue
3. View details
4. Abort workflow
```

---

## Phase 1: Git Preparation

### Step 1.1: Verify Branch Context

```bash
git branch --show-current
```

**Blocking Decision**: If on `main` or `master`:
- ABORT with message: "Cannot finish from main/master branch. Please switch to a feature/bug branch."

### Step 1.2: Fetch and Rebase

```bash
git fetch origin
git rebase origin/main  # or origin/master
```

**If conflicts occur**:
- Display conflict files
- Ask: "Merge conflicts detected. Resolve manually before continuing."
- BLOCK until resolved

### Step 1.3: Review Commits

```bash
git log origin/main..HEAD --oneline
```

Display for awareness. No blocking.

---

## Phase 2: Security and Hygiene

### Step 2.1: Scan for Secrets

**Detection patterns**:
```
AKIA[0-9A-Z]{16}                              # AWS Access Key
ghp_[A-Za-z0-9]{36}                           # GitHub PAT
-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY----- # Private keys
(password|secret|token|api_key)\s*[:=]\s*['"][^'"]{8,}  # Hardcoded creds
eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.        # JWT tokens
(mongodb|postgres|mysql|redis):\/\/[^@]+@     # Connection strings
```

**If found**: Ask user - critical security issue

### Step 2.2: Check Gitignore Candidates

**Patterns**:
```
.env, .env.local, .env.*.local
.idea/, .vscode/settings.json, *.swp, .DS_Store
node_modules/, __pycache__/, *.pyc, .venv/, venv/
dist/, build/, *.egg-info/
*.log, npm-debug.log*
```

**If found**: Ask user to add to .gitignore or confirm intentional

### Step 2.3: Detect User-Specific Paths

**Patterns**:
```
/Users/[a-zA-Z0-9_]+/     # macOS
/home/[a-zA-Z0-9_]+/      # Linux
C:\\Users\\[a-zA-Z0-9_]+\\ # Windows
```

**If found**: Ask user to replace with relative paths or env vars

### Step 2.4: Check Large Files

Files >1MB in the changeset.

**If found**: Suggest Git LFS or removal

---

## Phase 3: Code Cleanup

### Step 3.1: Debug Statements

**Python**:
```
print\(
pdb\.set_trace\(\)
breakpoint\(\)
import pdb
import ipdb
```

**JavaScript/TypeScript**:
```
console\.(log|debug|info|warn|error)\(
debugger;?
```

**Go**:
```
fmt\.Print(ln|f)?\(
```

**If found**: Ask user to remove or keep (with `// keep` comment)

### Step 3.2: Commented-Out Code

Look for commented blocks that appear to be code:
```
(//|#)\s*(if|for|while|function|def|class|return|import)\s+
```

**If found**: Ask user to remove or document why kept

### Step 3.3: Unresolved TODOs

**Patterns**:
```
TODO[\s:]+
FIXME[\s:]+
HACK[\s:]+
XXX[\s:]+
```

**If found**: Ask user to resolve, create follow-up issue, or keep

### Step 3.4: Unused Imports

Use language-specific tools:
- Python: `autoflake --check`
- JavaScript: `eslint --rule 'no-unused-vars: error'`

**If found**: Ask user to remove

---

## Phase 4: Project Checks

### Step 4.1: Detect and Run Linter

**Detection order**:
1. `package.json` scripts: `lint`, `eslint`
2. `Makefile`: `lint` target
3. `pyproject.toml`: `[tool.ruff]` or `[tool.flake8]`
4. Config files: `.eslintrc*`, `ruff.toml`, `.flake8`

**Fallback**: Ask user for lint command or skip

**If errors**: Offer auto-fix or manual resolution

### Step 4.2: Run Formatter

**Detection order**:
1. `package.json` scripts: `format`, `prettier`
2. `Makefile`: `format` target
3. `pyproject.toml`: `[tool.ruff.format]` or `[tool.black]`
4. Config files: `.prettierrc*`

**If changes**: Stage automatically or ask user

### Step 4.3: Run Type Checker

**Detection**:
- `tsconfig.json` -> `npx tsc --noEmit`
- `mypy.ini` or pyproject.toml mypy -> `mypy .`
- `pyrightconfig.json` -> `pyright`

**If errors**: Show and ask how to proceed

### Step 4.4: Sync Lockfiles

Check if lockfiles are in sync:
- `package-lock.json` with `package.json`
- `uv.lock` with `pyproject.toml`

**If outdated**: Offer to update

---

## Phase 5: Tests

### Step 5.1: Run Test Suite

**Detection order**:
1. `package.json` scripts: `test`
2. `Makefile`: `test` target
3. `pyproject.toml`: pytest config
4. Directory detection: `tests/`, `__tests__/`

**If tests fail**:
- Show failure summary
- Options: View details, fix now, skip (note in PR)

### Step 5.2: Flag Skipped Tests

**Patterns**:
```python
@pytest.mark.skip
@unittest.skip
pytest.skip(
```

```javascript
it.skip(
test.skip(
describe.skip(
xit(
```

**If found**: Note for reviewer awareness

---

## Phase 6: Context-Aware Review Recommendations

Analyze changed files to recommend appropriate reviewers:

| Pattern Detected | Review Type |
|-----------------|-------------|
| auth, login, session, token, jwt, oauth, password, credential | Security |
| database, query, sql, migration, index, schema, model | Performance/DB |
| New entries in package.json, pyproject.toml, go.mod | Security + License |
| payment, billing, stripe, checkout, invoice | Compliance |
| Dockerfile, kubernetes, terraform, .github/workflows | Ops |

**Output**: Include recommendations in PR description

---

## Phase 7: Create PR

### Step 7.1: Gather Context

```bash
# Get issue number from branch name
branch=$(git branch --show-current)
issue_number=$(echo "$branch" | grep -oE '[0-9]+' | head -1)

# Get issue title
gh issue view $issue_number --json title -q '.title'

# Read PLANNING.md if exists
cat PLANNING.md

# Get commit messages
git log origin/main..HEAD --format='- %s'
```

### Step 7.2: Generate PR Description

**Template**:
```markdown
## Summary

Closes #<ISSUE_NUMBER>

<Summary from PLANNING.md or commit messages>

## Changes

<Bullet list from commits, grouped logically>

## Review Recommendations

Based on code analysis:
- [ ] **<Review Type>**: <Reason>
  - Files: `<file1>`, `<file2>`

## Test Plan

- [x] All tests pass
- [ ] Manual testing: <describe>

## Checklist

- [x] Linting passes
- [x] Formatting applied
- [x] Tests pass
- [ ] Documentation updated
```

### Step 7.3: Size Warning

- >500 lines: "**Large PR**: Consider splitting"
- >20 files: "**Many files**: Review may take longer"
- >1000 lines: "**Very Large PR**: Strongly recommend splitting"

### Step 7.4: Push and Create

```bash
git push -u origin $(git branch --show-current)
gh pr create --title "<type>: <description> (closes #<issue>)" --body "<description>"
```

**PR title prefixes**:
- `feat:` for features
- `fix:` for bugs
- `refactor:` for refactoring
- `docs:` for documentation
- `chore:` for maintenance

### Step 7.5: Display Results

```
PR Created Successfully!

PR:       #<number>
URL:      <url>
Title:    <title>
Branch:   <branch> -> main

Review Recommendations:
<summary>

Next Steps:
1. Review the PR description
2. Request reviews from recommended team members
3. Address any CI failures
```

---

## Error Handling

For unexpected errors in any phase:
1. Display error context
2. Offer: Retry, Skip this check, Abort workflow
3. Log skipped checks for PR description
