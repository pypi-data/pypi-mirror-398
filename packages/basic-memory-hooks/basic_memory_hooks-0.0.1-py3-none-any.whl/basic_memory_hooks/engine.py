"""Hook execution engine."""

import importlib.util
import logging
import sys
from pathlib import Path

from basic_memory_hooks.config import FormatConfig
from basic_memory_hooks.hook import Hook
from basic_memory_hooks.parser import load_config_from_file, load_config_from_string
from basic_memory_hooks.types import HookContext, HookPriority, HookResult, HookStage

logger = logging.getLogger(__name__)


# Map string priority to enum
PRIORITY_MAP = {
    "first": HookPriority.FIRST,
    "high": HookPriority.HIGH,
    "normal": HookPriority.NORMAL,
    "low": HookPriority.LOW,
    "last": HookPriority.LAST,
}


class HookEngine:
    """Executes hooks in priority order."""

    def __init__(self):
        self._hooks: list[Hook] = []
        self._config: FormatConfig = FormatConfig()

    @property
    def config(self) -> FormatConfig:
        """Get current configuration."""
        return self._config

    def load_config(self, path: str | Path) -> None:
        """Load configuration from format.md file.

        Args:
            path: Path to format.md file.
        """
        self._config = load_config_from_file(path)
        self._register_standard_hooks()

    def load_config_from_string(self, content: str) -> None:
        """Load configuration from raw file content.

        Args:
            content: Raw format.md file content.
        """
        self._config = load_config_from_string(content)
        self._register_standard_hooks()

    def _register_standard_hooks(self) -> None:
        """Register all enabled standard hooks."""
        self._hooks.clear()

        # Import here to avoid circular imports
        from basic_memory_hooks.hooks import get_standard_hooks

        for hook_class in get_standard_hooks():
            hook = hook_class(self._config)
            if self._is_hook_enabled(hook):
                self._hooks.append(hook)

    def _is_hook_enabled(self, hook: Hook) -> bool:
        """Check if a hook is enabled in config."""
        hook_name = hook.name

        if hook.stage == HookStage.PRE_WRITE:
            stage_config = self._config.hooks.pre_write
            hook_config = getattr(stage_config, hook_name, None)
            if hook_config:
                return hook_config.enabled
        elif hook.stage == HookStage.POST_WRITE:
            stage_config = self._config.hooks.post_write
            hook_config = getattr(stage_config, hook_name, None)
            if hook_config:
                return hook_config.enabled

        return True  # Default to enabled

    def _get_hook_priority(self, hook: Hook) -> HookPriority:
        """Get configured priority for a hook."""
        hook_name = hook.name

        if hook.stage == HookStage.PRE_WRITE:
            stage_config = self._config.hooks.pre_write
            hook_config = getattr(stage_config, hook_name, None)
            if hook_config:
                return PRIORITY_MAP.get(hook_config.priority, hook.priority)
        elif hook.stage == HookStage.POST_WRITE:
            stage_config = self._config.hooks.post_write
            hook_config = getattr(stage_config, hook_name, None)
            if hook_config:
                return PRIORITY_MAP.get(hook_config.priority, hook.priority)

        return hook.priority

    def register_hook(self, hook: Hook) -> None:
        """Register a hook instance.

        Args:
            hook: Hook instance to register.
        """
        self._hooks.append(hook)

    def load_custom_hooks(self, directory: str | Path) -> None:
        """Load custom hooks from directory.

        Args:
            directory: Path to hooks directory.
        """
        directory = Path(directory)
        if not directory.exists():
            return

        for hook_config in self._config.custom_hooks:
            if not hook_config.enabled:
                continue

            hook_path = directory / hook_config.path
            if not hook_path.exists():
                logger.warning(f"Custom hook not found: {hook_path}")
                continue

            try:
                self._load_hooks_from_file(hook_path)
            except Exception as e:
                logger.error(f"Failed to load custom hook {hook_path}: {e}")

    def _load_hooks_from_file(self, path: Path) -> None:
        """Load hook classes from a Python file."""
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            return

        module = importlib.util.module_from_spec(spec)
        sys.modules[path.stem] = module

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            logger.error(f"Error executing module {path}: {e}")
            return

        # Find Hook subclasses
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isinstance(obj, type)
                and issubclass(obj, Hook)
                and obj is not Hook
            ):
                try:
                    hook = obj(self._config)
                    self._hooks.append(hook)
                    logger.info(f"Registered custom hook: {hook.name}")
                except Exception as e:
                    logger.error(f"Failed to instantiate hook {name}: {e}")

    def run(
        self,
        stage: HookStage,
        content: str,
        title: str,
        folder: str | None = None,
        project: str | None = None,
    ) -> HookResult:
        """Execute all hooks for a stage in priority order.

        All hooks run regardless of errors. Strictness controls final result:
        - strict: any error -> success=False
        - balanced: errors become warnings -> success=True
        - flexible: only formatting hooks run -> success=True

        Args:
            stage: Which stage to run (PRE_WRITE, POST_WRITE, etc.)
            content: Note markdown content.
            title: Note title.
            folder: Target folder (optional).
            project: Project identifier (optional).

        Returns:
            Aggregated HookResult with final content and all errors/warnings.
        """
        # Filter hooks for this stage
        stage_hooks = [h for h in self._hooks if h.stage == stage]

        # Sort by priority
        stage_hooks.sort(key=lambda h: self._get_hook_priority(h).value)

        # In flexible mode, only run formatting hooks (those that auto-fix)
        if self._config.is_flexible():
            formatting_hooks = {
                "remove_duplicate_headings",
                "consolidate_observations",
                "format_observations",
                "order_relations",
            }
            stage_hooks = [h for h in stage_hooks if h.name in formatting_hooks]

        # Execute hooks
        current_content = content
        all_errors: list[str] = []
        all_warnings: list[str] = []
        accumulated_metadata: dict = {}
        hooks_run: list[str] = []

        for hook in stage_hooks:
            context = HookContext(
                content=current_content,
                title=title,
                folder=folder,
                project=project,
                metadata=accumulated_metadata.copy(),
            )

            # Check if hook should run
            if not hook.should_run(context):
                continue

            try:
                result = hook.execute(context)
                hooks_run.append(hook.name)

                # Update content if modified
                if result.content is not None:
                    current_content = result.content

                # Collect errors and warnings
                all_errors.extend(result.errors)
                all_warnings.extend(result.warnings)

                # Accumulate metadata
                accumulated_metadata.update(result.metadata)

            except Exception as e:
                logger.error(f"Hook {hook.name} raised exception: {e}")
                all_errors.append(f"Hook {hook.name} failed: {str(e)}")

        # Determine success based on strictness
        if self._config.is_strict():
            success = len(all_errors) == 0
        else:
            # Balanced or flexible: errors become warnings
            all_warnings.extend(all_errors)
            all_errors = []
            success = True

        return HookResult(
            success=success,
            content=current_content,
            errors=all_errors,
            warnings=all_warnings,
            metadata={"hooks_run": hooks_run, **accumulated_metadata},
        )
