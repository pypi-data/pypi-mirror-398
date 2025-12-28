# Dossier Caching & Distribution Design

**Status**: Draft
**Author**: @yuvaldim
**Date**: 2025-12-16

## Problem Statement

The current `pull` command downloads dossiers to the current working directory, which has several issues:

1. **Project-centric**: Dossiers are tied to specific projects instead of being reusable across the system
2. **No single source of truth**: Downloaded files can drift from registry versions
3. **Wrong mental model**: Downloading to `./` implies vendoring/checking in, but dossiers should be referenced by name like Docker images
4. **No discoverability**: `dossier list` shows dossiers but doesn't provide URLs or access information

## Goals

- Enable dossiers to be used across multiple projects without duplication
- Provide a caching mechanism similar to Docker's image model
- Maintain registry as single source of truth
- Improve discoverability with URLs and detailed info

## Non-Goals

- Offline-first architecture (network access assumed for `run`)
- Complex dependency resolution between dossiers
- Automatic background sync/updates

## Design

### Mental Model: Docker-style

Dossiers are like **Dockerfiles**, not Docker images - they're small text files that define workflows. The distribution model follows Docker's approach:

| Docker | Dossier |
|--------|---------|
| `docker pull nginx` | `dossier pull myorg/deploy` |
| `docker run nginx` | `dossier run myorg/deploy` |
| `docker images` | `dossier cache list` |
| `docker rmi nginx` | `dossier cache clean myorg/deploy` |
| Images stored in `~/.docker/` | Dossiers cached in `~/.dossier/cache/` |

### Cache Location

```
~/.dossier/
├── credentials          # existing auth storage
├── keys/                # existing key storage
└── cache/
    └── myorg/
        └── deploy/
            ├── 1.0.0.ds.md
            ├── 1.1.0.ds.md
            └── latest -> 1.1.0.ds.md  # symlink to latest
```

### Command Changes

#### `dossier pull` (Modified)

**Current behavior**: Downloads to `./myorg-deploy.ds.md`

**New behavior**: Caches to `~/.dossier/cache/`

```bash
# Cache latest version
dossier pull myorg/deploy
# → Cached: ~/.dossier/cache/myorg/deploy/1.0.0.ds.md

# Cache specific version
dossier pull myorg/deploy@1.0.0
# → Cached: ~/.dossier/cache/myorg/deploy/1.0.0.ds.md

# Force re-download (bypass cache)
dossier pull --force myorg/deploy

# Pull multiple
dossier pull myorg/deploy myorg/backup
```

**Output**:
```
Pulling myorg/deploy@1.0.0...
Cached: ~/.dossier/cache/myorg/deploy/1.0.0.ds.md
```

#### `dossier export` (New)

Explicit file download for when you actually want a local file (e.g., to customize or vendor).

```bash
# Export to specific file
dossier export myorg/deploy -o ./workflows/deploy.ds.md

# Export to stdout
dossier export myorg/deploy --stdout

# Export specific version
dossier export myorg/deploy@1.0.0 -o ./deploy.ds.md
```

#### `dossier run` (Modified)

**Current behavior**: Always fetches from registry

**New behavior**: Check cache first, fall back to registry

```bash
dossier run myorg/deploy
# 1. Check ~/.dossier/cache/myorg/deploy/
# 2. If cached, use cached version
# 3. If not cached, fetch from registry (don't cache)

# Force fetch from registry (ignore cache)
dossier run --no-cache myorg/deploy

# Run and cache for future use
dossier run --pull myorg/deploy
```

**Rationale for not auto-caching on run**: Keeps behavior predictable. Users explicitly choose to cache with `pull`. Matches Docker's model where `run` uses cache but doesn't populate it unless `--pull` is specified.

#### `dossier cache` (New)

Cache management commands.

```bash
# List cached dossiers
dossier cache list
# NAME                    VERSION    CACHED AT
# myorg/deploy            1.0.0      2024-01-15 10:30
# myorg/backup            2.1.0      2024-01-14 09:00

# List with sizes
dossier cache list --size

# Clean all cache
dossier cache clean
# Removed 5 cached dossiers (12.3 KB)

# Clean specific dossier (all versions)
dossier cache clean myorg/deploy

# Clean specific version
dossier cache clean myorg/deploy@1.0.0

# Clean old entries (older than N days)
dossier cache clean --older-than 30
```

#### `dossier get` (Enhanced)

Add URL information to output.

```bash
dossier get myorg/deploy
```

**Current output**:
```
Source: registry:myorg/deploy

Name:      deploy
Title:     Deploy to Production
Version:   1.0.0
Status:    stable
...
```

**New output**:
```
Source: registry:myorg/deploy

Name:      deploy
Title:     Deploy to Production
Version:   1.0.0
Status:    stable
...

Registry:  https://dossier-registry.dev/myorg/deploy
Raw URL:   https://dossier-registry.dev/api/v1/dossiers/myorg/deploy/content
Cached:    ~/.dossier/cache/myorg/deploy/1.0.0.ds.md (or "No")
```

#### `dossier list` (Enhanced)

Add optional URL column.

```bash
# Current (unchanged default)
dossier list

# With URLs
dossier list --url
# NAME                    VERSION    TITLE                 URL
# myorg/deploy            1.0.0      Deploy to Production  https://...
```

#### `dossier outdated` (New, Optional)

Show cached dossiers that have newer versions in registry.

```bash
dossier outdated
# NAME                    CACHED     LATEST
# myorg/deploy            1.0.0      1.2.0
# myorg/backup            2.1.0      2.1.0  (up to date)
```

### Update Strategy

Following Docker's model: **explicit updates only**.

- `dossier pull` fetches latest and updates cache
- `dossier run` uses cache as-is, never auto-updates
- `dossier outdated` shows what's stale (optional command)
- No TTL or background updates (keeps it simple and predictable)

**Rationale**: Auto-updates can break workflows unexpectedly. Explicit updates give users control. This matches Docker, npm, and most package managers.

### Backward Compatibility

| Current Command | New Behavior | Migration |
|-----------------|--------------|-----------|
| `dossier pull myorg/deploy` | Caches to `~/.dossier/cache/` instead of `./` | Breaking change - document in changelog |
| `dossier pull -o ./file.md` | Deprecated, use `dossier export` | Show deprecation warning, remove in v1.0 |
| `dossier run` | Check cache first | Non-breaking, additive |

### Command Summary

| Command | Description |
|---------|-------------|
| `dossier list` | List registry dossiers |
| `dossier list --url` | List with URLs |
| `dossier get <name>` | Show dossier details + URLs |
| `dossier pull <name>` | Cache dossier locally |
| `dossier pull --force` | Re-download and update cache |
| `dossier export <name> -o <file>` | Download to specific file |
| `dossier run <name>` | Run (cache → registry fallback) |
| `dossier run --no-cache` | Run from registry only |
| `dossier run --pull` | Pull + run |
| `dossier cache list` | Show cached dossiers |
| `dossier cache clean` | Clear cache |
| `dossier outdated` | Show stale cached dossiers |

## Implementation Plan

### Phase 1: Cache Infrastructure
- [ ] Create cache directory structure (`~/.dossier/cache/`)
- [ ] Add cache read/write utilities
- [ ] Modify `pull` to cache instead of download to `./`

### Phase 2: Run Integration
- [ ] Modify `run` to check cache first
- [ ] Add `--no-cache` flag to `run`
- [ ] Add `--pull` flag to `run`

### Phase 3: Cache Management
- [ ] Implement `dossier cache list`
- [ ] Implement `dossier cache clean`

### Phase 4: Discoverability
- [ ] Add URLs to `dossier get` output
- [ ] Add `--url` flag to `dossier list`
- [ ] Implement `dossier export` command

### Phase 5: Polish (Optional)
- [ ] Implement `dossier outdated`
- [ ] Add cache size tracking
- [ ] Add `--older-than` to cache clean

## Open Questions

1. **Should `run` auto-cache on first use?** Current proposal: No, keep explicit. User can use `run --pull`.

2. **Version resolution**: When cache has `1.0.0` but registry has `1.1.0`, what does `run myorg/deploy` use?
   - Proposal: Uses cached version. User must `pull` to update.

3. **Symlinks for `latest`**: Worth the complexity?
   - Proposal: Skip for now, just store versioned files.

4. **Cache metadata**: Store pull timestamp, source URL?
   - Proposal: Yes, in a `.meta.json` file alongside cached dossier.

## Alternatives Considered

### 1. TTL-based Auto-refresh
Check registry for updates if cache is older than 24 hours.

**Rejected**: Adds complexity, can cause unexpected behavior changes, doesn't match Docker model.

### 2. Keep Current `pull` Behavior
Download to current directory by default.

**Rejected**: Wrong mental model for reusable workflows across projects.

### 3. No Caching
Always fetch from registry.

**Rejected**: Slower, no offline capability, unnecessary network traffic.

## References

- [Docker CLI Reference](https://docs.docker.com/reference/cli/docker/)
- [npm cache documentation](https://docs.npmjs.com/cli/cache)
