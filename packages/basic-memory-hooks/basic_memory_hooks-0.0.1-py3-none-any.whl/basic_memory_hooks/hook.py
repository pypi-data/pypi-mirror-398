"""Hook base class."""

from abc import ABC, abstractmethod

from basic_memory_hooks.config import FormatConfig
from basic_memory_hooks.types import HookContext, HookPriority, HookResult, HookStage


class Hook(ABC):
    """Base class for all hooks.

    Hooks receive config via constructor and can access it via self.config.
    """

    def __init__(self, config: FormatConfig):
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this hook."""
        pass

    @property
    @abstractmethod
    def stage(self) -> HookStage:
        """Which stage this hook runs in."""
        pass

    @property
    def priority(self) -> HookPriority:
        """Execution order within stage. Default: NORMAL."""
        return HookPriority.NORMAL

    @abstractmethod
    def execute(self, context: HookContext) -> HookResult:
        """Execute hook logic.

        Args:
            context: Input context with content, title, folder, etc.

        Returns:
            HookResult with success status, optionally modified content,
            and any errors/warnings.
        """
        pass

    def should_run(self, context: HookContext) -> bool:
        """Optional: conditional execution. Default: always run."""
        return True
