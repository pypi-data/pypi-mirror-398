# Basic Memory Hooks

**Structured output for your memos.**

Validates and formats memos before they're saved—catching LLM inconsistencies and fixing them automatically. No more hoping the model remembers your format. No more manual cleanup. Just consistent, machine-readable memos, every time.

## The Problem

You ask an LLM to write a memo and get back something that *almost* follows your format:

```markdown
## Observations
- fact: The API uses REST      ← Wrong format
- [decision] Use Python        ← Correct format
- This is important            ← Missing category entirely

## Observations                ← Duplicate section
- [fact] Another observation
```

Each inconsistency breaks your knowledge graph. Queries return garbage. Links fail.

## The Solution

Basic Memory Hooks fixes these automatically:

```markdown
## Observations
- [fact] The API uses REST
- [decision] Use Python
- [fact] This is important
- [fact] Another observation
```

Duplicate sections merged. Formats corrected. Content preserved.

## Installation

```bash
pip install basic-memory-hooks
```

## Quick Start

### With Basic Memory Plugins

If you're using `basic-memory-plugins`, hooks integrate automatically:

```
You: /remember API design decision
          ↓
basic-memory-plugins prepares the memo
          ↓
basic-memory-hooks validates and fixes it
          ↓
Clean memo saved to your project
```

Install both, add a `format.md` config, and every `/remember`, `/research`, and `/continue` runs through validation.

### Python Library

```python
from basic_memory_hooks import HookEngine, HookStage

engine = HookEngine()
engine.load_config(".basic-memory/format.md")

result = engine.run(
    stage=HookStage.PRE_WRITE,
    content="# My Note...",
    title="My Note",
)

if result.success:
    print(result.content)  # Cleaned content
else:
    print("Errors:", result.errors)
```

### Web API

```bash
python -m basic_memory_hooks  # Starts FastAPI server
```

```bash
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d '{"content": "...", "title": "My Memo"}'
```

Why a Web API? Basic Memory Cloud uses it for server-side validation. Self-hosted setups can centralize validation across multiple agents. And API-only integrations—agents without a Python runtime—can call it over HTTP.

## Configuration

Create `.basic-memory/format.md` in your project with YAML frontmatter:

```markdown
---
version: "1.0"
strictness: balanced

note_types:
  allowed: [memo, spec, decision, project]

quality:
  minimum_observations: 1
  require_tags: false
---

# Project Format Configuration

Your project-specific format rules.
```

Three strictness levels:
- **strict**: Errors fail validation. For production pipelines.
- **balanced**: Errors become warnings. Fixes what it can, accepts the rest.
- **flexible**: Only formatting hooks run. Maximum permissiveness.

## Standard Hooks

| Hook | What it does |
|------|--------------|
| **validate_frontmatter** | Ensures title and type exist |
| **validate_note_type** | Type must be in allowed list |
| **validate_minimum_observations** | Minimum observation count |
| **validate_observation_categories** | Required categories must be used |
| **format_observations** | Fixes `- category:` to `- [category]` |
| **remove_duplicate_headings** | Merges duplicate sections |
| **consolidate_observations** | Combines multiple Observations sections |
| **order_relations** | Primary relations before secondary |

## Custom Hooks

Add project-specific validation in `.basic-memory/hooks/`:

```python
# .basic-memory/hooks/my_hook.py
from basic_memory_hooks import Hook, HookContext, HookResult, HookStage, HookPriority

class MyCustomHook(Hook):
    @property
    def name(self) -> str:
        return "my_custom_hook"

    @property
    def stage(self) -> HookStage:
        return HookStage.PRE_WRITE

    @property
    def priority(self) -> HookPriority:
        return HookPriority.NORMAL

    def execute(self, context: HookContext) -> HookResult:
        # Your validation logic here
        return HookResult(success=True)
```

Reference it in your `format.md`:

```yaml
custom_hooks:
  - path: hooks/my_hook.py
    enabled: true
```

## License

MIT
