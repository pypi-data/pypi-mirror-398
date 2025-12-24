#!/usr/bin/env python3
"""Example: Validate a memo using the Python API.

This script demonstrates the full workflow:
1. Load configuration from a Basic Memory project's .basic-memory/format.md
2. Load custom hooks from the project's .basic-memory/hooks/ directory
3. Validate memo content
4. Handle the result

The .basic-memory/ directory lives in your Basic Memory project folder:

    ~/my-notes/              # Your Basic Memory project
      .basic-memory/         # Configuration directory
        format.md            # Hooks configuration
        hooks/               # Custom hooks directory
          my_hook.py
      notes/                 # Your notes
      ...

Usage:
    # Validate against a project's configuration
    python examples/validate_memo.py --project ~/my-notes

    # Validate a specific file
    python examples/validate_memo.py --project ~/my-notes --file path/to/memo.md

    # Use demo mode (no project required)
    python examples/validate_memo.py --demo
"""

import argparse
import json
import sys
from pathlib import Path

from basic_memory_hooks.engine import HookEngine
from basic_memory_hooks.types import HookStage


def validate_memo(
    content: str,
    title: str,
    project_path: Path | None = None,
) -> dict:
    """Validate a memo using the configured hooks.

    Args:
        content: The memo markdown content.
        title: The memo title.
        project_path: Path to Basic Memory project (contains .basic-memory/).

    Returns:
        Dictionary with validation results.
    """
    engine = HookEngine()

    if project_path:
        bm_dir = project_path / ".basic-memory"
        config_path = bm_dir / "format.md"

        if config_path.exists():
            engine.load_config(config_path)
            print(f"Loaded config from: {config_path}")

            # Load custom hooks - paths in config are relative to .basic-memory/
            engine.load_custom_hooks(bm_dir)
        else:
            print(f"No format.md found at {config_path}, using defaults")
    else:
        print("Using default configuration (no project specified)")

    # Run pre-write validation
    result = engine.run(
        stage=HookStage.PRE_WRITE,
        content=content,
        title=title,
    )

    return {
        "success": result.success,
        "content": result.content,
        "errors": result.errors,
        "warnings": result.warnings,
        "metadata": result.metadata,
    }


DEMO_MEMO = """---
title: Hook Priority Example
type: memo
tags:
  - hooks
  - architecture
---

# Hook Priority Example

This memo documents how hook priorities work.

## Observations

- [technique] Use PRE_WRITE stage for validation before saving
- [fact] Priorities execute in order: FIRST, HIGH, NORMAL, LOW, LAST
- [decision] Custom hooks integrate seamlessly with standard hooks

## Relations

- implements [[Basic Memory Hooks Architecture]]
- relates_to [[Hook-Based Architecture]]
"""


def main():
    parser = argparse.ArgumentParser(
        description="Validate a Basic Memory memo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --demo                    Run with demo content and defaults
  %(prog)s --project ~/my-notes      Use project's .basic-memory/ config
  %(prog)s -p ~/my-notes -f note.md  Validate a specific file
        """,
    )
    parser.add_argument(
        "--project", "-p",
        help="Path to Basic Memory project folder (contains .basic-memory/)",
    )
    parser.add_argument(
        "--file", "-f",
        help="Path to memo file to validate",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demo with example content (no project required)",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON",
    )
    args = parser.parse_args()

    # Determine project path
    project_path = Path(args.project) if args.project else None

    # Get content to validate
    if args.file:
        file_path = Path(args.file)
        content = file_path.read_text()
        title = file_path.stem
    else:
        content = DEMO_MEMO
        title = "Hook Priority Example"

    # Validate
    print()
    result = validate_memo(content, title, project_path)

    # Output results
    print()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Validation {'PASSED' if result['success'] else 'FAILED'}")
        hooks_run = result['metadata'].get('hooks_run', [])
        if hooks_run:
            print(f"Hooks run: {', '.join(hooks_run)}")

        if result["errors"]:
            print("\nErrors:")
            for error in result["errors"]:
                print(f"  - {error}")

        if result["warnings"]:
            print("\nWarnings:")
            for warning in result["warnings"]:
                print(f"  - {warning}")

        if result["content"] and result["content"] != content:
            print("\nContent was auto-fixed. Use --json to see the fixed content.")

    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
