"""Tests for types module."""

from basic_memory_hooks.types import (
    HookContext,
    HookPriority,
    HookResult,
    HookStage,
)


class TestHookStage:
    def test_stages_exist(self):
        assert HookStage.PRE_WRITE.value == "pre_write"
        assert HookStage.POST_WRITE.value == "post_write"
        assert HookStage.PRE_EDIT.value == "pre_edit"
        assert HookStage.POST_EDIT.value == "post_edit"


class TestHookPriority:
    def test_priority_ordering(self):
        assert HookPriority.FIRST.value < HookPriority.HIGH.value
        assert HookPriority.HIGH.value < HookPriority.NORMAL.value
        assert HookPriority.NORMAL.value < HookPriority.LOW.value
        assert HookPriority.LOW.value < HookPriority.LAST.value


class TestHookContext:
    def test_minimal_context(self):
        ctx = HookContext(content="# Test", title="Test Note")
        assert ctx.content == "# Test"
        assert ctx.title == "Test Note"
        assert ctx.folder is None
        assert ctx.project is None
        assert ctx.metadata == {}

    def test_full_context(self):
        ctx = HookContext(
            content="# Test",
            title="Test Note",
            folder="notes",
            project="main",
            metadata={"key": "value"},
        )
        assert ctx.folder == "notes"
        assert ctx.project == "main"
        assert ctx.metadata == {"key": "value"}


class TestHookResult:
    def test_default_result(self):
        result = HookResult()
        assert result.success is True
        assert result.content is None
        assert result.errors == []
        assert result.warnings == []
        assert result.metadata == {}

    def test_failure_result(self):
        result = HookResult(
            success=False,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
        )
        assert result.success is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1

    def test_content_modification(self):
        result = HookResult(success=True, content="Modified content")
        assert result.content == "Modified content"
