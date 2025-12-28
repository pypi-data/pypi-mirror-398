# Skills + Dossiers: The Hybrid Model

> Why you need both, and how they work together

---

## TL;DR

**Skills** = Natural language triggers (local, personal)
**Dossiers** = Versioned workflow engines (registry, organizational)
**Pattern C** = Skills trigger dossiers = Best of both worlds

---

## The Objection

> "I have Claude Code skills. Who needs dossiers?"

This document answers that question.

---

## The Hybrid Model (Pattern C)

```
┌──────────────────────────────────────────────────────────────────────┐
│                         USER EXPERIENCE                               │
│                                                                       │
│   USER: "start working on issue 123"                                  │
│                    │                                                  │
│                    ▼                                                  │
│   ┌─────────────────────────────┐                                    │
│   │  SKILL (Local Trigger)      │  ← Natural language               │
│   │  ~/.claude/skills/start-issue│  ← Auto-discovery                 │
│   └──────────────┬──────────────┘  ← Zero friction                  │
│                  │                                                    │
│                  ▼                                                    │
│   ┌─────────────────────────────┐                                    │
│   │  DOSSIER (Registry Engine)  │  ← Versioned                      │
│   │  imboard-ai/git/setup-issue │  ← Signed                         │
│   │  @1.2.0                     │  ← Shared                         │
│   └─────────────────────────────┘  ← Trusted                        │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Skills vs Dossiers: Feature Comparison

| Feature | Skill | Dossier |
|---------|-------|---------|
| Natural language invocation | Yes | No |
| Auto-discovery by context | Yes | No |
| Zero-friction trigger | Yes | No |
| Tool restrictions | Yes | No |
| Central registry | No | Yes |
| Semantic versioning | No | Yes |
| Cross-org publishing | No | Yes |
| Checksum verification | No | Yes |
| Digital signatures | No | Yes |
| Schema validation | No | Yes |
| `search` / `list` discovery | No | Yes |

**Key insight**: They're complementary, not competing.

---

## Real-World Scenarios

| Scenario | Skills Only | Skills + Dossiers |
|----------|-------------|-------------------|
| **You improve the workflow** | Edit local file, tell team to copy it | `dossier publish` → team runs `dossier pull` |
| **Teammate has better version** | Slack/email the file around | `dossier search setup-issue` → find it |
| **New hire joins** | "Check the wiki for our skills" | `dossier list your-org` → ready to go |
| **Workflow breaks after update** | "Who changed the skill??" | `dossier run workflow@1.0.0` → pin version |
| **Using workflow from another team** | Copy-paste, hope it works | Registry: verified, signed, trusted |
| **Auditing what ran** | Check git blame on skill file | Checksum + signature in execution log |
| **10 teams, 50 workflows** | 50 scattered skill files | Registry: searchable, categorized |

---

## The Core Arguments

### 1. Skills Are Personal, Dossiers Are Organizational

```
Skills                              Dossiers
─────────────────                   ─────────────────
~/.claude/skills/                   dossier search *
└── my-workflow/                    └── 1000+ workflows
    └── SKILL.md                        ├── imboard-ai/...
                                        ├── acme-corp/...
    "Works on my machine"               └── your-org/...

                                        "Works everywhere"
```

### 2. Skills Trigger, Dossiers Execute

| Layer | Responsibility | Changes Often? | Shared How? |
|-------|---------------|----------------|-------------|
| **Skill** | "When to run" (trigger words) | Rarely | Local git |
| **Dossier** | "How to run" (workflow steps) | Often | Registry |

**Benefit**: Iterate on the dossier (improve workflow), skill stays stable (same trigger).

### 3. Frontend vs Backend

```
┌─────────────────────────────────────────────────────────────┐
│                        ANALOGY                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   SKILL = Button in your app                                │
│           • User-facing                                      │
│           • Simple trigger                                   │
│           • "Start Issue" button                             │
│                                                              │
│   DOSSIER = API/Microservice behind it                      │
│           • Versioned                                        │
│           • Tested                                           │
│           • Shared infrastructure                            │
│           • Can be upgraded without changing the button      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4. The npm/pip Argument

> "I can just write Python code, why do I need pip?"

Same logic applies:

| Need | pip/npm | Dossier Registry |
|------|---------|------------------|
| **Discoverability** | `npm search` | `dossier search` |
| **Versioning** | `package@1.2.3` | `dossier@1.2.3` |
| **Trust** | Verified publishers | Signed dossiers |
| **Updates** | `npm update` | `dossier pull` |
| **Sharing** | `npm publish` | `dossier publish` |

**Dossiers = npm/pip for AI workflows.**

---

## Pattern C: Implementation Example

### The Skill (Trigger)

`~/.claude/skills/start-issue/SKILL.md`:

```yaml
---
name: start-issue
description: Set up a GitHub issue for development with branch, worktree, and planning doc.
  Use when user says "start issue", "work on issue #X", "set up issue", or "begin issue".
---

# Start Issue Workflow

When the user wants to start working on a GitHub issue:

1. Extract the issue number from their request
2. Run the setup workflow:
   ```bash
   dossier run imboard-ai/development/git/setup-issue-workflow
   ```
3. When prompted for issue number, provide the extracted number
4. Confirm successful setup with the user
```

### The Dossier (Engine)

Lives in registry at `imboard-ai/development/git/setup-issue-workflow`:

- Versioned (v1.0.0, v1.1.0, etc.)
- Signed by author
- Discoverable via `dossier search`
- Contains full workflow logic

### User Experience

```
User: "Hey, start working on issue 456"

Claude: [Skill auto-triggers]
        [Runs dossier workflow]

        Issue workflow setup complete!

        Issue:      #456 - Add dark mode support
        Type:       feature
        Branch:     feature/456-add-dark-mode-support
        Worktree:   ../feature-456
        Planning:   ../feature-456/PLANNING.md

        Ready to start coding!
```

---

## When to Use What

| Use Case | Recommended |
|----------|-------------|
| Quick personal shortcut | Skill only |
| Team-shared complex workflow | Dossier only |
| Frequently-used team workflow | Skill + Dossier |
| One-time setup task | Dossier only |
| Context-triggered automation | Skill + Dossier |

---

## Summary

| | Skill | Dossier | Skill + Dossier |
|---|:---:|:---:|:---:|
| Natural language trigger | ✅ | ❌ | ✅ |
| Versioned | ❌ | ✅ | ✅ |
| Registry/searchable | ❌ | ✅ | ✅ |
| Signed/trusted | ❌ | ✅ | ✅ |
| Cross-org sharing | ❌ | ✅ | ✅ |
| Zero friction | ✅ | ❌ | ✅ |

**Pattern C gives you everything.**

---

## One-Liner

> "Skills are how YOU trigger workflows. Dossiers are how TEAMS share, version, and trust workflows. Use both."
