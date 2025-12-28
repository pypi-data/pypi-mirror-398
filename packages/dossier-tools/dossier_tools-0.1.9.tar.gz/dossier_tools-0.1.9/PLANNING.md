# Issue #6: Add install-skill command to download skills from registry

## Type
feature

## Problem Statement
Add a new CLI command to install Claude Code skills from the registry directly into `.claude/skills/`.

### Motivation
Currently users must manually create skill files or download them via curl. A dedicated command would:
- Simplify skill installation
- Enable skill discovery via registry
- Maintain consistency with `dossier pull` pattern

### Proposed Usage
```bash
# Install a skill from registry
dossier install-skill imboard-ai/skills/start-issue

# Installs to: ~/.claude/skills/<name>/SKILL.md
```

## Acceptance Criteria
- [x] New `install-skill` command in CLI
- [x] Downloads skill file from registry to `~/.claude/skills/<name>/SKILL.md`
- [x] Creates directory structure if needed
- [x] Shows success message with path

## Implementation Checklist
- [x] Understand the issue and gather context
- [x] Identify files that need modification
- [x] Implement the changes
- [x] Add/update tests (5 tests added)
- [x] Self-review the changes
- [ ] Create pull request

## Files Modified
- `src/dossier_tools/cli/__init__.py` - Added `install-skill` to command sections
- `src/dossier_tools/cli/registry.py` - Added `_fetch_and_save_dossier()` helper and `install_skill` command
- `tests/test_cli.py` - Added `TestInstallSkill` test class with 5 tests

## Implementation Notes
- Extracted `_fetch_and_save_dossier()` helper function to share logic between `export` and `install-skill`
- Skills are installed to `~/.claude/skills/<skill-name>/SKILL.md`
- The skill name is extracted from the last segment of the dossier path
- Added `--force` flag to allow overwriting existing skills
- Supports version specifiers (e.g., `myorg/skill@1.0.0`)

## Testing
- [x] Unit tests (5 tests in `TestInstallSkill` class)
- [x] Manual testing with real registry

## Related Issues/PRs
- Issue: #6
