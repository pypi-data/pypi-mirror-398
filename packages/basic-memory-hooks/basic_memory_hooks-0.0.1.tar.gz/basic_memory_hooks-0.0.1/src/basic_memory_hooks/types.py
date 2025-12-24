"""Core types for Basic Memory Hooks."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HookStage(Enum):
    """When a hook executes in the note lifecycle."""

    PRE_WRITE = "pre_write"
    POST_WRITE = "post_write"
    PRE_EDIT = "pre_edit"  # Extension point for v1
    POST_EDIT = "post_edit"  # Extension point for v1


class HookPriority(Enum):
    """Execution order within a stage. Lower value = runs first."""

    FIRST = 0
    HIGH = 25
    NORMAL = 50
    LOW = 75
    LAST = 100


@dataclass
class HookContext:
    """Input context passed to each hook."""

    content: str
    title: str
    folder: str | None = None
    project: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HookResult:
    """Output from hook execution."""

    success: bool = True
    content: str | None = None  # None = unchanged, use previous content
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
