"""Tests for the hook engine."""

import pytest

from basic_memory_hooks.config import FormatConfig
from basic_memory_hooks.engine import HookEngine
from basic_memory_hooks.hook import Hook
from basic_memory_hooks.types import HookContext, HookPriority, HookResult, HookStage


class AlwaysFailHook(Hook):
    """Test hook that always fails."""

    @property
    def name(self) -> str:
        return "always_fail"

    @property
    def stage(self) -> HookStage:
        return HookStage.PRE_WRITE

    def execute(self, context: HookContext) -> HookResult:
        return HookResult(success=False, errors=["Always fails"])


class ModifyContentHook(Hook):
    """Test hook that modifies content."""

    @property
    def name(self) -> str:
        return "modify_content"

    @property
    def stage(self) -> HookStage:
        return HookStage.PRE_WRITE

    @property
    def priority(self) -> HookPriority:
        return HookPriority.FIRST

    def execute(self, context: HookContext) -> HookResult:
        return HookResult(
            success=True,
            content=context.content + "\n<!-- Modified -->",
        )


class TestHookEngine:
    def test_create_engine(self):
        engine = HookEngine()
        assert engine.config is not None

    def test_register_hook(self):
        engine = HookEngine()
        config = FormatConfig()
        hook = AlwaysFailHook(config)
        engine.register_hook(hook)
        assert len(engine._hooks) == 1

    def test_run_modifies_content(self):
        engine = HookEngine()
        config = FormatConfig()
        hook = ModifyContentHook(config)
        engine.register_hook(hook)

        result = engine.run(
            stage=HookStage.PRE_WRITE,
            content="# Test",
            title="Test",
        )

        assert result.success is True
        assert "<!-- Modified -->" in result.content

    def test_strict_mode_fails_on_error(self):
        engine = HookEngine()
        engine._config.strictness = "strict"
        config = engine._config
        hook = AlwaysFailHook(config)
        engine.register_hook(hook)

        result = engine.run(
            stage=HookStage.PRE_WRITE,
            content="# Test",
            title="Test",
        )

        assert result.success is False
        assert len(result.errors) > 0

    def test_balanced_mode_converts_errors_to_warnings(self):
        engine = HookEngine()
        engine._config.strictness = "balanced"
        config = engine._config
        hook = AlwaysFailHook(config)
        engine.register_hook(hook)

        result = engine.run(
            stage=HookStage.PRE_WRITE,
            content="# Test",
            title="Test",
        )

        assert result.success is True
        assert len(result.errors) == 0
        assert len(result.warnings) > 0

    def test_hooks_run_in_priority_order(self):
        engine = HookEngine()
        config = FormatConfig()
        execution_order = []

        class FirstHook(Hook):
            @property
            def name(self) -> str:
                return "first"

            @property
            def stage(self) -> HookStage:
                return HookStage.PRE_WRITE

            @property
            def priority(self) -> HookPriority:
                return HookPriority.FIRST

            def execute(self, context: HookContext) -> HookResult:
                execution_order.append("first")
                return HookResult(success=True)

        class LastHook(Hook):
            @property
            def name(self) -> str:
                return "last"

            @property
            def stage(self) -> HookStage:
                return HookStage.PRE_WRITE

            @property
            def priority(self) -> HookPriority:
                return HookPriority.LAST

            def execute(self, context: HookContext) -> HookResult:
                execution_order.append("last")
                return HookResult(success=True)

        # Register in reverse order
        engine.register_hook(LastHook(config))
        engine.register_hook(FirstHook(config))

        engine.run(
            stage=HookStage.PRE_WRITE,
            content="# Test",
            title="Test",
        )

        assert execution_order == ["first", "last"]

    def test_stage_filtering(self):
        engine = HookEngine()
        config = FormatConfig()
        pre_write_ran = []
        post_write_ran = []

        class PreWriteHook(Hook):
            @property
            def name(self) -> str:
                return "pre_write"

            @property
            def stage(self) -> HookStage:
                return HookStage.PRE_WRITE

            def execute(self, context: HookContext) -> HookResult:
                pre_write_ran.append(True)
                return HookResult(success=True)

        class PostWriteHook(Hook):
            @property
            def name(self) -> str:
                return "post_write"

            @property
            def stage(self) -> HookStage:
                return HookStage.POST_WRITE

            def execute(self, context: HookContext) -> HookResult:
                post_write_ran.append(True)
                return HookResult(success=True)

        engine.register_hook(PreWriteHook(config))
        engine.register_hook(PostWriteHook(config))

        # Run only pre_write
        engine.run(
            stage=HookStage.PRE_WRITE,
            content="# Test",
            title="Test",
        )

        assert len(pre_write_ran) == 1
        assert len(post_write_ran) == 0

    def test_hooks_run_metadata(self):
        engine = HookEngine()
        config = FormatConfig()

        class MetadataHook(Hook):
            @property
            def name(self) -> str:
                return "metadata_hook"

            @property
            def stage(self) -> HookStage:
                return HookStage.PRE_WRITE

            def execute(self, context: HookContext) -> HookResult:
                return HookResult(success=True)

        engine.register_hook(MetadataHook(config))

        result = engine.run(
            stage=HookStage.PRE_WRITE,
            content="# Test",
            title="Test",
        )

        assert "hooks_run" in result.metadata
        assert "metadata_hook" in result.metadata["hooks_run"]


class TestLoadConfigFromString:
    def test_load_config_with_hooks(self):
        engine = HookEngine()
        config_content = """---
title: Format
type: config
version: "1.0"
strictness: strict
quality:
  minimum_observations: 5
---

# Format Config
"""
        engine.load_config_from_string(config_content)
        assert engine.config.strictness == "strict"
        assert engine.config.quality.minimum_observations == 5
        # Standard hooks should be registered
        assert len(engine._hooks) > 0
