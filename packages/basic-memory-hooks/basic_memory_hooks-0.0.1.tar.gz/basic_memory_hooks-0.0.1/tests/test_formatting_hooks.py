"""Tests for formatting hooks."""

import pytest

from basic_memory_hooks.config import FormatConfig
from basic_memory_hooks.hooks.formatting import (
    ConsolidateObservationsHook,
    FormatObservationsHook,
    OrderRelationsHook,
    RemoveDuplicateHeadingsHook,
)
from basic_memory_hooks.types import HookContext, HookPriority, HookStage


@pytest.fixture
def config():
    return FormatConfig()


class TestRemoveDuplicateHeadingsHook:
    def test_no_duplicates(self, config):
        hook = RemoveDuplicateHeadingsHook(config)
        content = """## Observations
- [fact] A fact

## Relations
- implements [[Feature]]
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is True
        assert result.content is None  # No changes needed

    def test_removes_duplicate_heading(self, config):
        hook = RemoveDuplicateHeadingsHook(config)
        # Note: Observations and Relations are handled by consolidation hooks,
        # so we test with a different section type
        content = """## Context
First context section.

## Summary
The summary.

## Context
Duplicate context section.
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is True
        assert result.content is not None
        # Should only have one Context heading
        assert result.content.count("## Context") == 1
        assert result.metadata["duplicates_removed"] == 1

    def test_priority_is_high(self, config):
        hook = RemoveDuplicateHeadingsHook(config)
        assert hook.priority == HookPriority.HIGH
        assert hook.stage == HookStage.PRE_WRITE


class TestConsolidateObservationsHook:
    def test_single_section_unchanged(self, config):
        hook = ConsolidateObservationsHook(config)
        content = """## Observations
- [fact] A fact
- [decision] A decision
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is True
        assert result.content is None  # No changes

    def test_consolidates_multiple_sections(self, config):
        hook = ConsolidateObservationsHook(config)
        content = """## Observations
- [fact] First fact

## Relations
- implements [[Feature]]

## Observations
- [decision] Second section observation
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is True
        assert result.content is not None
        # Should have consolidated observations
        assert result.content.count("## Observations") == 1
        assert "[fact] First fact" in result.content
        assert "[decision] Second section observation" in result.content

    def test_removes_duplicates(self, config):
        hook = ConsolidateObservationsHook(config)
        content = """## Observations
- [fact] Same observation

## Observations
- [fact] Same observation
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is True
        assert result.content is not None
        # Should only have one instance
        assert result.content.count("Same observation") == 1


class TestFormatObservationsHook:
    def test_already_formatted(self, config):
        hook = FormatObservationsHook(config)
        content = """## Observations
- [fact] A properly formatted fact
- [decision] A properly formatted decision
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is True
        assert result.content is None  # No changes needed

    def test_fixes_colon_format(self, config):
        hook = FormatObservationsHook(config)
        content = """## Observations
- fact: This uses colon format
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is True
        assert result.content is not None
        assert "- [fact] This uses colon format" in result.content

    def test_fixes_bracket_colon_format(self, config):
        hook = FormatObservationsHook(config)
        content = """## Observations
- [fact]: Has colon after bracket
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is True
        assert result.content is not None
        assert "- [fact] Has colon after bracket" in result.content

    def test_no_observations_section(self, config):
        hook = FormatObservationsHook(config)
        content = "# Just a title\n\nNo observations here."
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is True
        assert result.content is None


class TestOrderRelationsHook:
    def test_already_ordered(self, config):
        config.relation_types.primary = ["implements", "requires"]
        config.relation_types.secondary = ["relates_to"]
        hook = OrderRelationsHook(config)
        content = """## Relations
- implements [[Feature A]]
- requires [[Component B]]
- relates_to [[Other]]
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is True
        # No reordering needed
        assert result.content is None or "relations_reordered" not in result.metadata

    def test_reorders_relations(self, config):
        config.relation_types.primary = ["implements", "requires"]
        config.relation_types.secondary = ["relates_to"]
        hook = OrderRelationsHook(config)
        content = """## Relations
- relates_to [[Other]]
- implements [[Feature A]]
- requires [[Component B]]
"""
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is True
        assert result.content is not None
        # Primary relations should come first
        lines = [l.strip() for l in result.content.split("\n") if l.strip().startswith("- ")]
        assert "implements" in lines[0]
        assert "relates_to" in lines[-1]

    def test_no_relations_section(self, config):
        hook = OrderRelationsHook(config)
        content = "# Just a title\n\nNo relations here."
        ctx = HookContext(content=content, title="Test")
        result = hook.execute(ctx)
        assert result.success is True
        assert result.content is None
