#!/usr/bin/env python3
"""Example: Integrate hooks into your own workflow.

This demonstrates how to:
1. Create custom hooks programmatically
2. Register them with the engine
3. Use different strictness levels
4. Handle results in your application

This pattern is useful when building tools that generate
Basic Memory content and want to ensure quality.
"""

from basic_memory_hooks.config import FormatConfig
from basic_memory_hooks.engine import HookEngine
from basic_memory_hooks.hook import Hook
from basic_memory_hooks.types import HookContext, HookPriority, HookResult, HookStage


# Example: Create a custom hook inline
class RequireCodeBlockHook(Hook):
    """Require at least one code block in technical memos."""

    @property
    def name(self) -> str:
        return "require_code_block"

    @property
    def stage(self) -> HookStage:
        return HookStage.PRE_WRITE

    @property
    def priority(self) -> HookPriority:
        return HookPriority.LOW

    def should_run(self, context: HookContext) -> bool:
        """Only run on technical content."""
        tech_keywords = ["api", "code", "function", "class", "implementation"]
        content_lower = context.content.lower()
        return any(kw in content_lower for kw in tech_keywords)

    def execute(self, context: HookContext) -> HookResult:
        has_code_block = "```" in context.content

        if not has_code_block:
            return HookResult(
                success=True,  # Warning only, not failure
                warnings=["Technical memo should include code examples"],
            )

        return HookResult(success=True)


def create_engine_with_custom_hooks() -> HookEngine:
    """Create an engine with custom configuration and hooks."""
    # Create engine with custom config
    engine = HookEngine()

    # Load config from string (useful for embedded configurations)
    config_content = """---
strictness: balanced
note_types:
  allowed:
    - memo
    - tutorial
    - reference
quality:
  minimum_observations: 1
  minimum_relations: 0
---
"""
    engine.load_config_from_string(config_content)

    # Register custom hook
    custom_hook = RequireCodeBlockHook(engine.config)
    engine.register_hook(custom_hook)

    return engine


def validate_content(engine: HookEngine, content: str, title: str) -> dict:
    """Validate content and return structured result."""
    result = engine.run(
        stage=HookStage.PRE_WRITE,
        content=content,
        title=title,
    )

    return {
        "valid": result.success,
        "content": result.content or content,
        "issues": result.errors + result.warnings,
        "auto_fixed": result.content is not None and result.content != content,
        "hooks_run": result.metadata.get("hooks_run", []),
    }


def main():
    # Create engine with our custom setup
    engine = create_engine_with_custom_hooks()

    # Example 1: Well-formed technical memo with code
    good_memo = """---
title: Using the API
type: tutorial
---

# Using the API

How to use our Python API.

## Observations

- [technique] Import the engine from basic_memory_hooks.engine
- [example] See the code block below

## Example

```python
from pathlib import Path
from basic_memory_hooks.engine import HookEngine

# Load from a Basic Memory project
project = Path("~/my-notes").expanduser()
engine = HookEngine()
engine.load_config(project / ".basic-memory" / "format.md")
engine.load_custom_hooks(project / ".basic-memory")
```
"""

    print("=== Example 1: Well-formed memo ===")
    result = validate_content(engine, good_memo, "Using the API")
    print(f"Valid: {result['valid']}")
    print(f"Issues: {result['issues']}")
    print(f"Hooks run: {result['hooks_run']}")

    # Example 2: Technical memo missing code block
    missing_code = """---
title: API Implementation
type: memo
---

# API Implementation

This memo discusses the implementation of our API.

## Observations

- [fact] The API uses FastAPI for HTTP endpoints
- [decision] We chose REST over GraphQL
"""

    print("\n=== Example 2: Technical memo without code ===")
    result = validate_content(engine, missing_code, "API Implementation")
    print(f"Valid: {result['valid']}")
    print(f"Issues: {result['issues']}")

    # Example 3: Memo with formatting issues (will be auto-fixed)
    messy_memo = """---
title: Quick Note
type: memo
---

# Quick Note

Some observations.

## Observations

- fact: This uses wrong format
- decision: This too
"""

    print("\n=== Example 3: Messy formatting (auto-fixed) ===")
    result = validate_content(engine, messy_memo, "Quick Note")
    print(f"Valid: {result['valid']}")
    print(f"Auto-fixed: {result['auto_fixed']}")

    # Show the fixed content
    if result["auto_fixed"]:
        print("\nFixed observations section:")
        for line in result["content"].split("\n"):
            if line.strip().startswith("- ["):
                print(f"  {line}")


if __name__ == "__main__":
    main()
