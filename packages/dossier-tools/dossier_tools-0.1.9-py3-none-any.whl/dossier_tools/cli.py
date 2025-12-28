"""CLI entry point for dossier-tools.

This module re-exports the main CLI group from the cli package.
All commands are defined in cli/local.py and cli/registry.py.
"""

from .cli import main

__all__ = ["main"]

if __name__ == "__main__":
    main()
