# SPEC-2: Hook System Interface

## Why

The hook system needs a Python interface that provides deterministic validation. Python was chosen because code either passes or fails—no interpretation ambiguity.

## What

- `basic_memory_hooks` Python package on PyPI
- Hook base class and engine
- Standard hooks for common validation/formatting
- Custom hook loading from project directory

## How (High Level)

### Core Types

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any

class HookStage(Enum):
    PRE_WRITE = "pre_write"
    POST_WRITE = "post_write"
    PRE_EDIT = "pre_edit"    # Extension point
    POST_EDIT = "post_edit"  # Extension point

class HookPriority(Enum):
    FIRST = 0
    HIGH = 25
    NORMAL = 50
    LOW = 75
    LAST = 100

@dataclass
class HookContext:
    content: str
    title: str
    folder: Optional[str] = None
    project: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class HookResult:
    success: bool = True
    content: Optional[str] = None  # None = use previous content
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
```

### Hook Base Class

```python
class Hook(ABC):
    def __init__(self, config: FormatConfig):
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str: pass

    @property
    @abstractmethod
    def stage(self) -> HookStage: pass

    @property
    def priority(self) -> HookPriority:
        return HookPriority.NORMAL

    @abstractmethod
    def execute(self, context: HookContext) -> HookResult: pass

    def should_run(self, context: HookContext) -> bool:
        return True
```

### HookEngine

```python
class HookEngine:
    def load_config(self, path: str) -> None:
        """Load .basic-memory/format.md and parse frontmatter."""

    def load_config_from_string(self, content: str) -> None:
        """Load config from raw file content."""

    def run(self, stage: HookStage, content: str, title: str,
            folder: str = None, project: str = None) -> HookResult:
        """Execute all hooks for stage in priority order."""
```

### Execution Model

Priority order: FIRST (0) → HIGH (25) → NORMAL (50) → LOW (75) → LAST (100)

Content flow: Each hook receives content from previous hook. If hook returns `content=None`, previous content passes through.

Error handling:
- All hooks run regardless of errors
- Errors and warnings collected from all hooks
- strict mode: any error → `success=False`
- balanced mode: errors become warnings → `success=True`
- flexible mode: only formatting hooks run → `success=True`

### Standard Hooks (PRE_WRITE)

**FIRST priority:**
- `validate_frontmatter` - Check required frontmatter fields

**HIGH priority:**
- `remove_duplicate_headings` - Remove duplicate headings (auto-fix)
- `consolidate_observations` - Merge multiple Observations sections (auto-fix)

**NORMAL priority:**
- `format_observations` - Standardize observation format (auto-fix)
- `validate_minimum_observations` - Check count >= minimum
- `validate_note_type` - Check type in allowed list
- `validate_observation_categories` - Check required categories
- `validate_tag_prefixes` - Check prefixes if enforced
- `order_relations` - Primary before secondary (auto-fix)

### Standard Hooks (POST_WRITE)

**NORMAL priority:**
- `verify_relation_targets` - Check targets exist

PRE_EDIT/POST_EDIT are extension points. No standard hooks use them in v1.

### Custom Hooks

Discovered from `.basic-memory/hooks/*.py`. Classes inheriting from `Hook` are auto-registered. Skip if `enabled: false` in config. Import errors are logged but don't stop engine.

## How to Evaluate

### Success Criteria
- [ ] Hook ABC enforces required interface
- [ ] Hooks receive config via constructor
- [ ] HookEngine executes hooks in priority order
- [ ] Content flows correctly through chain
- [ ] All hooks run regardless of errors
- [ ] Strictness controls success value
- [ ] Custom hooks load from directory

### Test Cases
- Hook modifies content, next hook receives modified
- Hook returns None, previous content passes through
- Error in strict → success=False
- Error in balanced → success=True with warning
- Custom hook import error logged, engine continues
