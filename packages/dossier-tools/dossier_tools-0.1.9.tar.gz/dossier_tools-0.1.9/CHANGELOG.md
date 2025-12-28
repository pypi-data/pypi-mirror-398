# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Registry commands: `list`, `get`, `pull`, `publish`, `login`, `logout`, `whoami`
- GitHub OAuth authentication for registry
- Documentation: CLI reference, API docs, schema reference, signing guide
- Pre-commit hooks configuration
- Issue and PR templates

### Changed

- Auth flow now uses copy/paste instead of local HTTP server

## [0.1.0] - 2024-12-04

Initial release.

### Added

- Core parsing and validation of `.ds.md` files
- JSON Schema validation for frontmatter
- SHA256 checksum calculation and verification
- Ed25519 signing and verification
- Key management in `~/.dossier/`
- CLI commands: `init`, `generate-keys`, `create`, `validate`, `checksum`, `sign`, `verify`, `info`
